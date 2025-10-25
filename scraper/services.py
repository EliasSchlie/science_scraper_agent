"""
Django service for running the scraper agent
"""
import threading
from typing import Optional
from django.utils import timezone
from .models import Interaction, ScraperJob
from .agent.paperfinder import GraphState, StateGraph, START, END
from .agent.pubmed import PubMedAPI
from .agent.doi2pdf import PDFFromDOI

try:
    from langchain_nebius import ChatNebius
    from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
    from langchain_core.tools import tool
    import pymupdf4llm
    from typing_extensions import Annotated
    from typing import Literal
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class ScraperService:
    """Service to run the scraper agent and update Django models"""
    
    def __init__(self, job_id: int):
        self.job = ScraperJob.objects.get(id=job_id)
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain dependencies not installed")
        
        self.llm = ChatNebius(model="moonshotai/Kimi-K2-Instruct")
        self.pubmed_api = PubMedAPI()
        self.pdf_from_doi = PDFFromDOI()
        self._stopped = False

    class JobStoppedException(Exception):
        pass

    def _check_stopped(self):
        """Refresh from DB and raise if stop was requested."""
        # Refresh job to get latest stop flag
        self.job.refresh_from_db(fields=["stop_requested"]) 
        if self.job.stop_requested:
            self._stopped = True
            raise ScraperService.JobStoppedException("Job stopped by user")
    
    def update_status(self, step: str, message: str = ""):
        """Update job status and add to logs"""
        log_message = f"[{step}] {message}"
        print(f"[Job {self.job.id}] {log_message}")
        self.job.add_log(log_message)
    
    def add_interaction(self, iv: str, dv: str, effect: str, doi: str, pub_date: str):
        """Add interaction to database"""
        normalized = self._normalize_effect(effect)
        if normalized is None:
            # Skip non +/- effects
            self.update_status("EXTRACT", f"✗ Skipping interaction with invalid effect '{effect}'")
            return
        Interaction.objects.create(
            workspace=self.job.workspace,
            job=self.job,
            independent_variable=iv,
            dependent_variable=dv,
            effect=normalized,
            reference=doi,
            date_published=pub_date
        )
        self.job.interactions_found += 1
        self.job.save(update_fields=['interactions_found'])
        self.update_status("EXTRACT", f"💾 Found interaction: {iv} → {dv} ({normalized})")

    def _normalize_effect(self, effect: str) -> Optional[str]:
        if not effect:
            return None
        e = str(effect).strip().lower()
        if e in ['+', 'increase', 'increases', 'increased', 'up', 'positive', 'pos', 'inc']:
            return '+'
        if e in ['-', 'decrease', 'decreases', 'decreased', 'down', 'negative', 'neg', 'dec']:
            return '-'
        return None
    
    def run(self):
        """Run the scraper agent"""
        try:
            self.job.status = 'running'
            self.job.save(update_fields=['status'])
            self._check_stopped()
            
            # Build and run the workflow
            agent = self._build_workflow()
            
            result = agent.invoke(
                {
                    "variable_of_interest": self.job.variable_of_interest,
                    "interactions_count": 0,
                    "min_interactions": self.job.min_interactions,
                    "checked_dois": [],
                    "tried_queries": []
                },
                {"recursion_limit": 400}
            )
            
            # Update job
            self.job.status = 'completed'
            self.job.papers_checked = len(result.get('checked_dois', []))
            self.job.completed_at = timezone.now()
            self.job.current_step = f"Completed: {self.job.interactions_found} interactions from {self.job.papers_checked} papers"
            self.job.save()

            # Deduct credits on successful completion
            if self.job.user and hasattr(self.job.user, 'profile'):
                credits_deducted = self.job.user.profile.deduct_credits(self.job.credits_cost)
                if credits_deducted:
                    self.update_status("CREDITS", f"✓ Deducted {self.job.credits_cost} credits. Remaining: {self.job.user.profile.credits}")
                else:
                    self.update_status("CREDITS", f"⚠ Could not deduct credits (insufficient balance)")
        except ScraperService.JobStoppedException as e:
            # Mark as failed (stopped) - NO credit deduction
            self.job.status = 'failed'
            self.job.error_message = 'Job stopped by user'
            self.job.completed_at = timezone.now()
            self.job.add_log('Job stopped by user - no credits charged')
            self.job.save()
            return
        except Exception as e:
            # Mark as failed - NO credit deduction
            self.job.status = 'failed'
            self.job.error_message = str(e)
            self.job.completed_at = timezone.now()
            self.job.add_log(f'Job failed - no credits charged')
            self.job.save()
            raise
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("create_query", self._create_query)
        workflow.add_node("search_pubmed", self._search_pubmed)
        workflow.add_node("filter_papers", self._filter_papers)
        workflow.add_node("check_abstract", self._check_abstract)
        workflow.add_node("download_paper", self._download_paper)
        workflow.add_node("extract_interactions", self._extract_interactions)
        
        # Add edges
        workflow.add_edge(START, "create_query")
        workflow.add_edge("create_query", "search_pubmed")
        workflow.add_edge("search_pubmed", "filter_papers")
        workflow.add_edge("filter_papers", "check_abstract")
        
        workflow.add_conditional_edges(
            "check_abstract",
            self._route_after_abstract,
            {
                "download_paper": "download_paper",
                "check_abstract": "check_abstract",
                "create_query": "create_query"
            }
        )
        
        workflow.add_conditional_edges(
            "download_paper",
            self._route_after_download,
            {
                "extract_interactions": "extract_interactions",
                "check_abstract": "check_abstract",
                "create_query": "create_query"
            }
        )
        
        workflow.add_conditional_edges(
            "extract_interactions",
            self._route_after_extraction,
            {
                "check_abstract": "check_abstract",
                "create_query": "create_query",
                END: END
            }
        )
        
        agent = workflow.compile()
        return agent.with_config(recursion_limit=400)
    
    # Node functions (adapted from paperfinder.py)
    def _create_query(self, state: GraphState) -> dict:
        """AI creates PubMed query from variable of interest"""
        self._check_stopped()
        tried = state.get("tried_queries", [])
        
        if tried:
            self.update_status("QUERY", f"Creating new query (tried {len(tried)} already)")
            previous_queries_text = "\n".join([f"  {i+1}. {q}" for i, q in enumerate(tried)])
            prompt = f"""Variable of interest: {state['variable_of_interest']}

Previously tried queries:
{previous_queries_text}

These queries have been exhausted. Create a NEW, CREATIVE query that approaches the topic differently.
Create a concise PubMed search query for intervention studies on human substrate."""
        else:
            self.update_status("QUERY", f"Creating query for: {state['variable_of_interest']}")
            prompt = f"""Variable of interest: {state['variable_of_interest']}
Create a concise PubMed search query for finding intervention studies on human substrate about this variable."""
        
        response = self.llm.invoke([
            SystemMessage(content="You are an expert at crafting PubMed search queries for human intervention studies."),
            HumanMessage(content=prompt)
        ])
        
        query = response.content.strip()
        self.update_status("QUERY", f"Generated: {query}")
        
        return {"query": query, "tried_queries": [query]}
    
    def _search_pubmed(self, state: GraphState) -> dict:
        """Search PubMed API"""
        self._check_stopped()
        self.update_status("PUBMED", f"Searching: {state['query']}")
        papers = self.pubmed_api.search(state['query'], max_results=100)
        self.update_status("PUBMED", f"Found {len(papers)} papers")
        return {"papers": papers}
    
    def _filter_papers(self, state: GraphState) -> dict:
        """Filter out already checked papers"""
        self._check_stopped()
        checked = state.get("checked_dois", [])
        filtered = [p for p in state["papers"] if p.get("doi") and p["doi"] not in checked]
        self.update_status("FILTER", f"Filtered to {len(filtered)} new papers")
        return {"papers": filtered}
    
    def _check_abstract(self, state: GraphState) -> dict:
        """AI checks if abstract is relevant"""
        self._check_stopped()
        if not state["papers"]:
            return {"current_paper": {}}
        
        paper = state["papers"][0]
        remaining = state["papers"][1:]
        
        # Show full title in logs
        title = paper.get('title', 'No title')
        self.update_status("ABSTRACT", f"Checking paper: '{title}'")
        
        response = self.llm.invoke([
            SystemMessage(content=f"You are evaluating if this paper is relevant to: {state['variable_of_interest']}. Check if it's an intervention study on human substrate. Reply with 'yes' or 'no'."),
            HumanMessage(content=f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}")
        ])
        
        is_relevant = response.content.strip().lower() in ["yes", "y"]
        
        if is_relevant:
            self.update_status("ABSTRACT", f"✓ Paper is relevant! Will download.")
            return {"papers": remaining, "current_paper": paper, "checked_dois": [paper.get("doi", "")]}
        else:
            self.update_status("ABSTRACT", f"✗ Not relevant. Skipping.")
            return {"papers": remaining, "current_paper": {}, "checked_dois": [paper.get("doi", "")]}
    
    def _download_paper(self, state: GraphState) -> dict:
        """Download paper PDF and convert to markdown"""
        self._check_stopped()
        paper = state["current_paper"]
        doi = paper.get("doi")
        
        if not doi:
            return {"paper_md": "", "current_paper": {}}
        
        self.update_status("DOWNLOAD", f"📥 Downloading PDF for DOI: {doi}")
        
        try:
            path = self.pdf_from_doi.download(doi)
            self.update_status("DOWNLOAD", f"✓ PDF downloaded successfully")
            self.update_status("CONVERT", f"📄 Converting PDF to text...")
            md = pymupdf4llm.to_markdown(str(path))
            self.update_status("CONVERT", f"✓ Converted to text ({len(md):,} characters)")
            return {"paper_md": md}
        except FileNotFoundError as e:
            self.update_status("DOWNLOAD", f"✗ Paper is paywalled (not open access). Skipping.")
            return {"paper_md": "", "current_paper": {}}
        except Exception as e:
            self.update_status("DOWNLOAD", f"✗ Download failed: {str(e)}")
            return {"paper_md": "", "current_paper": {}}
    
    def _extract_interactions(self, state: GraphState) -> dict:
        """AI extracts interactions from paper"""
        self._check_stopped()
        if not state["paper_md"]:
            return {"interactions_count": state.get("interactions_count", 0), "current_paper": {}, "paper_md": ""}
        
        self.update_status("EXTRACT", "Extracting interactions")
        
        doi = state['current_paper'].get('doi', '')
        pub_date = state['current_paper'].get('pub_date', '')
        
        # Truncate paper to avoid token limit issues
        # Rough estimate: 1 token ≈ 4 characters, we want to stay under 100k tokens
        # so limit to about 400k characters (leaving room for prompts and responses)
        paper_content = state['paper_md']
        max_chars = 400000
        if len(paper_content) > max_chars:
            self.update_status("EXTRACT", f"Paper too long ({len(paper_content):,} chars), truncating to {max_chars:,} chars")
            paper_content = paper_content[:max_chars] + "\n\n[... Paper truncated due to length ...]"
        
        extraction_complete = False
        
        # Create tools
        @tool
        def submit_interactions(interactions: list[dict]) -> str:
            """Submit extracted interactions"""
            count = 0
            for interaction in interactions:
                self.add_interaction(
                    interaction['iv'],
                    interaction['dv'],
                    interaction['effect'],
                    doi,
                    pub_date
                )
                count += 1
            return f"{count} interaction(s) submitted successfully."
        
        @tool
        def finish_extraction() -> str:
            """Call when finished extracting"""
            nonlocal extraction_complete
            extraction_complete = True
            return "Extraction complete."
        
        llm_with_tools = self.llm.bind_tools([submit_interactions, finish_extraction])
        
        initial_prompt = f"""Analyze this paper and extract ALL intervention studies on human substrate.

Variable of interest: {state['variable_of_interest']}

For each experiment:
- Independent variable (IV): what was manipulated
- Dependent variable (DV): what was measured
- Effect: '+' if IV increases DV, '-' if IV decreases DV

Call submit_interactions with your findings, then call finish_extraction when done.

Paper content:
{paper_content}"""
        
        messages = [
            SystemMessage(content="Extract ALL causal relationships. Call submit_interactions then finish_extraction."),
            HumanMessage(content=initial_prompt)
        ]
        
        count = state.get("interactions_count", 0)
        max_iterations = 20
        iteration = 0
        
        while not extraction_complete and iteration < max_iterations:
            self._check_stopped()
            iteration += 1
            response = llm_with_tools.invoke(messages)
            messages.append(response)
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_messages = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    
                    if tool_name == 'submit_interactions':
                        try:
                            result = submit_interactions.invoke(tool_call['args'])
                            count += len(tool_call['args'].get('interactions', []))
                            tool_messages.append({
                                "role": "tool",
                                "content": result,
                                "tool_call_id": tool_call['id']
                            })
                        except Exception as e:
                            tool_messages.append({
                                "role": "tool",
                                "content": f"Error: {e}",
                                "tool_call_id": tool_call['id']
                            })
                    
                    elif tool_name == 'finish_extraction':
                        result = finish_extraction.invoke({})
                        tool_messages.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call['id']
                        })
                
                for tm in tool_messages:
                    messages.append(ToolMessage(content=tm["content"], tool_call_id=tm["tool_call_id"]))
            else:
                messages.append(HumanMessage(content="Continue or call finish_extraction."))
        
        return {"interactions_count": count, "current_paper": {}, "paper_md": ""}
    
    # Routing functions
    def _route_after_abstract(self, state: GraphState) -> Literal["download_paper", "check_abstract", "create_query"]:
        if state.get("current_paper", {}).get("doi"):
            return "download_paper"
        elif state.get("papers", []):
            return "check_abstract"
        else:
            return "create_query"
    
    def _route_after_download(self, state: GraphState) -> Literal["extract_interactions", "check_abstract", "create_query"]:
        if state.get("paper_md"):
            return "extract_interactions"
        elif state.get("papers", []):
            return "check_abstract"
        else:
            return "create_query"
    
    def _route_after_extraction(self, state: GraphState) -> Literal["check_abstract", "create_query", END]:
        count = state.get("interactions_count", 0)
        min_count = state.get("min_interactions", 5)
        
        self.update_status("STATUS", f"Progress: {count}/{min_count} interactions")
        
        if count >= min_count:
            self.update_status("STATUS", "Target reached!")
            return END
        elif state.get("papers", []):
            return "check_abstract"
        else:
            return "create_query"


def run_scraper_job(job_id: int):
    """Run scraper job in background thread"""
    service = ScraperService(job_id)
    service.run()


def start_scraper_job_async(job_id: int):
    """Start scraper job in a background thread"""
    thread = threading.Thread(target=run_scraper_job, args=(job_id,), daemon=True)
    thread.start()
    return thread


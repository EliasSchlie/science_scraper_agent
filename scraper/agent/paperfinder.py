from langchain_nebius import ChatNebius
from langchain_core.messages import SystemMessage, HumanMessage
from typing_extensions import TypedDict, Annotated
from typing import Literal
from langgraph.graph import StateGraph, START, END
import pymupdf4llm
from dotenv import load_dotenv
load_dotenv()


# Relative imports for Django app
from .pubmed import PubMedAPI
from .doi2pdf import PDFFromDOI
from .interaction_storage import InteractionStorage



llm = ChatNebius(model="moonshotai/Kimi-K2-Instruct")
# llm = ChatNebius(model="Qwen/Qwen3-235B-A22B-Instruct-2507")
# reasoning_llm = ChatNebius(model="deepseek-ai/DeepSeek-R1-0528")
pubmed_api = PubMedAPI()
pdf_from_doi = PDFFromDOI()
interaction_storage = InteractionStorage()

# State definition
class GraphState(TypedDict):
    variable_of_interest: str
    query: str
    papers: list[dict]
    checked_dois: Annotated[list[str], lambda x, y: list(set(x + y))]
    tried_queries: Annotated[list[str], lambda x, y: x + y]
    current_paper: dict
    paper_md: str
    interactions_count: int
    min_interactions: int

# Node functions
def create_query(state: GraphState) -> dict:
    """AI creates PubMed query from variable of interest"""
    print(f"\n--- Creating query for: {state['variable_of_interest']} ---")
    
    tried = state.get("tried_queries", [])
    
    if tried:
        print(f"Previous queries tried: {len(tried)}")
        previous_queries_text = "\n".join([f"  {i+1}. {q}" for i, q in enumerate(tried)])
        prompt = f"""Variable of interest: {state['variable_of_interest']}

Previously tried queries:
{previous_queries_text}

These queries have been exhausted. Create a NEW, CREATIVE query that approaches the topic differently to uncover papers not yet found. 

Be creative:
- Use synonyms and related terms
- Try different medical terminology
- Include related conditions or mechanisms
- Use different publication types or filters
- Think laterally about the research question
- Be more broad in the query

Create a concise PubMed search query for intervention studies on human substrate."""
    else:
        prompt = f"""Variable of interest: {state['variable_of_interest']}

Create a concise PubMed search query for finding intervention studies on human substrate about this variable. Include relevant keywords and filters."""
    
    response = llm.invoke([
        SystemMessage(content="You are an expert at crafting PubMed search queries. Your aim is to create queries that uncover human intervention studies about the effects of a given variable of interest."),
        HumanMessage(content=prompt)
    ])
    
    query = response.content.strip()
    print(f"Generated query: {query}")
    
    return {"query": query, "tried_queries": [query]}

def search_pubmed(state: GraphState) -> dict:
    """Search PubMed API"""
    print(f"\n--- Searching PubMed: {state['query']} ---")
    papers = pubmed_api.search(state['query'], max_results=100)
    print(f"Found {len(papers)} papers")
    return {"papers": papers}

def filter_papers(state: GraphState) -> dict:
    """Filter out already checked papers"""
    print("\n--- Filtering papers ---")
    checked = state.get("checked_dois", [])
    filtered = [p for p in state["papers"] if p.get("doi") and p["doi"] not in checked]
    print(f"Filtered to {len(filtered)} new papers (from {len(state['papers'])})")
    return {"papers": filtered}

def check_abstract(state: GraphState) -> dict:
    """AI checks if abstract is relevant"""
    if not state["papers"]:
        return {"current_paper": {}}
    
    paper = state["papers"][0]
    remaining = state["papers"][1:]  # Remove current paper from list regardless
    
    print(f"\n--- Checking abstract: {paper.get('title', 'No title')[:50]}... ---")
    
    response = llm.invoke([
        SystemMessage(content=f"You are evaluating if this paper is relevant to: {state['variable_of_interest']}. Check if it's an intervention study on human substrate and contains causal relationships. Reply with 'yes' if relevant, 'no' if not."),
        HumanMessage(content=f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}")
    ])
    
    is_relevant = response.content.strip().lower() in ["yes", "y"]
    print(f"Abstract relevant: {is_relevant}")
    
    if is_relevant:
        return {"papers": remaining, "current_paper": paper, "checked_dois": [paper.get("doi", "")]}
    else:
        return {"papers": remaining, "current_paper": {}, "checked_dois": [paper.get("doi", "")]}

def download_paper(state: GraphState) -> dict:
    """Download paper PDF and convert to markdown"""
    paper = state["current_paper"]
    doi = paper.get("doi")
    
    if not doi:
        return {"paper_md": "", "current_paper": {}}
    
    print(f"\n--- Downloading DOI: {doi} ---")
    
    try:
        path = pdf_from_doi.download(doi)
        md = pymupdf4llm.to_markdown(str(path))
        print(f"Successfully converted to markdown ({len(md)} chars)")
        return {"paper_md": md}
    except Exception as e:
        print(f"Error processing paper: {e}")
        return {"paper_md": "", "current_paper": {}}

def extract_interactions(state: GraphState) -> dict:
    """AI extracts interactions from paper using tool calls, looping until done"""
    if not state["paper_md"]:
        return {"interactions_count": state.get("interactions_count", 0), "current_paper": {}, "paper_md": ""}
    
    print("\n--- Extracting interactions ---")
    
    # Get paper metadata for automatic reference/date
    doi = state['current_paper'].get('doi', '')
    pub_date = state['current_paper'].get('pub_date', '')
    
    # Track if extraction is complete
    extraction_complete = False
    
    # Create tools
    from langchain_core.tools import tool
    
    @tool
    def submit_interactions(interactions: list[dict]) -> str:
        """Submit one or more extracted interactions from the paper in a single call.
        
        Args:
            interactions: List of interaction dicts, each containing:
                - iv: The independentvariable that is manipulated/changed (IV)
                - dv: The dependent variable that is measured/affected (DV)
                - effect: The effect type - use '+' if IV increases DV (or IV decrease causes DV decrease), use '-' if IV decreases DV (or IV decrease causes DV increase)

        Example:
        submit_interactions([
            {
                "iv": "Creatine supplementation",
                "dv": "Creatine kinase",
                "effect": "+"
            },
            {
                "iv": "Creatine supplementation",
                "dv": "Migraines",
                "effect": "-"
            }
        ])
        """
        count = 0
        output = ""
        for interaction in interactions:
            interaction_storage.add_interaction(
                interaction['iv'], 
                interaction['dv'], 
                interaction['effect'], 
                doi, 
                pub_date
            )
            output += f"  ✓ Stored: {interaction['iv']} -> {interaction['dv']} ({interaction['effect']})\n"
            count += 1
        output += f"{count} interaction(s) submitted successfully. Continue extracting or call finish_extraction when done."
        print(output)
        return output
    
    @tool
    def finish_extraction() -> str:
        """Call this tool when you have finished extracting ALL relevant interactions from the paper, or if there are no relevant interactions to extract."""
        nonlocal extraction_complete
        extraction_complete = True
        return "Extraction complete."
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools([submit_interactions, finish_extraction])
    
    initial_prompt = f"""Analyze this paper and extract ALL intervention studies on human substrate.

Variable of interest: {state['variable_of_interest']}

For each experiment that shows a causal relationship:
- Identify the independent variable (IV) - what was manipulated
- Identify the dependent variable (DV) - what was measured
- Determine the effect:
  * '+' if IV increases DV, or if decreasing IV decreases DV
  * '-' if IV decreases DV, or if decreasing IV increases DV

IMPORTANT: 
1. Call the submit_interactions tool with the interactions you find. Don't just provide them in the chat!
2. When you have extracted ALL interactions (or if there are none), call finish_extraction
3. You MUST call finish_extraction when done

Paper content:
{state['paper_md']}"""
    
    # Initialize message history
    messages = [
        SystemMessage(content="You are a scientific paper analyzer. Extract ALL causal relationships by calling submit_interactions. When completely done, call finish_extraction."),
        HumanMessage(content=initial_prompt)
    ]
    
    count = state.get("interactions_count", 0)
    max_iterations = 20  # Safety limit
    iteration = 0
    
    # Loop until extraction is complete
    while not extraction_complete and iteration < max_iterations:
        iteration += 1
        print(f"\n  Extraction iteration {iteration}...")
        
        response = llm_with_tools.invoke(messages)
        messages.append(response)  # Add AI response to history
        
        # Process tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"  {len(response.tool_calls)} tool call(s)")
            
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                
                if tool_name == 'submit_interactions':
                    try:
                        result = submit_interactions.invoke(tool_call['args'])
                        # Count the number of interactions submitted
                        count += len(tool_call['args'].get('interactions', []))
                        tool_messages.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call['id']
                        })
                    except Exception as e:
                        print(f"  ✗ Failed to submit interaction: {e}")
                        tool_messages.append({
                            "role": "tool",
                            "content": f"Error: {e}",
                            "tool_call_id": tool_call['id']
                        })
                
                elif tool_name == 'finish_extraction':
                    result = finish_extraction.invoke({})
                    print(f"  ✓ {result}")
                    tool_messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call['id']
                    })
            
            # Add tool responses to message history
            from langchain_core.messages import ToolMessage
            for tm in tool_messages:
                messages.append(ToolMessage(content=tm["content"], tool_call_id=tm["tool_call_id"]))
        else:
            # No tool calls - prompt to continue
            print("  No tool calls, prompting to continue or finish...")
            messages.append(HumanMessage(content="Continue extracting interactions or call finish_extraction if you are done."))
    
    if iteration >= max_iterations:
        print(f"  ⚠ Reached max iterations ({max_iterations}), stopping extraction")
    
    # Clear current paper and paper_md to move to next
    return {"interactions_count": count, "current_paper": {}, "paper_md": ""}

# Routing functions
def route_after_abstract(state: GraphState) -> Literal["download_paper", "check_abstract", "create_query"]:
    """Route based on abstract check result"""
    if state.get("current_paper", {}).get("doi"):
        return "download_paper"
    elif state.get("papers", []):
        return "check_abstract"
    else:
        return "create_query"

def route_after_download(state: GraphState) -> Literal["extract_interactions", "check_abstract", "create_query"]:
    """Route based on download success"""
    if state.get("paper_md"):
        return "extract_interactions"
    elif state.get("papers", []):
        return "check_abstract"
    else:
        return "create_query"

def route_after_extraction(state: GraphState) -> Literal["check_abstract", "create_query", END]:
    """Route based on interactions count"""
    count = state.get("interactions_count", 0)
    min_count = state.get("min_interactions", 5)
    
    print(f"\n--- Interactions: {count}/{min_count} ---")
    
    if count >= min_count:
        print("✓ Enough interactions found!")
        return END
    elif state.get("papers", []):
        print("→ Checking next paper")
        return "check_abstract"
    else:
        print("→ Searching for more papers")
        return "create_query"

# Build workflow
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("create_query", create_query)
workflow.add_node("search_pubmed", search_pubmed)
workflow.add_node("filter_papers", filter_papers)
workflow.add_node("check_abstract", check_abstract)
workflow.add_node("download_paper", download_paper)
workflow.add_node("extract_interactions", extract_interactions)

# Add edges
workflow.add_edge(START, "create_query")
workflow.add_edge("create_query", "search_pubmed")
workflow.add_edge("search_pubmed", "filter_papers")
workflow.add_edge("filter_papers", "check_abstract")

workflow.add_conditional_edges(
    "check_abstract",
    route_after_abstract,
    {
        "download_paper": "download_paper",
        "check_abstract": "check_abstract",
        "create_query": "create_query"
    }
)

workflow.add_conditional_edges(
    "download_paper",
    route_after_download,
    {
        "extract_interactions": "extract_interactions",
        "check_abstract": "check_abstract",
        "create_query": "create_query"
    }
)

workflow.add_conditional_edges(
    "extract_interactions",
    route_after_extraction,
    {
        "check_abstract": "check_abstract",
        "create_query": "create_query",
        END: END
    }
)

# Compile with increased recursion limit
agent = workflow.compile()
agent = agent.with_config(recursion_limit=400)

if __name__ == "__main__":
    result = agent.invoke(
        {
            "variable_of_interest": "creatine",
            "interactions_count": 0,
            "min_interactions": 3,
            "checked_dois": [],
            "tried_queries": []
        },
        {"recursion_limit": 400}
    )
    print(f"\n\n=== FINAL RESULT ===")
    print(f"Total interactions found: {result.get('interactions_count', 0)}")
    print(f"Papers checked: {len(result.get('checked_dois', []))}")

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2+ web application with an AI-powered scientific paper scraper. The scraper uses LangGraph agents to automatically search PubMed, download papers, and extract causal relationships (IV→DV) from intervention studies.

## Tech Stack

- **Backend**: Django 5.2+, Python 3.13+
- **Package Management**: `uv` (preferred) or pip
- **AI/LLM**: LangChain, LangGraph, Nebius API (Kimi-K2-Instruct model)
- **Database**: SQLite (dev), PostgreSQL (production recommended)
- **PDF Processing**: PyMuPDF4LLM
- **APIs**: PubMed, Unpaywall, arXiv
- **Deployment**: Gunicorn, WhiteNoise (static files)
- **Frontend**: Vanilla JS, CSS3 (no framework)

## Development Commands

### Package Management (uv preferred)
```bash
# Install dependencies
uv sync

# Add new package
uv add package_name

# Run Python scripts
uv run python manage.py <command>
uv run python script.py
```

### Django Commands
```bash
# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files (production)
python manage.py collectstatic --noinput

# Run tests
python manage.py test
```

### Management Commands (Custom)
```bash
# Test scraper agent
python manage.py test_scraper "creatine" --min-interactions=3

# Fix stuck jobs (sets running jobs to failed)
python manage.py fix_stuck_jobs
```

## Environment Variables

Required in `.env` file:

```env
# Django core
SECRET_KEY=your-secret-key
DEBUG=True  # False in production
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# AI scraper (required)
NEBIUS_API_KEY=your-nebius-api-key

# Optional
BRIGHT_WEB_UNLOCKER_KEY=your-bright-data-key  # For paywalled papers
```

## Architecture

### Project Structure
```
config/           - Django settings, URLs, WSGI/ASGI
core/             - Core Django app (home page)
scraper/          - Scientific paper scraper app
  ├── agent/      - LangGraph agent implementation
  ├── management/ - Custom Django commands
  ├── migrations/ - Database migrations
  ├── templates/  - HTML templates
  ├── models.py   - Database models (Interaction, ScraperJob)
  ├── views.py    - API endpoints and views
  ├── services.py - ScraperService (agent runner)
  └── urls.py     - URL routing
```

### Key Apps

**scraper** - The main feature of this project
- Models: `Interaction` (IV→DV relationships), `ScraperJob` (job tracking)
- Service layer: `ScraperService` runs LangGraph agent in background threads
- Agent workflow: Query creation → PubMed search → Abstract check → PDF download → Interaction extraction
- Workspace system: Isolate different research topics/projects

### Scraper Agent Workflow (LangGraph)

The agent runs as a state machine with these nodes:
1. **create_query**: AI generates PubMed search query
2. **search_pubmed**: Search PubMed API (max 100 results)
3. **filter_papers**: Remove already-checked DOIs
4. **check_abstract**: AI evaluates paper relevance
5. **download_paper**: Get PDF from Unpaywall/arXiv, convert to markdown
6. **extract_interactions**: AI extracts IV/DV/effect tuples using tool calling
7. Loops until `min_interactions` found or queries exhausted

State tracking: GraphState TypedDict manages workflow state including `checked_dois`, `tried_queries`, `interactions_count`, etc.

### Database Models

**Interaction** - Stores extracted causal relationships
- Fields: `workspace`, `job`, `independent_variable`, `dependent_variable`, `effect` (+/-), `reference` (DOI), `date_published`
- Indexed by workspace and creation time
- Cascade deletes when parent job is deleted

**ScraperJob** - Tracks job execution
- Status: pending → running → completed/failed
- Real-time logging via `add_log()` method
- Tracks progress: `interactions_found`, `papers_checked`, `current_step`
- Stop mechanism: `stop_requested` flag checked throughout workflow
- Workspace isolation

### Background Job Execution

Jobs run in daemon threads (see `services.py`):
- `start_scraper_job_async()` spawns thread
- `ScraperService._check_stopped()` polls `stop_requested` flag
- Updates database in real-time as interactions found
- Frontend polls `/api/job/<id>/status/` every 2 seconds

**Important**: This uses simple threading. For production, consider Celery + Redis for better reliability and scalability.

## API Endpoints

All under `/scraper/api/`:
- `POST /start/` - Start new job
- `GET /job/<id>/status/` - Job status (polled by frontend)
- `GET /job/<id>/interactions/` - Get job's interactions
- `POST /job/<id>/stop/` - Request job stop
- `POST /job/<id>/delete/` - Delete job (with force option)
- `GET /interactions/` - All interactions (current workspace)
- `GET /workspaces/` - List all workspaces
- `POST /workspace/switch/` - Switch workspace (session-based)

## Frontend Notes

- Two views: `/scraper/` (job interface) and `/scraper/graph/` (network visualization)
- Vanilla JS with real-time polling (2 second intervals)
- Workspace switcher in header
- No build process required
- Templates in `scraper/templates/scraper/`

## Testing

- Use `python manage.py test` for Django tests
- Custom command: `python manage.py test_scraper <variable> --min-interactions=N`
- Agent logs print to console for debugging

## Deployment

Auto-deploys to VPS on push to `main` branch.

**Pre-deployment checklist**:
- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for production domain
- Set `NEBIUS_API_KEY` on server
- Run migrations: `python manage.py migrate`
- Collect static files: `python manage.py collectstatic --noinput`
- Restart Gunicorn service

**Production recommendations**:
- Use PostgreSQL instead of SQLite
- Implement Celery for background jobs
- Add rate limiting to API endpoints
- Configure proper logging
- Set up monitoring for stuck jobs

## Important Implementation Details

### LLM Integration
- Model: `moonshotai/Kimi-K2-Instruct` via Nebius API
- Tool calling used for interaction extraction
- Papers truncated to 400k chars (~100k tokens) to avoid context limits
- Handles tool invocation loops (max 20 iterations per paper)

### Effect Normalization
Effects are normalized in `ScraperService._normalize_effect()`:
- `+`: increase, increases, up, positive, pos, inc
- `-`: decrease, decreases, down, negative, neg, dec
- Invalid effects are skipped (not stored)

### Stop Mechanism
Jobs can be stopped via UI:
- Sets `stop_requested=True` on ScraperJob
- Agent checks flag via `_check_stopped()` before each node
- Raises `JobStoppedException` to cleanly exit workflow
- Job marked as `failed` with error message "Job stopped by user"

### Workspace System
- Session-based workspace switching
- All queries filtered by current workspace
- Default workspace: "default"
- Allows organizing research by topic/project

## Common Tasks

### Adding a new field to Interaction model
1. Edit `scraper/models.py` - add field to `Interaction` class
2. Run `python manage.py makemigrations scraper`
3. Run `python manage.py migrate`
4. Update `ScraperService.add_interaction()` to populate new field
5. Update API serialization in `views.py` (interactions_list, job_interactions)

### Modifying agent workflow
1. Edit node functions in `scraper/services.py` (e.g., `_create_query`, `_check_abstract`)
2. Update routing logic if needed (`_route_after_*` methods)
3. Test with `python manage.py test_scraper "test variable"`

### Adding new API endpoint
1. Add view function in `scraper/views.py`
2. Add URL pattern in `scraper/urls.py`
3. Update frontend JS if needed

## Known Issues & Limitations

- Threading approach not ideal for production (use Celery)
- No job cancellation mid-execution (only stop request)
- Papers over 400k chars are truncated
- Paywalled papers are skipped (unless Bright Data configured)
- SQLite may have concurrency issues with multiple simultaneous jobs
- No pagination on interactions list (limited to 100)

## Dependencies to Note

Critical packages:
- `langchain-nebius>=0.1.3` - Nebius LLM integration
- `langgraph>=0.2.0` - Workflow state machine
- `pymupdf4llm>=0.0.27` - PDF to markdown conversion
- `django>=5.2.7` - Web framework
- `python-decouple>=3.8` - Environment variable management

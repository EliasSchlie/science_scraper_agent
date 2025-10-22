# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2+ web application with AI-powered scientific paper scraper. The scraper uses LangGraph to autonomously search PubMed, download papers, and extract causal interactions (IV → DV relationships) from research literature.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Create .env file with required variables:
# SECRET_KEY, DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, NEBIUS_API_KEY
```

### Database Operations
```bash
# Create migrations
uv run manage.py makemigrations

# Apply migrations
uv run manage.py migrate

# Create superuser
uv run manage.py createsuperuser

# Access Django shell
uv run manage.py shell
```

### Development Server
```bash
# Run development server
uv run manage.py runserver

# Collect static files (production)
uv run manage.py collectstatic --noinput
```

### Testing
```bash
# Run all tests
uv run manage.py test

# Run tests for specific app
uv run manage.py test scraper

# Test scraper functionality
uv run manage.py test_scraper
```

### Management Commands
```bash
# Fix stuck jobs (default: jobs running for 2+ hours)
uv run manage.py fix_stuck_jobs

# Fix stuck jobs with custom threshold
uv run manage.py fix_stuck_jobs --hours 6
```

## Architecture

### Core Structure
- **config/**: Django project settings, URL routing
- **core/**: Simple landing page app
- **scraper/**: Main application for paper scraping and graph visualization

### Scraper App Components

#### Models (scraper/models.py)
- **Workspace**: Container for interaction graphs, has many jobs and interactions
- **ScraperJob**: Tracks background scraping jobs, belongs to workspace
- **Interaction**: Stores IV→DV relationships with effect (+/-), belongs to workspace

#### Services (scraper/services.py)
- **ScraperService**: Django wrapper around LangGraph agent
- Runs in background threads via `start_scraper_job_async()`
- Updates job status in real-time via `job.add_log()`
- Only stores interactions where `variable_of_interest` appears as exact IV or DV

#### Views (scraper/views.py)
- **graph_view**: Main UI page
- **create_workspace**: POST to create workspace and start initial search
- **expand_variable**: POST to search for new variable in existing workspace
- **workspace_data**: GET interactions for graph visualization
- **job_status**: GET real-time job progress (polled by frontend)
- **stop_job**: POST to request job cancellation

#### Agent Workflow (scraper/agent/paperfinder.py)
LangGraph state machine with nodes:
1. **create_query**: LLM generates PubMed search query
2. **search_pubmed**: Query PubMed API (max 100 results)
3. **filter_papers**: Remove already-checked DOIs
4. **check_abstract**: LLM evaluates relevance
5. **download_paper**: Get PDF via Unpaywall/arXiv, convert to markdown
6. **extract_interactions**: LLM extracts IV/DV/effect tuples via tool calls

Loops until `min_interactions` found or exhausts search strategies.

#### Helper Modules
- **agent/pubmed.py**: PubMed API wrapper
- **agent/doi2pdf.py**: PDF downloader (Unpaywall, arXiv)
- **agent/interaction_storage.py**: CSV storage (unused in Django version)

### Key Design Patterns

#### Job Lifecycle
1. User creates workspace or expands variable
2. ScraperJob created with status='pending'
3. `start_scraper_job_async()` spawns background thread
4. Thread runs LangGraph workflow, updates job in real-time
5. Job completes with status='completed' or 'failed'

#### Stop Mechanism
- Frontend sets `job.stop_requested = True`
- Service checks `_check_stopped()` at every node
- Raises `JobStoppedException` to cleanly exit workflow

#### Real-time Updates
- Frontend polls `/scraper/api/job/{id}/status/` every 2 seconds
- Service calls `job.add_log()` to update logs and current_step
- Graph updates via `/scraper/api/workspace/{id}/`

#### Frontend Architecture
- Single-page app using vanilla JavaScript (no framework)
- Cytoscape.js for interactive graph visualization
- Nodes represent variables, edges represent IV→DV relationships
- Color-coded edges: green for positive effects (+), red for negative (-)
- Right-click on nodes to expand (search for that variable's interactions)

## Environment Variables

Required:
- `SECRET_KEY`: Django secret key
- `DEBUG`: True/False
- `ALLOWED_HOSTS`: Comma-separated hostnames
- `NEBIUS_API_KEY`: For ChatNebius LLM (required for scraper)

Optional:
- `CSRF_TRUSTED_ORIGINS`: Comma-separated URLs
- `BRIGHT_WEB_UNLOCKER_KEY`: For paywalled papers

## Database

Development: SQLite (db.sqlite3)
Production: Consider PostgreSQL for better concurrency

## Static Files

Uses WhiteNoise for serving in production:
- `STATIC_ROOT = BASE_DIR / 'staticfiles'`
- `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`

## Media Files

PDF downloads stored in: `MEDIA_ROOT = BASE_DIR / 'media'`

## Important Constraints

### Interaction Storage
The scraper only stores interactions where `variable_of_interest` matches IV or DV **exactly** (case-sensitive). This is enforced in `services.py:add_interaction()` at lines 64-66. This prevents storing tangential relationships.

### Background Jobs
Current implementation uses simple threading (`daemon=True`) via `start_scraper_job_async()`. Jobs run in background threads and update the database in real-time. For production with high load, consider:
- Celery + Redis
- Django-Q
- Huey

Note: Threading works well for low-to-medium load. Each job is independent and self-contained.

### LLM Model
Uses `moonshotai/Kimi-K2-Instruct` via ChatNebius API (Nebius AI). To change model, update:
- `services.py:32` - Service instantiation
- `agent/paperfinder.py:17` - Standalone agent

### Recursion Limit
LangGraph workflow has `recursion_limit=400` to handle long search sessions. Each query→search→filter→check→download→extract cycle counts toward this limit.

## URL Structure

- `/` - Core app landing page
- `/scraper/` - Graph visualization UI (Cytoscape.js-based interactive graph)
- `/admin/` - Django admin panel
- `/scraper/api/workspace/create/` - POST: Create workspace and start initial search
- `/scraper/api/workspace/{id}/` - GET: Get workspace data and interactions
- `/scraper/api/workspace/{id}/expand/` - POST: Expand graph by searching for new variable
- `/scraper/api/workspace/{id}/jobs/` - GET: Get all jobs for workspace
- `/scraper/api/workspace/{id}/delete/` - POST: Delete workspace and all data
- `/scraper/api/job/{id}/status/` - GET: Real-time job status (polled by frontend)
- `/scraper/api/job/{id}/stop/` - POST: Request job cancellation

## Deployment

Auto-deploys to VPS on push to main branch. Ensure deployment script includes:
```bash
uv sync
uv run manage.py migrate
uv run manage.py collectstatic --noinput
sudo systemctl restart your-django-service
```

Set `DEBUG=False` and proper `ALLOWED_HOSTS` in production.

## Common Gotchas

1. **Job stuck in "running"**: Check server logs, may need `fix_stuck_jobs` management command
2. **No interactions found**: Variable may be too specific, try broader terms
3. **PDF download fails**: Paper may be paywalled, agent skips to next
4. **LangChain import errors**: Ensure all requirements installed via `uv sync`
5. **Stop button doesn't work immediately**: Agent only checks between nodes, may take 10-30 seconds

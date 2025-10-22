# Scientific Paper Scraper Agent - Django Web Interface

This Django app provides a beautiful web interface for the scientific paper scraper agent. It automatically searches PubMed for scientific papers, downloads them, and extracts causal interactions using AI.

## Features

- 🔍 **Smart Search**: AI-powered PubMed query generation
- 📄 **Automatic PDF Download**: Downloads open-access papers from Unpaywall and arXiv
- 🤖 **AI Extraction**: Uses LLMs to extract causal relationships from papers
- 📊 **Real-time Progress**: See the agent work in real-time with live updates
- 💾 **Database Storage**: All interactions saved to Django database
- 🎨 **Beautiful UI**: Modern, responsive interface with gradient design
- 📈 **Job Management**: Track multiple scraping jobs and their progress

## Architecture

The scraper consists of several components:

### Models (`models.py`)
- **Interaction**: Stores extracted IV→DV relationships
- **ScraperJob**: Tracks job execution and progress

### Services (`services.py`)
- **ScraperService**: Wraps the LangGraph agent and integrates with Django
- Runs in background threads to avoid blocking web requests
- Updates database in real-time as interactions are found

### Agent (`agent/`)
- **paperfinder.py**: Original LangGraph workflow
- **pubmed.py**: PubMed API wrapper
- **doi2pdf.py**: PDF download from DOI
- **interaction_storage.py**: CSV storage (not used in Django version)

### Views (`views.py`)
- `scraper_home`: Main interface
- `start_job`: API endpoint to start a scraping job
- `job_status`: API endpoint for real-time job status
- `job_interactions`: Get interactions for a specific job
- `interactions_list`: Get all interactions

## Setup

### 1. Environment Variables

Create a `.env` file with:

```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# LangChain/Nebius API (required for AI features)
NEBIUS_API_KEY=your-nebius-api-key

# Optional: Bright Data for paywalled papers
BRIGHT_WEB_UNLOCKER_KEY=your-bright-data-key
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

### 6. Access the Interface

- **Scraper Interface**: http://localhost:8000/scraper/
- **Admin Panel**: http://localhost:8000/admin/
- **Home Page**: http://localhost:8000/

## Usage

### Starting a Scraping Job

1. Go to http://localhost:8000/scraper/
2. Enter a variable of interest (e.g., "creatine", "vitamin D", "exercise")
3. Set minimum interactions to find (default: 5)
4. Click "Start Scraping"

### Monitoring Progress

The interface automatically updates every 2 seconds showing:
- Current step (query creation, PubMed search, abstract checking, etc.)
- Number of interactions found
- Number of papers checked
- Real-time log of agent actions

### Viewing Results

Interactions are displayed in a table showing:
- Independent Variable (IV): What was manipulated
- Effect: `+` (increase) or `-` (decrease)
- Dependent Variable (DV): What was measured
- Reference: DOI link to the paper

## API Endpoints

### Start Job
```http
POST /scraper/api/start/
Content-Type: application/json

{
  "variable_of_interest": "creatine",
  "min_interactions": 5
}
```

### Get Job Status
```http
GET /scraper/api/job/{job_id}/status/
```

### Get Job Interactions
```http
GET /scraper/api/job/{job_id}/interactions/
```

### Get All Interactions
```http
GET /scraper/api/interactions/
```

## Agent Workflow

The scraper follows this workflow:

1. **Query Creation**: AI generates PubMed search query
2. **PubMed Search**: Search for papers (max 100 results)
3. **Filter Papers**: Remove already-checked papers
4. **Abstract Check**: AI evaluates if paper is relevant
5. **Download Paper**: Get PDF and convert to markdown
6. **Extract Interactions**: AI extracts IV/DV/effect tuples
7. **Store to Database**: Save interactions to Django DB
8. **Loop**: Repeat until minimum interactions found

## Deployment to VPS

Since you have automatic deployment to your VPS on push to main:

### 1. Environment Setup on VPS

Make sure your VPS has:
- Python 3.9+
- PostgreSQL (recommended for production) or SQLite
- Environment variables set

### 2. Update Deployment Script

Ensure your deployment script includes:

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart gunicorn/service
sudo systemctl restart your-django-service
```

### 3. Production Settings

For production, update `.env`:

```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### 4. Background Jobs (Optional)

For production, consider using:
- **Celery** for background task processing
- **Redis** for task queue
- **Django-Q** or **Huey** as lighter alternatives

This would replace the simple threading approach used currently.

## Admin Interface

Access Django admin at `/admin/` to:
- View all scraping jobs
- Browse interactions
- Manually create/edit records
- Monitor system health

## Troubleshooting

### "LangChain dependencies not installed"
- Make sure all requirements are installed
- Check that `langchain-nebius` is properly configured

### "No open-access PDF found"
- The paper may be behind a paywall
- Agent will skip and continue to next paper
- Consider adding Bright Data API key for better access

### Job stuck in "running" state
- Check server logs for errors
- The agent may be processing a large paper
- Maximum runtime is ~20 iterations per paper

### No interactions found
- Variable may be too specific
- Try broader terms or related concepts
- AI will generate creative alternative queries

## Future Improvements

- [ ] Add Celery for proper background task handling
- [ ] Implement job cancellation
- [ ] Add network graph visualization (like original frontend)
- [ ] Export interactions to CSV/JSON
- [ ] Add paper caching to avoid re-downloading
- [ ] Implement rate limiting for API endpoints
- [ ] Add user authentication for multi-user support
- [ ] Create search/filter for interactions
- [ ] Add pagination for large result sets

## License

See project LICENSE file.


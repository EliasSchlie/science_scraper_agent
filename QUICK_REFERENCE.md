# Quick Reference - Scientific Paper Scraper

## 🔗 URLs

### Local Development
- **Home**: http://localhost:8000/
- **Scraper**: http://localhost:8000/scraper/
- **Admin**: http://localhost:8000/admin/

### Production
- **Home**: https://your-domain.com/
- **Scraper**: https://your-domain.com/scraper/
- **Admin**: https://your-domain.com/admin/

## 🚀 Common Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Testing
```bash
# Test scraper setup
python manage.py test_scraper

# Test scraper with monitoring
python manage.py test_scraper --wait

# Test with custom term
python manage.py test_scraper --variable "exercise" --min-interactions 3 --wait
```

### Database
```bash
# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Open database shell
python manage.py dbshell

# Open Django shell
python manage.py shell
```

### Deployment
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check deployment readiness
python manage.py check --deploy
```

## 📡 API Endpoints

### Start Job
```bash
curl -X POST http://localhost:8000/scraper/api/start/ \
  -H "Content-Type: application/json" \
  -d '{"variable_of_interest": "creatine", "min_interactions": 5}'
```

### Get Job Status
```bash
curl http://localhost:8000/scraper/api/job/1/status/
```

### Get Job Interactions
```bash
curl http://localhost:8000/scraper/api/job/1/interactions/
```

### Get All Interactions
```bash
curl http://localhost:8000/scraper/api/interactions/
```

## 🗄️ Database Queries

### Django Shell
```python
python manage.py shell

# Get recent jobs
from scraper.models import ScraperJob
jobs = ScraperJob.objects.all()[:5]
for job in jobs:
    print(f"{job.id}: {job.variable_of_interest} - {job.status}")

# Get recent interactions
from scraper.models import Interaction
interactions = Interaction.objects.all()[:10]
for i in interactions:
    print(f"{i.independent_variable} -> {i.dependent_variable} ({i.effect})")

# Get interactions for a specific job
job = ScraperJob.objects.get(id=1)
interactions = Interaction.objects.filter(
    created_at__gte=job.started_at,
    created_at__lte=job.completed_at
)

# Count totals
print(f"Total jobs: {ScraperJob.objects.count()}")
print(f"Total interactions: {Interaction.objects.count()}")
```

### SQL Queries
```sql
-- Total interactions
SELECT COUNT(*) FROM scraper_interaction;

-- Recent jobs
SELECT id, variable_of_interest, status, interactions_found 
FROM scraper_scraperjob 
ORDER BY started_at DESC LIMIT 10;

-- Interactions by effect
SELECT effect, COUNT(*) 
FROM scraper_interaction 
GROUP BY effect;
```

## 🔧 Troubleshooting

### Check Dependencies
```bash
pip list | grep -E "django|langchain|langgraph|pymupdf"
```

### Check Environment
```python
python manage.py shell
import os
print("NEBIUS_API_KEY:", "SET" if os.environ.get("NEBIUS_API_KEY") else "MISSING")
```

### View Logs
```bash
# Django development server logs
# (shown in terminal where runserver is running)

# Production logs (systemd)
sudo journalctl -u your-django-service -f

# Production logs (if using log file)
tail -f /path/to/logs/django.log
```

### Check Service Status
```bash
# On VPS
sudo systemctl status your-django-service
sudo systemctl restart your-django-service
```

## 📁 Important Files

### Configuration
- `config/settings.py` - Django settings
- `config/urls.py` - URL routing
- `.env` - Environment variables (not in git)
- `requirements.txt` - Python dependencies

### Scraper
- `scraper/models.py` - Database models
- `scraper/views.py` - API endpoints
- `scraper/services.py` - Background job runner
- `scraper/agent/paperfinder.py` - Main agent workflow
- `scraper/templates/scraper/home.html` - Web interface

### Documentation
- `README.md` - Main project docs
- `scraper/README.md` - Detailed scraper docs
- `SCRAPER_SETUP.md` - Quick setup guide
- `MIGRATION_GUIDE.md` - VPS deployment
- `PRE_DEPLOYMENT_CHECKLIST.md` - Pre-deploy checklist

## 🎨 UI Components

### Status Colors
- **Pending**: Yellow (#ffeaa7)
- **Running**: Blue (#74b9ff)
- **Completed**: Green (#00b894)
- **Failed**: Red (#ff7675)

### Effect Symbols
- **+**: Positive effect (increases)
- **-**: Negative effect (decreases)

## 📊 Admin Interface

### URLs
- **Jobs**: http://localhost:8000/admin/scraper/scraperjob/
- **Interactions**: http://localhost:8000/admin/scraper/interaction/

### Common Actions
1. View all jobs and their status
2. View all interactions
3. Search interactions by variable name
4. Filter jobs by status
5. Export data (use Django admin export)

## 🔐 Environment Variables

### Required
```env
SECRET_KEY=your-secret-key
NEBIUS_API_KEY=your-nebius-api-key
```

### Development
```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

### Production
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Optional
```env
BRIGHT_WEB_UNLOCKER_KEY=your-bright-data-key
```

## 🚨 Emergency Procedures

### Stop Running Job
Currently no built-in cancellation. Options:
1. Restart Django service (kills all jobs)
2. Wait for job to complete or timeout
3. Future: Add cancellation feature

### Clear All Data
```python
python manage.py shell
from scraper.models import ScraperJob, Interaction
ScraperJob.objects.all().delete()
Interaction.objects.all().delete()
```

### Reset Database
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📞 Support Resources

1. **Detailed Documentation**: See `scraper/README.md`
2. **Deployment Help**: See `MIGRATION_GUIDE.md`
3. **Setup Guide**: See `SCRAPER_SETUP.md`
4. **Pre-Deploy**: See `PRE_DEPLOYMENT_CHECKLIST.md`

## 💡 Tips & Tricks

### Faster Testing
```bash
# Use fewer interactions for quick tests
python manage.py test_scraper --variable "creatine" --min-interactions 2
```

### Monitor in Real-Time
```bash
# Watch database grow
watch -n 2 'sqlite3 db.sqlite3 "SELECT COUNT(*) FROM scraper_interaction;"'
```

### Check Latest Job
```python
python manage.py shell
from scraper.models import ScraperJob
job = ScraperJob.objects.latest('started_at')
print(f"Status: {job.status}")
print(f"Progress: {job.interactions_found}/{job.min_interactions}")
print(f"Step: {job.current_step}")
```

### Export Interactions
```python
python manage.py shell
from scraper.models import Interaction
import csv

with open('interactions.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['IV', 'DV', 'Effect', 'DOI', 'Date'])
    for i in Interaction.objects.all():
        writer.writerow([i.independent_variable, i.dependent_variable, 
                        i.effect, i.reference, i.date_published])
```

## 🎯 Common Use Cases

### Research Assistant
Search for: "intermittent fasting", "cold exposure", "meditation"

### Medical Research
Search for: "metformin", "resveratrol", "rapamycin"

### Fitness & Health
Search for: "creatine", "protein supplementation", "resistance training"

### Aging Research
Search for: "NAD+", "autophagy", "mitochondrial function"

---

**Keep this handy for quick reference!** 📌


# Migration Guide: Setting Up the Scraper on Your VPS

This guide will help you get the scientific paper scraper running on your VPS with automatic deployment.

## ✅ Prerequisites Checklist

Before deploying, ensure:
- [ ] Python 3.9+ installed on VPS
- [ ] Git configured on VPS
- [ ] Automatic deployment script set up for main branch
- [ ] Nebius API key obtained
- [ ] VPS has internet access for PubMed API

## 📝 Step-by-Step Migration

### Step 1: Prepare Local Environment

```bash
# Navigate to project
cd /path/to/andrei_django_frontend

# Create migrations for scraper app
python manage.py makemigrations scraper

# Test migrations locally
python manage.py migrate

# Test the scraper locally
python manage.py runserver
# Visit http://localhost:8000/scraper/
```

### Step 2: Configure Environment on VPS

SSH into your VPS and update/create the `.env` file:

```bash
ssh your-vps

# Navigate to your Django project directory
cd /path/to/andrei_django_frontend

# Edit .env file
nano .env
```

Add these required variables:

```env
# Existing Django settings
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# NEW: Required for scraper functionality
NEBIUS_API_KEY=your-nebius-api-key-here

# OPTIONAL: For better PDF access
BRIGHT_WEB_UNLOCKER_KEY=your-bright-data-key-if-you-have-one
```

### Step 3: Update Deployment Script

Ensure your deployment script (GitHub Actions, hook script, etc.) includes:

```bash
#!/bin/bash

# Pull latest code
git pull origin main

# Install/upgrade dependencies (important for new packages)
pip install -r requirements.txt --upgrade

# Run migrations (NEW - critical for scraper tables)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create media directory for PDFs
mkdir -p media/pdfs

# Restart your Django service
sudo systemctl restart your-django-service
# OR if using gunicorn directly:
# pkill gunicorn
# gunicorn config.wsgi:application --bind 0.0.0.0:8000 --daemon
```

### Step 4: Manual First-Time Setup on VPS

```bash
# SSH into VPS
ssh your-vps

# Navigate to project
cd /path/to/andrei_django_frontend

# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Create scraper migrations (if not in repo yet)
python manage.py makemigrations scraper

# Run all migrations
python manage.py migrate

# Create media directory
mkdir -p media/pdfs

# Restart service
sudo systemctl restart your-django-service
```

### Step 5: Verify Installation

1. **Check service is running:**
   ```bash
   sudo systemctl status your-django-service
   ```

2. **Check logs for errors:**
   ```bash
   sudo journalctl -u your-django-service -f
   ```

3. **Test the scraper:**
   - Visit: `https://your-domain.com/scraper/`
   - You should see the scraper interface
   - Try starting a test job with a simple term like "creatine"

4. **Check admin interface:**
   - Visit: `https://your-domain.com/admin/`
   - Log in with superuser
   - Verify you can see "Interactions" and "Scraper Jobs" in the admin

## 🔍 Post-Deployment Checks

### 1. Database Check

```bash
python manage.py dbshell
```

```sql
-- Check if tables exist
.tables

-- Should see:
-- scraper_interaction
-- scraper_scraperjob
```

### 2. Dependencies Check

```bash
pip list | grep -E "langchain|langgraph|pymupdf"
```

Should show:
- langchain
- langchain-core
- langchain-nebius
- langgraph
- pymupdf4llm

### 3. Environment Variables Check

```bash
python manage.py shell
```

```python
import os
print("NEBIUS_API_KEY:", "SET" if os.environ.get("NEBIUS_API_KEY") else "MISSING")
```

### 4. Permissions Check

```bash
# Ensure media directory is writable
ls -la media/
# Should show proper permissions
```

## 🚨 Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'langchain_nebius'"

**Solution:**
```bash
pip install langchain-nebius>=0.1.3
```

### Issue 2: "Table doesn't exist: scraper_scraperjob"

**Solution:**
```bash
python manage.py migrate scraper
```

### Issue 3: "No such file or directory: media/pdfs"

**Solution:**
```bash
mkdir -p media/pdfs
chmod 755 media/pdfs
```

### Issue 4: Jobs start but never complete

**Possible causes:**
- NEBIUS_API_KEY not set or invalid
- No internet access from VPS
- Firewall blocking PubMed API

**Check:**
```bash
# Test internet access
curl -I https://eutils.ncbi.nlm.nih.gov/

# Check API key
python manage.py shell
>>> import os
>>> os.environ.get('NEBIUS_API_KEY')
```

### Issue 5: Static files not loading on scraper page

**Solution:**
```bash
python manage.py collectstatic --noinput
sudo systemctl restart your-django-service
```

## 📊 Monitoring the Scraper

### View Running Jobs

```bash
python manage.py shell
```

```python
from scraper.models import ScraperJob

# Check recent jobs
jobs = ScraperJob.objects.all()[:5]
for job in jobs:
    print(f"Job {job.id}: {job.variable_of_interest} - {job.status}")
    print(f"  Found: {job.interactions_found} interactions")
    print(f"  Step: {job.current_step}")
```

### View Interactions

```bash
python manage.py shell
```

```python
from scraper.models import Interaction

# Check recent interactions
interactions = Interaction.objects.all()[:10]
for i in interactions:
    print(f"{i.independent_variable} -> {i.dependent_variable} ({i.effect})")
```

## 🔄 Future Updates

When you push updates to the scraper code:

1. **Commit and push:**
   ```bash
   git add .
   git commit -m "Update scraper functionality"
   git push origin main
   ```

2. **Automatic deployment should:**
   - Pull latest code
   - Install dependencies
   - Run migrations
   - Restart service

3. **Manual check (if needed):**
   ```bash
   ssh your-vps
   cd /path/to/project
   sudo systemctl status your-django-service
   ```

## 🎯 Testing After Deployment

### Quick Test Checklist

- [ ] Visit `/scraper/` - page loads
- [ ] Start a test job with "creatine"
- [ ] See real-time progress updates
- [ ] Job completes successfully
- [ ] Interactions appear in table
- [ ] Can view job in `/admin/`
- [ ] Can see interactions in `/admin/`

### Load Test (Optional)

Start multiple jobs concurrently to ensure stability:

```python
# In Django shell
from scraper.models import ScraperJob
from scraper.services import start_scraper_job_async

# Create and start multiple jobs
for term in ['creatine', 'vitamin D', 'exercise']:
    job = ScraperJob.objects.create(
        variable_of_interest=term,
        min_interactions=3
    )
    start_scraper_job_async(job.id)
```

## 📞 Getting Help

If you encounter issues:

1. **Check logs:**
   ```bash
   sudo journalctl -u your-django-service -n 100
   ```

2. **Check Django errors:**
   ```bash
   tail -f /path/to/logs/django.log  # if you have logging configured
   ```

3. **Test components individually:**
   ```bash
   python manage.py shell
   ```
   ```python
   # Test PubMed API
   from scraper.agent.pubmed import PubMedAPI
   api = PubMedAPI()
   papers = api.search("creatine", max_results=5)
   print(len(papers))
   
   # Test LLM
   from langchain_nebius import ChatNebius
   llm = ChatNebius(model="moonshotai/Kimi-K2-Instruct")
   response = llm.invoke("Hello")
   print(response.content)
   ```

## ✅ Success Indicators

You know everything is working when:

1. ✅ Scraper interface loads at `/scraper/`
2. ✅ Jobs start and show "running" status
3. ✅ Progress log updates in real-time
4. ✅ Interactions appear in the table
5. ✅ Jobs complete with "completed" status
6. ✅ PDF files appear in `media/pdfs/`
7. ✅ Admin interface shows all data

## 🎉 You're Done!

Your scientific paper scraper is now live and accessible at:
`https://your-domain.com/scraper/`

Share it, use it, and watch the AI discover causal relationships from scientific literature!


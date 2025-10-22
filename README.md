# Django Project with Scientific Paper Scraper

A Django web application with automatic VPS deployment featuring a scientific paper scraper agent that extracts causal interactions from research papers.

## 🚀 Features

### Core Application
- Auto-deployment to VPS on push to main branch
- Modern Django 5.2+ setup
- WhiteNoise for static file serving
- Gunicorn for production serving

### Scientific Paper Scraper (`/scraper/`)
- 🔍 AI-powered PubMed search query generation
- 📄 Automatic PDF download from open-access sources
- 🤖 LLM-based extraction of causal relationships
- 📊 Real-time progress monitoring with beautiful web UI
- 💾 Database storage of all interactions
- 🎨 Modern gradient-based UI design

## 📋 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd andrei_django_frontend
pip install -r requirements.txt
```

### 2. Environment Setup

Create `.env` file:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Required for scraper
NEBIUS_API_KEY=your-nebius-api-key

# Optional
BRIGHT_WEB_UNLOCKER_KEY=your-bright-data-key
```

### 3. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

### 5. Access the Application

- **Home**: http://localhost:8000/
- **Scraper**: http://localhost:8000/scraper/
- **Admin**: http://localhost:8000/admin/

## 🔬 Scraper Usage

1. Navigate to http://localhost:8000/scraper/
2. Enter a variable of interest (e.g., "creatine", "exercise", "vitamin D")
3. Set minimum interactions to find
4. Click "Start Scraping"
5. Watch the AI agent work in real-time!

### What the Scraper Does

The agent automatically:
1. Generates intelligent PubMed search queries
2. Finds relevant scientific papers
3. Checks if papers are intervention studies
4. Downloads open-access PDFs
5. Extracts causal relationships (IV → DV)
6. Stores interactions in the database

### Example Output

| Independent Variable | Effect | Dependent Variable | Reference |
|---------------------|--------|-------------------|-----------|
| Creatine supplementation | + | Muscle mass | DOI: 10.xxx |
| Exercise | - | Blood pressure | DOI: 10.yyy |

## 📁 Project Structure

```
andrei_django_frontend/
├── config/              # Django settings
├── core/                # Core app
├── scraper/             # Scientific paper scraper
│   ├── agent/          # LangGraph agent code
│   ├── templates/      # Web interface
│   ├── models.py       # Database models
│   ├── views.py        # API & views
│   ├── services.py     # Background agent runner
│   └── README.md       # Detailed scraper docs
├── scraper-agent-code/ # Original Python implementation
├── manage.py
├── requirements.txt
└── README.md          # This file
```

## 🚀 Deployment

### Automatic Deployment to VPS

This project is configured for automatic deployment when you push to the main branch.

### Pre-deployment Checklist

1. ✅ Set environment variables on VPS (especially `NEBIUS_API_KEY`)
2. ✅ Ensure Python 3.9+ is installed
3. ✅ Configure your deployment script to run migrations
4. ✅ Set `DEBUG=False` in production
5. ✅ Configure proper `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`

### Deployment Commands (on VPS)

```bash
# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart service
sudo systemctl restart your-django-service
```

## 🛠️ Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Django Shell

```bash
python manage.py shell
```

## 📚 Documentation

- **Scraper Detailed Docs**: See `scraper/README.md`
- **Quick Setup**: See `SCRAPER_SETUP.md`

## 🔧 Configuration

### Required Environment Variables

```env
SECRET_KEY          # Django secret key
DEBUG               # True/False
ALLOWED_HOSTS       # Comma-separated hostnames
NEBIUS_API_KEY      # For AI functionality (required for scraper)
```

### Optional Environment Variables

```env
CSRF_TRUSTED_ORIGINS      # Comma-separated URLs
BRIGHT_WEB_UNLOCKER_KEY   # For paywalled papers
```

## 🗄️ Database

Default: SQLite (`db.sqlite3`)

For production, consider PostgreSQL:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🐛 Troubleshooting

### Scraper Not Working

**"LangChain dependencies not installed"**
- Run: `pip install -r requirements.txt`
- Ensure `langchain-nebius>=0.1.3` is installed

**"No module named 'langchain_nebius'"**
- Check that NEBIUS_API_KEY is set
- Verify package installation

### Deployment Issues

**Static files not loading**
- Run: `python manage.py collectstatic`
- Check WhiteNoise configuration

**Database errors**
- Ensure migrations are run: `python manage.py migrate`
- Check database permissions

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Push to main for auto-deployment

## 🔗 Links

- **Admin Panel**: `/admin/`
- **Scraper Interface**: `/scraper/`
- **API Endpoints**: `/scraper/api/`

## ⚡ Tech Stack

- **Backend**: Django 5.2+
- **AI**: LangChain, LangGraph, Nebius
- **Database**: SQLite (dev), PostgreSQL (production recommended)
- **Deployment**: Gunicorn, WhiteNoise
- **Frontend**: Vanilla JS, CSS3 (no framework needed)
- **PDF Processing**: PyMuPDF4LLM
- **APIs**: PubMed, Unpaywall, arXiv

## 🎯 Future Enhancements

- [ ] Add Celery for better background task handling
- [ ] Implement job cancellation
- [ ] Add network graph visualization
- [ ] Export functionality (CSV, JSON)
- [ ] User authentication
- [ ] Search and filter interactions
- [ ] Pagination for large datasets
- [ ] Email notifications on job completion

---

Built with ❤️ using Django and AI


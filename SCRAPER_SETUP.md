# Quick Setup Guide for Scientific Paper Scraper

## Prerequisites

1. Python 3.9 or higher
2. All dependencies from `requirements.txt`
3. Nebius API key for LangChain

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Add to your `.env` file:

```env
# Required for scraper AI functionality
NEBIUS_API_KEY=your-nebius-api-key-here

# Optional for better PDF access
BRIGHT_WEB_UNLOCKER_KEY=your-bright-data-key
```

### 3. Run Migrations

```bash
python manage.py makemigrations scraper
python manage.py migrate
```

### 4. Create Superuser (if not already done)

```bash
python manage.py createsuperuser
```

### 5. Start Server

```bash
python manage.py runserver
```

### 6. Access the Scraper

Open your browser to: **http://localhost:8000/scraper/**

## Usage Example

1. Enter a search term like "creatine" or "vitamin D"
2. Set minimum interactions (default: 5)
3. Click "Start Scraping"
4. Watch the agent work in real-time!
5. View discovered interactions in the table below

## What It Does

The scraper agent:
1. 🔍 Generates smart PubMed queries using AI
2. 📚 Searches for relevant scientific papers
3. 🤖 Checks if papers are intervention studies on humans
4. 📄 Downloads open-access PDFs
5. 🔬 Extracts causal relationships (IV → DV)
6. 💾 Stores everything in the database
7. 🔄 Continues until target number of interactions found

## Example Output

Each interaction shows:
- **Independent Variable**: What was changed (e.g., "Creatine supplementation")
- **Effect**: `+` means increases, `-` means decreases
- **Dependent Variable**: What was measured (e.g., "Muscle mass")
- **Reference**: DOI link to the source paper

## Deployment

Since you have auto-deployment to VPS:

1. Push to main branch
2. Ensure `.env` on VPS has `NEBIUS_API_KEY`
3. Make sure migrations run: `python manage.py migrate`
4. Restart your Django service

## Accessing on VPS

Once deployed, access at:
- `https://your-domain.com/scraper/`
- `https://your-domain.com/admin/` (to view/manage data)

## Troubleshooting

**"LangChain dependencies not installed"**
- Run: `pip install -r requirements.txt`

**"ModuleNotFoundError: No module named 'langchain_nebius'"**
- Ensure `langchain-nebius>=0.1.3` is installed
- Check that NEBIUS_API_KEY is set in environment

**Jobs not running**
- Check server console for errors
- Verify NEBIUS_API_KEY is valid
- Ensure internet access for PubMed API

## Admin Access

View all data at `/admin/`:
- **Interactions**: Browse all IV→DV relationships
- **Scraper Jobs**: Monitor job history and status

## Notes

- Downloads are stored in `media/pdfs/` directory
- Each job runs in a background thread
- Real-time updates via polling every 2 seconds
- Open-access papers only (unless Bright Data key provided)

## Need Help?

Check the detailed documentation at `scraper/README.md`


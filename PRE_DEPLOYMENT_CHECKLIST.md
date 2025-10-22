# Pre-Deployment Checklist

Before pushing to your VPS, complete these steps:

## 🔧 Local Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
- [ ] All packages installed without errors
- [ ] `langchain-nebius` version >= 0.1.3

### 2. Environment Variables
Create/update `.env` file:
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
NEBIUS_API_KEY=your-nebius-api-key
```
- [ ] `.env` file created
- [ ] `NEBIUS_API_KEY` obtained and added
- [ ] All variables set correctly

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
- [ ] Migrations created successfully
- [ ] Database migrated
- [ ] Superuser created
- [ ] `scraper_interaction` table exists
- [ ] `scraper_scraperjob` table exists

### 4. Test Locally
```bash
python manage.py runserver
```
Visit http://localhost:8000/scraper/

- [ ] Server starts without errors
- [ ] Scraper page loads
- [ ] Can create a test job
- [ ] Job runs and shows progress
- [ ] Interactions appear in table
- [ ] Admin interface accessible
- [ ] Can view jobs and interactions in admin

### 5. Run Test Command (Optional)
```bash
python manage.py test_scraper --wait
```
- [ ] All tests pass
- [ ] Test job completes successfully

## 🚀 VPS Preparation

### 1. Environment Variables on VPS
SSH into your VPS and update `.env`:

```env
SECRET_KEY=different-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
NEBIUS_API_KEY=your-nebius-api-key
```

- [ ] SSH access to VPS confirmed
- [ ] `.env` file updated on VPS
- [ ] `DEBUG=False` for production
- [ ] `ALLOWED_HOSTS` set correctly
- [ ] `CSRF_TRUSTED_ORIGINS` includes https://
- [ ] `NEBIUS_API_KEY` set on VPS

### 2. Update Deployment Script
Ensure your deployment script includes:

```bash
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput
mkdir -p media/pdfs
sudo systemctl restart your-django-service
```

- [ ] Deployment script updated
- [ ] Includes `pip install -r requirements.txt`
- [ ] Includes `python manage.py migrate`
- [ ] Creates media directory
- [ ] Restarts Django service

### 3. File Permissions
On VPS, ensure:
```bash
mkdir -p media/pdfs
chmod 755 media/pdfs
```
- [ ] Media directory exists
- [ ] Proper permissions set

## 📋 Code Review

### Files to Commit
- [ ] `scraper/` app directory (all files)
- [ ] `config/settings.py` (updated)
- [ ] `config/urls.py` (updated)
- [ ] `requirements.txt` (updated)
- [ ] `README.md` (new)
- [ ] `SCRAPER_SETUP.md` (new)
- [ ] `MIGRATION_GUIDE.md` (new)
- [ ] `.gitignore` (updated with media/)

### Files to NOT Commit
- [ ] `.env` (should be in .gitignore)
- [ ] `db.sqlite3` (should be in .gitignore)
- [ ] `media/` (should be in .gitignore)
- [ ] `__pycache__/` (should be in .gitignore)

## 🧪 Final Tests

### Test Checklist
Run through this sequence:

1. **Fresh Start**
   ```bash
   rm db.sqlite3
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```
   - [ ] Works from scratch

2. **Basic Functionality**
   - [ ] Visit `/scraper/`
   - [ ] Start job with "creatine"
   - [ ] See real-time updates
   - [ ] Job completes
   - [ ] Interactions saved

3. **Admin Interface**
   - [ ] Login to `/admin/`
   - [ ] See Scraper Jobs
   - [ ] See Interactions
   - [ ] Can edit/delete

4. **API Endpoints**
   - [ ] POST `/scraper/api/start/` works
   - [ ] GET `/scraper/api/job/<id>/status/` works
   - [ ] GET `/scraper/api/interactions/` works

## 🔐 Security Check

- [ ] `DEBUG=False` in production `.env`
- [ ] `SECRET_KEY` is different in production
- [ ] `.env` file is in `.gitignore`
- [ ] No API keys in committed code
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] `CSRF_TRUSTED_ORIGINS` uses https://

## 📊 Documentation

- [ ] `README.md` explains the project
- [ ] `scraper/README.md` explains scraper details
- [ ] `SCRAPER_SETUP.md` has quick start guide
- [ ] `MIGRATION_GUIDE.md` has VPS setup steps
- [ ] Code is commented where needed

## 🎯 Deployment Steps

When ready to deploy:

### 1. Commit Changes
```bash
git add .
git status  # Review what will be committed
git commit -m "Add scientific paper scraper Django app"
```
- [ ] Reviewed files to be committed
- [ ] No sensitive data in commit
- [ ] Commit message is clear

### 2. Push to Main
```bash
git push origin main
```
- [ ] Push successful
- [ ] Automatic deployment triggered

### 3. Monitor Deployment
- [ ] Check VPS deployment logs
- [ ] Verify service restarted
- [ ] Check for errors

### 4. Verify on VPS
Visit your domain:
- [ ] `https://your-domain.com/scraper/` loads
- [ ] Can start a test job
- [ ] Job runs successfully
- [ ] Admin interface works

### 5. Post-Deployment Test
```bash
ssh your-vps
cd /path/to/project
python manage.py test_scraper --variable "vitamin D" --min-interactions 2 --wait
```
- [ ] Test completes successfully
- [ ] Interactions found
- [ ] No errors in logs

## 🚨 Rollback Plan

If something goes wrong:

### Quick Rollback
```bash
ssh your-vps
cd /path/to/project
git checkout HEAD~1  # Go back one commit
pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart your-django-service
```

### Nuclear Option
1. Remove scraper app from `INSTALLED_APPS`
2. Comment out scraper URL in `config/urls.py`
3. Restart service
4. System works without scraper

## ✅ Final Verification

Before marking as complete:

- [ ] Scraper works locally
- [ ] All dependencies installed
- [ ] Documentation complete
- [ ] Tests pass
- [ ] Code committed
- [ ] `.env` configured on VPS
- [ ] Deployment script updated
- [ ] Ready to push to main

## 🎉 Ready to Deploy!

Once all items are checked:
1. Review one final time
2. Push to main
3. Monitor deployment
4. Test on production
5. Celebrate! 🎊

---

**Important Notes:**
- The scraper uses background threading (simple but works)
- For heavy production use, consider Celery + Redis
- PDFs are stored in `media/pdfs/` (not in git)
- Each job runs independently
- Real-time updates via 2-second polling

**Support:**
- See `MIGRATION_GUIDE.md` for troubleshooting
- Check `scraper/README.md` for detailed docs
- Review Django logs for errors


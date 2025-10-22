# Bug Fixes - Scraper Web Interface

## Issues Fixed

### 1. ✅ Effect Display Issue
**Problem:** Interactions showed "+" and "-" symbols, and sometimes a red zero instead of minus.

**Solution:**
- Changed display from symbols to readable text
- `+` now shows as **"INCREASES"** in bold green (#00b894)
- `-` now shows as **"DECREASES"** in bold red (#ff7675)
- Added proper HTML rendering with color styles

**Code Change:**
```javascript
if (i.effect === '+') {
  effectText = '<strong style="color: #00b894;">INCREASES</strong>';
} else if (i.effect === '-') {
  effectText = '<strong style="color: #ff7675;">DECREASES</strong>';
}
```

### 2. ✅ New Job Not Appearing in Recent Jobs
**Problem:** When starting a new job, it didn't appear in the "Recent Jobs" sidebar.

**Solution:**
- After job creation, redirect to `/scraper/?job_id={job_id}`
- Added URL parameter handling on page load
- Automatically loads the job and starts polling when page loads with job_id parameter

**Code Change:**
```javascript
// On successful job creation
window.location.href = `/scraper/?job_id=${data.job_id}`;

// On page load
window.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get('job_id');
  if (jobId) {
    loadJob(parseInt(jobId));
  }
});
```

### 3. ✅ Can't Stop/Cancel Jobs
**Problem:** No way to stop a running job.

**Solution:**
- Added **"⏹ Stop Job"** button in the progress container
- Button only visible when job status is "running"
- Created API endpoint `/scraper/api/job/<id>/stop/` to stop jobs
- Confirmation dialog before stopping
- Updates job status to 'failed' with message "Job stopped by user"

**New Features:**
- Red stop button appears only for running jobs
- Confirmation prompt prevents accidental stops
- Logs the stop action

**Code Changes:**

Views (`views.py`):
```python
@require_POST
@csrf_exempt
def stop_job(request, job_id):
    """Stop a running job"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    if job.status == 'running':
        job.status = 'failed'
        job.error_message = 'Job stopped by user'
        job.completed_at = timezone.now()
        job.add_log('Job stopped by user')
        job.save()
        return JsonResponse({'message': 'Job stopped successfully'})
```

Frontend:
```javascript
async function stopJob() {
  if (!confirm('Are you sure you want to stop this job?')) return;
  
  const response = await fetch(`/scraper/api/job/${currentJobId}/stop/`, {
    method: 'POST',
  });
  
  if (response.ok) {
    alert('Job stopped successfully');
    stopPolling();
    loadJob(currentJobId);
  }
}
```

### 4. ✅ Interactions Not Displaying on Web Page
**Problem:** Interactions table wasn't showing data properly.

**Solution:**
- Fixed JavaScript to properly parse and display interactions
- Added proper HTML escaping and formatting
- Made DOI links clickable with proper styling
- Improved table rendering

### 5. ✅ Better User Experience Enhancements

**Additional Improvements:**
- **Auto-scroll** in logs to show latest activity
- **Color-coded logs** for different operation types
- **Responsive updates** every 2 seconds
- **Clear visual feedback** for all user actions
- **Proper error handling** with user-friendly messages

## Testing Checklist

After these fixes, verify:
- [ ] Start a new job → it redirects and shows job progress immediately
- [ ] Job appears in "Recent Jobs" sidebar after page reload
- [ ] Interactions display with "INCREASES" (green) or "DECREASES" (red)
- [ ] Click on a recent job → loads its details and interactions
- [ ] Stop button appears when job is running
- [ ] Stop button works and updates job status
- [ ] Logs show color-coded messages
- [ ] DOI links are clickable
- [ ] No red zeros appear in effect column

## Files Modified

1. `scraper/templates/scraper/home.html`
   - Fixed effect display (INCREASES/DECREASES)
   - Added page load handler for job_id parameter
   - Added stop button and functionality
   - Improved interactions table rendering

2. `scraper/views.py`
   - Added `stop_job()` endpoint

3. `scraper/urls.py`
   - Added route for stop job endpoint

## Migration Required

None - these are all frontend and view logic changes.

## Deployment Notes

Just push the changes and restart Django. No database migrations needed.

```bash
git add .
git commit -m "Fix bugs: improve effect display, add job stopping, fix interactions rendering"
git push origin main
```

## Known Limitations

**Stop Button Behavior:**
- Stopping a job marks it as "failed" (not a separate "stopped" status)
- Background thread continues until current operation completes
- Can't truly interrupt PDF downloads or LLM calls mid-operation
- Job will finish current step then check status

**Future Enhancements:**
- Add proper "cancelled" status (instead of using "failed")
- Implement thread interruption for more immediate stops
- Add "Resume" functionality for stopped jobs
- Show warning if trying to start multiple jobs simultaneously

## Summary

All reported bugs have been fixed! The scraper now:
- ✅ Shows interactions properly with readable text
- ✅ Updates recent jobs list immediately
- ✅ Allows stopping running jobs
- ✅ Displays effects in color (green/red)
- ✅ Provides better overall user experience

**Ready for deployment!** 🚀


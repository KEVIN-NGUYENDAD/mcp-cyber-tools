# Troubleshooting Guide

## Common Issues & Solutions

### Render Deployment Not Working

**Symptom**: Push code but production doesn't update

**Diagnosis**:
1. Check GitHub has your commit: `git log --oneline -5`
2. Check Render dashboard to see last build time
3. Check if webhook is configured

**Solution**:
1. Try different branch (develop vs production)
2. Update render.yaml and push
3. Manually trigger build in Render dashboard
4. Check Render service status
5. Switch to alternative platform (Vercel, Railway)

**Current Status**: Render auto-deploy is completely broken (Sept 7)

---

### Dashboard Shows Old Data

**Symptom**: Dashboard hasn't updated in hours

**Cause**: state/*.json files not updated

**Solution**:
```bash
# Update state files with current data
# Edit state/assets.json, state/incidents.json, etc.
# Change "timestamp" field to current time
git add state/
git commit -m "Update state files"
git push
```

---

### Console Shows [RENDER] Logs but Not [WARN]

**Symptom**: renderOverviewPage() is called but renderIncidentBoard() is not

**Cause**: Data guard condition failing

**Debug**:
```javascript
// Add to renderOverviewPage():
console.log('[DEBUG] stateData:', {
  assets: stateData.assets ? 'OK' : 'NULL',
  incidents: stateData.incidents ? 'OK' : 'NULL',
  risk: stateData.risk ? 'OK' : 'NULL'
});
```

**Solution**:
- Verify loadAllData() successfully fetches all data
- Check /api/state/* endpoints return data
- Make sure state/*.json files exist and are valid JSON

---

### Executive Scorecard Shows "UNKNOWN" (C-001)

**Symptom**: Risk score element shows "UNKNOWN" instead of "74/100"

**Cause**: renderExecutiveScorecard() updating wrong elements or data is null

**Fix**:
1. Check element IDs in HTML match code
2. Verify stateData.risk has required fields
3. Debug renderExecutiveScorecard() function

---

### Incident Board Empty (C-003)

**Symptom**: #incident-board div is empty (no cards)

**Cause**: renderIncidentBoard() not generating HTML

**Debug**:
```javascript
// In renderIncidentBoard():
console.log('[DEBUG] Creating incident cards for:', stateData.incidents.total_incidents);
console.log('[DEBUG] First incident:', stateData.incidents.incidents[0]);
```

**Solution**:
- Verify incidents.json has valid data
- Check HTML generation code
- Ensure DOM insertion is correct

---

### Timeline Empty (C-004)

**Symptom**: #timeline div is empty (no events)

**Cause**: renderTimeline() not generating HTML

**Debug**:
```javascript
// In renderTimeline():
console.log('[DEBUG] Creating timeline for:', stateData.incidents.length, 'events');
```

**Solution**:
- Verify data source has events
- Check HTML generation
- Inspect DOM after rendering

---

### Data Freshness Shows "STALE"

**Symptom**: "2154 min" instead of "1 min"

**Cause**: Using file timestamp instead of fetch time

**Solution**: 
- Server should send `_fetched_at` in response
- Client should use `_fetched_at` not `timestamp`

---

### Vulnerability Distribution Wrong

**Symptom**: 0+0+4+9=13 but total=385

**Cause**: Missing "Info" severity count

**Solution**:
- Add infoVulns = total - critical - high - medium - low
- Display all 5 levels (critical, high, medium, low, info)

---

### MCP Shows OFFLINE Instead of ACTIVE

**Symptom**: MCP Intelligence shows "OFFLINE" status

**Cause**: stateData.mcp not initialized

**Solution**:
```javascript
// In loadAllData():
stateData.mcp = {
  status: 'ONLINE',
  tool_count: '90+',
  threat_hunting_active: true,
  dfir_active: true
};
```

---

### Page Loading Forever

**Symptom**: Page stuck on loading, doesn't render

**Cause**: loadAllData() hanging on API call

**Solution**:
1. Check if /api/state/* endpoints respond
2. Add timeout to fetch calls
3. Use fetch polyfill if needed
4. Check network in F12 DevTools

---

## Debugging Workflow

### Step 1: Check Console
```
F12 → Console tab
Look for [INIT], [DATA], [RENDER], [WARN] logs
```

### Step 2: Check Network
```
F12 → Network tab
Look for /api/state/* requests
Verify they return 200 status
Check response data
```

### Step 3: Check Elements
```
F12 → Elements tab
Find #incident-board, #timeline, #score-risk
Check if they have innerHTML content
Look for empty elements
```

### Step 4: Check Git
```
git status           # See uncommitted changes
git log -5           # See recent commits
git diff             # See what changed
```

### Step 5: Check Render
```
Visit Render dashboard
Check last build time
Look for build errors
Check service status
```

---

## Testing Fixes

After editing code:

1. **Local test** (if possible):
   ```bash
   npm start
   # Open localhost:3000
   # Check console for logs
   ```

2. **Commit**:
   ```bash
   git add web/app.js
   git commit -m "Fix C-001: Executive Scorecard"
   git push origin develop
   ```

3. **Wait for deploy**:
   - Render should build and deploy
   - Check Render dashboard for progress
   - Takes 2-5 minutes typically

4. **Verify in production**:
   ```
   Visit https://sentinelops-soc.onrender.com
   F12 → Console
   F12 → Elements
   Verify fix worked
   ```

---

## When Nothing Works

### Nuclear Options

1. **Clear browser cache**:
   - F12 → Application tab → Clear site data
   - Hard refresh: Ctrl+Shift+R

2. **Check branch**:
   ```bash
   git branch -a
   git status
   ```

3. **Force redeploy**:
   - Go to Render dashboard
   - Click "Trigger Deploy"
   - Wait for build

4. **Try alternate branch**:
   ```bash
   git checkout -b production
   git push origin production
   # Update render.yaml to use production
   ```

5. **Last resort - redeploy elsewhere**:
   - Use Vercel, Railway, or Heroku
   - Push code to new platform
   - Update render.yaml for new URL

---

**Note**: Currently (Sept 7), Render deployment is completely broken. Option 5 may be necessary.

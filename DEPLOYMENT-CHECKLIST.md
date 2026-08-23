# DEPLOYMENT CHECKLIST

**Date:** 2026-08-23  
**ICs:** IC-035, IC-036, IC-041  
**Status:** Ready for deployment

---

## MACHINE A: DESKTOP DEPLOYMENT

### Prerequisites
```
- Windows 10 or later
- PowerShell 5.0+
- Node.js 14+
- npm 6+
- ~50MB disk space
- Internet connectivity (for npm packages)
```

### Install Steps

**Step 1: Clone/Pull Latest Code**
```bash
cd mcp-cyber-tools
git pull origin learning-factory-v2
```

**Step 2: Install Dependencies**
```bash
npm install
```

**Step 3: Verify Telemetry Directory**
```bash
mkdir -p telemetry
```

**Step 4: Verify Modules Loaded**
```bash
npm run check:tools
```

**Step 5: Start Telemetry**
```bash
node scripts/daily-intelligence.js
```

### Verification Steps

**Verify Installation**
```powershell
# Should return no errors
node -e "const shared = require('./modules/shared.js'); console.log('✓ Modules load')"
```

**Verify Telemetry**
```bash
# Should create telemetry-YYYY-MM-DD.json
ls telemetry/ 
```

**Verify Event Log Functions**
```powershell
# Test failedLogons (Event ID 4625)
powershell -Command "Import-Module .\modules\shared.js; Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 5"
```

**Verify Registry Caching**
```powershell
# Test registry access
powershell -Command "Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion"
```

### Rollback Steps

**If deployment fails:**
```bash
git reset --hard origin/learning-factory-v2
npm install
# Return to previous known state
```

---

## MACHINE B: LAPTOP DEPLOYMENT

### Prerequisites (Same as Desktop)
```
- Windows 10 or later
- PowerShell 5.0+
- Node.js 14+
- npm 6+
```

### Install Steps (Same as Desktop)

**Unique consideration for Laptop:**
```
- May have lower permissions (non-admin)
- securityLog may fallback gracefully
- Registry queries will use fallback paths
- This is expected behavior (IC-041 handles it)
```

### Verification Steps

**Test with Limited Permissions**
```powershell
# Should still work (IC-041 fallback)
powershell -Command "Get-EventLog -LogName Application -Newest 5"
```

**Verify Fallback Works**
```powershell
# If Security log fails, Application log should work
powershell -Command "Import-Module .\modules\shared.js; queryEventLogWithFallback('Security', 4625)"
```

### Rollback Steps (Same as Desktop)

---

## MACHINE C: CLIENT DEPLOYMENT

### Prerequisites
```
- Remote client access to Machine A/B
- Read-only telemetry access
- Network connectivity
```

### Install Steps

**Option 1: SSH/Remote Access**
```bash
ssh user@machine-a.local
cd mcp-cyber-tools
git pull origin learning-factory-v2
npm run intelligence:daily
```

**Option 2: Telemetry Only**
```bash
# Copy telemetry files from Machine A
scp user@machine-a.local:~/mcp-cyber-tools/telemetry/* ./telemetry/

# Run local analysis
node scripts/telemetry-analytics.js
```

### Verification Steps

**Verify Remote Access**
```bash
ssh user@machine-a.local "cd mcp-cyber-tools && npm run intelligence:daily"
```

**Verify Telemetry Sync**
```bash
# Should show recent telemetry files
ls -lt telemetry/ | head -5
```

### Rollback Steps

**If remote connection fails:**
```bash
# Reset to known good state
git reset --hard
ssh user@machine-a.local "cd mcp-cyber-tools && git reset --hard origin/learning-factory-v2"
```

---

## DEPLOYMENT VALIDATION MATRIX

| Check | Machine A | Machine B | Machine C | Status |
|-------|-----------|-----------|-----------|--------|
| Code pulls | ✓ | ✓ | ✓ | Ready |
| Dependencies install | ✓ | ✓ | ✓ | Ready |
| Telemetry initializes | ✓ | ✓ | ✓ | Ready |
| Event log works | ✓ | ✓ (fallback) | ✓ | Ready |
| Registry works | ✓ | ✓ | ✓ | Ready |
| Caching functions | ✓ | ✓ | ✓ | Ready |
| Fallback works | ✓ | ✓ | ✓ | Ready |

---

## EXPECTED BEHAVIOR

### IC-035: Event Log Standardization
- failedLogons should return results without syntax errors
- successfulLogons should return results without syntax errors
- loggedOnUsers should return results without syntax errors

### IC-036: Registry Caching
- First run: 8-10 seconds (cold-start)
- Second run: <100ms (cached)
- Clear cache and rerun: 8-10 seconds again

### IC-041: Reliability Improvement
- securityLog on admin machine: succeeds with Security log
- securityLog on non-admin machine: succeeds with fallback (Application)
- All queries include retry logic (2 attempts with backoff)

---

## DEPLOYMENT COMPLETE CRITERIA

All three machines must have:
- ✅ Latest code (learning-factory-v2 branch)
- ✅ Dependencies installed (npm install)
- ✅ Telemetry running (daily-intelligence.js active)
- ✅ No deployment errors
- ✅ All verification steps pass
- ✅ Telemetry files being created (telemetry/*.json)

---

## NEXT STEPS

After deployment verification:
1. Run BENCHMARK-RUNNER.js
2. Execute FIELD-TEST-PACK.md scenarios
3. Validate telemetry with TELEMETRY-VALIDATOR.js
4. Calculate ROI with ROI-CALCULATOR.js

**Estimated time to ready:** 30 minutes per machine

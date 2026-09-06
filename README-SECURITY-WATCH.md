# Security Watch - 72 Hour POC

Minimal security monitoring. Detects 5 critical control changes. Alerts in <60 seconds. No spam.

## Quick Start (5 minutes)

```powershell
# 1. Set Gmail App Password (one time)
[Environment]::SetEnvironmentVariable("GMAIL_APP_PASSWORD", "xxxx-xxxx-xxxx-xxxx", "User")
[Environment]::SetEnvironmentVariable("EMAIL_USER", "tamngankevin@gmail.com", "User")

# Restart PowerShell to load variables

# 2. Install dependency
npm install nodemailer

# 3. Run
node security-watch.js

# First run: Approve baseline when prompted
```

## What It Monitors

| Detection | Change | Alert |
|-----------|--------|-------|
| DNS Change | DNS servers modified | < 60 seconds |
| Firewall Disabled | Windows Firewall turned off | < 60 seconds |
| Defender Disabled | Real-time protection off | < 60 seconds |
| RDP Enabled | Port 3389 listening | < 60 seconds |
| SSH Enabled | Port 22 listening | < 60 seconds |

## How It Works

1. **Baseline Approval** (first run)
   - Scan current security state
   - Show values to user
   - Require approval before monitoring starts
   - Save to `baseline.json` (read-only)

2. **Continuous Monitoring** (every 30 seconds)
   - Check 5 security controls
   - Compare against baseline
   - If change detected → send alert email

3. **Alert Cooldown** (4 hours)
   - Same alert cannot email twice within 4 hours
   - Prevents spam from persistent threats
   - Silently logs duplicate detections

4. **Heartbeat** (every 12 hours)
   - "✅ Security Watch Alive" email
   - Proves monitoring process is running
   - If missing = monitoring crashed

## Files Created

| File | Purpose |
|------|---------|
| `baseline.json` | Golden state (created on approval, never auto-updated) |
| `state.json` | Current state (updated every 30s) |
| `cooldown.json` | Alert cooldown tracking |
| `security-watch.js` | Main monitoring script (360 lines) |

## Get Gmail App Password

Required for email alerts.

1. Go to: https://myaccount.google.com/security
2. Find: **App passwords** (or 2-Step Verification first if needed)
3. Select: **Mail** + **Windows Computer**
4. Copy: 16-character password
5. Set environment variable:
   ```powershell
   [Environment]::SetEnvironmentVariable("GMAIL_APP_PASSWORD", "your-16-char-password", "User")
   ```

## Reset Baseline

To create a new baseline (clear cached state):

```powershell
# Delete baseline
Remove-Item baseline.json

# Restart monitoring
node security-watch.js

# Approve new baseline when prompted
```

## Troubleshooting

**"No baseline found" message**
- Run `node security-watch.js` to create baseline
- Approve when prompted

**No alerts arriving**
- Check `state.json` is updating every 30s
- Verify Gmail password is correct
- Test: Turn off Firewall manually, wait 60s

**Email delivery delayed**
- Check Gmail app password is valid
- Verify network connectivity
- Check spam folder

**Heartbeat missing after 12 hours**
- Monitoring process crashed
- Check console output
- Restart: `node security-watch.js`

**PowerShell errors**
- Run PowerShell as Administrator
- Enable execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

## 72-Hour Test

Success criteria:
- ✅ No crashes
- ✅ Detects all 5 changes
- ✅ Alert arrives < 60 seconds
- ✅ No email spam (cooldown works)
- ✅ Heartbeat every 12 hours
- ✅ Baseline never auto-corrupted

Use `test-checklist.md` to validate each detection.

## After 72 Hours

**If all tests pass**: Ready to expand with more detections

**If issues found**: Debug and fix before expanding

**Do NOT add features until 72-hour test completes**

## Files

- `security-watch.js` - Main script (production ready)
- `README-SECURITY-WATCH.md` - This file
- `test-checklist.md` - 72-hour validation tests
- `package.json` - Dependencies (nodemailer only)

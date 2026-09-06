# Security Watch - 72 Hour Test Checklist

Complete validation checklist for 72-hour production test.

---

## Pre-Test Setup

- [ ] `npm install nodemailer` completed
- [ ] Gmail App Password set via environment variable
- [ ] EMAIL_USER set via environment variable
- [ ] PowerShell restarted (to load env vars)
- [ ] `node security-watch.js` runs without errors
- [ ] Baseline approved on first run
- [ ] First heartbeat email received

**Test Start Date**: ___________  
**Test End Date**: ___________  
**Tester Name**: ___________

---

## Detection Test 1: DNS Change

**Objective**: Verify DNS change triggers alert within 60 seconds

**Steps**:
1. Ensure `security-watch.js` is running
2. Wait 30 seconds for first baseline scan
3. Change DNS servers:
   ```powershell
   netsh interface ip set dns "Ethernet" static 8.8.8.8
   ```
4. Wait 60 seconds for alert

**Expected Result**: 
- Email arrives with subject: `🚨 DNS CHANGED - Possible Hijacking`
- Email shows previous DNS vs current DNS
- Email includes recommended actions

**Actual Result**: [ ] PASS [ ] FAIL

**Time to Alert**: _____ seconds  

**Email Received**: [ ] Yes [ ] No

**Notes**: _____________________________

**Restore DNS**:
```powershell
netsh interface ip set dns "Ethernet" dhcp
```

---

## Detection Test 2: Firewall Disabled

**Objective**: Verify Firewall disable triggers alert within 60 seconds

**Steps**:
1. Ensure `security-watch.js` is running
2. Disable Windows Firewall:
   ```powershell
   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
   ```
3. Wait 60 seconds for alert

**Expected Result**:
- Email arrives with subject: `🚨 FIREWALL DISABLED - Network Exposed`
- Email includes recommended actions
- Alert is NOT sent if firewall was already disabled at baseline

**Actual Result**: [ ] PASS [ ] FAIL

**Time to Alert**: _____ seconds

**Email Received**: [ ] Yes [ ] No

**Notes**: _____________________________

**Restore Firewall**:
```powershell
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

---

## Detection Test 3: Defender Disabled

**Objective**: Verify Defender disable triggers alert within 60 seconds

**Steps**:
1. Ensure `security-watch.js` is running
2. Disable Windows Defender:
   ```powershell
   Set-MpPreference -DisableRealtimeMonitoring $true
   ```
3. Wait 60 seconds for alert

**Expected Result**:
- Email arrives with subject: `🚨 DEFENDER DISABLED - Malware Unprotected`
- Email includes recommended actions
- Alert is NOT sent if Defender was already disabled at baseline

**Actual Result**: [ ] PASS [ ] FAIL

**Time to Alert**: _____ seconds

**Email Received**: [ ] Yes [ ] No

**Notes**: _____________________________

**Restore Defender**:
```powershell
Set-MpPreference -DisableRealtimeMonitoring $false
```

---

## Detection Test 4: RDP Enabled

**Objective**: Verify RDP enable triggers alert within 60 seconds

**Steps**:
1. Ensure `security-watch.js` is running
2. Enable RDP:
   ```powershell
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0
   ```
3. Restart Terminal Server:
   ```powershell
   Stop-Service TermService -Force
   Start-Service TermService
   ```
4. Wait 60 seconds for alert

**Expected Result**:
- Email arrives with subject: `🚨 RDP ENABLED - Remote Access Active`
- Email includes recommended actions
- Alert is NOT sent if RDP was already enabled at baseline

**Actual Result**: [ ] PASS [ ] FAIL

**Time to Alert**: _____ seconds

**Email Received**: [ ] Yes [ ] No

**Notes**: _____________________________

**Restore RDP (Disable)**:
```powershell
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 1
Stop-Service TermService -Force
Start-Service TermService
```

---

## Detection Test 5: SSH Enabled

**Objective**: Verify SSH enable triggers alert within 60 seconds

**Steps**:
1. Ensure `security-watch.js` is running
2. Start SSH service:
   ```powershell
   Start-Service sshd
   Set-Service -Name sshd -StartupType Automatic
   ```
3. Wait 60 seconds for alert

**Expected Result**:
- Email arrives with subject: `🚨 SSH ENABLED - Remote Shell Active`
- Email includes recommended actions
- Alert is NOT sent if SSH was already enabled at baseline

**Actual Result**: [ ] PASS [ ] FAIL

**Time to Alert**: _____ seconds

**Email Received**: [ ] Yes [ ] No

**Notes**: _____________________________

**Restore SSH (Disable)**:
```powershell
Stop-Service sshd
Set-Service -Name sshd -StartupType Disabled
```

---

## Operational Test 6: Alert Cooldown (4 hours)

**Objective**: Verify same alert doesn't send twice within 4 hours

**Steps**:
1. Trigger a detection (e.g., disable Firewall)
2. Wait for first alert email (should arrive)
3. Immediately trigger same detection again
4. Wait 60 seconds

**Expected Result**:
- First alert: Email sent ✅
- Second alert (same): No email (on cooldown) ✅
- Console shows: "⏸️ on cooldown"
- After 4 hours, same alert can fire again

**Actual Result**: [ ] PASS [ ] FAIL

**Notes**: _____________________________

---

## Operational Test 7: Heartbeat (12 hours)

**Objective**: Verify heartbeat email arrives every 12 hours

**Steps**:
1. Run `security-watch.js` for 12+ hours
2. Check email for "✅ Security Watch Alive" messages

**Expected Result**:
- First heartbeat: ~12 hours after start
- Second heartbeat: ~24 hours after start
- Third heartbeat: ~36 hours after start
- Each includes current DNS, Firewall, Defender, RDP, SSH status

**Actual Result**: [ ] PASS [ ] FAIL

**Heartbeat Times Received**:
- 1st: ___________ (should be ~12h after start)
- 2nd: ___________ (should be ~24h after start)
- 3rd: ___________ (should be ~36h after start)

**Notes**: _____________________________

---

## Operational Test 8: Baseline Approval

**Objective**: Verify baseline requires user approval

**Steps**:
1. Delete `baseline.json`:
   ```powershell
   Remove-Item baseline.json
   ```
2. Run: `node security-watch.js`
3. See approval prompt with current values
4. Type "no" when asked to approve

**Expected Result**:
- Program shows approval prompt ✅
- Shows 5 current values (DNS, FW, Def, RDP, SSH) ✅
- Program exits without creating baseline ✅
- `baseline.json` does NOT exist ✅

**Actual Result**: [ ] PASS [ ] FAIL

**Notes**: _____________________________

**Then Approve**:
1. Run: `node security-watch.js` again
2. Type "yes" when asked to approve
3. Verify `baseline.json` is created
4. Verify monitoring starts

**Approval Result**: [ ] PASS [ ] FAIL

---

## Persistence Test 9: Restart Persistence

**Objective**: Verify state persists after restart

**Steps**:
1. Run `security-watch.js` for 2 hours
2. Make a security change (e.g., change DNS)
3. Kill monitoring process (Ctrl+C)
4. Restart: `node security-watch.js`
5. Wait 60 seconds

**Expected Result**:
- Baseline.json still exists ✅
- Detection fires for the change we made ✅
- Alert email arrives (not suppressed due to restart) ✅

**Actual Result**: [ ] PASS [ ] FAIL

**Time to Alert After Restart**: _____ seconds

**Notes**: _____________________________

---

## Email Test 10: Delivery Verification

**Objective**: Verify all emails are delivered (no missing alerts)

**Steps**:
1. Run entire 72-hour test
2. Count all emails received
3. Categorize by type (Alerts vs Heartbeats)

**Expected Result**:
- All triggered alerts arrive ✅
- Heartbeat every 12 hours (6 total in 72h) ✅
- No missing emails ✅

**Actual Result**: [ ] PASS [ ] FAIL

**Total Emails Received**: _____

**Breakdown**:
- Heartbeat emails: _____ (expected: 6)
- Alert emails: _____ (expected: 5+)
- Other emails: _____

**Missing/Unexpected**:
- _____________________________
- _____________________________

**Notes**: _____________________________

---

## 72-Hour Summary

**Test Duration**: _____ hours

**Stability**: [ ] No crashes [ ] Crashes (_____ count)

**Detection Accuracy**: _____ / 5 detections working

**Alert Speed**: Average _____ seconds

**Spam Issues**: [ ] None [ ] Yes (describe) _____

**False Positives**: _____ detected

**Email Delivery**: [ ] All arrived [ ] Some missing

**Baseline Integrity**: [ ] Never corrupted [ ] Corrupted (describe) _____

---

## Overall Result

**Status**: [ ] ✅ PASS - All tests successful [ ] ❌ FAIL - Issues found

**Critical Issues** (blocking 72h pass):
1. _____________________________
2. _____________________________
3. _____________________________

**Minor Issues** (non-blocking):
1. _____________________________
2. _____________________________

**Next Steps**:
- [ ] Debug failing tests
- [ ] Retest failing components
- [ ] If all pass: Ready to expand
- [ ] If any fail: Do NOT expand until fixed

---

## Sign-Off

**Tester**: ___________________  
**Date Started**: ___________________  
**Date Completed**: ___________________  
**Test Result**: [ ] PASS [ ] FAIL  

**Comments**:
_________________________________________________________
_________________________________________________________
_________________________________________________________

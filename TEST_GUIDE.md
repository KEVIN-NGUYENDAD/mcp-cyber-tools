# Testing v1.0.0 in Claude Desktop

**Status**: Ready for Testing ✅  
**Version**: v1.0.0 (Production)  
**Tools**: 90+  
**Last Updated**: 2026-08-21

---

## 🚀 Quick Start

### Step 1: Verify Server Works
```bash
cd C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools
node server.js
```

**Expected Output**:
```
Loading Phase 1 modules...
Loading Phase 2 modules...
Loading Phase 3 modules...
Loading Phase 4 modules...
✓ Cyber Tools MCP Server Started - 90+ Security Analysis Tools Ready
```

### Step 2: Restart Claude Desktop
- Close Claude Desktop completely
- Wait 2-3 seconds
- Reopen Claude Desktop

### Step 3: Verify Tools Appear
- Open Claude Desktop
- Look for "cyber-tools" in the tools palette
- 90+ tools should be available

---

## 🧪 Test Scenarios

### Test 1: Host Enumeration (Verify System Info)
```
Claude: Run the whoami tool
```
**Expected**: Current user identity displayed

```
Claude: Run systemInfo
```
**Expected**: OS version, CPU count, RAM, build number

```
Claude: Run hostname
```
**Expected**: Computer name displayed

---

### Test 2: Network Analysis (Check Connectivity)
```
Claude: Show my network configuration with ipconfig
```
**Expected**: IP addresses, DNS servers, network adapters

```
Claude: Check active network connections with activeConnections
```
**Expected**: List of established TCP connections with process names

```
Claude: Scan port 445 on localhost with scanPort
```
**Expected**: TCP connection test result (open/closed)

---

### Test 3: Process Analysis (Monitor System)
```
Claude: Run tasklist to show all running processes
```
**Expected**: List of running processes

```
Claude: Check top 10 processes by memory usage
```
**Expected**: Processes sorted by memory consumption

```
Claude: Show CPU usage by top processes
```
**Expected**: Processes with highest CPU usage

---

### Test 4: Security Status (Firewall & Defender)
```
Claude: Check firewall status
```
**Expected**: Firewall profile status (enabled/disabled)

```
Claude: List firewall rules
```
**Expected**: Windows Firewall rules list

```
Claude: Check Windows Defender status
```
**Expected**: Defender protection status

```
Claude: Check for detected threats with defenderThreats
```
**Expected**: List of threats (if any detected)

---

### Test 5: Event Logs (Check Logs)
```
Claude: Show recent security event logs
```
**Expected**: Security event log entries

```
Claude: Check for failed login attempts
```
**Expected**: Failed logon events (Event 4625)

```
Claude: Show RDP connection logs
```
**Expected**: RDP events

---

### Test 6: Persistence Check (Find Autorun Programs)
```
Claude: Check startup programs with startupPrograms
```
**Expected**: Startup programs list

```
Claude: Audit all persistence mechanisms with persistenceAudit
```
**Expected**: Summary of persistence methods

```
Claude: Check Registry Run keys with registryRunKeys
```
**Expected**: HKLM and HKCU Run keys

---

### Test 7: Forensics (File Analysis)
```
Claude: Calculate SHA256 hash of C:\Windows\System32\cmd.exe
```
**Expected**: SHA256 hash of cmd.exe

```
Claude: Get metadata for C:\Windows\System32\cmd.exe
```
**Expected**: File timestamps, size, owner, attributes

```
Claude: List recent files
```
**Expected**: Recently accessed files

---

### Test 8: Threat Hunting (Find Suspicious Activity)
```
Claude: Hunt for encoded PowerShell commands
```
**Expected**: Encoded PowerShell in event logs (if present)

```
Claude: Hunt for suspicious services
```
**Expected**: Services with suspicious names or paths

```
Claude: Hunt for living off the land binaries (LOLBins)
```
**Expected**: Running processes using common LOLBins

---

### Test 9: Incident Response (Generate Reports)
```
Claude: Collect evidence for incident INC-2024-001
```
**Expected**: JSON report saved to ./reports/

**Verify Report**:
```bash
# Check if report was created
dir C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\reports\

# View report content
type C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\reports\incident_*.json | more
```

```
Claude: Generate a full security audit
```
**Expected**: HTML report saved to ./reports/

**Open Report**:
```bash
# Open in browser
start C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\reports\audit_*.html
```

```
Claude: Generate a 7-day incident timeline
```
**Expected**: JSON timeline report

---

### Test 10: Comprehensive Workflow (End-to-End Test)
```
Claude: I need to investigate a potential security incident. 
Let me:
1. Check current network connections
2. List suspicious services
3. Review firewall rules
4. Check event logs for failed logons
5. Generate a security audit report
```

**Expected**: All tools run in sequence, report generated

---

## ✅ Verification Checklist

After testing, verify:

- [ ] Server starts without errors
- [ ] Tools appear in Claude Desktop
- [ ] At least 5 tools tested successfully
- [ ] Network analysis tools work
- [ ] Security tools return valid data
- [ ] Reports generate successfully
- [ ] HTML reports open in browser
- [ ] JSON reports contain valid data
- [ ] No fatal errors encountered
- [ ] All 4 phases accessible

---

## 📊 Test Results Template

Copy this to document your testing:

```
v1.0.0 Testing Results
======================

Date: [Your Date]
Tester: [Your Name]
System: Windows [Version]

Test Results:
✅ Host Enumeration - PASSED
✅ Network Analysis - PASSED
✅ Process Analysis - PASSED
✅ Firewall Check - PASSED
✅ Defender Status - PASSED
✅ Event Logs - PASSED
✅ Persistence Check - PASSED
✅ Forensics - PASSED
✅ Threat Hunting - PASSED
✅ Incident Response - PASSED

Reports Generated:
✅ JSON reports created
✅ HTML reports created
✅ Audit reports created

Overall Status: PASSED ✅
```

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check Node.js version
node --version  # Should be 18+

# Check for port conflicts
netstat -ano | findstr :3000

# Run with verbose output
node server.js 2>&1 | more
```

### Tools Don't Appear in Claude
1. **Close Claude completely** (not just minimize)
2. **Wait 5 seconds**
3. **Restart Claude Desktop**
4. **Check Tools menu** - should see "cyber-tools"

### Error: "Cannot find module"
```bash
# Reinstall dependencies
npm install

# Verify zod is installed
npm list zod

# Verify SDK is installed
npm list @modelcontextprotocol/sdk
```

### PowerShell Execution Error
```powershell
# Check execution policy
Get-ExecutionPolicy

# Set if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Permission Denied Errors
- Run Claude Desktop as Administrator
- Or run server as Administrator:
```bash
# Open PowerShell as Admin
powershell -Command "Start-Process powershell -Verb RunAs"

# Then run server
cd C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools
node server.js
```

---

## 📋 Tools List (Quick Reference)

### Phase 1: Core Analysis
**Host** (10): whoami, hostname, systemInfo, localUsers, localAdmins, installedSoftware, sharedFolders, environmentVars, userProfiles, loggedOnUsers

**Network** (10): ipconfig, netstat, arp, routePrint, dnsCache, ping, tracert, nslookup, scanPort, activeConnections

**Process** (10): tasklist, processMonitor, processDetails, processTree, processByPid, runningProcesses, cpuUsage, memoryUsage, topProcesses, suspiciousProcesses

### Phase 2: System Security
**Services** (5): servicesChecker, runningServices, stoppedServices, autoStartServices, disabledServices

**Event Logs** (10): eventLogs, securityLogs, systemLogs, applicationLogs, failedLogons, successfulLogons, powershellLogs, rdpLogs, usbLogs, serviceLogs

**Firewall** (5): firewallStatus, firewallRules, inboundRules, outboundRules, disabledFirewallRules

**Defender** (5): defenderStatus, defenderThreats, defenderHistory, defenderExclusions, defenderQuickScan

### Phase 3: Forensics & Persistence
**Persistence** (10): startupPrograms, startupFolders, scheduledTasks, registryRunKeys, registryRunOnce, wmiPersistence, servicePersistence, browserPersistence, dllHijackLocations, persistenceAudit

**Forensics** (10): checkHash, readLogFile, fileMetadata, recentFiles, downloadsFolder, desktopFiles, tempFiles, recycleBin, alternateDataStreams, suspiciousExecutables

### Phase 4: Threat Hunting & IR
**Hunting** (10): huntEncodedPowerShell, huntPersistence, huntSuspiciousServices, huntSuspiciousTasks, huntCredentialDumping, huntLateralMovement, huntRemoteDesktop, huntNetworkBeacons, huntLivingOffTheLand, huntIndicators

**Incident** (10): collectEvidence, collectProcesses, collectServices, collectNetworkState, collectStartupItems, collectFirewall, collectDefender, collectLogs, timeline, securityAudit

---

## 📊 Success Criteria

✅ **Test Passes If:**
- Server starts without errors
- All 90+ tools accessible in Claude
- At least 8 out of 10 test scenarios pass
- Reports generate successfully
- No critical errors encountered
- All 4 phases functional
- Documentation accurate

❌ **Test Fails If:**
- Server won't start
- Tools don't appear
- More than 2 tests fail
- Reports don't generate
- Critical errors encountered
- Any phase completely non-functional

---

## 🎯 Next Steps After Testing

### If Tests PASS ✅
1. Confirm v1.0.0 is production ready
2. Begin using for security analysis
3. Start development on v1.1.0
4. Create feature branches as needed

### If Issues Found ❌
1. Document errors in issue tracker
2. Create hotfix branch: `git checkout -b hotfix/issue-name`
3. Fix the issue
4. Test again
5. Merge to main as v1.0.1
6. Continue with develop branch

---

## 📝 Configuration Used

**Config File**: `C:\Users\tamng\AppData\Roaming\Claude\Profiles\claude_desktop_config.json`

**Server Path**: `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\server.js`

**Status**: ✅ Configured and Ready

---

**Test Guide v1.0 | v1.0.0 Testing**
Last Updated: 2026-08-21

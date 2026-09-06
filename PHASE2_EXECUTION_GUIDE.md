# PHASE 2 EXECUTION GUIDE
**Fresh Laptop #1: SoftLanding Artifact Correlation**
**How to Run on Thanh-Nguyen Machine**
**Date**: 2026-08-21

---

## 🎯 QUICK START

### On Thanh-Nguyen Machine (Claude Desktop)

Run these commands **in order** via Claude:

```
1. @cyber-tools collectEvidence
   Purpose: Get SoftLanding executable details
   Expected: File location, properties, hash
   
2. @cyber-tools fileMetadata SoftLanding
   Purpose: Analyze executable signature and properties
   Expected: Publisher, version, timestamp
   
3. @cyber-tools servicesChecker
   Purpose: Find auto-start services (including SoftLanding)
   Expected: Service list with state and startup type
   
4. @cyber-tools defenderStatus
   Purpose: Check Windows Defender configuration
   Expected: Protection status, exclusions
   
5. @cyber-tools firewallRules
   Purpose: Get Windows Firewall rules
   Expected: Inbound/outbound rules for all applications
   
6. @cyber-tools networkConnections
   Purpose: Active network connections
   Expected: Process names, remote IPs, ports
```

---

## 📊 PHASE 2 INVESTIGATION MATRIX

### Layer 1: Executable Analysis

**Command**: `@cyber-tools collectEvidence`

**What to Look For**:
```
SoftLanding.exe or SoftLandingXXX.exe

Properties Needed:
  ✓ Full file path (C:\Program Files\... or C:\Windows\... or C:\Users\...)
  ✓ File size
  ✓ Created date
  ✓ Modified date
  ✓ Digital signature status
  ✓ Publisher name
  ✓ File version
  ✓ File hash (SHA256)
```

**Analysis Questions**:
- Is it in a suspicious location?
- Is it signed by a recognized publisher?
- Is the timestamp consistent with installation?
- Does the hash match known SoftLanding versions?

**Record Results in**: `PHASE2_RESULTS_SOFTLANDING.md`

---

### Layer 2: Executable Properties

**Command**: `@cyber-tools fileMetadata SoftLanding*`

**What to Look For**:
```
Detailed file metadata:
  ✓ Digital signature validity
  ✓ Certificate issuer
  ✓ Code signing timestamp
  ✓ File version info
  ✓ Product name
  ✓ Company name
  ✓ Internal name vs external name
```

**Analysis Questions**:
- Is signature valid and from trusted authority?
- Does company name match publisher?
- Are version numbers consistent?
- Is this a known SoftLanding version?

---

### Layer 3: Service Correlation

**Command**: `@cyber-tools servicesChecker`

**What to Look For**:
```
Search for SoftLanding-related services:

Service Name       State       Startup Type    ImagePath
-----------        -----       -----------     ---------
SoftLanding*       ?           ?               ?
```

**Analysis Questions**:
- Is there a SoftLanding service?
- Is it set to auto-start?
- Does ImagePath match executable found in Layer 1?
- Is the service actually running?
- What account does it run under?

**Correlation Check**:
```
Scheduled Task: SoftLandingCreativeManagementTask
    ↓ (Points to)
Executable: C:\...\SoftLanding.exe
    ↓ (Also runs via)
Service: SoftLanding (if exists)
    ↓ (Both should point to same file or related files)
```

---

### Layer 4: Security Recognition

**Command**: `@cyber-tools defenderStatus`

Then: `@cyber-tools defenderHistory`

**What to Look For**:
```
Defender Status:
  ✓ Real-time protection enabled/disabled
  ✓ Virus and threat protection status
  ✓ Exclusions (are any SoftLanding paths excluded?)
  ✓ Quarantine history

Threat History:
  ✓ Any SoftLanding detections?
  ✓ Quarantine events?
  ✓ When was last scan?
  ✓ Were threats found?
```

**Analysis Questions**:
- Does Defender recognize SoftLanding?
- Is there a threat signature for it?
- Has it been quarantined before?
- Is there an exclusion configured?

**Red Flags**:
- ⚠️ SoftLanding path in exclusions (why excluded?)
- ⚠️ Defender disabled just before SoftLanding installation
- ⚠️ Recent quarantine and then exclusion added

---

### Layer 5: Firewall Rules

**Command**: `@cyber-tools firewallRules`

**What to Look For**:
```
Firewall Rules:
  Inbound Rules:
    - Any allow rules for SoftLanding?
    
  Outbound Rules:
    - SoftLanding.exe allowed to connect?
    - Restricted to specific IPs/ports?
    - Allowed to any destination?
```

**Analysis Questions**:
- Are there firewall rules for SoftLanding?
- Are they permissive or restrictive?
- What protocols (TCP/UDP)?
- What ports?
- Remote addresses?

**Suspicious Pattern**:
- Rule allowing SoftLanding to any IP on any port
- Rules to non-standard ports (not 80, 443)
- Rules to internal network ranges

---

### Layer 6: Network Connections

**Command**: `@cyber-tools networkConnections`

**What to Look For**:
```
Active connections:
  Process Name: SoftLanding.exe (or related)
  
  Connections:
    Local IP       Local Port    Remote IP      Remote Port    State
    -----------    ----------    -----------    -----------    -----
    ?              ?             ?              ?              ?
```

**Analysis Questions**:
- Is SoftLanding connecting to anything?
- What remote IPs/hosts?
- What ports?
- Is traffic encrypted (HTTPS) or plain (HTTP)?
- Are connections to known CDNs or suspicious IPs?

**Check Against**:
- Whois database for remote IPs
- Known malware C&C lists
- Internal vs external traffic

---

## 📝 RESULT COLLECTION TEMPLATE

### Create File: `PHASE2_RESULTS_SOFTLANDING.md`

```markdown
# PHASE 2 RESULTS: SoftLanding Artifact Correlation
**Date**: [TODAY]
**Machine**: THANH-NGUYEN
**Investigator**: [YOUR NAME]

## Layer 1: Executable Analysis

### collectEvidence Results
[Paste SoftLanding.exe details from output]

File Path: 
File Size: 
Created: 
Modified: 
Digital Signature: 
Publisher: 
Version: 
Hash (SHA256): 

**Analysis**: 
[Write your assessment here]

---

## Layer 2: File Metadata

### fileMetadata Results
[Paste detailed metadata from output]

Signature Valid: Yes/No
Certificate Issuer: 
Code Signing Date: 

**Analysis**: 
[Write your assessment here]

---

## Layer 3: Service Correlation

### servicesChecker Results
[Paste service information from output]

SoftLanding Service Found: Yes/No
Service Name: 
Service State: 
Startup Type: 
ImagePath: 

**Correlation Analysis**:
Scheduled Task → Executable → Service Path: [Match/Mismatch]

[Write your assessment here]

---

## Layer 4: Security Recognition

### defenderStatus Results
[Paste Defender status from output]

Defender Status: 
Exclusions Found: 
SoftLanding in Exclusions: Yes/No

### defenderHistory Results
[Paste history from output]

SoftLanding Detections: 
Quarantine Events: 

**Analysis**: 
[Write your assessment here]

---

## Layer 5: Firewall Rules

### firewallRules Results
[Paste SoftLanding-related rules]

Inbound Rules: 
Outbound Rules: 

**Analysis**: 
[Write your assessment here]

---

## Layer 6: Network Connections

### networkConnections Results
[Paste active connections from output]

SoftLanding Active Connections: 
Remote IPs: 
Ports: 

**Analysis**: 
[Write your assessment here]

---

## 🎯 FINAL CORRELATION ASSESSMENT

### Evidence Summary
```
Executable:      [Safe/Interesting/Suspicious]
Signature:       [Valid/Invalid/Missing]
Service:         [Present/Absent] [Auto-start/Manual/Disabled]
Defender:        [Recognized/Unknown] [Threat/Safe]
Firewall:        [Rules present/absent] [Permissive/Restrictive]
Network:         [Active/Inactive] [Suspicious connections/None]
```

### Conclusion

**Classification**: 
- [ ] Safe (legitimate software, false positive)
- [ ] Interesting (needs further monitoring)
- [ ] Suspicious (potential threat)

**Reasoning**:
[Write your detailed conclusion with evidence from all layers]

**Recommendation**:
[What should be done with this artifact?]

---

## 📋 SIGN-OFF

**Investigation Date**: 
**Investigator**: 
**Peer Review**: [Pending/Complete]
**Status**: [Phase 2 In Progress / Phase 2 Complete]
```

---

## 🔄 EXECUTION WORKFLOW

### Step 1: Run Phase 2 Commands (On Thanh-Nguyen)
```
In Claude Desktop on Thanh-Nguyen machine:

1. Type: @cyber-tools collectEvidence
   Wait for results
   Copy output to PHASE2_RESULTS_SOFTLANDING.md

2. Type: @cyber-tools fileMetadata
   Wait for results
   Copy output to PHASE2_RESULTS_SOFTLANDING.md
   
3. Type: @cyber-tools servicesChecker
   Wait for results
   Copy output to PHASE2_RESULTS_SOFTLANDING.md
   
4. Type: @cyber-tools defenderStatus
   Wait for results
   Copy output to PHASE2_RESULTS_SOFTLANDING.md
   
5. Type: @cyber-tools firewallRules
   Wait for results
   Copy output to PHASE2_RESULTS_SOFTLANDING.md
   
6. Type: @cyber-tools networkConnections
   Wait for results
   Copy output to PHASE2_RESULTS_SOFTLANDING.md
```

### Step 2: Analyze Results (On Thanh-Nguyen)
```
Fill in analysis section for each layer
Document findings in the template
```

### Step 3: Draw Conclusions (On Thanh-Nguyen)
```
Correlate all layers
Reach defensible classification
Document reasoning with evidence
```

### Step 4: Share Results (Back to Claude Code)
```
Copy PHASE2_RESULTS_SOFTLANDING.md to Claude Code session
Create final Phase 2 completion report
Archive results in reports/
```

---

## ✅ SUCCESS CRITERIA

Phase 2 is complete when:

```
✅ All 6 tool outputs collected
✅ Each layer analyzed with findings documented
✅ Multi-layer correlation completed
✅ Final classification reached (Safe/Interesting/Suspicious)
✅ Evidence trails documented
✅ Defensible conclusion written
✅ Recommendation provided
```

---

## 🏆 WHAT THIS DEMONSTRATES

When Phase 2 completes, Fresh Laptop #1 will have proven:

```
✅ Evidence collection works
✅ Data analysis works
✅ Multi-source correlation works
✅ Investigator discipline maintained
✅ Artifact classification methodology works
✅ Complete DFIR workflow operational
```

Result: cyber-tools proven as complete investigation platform ✅

---

**PHASE 2 READY FOR EXECUTION** 🚀

On Thanh-Nguyen machine, in Claude Desktop, run the commands above.
Capture results in PHASE2_RESULTS_SOFTLANDING.md template.
Share results back to Claude Code session for final analysis.

This completes Fresh Laptop #1 validation.

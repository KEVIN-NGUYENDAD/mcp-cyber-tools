# PROD-00008 Guidance: USB & Removable Media Security Audit

**Status:** Ready for collection  
**Case ID:** PROD-00008  
**Investigation Type:** USB & Removable Media Security Audit  
**Timeline:** After PROD-00007  
**Objective:** Cover new domain (external storage) before baseline

---

## WHY THIS INVESTIGATION TYPE

### Current Dataset Coverage (n=7)

```
✅ Persistence (behavioral)
✅ Endpoint (state-based)
✅ Network (connectivity)
✅ Threat Hunting (behavioral)
✅ Software (state-based)
✅ Authentication (access/logs)
✅ Browser (application-level)
```

### New Domain Not Yet Covered

```
⏳ USB Devices
⏳ Removable Storage
⏳ External Drives
⏳ Device History
⏳ Unauthorized Storage
```

### Why USB Security Matters

1. **Different Attack Vector**
   - Physical security aspect
   - Data exfiltration channel
   - Malware distribution vector
   - Not network-based like previous cases

2. **Common Bypass Technique**
   - USB devices can bypass firewall restrictions
   - External drives can contain hidden malware
   - Device history shows past connections
   - Frequently overlooked in security audits

3. **Complete Coverage**
   - Covers all major Windows security domains
   - After PROD-00008: Have comprehensive baseline
   - Prepares for n=10 baseline review

---

## INVESTIGATION SCOPE

### Investigate

```
Connected USB Devices
  - Currently connected devices
  - Device types
  - Device names/manufacturer
  - Connection status
  
Device Installation History
  - Previously connected devices
  - Installation timeline
  - Device identifiers
  - Unknown/unidentified devices
  
Removable Storage
  - External drives
  - USB flash drives
  - SD cards
  - Portable storage devices
  
Device Security Events
  - Device connection/disconnection logs
  - Unauthorized device attempts
  - Device permission changes
  
Suspicious Device Indicators
  - Unknown manufacturers
  - Suspicious device names
  - Devices with executable files
  - Devices with autorun.inf
```

### For Each Finding Provide

```
Title:             [clear description]
Severity:          [critical/high/medium/low]
Source:            [usb_audit]
Classification:    [connected/historical/suspicious/clean]
Confidence:        [0-100]
```

### Example Scenarios

#### Scenario A: Clean USB History
```json
{
  "title": "USB Device History - No Suspicious Devices Found",
  "severity": "none",
  "devices_ever_connected": 0,
  "currently_connected": 0,
  "classification": "clean",
  "confidence": 98
}
```

#### Scenario B: Legitimate Devices
```json
{
  "title": "USB Devices - Only Legitimate Peripherals Connected",
  "severity": "low",
  "connected_devices": [
    "Logitech Mouse",
    "Dell Keyboard",
    "Printer"
  ],
  "classification": "clean",
  "confidence": 99
}
```

#### Scenario C: Suspicious Device
```json
{
  "title": "Unknown USB Device Detected",
  "severity": "medium",
  "device_id": "USB\\VID_1234&PID_5678",
  "manufacturer": "Unknown",
  "classification": "suspicious",
  "confidence": 85
}
```

#### Scenario D: Device Persistence
```json
{
  "title": "Removable Storage with Autorun Script",
  "severity": "high",
  "device": "External Drive",
  "autorun_found": true,
  "executable_content": true,
  "classification": "suspicious",
  "confidence": 92
}
```

---

## SYSTEM DECISION LOGIC

### If USB Clean

```
Recommendation: MONITOR
Reasoning: No suspicious USB devices detected, no device-based risks
Confidence: 95%+
```

### If USB Suspicious

```
Option A: Unknown device connected
  Recommendation: INVESTIGATE
  Reasoning: Unknown USB device requires verification
  
Option B: Suspicious history
  Recommendation: MONITOR (with note)
  Reasoning: Historical device is lower risk than current threat
  
Option C: Executable on removable storage
  Recommendation: ESCALATE
  Reasoning: Portable malware vector detected
```

---

## ANALYST REVIEW TEMPLATE

After system recommendation, review as analyst:

```
Question 1: Are there unknown USB devices?
  ✅ YES - Identify and validate
  ✅ NO - Proceed with monitoring

Question 2: Is device currently connected?
  ✅ YES - Higher risk, investigate
  ✅ NO - Lower risk, monitor

Question 3: Are there executables on external storage?
  ✅ YES - Require justification
  ✅ NO - Proceed with recommendation
```

---

## EXPECTED PATTERNS

### Scenario A: No USB Devices (Most Likely)

```
System Recommendation: MONITOR (no devices, no risk)
Analyst Decision: MONITOR
Agreement: YES
Outcome: 100%

Result: System handles zero-findings correctly
```

### Scenario B: Legitimate Peripherals Only

```
System Recommendation: MONITOR (devices are known/legitimate)
Analyst Decision: MONITOR
Agreement: YES
Outcome: 100%

Result: Device baseline established
```

### Scenario C: Unknown Device Found

```
System Recommendation: INVESTIGATE
Analyst Decision: INVESTIGATE (or verify legitimacy first)
Agreement: YES or NO (depends on device origin)

Result: Device security protocol demonstrated
```

---

## COLLECTION PROCEDURE

1. **Run Investigation**
   ```
   Use cyber-tools to perform USB & removable media security audit
   ```

2. **Document Findings**
   ```
   For each device/finding:
   - Title
   - Device type
   - Severity
   - Classification
   - Confidence
   
   NOTE: Unknown devices are key data point
   ```

3. **Get System Recommendation**
   ```
   Capture:
   - Recommendation (MONITOR/INVESTIGATE/ESCALATE)
   - Confidence (0-100)
   - Reasoning (especially for suspicious devices)
   ```

4. **Analyst Review**
   ```
   Decision: Agree or override?
   Confidence: 0-100
   Reasoning: Why? (especially about device identification)
   ```

5. **Record Outcome**
   ```
   Agreement: YES/NO
   Override: YES/NO
   Result Correct: YES/NO
   Devices Found: [count]
   Suspicious Devices: [count]
   ```

---

## IMPORTANCE OF PROD-00008

### Why This Case Matters

```
After 7 cases: Have coverage of most domains
After 8 cases: Have covered external storage domain
Before baseline: Need complete picture

USB audit completes the security perimeter:
- Internal: Persistence, Threat, Processes
- State-based: Software, Updates
- Access: Authentication, Logs
- Applications: Browser
- External: USB/Removable (PROD-00008)
```

### What Happens at n=8

```
Dataset becomes more complete
Coverage reaches 8 major security domains
PROD-00009, 00010 can focus on:
- Depth in any domain
- Edge cases
- Cross-domain validation
```

---

## DISCIPLINE REMINDER

**Still Collection Phase:**
- ❌ Don't plan USB restrictions yet
- ❌ Don't recommend device blocking
- ❌ Don't assume findings mean action
- ✅ Collect data accurately
- ✅ Record analyst decisions
- ✅ Build toward n=10 baseline

---

## TIMELINE

```
PROD-00008:       USB/Removable Media (collect)
PROD-00009:       TBD (complete coverage)
PROD-00010:       Final baseline case
At n=10:          Production Baseline Review v1 (full analysis)
```

---

## NEXT CHECKPOINT

**When:** After PROD-00010 (n=10)  
**What:** Production Baseline v1 Review Complete  
**Analysis:** Top observations, visibility gaps, bottleneck ranking  
**Decision:** Which observations become improvement targets

---

**Ready to collect PROD-00008.**

**Expanding coverage to external storage domain.**

**Moving toward complete production baseline.**

🏆 📊 🚀

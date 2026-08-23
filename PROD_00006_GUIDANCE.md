# PROD-00006 Guidance: Authentication & Account Security Audit

**Status:** Ready for collection  
**Case ID:** PROD-00006  
**Investigation Type:** Authentication & Account Security Audit  
**Timeline:** After PROD-00005  
**Objective:** Test visibility hypothesis via security log access

---

## HYPOTHESIS-DRIVEN COLLECTION

### The Question

After 5 production cases, data shows:
- Firewall visibility gap: 2/5 cases (40%)
- Event log access denied: 1/5 cases (20%)
- Pattern: Information gaps appear when querying security-sensitive data

### The Test

**Hypothesis:** Visibility constraints are the real bottleneck, not detection.

**How to Test:** Run authentication audit, which requires:
- Security event log access
- Authentication history
- Failed logon tracking
- Account status queries

**Expected Result:**
```
If audit succeeds:
  → Visibility gap is contextual, not systemic
  
If audit fails (access denied):
  → Visibility gap is systemic
  → Escalate from Observation to Bottleneck Candidate
  → Frequency reaches 3+ (triggering escalation rule)
```

---

## INVESTIGATION SCOPE

### Investigate

```
Security Event Log Access
  - Can we read security events?
  - Any access restrictions?
  
Failed Logon Events
  - Failed attempts in past 7 days
  - Pattern analysis
  - Anomalies
  
Successful Logon Events
  - Recent successful logins
  - Time patterns
  - Geographic patterns (if tracked)
  
Local Users & Accounts
  - Local user list
  - Privileged accounts
  - Last password change
  
Remote Desktop Activity
  - RDP logons
  - Session duration
  - Failed RDP attempts
  
Authentication Anomalies
  - Unusual login times
  - Unusual locations
  - Account lockouts
  - Password changes
  
Privileged Account Usage
  - Admin account activity
  - Service account usage
  - Privilege escalation attempts
```

### For Each Finding Provide

```
Title:             [clear description]
Severity:          [critical/high/medium/low]
Source:            [event_log / security_audit]
Classification:    [anomaly/normal/unavailable/denied]
Confidence:        [0-100]
```

### Example Scenarios

#### Scenario A: Clean Auth Data
```json
{
  "title": "Normal authentication patterns",
  "severity": "none",
  "failed_logons_7day": 3,
  "assessment": "Normal user errors",
  "classification": "clean",
  "confidence": 95
}
```

#### Scenario B: Log Access Denied
```json
{
  "title": "Security Event Log Access Denied",
  "severity": "high",
  "source": "event_log",
  "error": "Access Denied",
  "classification": "unavailable",
  "confidence": 100
}
```

#### Scenario C: Suspicious Activity
```json
{
  "title": "Multiple failed logons from unusual location",
  "severity": "medium",
  "failed_attempts": 7,
  "time_window": "1 hour",
  "classification": "anomaly",
  "confidence": 85
}
```

---

## HYPOTHESIS TEST: VISIBILITY

### Critical Data Points to Note

**Watch For:**
```
✓ Any "Access Denied" messages
✓ Any "Unavailable" log data
✓ Any restricted event log queries
✓ Any permission-based limitations
```

**These Confirm Hypothesis:** Visibility is the gap

---

## SYSTEM DECISION LOGIC

### If Authentication Clean

```
Recommendation: MONITOR
Reasoning: Normal authentication patterns, no anomalies detected
Confidence: 90%+
```

### If Anomalies Found

```
Option A: Suspicious pattern
  Recommendation: INVESTIGATE
  Reasoning: Unusual logon activity requires assessment
  
Option B: Access Denied / Data Unavailable
  Recommendation: MONITOR (with caveat)
  Reasoning: Cannot fully assess due to visibility limitations
  
Option C: Critical anomaly
  Recommendation: ESCALATE
  Reasoning: Potential compromise detected
```

---

## ANALYST REVIEW TEMPLATE

After system recommendation, review as analyst:

```
Question 1: Can we see the security logs?
  ✅ YES - Proceed with normal assessment
  ❌ NO - This confirms visibility hypothesis

Question 2: If logs available, are anomalies real?
  ✅ YES - System recommendation valid
  ❌ NO - Override to different decision

Question 3: Are log gaps affecting decision quality?
  ✅ YES - Note impact on accuracy
  ⚠️  MAYBE - Partial visibility
```

---

## WHAT THIS CASE REVEALS

### If Successful (Logs Available)

```
Outcome:
  System makes recommendation based on auth data
  Analyst confirms or overrides
  Result: Normal case

Implication:
  Visibility gaps are scattered, not systemic
  Firewall gap is contextual
  Not a bottleneck yet
  
Next Action:
  Continue to n=10
  Observations stay as observations
```

### If Access Denied (Logs Unavailable)

```
Outcome:
  Cannot analyze authentication data
  System cannot make full assessment
  Visibility gap confirmed again
  
Implication:
  Frequency: 3/6 cases (50%)
  Pattern: Systemic visibility limitation
  Severity: Blocks security log access
  
Next Action:
  Escalate Visibility Gap to Bottleneck Candidate
  PROD-00007+ should test other areas
  Plan for visibility improvement analysis
```

---

## COLLECTION PROCEDURE

1. **Run Investigation**
   ```
   Use cyber-tools to perform authentication & account security audit
   ```

2. **Document Findings**
   ```
   For each finding:
   - Title
   - Severity
   - Source (event_log, account, auth_policy)
   - Classification
   - Confidence
   
   CRITICAL: Note any "Access Denied" or "Unavailable"
   ```

3. **Get System Recommendation**
   ```
   Capture:
   - Recommendation (MONITOR/INVESTIGATE/ESCALATE)
   - Confidence (0-100)
   - Reasoning (especially if limited by data availability)
   ```

4. **Analyst Review**
   ```
   Decision: Agree or override?
   Confidence: 0-100
   Reasoning: Why? (especially about visibility limitations)
   ```

5. **Record Outcome**
   ```
   Agreement: YES/NO
   Override: YES/NO
   Result Correct: YES/NO/UNKNOWN (if incomplete data)
   Visibility Impact: Was decision affected by access limitations?
   ```

---

## HYPOTHESIS TESTING METRICS

### Success Measure

After PROD-00006, we'll know:

```
Firewall Visibility Gap:     2/5 → 2/6 or 3/6
Office Update Failure:       2/5 → 2/6 or 3/6
Auth Log Access Denied:      1/5 → 1/6 or 2/6

If any reach 3/6 (50%):
  Escalate to Bottleneck Candidate
  
If all stay below 50%:
  Observations confirmed as scattered issues
  Continue collection to n=10
```

---

## ESCALATION RULES (LOCKED)

**When Observation Becomes Bottleneck Candidate:**

```
Criteria:
  1. Appears 3+ times (out of n collected)
  2. Is repeating pattern (not random)
  3. Affects system capability

Current Candidates:
  Firewall Gap:     2/5 (needs 1 more)
  Office Failure:   2/5 (needs 1 more)
  
Test Case:
  PROD-00006 will determine if either reaches 3/6
```

---

## IMPORTANCE OF PROD-00006

### Why This Case Matters

```
PROD-00005: "Here's the pattern"
PROD-00006: "Is it real or coincidence?"

One data point = Pattern
Two data points = Could be luck
Three data points = Evidence
```

### What Happens at n=6

```
If Visibility Gap escalates:
  We know the problem
  Can design fix
  Can test fix
  
If Visibility Gap stays at 2/6:
  It's scattered, not systemic
  Continue to n=10
  Different bottleneck likely
```

---

## TIMELINE

```
PROD-00006:     Authentication Audit (collect)
At n=6:         Hypothesis test result (escalation or not)
PROD-00007-010: Continue to baseline (n=10)
At n=10:        Production Baseline v0.1 confirmed
```

---

**Ready to collect PROD-00006.**

**Hypothesis-driven data collection at work.**

**Visibility hypothesis about to be tested.**

🏆 📊 🚀

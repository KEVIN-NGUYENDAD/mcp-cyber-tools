# PROD-00005 Guidance: Software Inventory & Vulnerability Assessment

**Status:** Ready for collection  
**Case ID:** PROD-00005  
**Investigation Type:** Software Inventory & Vulnerability Assessment  
**Timeline:** After PROD-00004  
**Objective:** Diversify dataset with asset visibility dimension

---

## WHY THIS INVESTIGATION TYPE

### Current Dataset Balance (n=4)

```
✅ Persistence (PROD-00001)      - Startup/scheduled task focus
✅ Endpoint Health (PROD-00002)  - Service/defender focus
✅ Network (PROD-00003)          - Connection/port focus
✅ Threat Hunting (PROD-00004)   - Process/behavior focus
```

**Pattern:** All security operations focused.

### Missing Dimension

```
⏳ Asset Visibility
⏳ Patch State
⏳ Software Risk
⏳ Vulnerability Status
```

### Why Software Inventory Matters

1. **Different Decision Logic**
   - Registry/persistence: Behavioral detection
   - Software inventory: State-based detection
   - Different false positive patterns likely

2. **Real-World Bottleneck**
   - Patch management critical for real networks
   - Vulnerability data affects risk scoring
   - Potential INVESTIGATE findings (rare so far)

3. **Dataset Balance**
   - All 4 current cases = CLEAN/MONITOR
   - Software assessment may find actual issues
   - Diversifies outcome patterns before baseline

---

## INVESTIGATION SCOPE

### Investigate

```
- Installed Software List
- Software Versions
- Patch Status
- Known Vulnerabilities
- End-of-Life Software
- Unauthorized Software
- Legacy/Unsupported Applications
```

### For Each Finding Provide

```
Title:             [clear description]
Severity:          [critical/high/medium/low]
Source:            [software_inventory]
Classification:    [vulnerable/outdated/unsupported/unauthorized]
Confidence:        [0-100]
```

### Example Findings

```json
{
  "title": "Outdated Java Runtime Environment",
  "severity": "high",
  "version": "8.0.191",
  "latestVersion": "8.0.402",
  "vulnerabilities": 23,
  "classification": "outdated",
  "confidence": 95
}
```

or

```json
{
  "title": "No Critical Vulnerabilities Detected",
  "severity": "none",
  "assessment": "Software portfolio is current",
  "classification": "clean",
  "confidence": 94
}
```

---

## SYSTEM DECISION LOGIC

### If Software Clean

```
Recommendation: MONITOR
Reasoning: Software baseline is current, no patches required
Confidence: 95%+
```

### If Vulnerabilities Found

```
Option A: High severity + many vulns
  Recommendation: INVESTIGATE
  Reasoning: Software vulnerabilities require assessment
  
Option B: Medium severity + few vulns
  Recommendation: MONITOR
  Reasoning: Known issues, patch plan needed but not urgent
  
Option C: Outdated but supported
  Recommendation: MONITOR
  Reasoning: Patch plan in place, follow standard update cycle
```

---

## ANALYST REVIEW TEMPLATE

After system recommendation, review as analyst:

```
Question 1: Does system recommendation match severity assessment?
  ✅ YES - Agreement
  ⚠️  NO - Override likely

Question 2: Are vulnerable systems business-critical?
  ✅ YES - Override to INVESTIGATE if missed
  ✅ NO - Accept system recommendation

Question 3: Is patch timeline reasonable?
  ✅ YES - MONITOR acceptable
  ✅ NO - Override to INVESTIGATE
```

---

## EXPECTED PATTERNS

### Scenario A: Clean Software (Most Likely)

```
System Recommendation: MONITOR (software current)
Analyst Decision: MONITOR
Agreement: YES
Outcome: 100% (4/4 agreement continues)
```

**Result:** Reinforces Decision Engine accuracy across domain

### Scenario B: Vulnerabilities Found

```
System Recommendation: INVESTIGATE (critical issues found)
Analyst Decision: INVESTIGATE
Agreement: YES
Outcome: 100%
```

**Result:** Shows system handles findings correctly

### Scenario C: Disagreement (Possible First Override)

```
System Recommendation: MONITOR
Analyst Decision: INVESTIGATE
Reason: Business-critical software with unpatched issues
Agreement: NO
Override: YES
Outcome: TBD (depends on actual severity)
```

**Result:** First analyst override - data point for override frequency

---

## COLLECTION PROCEDURE

1. **Run Investigation**
   ```
   Use cyber-tools to perform software inventory & vulnerability assessment
   ```

2. **Document Findings**
   ```
   For each finding:
   - Title
   - Severity
   - Classification
   - Confidence
   ```

3. **Get System Recommendation**
   ```
   Capture:
   - Recommendation (MONITOR/INVESTIGATE/ESCALATE)
   - Confidence (0-100)
   - Reasoning
   ```

4. **Analyst Review**
   ```
   Decision: Agree or override?
   Confidence: 0-100
   Reasoning: Why?
   ```

5. **Record Outcome**
   ```
   Agreement: YES/NO
   Override: YES/NO
   Result Correct: YES/NO
   ```

---

## IMPORTANCE OF PROD-00005

### Why Now

```
At n=4: Dataset starting to show patterns
At n=5: First Pattern Review possible
Goal: Diversify before n=10 baseline

Software inventory adds:
- Asset visibility dimension
- Patch status perspective
- Vulnerability assessment depth
- Different decision scenarios
```

### What Happens at n=5

After PROD-00005 recorded:
```
First Production Pattern Review
  ✓ Agreement rate analysis
  ✓ Investigation type comparison
  ✓ Decision distribution
  ✓ Observation tracking update
```

Not final. But **first real analysis** of production data.

---

## DISCIPLINE REMINDER

**This is still collection phase.** Do NOT:
- ❌ Assume findings mean changes needed
- ❌ Plan fixes based on single case
- ❌ Make decisions based on n=5
- ❌ Prioritize issues yet

**Do:**
- ✅ Collect data accurately
- ✅ Record analyst decision faithfully
- ✅ Observe patterns forming
- ✅ Move toward n=10 baseline

---

## NEXT CHECKPOINTS

```
PROD-00005:       Software Inventory (collect)
At n=5:           First Pattern Review (preliminary)
PROD-00006-010:   Continue to baseline (n=10)
At n=10:          Production Baseline v0.1 (statistical confidence)
PROD-00011-050:   Accelerate collection to n=50
At n=50:          Production Leaderboard v1 (real bottleneck)
```

---

**Ready to collect PROD-00005.**

**Dataset diversity increases with each case.**

**Pattern recognition accelerates toward baseline.**

🏆 📊 🚀

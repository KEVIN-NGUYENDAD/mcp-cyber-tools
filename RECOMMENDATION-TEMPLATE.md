# RECOMMENDATION WITH CONFIDENCE SCORING

**Template for evidence-based recommendations**

---

## EXAMPLE 1: UNVERIFIED FINDING

```
FINDING: RunAsPPL = 2 (unvalidated)

CONFIDENCE: 40%

EVIDENCE SOURCES: 1
  └─ Registry check only

VALIDATION STATUS: Required

RECOMMENDATION:
  DO NOT remediate immediately.
  
  First: Verify Device Guard status
  - Run: Get-ComputerInfo | Select-Object DeviceGuard*
  - If HVCI enabled → No remediation needed
  - If HVCI disabled → Evaluate remediation
  
SUCCESS CRITERIA:
  - Device Guard status verified
  - HVCI state documented
  - Context-aware decision made
```

---

## EXAMPLE 2: PARTIALLY VERIFIED FINDING

```
FINDING: Process memory usage spike

CONFIDENCE: 60%

EVIDENCE SOURCES: 2
  ├─ Telemetry (process execution time)
  └─ Partial validation (not yet human-verified)

VALIDATION STATUS: In Progress

RECOMMENDATION:
  Monitor process for 24 hours.
  Collect additional context:
  - Network connections
  - File activity
  - Registry modifications
  
  After 24-hour observation period:
  Re-assess with full context
```

---

## EXAMPLE 3: FULLY VERIFIED FINDING

```
FINDING: RunAsPPL = 2 (validated with Device Guard context)

CONFIDENCE: 95%

EVIDENCE SOURCES: 3
  ├─ Registry: RunAsPPL value confirmed
  ├─ Device Guard: HVCI enabled and enforcing
  └─ Human verification: DFIR analyst validated

VALIDATION STATUS: Verified

RECOMMENDATION:
  No remediation required.
  
  This is a correct configuration state.
  RunAsPPL = 2 with HVCI enforcement is expected.
  
  REASON: When Device Guard enforces Code Integrity,
  RunAsPPL = 2 is the appropriate setting.

CONFIDENCE JUSTIFICATION: 95%
  - Finding accuracy verified ✓
  - Context confirmed ✓
  - Human validation passed ✓
  - No false positive indicators ✓
```

---

## SCORING RULES

### Confidence Calculation

**Base Score (from evidence sources):**
- 1 source = 30-40% base confidence
- 2 sources = 50-60% base confidence
- 3+ sources = 70-80% base confidence

**Validation Multipliers:**
- Unverified: ×0.5 (max 50%)
- Partially verified: ×0.8 (max 80%)
- Fully verified: ×1.0 (max 100%)

**Context Multipliers:**
- Single finding: ×0.7
- Multiple correlated findings: ×0.9
- Workflow context: ×1.0

### Examples

```
RunAsPPL = 2 (unvalidated):
  Base: 40% (1 registry source)
  × 0.5 (unverified)
  = 20-40% confidence → Recommend "Verify first"

RunAsPPL = 2 (with Device Guard checked):
  Base: 60% (2 sources: registry + Device Guard API)
  × 0.8 (partially verified)
  = 48-60% confidence → Recommend "Additional context check"

RunAsPPL = 2 (full validation with analyst):
  Base: 70% (3 sources: registry + Device Guard + workflow)
  × 1.0 (verified)
  = 70-95% confidence → Confident recommendation
```

---

## RECOMMENDATION FRAMEWORK

Every recommendation must include:

### 1. FINDING
What did we observe?
```
Registry value X = Y
Process behavior Z detected
Log entry showing ABC
```

### 2. CONFIDENCE %
How certain are we?
```
0-30%:   Require validation (exploratory)
30-60%:  Recommend with caveats (partial evidence)
60-80%:  Recommend with verification steps (context needed)
80-100%: Recommend with confidence (verified)
```

### 3. EVIDENCE SOURCES
What data supports this?
```
- Source 1: Registry check
- Source 2: Process telemetry
- Source 3: Event log correlation
- Source 4: Workflow pattern
- Source 5: Human validation
```

### 4. VALIDATION STATUS
Is this verified?
```
Required    → Need human review or additional data
In Progress → Partial validation underway
Verified    → Human confirmed this is accurate
```

### 5. RECOMMENDATION
What should we do?
```
Immediate action: [if high confidence + verified]
Verify first: [if medium confidence or unverified]
Monitor: [if exploratory or pattern-based]
No action: [if false positive detected]
```

### 6. AIRLIFTS (CRITICAL RULES)
Non-negotiable constraints:
```
AIRLIFT-001: Never remediate RunAsPPL without checking Device Guard
AIRLIFT-002: Never disable security features without full context
AIRLIFT-003: Always verify before recommending urgent actions
```

---

## VALIDATION WORKFLOW

**If confidence < 80%:**

```
Step 1: Gather additional evidence
  └─ Expand to multiple data sources
  
Step 2: Get human validation
  └─ Have DFIR analyst verify
  
Step 3: Update confidence
  └─ Recalculate with new evidence
  
Step 4: Document lesson
  └─ If pattern found, record in lessons.json
```

**If confidence ≥ 80%:**

```
Step 1: Recommend with confidence
  └─ Action is evidence-backed
  
Step 2: Monitor outcome
  └─ Track if recommendation was correct
  
Step 3: Update validation
  └─ Record verification in validations.json
  
Step 4: Update confidence
  └─ Increase if correct, investigate if wrong
```

---

## TRACKING ACCURACY

### After each investigation:

1. **Was the finding correct?**
   - YES: Increase confidence for this finding type
   - NO: Decrease confidence, investigate why

2. **Was the recommendation correct?**
   - YES: Validate the logic, mark as verified
   - NO: Create lesson to prevent future error

3. **Did we miss anything?**
   - YES: Add to validation requirements
   - NO: Document as negative validation

### Confidence updates:

```
Found correct → Confidence +5%
Found incorrect → Confidence -10%
Validation passed → Multiply by 1.1 (max 95%)
Validation failed → Divide by 1.5 (max 50%)
```

---

## IMPLEMENTATION RULE

**All recommendations must include:**

✅ Confidence % (0-100)  
✅ Evidence source count (1-5)  
✅ Validation status (Required/In Progress/Verified)  
✅ Rationale (why this confidence)  
✅ Next steps (what to do next)  

**No recommendations without confidence + evidence + validation status.**

---

## WEEKLY REVIEW

Every week:

1. Review all recommendations made
2. Check validation status of each
3. Update confidence scores based on outcomes
4. Extract lessons from incorrect recommendations
5. Update airlifts if new patterns found
6. Generate WEEKLY-LESSONS-LEARNED report

---

## GOAL

**Transform recommendations from:**
- "I think this is a problem" (0% evidence)

**To:**
- "Evidence shows this finding with 95% confidence, verified by human analyst, based on 3 independent sources" (95% evidence)

**All decisions backed by data. All confidence justified. All validation documented.**

# Registry Finding Schema - Discovery Package

**Date:** August 22, 2026  
**Purpose:** Document known facts, failed assumptions, and unknown schema elements  
**Status:** Awaiting real data inspection

---

## VERIFIED FACTS (Ground Truth)

```
Decision Accuracy: 68% ✅
False Ignores: 32 cases ✅
Registry Subset: 18 cases ✅
Unsigned Startup Entries: 11 cases ✅
```

These numbers are proven via 50-case validation test.

---

## FAILED ASSUMPTIONS (Learned from Regression)

### Assumed Fields (❌ WRONG)

We assumed Decision Engine finding objects contained:

```
vendor_confidence: number
is_unsigned: boolean
vendor_unknown: boolean
```

**Status:** Implementation failed (-32% regression)  
**Verdict:** Fields do not exist in actual finding structure

### Why It Mattered

Rule implementation checked for:
```javascript
if (finding.title && finding.title.toLowerCase().includes('registry')) {
    if (isStartupLocation && !knowledge) {
        // Assumed vendor_confidence, is_unsigned existed
    }
}
```

**Result:** Wrong schema assumptions → wrong rule logic → regression caught

---

## UNKNOWN SCHEMA (To Be Discovered)

### Questions for Real Data Inspection

```
Actual Registry Path Field:
  ❓ Is it finding.registryPath?
  ❓ Is it finding.path?
  ❓ Is it in finding.metadata?
  ❓ Format and structure?

Actual Signature Status Field:
  ❓ Is it finding.signatureStatus?
  ❓ Is it finding.signed?
  ❓ Is it finding.signature.status?
  ❓ Possible values?

Actual Publisher/Vendor Field:
  ❓ Is it finding.publisher?
  ❓ Is it finding.vendor?
  ❓ Is it finding.author?
  ❓ Possible values (Unknown, System, Custom)?

Actual Confidence Field:
  ❓ Is it finding.confidence?
  ❓ Is it in finding.metadata?
  ❓ Scale (0-100, 0-1)?

Actual Startup Location Field:
  ❓ Is it finding.registryLocation?
  ❓ How are startup locations identified?
  ❓ Possible values (Run, RunOnce, Startup, etc)?

Metadata Structure:
  ❓ What fields exist in finding.metadata?
  ❓ How is risk information stored?
  ❓ How is history stored?
```

---

## SCHEMA DISCOVERY CHECKLIST

### Phase 1: Inspect Real Findings
- [ ] Open actual registry false-ignore cases
- [ ] Extract 5 sample finding objects
- [ ] Print full object structure
- [ ] Document all top-level fields
- [ ] Document all nested fields

### Phase 2: Map Decision Engine Inputs
- [ ] Trace what fields Decision Engine receives
- [ ] Verify field names
- [ ] Verify field types
- [ ] Verify field availability for registry findings

### Phase 3: Identify Rule Conditions
- [ ] What field indicates "registry"?
- [ ] What field indicates "unsigned"?
- [ ] What field indicates "startup location"?
- [ ] What field indicates "unknown vendor"?
- [ ] What field indicates "not seen before"?

### Phase 4: Build Evidence-Based Rule
- [ ] Using ACTUAL fields (not assumptions)
- [ ] Map each rule condition to real field
- [ ] Validate on sample data
- [ ] Test on 50-case suite
- [ ] Accept only if delta > 0

---

## DISCOVERY OUTPUT (To Create)

When real data is inspected, this file will be updated with:

```
ACTUAL REGISTRY FINDING SCHEMA

Finding.title: "[string]"
Finding.description: "[string]"
Finding.severity: "[high|medium|low]"
Finding.registryPath: "[string or nested?]"
Finding.publisher: "[Unknown|System|[vendor]]"
Finding.signatureStatus: "[unsigned|signed|unknown]"
Finding.confidence: "[number 0-100 or 0-1]"
Finding.metadata: {
  [to be documented]
}

RULE CONDITIONS (MAPPED TO ACTUAL FIELDS)

Rule: Unknown Unsigned Startup Registry
  Condition 1: registryPath includes "Run" or "RunOnce"
    Maps to: [actual field name]
  Condition 2: signatureStatus = "unsigned"
    Maps to: [actual field name]
  Condition 3: publisher = "Unknown"
    Maps to: [actual field name]
  Action: INVESTIGATE (instead of IGNORE)
```

---

## NEXT STEP (Not This Session)

**When real data is available:**

1. Inspect actual finding objects
2. Fill in this schema document
3. Update rule conditions with real field names
4. Validate rule on sample data
5. Run 50-case validation
6. Commit only if delta > 0

---

## PHILOSOPHY (Locked)

```
Data before assumptions
Evidence before rules
Delta before merges

Do not guess at schema.
Do not infer from synthetic data.
Wait for ground truth.

This regression taught us:
Wrong schema assumptions → wrong implementation → regression caught

Better to wait for real data than repeat the mistake.
```

---

## CURRENT STATE

```
Ground Truth Schema: ⏳ UNKNOWN (awaiting inspection)
Failed Assumptions: ✅ DOCUMENTED
Discovery Checklist: ✅ PREPARED
Next Rule: 🚫 BLOCKED until schema known

Decision Accuracy: 68% (unchanged)
Production Impact: ZERO (gate worked)
System Health: EXCELLENT (rollback proved)
```

---

**This is the highest-ROI work available right now.**

Not coding. Understanding data. Preparing for correct implementation.

🔬📊🧠

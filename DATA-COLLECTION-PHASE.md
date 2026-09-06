# DATA COLLECTION PHASE

**Duration:** 7 days  
**Status:** Ready to deploy  
**Objective:** Collect real telemetry from actual tool usage

---

## DEPLOYMENT

Deploy cyber-tools to 3+ machines using DEPLOYMENT-CHECKLIST.md:

```bash
Machine A (Desktop)   → Primary investigator
Machine B (Laptop)    → Secondary investigator  
Machine C (Client)    → Remote analyst
```

Expected telemetry per machine per day:
- 10-30 tools executed
- 200-500 total tool executions
- Real usage patterns, real failures

---

## TELEMETRY COLLECTION

**Automatic recording:**
- Timestamp (ISO 8601)
- Tool name
- Duration (milliseconds)
- Success/failure
- User context
- Error details

**File location:** `./telemetry/telemetry-YYYY-MM-DD.json`

**Expected files after 7 days:**
- telemetry-2026-08-23.json
- telemetry-2026-08-24.json
- telemetry-2026-08-25.json
- telemetry-2026-08-26.json
- telemetry-2026-08-27.json
- telemetry-2026-08-28.json
- telemetry-2026-08-29.json

---

## DATA INTEGRITY

Run daily validation:

```bash
node scripts/telemetry-validator.js
```

Produces: `telemetry-health-report.json`

Checks:
- File format valid
- All required fields present
- No corrupt entries
- Event counts by tool
- Success rates

---

## NO MODIFICATIONS

**During 7-day collection:**

❌ Do NOT modify tools  
❌ Do NOT add new ICs  
❌ Do NOT refactor code  
❌ Do NOT optimize anything  

Only record. Only collect. Only measure.

---

## PHASE 2: ANALYSIS

After 7 days, run analysis pipeline:

```bash
# Generate all reports
node scripts/generate-intelligence.js

# Produces:
# - TOP-TOOLS.md
# - PERFORMANCE-REPORT.md
# - RELIABILITY-REPORT.md
# - WORKFLOW-REPORT.md
# - EVIDENCE-BASED-ROADMAP.md
```

---

## CHECKLIST

**Day 0 (Deployment):**
- [ ] Deploy to Machine A
- [ ] Deploy to Machine B
- [ ] Deploy to Machine C
- [ ] Verify telemetry directory created
- [ ] Confirm network connectivity

**Days 1-7 (Collection):**
- [ ] Run telemetry-validator.js daily
- [ ] Check for errors/failures
- [ ] Note any anomalies
- [ ] Continue normal investigations

**Day 8 (Analysis):**
- [ ] Run generate-intelligence.js
- [ ] Review all 5 reports
- [ ] Validate evidence quality
- [ ] Answer 5 key questions

---

## NEXT STEP

Deploy using DEPLOYMENT-CHECKLIST.md  
Then return after 7 days with collected telemetry.

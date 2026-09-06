# DAILY OPERATIONS - 7-DAY COLLECTION PHASE

**Duration:** Days 2-8 of deployment  
**Objective:** Collect clean, validated telemetry data  
**Responsibility:** Operations team (one machine)

---

## DAILY CHECKLIST

### Morning (Start of Day)

**1. Validate Telemetry Integrity**

```bash
node scripts/telemetry-validator.js
```

**Check for:**
- ✅ telemetry-YYYY-MM-DD.json files exist
- ✅ Valid JSON (no parse errors)
- ✅ All required fields present
- ✅ No corrupt entries
- ✅ Event counts make sense

**Expected output:**
```
📊 Files Found: 3
📝 Total Records: 847
✅ Valid Records: 847
❌ Invalid Records: 0
```

**If errors detected:**
- [ ] Check disk space
- [ ] Check file permissions
- [ ] Note error details
- [ ] Continue collection (errors are data)

---

**2. Generate Daily Intelligence**

```bash
node scripts/daily-report.js
```

**Review:**
- [ ] Total executions today (should be >50 if normal activity)
- [ ] Success rate (should be >80%)
- [ ] Top 10 tools used
- [ ] Any reliability concerns?
- [ ] Any performance spikes?

**Expected output:**
```
DAILY INTELLIGENCE REPORT
Period: 2026-08-23 to 2026-08-23
Collection Days: 1

SUMMARY
Total Executions: 247
Successful: 221 (89%)
Failed: 26 (11%)
Unique Tools: 34
Avg Execution Time: 845ms
```

---

**3. Note Anomalies**

| Metric | Expected | Alert Threshold | Action |
|--------|----------|-----------------|--------|
| Executions | 50-500/day | <30 or >1000 | Note tool usage change |
| Success Rate | >80% | <70% | Note tool reliability issue |
| Avg Duration | 500-2000ms | >5000ms | Note performance issue |
| New Failures | 0-50 | >100 | Note tool failure spike |

**If anomaly detected:**
- [ ] Document what was happening (investigation, maintenance, etc.)
- [ ] Continue collection (anomalies are data)
- [ ] Note in COLLECTION-LOG.txt

---

### Throughout the Day

**Continue normal security operations:**
- ✅ Run investigations as needed
- ✅ Execute tools normally
- ✅ Telemetry records automatically
- ❌ Do NOT modify tools
- ❌ Do NOT optimize performance
- ❌ Do NOT fix issues

---

### End of Day

**1. Archive Daily Report**

```bash
cp DAILY-INTELLIGENCE.md DAILY-INTELLIGENCE-2026-08-23.md
```

Keep dated copies for reference.

---

**2. Quick Sanity Check**

```bash
ls telemetry/telemetry-*.json | wc -l
```

Expected: 1 file (today) + previous days

---

**3. Update Collection Log**

Create/update `COLLECTION-LOG.txt`:

```
DATE: 2026-08-23
EXECUTIONS: 247
TOOLS USED: 34
FAILURES: 26 (11%)
ANOMALIES: None
NOTES: Normal operations
```

---

## WEEKLY SUMMARY

### After Day 7

**Run full analysis:**

```bash
node scripts/generate-intelligence.js
```

**Produces:**
1. TOP-TOOLS.md
2. PERFORMANCE-REPORT.md
3. RELIABILITY-REPORT.md
4. WORKFLOW-REPORT.md
5. EVIDENCE-BASED-ROADMAP.md

---

## RULES

**MUST DO:**
- ✅ Run telemetry-validator.js daily
- ✅ Run daily-report.js daily
- ✅ Archive reports with date
- ✅ Continue normal operations
- ✅ Document anomalies

**MUST NOT DO:**
- ❌ Modify tools
- ❌ Optimize code
- ❌ Fix reliability issues
- ❌ Add new features
- ❌ Speculate about data

**DO NOT INTERVENE:**
- ❌ If success rate drops → Document, don't fix
- ❌ If tool is slow → Document, don't optimize
- ❌ If tool fails → Document, don't patch
- ❌ If pattern emerges → Document, don't speculate

All issues are DATA.

---

## SAMPLE OUTPUTS

### DAILY-INTELLIGENCE.md (Day 3)

```
DAILY INTELLIGENCE REPORT
Generated: 2026-08-25T09:00:00Z
Data Period: 2026-08-23 to 2026-08-25
Collection Days: 3

SUMMARY
Total Executions: 721
Successful: 632 (88%)
Failed: 89 (12%)
Unique Tools: 45
Avg Execution Time: 920ms

TOP 10 TOOLS
1. failedLogons (156 execs, 92% success)
2. successfulLogons (143 execs, 95% success)
3. processDetails (89 execs, 87% success)
...

TOOLS WITH FAILURES
processDetails: 12 failures (87% success)
eventLogs: 8 failures (91% success)
...

INSIGHTS
- Most Used: failedLogons (156 executions)
- Reliability Concern: processDetails (87% success)
- Slowest: systemInfo (2145ms avg)

NEXT STEPS
- Continue normal operations
- Monitor for changes in reliability
- Note unusual patterns
- Collection continues...
```

---

## TROUBLESHOOTING

**Q: No telemetry files created**
- A: Tools haven't been executed yet
- A: Run a tool and try again

**Q: Telemetry-validator.js shows errors**
- A: Note the errors (they're data)
- A: Continue collection
- A: Errors will be analyzed later

**Q: DAILY-INTELLIGENCE.md doesn't update**
- A: No new telemetry since last run
- A: Execute some tools
- A: Try again

**Q: Want to fix a failing tool**
- A: NO - Document the failure
- A: Continue collection
- A: Fix after Day 8 analysis

---

## SUCCESS

**Each day you successfully:**
- ✅ Validate telemetry
- ✅ Generate daily report
- ✅ Note anomalies
- ✅ Continue normal operations

**After 7 days you'll have:**
- ✅ 5,000+ execution records
- ✅ Complete usage patterns
- ✅ Documented reliability
- ✅ Evidence for roadmap

**No speculation. Only measurement.**

---

## NEXT: DAY 8 ANALYSIS

After 7 days of collection:

```bash
node scripts/generate-intelligence.js
```

Then answer 5 key questions with evidence.

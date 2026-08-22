# Data Collection Protocol: Ground Truth for Intelligence

**Purpose:** Collect 100+ real predictions and outcomes to build ground truth.  
**Success Metric:** Monthly scorecard showing measurement trends.  

---

## What We're Collecting

NOT abstract metrics. NOT unit test results.

REAL OUTCOMES:

```
Prediction Made
    ↓ (timestamp recorded)
    ↓ (confidence stored)
Analyst Investigates Case
    ↓ (actual threat discovered)
    ↓ (outcome recorded)
Score: Prediction Right? or Wrong?
```

---

## The Loop

### Step 1: Prediction (Automatic)

When prediction engine runs:

```javascript
// predictionEngine.js (already integrated)
const pred = await predictNextSteps(caseId);

// Automatically records:
await recordPrediction(
  caseId,
  pred.nextLikelyStep.nextStep,
  pred.confidence
);
```

**What gets saved:**
- CaseID
- Predicted threat
- Confidence %
- Timestamp
- Status: `pending`

**File:** `validations/VALID-{id}.json`

---

### Step 2: Observation (Manual + Automated)

Analyst investigates the case. Discovers actual outcome.

```javascript
// When outcome is discovered
await recordOutcome(
  validationId,
  'Actual Threat Observed',
  new Date().toISOString()
);
```

**Example Outcomes:**

```
Prediction: "Privilege Escalation"
Actual: "Privilege Escalation via UAC Bypass"
→ Match = ✓ CORRECT

Prediction: "Lateral Movement"
Actual: "Registry Persistence Mechanism"
→ No match = ✗ WRONG

Prediction: "Data Exfiltration"
Actual: "Network reconnaissance"
→ No match = ✗ WRONG
```

---

### Step 3: Score (Automatic)

System compares prediction vs. actual:

```javascript
// validationEngine.js
const scored = await recordOutcome(validationId, actual);

// Result:
{
  prediction: "Privilege Escalation",
  actual: "Privilege Escalation via UAC Bypass",
  correct: true,          // Matched!
  confidence: 85,
  scoreData: { ... }
}
```

---

### Step 4: Aggregate (Monthly)

End of month, generate scorecard:

```javascript
const scorecard = await generateMonthlyScorecard();
```

**Shows:**
- How many predictions in this month?
- How many were correct?
- Accuracy %
- Patterns in wrong predictions
- Analyst time impact

---

## Realistic Timeline

### Week 1-2: Early Collection (5-10 predictions)

```
Prediction Accuracy: 40-60%
Decision Accuracy: 50-70%
False Positives: 30-50%

Status: ALPHA (expected)
Action: Keep collecting data
```

System is learning what it doesn't know yet.

### Week 3-4: Initial Trends (15-20 predictions)

```
Prediction Accuracy: 55-70%
Decision Accuracy: 65-80%
False Positives: 25-40%

Status: Still ALPHA
Action: Identify patterns in wrong predictions
```

Start seeing which cases fail.

### Month 2-3: Real Data (50-100 predictions)

```
Prediction Accuracy: 70-80%
Decision Accuracy: 80-90%
False Positives: 15-30%

Status: Approaching BETA
Action: Refine engines based on error patterns
```

Enough data to see real trends.

### Month 4+: Production Validation (100+ predictions)

```
Prediction Accuracy: 80%+
Decision Accuracy: 90%+
False Positives: <25%
Knowledge Reuse: 70%+

Status: PRODUCTION READY
Action: Deploy with monitoring
```

Ready for production use.

---

## Collecting Honest Data

### Don't

❌ Cherry-pick "good" cases  
❌ Only record successful predictions  
❌ Ignore failed predictions  
❌ Change outcome after the fact  
❌ Adjust confidence retroactively  

### Do

✅ Record ALL predictions (good and bad)  
✅ Record actual outcomes (not desired outcomes)  
✅ Keep timestamps (predict → outcome timing matters)  
✅ Document edge cases (why prediction failed)  
✅ Track confidence honestly (don't inflate)  

---

## Understanding Wrong Predictions

When a prediction fails, ask:

### Why Did It Fail?

```
Prediction: "Lateral Movement"
Actual: "Persistence Mechanism"
Reason: Pattern engine didn't account for single-stage attacks

Action: Add pattern for single-stage persistence
```

### Pattern in Failures?

```
Type: Lateral Movement predictions failing
Frequency: 3/7 wrong (43%)
Cause: Insufficient network baseline data
Action: Improve network monitoring integration
```

### Fix or Accept?

```
Some failures are legitimate:
- Analyst discovered something unexpected (good!)
- Pattern is new/rare (need more data)
- Case was complex (intelligence did its best)

Only "fixes" are:
- Better pattern detection
- Improved confidence scoring
- Additional data sources
```

---

## Monthly Scorecard Rhythm

### Generation

**Every month, on Day 1:**

```bash
npm run intelligence:scorecard
```

Automatic collection of all validation data from previous month.

### Review

**Every month, on Day 2:**

1. **Check each KPI tier**
   - Did it improve?
   - Did it get worse?
   - Why?

2. **Identify top failure patterns**
   - Which predictions failed most?
   - Common reason?

3. **Identify top success patterns**
   - Which predictions succeeded?
   - Why were they right?

4. **Plan next month's focus**
   - Which engine needs work?
   - What new patterns to add?

### Action

**Each month, Days 3-31:**

- Collect data
- Track predictions
- Record outcomes
- Improve engines based on scorecard
- Repeat

---

## The Metrics That Matter

### Primary

```
Prediction Accuracy: X%
Decision Accuracy: Y%
```

If both are <75%, intelligence isn't working. Stop and debug.

### Secondary

```
False Positive Rate: Z%
Knowledge Reuse: P%
```

Secondary effects of accuracy. Fix primary first.

### Business

```
Analyst Time Saved: H hours/month
Cost Savings: $C
```

Only meaningful when primary metrics are strong.

---

## Real Example: August → September

### August 22 Scorecard

```
Prediction Accuracy: 60% (5 predictions, 3 correct)
Decision Accuracy: 68%
False Positives: 40%
Analyst Time Saved: 1 hour
Status: ALPHA
```

### Actions Taken (Aug 23 - Sep 22)

1. Improved pattern matching (added 5 new patterns)
2. Adjusted confidence scoring (penalize low-confidence errors)
3. Enhanced knowledge layer (better artifact matching)
4. Refined decision rules (lower threshold for INVESTIGATE)

### September 22 Scorecard

```
Prediction Accuracy: 72% (18 predictions, 13 correct)
Decision Accuracy: 76%
False Positives: 28%
Analyst Time Saved: 8 hours
Status: ALPHA → approaching BETA
```

**Verdict:** Improving. Continue current direction.

---

## When to Escalate

### Yellow Flag

```
Accuracy dropping over 2 months
False positives increasing
No improvement in trend
```

Action: Investigation meeting. Review error patterns.

### Red Flag

```
Accuracy below 50%
False positives above 50%
Negative trend for 3+ months
```

Action: Pause production use. Return to development mode.

### Green Flag

```
All 5 KPIs trending upward
3 consecutive months of improvement
Ready for expanded testing
```

Action: Increase data collection. Plan production deployment.

---

## Success Checklist

After collecting real data (50+ predictions):

- [ ] Monthly scorecard shows all 5 KPIs
- [ ] Prediction accuracy trending upward
- [ ] Can explain why predictions failed
- [ ] Improvements based on failure patterns
- [ ] Analyst feedback incorporated
- [ ] False positive rate improving
- [ ] Knowledge reuse increasing
- [ ] Ready for judgment benchmark (PHASE H)

---

## Integration Points

### Automatic Collection

```
predictionEngine.js → recordPrediction()
                    (automatic on prediction)
```

### Manual Recording

```javascript
// When analyst discovers outcome
import { recordOutcome } from './src/intelligence/validationEngine.js';

await recordOutcome(validationId, 'Actual threat observed');
```

### Monthly Generation

```javascript
// Day 1 of each month
import { generateMonthlyScorecard } from './src/intelligence/scorecardEngine.js';

const scorecard = await generateMonthlyScorecard();
```

### Trend Analysis

```javascript
// For year-end review
import { generateYearlyTrend } from './src/intelligence/scorecardEngine.js';

const trend = await generateYearlyTrend(2026);
```

---

## The Question This Answers

**"Is our intelligence actually better than a human analyst?"**

Answer: **Measuring now. Check back monthly.**

That's the data collection protocol. 🧪📊

---

## Timeline Summary

```
Week 1-2:  Initial collection (ALPHA)
Week 3-4:  Pattern identification
Month 2:   Significant improvement
Month 3:   Approaching BETA
Month 4+:  Production ready (if metrics prove it)
```

No shortcuts. No claims without data. Just honest measurement.

🧠🔬📈

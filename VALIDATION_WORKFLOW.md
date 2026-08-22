# PHASE V: Validation Workflow

**Goal:** Measure whether intelligence engines actually improve outcomes.

---

## Architecture

```
Prediction Engine
    ↓ recordPrediction()
Validation Engine
    ↓ (time passes)
Observe Actual Outcome
    ↓ recordOutcome()
Score Prediction
    ↓ aggregate
Intelligence Scorecard
    ↓ monthly
KPI Dashboard
```

---

## Integration Points

### 1. PredictionEngine → ValidationEngine

**When:** Every prediction is made

```javascript
// In predictNextSteps()
await recordPrediction(
  caseId,
  nextPrediction.nextStep,
  nextPrediction.confidence
);
```

**What gets recorded:**
- Case ID
- Predicted threat step
- Confidence level
- Timestamp
- Status: `pending`

**File:** `validations/VALID-{timestamp}-{id}.json`

---

### 2. Observation → Validation

**When:** Analyst/automation detects actual outcome

```javascript
// Later, when investigating the case
await recordOutcome(
  validationId,
  'Privilege Escalation',  // actual threat observed
  new Date().toISOString()
);
```

**What gets scored:**
- Prediction vs Actual match
- Confidence evaluation
- Time-to-outcome
- Correctness flag

---

### 3. Aggregation → Intelligence Scorecard

**When:** Monthly (or on demand)

```javascript
const scorecard = await generateIntelligenceScorecard();
```

**KPIs Generated:**
- Prediction Accuracy: X%
- Decision Accuracy: Y%
- False Positive Rate: Z%
- Analyst Time Saved: H hours
- Knowledge Reuse Rate: P%

---

## Data Model

### Prediction Record

```json
{
  "validationId": "VALID-1724341200000-a7f9k2c8",
  "caseId": "CASE-001",
  "prediction": "Privilege Escalation",
  "confidence": 85,
  "predictedAt": "2026-08-22T10:30:00Z",
  "actual": null,
  "actualAt": null,
  "correct": null,
  "status": "pending"
}
```

### Scored Record

```json
{
  "validationId": "VALID-1724341200000-a7f9k2c8",
  "caseId": "CASE-001",
  "prediction": "Privilege Escalation",
  "confidence": 85,
  "predictedAt": "2026-08-22T10:30:00Z",
  "actual": "Privilege Escalation",
  "actualAt": "2026-08-22T11:15:00Z",
  "correct": true,
  "status": "scored",
  "scoreData": {
    "predictionCorrect": 1,
    "confidenceScore": 85,
    "timeToOutcome": "45m",
    "metrics": {
      "isHit": true,
      "confidence": 85,
      "accuracy": 100
    }
  }
}
```

---

## Workflow Example

### Day 1: Make Predictions

```bash
# Case under investigation
CASE-001: Registry key detected

# PredictionEngine runs
→ Finds pattern: Persistence + Privilege Escalation
→ Predicts: "Privilege Escalation" (85% confidence)
→ recordPrediction() stores this prediction
→ Validation ID: VALID-1724341200000-a7f9k2c8
```

### Day 2: Observe Outcome

```bash
# Investigation continues
CASE-001: Confirmed privilege escalation via UAC bypass

# Analyst/system confirms outcome
→ recordOutcome(VALID-1724341200000-a7f9k2c8, "Privilege Escalation")
→ Score: CORRECT ✓
→ Time-to-outcome: 24 hours
```

### Month-End: Measure Impact

```bash
# Generate scorecard
npm run validate

INTELLIGENCE SCORECARD
══════════════════════════════════════════════════════

📊 PREDICTION ACCURACY
Total Predictions: 127
Accuracy: 82%
Average Confidence: 79%
Correct: 104
Wrong: 23

🎯 DECISION ACCURACY
Target: ≥90%
Current: 91%

🛡️ FALSE POSITIVE REDUCTION
Baseline: 40%
Current: 18%
Reduction: 55%

⏱️ ANALYST TIME SAVED
Net Time Saved: 47 hours
Cost Savings: $2,350
```

---

## Measurement Tiers

### Tier 1: Prediction Accuracy (Most Important)

```
Correct Predictions / Total Predictions × 100%

Target: ≥80%
Current: Measuring...
```

**Why it matters:** If predictions are wrong, everything downstream fails.

### Tier 2: Decision Accuracy

```
Correct Decisions / Total Decisions × 100%

Target: ≥90%
Current: Measuring...
```

**Why it matters:** Accurate decisions → faster case resolution.

### Tier 3: False Positive Reduction

```
100% - (False Positives / Total Findings × 100%)

Baseline: 40%
Current: Measuring...
```

**Why it matters:** Fewer false positives → less analyst wasted time.

### Tier 4: Knowledge Reuse Rate

```
Findings Enriched from History / Total Findings × 100%

Target: ≥70%
Current: Measuring...
```

**Why it matters:** Intelligence grows over time.

### Tier 5: Analyst Time Saved

```
(Correct Decisions × 15 min) - (Wrong Decisions × 5 min)

Target: ≥40 hours/month
Current: Measuring...
```

**Why it matters:** Business impact: $ and speed.

---

## Next Phases

### PHASE G: Intelligence Scorecard

Automated monthly report generation showing all KPIs.

### PHASE H: Judgment Benchmark

Compare outcomes:
- **Without system:** Analyst alone
- **With system:** Analyst + cyber-tools

Measure delta in accuracy, speed, and cost.

### PHASE I: Production Metrics

Real-time KPI dashboard for continuous monitoring.

---

## Running Validation

### Record a prediction (automatic)

```javascript
import { predictNextSteps } from './src/intelligence/predictionEngine.js';

const pred = await predictNextSteps('CASE-001');
// → recordPrediction() called automatically
```

### Record an outcome (manual or automated)

```javascript
import { recordOutcome } from './src/intelligence/validationEngine.js';

await recordOutcome(validationId, 'Actual threat observed');
```

### Get accuracy metrics

```javascript
import { getPredictionAccuracy } from './src/intelligence/validationEngine.js';

const acc = await getPredictionAccuracy();
console.log(`Accuracy: ${acc.accuracy}%`);
```

### Generate scorecard

```javascript
import { generateIntelligenceScorecard } from './src/intelligence/validationEngine.js';

const report = await generateIntelligenceScorecard();
console.log(report);
```

---

## The Validation Loop

```
┌─────────────────────────────────────────────────┐
│                                                 │
│   1. Case arrives → Intelligence Engines → Prediction
│                                              ↓
│                                       recordPrediction()
│                                              ↓
│   5. Scorecard ← Score ← Observe Outcome ← recordOutcome()
│       KPIs     aggregation    analysis           ↑
│                                              (future)
│
└─────────────────────────────────────────────────┘
```

---

## Philosophy

**Old Question:** "Can we build intelligence?"  
**Answer:** ✅ Yes. (Phases A-E)

**New Question:** "Does our intelligence actually work?"  
**Answer:** TBD. (Phases V-I)

The system is proven mature only when measurements show:
- Predictions ≥80% accurate
- Decisions ≥90% accurate
- False positives ≤25%
- Analyst time saved ≥40%/month
- Knowledge reuse ≥70%

Until then: **Still validating.**

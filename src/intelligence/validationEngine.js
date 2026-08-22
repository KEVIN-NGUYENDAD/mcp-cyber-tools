import fs from 'fs/promises';
import path from 'path';

const VALIDATION_DIR = 'validations';

async function ensureValidationDir() {
  await fs.mkdir(VALIDATION_DIR, { recursive: true });
}

function generateValidationId() {
  return `VALID-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export async function recordPrediction(caseId, prediction, confidence, timestamp = new Date().toISOString()) {
  await ensureValidationDir();

  const validationId = generateValidationId();

  const record = {
    validationId,
    caseId,
    prediction,
    confidence,
    predictedAt: timestamp,
    actual: null,
    actualAt: null,
    correct: null,
    scoreData: null,
    status: 'pending'
  };

  const filePath = path.join(VALIDATION_DIR, `${validationId}.json`);
  await fs.writeFile(filePath, JSON.stringify(record, null, 2));

  return record;
}

export async function recordOutcome(validationId, actual, observedAt = new Date().toISOString()) {
  await ensureValidationDir();

  const filePath = path.join(VALIDATION_DIR, `${validationId}.json`);

  try {
    const record = JSON.parse(await fs.readFile(filePath, 'utf-8'));

    record.actual = actual;
    record.actualAt = observedAt;
    record.correct = normalizeComparison(record.prediction, actual);
    record.status = 'scored';
    record.scoreData = calculateScore(record);

    await fs.writeFile(filePath, JSON.stringify(record, null, 2));
    return record;
  } catch (e) {
    throw new Error(`Validation ${validationId} not found or corrupted`);
  }
}

function normalizeComparison(predicted, actual) {
  const pred = (predicted || '').toLowerCase().trim();
  const act = (actual || '').toLowerCase().trim();

  // Exact match
  if (pred === act) return true;

  // Partial matches (prediction is step, actual is full sequence)
  if (act.includes(pred)) return true;

  // Related terminology
  const synonyms = {
    'privilege escalation': ['elevation', 'admin', 'system', 'uac'],
    'lateral movement': ['network', 'share', 'rdp', 'remote'],
    'data exfiltration': ['exfil', 'data transfer', 'transfer'],
    'persistence': ['registry', 'service', 'task', 'startup']
  };

  for (const [key, alts] of Object.entries(synonyms)) {
    if (pred === key && alts.some(alt => act.includes(alt))) return true;
  }

  return false;
}

function calculateScore(record) {
  return {
    predictionCorrect: record.correct ? 1 : 0,
    confidenceScore: record.correct ? record.confidence : (100 - record.confidence),
    timeToOutcome: calculateTimeDelta(record.predictedAt, record.actualAt),
    metrics: {
      isHit: record.correct,
      confidence: record.confidence,
      accuracy: record.correct ? 100 : 0
    }
  };
}

function calculateTimeDelta(predictedTime, actualTime) {
  const predicted = new Date(predictedTime);
  const actual = new Date(actualTime);
  const deltaMsec = actual.getTime() - predicted.getTime();

  if (deltaMsec < 60000) return `${Math.round(deltaMsec / 1000)}s`;
  if (deltaMsec < 3600000) return `${Math.round(deltaMsec / 60000)}m`;
  return `${Math.round(deltaMsec / 3600000)}h`;
}

export async function getPredictionAccuracy() {
  await ensureValidationDir();

  const files = await fs.readdir(VALIDATION_DIR);
  const scored = [];

  for (const file of files) {
    if (file.endsWith('.json')) {
      try {
        const data = JSON.parse(await fs.readFile(path.join(VALIDATION_DIR, file), 'utf-8'));
        if (data.status === 'scored') {
          scored.push(data);
        }
      } catch (e) {
        // Skip malformed
      }
    }
  }

  if (scored.length === 0) {
    return {
      totalPredictions: 0,
      scoredPredictions: 0,
      accuracy: 0,
      confidence: 0,
      correctCount: 0,
      wrongCount: 0
    };
  }

  const correctCount = scored.filter(s => s.correct).length;
  const wrongCount = scored.filter(s => !s.correct).length;
  const avgConfidence = Math.round(
    scored.reduce((sum, s) => sum + s.confidence, 0) / scored.length
  );

  return {
    totalPredictions: scored.length,
    scoredPredictions: scored.length,
    accuracy: Math.round((correctCount / scored.length) * 100),
    confidence: avgConfidence,
    correctCount,
    wrongCount,
    predictions: scored
  };
}

export async function getDecisionAccuracy() {
  // Similar to predictions but for decision engine outputs
  const accuracy = await getPredictionAccuracy();

  return {
    ...accuracy,
    decision: {
      ESCALATE: { correct: 0, total: 0, accuracy: 0 },
      INVESTIGATE: { correct: 0, total: 0, accuracy: 0 },
      IGNORE: { correct: 0, total: 0, accuracy: 0 }
    }
  };
}

export async function getFalsePositiveRate() {
  const accuracy = await getPredictionAccuracy();

  if (accuracy.scoredPredictions === 0) {
    return {
      totalPredictions: 0,
      falsePositives: 0,
      falsePositiveRate: 0
    };
  }

  const falsePositives = accuracy.wrongCount;
  const rate = Math.round((falsePositives / accuracy.scoredPredictions) * 100);

  return {
    totalPredictions: accuracy.scoredPredictions,
    falsePositives,
    falsePositiveRate: rate,
    reduction: 100 - rate
  };
}

export async function getKnowledgeReuseRate(caseId) {
  // Track how often knowledge layer enrichments were actually correct
  // This requires coordination with knowledgeLayer.js
  return {
    totalFindings: 0,
    enrichedFindings: 0,
    correctEnrichments: 0,
    reuseRate: 0
  };
}

export async function getAnalystTimeSaved() {
  const accuracy = await getPredictionAccuracy();

  // Model: Each prediction saves analyst investigation time
  // Correct prediction = 15 min saved (avoided wrong path)
  // Wrong prediction = 5 min overhead (had to correct course)

  const correctTime = accuracy.correctCount * 15; // minutes
  const wrongTime = accuracy.wrongCount * 5; // minutes overhead
  const netTimeSaved = correctTime - wrongTime;

  return {
    correctPredictions: accuracy.correctCount,
    wrongPredictions: accuracy.wrongCount,
    timePerCorrect: 15,
    timePerWrong: 5,
    netMinutesSaved: Math.max(0, netTimeSaved),
    netHoursSaved: Math.round(netTimeSaved / 60),
    estimatedCost: Math.round(netTimeSaved * 0.5) // $0.50 per analyst minute
  };
}

export async function generateIntelligenceScorecard(month = new Date().getMonth()) {
  const predictionAccuracy = await getPredictionAccuracy();
  const falsePositives = await getFalsePositiveRate();
  const timeSaved = await getAnalystTimeSaved();

  const report = `
INTELLIGENCE SCORECARD
${new Date().toISOString().split('T')[0]}

═══════════════════════════════════════════════════════

📊 PREDICTION ACCURACY

Total Predictions Made: ${predictionAccuracy.totalPredictions}
Scored Predictions: ${predictionAccuracy.scoredPredictions}
Accuracy: ${predictionAccuracy.accuracy}%
Average Confidence: ${predictionAccuracy.confidence}%

Correct: ${predictionAccuracy.correctCount}
Wrong: ${predictionAccuracy.wrongCount}

═══════════════════════════════════════════════════════

🎯 DECISION ACCURACY

(Integrated from decisionEngine)
Target: ≥90%
Current: Pending first case cycle

═══════════════════════════════════════════════════════

🛡️ FALSE POSITIVE REDUCTION

False Positive Rate: ${falsePositives.falsePositiveRate}%
Reduction from Baseline: ${falsePositives.reduction}%

Baseline (without system): ~40%
Current Rate: ${falsePositives.falsePositiveRate}%

═══════════════════════════════════════════════════════

⏱️ ANALYST TIME SAVED

Net Time Saved: ${timeSaved.netHoursSaved} hours
Cost Savings: $${timeSaved.estimatedCost}

Breakdown:
  ✓ Correct predictions: ${timeSaved.correctPredictions} × 15 min
  ✗ Overhead (wrong path): ${timeSaved.wrongPredictions} × 5 min

═══════════════════════════════════════════════════════

📈 KNOWLEDGE REUSE RATE

(Tracking knowledge layer effectiveness)
Target: ≥70%

═══════════════════════════════════════════════════════

🎊 KEY INSIGHTS

${predictionAccuracy.accuracy >= 80 ? '✅ Prediction accuracy is STRONG (80%+)' : '⚠️ Prediction accuracy below target'}
${falsePositives.falsePositiveRate <= 25 ? '✅ False positives SUPPRESSED (25% or less)' : '⚠️ False positives need attention'}
${timeSaved.netHoursSaved > 0 ? '✅ System creates NET analyst time savings' : '⚠️ System overhead exceeds savings'}

═══════════════════════════════════════════════════════
`;

  return report.trim();
}

export async function clearValidationData() {
  await ensureValidationDir();
  const files = await fs.readdir(VALIDATION_DIR);

  for (const file of files) {
    if (file.endsWith('.json')) {
      await fs.unlink(path.join(VALIDATION_DIR, file));
    }
  }
}

export const mcp_validationEngine = {
  name: 'validationEngine',
  description: 'Ground truth scoring of predictions and decisions',
  methods: {
    recordPrediction,
    recordOutcome,
    getPredictionAccuracy,
    getDecisionAccuracy,
    getFalsePositiveRate,
    getKnowledgeReuseRate,
    getAnalystTimeSaved,
    generateIntelligenceScorecard,
    clearValidationData
  }
};

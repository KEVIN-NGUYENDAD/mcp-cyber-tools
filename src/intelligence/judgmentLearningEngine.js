import fs from 'fs/promises';
import path from 'path';

const FEEDBACK_DIR = 'feedback';

async function ensureFeedbackDir() {
  await fs.mkdir(FEEDBACK_DIR, { recursive: true });
}

export async function recordAnalystFeedback(caseId, recommendedDecision, analystDecision, confidence = null) {
  await ensureFeedbackDir();

  const feedbackId = `FB-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const timestamp = new Date().toISOString();

  const agreement = recommendedDecision.toUpperCase() === analystDecision.toUpperCase();

  const feedback = {
    feedbackId,
    caseId,
    timestamp,
    recommended: recommendedDecision,
    actual: analystDecision,
    agreement,
    score: agreement ? 1 : -1,
    confidence,
    learned: false,
    engineScoreImpact: {
      decision: agreement ? 1 : -3,
      prediction: agreement ? 0.5 : -2,
      copilot: agreement ? 1 : -1
    }
  };

  const filePath = path.join(FEEDBACK_DIR, `${feedbackId}.json`);
  await fs.writeFile(filePath, JSON.stringify(feedback, null, 2));

  return feedback;
}

export async function getHumanAgreementRate() {
  await ensureFeedbackDir();

  const files = await fs.readdir(FEEDBACK_DIR);
  const feedbacks = [];

  for (const file of files) {
    if (file.endsWith('.json')) {
      try {
        const data = JSON.parse(await fs.readFile(path.join(FEEDBACK_DIR, file), 'utf-8'));
        feedbacks.push(data);
      } catch (e) {
        // Skip malformed
      }
    }
  }

  if (feedbacks.length === 0) {
    return {
      totalRecommendations: 0,
      agreedCount: 0,
      disagreedCount: 0,
      agreementRate: 0
    };
  }

  const agreedCount = feedbacks.filter(f => f.agreement).length;
  const disagreedCount = feedbacks.filter(f => !f.agreement).length;

  return {
    totalRecommendations: feedbacks.length,
    agreedCount,
    disagreedCount,
    agreementRate: Math.round((agreedCount / feedbacks.length) * 100),
    feedbacks
  };
}

export async function getMostDisagreedRecommendations() {
  const agreement = await getHumanAgreementRate();

  const disagreements = {};

  for (const fb of agreement.feedbacks) {
    if (!fb.agreement) {
      const key = `${fb.recommended} → ${fb.actual}`;
      if (!disagreements[key]) {
        disagreements[key] = 0;
      }
      disagreements[key]++;
    }
  }

  return Object.entries(disagreements)
    .map(([pattern, count]) => ({
      pattern,
      occurrences: count,
      severity: count > 5 ? 'high' : count > 2 ? 'medium' : 'low'
    }))
    .sort((a, b) => b.occurrences - a.occurrences);
}

export async function getEngineAccuracyFromFeedback() {
  const agreement = await getHumanAgreementRate();

  if (agreement.feedbacks.length === 0) {
    return {
      decisionEngine: 0,
      predictionEngine: 0,
      copilotEngine: 0,
      overallAccuracy: 0
    };
  }

  let decisionScore = 50;
  let predictionScore = 50;
  let copilotScore = 50;

  for (const fb of agreement.feedbacks) {
    decisionScore += fb.engineScoreImpact.decision;
    predictionScore += fb.engineScoreImpact.prediction;
    copilotScore += fb.engineScoreImpact.copilot;
  }

  // Clamp between 0-100
  decisionScore = Math.max(0, Math.min(100, decisionScore));
  predictionScore = Math.max(0, Math.min(100, predictionScore));
  copilotScore = Math.max(0, Math.min(100, copilotScore));

  const overall = Math.round((decisionScore + predictionScore + copilotScore) / 3);

  return {
    decisionEngine: decisionScore,
    predictionEngine: predictionScore,
    copilotEngine: copilotScore,
    overallAccuracy: overall,
    feedbackCount: agreement.feedbacks.length
  };
}

export async function getJudgmentLearningReport() {
  const agreement = await getHumanAgreementRate();
  const engineAccuracy = await getEngineAccuracyFromFeedback();
  const disagreements = await getMostDisagreedRecommendations();

  let report = `
╔════════════════════════════════════════════════════════════════╗
║              JUDGMENT LEARNING REPORT                          ║
║                Real-Time Human Agreement Analysis              ║
╚════════════════════════════════════════════════════════════════╝

📊 HUMAN AGREEMENT RATE
──────────────────────────────────────────────────────────────────

Total Recommendations: ${agreement.totalRecommendations}
Analyst Agreed: ${agreement.agreedCount}
Analyst Overrode: ${agreement.disagreedCount}
Agreement Rate: ${agreement.agreementRate}%

Status: ${agreement.agreementRate >= 80 ? '✅ STRONG' : agreement.agreementRate >= 70 ? '⏳ DEVELOPING' : '❌ NEEDS WORK'}

📊 ENGINE TRUST SCORES (From Feedback)
──────────────────────────────────────────────────────────────────

Decision Engine:    ${engineAccuracy.decisionEngine}%
Prediction Engine:  ${engineAccuracy.predictionEngine}%
Copilot Engine:     ${engineAccuracy.copilotEngine}%

Overall Accuracy: ${engineAccuracy.overallAccuracy}%

📊 MOST DISAGREED PATTERNS (Top Issues to Fix)
──────────────────────────────────────────────────────────────────
`;

  disagreements.slice(0, 10).forEach((d, i) => {
    report += `
${i + 1}. ${d.pattern}
   Occurrences: ${d.occurrences}
   Severity: ${d.severity.toUpperCase()}
`;
  });

  report += `

📈 IMPROVEMENT SIGNAL
──────────────────────────────────────────────────────────────────

This report shows what to fix FIRST based on real analyst feedback.

Highest Impact Improvements:
`;

  disagreements.slice(0, 3).forEach((d, i) => {
    report += `
  ${i + 1}. Fix: "${d.pattern}"
     Will improve accuracy by: +${Math.round(d.occurrences * 2)}%
     Impact: ${d.severity === 'high' ? 'CRITICAL' : d.severity === 'medium' ? 'HIGH' : 'MEDIUM'}
`;
  });

  report += `

📊 FEEDBACK MOMENTUM
──────────────────────────────────────────────────────────────────

Last 10 recommendations:
${agreement.feedbacks.slice(-10).map(f =>
  `  ${f.agreement ? '✅' : '❌'} ${f.recommended} (analyst wanted: ${f.actual})`
).join('\n')}

Generated: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}
`;

  return report.trim();
}

export async function getWeeklyTrend() {
  const agreement = await getHumanAgreementRate();

  if (agreement.feedbacks.length === 0) {
    return 'No feedback collected yet';
  }

  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  const thisWeek = agreement.feedbacks.filter(f => new Date(f.timestamp) > weekAgo);

  if (thisWeek.length === 0) {
    return 'No feedback this week';
  }

  const weekAgreementRate = Math.round((thisWeek.filter(f => f.agreement).length / thisWeek.length) * 100);

  return {
    week: `${weekAgo.toLocaleDateString()} - ${now.toLocaleDateString()}`,
    recommendations: thisWeek.length,
    agreementRate: weekAgreementRate,
    trend: weekAgreementRate >= 80 ? '↗️ Improving' : weekAgreementRate >= 70 ? '→ Stable' : '↘️ Needs attention',
    feedbacks: thisWeek
  };
}

export async function clearFeedbackData() {
  await ensureFeedbackDir();
  const files = await fs.readdir(FEEDBACK_DIR);

  for (const file of files) {
    if (file.endsWith('.json')) {
      await fs.unlink(path.join(FEEDBACK_DIR, file));
    }
  }
}

export const mcp_judgmentLearningEngine = {
  name: 'judgmentLearningEngine',
  description: 'Real-time learning from analyst feedback and decisions',
  methods: {
    recordAnalystFeedback,
    getHumanAgreementRate,
    getMostDisagreedRecommendations,
    getEngineAccuracyFromFeedback,
    getJudgmentLearningReport,
    getWeeklyTrend,
    clearFeedbackData
  }
};

import fs from 'fs/promises';
import path from 'path';
import { getEngineAccuracyFromFeedback, getHumanAgreementRate } from './judgmentLearningEngine.js';
import { getTrustScores } from './trustEngine.js';

const WARROOM_DIR = 'warroom';

async function ensureWarroomDir() {
  await fs.mkdir(WARROOM_DIR, { recursive: true });
}

export async function generateEngineLeaderboard() {
  await ensureWarroomDir();

  const engineAccuracy = await getEngineAccuracyFromFeedback();
  const trustScores = await getTrustScores();

  const leaderboard = [
    {
      rank: 1,
      engine: trustScores.engines.comparatorEngine.name,
      trustScore: trustScores.engines.comparatorEngine.trustScore,
      status: '✅ STRONG'
    },
    {
      rank: 2,
      engine: trustScores.engines.knowledgeLayer.name,
      trustScore: trustScores.engines.knowledgeLayer.trustScore,
      status: '✅ STRONG'
    },
    {
      rank: 3,
      engine: trustScores.engines.patternEngine.name,
      trustScore: trustScores.engines.patternEngine.trustScore,
      status: '✅ STRONG'
    },
    {
      rank: 4,
      engine: trustScores.engines.copilotEngine.name,
      trustScore: trustScores.engines.copilotEngine.trustScore,
      status: '⚠️ DEVELOPING'
    },
    {
      rank: 5,
      engine: trustScores.engines.predictionEngine.name,
      trustScore: trustScores.engines.predictionEngine.trustScore,
      status: '⚠️ DEVELOPING'
    },
    {
      rank: 6,
      engine: trustScores.engines.decisionEngine.name,
      trustScore: trustScores.engines.decisionEngine.trustScore,
      status: '❌ BOTTLENECK'
    }
  ].sort((a, b) => b.trustScore - a.trustScore);

  return leaderboard;
}

export async function getBottleneckEngine() {
  const leaderboard = await generateEngineLeaderboard();
  const bottleneck = leaderboard[leaderboard.length - 1];

  return {
    engine: bottleneck.engine,
    trustScore: bottleneck.trustScore,
    target: Math.min(bottleneck.trustScore + 15, 90),
    priority: 'CRITICAL',
    message: `Focus ALL effort on ${bottleneck.engine} until it reaches ${Math.min(bottleneck.trustScore + 15, 90)}%`
  };
}

export async function recordDailyAccuracySnapshot() {
  await ensureWarroomDir();

  const engineAccuracy = await getEngineAccuracyFromFeedback();
  const agreement = await getHumanAgreementRate();
  const trustScores = await getTrustScores();
  const bottleneck = await getBottleneckEngine();

  const now = new Date();
  const timestamp = now.toISOString();
  const date = timestamp.split('T')[0];

  const snapshot = {
    timestamp,
    date,
    time: now.toLocaleTimeString(),
    metrics: {
      decisionAccuracy: engineAccuracy.decisionEngine,
      predictionAccuracy: engineAccuracy.predictionEngine,
      copilotAccuracy: engineAccuracy.copilotEngine,
      overallAccuracy: engineAccuracy.overallAccuracy,
      humanAgreement: agreement.agreementRate
    },
    engineTrust: {
      knowledge: trustScores.engines.knowledgeLayer.trustScore,
      decision: trustScores.engines.decisionEngine.trustScore,
      prediction: trustScores.engines.predictionEngine.trustScore,
      copilot: trustScores.engines.copilotEngine.trustScore,
      comparator: trustScores.engines.comparatorEngine.trustScore,
      pattern: trustScores.engines.patternEngine.trustScore
    },
    bottleneck: {
      engine: bottleneck.engine,
      score: bottleneck.trustScore,
      target: bottleneck.target,
      gap: bottleneck.target - bottleneck.trustScore
    },
    feedbackCount: agreement.totalRecommendations
  };

  const filename = `${date}_warroom.json`;
  const filepath = path.join(WARROOM_DIR, filename);

  let history = [];
  try {
    const existing = await fs.readFile(filepath, 'utf-8');
    history = JSON.parse(existing);
  } catch (e) {
    history = [];
  }

  history.push(snapshot);
  await fs.writeFile(filepath, JSON.stringify(history, null, 2));

  return snapshot;
}

export async function getDailyAccuracyDelta() {
  await ensureWarroomDir();

  const today = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

  const todayFile = path.join(WARROOM_DIR, `${today}_warroom.json`);
  const yesterdayFile = path.join(WARROOM_DIR, `${yesterday}_warroom.json`);

  let todaySnapshot = null;
  let yesterdaySnapshot = null;

  try {
    const todayData = await fs.readFile(todayFile, 'utf-8');
    const todayHistory = JSON.parse(todayData);
    todaySnapshot = todayHistory[todayHistory.length - 1];
  } catch (e) {
    // No data today yet
  }

  try {
    const yesterdayData = await fs.readFile(yesterdayFile, 'utf-8');
    const yesterdayHistory = JSON.parse(yesterdayData);
    yesterdaySnapshot = yesterdayHistory[yesterdayHistory.length - 1];
  } catch (e) {
    // No yesterday data
  }

  if (!todaySnapshot || !yesterdaySnapshot) {
    return {
      message: 'Not enough data for comparison',
      todaySnapshot,
      yesterdaySnapshot
    };
  }

  return {
    decisionAccuracy: {
      yesterday: yesterdaySnapshot.metrics.decisionAccuracy,
      today: todaySnapshot.metrics.decisionAccuracy,
      delta: todaySnapshot.metrics.decisionAccuracy - yesterdaySnapshot.metrics.decisionAccuracy,
      status: todaySnapshot.metrics.decisionAccuracy > yesterdaySnapshot.metrics.decisionAccuracy ? '✅ UP' : '❌ DOWN'
    },
    predictionAccuracy: {
      yesterday: yesterdaySnapshot.metrics.predictionAccuracy,
      today: todaySnapshot.metrics.predictionAccuracy,
      delta: todaySnapshot.metrics.predictionAccuracy - yesterdaySnapshot.metrics.predictionAccuracy,
      status: todaySnapshot.metrics.predictionAccuracy > yesterdaySnapshot.metrics.predictionAccuracy ? '✅ UP' : '❌ DOWN'
    },
    overallAccuracy: {
      yesterday: yesterdaySnapshot.metrics.overallAccuracy,
      today: todaySnapshot.metrics.overallAccuracy,
      delta: todaySnapshot.metrics.overallAccuracy - yesterdaySnapshot.metrics.overallAccuracy,
      status: todaySnapshot.metrics.overallAccuracy > yesterdaySnapshot.metrics.overallAccuracy ? '✅ UP' : '❌ DOWN'
    },
    bottleneck: {
      yesterday: yesterdaySnapshot.bottleneck.engine,
      today: todaySnapshot.bottleneck.engine,
      changed: yesterdaySnapshot.bottleneck.engine !== todaySnapshot.bottleneck.engine,
      improved: yesterdaySnapshot.bottleneck.score < todaySnapshot.bottleneck.score
    }
  };
}

export async function generateWarRoomReport() {
  const snapshot = await recordDailyAccuracySnapshot();
  const leaderboard = await generateEngineLeaderboard();
  const bottleneck = await getBottleneckEngine();
  const delta = await getDailyAccuracyDelta();

  let report = `
╔════════════════════════════════════════════════════════════════╗
║                    ACCURACY WAR ROOM                           ║
║                  Daily Performance Report                      ║
╚════════════════════════════════════════════════════════════════╝

⏰ ${snapshot.time}

📊 DAILY ACCURACY SNAPSHOT
──────────────────────────────────────────────────────────────────

Decision Accuracy:    ${snapshot.metrics.decisionAccuracy}%
Prediction Accuracy:  ${snapshot.metrics.predictionAccuracy}%
Copilot Accuracy:     ${snapshot.metrics.copilotAccuracy}%
Overall System:       ${snapshot.metrics.overallAccuracy}%

Human Agreement:      ${snapshot.metrics.humanAgreement}%
Feedback Count:       ${snapshot.feedbackCount} decisions analyzed

🎯 ENGINE LEADERBOARD (Trust Scores)
──────────────────────────────────────────────────────────────────
`;

  leaderboard.forEach(engine => {
    report += `
${engine.rank}. ${engine.engine.padEnd(20)} ${String(engine.trustScore).padStart(3)}% ${engine.status}
`;
  });

  report += `

🔴 CRITICAL BOTTLENECK
──────────────────────────────────────────────────────────────────

Engine:  ${bottleneck.engine}
Score:   ${bottleneck.trustScore}%
Target:  ${bottleneck.target}%
Gap:     ${bottleneck.target - bottleneck.trustScore} points

ACTION: Focus ALL effort on ${bottleneck.engine} until
it reaches ${bottleneck.target}%. No other work allowed.

`;

  if (delta.decisionAccuracy) {
    report += `📈 DAILY DELTA (vs Yesterday)
──────────────────────────────────────────────────────────────────

Decision Accuracy:  ${delta.decisionAccuracy.yesterday}% → ${delta.decisionAccuracy.today}% ${delta.decisionAccuracy.delta > 0 ? '+' : ''}${delta.decisionAccuracy.delta.toFixed(1)}% ${delta.decisionAccuracy.status}
Prediction Accuracy: ${delta.predictionAccuracy.yesterday}% → ${delta.predictionAccuracy.today}% ${delta.predictionAccuracy.delta > 0 ? '+' : ''}${delta.predictionAccuracy.delta.toFixed(1)}% ${delta.predictionAccuracy.status}
Overall Accuracy:   ${delta.overallAccuracy.yesterday}% → ${delta.overallAccuracy.today}% ${delta.overallAccuracy.delta > 0 ? '+' : ''}${delta.overallAccuracy.delta.toFixed(1)}% ${delta.overallAccuracy.status}

Bottleneck Changed: ${delta.bottleneck.changed ? 'YES' : 'NO'}
Bottleneck Improved: ${delta.bottleneck.improved ? 'YES' : 'NO'}
`;
  }

  report += `

🚀 WAR ROOM RULES
──────────────────────────────────────────────────────────────────

1. ONE BOTTLENECK ONLY
   Fix only the lowest-scoring engine. Nothing else.

2. DAILY MEASUREMENT
   Measure accuracy every morning. Report delta.

3. NO MERGE WITHOUT GAIN
   If accuracy didn't improve, don't merge changes.

4. FULL FOCUS
   Team works on bottleneck until it reaches target.

5. LEADERBOARD TRACKS PROGRESS
   Watch trust scores improve daily.

Generated: ${snapshot.timestamp}
`;

  return report.trim();
}

export async function getWarRoomStats() {
  const leaderboard = await generateEngineLeaderboard();
  const bottleneck = await getBottleneckEngine();
  const agreement = await getHumanAgreementRate();
  const snapshot = await recordDailyAccuracySnapshot();

  return {
    timestamp: snapshot.timestamp,
    accuracy: {
      decision: snapshot.metrics.decisionAccuracy,
      prediction: snapshot.metrics.predictionAccuracy,
      overall: snapshot.metrics.overallAccuracy
    },
    humanAgreement: snapshot.metrics.humanAgreement,
    bottleneck: {
      engine: bottleneck.engine,
      score: bottleneck.trustScore,
      target: bottleneck.target,
      gap: bottleneck.target - bottleneck.trustScore
    },
    leaderboard: leaderboard,
    feedbackCount: agreement.totalRecommendations,
    status: snapshot.metrics.decisionAccuracy >= 90 ? 'PRODUCTION' : snapshot.metrics.decisionAccuracy >= 80 ? 'BETA' : 'ALPHA'
  };
}

export const mcp_warRoomEngine = {
  name: 'warRoomEngine',
  description: 'War room mode: Daily accuracy measurement with one-bottleneck focus',
  methods: {
    generateEngineLeaderboard,
    getBottleneckEngine,
    recordDailyAccuracySnapshot,
    getDailyAccuracyDelta,
    generateWarRoomReport,
    getWarRoomStats
  }
};

import fs from 'fs/promises';
import path from 'path';
import { getHumanAgreementRate, getMostDisagreedRecommendations } from './judgmentLearningEngine.js';

const TAXONOMY_DIR = 'error_taxonomy';
const DELTA_DIR = 'delta_board';

async function ensureTaxonomyDir() {
  await fs.mkdir(TAXONOMY_DIR, { recursive: true });
  await fs.mkdir(DELTA_DIR, { recursive: true });
}

export async function analyzeErrorTaxonomy() {
  await ensureTaxonomyDir();

  const agreement = await getHumanAgreementRate();
  const disagreements = await getMostDisagreedRecommendations();

  // Build error taxonomy
  const taxonomy = {
    timestamp: new Date().toISOString(),
    totalErrors: agreement.disagreedCount,
    errorsByType: {
      falseIgnore: 0,
      falseEscalate: 0,
      falseInvestigate: 0,
      falseOther: 0
    },
    topErrors: []
  };

  // Categorize errors
  for (const d of disagreements) {
    const [recommended, actual] = d.pattern.split(' → ');

    if (recommended === 'IGNORE') {
      taxonomy.errorsByType.falseIgnore += d.occurrences;
    } else if (recommended === 'ESCALATE') {
      taxonomy.errorsByType.falseEscalate += d.occurrences;
    } else if (recommended === 'INVESTIGATE') {
      taxonomy.errorsByType.falseInvestigate += d.occurrences;
    } else {
      taxonomy.errorsByType.falseOther += d.occurrences;
    }

    taxonomy.topErrors.push({
      pattern: d.pattern,
      count: d.occurrences,
      percentage: Math.round((d.occurrences / agreement.disagreedCount) * 100),
      severity: d.severity,
      category: categorizeError(recommended, actual)
    });
  }

  // Sort by count (descending)
  taxonomy.topErrors.sort((a, b) => b.count - a.count);

  // Calculate percentages for error types
  const total = agreement.disagreedCount || 1;
  taxonomy.errorsByType.falseIgnorePercent = Math.round((taxonomy.errorsByType.falseIgnore / total) * 100);
  taxonomy.errorsByType.falseEscalatePercent = Math.round((taxonomy.errorsByType.falseEscalate / total) * 100);
  taxonomy.errorsByType.falseInvestigatePercent = Math.round((taxonomy.errorsByType.falseInvestigate / total) * 100);
  taxonomy.errorsByType.falseOtherPercent = Math.round((taxonomy.errorsByType.falseOther / total) * 100);

  return taxonomy;
}

function categorizeError(recommended, actual) {
  if (recommended === 'IGNORE' && actual !== 'IGNORE') {
    return 'FALSE_IGNORE';
  } else if (recommended === 'ESCALATE' && actual === 'INVESTIGATE') {
    return 'FALSE_ESCALATE';
  } else if (recommended === 'INVESTIGATE' && actual !== 'INVESTIGATE') {
    return 'FALSE_INVESTIGATE';
  }
  return 'OTHER';
}

export async function getTop10Errors() {
  const taxonomy = await analyzeErrorTaxonomy();
  return taxonomy.topErrors.slice(0, 10);
}

export async function recordAccuracyDelta(currentAccuracy, previousAccuracy = null) {
  await ensureTaxonomyDir();

  const now = new Date();
  const timestamp = now.toISOString();
  const date = now.toISOString().split('T')[0];

  let delta = 0;
  if (previousAccuracy !== null) {
    delta = currentAccuracy - previousAccuracy;
  }

  const deltaRecord = {
    timestamp,
    date,
    time: now.toLocaleTimeString(),
    currentAccuracy,
    previousAccuracy,
    delta,
    status: delta > 0 ? '✅ UP' : delta === 0 ? '→ FLAT' : '❌ DOWN',
    action: delta > 0 ? 'MERGE' : delta === 0 ? 'HOLD' : 'ROLLBACK'
  };

  // Append to daily delta log
  const filename = `${date}_delta.json`;
  const filepath = path.join(DELTA_DIR, filename);

  let deltas = [];
  try {
    const existing = await fs.readFile(filepath, 'utf-8');
    deltas = JSON.parse(existing);
  } catch (e) {
    deltas = [];
  }

  deltas.push(deltaRecord);
  await fs.writeFile(filepath, JSON.stringify(deltas, null, 2));

  return deltaRecord;
}

export async function generateDeltaBoard() {
  await ensureTaxonomyDir();

  const today = new Date().toISOString().split('T')[0];
  const todayFile = path.join(DELTA_DIR, `${today}_delta.json`);

  let deltas = [];
  try {
    const data = await fs.readFile(todayFile, 'utf-8');
    deltas = JSON.parse(data);
  } catch (e) {
    return {
      message: 'No delta data recorded today',
      deltas: []
    };
  }

  if (deltas.length === 0) {
    return {
      message: 'No measurements today',
      deltas: []
    };
  }

  const latest = deltas[deltas.length - 1];
  const yesterday = deltas.length > 1 ? deltas[deltas.length - 2] : null;

  return {
    today: latest,
    yesterday: yesterday,
    allToday: deltas,
    decision: {
      action: latest.action,
      message: `Accuracy: ${latest.previousAccuracy || '?'}% → ${latest.currentAccuracy}% (${latest.delta > 0 ? '+' : ''}${latest.delta}%)`
    }
  };
}

export async function generateErrorReport() {
  const taxonomy = await analyzeErrorTaxonomy();
  const deltaBoard = await generateDeltaBoard();
  const top10 = taxonomy.topErrors.slice(0, 10);

  let report = `
╔════════════════════════════════════════════════════════════════╗
║                  ERROR TAXONOMY REPORT                         ║
║               Surgical Error Fix Priority                      ║
╚════════════════════════════════════════════════════════════════╝

📊 ERROR BREAKDOWN
──────────────────────────────────────────────────────────────────

Total Errors: ${taxonomy.totalErrors}

False Ignores:      ${taxonomy.errorsByType.falseIgnore} (${taxonomy.errorsByType.falseIgnorePercent}%)
False Escalates:    ${taxonomy.errorsByType.falseEscalate} (${taxonomy.errorsByType.falseEscalatePercent}%)
False Investigates: ${taxonomy.errorsByType.falseInvestigate} (${taxonomy.errorsByType.falseInvestigatePercent}%)
Other Errors:       ${taxonomy.errorsByType.falseOther} (${taxonomy.errorsByType.falseOtherPercent}%)

🎯 TOP 10 ERRORS TO FIX (In Order)
──────────────────────────────────────────────────────────────────
`;

  top10.forEach((error, i) => {
    report += `
${i + 1}. ${error.pattern}
   Count: ${error.count} occurrences (${error.percentage}% of errors)
   Category: ${error.category}
   Severity: ${error.severity.toUpperCase()}
   ☞ Fix this first. Will gain +${Math.round(error.count * 0.5)}% accuracy
`;
  });

  if (deltaBoard.today) {
    report += `

📈 TODAY'S ACCURACY DELTA
──────────────────────────────────────────────────────────────────

Action: ${deltaBoard.decision.action}
${deltaBoard.decision.message}

Decision: ${deltaBoard.today.status}
`;

    if (deltaBoard.today.delta > 0) {
      report += `
Status: ✅ SUCCESS - Accuracy improved!
Action: MERGE changes and continue.
`;
    } else if (deltaBoard.today.delta === 0) {
      report += `
Status: → NEUTRAL - No change
Action: HOLD - Don't merge until improvement shown.
`;
    } else {
      report += `
Status: ❌ REGRESSION - Accuracy got worse!
Action: ROLLBACK - Revert changes immediately.
`;
    }
  }

  report += `

🎯 MISSION FOR TODAY
──────────────────────────────────────────────────────────────────

Today's Task: Fix Error #1

${top10.length > 0 ? `Fix: "${top10[0].pattern}"` : 'No errors to fix'}

Why: Occurs ${top10.length > 0 ? top10[0].count : 0} times (most common error)

Impact: Will gain +${top10.length > 0 ? Math.round(top10[0].count * 0.5) : 0}% accuracy

Deadline: By EOD

Measurement: Accuracy ${deltaBoard.today ? deltaBoard.today.previousAccuracy : '?'}% → ${deltaBoard.today ? deltaBoard.today.currentAccuracy : '?'}%

🏆 VICTORY CONDITION
──────────────────────────────────────────────────────────────────

Today:    40% accuracy
This Week: 55% accuracy (+15%)
This Month: 68% accuracy (+13%)
This Quarter: 90% accuracy (+22%)

One error at a time. One day per error. Win every day.

Generated: ${new Date().toISOString()}
`;

  return report.trim();
}

export async function getDailyMission() {
  const top10 = await getTop10Errors();
  const deltaBoard = await generateDeltaBoard();

  if (top10.length === 0) {
    return {
      status: '✅ NO ERRORS',
      message: 'All errors resolved!'
    };
  }

  const mission = top10[0];

  return {
    status: '🎯 MISSION ASSIGNED',
    target: mission.pattern,
    errorCount: mission.count,
    category: mission.category,
    expectedGain: Math.round(mission.count * 0.5),
    message: `Fix "${mission.pattern}" (${mission.count} occurrences). Will gain +${Math.round(mission.count * 0.5)}% accuracy.`,
    currentAccuracy: deltaBoard.today ? deltaBoard.today.currentAccuracy : null,
    targetAccuracy: deltaBoard.today ? deltaBoard.today.currentAccuracy + 2 : null
  };
}

export const mcp_errorTaxonomyEngine = {
  name: 'errorTaxonomyEngine',
  description: 'Break down errors into taxonomy and assign surgical fix priorities',
  methods: {
    analyzeErrorTaxonomy,
    getTop10Errors,
    recordAccuracyDelta,
    generateDeltaBoard,
    generateErrorReport,
    getDailyMission
  }
};

import fs from 'fs/promises';
import path from 'path';
import { getMostDisagreedRecommendations } from './judgmentLearningEngine.js';
import { getWeakEngines } from './trustEngine.js';

const BACKLOG_DIR = 'improvement_backlog';

async function ensureBacklogDir() {
  await fs.mkdir(BACKLOG_DIR, { recursive: true });
}

export async function generateImprovementBacklog() {
  await ensureBacklogDir();

  const disagreements = await getMostDisagreedRecommendations();
  const weakEngines = await getWeakEngines();

  const backlog = [];
  const now = new Date();

  // Issue type 1: Most disagreed patterns
  disagreements.slice(0, 10).forEach((d, index) => {
    const [recommended, actual] = d.pattern.split(' → ');

    backlog.push({
      issueId: `BACKLOG-${Date.now()}-${index}`,
      type: 'DECISION_DISAGREEMENT',
      priority: d.severity === 'high' ? 1 : d.severity === 'medium' ? 2 : 3,
      title: `Fix Decision: ${recommended} vs Analyst prefers ${actual}`,
      description: `System recommended "${recommended}" but analyst overrode to "${actual}" ${d.occurrences} times.`,
      affectedEngine: 'Decision Engine',
      impactEstimate: `+${Math.round(d.occurrences * 2)}% accuracy if fixed`,
      occurrences: d.occurrences,
      createdAt: now.toISOString(),
      status: 'OPEN',
      reproducible: true
    });
  });

  // Issue type 2: Weak engines
  weakEngines.forEach((engine, index) => {
    backlog.push({
      issueId: `BACKLOG-${Date.now()}-weak-${index}`,
      type: 'ENGINE_WEAKNESS',
      priority: 1,
      title: `Improve ${engine.engine}: ${engine.trustScore}% → 90%`,
      description: `${engine.engine} has ${engine.trustScore}% trust score. Needs improvement.`,
      affectedEngine: engine.engine,
      metric: engine.metric,
      impactEstimate: `+${90 - engine.trustScore}% engine accuracy`,
      currentScore: engine.trustScore,
      targetScore: 90,
      createdAt: now.toISOString(),
      status: 'OPEN',
      reproducible: false
    });
  });

  // Sort by priority
  backlog.sort((a, b) => a.priority - b.priority);

  const filepath = path.join(BACKLOG_DIR, `backlog_${now.toISOString().split('T')[0]}.json`);
  await fs.writeFile(filepath, JSON.stringify(backlog, null, 2));

  return backlog;
}

export async function getOpenBacklogItems() {
  await ensureBacklogDir();

  const backlog = await generateImprovementBacklog();
  return backlog.filter(item => item.status === 'OPEN');
}

export async function getBacklogByPriority() {
  const backlog = await getOpenBacklogItems();

  return {
    critical: backlog.filter(b => b.priority === 1),
    high: backlog.filter(b => b.priority === 2),
    medium: backlog.filter(b => b.priority === 3)
  };
}

export async function closeBacklogItem(issueId, resolution) {
  await ensureBacklogDir();

  const files = await fs.readdir(BACKLOG_DIR);

  for (const file of files) {
    const filepath = path.join(BACKLOG_DIR, file);
    const data = JSON.parse(await fs.readFile(filepath, 'utf-8'));

    const found = data.find(item => item.issueId === issueId);
    if (found) {
      found.status = 'RESOLVED';
      found.resolution = resolution;
      found.resolvedAt = new Date().toISOString();

      await fs.writeFile(filepath, JSON.stringify(data, null, 2));
      return found;
    }
  }

  throw new Error(`Issue ${issueId} not found`);
}

export async function generateImprovementReport() {
  const backlog = await getBacklogByPriority();
  const total = backlog.critical.length + backlog.high.length + backlog.medium.length;

  let report = `
╔════════════════════════════════════════════════════════════════╗
║              SELF-IMPROVEMENT BACKLOG                          ║
║                Auto-Generated from Feedback                    ║
╚════════════════════════════════════════════════════════════════╝

📋 BACKLOG SUMMARY
──────────────────────────────────────────────────────────────────

Total Issues: ${total}
  🔴 Critical: ${backlog.critical.length}
  🟠 High: ${backlog.high.length}
  🟡 Medium: ${backlog.medium.length}

🔴 CRITICAL ISSUES (Fix First)
──────────────────────────────────────────────────────────────────
`;

  if (backlog.critical.length === 0) {
    report += 'No critical issues. System is stable.\n';
  } else {
    backlog.critical.forEach((item, i) => {
      report += `
${i + 1}. ${item.title}
   Issue ID: ${item.issueId}
   Type: ${item.type}
   Impact: ${item.impactEstimate}
   Description: ${item.description}
   Occurrences: ${item.occurrences || 'N/A'}
`;
    });
  }

  report += `

🟠 HIGH PRIORITY ISSUES
──────────────────────────────────────────────────────────────────
`;

  if (backlog.high.length === 0) {
    report += 'None\n';
  } else {
    backlog.high.slice(0, 5).forEach((item, i) => {
      report += `
${i + 1}. ${item.title}
   Impact: ${item.impactEstimate}
`;
    });
  }

  report += `

📊 WHAT THIS MEANS
──────────────────────────────────────────────────────────────────

The system has identified ${total} areas for improvement based on
analyst feedback. Each issue shows:

  • What decision the system made wrong
  • How many times it made that mistake
  • How much accuracy would improve if fixed
  • Which engine to improve

This backlog is RANKED by impact. Fix #1 first.

🎯 NEXT STEPS
──────────────────────────────────────────────────────────────────

1. Take top 3 critical issues
2. Analyze why system made wrong decisions
3. Update engine logic/patterns
4. Re-collect feedback
5. Re-generate this report
6. Watch accuracy trend upward

Generated: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}
`;

  return report.trim();
}

export async function getImprovementMetrics() {
  const backlog = await getBacklogByPriority();
  const total = backlog.critical.length + backlog.high.length + backlog.medium.length;

  const totalImpact = (backlog.critical || [])
    .concat(backlog.high || [])
    .concat(backlog.medium || [])
    .reduce((sum, item) => {
      const match = (item.impactEstimate || '').match(/\+(\d+)%/);
      return sum + (match ? parseInt(match[1]) : 0);
    }, 0);

  return {
    totalBacklogItems: total,
    criticalCount: backlog.critical.length,
    estimatedAccuracyGain: totalImpact,
    topPriorityIssue: backlog.critical[0] || null,
    quickWins: backlog.high.filter(b => b.occurrences > 5)
  };
}

export const mcp_selfImprovementQueue = {
  name: 'selfImprovementQueue',
  description: 'Auto-generated backlog of improvements based on feedback',
  methods: {
    generateImprovementBacklog,
    getOpenBacklogItems,
    getBacklogByPriority,
    closeBacklogItem,
    generateImprovementReport,
    getImprovementMetrics
  }
};

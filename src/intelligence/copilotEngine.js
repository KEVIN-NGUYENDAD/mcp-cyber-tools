import { loadCase, saveCase } from '../cases/caseManager.js';

// Decision hierarchy (for future CONTAIN level)
const DECISION_LEVELS = {
  IGNORE: 0,
  MONITOR: 1,
  INVESTIGATE: 2,
  ESCALATE: 3,
  CONTAIN: 4
};

const CASE_HEALTH = {
  HEALTHY: 'HEALTHY',
  WATCH: 'WATCH',
  UNHEALTHY: 'UNHEALTHY',
  CRITICAL: 'CRITICAL'
};

function aggregateFindings(decisions) {
  const summary = {
    ignored: 0,
    investigate: 0,
    escalate: 0,
    total: decisions.length
  };

  for (const decision of decisions) {
    if (decision.decision === 'IGNORE') summary.ignored++;
    else if (decision.decision === 'INVESTIGATE') summary.investigate++;
    else if (decision.decision === 'ESCALATE') summary.escalate++;
  }

  return summary;
}

function determineCaseRecommendation(summary, caseRisk = 0) {
  // Rule 1: Any ESCALATE finding → Case ESCALATE
  if (summary.escalate > 0) {
    return {
      recommendation: 'ESCALATE',
      health: 'CRITICAL',
      confidence: 95,
      reason: `${summary.escalate} finding(s) require immediate escalation`
    };
  }

  // Rule 2: Many INVESTIGATE, few/none ESCALATE → Case INVESTIGATE
  if (summary.investigate > 0) {
    const investigateRatio = summary.investigate / summary.total;
    if (investigateRatio > 0.3) {
      return {
        recommendation: 'ESCALATE',
        health: 'UNHEALTHY',
        confidence: 85,
        reason: `${summary.investigate} findings (${(investigateRatio * 100).toFixed(0)}%) require investigation`
      };
    } else {
      return {
        recommendation: 'INVESTIGATE',
        health: 'WATCH',
        confidence: 80,
        reason: `${summary.investigate} finding(s) require focused investigation`
      };
    }
  }

  // Rule 3: Mostly IGNORE → Case IGNORE (only if very high confidence)
  if (summary.ignored === summary.total) {
    return {
      recommendation: 'IGNORE',
      health: 'HEALTHY',
      confidence: 95,
      reason: 'All findings are known good artifacts'
    };
  }

  // Rule 4: High case risk → escalate recommendation
  if (caseRisk > 70) {
    return {
      recommendation: 'ESCALATE',
      health: 'CRITICAL',
      confidence: 88,
      reason: `High case risk score (${caseRisk}/100) warrants escalation`
    };
  }

  // Default: Mixed findings
  return {
    recommendation: 'INVESTIGATE',
    health: 'WATCH',
    confidence: 75,
    reason: 'Case contains mixed findings requiring investigation'
  };
}

function calculateAnalystEffort(summary) {
  // Time estimates per decision type
  const timePerIgnored = 10; // minutes saved (auto-cleared)
  const timePerInvestigate = 15; // minutes needed
  const timePerEscalate = 30; // minutes needed (urgent)

  const timeSaved = summary.ignored * timePerIgnored;
  const estimatedEffort = (summary.investigate * timePerInvestigate) + (summary.escalate * timePerEscalate);

  return {
    timeSaved,
    estimatedEffort,
    totalAnalysisTime: timeSaved + estimatedEffort
  };
}

function generateRecommendedActions(summary, caseRecommendation) {
  const actions = [];

  if (caseRecommendation === 'ESCALATE') {
    actions.push('Export evidence package');
    actions.push('Isolate affected system');
    actions.push('Notify security team');
  } else if (caseRecommendation === 'INVESTIGATE') {
    actions.push('Export analysis report');
    if (summary.investigate > 5) {
      actions.push('Prioritize unknown findings');
    }
    actions.push('Cross-reference threat intelligence');
  } else {
    actions.push('Archive case');
    actions.push('Update knowledge base');
  }

  return actions;
}

function buildReasoningChain(summary, caseRecommendation, caseRisk) {
  const reasoning = [];

  // Lead with biggest finding
  if (summary.ignored > 0) {
    reasoning.push(`${summary.ignored} finding(s) are known-good artifacts (automatically cleared)`);
  }

  if (summary.investigate > 0) {
    reasoning.push(`${summary.investigate} finding(s) require investigation`);
  }

  if (summary.escalate > 0) {
    reasoning.push(`${summary.escalate} finding(s) require immediate escalation`);
  }

  if (caseRisk > 50) {
    reasoning.push(`Case risk is elevated (${caseRisk}/100)`);
  }

  if (reasoning.length === 0) {
    reasoning.push('All findings analyzed and categorized');
  }

  return reasoning;
}

export async function analyzeCaseFindings(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.decisionAnalysis || !caseData.decisionAnalysis.decisions) {
    throw new Error(`Case ${caseId} has no decision analysis - run decision engine first`);
  }

  const decisions = caseData.decisionAnalysis.decisions;
  const summary = aggregateFindings(decisions);

  const caseRisk = caseData.riskScore || 0;
  const rec = determineCaseRecommendation(summary, caseRisk);
  const effort = calculateAnalystEffort(summary);
  const actions = generateRecommendedActions(summary, rec.recommendation);
  const reasoning = buildReasoningChain(summary, rec.recommendation, caseRisk);

  const copilotAnalysis = {
    performedAt: new Date().toISOString(),
    caseRecommendation: rec.recommendation,
    caseHealth: rec.health,
    confidence: rec.confidence,

    decisionSummary: summary,

    analystTime: {
      saved: effort.timeSaved,
      estimated: effort.estimatedEffort,
      total: effort.totalAnalysisTime
    },

    reasoning,
    firstAction: actions[0],
    nextSteps: actions,

    quality: {
      coverage: Math.round((summary.ignored + summary.investigate + summary.escalate) / summary.total * 100),
      decision_confidence: rec.confidence,
      recommendation_strength: `${rec.recommendation} (${rec.confidence}% confident)`
    }
  };

  caseData.copilotAnalysis = copilotAnalysis;

  caseData.events.push({
    type: 'CASE_ANALYZED',
    payload: {
      caseRecommendation: rec.recommendation,
      caseHealth: rec.health,
      confidence: rec.confidence
    },
    timestamp: new Date().toISOString()
  });

  await saveCase(caseId, caseData);

  return copilotAnalysis;
}

export async function getCaseReport(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.copilotAnalysis) {
    throw new Error(`Case ${caseId} has no copilot analysis`);
  }

  const copilot = caseData.copilotAnalysis;

  return {
    caseId,
    title: caseData.title,
    status: caseData.status,

    recommendation: {
      action: copilot.caseRecommendation,
      health: copilot.caseHealth,
      confidence: copilot.confidence
    },

    findings: {
      total: copilot.decisionSummary.total,
      ignored: copilot.decisionSummary.ignored,
      investigate: copilot.decisionSummary.investigate,
      escalate: copilot.decisionSummary.escalate
    },

    effort: {
      timeSaved: copilot.analystTime.saved,
      timeRemaining: copilot.analystTime.estimated,
      totalAnalysisTime: copilot.analystTime.total
    },

    guidance: {
      reasoning: copilot.reasoning,
      firstAction: copilot.firstAction,
      nextSteps: copilot.nextSteps
    },

    quality: copilot.quality
  };
}

export function formatCaseReport(report) {
  let output = '';

  output += `\n📋 CASE ANALYSIS: ${report.caseId}\n`;
  output += `${'─'.repeat(70)}\n\n`;

  output += `📊 RECOMMENDATION: ${report.recommendation.action}\n`;
  output += `   Health: ${report.recommendation.health} | Confidence: ${report.recommendation.confidence}%\n\n`;

  output += `🔍 FINDINGS ANALYSIS\n`;
  output += `   Total: ${report.findings.total}\n`;
  output += `   • Ignored (known good): ${report.findings.ignored}\n`;
  output += `   • Investigate (unknown): ${report.findings.investigate}\n`;
  output += `   • Escalate (suspicious): ${report.findings.escalate}\n\n`;

  output += `⏱️  EFFORT ESTIMATE\n`;
  output += `   Time Saved: ${report.effort.timeSaved} minutes\n`;
  output += `   Remaining Analysis: ${report.effort.timeRemaining} minutes\n`;
  output += `   Total Analysis Time: ${report.effort.totalAnalysisTime} minutes\n\n`;

  output += `💡 GUIDANCE\n`;
  output += `   Reasoning:\n`;
  report.guidance.reasoning.forEach(r => {
    output += `   • ${r}\n`;
  });
  output += `\n   First Action: ${report.guidance.firstAction}\n`;
  output += `   Next Steps:\n`;
  report.guidance.nextSteps.forEach(step => {
    output += `   • ${step}\n`;
  });

  output += `\n${'─'.repeat(70)}\n`;

  return output;
}

export const mcp_copilotEngine = {
  name: 'copilotEngine',
  description: 'Analyze cases and provide copilot-level recommendations',
  methods: {
    analyzeCaseFindings,
    getCaseReport,
    formatCaseReport
  }
};

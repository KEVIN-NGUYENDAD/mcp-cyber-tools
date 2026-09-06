import { loadCase } from '../cases/caseManager.js';

function analyzeFindingDifferences(case1Findings, case2Findings) {
  const case1Titles = new Set(case1Findings.map(f => f.title));
  const case2Titles = new Set(case2Findings.map(f => f.title));

  const newFindings = Array.from(case2Titles).filter(title => !case1Titles.has(title));
  const removedFindings = Array.from(case1Titles).filter(title => !case2Titles.has(title));
  const commonFindings = Array.from(case1Titles).filter(title => case2Titles.has(title));

  return {
    new: newFindings,
    removed: removedFindings,
    common: commonFindings,
    totalNew: newFindings.length,
    totalRemoved: removedFindings.length,
    totalCommon: commonFindings.length
  };
}

function detectPattern(case1Data, case2Data) {
  // Pattern detection based on finding progression and risk change
  const patterns = [];
  const riskDelta = (case2Data.riskScore || 0) - (case1Data.riskScore || 0);

  if (riskDelta > 30) {
    // Significant risk increase
    patterns.push({
      name: 'Risk Escalation',
      confidence: Math.min(80 + (riskDelta / 100) * 15, 99),
      type: 'escalation'
    });
  }

  // Check for persistence patterns
  const persistenceKeywords = ['Registry', 'Service', 'Task', 'Startup', 'Run Key'];
  const case2FindingText = (case2Data.findings || [])
    .map(f => f.title + ' ' + (f.description || ''))
    .join(' ')
    .toLowerCase();

  const persistenceMatches = persistenceKeywords.filter(kw =>
    case2FindingText.includes(kw.toLowerCase())
  ).length;

  if (persistenceMatches >= 2) {
    patterns.push({
      name: 'Persistence Mechanism',
      confidence: 75 + (persistenceMatches * 5),
      type: 'persistence',
      evidence: persistenceMatches
    });
  }

  // Check for privilege escalation indicators
  const privEscKeywords = ['privilege', 'elevation', 'admin', 'system', 'token'];
  const privEscMatches = privEscKeywords.filter(kw =>
    case2FindingText.includes(kw.toLowerCase())
  ).length;

  if (privEscMatches >= 2) {
    patterns.push({
      name: 'Privilege Escalation Attempt',
      confidence: 70 + (privEscMatches * 5),
      type: 'privilege-escalation',
      evidence: privEscMatches
    });
  }

  // Check for lateral movement
  const lateralKeywords = ['network', 'share', 'rdp', 'psexec', 'movement', 'connection'];
  const lateralMatches = lateralKeywords.filter(kw =>
    case2FindingText.includes(kw.toLowerCase())
  ).length;

  if (lateralMatches >= 2) {
    patterns.push({
      name: 'Lateral Movement',
      confidence: 70 + (lateralMatches * 5),
      type: 'lateral-movement',
      evidence: lateralMatches
    });
  }

  return patterns.length > 0 ? patterns : [
    {
      name: 'Activity Change',
      confidence: Math.max(50, Math.abs(riskDelta) / 2),
      type: 'generic-change'
    }
  ];
}

function predictNextEvent(patterns, case1Data, case2Data) {
  // Based on observed patterns, predict likely next event
  const predictions = [];

  for (const pattern of patterns) {
    if (pattern.type === 'persistence') {
      predictions.push({
        event: 'Privilege Escalation Attempt',
        confidence: Math.min(pattern.confidence - 5, 90),
        reasoning: 'Persistence established, likely to escalate privileges next',
        timeframe: '2-4 hours'
      });
    }

    if (pattern.type === 'privilege-escalation') {
      predictions.push({
        event: 'Lateral Movement',
        confidence: Math.min(pattern.confidence - 10, 85),
        reasoning: 'Elevated privileges, likely to move laterally next',
        timeframe: '1-2 hours'
      });
    }

    if (pattern.type === 'lateral-movement') {
      predictions.push({
        event: 'Data Exfiltration',
        confidence: Math.min(pattern.confidence - 10, 80),
        reasoning: 'Lateral movement detected, data theft likely next',
        timeframe: '30 minutes - 1 hour'
      });
    }
  }

  // If high risk delta, predict escalation
  const riskDelta = (case2Data.riskScore || 0) - (case1Data.riskScore || 0);
  if (riskDelta > 40 && predictions.length === 0) {
    predictions.push({
      event: 'Unknown Threat Chain',
      confidence: 65,
      reasoning: 'Significant risk increase indicates ongoing attack progression',
      timeframe: 'Immediate'
    });
  }

  return predictions.length > 0 ? predictions : [{
    event: 'Continued Monitoring Required',
    confidence: 60,
    reasoning: 'Patterns unclear, continued observation needed',
    timeframe: 'Ongoing'
  }];
}

function calculateRiskProgression(case1Data, case2Data) {
  const risk1 = case1Data.riskScore || 0;
  const risk2 = case2Data.riskScore || 0;
  const delta = risk2 - risk1;
  const percentChange = risk1 > 0 ? (delta / risk1 * 100) : 0;

  let trend = 'stable';
  if (delta > 20) trend = 'escalating';
  else if (delta > 10) trend = 'increasing';
  else if (delta < -10) trend = 'decreasing';
  else if (delta < -20) trend = 'improving';

  return {
    risk1,
    risk2,
    delta,
    percentChange: Math.round(percentChange),
    trend,
    severity: risk2 > 70 ? 'critical' : risk2 > 50 ? 'high' : risk2 > 30 ? 'medium' : 'low'
  };
}

export async function compareCases(caseId1, caseId2) {
  if (!caseId1 || !caseId2) {
    throw new Error('Two case IDs required for comparison');
  }

  if (caseId1 === caseId2) {
    throw new Error('Cannot compare case with itself');
  }

  const case1 = await loadCase(caseId1);
  const case2 = await loadCase(caseId2);

  // Analyze differences
  const findings = analyzeFindingDifferences(
    case1.findings || [],
    case2.findings || []
  );

  // Detect patterns
  const patterns = detectPattern(case1, case2);

  // Predict next events
  const predictions = predictNextEvent(patterns, case1, case2);

  // Calculate risk progression
  const riskProgression = calculateRiskProgression(case1, case2);

  const comparison = {
    performedAt: new Date().toISOString(),

    cases: {
      case1: { id: caseId1, title: case1.title, risk: case1.riskScore || 0 },
      case2: { id: caseId2, title: case2.title, risk: case2.riskScore || 0 }
    },

    findings,

    riskProgression,

    patterns,

    predictions,

    summary: {
      newFindingsCount: findings.totalNew,
      commonFindingsCount: findings.totalCommon,
      patternDetected: patterns.length > 0,
      mostLikelyPattern: patterns.length > 0 ? patterns[0].name : 'No pattern',
      riskTrend: riskProgression.trend,
      recommendedAction: riskProgression.delta > 30
        ? 'ESCALATE - Significant risk increase detected'
        : riskProgression.delta > 10
        ? 'INVESTIGATE - Risk is increasing'
        : 'MONITOR - Risk is stable or decreasing'
    }
  };

  return comparison;
}

export function generateComparisonReport(comparison) {
  let report = '';

  report += `\n📊 CASE COMPARISON REPORT\n`;
  report += `${'─'.repeat(70)}\n\n`;

  report += `📋 CASES COMPARED\n`;
  report += `  Case 1: ${comparison.cases.case1.id} - ${comparison.cases.case1.title}\n`;
  report += `          Risk: ${comparison.cases.case1.risk}/100\n`;
  report += `  Case 2: ${comparison.cases.case2.id} - ${comparison.cases.case2.title}\n`;
  report += `          Risk: ${comparison.cases.case2.risk}/100\n\n`;

  report += `📈 RISK PROGRESSION\n`;
  report += `  Risk Change: ${comparison.riskProgression.delta > 0 ? '+' : ''}${comparison.riskProgression.delta} (${comparison.riskProgression.percentChange > 0 ? '+' : ''}${comparison.riskProgression.percentChange}%)\n`;
  report += `  Trend: ${comparison.riskProgression.trend}\n`;
  report += `  Severity: ${comparison.riskProgression.severity}\n\n`;

  report += `🔍 FINDING DIFFERENCES\n`;
  report += `  New Findings: ${comparison.findings.totalNew}\n`;
  if (comparison.findings.new.length > 0) {
    report += `    ${comparison.findings.new.slice(0, 3).map(f => `• ${f}`).join('\n    ')}\n`;
    if (comparison.findings.new.length > 3) {
      report += `    ... and ${comparison.findings.new.length - 3} more\n`;
    }
  }
  report += `  Removed Findings: ${comparison.findings.totalRemoved}\n`;
  report += `  Common Findings: ${comparison.findings.totalCommon}\n\n`;

  report += `🎯 DETECTED PATTERNS\n`;
  comparison.patterns.forEach(p => {
    report += `  • ${p.name}\n`;
    report += `    Confidence: ${p.confidence.toFixed(0)}%\n`;
  });
  report += '\n';

  report += `🔮 LIKELY NEXT EVENTS\n`;
  comparison.predictions.forEach(pred => {
    report += `  • ${pred.event}\n`;
    report += `    Confidence: ${pred.confidence.toFixed(0)}%\n`;
    report += `    Timeframe: ${pred.timeframe}\n`;
  });
  report += '\n';

  report += `💡 RECOMMENDATION\n`;
  report += `  ${comparison.summary.recommendedAction}\n\n`;

  report += `${'─'.repeat(70)}\n`;

  return report;
}

export const mcp_comparatorEngine = {
  name: 'comparatorEngine',
  description: 'Compare two cases and detect patterns',
  methods: {
    compareCases,
    generateComparisonReport
  }
};

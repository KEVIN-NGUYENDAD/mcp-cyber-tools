import { loadCase, saveCase } from '../cases/caseManager.js';

// Risk scoring matrix
const findingSeverityScores = {
  'critical': 40,
  'high': 30,
  'medium': 15,
  'low': 5,
  'info': 0
};

const findingTypeScores = {
  'persistence': 35,
  'malware': 50,
  'lateral-movement': 40,
  'credential-access': 45,
  'exfiltration': 35,
  'defense-evasion': 25,
  'privilege-escalation': 30,
  'reconnaissance': 10,
  'normal': 0
};

const findingSourceScores = {
  'defenderCheck': -5, // Defender findings reduce risk
  'firewallCheck': -3,
  'servicesCheck': 5,
  'registryCheck': 15,
  'persistenceCheck': 20,
  'powerShellHunt': 25,
  'incidentDetection': 45,
  'threatIndicator': 30
};

function categorizeIndicator(finding) {
  const title = finding.title.toLowerCase();
  const description = finding.description ? finding.description.toLowerCase() : '';
  const text = `${title} ${description}`;

  if (text.includes('malware') || text.includes('virus')) return 'malware';
  if (text.includes('persistence') || text.includes('registry')) return 'persistence';
  if (text.includes('lateral') || text.includes('movement')) return 'lateral-movement';
  if (text.includes('credential') || text.includes('dump')) return 'credential-access';
  if (text.includes('exfiltration') || text.includes('data')) return 'exfiltration';
  if (text.includes('encoded') || text.includes('obfuscated')) return 'defense-evasion';
  if (text.includes('privilege') || text.includes('elevated')) return 'privilege-escalation';
  if (text.includes('reconnaissance') || text.includes('scan')) return 'reconnaissance';
  if (text.includes('enabled') || text.includes('active') || text.includes('healthy')) return 'normal';

  return 'unknown';
}

export function calculateRiskScore(findings) {
  let totalScore = 0;
  const breakdown = [];

  findings.forEach(finding => {
    let score = 0;

    // Base score from severity
    score += findingSeverityScores[finding.severity] || 0;

    // Additional score from finding type
    const category = categorizeIndicator(finding);
    score += findingTypeScores[category] || 5;

    // Adjust based on source
    const sourceAdjustment = findingSourceScores[finding.source] || 0;
    score += sourceAdjustment;

    // Critical findings get multiplier
    if (finding.severity === 'critical') {
      score *= 1.5;
    }

    totalScore += score;

    breakdown.push({
      finding: finding.title,
      severity: finding.severity,
      category,
      contribution: Math.round(score)
    });
  });

  // Normalize to 0-100 scale
  const normalizedScore = Math.min(Math.round(totalScore / findings.length), 100);

  return {
    score: normalizedScore,
    level: normalizedScore <= 20 ? 'low' : normalizedScore <= 50 ? 'medium' : 'high',
    breakdown
  };
}

export function getRiskLevel(score) {
  if (score <= 20) return 'low';
  if (score <= 50) return 'medium';
  return 'high';
}

export async function calculateAndUpdateRisk(caseId) {
  const caseData = await loadCase(caseId);

  if (caseData.findings.length === 0) {
    caseData.riskScore = 0;
    caseData.risk = 'low';
    caseData.riskCalculation = null;
    await saveCase(caseId, caseData);
    return { score: 0, level: 'low' };
  }

  const riskAnalysis = calculateRiskScore(caseData.findings);

  caseData.riskScore = riskAnalysis.score;
  caseData.risk = riskAnalysis.level;
  caseData.riskCalculation = {
    calculatedAt: new Date().toISOString(),
    breakdown: riskAnalysis.breakdown,
    totalFindings: caseData.findings.length
  };

  await saveCase(caseId, caseData);

  return riskAnalysis;
}

export const mcp_riskEngine = {
  name: 'riskEngine',
  description: 'Calculate intelligent risk scoring based on findings',
  methods: {
    calculateRiskScore,
    calculateAndUpdateRisk
  }
};

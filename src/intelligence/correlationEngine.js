import { loadCase, addFinding, saveCase } from '../cases/caseManager.js';

// Define correlation patterns
const correlationPatterns = [
  {
    name: 'Persistence Chain',
    findings: ['persistence', 'registry', 'startup', 'task'],
    threshold: 3,
    severity: 'high',
    description: 'Multiple persistence mechanisms detected in combination'
  },
  {
    name: 'Potential Malware',
    findings: ['malware', 'defender', 'encoded', 'suspicious'],
    threshold: 2,
    severity: 'critical',
    description: 'Multiple indicators of malware activity'
  },
  {
    name: 'Lateral Movement',
    findings: ['lateral', 'movement', 'credential', 'network'],
    threshold: 2,
    severity: 'high',
    description: 'Evidence of lateral movement attempt detected'
  },
  {
    name: 'Defense Evasion',
    findings: ['encoded', 'obfuscated', 'defender', 'firewall'],
    threshold: 2,
    severity: 'high',
    description: 'Indicators of defense evasion techniques'
  },
  {
    name: 'Credential Access',
    findings: ['credential', 'dump', 'lsass', 'password'],
    threshold: 2,
    severity: 'critical',
    description: 'Potential credential harvesting activity'
  }
];

function normalizeText(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function findCorrelations(findings) {
  const correlations = [];

  for (const pattern of correlationPatterns) {
    let matches = 0;
    const matchedFindings = [];

    for (const finding of findings) {
      const titleNorm = normalizeText(finding.title);
      const descNorm = normalizeText(finding.description || '');
      const fullText = `${titleNorm} ${descNorm}`;

      for (const keyword of pattern.findings) {
        if (fullText.includes(normalizeText(keyword))) {
          matches++;
          matchedFindings.push(finding.title);
          break;
        }
      }
    }

    if (matches >= pattern.threshold) {
      correlations.push({
        pattern: pattern.name,
        severity: pattern.severity,
        description: pattern.description,
        evidence: matchedFindings,
        confidence: Math.min(95 + (matches - pattern.threshold) * 5, 99),
        matchCount: matches
      });
    }
  }

  return correlations;
}

export async function analyzeCorrelations(caseId) {
  const caseData = await loadCase(caseId);

  if (caseData.findings.length < 2) {
    return { correlations: [], summary: 'Insufficient findings for correlation analysis' };
  }

  const correlations = findCorrelations(caseData.findings);

  // Store correlations in case
  caseData.correlationAnalysis = {
    performedAt: new Date().toISOString(),
    correlations,
    totalPatterns: correlationPatterns.length,
    detectedPatterns: correlations.length
  };

  await saveCase(caseId, caseData);

  return {
    correlations,
    summary: correlations.length > 0
      ? `${correlations.length} correlation pattern(s) detected`
      : 'No correlation patterns detected'
  };
}

export async function addCorrelatedFinding(caseId, correlation) {
  const caseData = await loadCase(caseId);

  // Create a meta-finding from correlation
  const correlatedFinding = {
    severity: correlation.severity,
    title: `Correlated: ${correlation.pattern}`,
    description: correlation.description,
    source: 'correlationEngine',
    evidence: correlation.evidence,
    confidence: correlation.confidence,
    type: 'correlated'
  };

  await addFinding(caseId, correlatedFinding);

  return correlatedFinding;
}

export async function generateCorrelationReport(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.correlationAnalysis || caseData.correlationAnalysis.correlations.length === 0) {
    return 'No correlations to report';
  }

  let report = '## Correlation Analysis\n\n';

  caseData.correlationAnalysis.correlations.forEach((corr, idx) => {
    report += `### ${idx + 1}. ${corr.pattern}\n`;
    report += `**Severity**: ${corr.severity}\n`;
    report += `**Confidence**: ${corr.confidence}%\n`;
    report += `**Description**: ${corr.description}\n`;
    report += `**Evidence**: ${corr.evidence.join(', ')}\n\n`;
  });

  return report;
}

export const mcp_correlationEngine = {
  name: 'correlationEngine',
  description: 'Correlate findings to detect higher-level threat patterns',
  methods: {
    analyzeCorrelations,
    addCorrelatedFinding,
    generateCorrelationReport
  }
};

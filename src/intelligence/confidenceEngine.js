import { loadCase, saveCase } from '../cases/caseManager.js';

// Evidence patterns for confidence calculation
const artifactPatterns = {
  // Known legitimate artifacts
  'SoftLanding': { type: 'legitimate', confidence: 95, reason: 'Known OEM artifact' },
  'Windows Defender': { type: 'legitimate', confidence: 98, reason: 'Microsoft security component' },
  'McAfee': { type: 'legitimate', confidence: 92, reason: 'Known antivirus software' },
  'Norton': { type: 'legitimate', confidence: 92, reason: 'Known antivirus software' },
  'LG gram Link': { type: 'legitimate', confidence: 88, reason: 'OEM utility' },
  'OneDrive': { type: 'legitimate', confidence: 95, reason: 'Microsoft service' },

  // Known suspicious patterns
  'iex': { type: 'malicious', confidence: 90, reason: 'PowerShell code execution' },
  'DownloadString': { type: 'malicious', confidence: 85, reason: 'Remote script download' },
  'Base64': { type: 'suspicious', confidence: 70, reason: 'Encoding detected' },
  'Encoded': { type: 'suspicious', confidence: 75, reason: 'Obfuscation detected' }
};

function classifyArtifact(finding) {
  let maxConfidence = 0;
  let classification = 'unknown';
  let reason = 'No pattern match';

  const titleLower = finding.title.toLowerCase();
  const descLower = (finding.description || '').toLowerCase();
  const fullText = `${titleLower} ${descLower}`;

  for (const [pattern, info] of Object.entries(artifactPatterns)) {
    if (fullText.includes(pattern.toLowerCase())) {
      if (info.confidence > maxConfidence) {
        maxConfidence = info.confidence;
        classification = info.type;
        reason = info.reason;
      }
    }
  }

  // Adjust confidence based on severity
  if (finding.severity === 'critical') {
    maxConfidence = Math.min(maxConfidence + 15, 99);
  } else if (finding.severity === 'high') {
    maxConfidence = Math.min(maxConfidence + 10, 98);
  }

  return {
    classification,
    confidence: maxConfidence,
    reason
  };
}

export async function addConfidenceMetrics(caseId) {
  const caseData = await loadCase(caseId);

  const enrichedFindings = caseData.findings.map(finding => {
    const confidence = classifyArtifact(finding);
    return {
      ...finding,
      classification: confidence.classification,
      confidence: confidence.confidence,
      confidenceReason: confidence.reason
    };
  });

  caseData.findings = enrichedFindings;
  caseData.confidenceAnalysis = {
    performedAt: new Date().toISOString(),
    averageConfidence: Math.round(
      enrichedFindings.reduce((sum, f) => sum + (f.confidence || 0), 0) / enrichedFindings.length
    ),
    classifications: {
      legitimate: enrichedFindings.filter(f => f.classification === 'legitimate').length,
      malicious: enrichedFindings.filter(f => f.classification === 'malicious').length,
      suspicious: enrichedFindings.filter(f => f.classification === 'suspicious').length,
      unknown: enrichedFindings.filter(f => f.classification === 'unknown').length
    }
  };

  await saveCase(caseId, caseData);

  return caseData.confidenceAnalysis;
}

export function generateConfidenceReport(caseData) {
  if (!caseData.findings.some(f => f.confidence)) {
    return 'No confidence analysis available';
  }

  let report = '## Confidence Analysis\n\n';
  report += `**Average Confidence**: ${caseData.confidenceAnalysis.averageConfidence}%\n\n`;

  report += '### Classifications\n';
  report += `- Legitimate: ${caseData.confidenceAnalysis.classifications.legitimate}\n`;
  report += `- Suspicious: ${caseData.confidenceAnalysis.classifications.suspicious}\n`;
  report += `- Malicious: ${caseData.confidenceAnalysis.classifications.malicious}\n`;
  report += `- Unknown: ${caseData.confidenceAnalysis.classifications.unknown}\n\n`;

  report += '### Finding Details\n';
  caseData.findings.forEach(f => {
    if (f.confidence) {
      report += `- **${f.title}** (${f.confidence}% - ${f.classification})\n`;
      report += `  ${f.confidenceReason}\n`;
    }
  });

  return report;
}

export const mcp_confidenceEngine = {
  name: 'confidenceEngine',
  description: 'Quantify confidence levels for each finding based on evidence patterns',
  methods: {
    addConfidenceMetrics,
    generateConfidenceReport
  }
};

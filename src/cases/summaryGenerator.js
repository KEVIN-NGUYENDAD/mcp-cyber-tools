import { loadCase } from './caseManager.js';
import { calculateRiskScore } from '../risk/riskEngine.js';
import { rankRecommendations } from '../recommendations/rankingEngine.js';

function generateInterpretation(riskScore, findings) {
  if (riskScore <= 20) {
    return 'System appears healthy with no critical security concerns detected.';
  } else if (riskScore <= 50) {
    return 'System shows some security concerns that should be addressed. Recommend further investigation.';
  } else {
    return 'System has significant security concerns requiring immediate attention.';
  }
}

function generateKeyTakeaway(findings) {
  if (findings.length === 0) {
    return 'No significant findings.';
  }

  const criticalFindings = findings.filter(f => f.severity === 'critical');
  const highFindings = findings.filter(f => f.severity === 'high');

  if (criticalFindings.length > 0) {
    return `CRITICAL: ${criticalFindings[0].title}`;
  } else if (highFindings.length > 0) {
    return `WARNING: ${highFindings[0].title}`;
  } else {
    return findings[0].title;
  }
}

function generateActionSummary(recommendations, ranked = false) {
  if (!Array.isArray(recommendations) || recommendations.length === 0) {
    return 'No actions recommended.';
  }

  if (!ranked) {
    // Fallback if not pre-ranked
    const critical = recommendations.filter(r => r.requiresApproval !== false);
    if (critical.length > 0) {
      return `Recommended: ${critical[0].title}`;
    }
  } else {
    // Use pre-ranked data
    const recommended = recommendations.filter(r => r.recommended);
    if (recommended.length > 0) {
      return `Recommended: ${recommended[0].title} (${recommended[0].confidence}% confidence)`;
    }
  }

  return `Start with: ${recommendations[0].title}`;
}

export async function generateExecutiveSummary(caseId) {
  const caseData = await loadCase(caseId);

  // Calculate risk if not already calculated
  const riskInfo = caseData.riskScore
    ? { score: caseData.riskScore, level: caseData.risk }
    : calculateRiskScore(caseData.findings);

  // Rank recommendations if not already ranked
  const ranked = caseData.recommendations.some(r => r.confidence)
    ? caseData.recommendations
    : rankRecommendations(caseData.recommendations, riskInfo.score);

  const summary = {
    caseId: caseData.caseId,
    title: caseData.title,
    riskScore: riskInfo.score,
    riskLevel: riskInfo.level,
    status: caseData.status,
    findingCount: caseData.findings.length,
    recommendationCount: caseData.recommendations.length,
    approvedCount: caseData.recommendations.filter(r => r.approved).length,
    interpretation: generateInterpretation(riskInfo.score, caseData.findings),
    keyTakeaway: generateKeyTakeaway(caseData.findings),
    recommendedAction: generateActionSummary(ranked, true),
    findings: caseData.findings.slice(0, 3).map(f => ({
      title: f.title,
      severity: f.severity
    })),
    topRecommendations: ranked
      .filter(r => r.recommended)
      .slice(0, 3)
      .map(r => ({
        id: r.id,
        title: r.title,
        confidence: r.confidence
      }))
  };

  return summary;
}

export async function generateMarkdownSummary(caseId) {
  const caseData = await loadCase(caseId);

  // Calculate risk if not already calculated
  const riskInfo = caseData.riskScore
    ? { score: caseData.riskScore, level: caseData.risk }
    : calculateRiskScore(caseData.findings);

  const ranked = caseData.recommendations.some(r => r.confidence)
    ? caseData.recommendations
    : rankRecommendations(caseData.recommendations, riskInfo.score);

  let markdown = `# ${caseData.caseId}\n\n`;
  markdown += `**${caseData.title}**\n\n`;

  // Risk and Status
  markdown += `## Status\n\n`;
  markdown += `- **Risk Score**: ${riskInfo.score}/100 (${riskInfo.level.toUpperCase()})\n`;
  markdown += `- **Status**: ${caseData.status}\n`;
  markdown += `- **Findings**: ${caseData.findings.length}\n`;
  markdown += `- **Approved Actions**: ${caseData.recommendations.filter(r => r.approved).length}/${caseData.recommendations.length}\n\n`;

  // Interpretation
  markdown += `## Interpretation\n\n`;
  markdown += `${generateInterpretation(riskInfo.score, caseData.findings)}\n\n`;

  // Key Takeaway
  markdown += `## Key Takeaway\n\n`;
  markdown += `**${generateKeyTakeaway(caseData.findings)}**\n\n`;

  // Findings
  if (caseData.findings.length > 0) {
    markdown += `## Findings (${caseData.findings.length})\n\n`;
    caseData.findings.forEach(f => {
      markdown += `- **${f.title}** _(${f.severity})_\n`;
      markdown += `  ${f.description}\n\n`;
    });
  }

  // Recommended Actions
  const recommendedActions = ranked.filter(r => r.recommended);
  if (recommendedActions.length > 0) {
    markdown += `## Recommended Actions\n\n`;
    recommendedActions.forEach((r, idx) => {
      markdown += `${idx + 1}. **${r.title}**\n`;
      markdown += `   - Confidence: ${r.confidence}%\n`;
      markdown += `   - Priority: ${r.priority === 0 ? 'URGENT' : r.priority === 1 ? 'HIGH' : 'NORMAL'}\n\n`;
    });
  }

  return markdown;
}

export const mcp_summaryGenerator = {
  name: 'summaryGenerator',
  description: 'Generate executive summaries and human-readable case output',
  methods: {
    generateExecutiveSummary,
    generateMarkdownSummary
  }
};

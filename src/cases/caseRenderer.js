import fs from 'fs/promises';
import path from 'path';

export async function generateCaseReport(caseId) {
  const casePath = path.join('cases', `${caseId}.json`);
  const caseData = JSON.parse(await fs.readFile(casePath, 'utf-8'));

  const report = `# ${caseData.caseId}

**Title**: ${caseData.title}
**Status**: ${caseData.status.toUpperCase()}
**Risk Level**: ${caseData.risk.toUpperCase()}
**Created**: ${caseData.createdAt}

## Findings

${caseData.findings.length > 0
  ? caseData.findings.map(f => `- **${f.title}** (${f.severity})`).join('\n')
  : 'No findings recorded'}

## Recommendations

${caseData.recommendations.length > 0
  ? caseData.recommendations.map((r, i) => `[${i + 1}] ${r.title}`).join('\n')
  : 'No recommendations'}

## Audit Trail

${caseData.auditTrail.map(entry =>
  `- ${new Date(entry.timestamp).toLocaleString()} | ${entry.action}`
).join('\n')}
`;

  const reportPath = path.join('cases', `${caseId}.md`);
  await fs.writeFile(reportPath, report);

  return reportPath;
}

export async function renderCaseForClaude(caseData) {
  return {
    caseId: caseData.caseId,
    title: caseData.title,
    status: caseData.status,
    risk: caseData.risk,
    findings: caseData.findings.map(f => `- ${f.title}`),
    recommendations: caseData.recommendations.map((r, i) => `[${i + 1}] ${r.title}`)
  };
}

export function formatCaseForConsole(caseData) {
  return `
Case Created: ${caseData.caseId}

Title: ${caseData.title}
Status: ${caseData.status}
Risk: ${caseData.risk}

Findings:
${caseData.findings.map(f => `- ${f.title}`).join('\n')}

Recommendations:
${caseData.recommendations.map((r, i) => `[${i + 1}] ${r.title}`).join('\n')}
`;
}

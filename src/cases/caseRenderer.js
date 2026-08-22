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
**Updated**: ${caseData.updatedAt}
**Version**: ${caseData.version}

## Findings

${caseData.findings.length > 0
  ? caseData.findings.map(f => `- **${f.title}** (${f.severity})`).join('\n')
  : 'No findings recorded'}

## Recommendations

${caseData.recommendations.length > 0
  ? caseData.recommendations.map(r => `[${r.id}] ${r.title} (risk: ${r.risk}${r.requiresApproval ? ', requires approval' : ''})`).join('\n')
  : 'No recommendations'}

## Event Timeline

${caseData.events.map(event => {
  const ts = new Date(event.timestamp).toLocaleString();
  if (event.type === 'CASE_CREATED') {
    return `- ${ts} | Case created`;
  } else if (event.type === 'FINDING_ADDED') {
    return `- ${ts} | Finding added: ${event.payload.title} (${event.payload.severity})`;
  } else if (event.type === 'RECOMMENDATION_GENERATED') {
    return `- ${ts} | Recommendations generated (${event.payload.count} total)`;
  } else if (event.type === 'STATUS_CHANGED') {
    return `- ${ts} | Status changed: ${event.payload.from} → ${event.payload.to}`;
  }
  return `- ${ts} | ${event.type}`;
}).join('\n')}
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
    findings: caseData.findings.map(f => `- ${f.title} (${f.severity})`),
    recommendations: caseData.recommendations.map(r => `[${r.id}] ${r.title}${r.requiresApproval ? ' (requires approval)' : ''}`)
  };
}

export function formatCaseForConsole(caseData) {
  return `
Case Created: ${caseData.caseId}

Title: ${caseData.title}
Status: ${caseData.status}
Risk: ${caseData.risk}
Version: ${caseData.version}

Findings:
${caseData.findings.map(f => `- ${f.title} (${f.severity})`).join('\n')}

Recommendations:
${caseData.recommendations.map(r => `[${r.id}] ${r.title} (requires approval: ${r.requiresApproval})`).join('\n')}
`;
}

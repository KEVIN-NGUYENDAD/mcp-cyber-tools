import fs from 'fs/promises';
import path from 'path';

const CASES_DIR = 'cases';

export async function createCase(title) {
  await fs.mkdir(CASES_DIR, { recursive: true });

  const caseId = `CASE-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;

  const caseData = {
    caseId,
    title,
    status: 'open',
    createdAt: new Date().toISOString(),
    risk: 'low',
    findings: [],
    recommendations: [],
    auditTrail: [
      {
        timestamp: new Date().toISOString(),
        action: 'Case created',
        actor: 'system'
      }
    ]
  };

  const filePath = path.join(CASES_DIR, `${caseId}.json`);
  await fs.writeFile(filePath, JSON.stringify(caseData, null, 2));

  return caseData;
}

export async function loadCase(caseId) {
  const filePath = path.join(CASES_DIR, `${caseId}.json`);
  const data = await fs.readFile(filePath, 'utf-8');
  return JSON.parse(data);
}

export async function saveCase(caseId, caseData) {
  const filePath = path.join(CASES_DIR, `${caseId}.json`);
  await fs.writeFile(filePath, JSON.stringify(caseData, null, 2));
  return caseData;
}

export async function addFinding(caseId, finding) {
  const caseData = await loadCase(caseId);

  const findingRecord = {
    id: `F-${Date.now()}`,
    timestamp: new Date().toISOString(),
    ...finding
  };

  caseData.findings.push(findingRecord);

  caseData.auditTrail.push({
    timestamp: new Date().toISOString(),
    action: 'Finding added',
    actor: 'system',
    details: finding.title
  });

  return await saveCase(caseId, caseData);
}

export async function addRecommendations(caseId, recommendations) {
  const caseData = await loadCase(caseId);

  const recs = recommendations.map((title, index) => ({
    id: `R-${index + 1}`,
    title
  }));

  caseData.recommendations = recs;

  caseData.auditTrail.push({
    timestamp: new Date().toISOString(),
    action: 'Recommendations generated',
    actor: 'system',
    details: `${recs.length} recommendations created`
  });

  return await saveCase(caseId, caseData);
}

export async function closeCase(caseId) {
  const caseData = await loadCase(caseId);
  caseData.status = 'closed';
  caseData.closedAt = new Date().toISOString();

  caseData.auditTrail.push({
    timestamp: new Date().toISOString(),
    action: 'Case closed',
    actor: 'system'
  });

  return await saveCase(caseId, caseData);
}

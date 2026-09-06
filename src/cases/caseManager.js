import fs from 'fs/promises';
import path from 'path';
import { learnFromCase } from '../intelligence/knowledgeLayer.js';

const CASES_DIR = 'cases';

export async function createCase(title) {
  await fs.mkdir(CASES_DIR, { recursive: true });

  const caseId = `CASE-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;
  const now = new Date().toISOString();

  const caseData = {
    version: '1.1.1-alpha',
    caseId,
    title,
    status: 'open',
    statusHistory: [
      {
        status: 'open',
        timestamp: now
      }
    ],
    createdAt: now,
    updatedAt: now,
    risk: 'low',
    findings: [],
    recommendations: [],
    events: [
      {
        type: 'CASE_CREATED',
        timestamp: now
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
  const now = new Date().toISOString();

  const findingRecord = {
    id: `F-${Date.now()}`,
    timestamp: now,
    ...finding
  };

  caseData.findings.push(findingRecord);
  caseData.updatedAt = now;

  caseData.events.push({
    type: 'FINDING_ADDED',
    payload: {
      findingId: findingRecord.id,
      title: finding.title,
      severity: finding.severity
    },
    timestamp: now
  });

  return await saveCase(caseId, caseData);
}

export async function addRecommendations(caseId, recommendations) {
  const caseData = await loadCase(caseId);
  const now = new Date().toISOString();

  const recs = recommendations.map((rec, index) => {
    if (typeof rec === 'string') {
      return {
        id: `REC-${String(index + 1).padStart(3, '0')}`,
        title: rec,
        risk: 'safe',
        requiresApproval: true
      };
    }
    return {
      id: rec.id || `REC-${String(index + 1).padStart(3, '0')}`,
      title: rec.title,
      risk: rec.risk || 'safe',
      requiresApproval: rec.requiresApproval !== false
    };
  });

  caseData.recommendations = recs;
  caseData.updatedAt = now;

  caseData.events.push({
    type: 'RECOMMENDATION_GENERATED',
    payload: {
      count: recs.length,
      recommendations: recs.map(r => ({ id: r.id, title: r.title }))
    },
    timestamp: now
  });

  return await saveCase(caseId, caseData);
}

export async function approveRecommendation(caseId, recommendationId, approver = 'user') {
  const caseData = await loadCase(caseId);
  const now = new Date().toISOString();

  // Find the recommendation
  const rec = caseData.recommendations.find(r => r.id === recommendationId);
  if (!rec) {
    throw new Error(`Recommendation ${recommendationId} not found`);
  }

  // Mark as approved
  rec.approved = true;
  rec.approvedAt = now;
  rec.approvedBy = approver;

  // Record approval event
  caseData.events.push({
    type: 'RECOMMENDATION_APPROVED',
    payload: {
      recommendationId,
      title: rec.title,
      approver,
      risk: rec.risk
    },
    timestamp: now
  });

  caseData.updatedAt = now;
  return await saveCase(caseId, caseData);
}

export async function closeCase(caseId) {
  const caseData = await loadCase(caseId);
  const now = new Date().toISOString();
  const previousStatus = caseData.status;

  caseData.status = 'closed';
  caseData.closedAt = now;
  caseData.updatedAt = now;

  caseData.statusHistory.push({
    status: 'closed',
    timestamp: now
  });

  caseData.events.push({
    type: 'STATUS_CHANGED',
    payload: {
      from: previousStatus,
      to: 'closed'
    },
    timestamp: now
  });

  const saved = await saveCase(caseId, caseData);

  // Sprint 2: Learning Hook - When case closes, learn from it
  try {
    await learnFromCase(caseId);
  } catch (e) {
    console.error(`Failed to learn from case ${caseId}:`, e.message);
  }

  return saved;
}

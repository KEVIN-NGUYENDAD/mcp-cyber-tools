import { loadCase, saveCase } from '../cases/caseManager.js';
import fs from 'fs/promises';
import path from 'path';

// Map recommendation IDs to their execution functions
const actionHandlers = {
  'REC-001': createSystemBaseline,
  'REC-002': exportEvidencePackage,
  'REC-003': closeCase
};

async function createSystemBaseline(caseId) {
  const timestamp = new Date().toISOString();
  const filename = `BASELINE-${new Date().toISOString().split('T')[0]}.json`;
  const filepath = path.join('baseline', filename);

  await fs.mkdir('baseline', { recursive: true });

  const baseline = {
    caseId,
    createdAt: timestamp,
    type: 'SYSTEM_BASELINE',
    description: 'System state snapshot for comparison',
    processes: 'system',
    services: 'system',
    tasks: 'system',
    users: 'system'
  };

  await fs.writeFile(filepath, JSON.stringify(baseline, null, 2));

  return {
    success: true,
    action: 'REC-001',
    result: 'System baseline created',
    file: filepath,
    timestamp
  };
}

async function exportEvidencePackage(caseId) {
  const timestamp = new Date().toISOString();
  const filename = `EVIDENCE-${new Date().toISOString().split('T')[0]}.json`;
  const filepath = path.join('evidence', filename);

  await fs.mkdir('evidence', { recursive: true });

  const caseData = await loadCase(caseId);
  const evidence = {
    caseId,
    exportedAt: timestamp,
    findings: caseData.findings,
    recommendations: caseData.recommendations,
    events: caseData.events
  };

  await fs.writeFile(filepath, JSON.stringify(evidence, null, 2));

  return {
    success: true,
    action: 'REC-002',
    result: 'Evidence package exported',
    file: filepath,
    timestamp
  };
}

async function closeCase(caseId) {
  const caseData = await loadCase(caseId);
  const now = new Date().toISOString();

  caseData.status = 'closed';
  caseData.closedAt = now;
  caseData.updatedAt = now;

  caseData.statusHistory.push({
    status: 'closed',
    timestamp: now
  });

  await saveCase(caseId, caseData);

  return {
    success: true,
    action: 'REC-003',
    result: 'Case closed',
    timestamp: now
  };
}

export async function executeApprovedAction(caseId, recommendationId) {
  const caseData = await loadCase(caseId);
  const now = new Date().toISOString();

  // Find the recommendation
  const rec = caseData.recommendations.find(r => r.id === recommendationId);
  if (!rec) {
    throw new Error(`Recommendation ${recommendationId} not found`);
  }

  if (!rec.approved) {
    throw new Error(`Recommendation ${recommendationId} not approved yet`);
  }

  if (rec.executed) {
    throw new Error(`Recommendation ${recommendationId} already executed`);
  }

  // Execute the action
  const handler = actionHandlers[recommendationId];
  if (!handler) {
    throw new Error(`No handler for ${recommendationId}`);
  }

  let executionResult;
  try {
    executionResult = await handler(caseId);
  } catch (error) {
    executionResult = {
      success: false,
      action: recommendationId,
      error: error.message,
      timestamp: now
    };
  }

  // Record execution in case
  rec.executed = true;
  rec.executedAt = now;
  rec.executionResult = executionResult;

  caseData.events.push({
    type: 'ACTION_EXECUTED',
    payload: {
      recommendationId,
      title: rec.title,
      success: executionResult.success,
      result: executionResult.result
    },
    timestamp: now
  });

  caseData.updatedAt = now;
  await saveCase(caseId, caseData);

  return executionResult;
}

export async function executeAllApprovedActions(caseId) {
  const caseData = await loadCase(caseId);

  const approvedButNotExecuted = caseData.recommendations.filter(
    r => r.approved && !r.executed
  );

  const results = [];
  for (const rec of approvedButNotExecuted) {
    try {
      const result = await executeApprovedAction(caseId, rec.id);
      results.push(result);
    } catch (error) {
      results.push({
        success: false,
        action: rec.id,
        error: error.message
      });
    }
  }

  return {
    caseId,
    executedCount: results.filter(r => r.success).length,
    results
  };
}

export const mcp_executionEngine = {
  name: 'executionEngine',
  description: 'Execute approved case recommendations',
  methods: {
    executeApprovedAction,
    executeAllApprovedActions
  }
};

import { loadCase, approveRecommendation } from '../cases/caseManager.js';

export async function getApprovalsNeeded(caseId) {
  const caseData = await loadCase(caseId);

  return {
    caseId: caseData.caseId,
    title: caseData.title,
    status: caseData.status,
    recommendationsNeedingApproval: caseData.recommendations
      .filter(r => r.requiresApproval && !r.approved)
      .map(r => ({
        id: r.id,
        title: r.title,
        risk: r.risk,
        requiresApproval: r.requiresApproval
      })),
    totalNeeded: caseData.recommendations.filter(r => r.requiresApproval && !r.approved).length,
    totalApproved: caseData.recommendations.filter(r => r.approved).length
  };
}

export async function approveAction(caseId, recommendationId, approver = 'system') {
  const beforeApproval = await loadCase(caseId);

  // Record approval
  const afterApproval = await approveRecommendation(caseId, recommendationId, approver);

  return {
    caseId,
    recommendationId,
    approver,
    approved: true,
    message: `Recommendation ${recommendationId} approved by ${approver}`,
    nextSteps: afterApproval.recommendations
      .filter(r => r.requiresApproval && !r.approved)
      .map(r => `Approve ${r.id}: ${r.title}`)
  };
}

export async function getApprovedActions(caseId) {
  const caseData = await loadCase(caseId);

  return {
    caseId,
    approvedActions: caseData.recommendations
      .filter(r => r.approved)
      .map(r => ({
        id: r.id,
        title: r.title,
        approvedAt: r.approvedAt,
        approvedBy: r.approvedBy,
        risk: r.risk
      })),
    readyForExecution: caseData.recommendations
      .filter(r => r.approved && !r.executed)
      .map(r => r.id)
  };
}

export const mcp_approvalController = {
  name: 'approvalController',
  description: 'Handle case approval workflow',
  methods: {
    getApprovalsNeeded,
    approveAction,
    getApprovedActions
  }
};

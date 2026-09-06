import { loadCase, saveCase } from '../cases/caseManager.js';

const actionImpactMatrix = {
  'Create System Baseline': { priority: 2, confidence: 95, impact: 'medium' },
  'Export Evidence Package': { priority: 1, confidence: 90, impact: 'high' },
  'Export Persistence Report': { priority: 1, confidence: 85, impact: 'high' },
  'Export PowerShell Timeline': { priority: 2, confidence: 80, impact: 'medium' },
  'Create Persistence Baseline': { priority: 3, confidence: 75, impact: 'low' },
  'Create Hunt Baseline': { priority: 3, confidence: 75, impact: 'low' },
  'Isolate Affected System': { priority: 0, confidence: 100, impact: 'critical' },
  'Collect Forensic Evidence': { priority: 1, confidence: 95, impact: 'critical' },
  'Notify Security Team': { priority: 0, confidence: 100, impact: 'critical' },
  'Document Incident': { priority: 2, confidence: 85, impact: 'high' },
  'Schedule Weekly Assessment': { priority: 4, confidence: 70, impact: 'low' },
  'Close Case': { priority: 5, confidence: 100, impact: 'none' }
};

export function rankRecommendations(recommendations, riskScore = 50) {
  const ranked = recommendations.map(rec => {
    const metadata = actionImpactMatrix[rec.title] || {
      priority: 3,
      confidence: 60,
      impact: 'medium'
    };

    // Adjust priority based on risk score
    let adjustedPriority = metadata.priority;
    if (riskScore > 70) {
      adjustedPriority = Math.max(0, adjustedPriority - 1);
    }

    return {
      ...rec,
      priority: adjustedPriority,
      confidence: metadata.confidence,
      impact: metadata.impact,
      recommended: metadata.priority <= 2,
      urgency: riskScore > 70 ? 'high' : metadata.priority <= 1 ? 'medium' : 'low'
    };
  });

  // Sort by: recommended first, then by priority, then by confidence
  return ranked.sort((a, b) => {
    if (a.recommended !== b.recommended) {
      return a.recommended ? -1 : 1;
    }
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return b.confidence - a.confidence;
  });
}

export async function rankAndUpdateRecommendations(caseId) {
  const caseData = await loadCase(caseId);

  const riskScore = caseData.riskScore || 50;
  const ranked = rankRecommendations(caseData.recommendations, riskScore);

  // Update recommendation objects with ranking metadata
  caseData.recommendations = ranked;
  caseData.recommendationRanking = {
    rankedAt: new Date().toISOString(),
    riskScoreUsed: riskScore,
    recommendedCount: ranked.filter(r => r.recommended).length,
    totalCount: ranked.length
  };

  await saveCase(caseId, caseData);

  return ranked;
}

export const mcp_rankingEngine = {
  name: 'rankingEngine',
  description: 'Rank recommendations by priority and confidence',
  methods: {
    rankRecommendations,
    rankAndUpdateRecommendations
  }
};

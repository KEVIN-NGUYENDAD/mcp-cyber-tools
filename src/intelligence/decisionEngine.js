import { loadCase, saveCase } from '../cases/caseManager.js';

// Decision types
const DECISIONS = {
  IGNORE: 'IGNORE',
  INVESTIGATE: 'INVESTIGATE',
  ESCALATE: 'ESCALATE'
};

// Decision rules - simple, deterministic, testable
function evaluateArtifact(finding, knowledge) {
  const decisions = [];
  let baseConfidence = finding.confidence || 0;
  let knowledgeConfidence = knowledge?.confidence || 0;

  // Rule 1: Known good artifacts (high confidence, no incidents)
  if (knowledge && knowledge.classification === 'legitimate') {
    if (knowledgeConfidence >= 90 && knowledge.incidentCount === 0) {
      decisions.push({
        decision: DECISIONS.IGNORE,
        confidence: Math.min(knowledgeConfidence - 2, 99),
        reasoning: [
          `Known good artifact: seen ${knowledge.seenCount} times`,
          `Zero incidents observed`,
          `High confidence classification (${knowledgeConfidence}%)`
        ],
        weight: 95
      });
    } else if (knowledgeConfidence >= 70 && knowledge.incidentCount < knowledge.seenCount * 0.2) {
      decisions.push({
        decision: DECISIONS.IGNORE,
        confidence: 80,
        reasoning: [
          `Likely legitimate: ${knowledge.seenCount} observations`,
          `Low incident rate (${(knowledge.incidentCount / knowledge.seenCount * 100).toFixed(1)}%)`,
          `Known classification: ${knowledge.classification}`
        ],
        weight: 75
      });
    }
  }

  // Rule 1b: Known good with medium-low confidence but few incidents
  if (knowledge && knowledge.classification === 'legitimate' && !decisions.some(d => d.decision === DECISIONS.IGNORE)) {
    if (knowledgeConfidence >= 65 && knowledge.incidentCount <= knowledge.seenCount * 0.3) {
      decisions.push({
        decision: DECISIONS.IGNORE,
        confidence: 78,
        reasoning: [
          `Likely legitimate: ${knowledge.seenCount} observations`,
          `Moderate confidence (${knowledgeConfidence}%)`,
          `Low incident rate (${(knowledge.incidentCount / knowledge.seenCount * 100).toFixed(1)}%)`
        ],
        weight: 78
      });
    }
  }

  // Rule 2: Known malicious artifacts
  if (knowledge && knowledge.classification === 'malicious') {
    if (knowledgeConfidence >= 80) {
      decisions.push({
        decision: DECISIONS.ESCALATE,
        confidence: Math.min(knowledgeConfidence + 5, 99),
        reasoning: [
          `Known malicious artifact`,
          `High confidence classification (${knowledgeConfidence}%)`,
          `Observed in ${knowledge.seenCount} incidents`
        ],
        weight: 99
      });
    } else if (knowledgeConfidence >= 60) {
      decisions.push({
        decision: DECISIONS.ESCALATE,
        confidence: 85,
        reasoning: [
          `Suspected malicious artifact`,
          `Moderate confidence (${knowledgeConfidence}%)`,
          `Associated with ${knowledge.incidentCount} incidents`
        ],
        weight: 85
      });
    }
  }

  // Rule 3: Unknown registry entries in startup locations
  if (finding.source === 'registryRunKeys' || finding.title?.toLowerCase().includes('registry')) {
    const isStartupLocation = finding.source === 'registryRunKeys';
    const isLowToMediumSeverity = finding.severity === 'low' || finding.severity === 'medium';

    // Check if truly unknown (no knowledge AND not marked as legitimate)
    const isUnknown = !knowledge && finding.classification !== 'legitimate';
    const isClassifiedUnknown = knowledge && knowledge.classification === 'unknown';

    if (isStartupLocation && isLowToMediumSeverity && (isUnknown || isClassifiedUnknown)) {
      decisions.push({
        decision: DECISIONS.INVESTIGATE,
        confidence: 75,
        reasoning: [
          `Unknown startup registry entry: ${finding.title}`,
          `Persistence indicator (not seen before or unknown classification)`,
          `Requires investigation despite low severity classification`
        ],
        weight: 80
      });
    }
  }

  // Rule 3b: High severity findings (regardless of knowledge)
  if (finding.severity === 'critical' || finding.severity === 'high') {
    if (!decisions.some(d => d.decision === DECISIONS.ESCALATE)) {
      decisions.push({
        decision: DECISIONS.ESCALATE,
        confidence: 90,
        reasoning: [
          `High severity finding: ${finding.severity}`,
          `Requires immediate review regardless of history`
        ],
        weight: 90
      });
    }
  }

  // Rule 4: New or unknown artifacts
  if (!knowledge) {
    if (finding.severity === 'critical' || finding.severity === 'high') {
      decisions.push({
        decision: DECISIONS.ESCALATE,
        confidence: 75,
        reasoning: [
          `New artifact with high severity: ${finding.severity}`,
          `No prior observations`,
          `Requires investigation`
        ],
        weight: 80
      });
    } else if (finding.severity === 'medium') {
      decisions.push({
        decision: DECISIONS.INVESTIGATE,
        confidence: 70,
        reasoning: [
          `New artifact with moderate severity`,
          `No historical data available`,
          `Requires deeper analysis`
        ],
        weight: 70
      });
    } else {
      decisions.push({
        decision: DECISIONS.INVESTIGATE,
        confidence: 60,
        reasoning: [
          `Unknown artifact`,
          `First observation`,
          `Recommend standard analysis`
        ],
        weight: 60
      });
    }
  }

  // Rule 5: Suspicious classification with no knowledge
  if (!knowledge && (finding.classification === 'suspicious' || finding.classification === 'malicious')) {
    decisions.push({
      decision: DECISIONS.ESCALATE,
      confidence: 85,
      reasoning: [
        `New suspicious/malicious artifact detected`,
        `Classification: ${finding.classification}`,
        `Requires immediate investigation`
      ],
      weight: 85
    });
  }

  // Choose highest weight decision
  if (decisions.length === 0) {
    decisions.push({
      decision: DECISIONS.INVESTIGATE,
      confidence: 65,
      reasoning: ['No specific rules matched', 'Standard investigation recommended'],
      weight: 65
    });
  }

  return decisions.sort((a, b) => b.weight - a.weight)[0];
}

export async function makeDecision(finding, knowledge = null, caseRisk = 0) {
  if (!finding) {
    throw new Error('Finding required for decision');
  }

  const decision = evaluateArtifact(finding, knowledge);

  // Adjust confidence based on case risk
  let adjustedConfidence = decision.confidence;
  if (caseRisk > 70) {
    // High risk cases: lower confidence in IGNORE decisions
    if (decision.decision === DECISIONS.IGNORE) {
      adjustedConfidence = Math.max(decision.confidence - 15, 50);
      decision.reasoning.push(`Case risk level: ${caseRisk}/100 (reduces ignore confidence)`);
    } else if (decision.decision === DECISIONS.INVESTIGATE) {
      adjustedConfidence = Math.min(decision.confidence + 10, 90);
      decision.reasoning.push(`Case risk level: ${caseRisk}/100 (increases investigation priority)`);
    }
  }

  return {
    finding: finding.title,
    decision: decision.decision,
    confidence: adjustedConfidence,
    reasoning: decision.reasoning,
    action: getRecommendedAction(decision.decision, finding, knowledge),
    estimatedTime: getTimeEstimate(decision.decision)
  };
}

function getRecommendedAction(decision, finding, knowledge) {
  const actions = {
    [DECISIONS.IGNORE]: 'No action required - Known benign artifact',
    [DECISIONS.INVESTIGATE]: `Investigate: ${finding.title} - Requires deeper analysis`,
    [DECISIONS.ESCALATE]: `ESCALATE: ${finding.title} - Requires immediate attention`
  };
  return actions[decision] || 'Standard action required';
}

function getTimeEstimate(decision) {
  const estimates = {
    [DECISIONS.IGNORE]: 0,
    [DECISIONS.INVESTIGATE]: 15,
    [DECISIONS.ESCALATE]: 30
  };
  return estimates[decision] || 0;
}

export async function decideFindingsForCase(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.findings || caseData.findings.length === 0) {
    return { decided: 0, ignored: 0, investigated: 0, escalated: 0 };
  }

  const decisions = [];
  let ignored = 0;
  let investigated = 0;
  let escalated = 0;

  for (const finding of caseData.findings) {
    const knowledge = finding.knowledgeContext ? {
      confidence: finding.knowledgeContext.confidence,
      classification: finding.knowledgeContext.classification,
      seenCount: finding.knowledgeContext.seenCount,
      incidentCount: finding.knowledgeContext.incidentCount
    } : null;

    try {
      const decision = await makeDecision(finding, knowledge, caseData.riskScore || 0);
      decisions.push(decision);

      if (decision.decision === DECISIONS.IGNORE) ignored++;
      else if (decision.decision === DECISIONS.INVESTIGATE) investigated++;
      else if (decision.decision === DECISIONS.ESCALATE) escalated++;
    } catch (e) {
      console.error(`Failed to decide on ${finding.title}:`, e.message);
    }
  }

  // Add decision metadata to case
  caseData.decisionAnalysis = {
    performedAt: new Date().toISOString(),
    decisions,
    summary: {
      ignored,
      investigated,
      escalated,
      total: decisions.length
    },
    timeline: [
      ...decisions
        .filter(d => d.decision === DECISIONS.ESCALATE)
        .map(d => ({ finding: d.finding, decision: 'ESCALATE', timestamp: new Date().toISOString() })),
      ...decisions
        .filter(d => d.decision === DECISIONS.INVESTIGATE)
        .map(d => ({ finding: d.finding, decision: 'INVESTIGATE', timestamp: new Date().toISOString() }))
    ],
    analystTimeEstimate: decisions.reduce((sum, d) => sum + (d.estimatedTime || 0), 0)
  };

  caseData.events.push({
    type: 'DECISIONS_MADE',
    payload: {
      ignored,
      investigated,
      escalated,
      totalDecisions: decisions.length
    },
    timestamp: new Date().toISOString()
  });

  await saveCase(caseId, caseData);

  return {
    decided: decisions.length,
    ignored,
    investigated,
    escalated,
    decisions,
    timeSaved: decisions.filter(d => d.decision === DECISIONS.IGNORE).length * 10 // 10 min per ignored finding
  };
}

export const mcp_decisionEngine = {
  name: 'decisionEngine',
  description: 'Make recommendations on findings based on knowledge and risk',
  methods: {
    makeDecision,
    decideFindingsForCase
  }
};

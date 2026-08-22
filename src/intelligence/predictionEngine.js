import { loadCase } from '../cases/caseManager.js';
import { findPatternMatch, getAllPatterns } from './patternEngine.js';
import { recordPrediction } from './validationEngine.js';

export async function predictNextSteps(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.findings || caseData.findings.length === 0) {
    return {
      hasPrediction: false,
      message: 'No findings available for prediction'
    };
  }

  // Build current threat sequence from detected patterns
  const currentSequence = buildCurrentSequence(caseData);

  if (currentSequence.length === 0) {
    return {
      hasPrediction: false,
      message: 'Unable to establish threat sequence from current findings'
    };
  }

  // Find matching patterns
  const patternMatches = await findPatternMatch(currentSequence);

  if (patternMatches.length === 0) {
    return {
      hasPrediction: false,
      currentSequence,
      message: 'No historical patterns match current threat sequence'
    };
  }

  // Generate predictions from pattern matches
  const predictions = generatePredictions(patternMatches, caseData);
  const nextPrediction = predictions[0];

  // Record prediction for validation tracking
  await recordPrediction(
    caseId,
    nextPrediction.nextStep,
    nextPrediction.confidence
  );

  return {
    hasPrediction: true,
    currentSequence,
    predictions,
    nextLikelyStep: nextPrediction,
    allPossibilities: predictions,
    timeframe: estimateTimeframe(nextPrediction),
    confidence: nextPrediction.confidence,
    recommendation: generateRecommendation(nextPrediction, caseData)
  };
}

function buildCurrentSequence(caseData) {
  // Extract threat sequence from case findings and decisions
  const sequence = [];

  // Look for key threat indicators in findings
  const findingTypes = new Set();

  for (const finding of caseData.findings || []) {
    const title = (finding.title || '').toLowerCase();
    const description = (finding.description || '').toLowerCase();

    // Persistence indicators
    if (title.includes('registry') || title.includes('run key') || title.includes('service') || title.includes('task')) {
      findingTypes.add('Persistence');
    }

    // Privilege escalation
    if (title.includes('privilege') || title.includes('elevation') || title.includes('admin') || title.includes('system')) {
      findingTypes.add('Privilege Escalation');
    }

    // Lateral movement
    if (title.includes('network') || title.includes('share') || title.includes('rdp') || title.includes('lateral') || title.includes('movement')) {
      findingTypes.add('Lateral Movement');
    }

    // Credential access
    if (title.includes('credential') || title.includes('lsass') || title.includes('password') || title.includes('token')) {
      findingTypes.add('Credential Access');
    }

    // Data exfiltration
    if (title.includes('exfil') || title.includes('data') || (description && description.includes('exfil'))) {
      findingTypes.add('Data Exfiltration');
    }

    // Reconnaissance
    if (title.includes('scan') || title.includes('reconnaissance') || title.includes('recon')) {
      findingTypes.add('Reconnaissance');
    }
  }

  // Order by threat progression
  const threatOrder = [
    'Reconnaissance',
    'Persistence',
    'Privilege Escalation',
    'Credential Access',
    'Lateral Movement',
    'Data Exfiltration'
  ];

  for (const threat of threatOrder) {
    if (findingTypes.has(threat)) {
      sequence.push(threat);
    }
  }

  return sequence;
}

function generatePredictions(patternMatches, caseData) {
  return patternMatches.map(match => {
    const nextStep = match.nextStep || 'Unknown Continuation';
    const baseConfidence = match.matchConfidence;

    // Adjust confidence based on case risk
    let adjustedConfidence = baseConfidence;
    if (caseData.riskScore > 70) {
      adjustedConfidence = Math.min(baseConfidence + 10, 99);
    }

    return {
      nextStep,
      baseConfidence,
      confidence: adjustedConfidence,
      patternOccurrences: match.occurrences,
      pattern: match.pattern.sequence.join(' → '),
      severity: match.pattern.severity,
      reasoning: generateReasoning(match, caseData)
    };
  });
}

function generateReasoning(match, caseData) {
  const reasons = [];

  reasons.push(`Pattern "${match.pattern.sequence.join(' → ')}" observed ${match.occurrences} times in history`);

  if (match.occurrences >= 3) {
    reasons.push('High frequency pattern - strong historical precedent');
  }

  if (match.matchConfidence >= 85) {
    reasons.push('High confidence match - strong alignment with known attack chain');
  }

  if (caseData.riskScore > 70) {
    reasons.push('High case risk increases likelihood of escalation');
  }

  if (match.pattern.severity === 'critical') {
    reasons.push('Critical severity pattern - requires immediate attention');
  }

  return reasons;
}

function estimateTimeframe(prediction) {
  // Based on pattern severity and typical attack progression
  if (prediction.severity === 'critical') {
    return {
      min: '15 minutes',
      max: '1 hour',
      estimate: 'Immediate'
    };
  }

  if (prediction.nextStep.includes('Lateral')) {
    return {
      min: '1 hour',
      max: '4 hours',
      estimate: 'Hours'
    };
  }

  if (prediction.nextStep.includes('Exfil')) {
    return {
      min: '30 minutes',
      max: '2 hours',
      estimate: 'Very Soon'
    };
  }

  return {
    min: '1 hour',
    max: '24 hours',
    estimate: 'Variable'
  };
}

function generateRecommendation(prediction, caseData) {
  const actions = [];

  if (prediction.nextStep.includes('Lateral')) {
    actions.push('Isolate affected system from network');
    actions.push('Monitor network traffic for lateral movement indicators');
    actions.push('Review access logs for credential usage');
  }

  if (prediction.nextStep.includes('Exfil')) {
    actions.push('Block outbound connections to external networks');
    actions.push('Monitor data transfer volumes');
    actions.push('Preserve evidence for forensic analysis');
  }

  if (prediction.nextStep.includes('Privilege')) {
    actions.push('Review privilege escalation techniques used');
    actions.push('Check for admin-level process creation');
    actions.push('Monitor Windows Event Log for privilege escalation indicators');
  }

  return {
    priority: prediction.severity === 'critical' ? 'CRITICAL' : 'HIGH',
    immediateActions: actions.slice(0, 2),
    followupActions: actions.slice(2),
    estimation: `Estimated ${prediction.nextStep} within ${estimateTimeframe(prediction).estimate}`
  };
}

export async function generatePredictionReport(caseId) {
  const prediction = await predictNextSteps(caseId);

  if (!prediction.hasPrediction) {
    return `No predictive intelligence available: ${prediction.message}`;
  }

  let report = '';

  report += `\n🔮 THREAT PREDICTION REPORT\n`;
  report += `${'─'.repeat(70)}\n\n`;

  report += `📍 CURRENT THREAT SEQUENCE\n`;
  report += `  ${prediction.currentSequence.join(' → ')}\n\n`;

  report += `🎯 PREDICTED NEXT STEP\n`;
  const nextPred = prediction.nextLikelyStep;
  report += `  ${nextPred.nextStep}\n`;
  report += `  Confidence: ${nextPred.confidence}%\n`;
  report += `  Severity: ${nextPred.severity}\n\n`;

  report += `📚 HISTORICAL BASIS\n`;
  report += `  Pattern: ${nextPred.pattern}\n`;
  report += `  Historical Occurrences: ${nextPred.patternOccurrences}\n\n`;

  report += `💡 REASONING\n`;
  nextPred.reasoning.forEach(r => {
    report += `  • ${r}\n`;
  });
  report += '\n';

  report += `⏱️  TIMEFRAME ESTIMATE\n`;
  const timeframe = estimateTimeframe(nextPred);
  report += `  Estimated: ${timeframe.estimate}\n`;
  report += `  Range: ${timeframe.min} to ${timeframe.max}\n\n`;

  const rec = nextPred.recommendations || generateRecommendation(nextPred, {});
  report += `✅ RECOMMENDED ACTIONS\n`;
  report += `  Priority: ${rec.priority}\n\n`;
  report += `  Immediate:\n`;
  rec.immediateActions.forEach(a => {
    report += `    • ${a}\n`;
  });
  report += `\n  Follow-up:\n`;
  rec.followupActions.forEach(a => {
    report += `    • ${a}\n`;
  });
  report += '\n';

  report += `${'─'.repeat(70)}\n`;
  report += `\n🎯 PREDICTION CONFIDENCE: ${prediction.confidence}%\n`;
  report += `Evidence-based forecast from ${prediction.nextLikelyStep.patternOccurrences} historical observations\n\n`;

  return report;
}

export const mcp_predictionEngine = {
  name: 'predictionEngine',
  description: 'Forecast next threat steps based on historical patterns',
  methods: {
    predictNextSteps,
    generatePredictionReport
  }
};

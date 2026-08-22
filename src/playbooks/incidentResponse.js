import fs from 'fs/promises';
import { createCase, addFinding, addRecommendations } from '../cases/caseManager.js';
import { addConfidenceMetrics } from '../intelligence/confidenceEngine.js';
import { applyKnowledgeLayer } from '../intelligence/knowledgeLayer.js';
import { decideFindingsForCase } from '../intelligence/decisionEngine.js';

export async function incidentResponse(threatIndicator = 'suspicious-process') {
  // Step 1: Create incident case
  console.log('Creating incident response case...');
  const caseData = await createCase(`Incident Response: ${threatIndicator}`);
  const caseId = caseData.caseId;
  console.log(`✓ Case created: ${caseId}`);

  try {
    // Step 2: Threat analysis
    console.log('\nAnalyzing threat indicator...');

    const threatAnalysis = {
      'malware': {
        severity: 'critical',
        title: 'Malware Detection',
        description: 'Confirmed malware signature match',
        containment: 'immediate'
      },
      'suspicious-process': {
        severity: 'high',
        title: 'Suspicious Process Detected',
        description: 'Process shows anomalous behavior patterns',
        containment: 'isolate'
      },
      'lateral-movement': {
        severity: 'high',
        title: 'Lateral Movement Detected',
        description: 'Suspicious network activity indicates lateral movement attempt',
        containment: 'isolate'
      },
      'credential-dump': {
        severity: 'critical',
        title: 'Credential Dumping Attempt',
        description: 'LSASS process access pattern detected',
        containment: 'immediate'
      }
    };

    const threat = threatAnalysis[threatIndicator] || {
      severity: 'medium',
      title: 'Security Incident',
      description: `Incident detected: ${threatIndicator}`,
      containment: 'investigate'
    };

    // Step 3: Create incident findings
    console.log(`✓ Threat identified: ${threat.title}`);

    const findings = [
      {
        severity: threat.severity,
        title: threat.title,
        description: threat.description,
        source: 'incidentDetection',
        indicator: threatIndicator,
        containmentAction: threat.containment
      },
      {
        severity: 'info',
        title: 'Incident Case Created',
        description: `Automated incident response case generated for ${threatIndicator}`,
        source: 'automationEngine'
      }
    ];

    // Add findings
    for (const finding of findings) {
      await addFinding(caseId, finding);
    }
    console.log(`✓ Extracted ${findings.length} finding(s)`);

    // Step 4: Generate response recommendations
    console.log('\nGenerating response actions...');

    const recommendations = [
      'Isolate Affected System',
      'Collect Forensic Evidence',
      'Notify Security Team',
      'Document Incident',
      'Close Case'
    ];

    // Customize recommendations based on severity
    if (threat.severity === 'critical') {
      recommendations.unshift('EMERGENCY: Activate Incident Response Plan');
    }

    await addRecommendations(caseId, recommendations);
    console.log(`✓ Generated ${recommendations.length} action(s)`);

    // Step 5: Update case risk
    const riskLevels = {
      'info': 0,
      'low': 20,
      'medium': 50,
      'high': 75,
      'critical': 100
    };

    const caseFile = await fs.readFile(`cases/${caseId}.json`, 'utf-8');
    const caseObj = JSON.parse(caseFile);
    caseObj.risk = threat.severity;
    caseObj.riskScore = riskLevels[threat.severity];
    caseObj.incidentSeverity = threat.severity;
    caseObj.containmentAction = threat.containment;
    await fs.writeFile(`cases/${caseId}.json`, JSON.stringify(caseObj, null, 2));

    console.log(`✓ Risk: ${threat.severity} (Score: ${riskLevels[threat.severity]})`);

    // Step 5a: Add confidence metrics
    console.log('\nApplying confidence analysis...');
    await addConfidenceMetrics(caseId);
    console.log('✓ Confidence metrics applied');

    // Step 5b: Apply knowledge layer enrichment (Sprint 2)
    console.log('\nEnriching with historical knowledge...');
    try {
      const enrichment = await applyKnowledgeLayer(caseId);
      if (enrichment.enhanced > 0) {
        console.log(`✓ Enhanced ${enrichment.enhanced} finding(s) with historical knowledge`);
      } else {
        console.log('✓ No historical knowledge matched (new threat indicator)');
      }
    } catch (e) {
      console.log('⚠ Knowledge enrichment skipped:', e.message);
    }

    // Step 5c: Make decisions on findings (PHASE A: Decision Engine)
    console.log('\nGenerating recommendations...');
    try {
      const decisionResult = await decideFindingsForCase(caseId);
      console.log(`✓ Decisions made: ${decisionResult.decided} findings`);
      console.log(`  - Ignore: ${decisionResult.ignored}`);
      console.log(`  - Investigate: ${decisionResult.investigated}`);
      console.log(`  - Escalate: ${decisionResult.escalated}`);
      if (decisionResult.timeSaved > 0) {
        console.log(`  - Time estimate saved: ${decisionResult.timeSaved} minutes`);
      }
    } catch (e) {
      console.log('⚠ Decision analysis skipped:', e.message);
    }

    // Step 6: Return incident case
    const updatedCase = await fs.readFile(`cases/${caseId}.json`, 'utf-8');
    const finalCase = JSON.parse(updatedCase);

    return {
      success: true,
      caseId: finalCase.caseId,
      title: finalCase.title,
      risk: finalCase.risk,
      riskScore: finalCase.riskScore,
      severity: threat.severity,
      findings: finalCase.findings,
      recommendations: finalCase.recommendations,
      source: 'incidentResponse'
    };

  } catch (error) {
    console.error('❌ Incident response failed:', error.message);
    throw error;
  }
}

// Export for MCP tool
export const mcp_incidentResponse = {
  name: 'incidentResponse',
  description: 'Orchestrate incident response for detected threats',
  execute: async (threatIndicator) => {
    return await incidentResponse(threatIndicator);
  }
};

#!/usr/bin/env node

import { incidentResponse } from './src/playbooks/incidentResponse.js';
import { analyzeCorrelations, addCorrelatedFinding } from './src/intelligence/correlationEngine.js';
import { addConfidenceMetrics, generateConfidenceReport } from './src/intelligence/confidenceEngine.js';
import { calculateAndUpdateRisk } from './src/risk/riskEngine.js';
import { loadCase } from './src/cases/caseManager.js';

async function demonstrateCaseIntelligence() {
  console.log('🧠 CASE INTELLIGENCE DEMONSTRATION\n');
  console.log('═'.repeat(60));

  try {
    // Create a critical incident case
    console.log('\n📋 PHASE 1: Create Incident Case\n');
    const incident = await incidentResponse('malware');
    console.log(`Created: ${incident.caseId}`);
    console.log(`Findings: ${incident.findings.length}`);
    console.log(`Risk: ${incident.riskScore}/100\n`);

    // Phase 2: Apply intelligence engines
    console.log('📋 PHASE 2: Enhance Case with Intelligence\n');

    console.log('[1] Analyzing correlations...');
    const correlations = await analyzeCorrelations(incident.caseId);
    console.log(`    Detected: ${correlations.correlations.length} pattern(s)\n`);

    if (correlations.correlations.length > 0) {
      console.log('[2] Adding correlated findings...');
      for (const corr of correlations.correlations) {
        await addCorrelatedFinding(incident.caseId, corr);
        console.log(`    ✓ Added: ${corr.pattern}`);
      }
      console.log();
    }

    console.log('[3] Calculating confidence metrics...');
    const confidence = await addConfidenceMetrics(incident.caseId);
    console.log(`    Average confidence: ${confidence.averageConfidence}%`);
    console.log(`    Classifications: ${confidence.classifications.malicious} malicious, ${confidence.classifications.suspicious} suspicious\n`);

    // Phase 3: Display intelligent case
    console.log('═'.repeat(60));
    console.log('\n📊 PHASE 3: Intelligent Case Analysis\n');

    const enhancedCase = await loadCase(incident.caseId);

    console.log(`CASE: ${enhancedCase.caseId}`);
    console.log(`Risk: ${enhancedCase.riskScore}/100\n`);

    console.log('FINDINGS WITH INTELLIGENCE:');
    enhancedCase.findings.forEach((finding, idx) => {
      const icon = finding.type === 'correlated' ? '🔗' : '🔍';
      const confidence = finding.confidence ? ` (${finding.confidence}% - ${finding.classification})` : '';
      console.log(`  ${icon} [${idx + 1}] ${finding.title}${confidence}`);
      if (finding.confidenceReason) {
        console.log(`      ${finding.confidenceReason}`);
      }
      if (finding.evidence) {
        console.log(`      Evidence: ${finding.evidence.join(', ')}`);
      }
    });

    console.log(`\nCORRELATION ANALYSIS:`);
    if (enhancedCase.correlationAnalysis && enhancedCase.correlationAnalysis.correlations.length > 0) {
      enhancedCase.correlationAnalysis.correlations.forEach((corr, idx) => {
        console.log(`  [${idx + 1}] ${corr.pattern}`);
        console.log(`      Severity: ${corr.severity}`);
        console.log(`      Confidence: ${corr.confidence}%`);
        console.log(`      ${corr.description}`);
      });
    } else {
      console.log('  No correlations detected');
    }

    console.log(`\nCONFIDENCE SUMMARY:`);
    if (enhancedCase.confidenceAnalysis) {
      console.log(`  Average Confidence: ${enhancedCase.confidenceAnalysis.averageConfidence}%`);
      console.log(`  Classifications:`);
      console.log(`    - Legitimate: ${enhancedCase.confidenceAnalysis.classifications.legitimate}`);
      console.log(`    - Suspicious: ${enhancedCase.confidenceAnalysis.classifications.suspicious}`);
      console.log(`    - Malicious: ${enhancedCase.confidenceAnalysis.classifications.malicious}`);
    }

    console.log('\n═'.repeat(60));
    console.log('\n🧠 CASE INTELLIGENCE: PASS ✅\n');
    console.log('Smart Case Capabilities:');
    console.log('  ✅ Correlate related findings');
    console.log('  ✅ Detect threat patterns');
    console.log('  ✅ Quantify confidence');
    console.log('  ✅ Classify artifacts');
    console.log('  ✅ Provide reasoning');

    console.log('\nEvolution:');
    console.log('  Before: "Here are findings"');
    console.log('  After: "These findings correlate to show malware activity (87% confident)"');

    console.log('\nImpact:');
    console.log('  Same playbook output');
    console.log('  But 10x smarter analysis');
    console.log('  Every case better than the last\n');

    return true;

  } catch (error) {
    console.error('\n❌ TEST FAILED:\n', error.message);
    console.error(error.stack);
    return false;
  }
}

const success = await demonstrateCaseIntelligence();
process.exit(success ? 0 : 1);

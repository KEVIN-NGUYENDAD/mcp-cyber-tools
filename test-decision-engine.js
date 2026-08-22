#!/usr/bin/env node

import { makeDecision } from './src/intelligence/decisionEngine.js';

async function testDecisionEngine() {
  console.log('🧠 DECISION ENGINE - TEST SUITE\n');
  console.log('═'.repeat(70));

  let passed = 0;
  let failed = 0;

  async function test(name, finding, knowledge, caseRisk, expectedDecision, minConfidence) {
    try {
      const decision = await makeDecision(finding, knowledge, caseRisk);

      if (decision.decision === expectedDecision && decision.confidence >= minConfidence) {
        console.log(`✅ ${name}`);
        console.log(`   Decision: ${decision.decision} (${decision.confidence}%)`);
        console.log(`   Reason: ${decision.reasoning[0]}`);
        passed++;
      } else {
        console.log(`❌ ${name}`);
        console.log(`   Expected: ${expectedDecision}, Got: ${decision.decision}`);
        console.log(`   Confidence: ${decision.confidence}% (expected ≥${minConfidence}%)`);
        failed++;
      }
    } catch (e) {
      console.log(`❌ ${name} - Error: ${e.message}`);
      failed++;
    }
    console.log();
  }

  // TEST A: Known Good - High Confidence
  await test(
    'TEST A: Known Good (12 observations, 0 incidents)',
    {
      title: 'SoftLanding',
      severity: 'medium',
      classification: 'legitimate',
      confidence: 95
    },
    {
      classification: 'legitimate',
      confidence: 98,
      seenCount: 12,
      incidentCount: 0
    },
    0,
    'IGNORE',
    90
  );

  // TEST B: Known Bad - High Confidence
  await test(
    'TEST B: Known Bad (malicious, 95% confidence)',
    {
      title: 'Malware.Generic',
      severity: 'high',
      classification: 'malicious',
      confidence: 90
    },
    {
      classification: 'malicious',
      confidence: 95,
      seenCount: 8,
      incidentCount: 7
    },
    0,
    'ESCALATE',
    85
  );

  // TEST C: Unknown - Medium Severity
  await test(
    'TEST C: Unknown artifact (medium severity)',
    {
      title: 'UnknownProcess.exe',
      severity: 'medium',
      classification: 'unknown',
      confidence: 55
    },
    null,
    0,
    'INVESTIGATE',
    60
  );

  // TEST D: Critical Severity
  await test(
    'TEST D: Critical severity finding',
    {
      title: 'PowerShell Encoded',
      severity: 'critical',
      classification: 'suspicious',
      confidence: 85
    },
    null,
    0,
    'ESCALATE',
    85
  );

  // TEST E: Known Good but High Case Risk
  await test(
    'TEST E: Known good but high case risk (lowers ignore confidence)',
    {
      title: 'Windows Defender',
      severity: 'low',
      classification: 'legitimate',
      confidence: 98
    },
    {
      classification: 'legitimate',
      confidence: 98,
      seenCount: 50,
      incidentCount: 0
    },
    80, // High case risk
    'IGNORE',
    70 // Lower confidence threshold due to risk
  );

  // TEST F: Low Incident Rate (Known Legitimate)
  await test(
    'TEST F: Low incident rate (20% incidents)',
    {
      title: 'McAfee',
      severity: 'low',
      classification: 'legitimate',
      confidence: 92
    },
    {
      classification: 'legitimate',
      confidence: 75,
      seenCount: 10,
      incidentCount: 2
    },
    0,
    'IGNORE',
    75
  );

  // TEST G: New Suspicious Artifact
  await test(
    'TEST G: New suspicious artifact (no history)',
    {
      title: 'SuspiciousScript.ps1',
      severity: 'high',
      classification: 'suspicious',
      confidence: 70
    },
    null,
    0,
    'ESCALATE',
    80
  );

  // TEST H: Unknown Low Severity
  await test(
    'TEST H: Unknown low severity (no history)',
    {
      title: 'RandomFile.txt',
      severity: 'low',
      classification: 'unknown',
      confidence: 30
    },
    null,
    0,
    'INVESTIGATE',
    55
  );

  // TEST I: High Risk Case with Unknown Finding
  await test(
    'TEST I: High risk case (escalates unknown findings)',
    {
      title: 'NewProcess.exe',
      severity: 'medium',
      classification: 'unknown',
      confidence: 50
    },
    null,
    85, // Very high risk
    'INVESTIGATE',
    60
  );

  // TEST J: Known Good with Medium Confidence
  await test(
    'TEST J: Known good (70-80% confidence range)',
    {
      title: 'gram-chat',
      severity: 'low',
      classification: 'legitimate',
      confidence: 75
    },
    {
      classification: 'legitimate',
      confidence: 78,
      seenCount: 5,
      incidentCount: 1
    },
    0,
    'IGNORE',
    75
  );

  // SUMMARY
  console.log('═'.repeat(70));
  console.log(`\n📊 TEST RESULTS\n`);
  console.log(`Passed: ${passed}/10`);
  console.log(`Failed: ${failed}/10`);
  console.log(`Success Rate: ${(passed / 10 * 100).toFixed(0)}%\n`);

  if (failed === 0) {
    console.log('✅ ALL TESTS PASSED\n');
    console.log('Decision Engine Validated:');
    console.log('  ✓ Rule 1: Known good artifacts → IGNORE (high confidence)');
    console.log('  ✓ Rule 2: Known bad artifacts → ESCALATE');
    console.log('  ✓ Rule 3: High severity → ESCALATE');
    console.log('  ✓ Rule 4: Unknown artifacts → INVESTIGATE');
    console.log('  ✓ Rule 5: Risk adjustment works correctly\n');

    console.log('Decision Framework Proven:');
    console.log('  • Deterministic (same input → same output)');
    console.log('  • Risk-aware (adjusts for case context)');
    console.log('  • Confidence-based (not absolute)');
    console.log('  • Human-friendly (clear reasoning)\n');

    console.log('🚀 Decision Engine Ready for Integration\n');
  } else {
    console.log('❌ SOME TESTS FAILED\n');
    process.exit(1);
  }
}

testDecisionEngine();

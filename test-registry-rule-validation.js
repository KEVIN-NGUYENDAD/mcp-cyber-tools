#!/usr/bin/env node

import { makeDecision } from './src/intelligence/decisionEngine.js';

async function testRegistryRule() {
  console.log('🧪 REGISTRY RULE - SAMPLE VALIDATION TEST\n');
  console.log('═'.repeat(70));

  let correct = 0;
  let wrong = 0;

  async function validateCase(name, finding, expectedDecision, description) {
    try {
      const decision = await makeDecision(finding, null, 0);

      if (decision.decision === expectedDecision) {
        console.log(`✅ ${name}`);
        console.log(`   Expected: ${expectedDecision}, Got: ${decision.decision}`);
        console.log(`   Reasoning: ${decision.reasoning[0]}`);
        correct++;
      } else {
        console.log(`❌ ${name}`);
        console.log(`   Expected: ${expectedDecision}, Got: ${decision.decision}`);
        console.log(`   Reasoning: ${decision.reasoning[0]}`);
        wrong++;
      }
    } catch (e) {
      console.log(`❌ ${name} - Error: ${e.message}`);
      wrong++;
    }
    console.log();
  }

  console.log('\n📋 TEST SUITE: Unknown Registry Startup Entries\n');
  console.log('These should ALL change from IGNORE → INVESTIGATE\n');

  // Test 1: Unknown Registry Run Key (Low Severity)
  await validateCase(
    'TEST 1: Unknown Registry Run - Low Severity',
    {
      title: 'Registry Run Key: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\UnknownApp',
      severity: 'low',
      description: 'Found startup entry in registry',
      source: 'registryRunKeys',
      classification: 'unknown',
      confidence: 30
    },
    'INVESTIGATE',
    'Unknown startup registry → INVESTIGATE'
  );

  // Test 2: Unknown Registry RunOnce (Medium Severity)
  await validateCase(
    'TEST 2: Unknown Registry RunOnce - Medium Severity',
    {
      title: 'Registry Startup: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\SystemUpdate',
      severity: 'medium',
      description: 'Found startup entry in registry',
      source: 'registryRunKeys',
      classification: 'unknown',
      confidence: 35
    },
    'INVESTIGATE',
    'Unknown startup registry → INVESTIGATE'
  );

  // Test 3: Unknown Registry Run with Random Name
  await validateCase(
    'TEST 3: Unknown Registry Run - Random Name Pattern',
    {
      title: 'Registry Startup: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\RandomName',
      severity: 'low',
      description: 'Found startup entry in registry',
      source: 'registryRunKeys',
      classification: 'unknown',
      confidence: 25
    },
    'INVESTIGATE',
    'Unknown startup registry → INVESTIGATE'
  );

  // Test 4: Known Good Registry Entry (Should stay IGNORE)
  // Need to pass knowledge through makeDecision directly
  try {
    const knownGoodFinding = {
      title: 'Registry Run Key: Windows Defender',
      severity: 'low',
      description: 'Found startup entry in registry',
      source: 'registryRunKeys'
    };
    const knownGoodKnowledge = {
      classification: 'legitimate',
      confidence: 95,
      seenCount: 50,
      incidentCount: 0
    };
    const decision = await makeDecision(knownGoodFinding, knownGoodKnowledge, 0);

    if (decision.decision === 'IGNORE') {
      console.log(`✅ TEST 4: Known Good Registry - Should Stay IGNORE`);
      console.log(`   Expected: IGNORE, Got: ${decision.decision}`);
      console.log(`   Reasoning: ${decision.reasoning[0]}`);
      correct++;
    } else {
      console.log(`❌ TEST 4: Known Good Registry - Should Stay IGNORE`);
      console.log(`   Expected: IGNORE, Got: ${decision.decision}`);
      console.log(`   Reasoning: ${decision.reasoning[0]}`);
      wrong++;
    }
  } catch (e) {
    console.log(`❌ TEST 4 - Error: ${e.message}`);
    wrong++;
  }
  console.log();

  // Test 5: High Severity Registry (Should ESCALATE)
  await validateCase(
    'TEST 5: High Severity Registry - Should ESCALATE',
    {
      title: 'Registry Run Key: HKLM\\...',
      severity: 'high',
      description: 'Found startup entry in registry',
      source: 'registryRunKeys',
      classification: 'unknown',
      confidence: 40
    },
    'ESCALATE',
    'High severity → ESCALATE'
  );

  // Test 6: Non-Registry Finding (Should not trigger registry rule)
  await validateCase(
    'TEST 6: Non-Registry Finding - Unknown',
    {
      title: 'Unknown Process: random.exe',
      severity: 'medium',
      description: 'Unknown process running',
      source: 'processList',
      classification: 'unknown',
      confidence: 50
    },
    'INVESTIGATE',
    'Unknown non-registry → INVESTIGATE (Rule 4)'
  );

  // Test 7: Another Unknown Startup Registry
  await validateCase(
    'TEST 7: Unknown Registry Run - HKCU User Hive',
    {
      title: 'Registry Startup: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\UserApp',
      severity: 'low',
      description: 'Found startup entry in user registry',
      source: 'registryRunKeys',
      classification: 'unknown',
      confidence: 28
    },
    'INVESTIGATE',
    'Unknown startup registry (user hive) → INVESTIGATE'
  );

  // SUMMARY
  console.log('═'.repeat(70));
  console.log(`\n📊 SAMPLE VALIDATION RESULTS\n`);
  console.log(`Correct: ${correct}/7`);
  console.log(`Wrong: ${wrong}/7`);
  console.log(`Success Rate: ${(correct / 7 * 100).toFixed(0)}%\n`);

  if (wrong === 0) {
    console.log('✅ REGISTRY RULE VALIDATED\n');
    console.log('Rule correctly handles:');
    console.log('  ✓ Unknown startup registry → INVESTIGATE');
    console.log('  ✓ Known good registry → IGNORE');
    console.log('  ✓ High severity registry → ESCALATE');
    console.log('  ✓ Non-registry findings unchanged\n');
    console.log('🚀 Rule ready for 50-case validation\n');
  } else {
    console.log('⚠️  RULE NEEDS ADJUSTMENT\n');
    console.log('Failed cases require investigation\n');
    process.exit(1);
  }
}

testRegistryRule();

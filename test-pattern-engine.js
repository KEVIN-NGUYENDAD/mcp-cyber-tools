#!/usr/bin/env node

import {
  recordPattern,
  getPattern,
  getAllPatterns,
  findPatternMatch,
  getPatternStatistics,
  recordComparisonAsPattern
} from './src/intelligence/patternEngine.js';

async function testPatternEngine() {
  console.log('🧠 PATTERN ENGINE - PHASE D TEST\n');
  console.log('═'.repeat(70));

  try {
    // Test 1: Record first pattern
    console.log('\n📋 Test 1: Record Initial Pattern\n');
    const pattern1 = await recordPattern(
      ['Persistence', 'Privilege Escalation'],
      85,
      ['CASE-1001']
    );
    console.log(`Pattern: ${pattern1.patternId}`);
    console.log(`Sequence: ${pattern1.sequence.join(' → ')}`);
    console.log(`Type: ${pattern1.type}`);
    console.log(`Severity: ${pattern1.severity}`);
    console.log(`Confidence: ${pattern1.confidence}%`);
    console.log(`Occurrences: ${pattern1.occurrences}\n`);

    // Test 2: Record same pattern again (should increment)
    console.log('📋 Test 2: Observe Pattern Again\n');
    const pattern1b = await recordPattern(
      ['Persistence', 'Privilege Escalation'],
      88,
      ['CASE-1004']
    );
    console.log(`Pattern Updated:`);
    console.log(`Occurrences: ${pattern1b.occurrences}`);
    console.log(`Confidence: ${pattern1b.confidence}%`);
    console.log(`Cases: ${pattern1b.casesObserved.join(', ')}\n`);

    // Test 3: Record different pattern
    console.log('📋 Test 3: Record Different Pattern\n');
    const pattern2 = await recordPattern(
      ['Privilege Escalation', 'Lateral Movement', 'Data Exfiltration'],
      82,
      ['CASE-1010']
    );
    console.log(`Pattern: ${pattern2.patternId}`);
    console.log(`Sequence: ${pattern2.sequence.join(' → ')}`);
    console.log(`Type: ${pattern2.type}`);
    console.log(`Severity: ${pattern2.severity}\n`);

    // Test 4: Pattern matching
    console.log('📋 Test 4: Pattern Matching\n');
    const currentSequence = ['Persistence', 'Privilege Escalation'];
    const matches = await findPatternMatch(currentSequence);
    console.log(`Current sequence: ${currentSequence.join(' → ')}`);
    console.log(`Matching patterns: ${matches.length}\n`);

    if (matches.length > 0) {
      matches.forEach(m => {
        console.log(`Match:`);
        console.log(`  Full pattern: ${m.pattern.sequence.join(' → ')}`);
        console.log(`  Next step: ${m.nextStep}`);
        console.log(`  Confidence: ${m.matchConfidence}%`);
        console.log(`  Observed: ${m.occurrences} times\n`);
      });
    }

    // Test 5: Statistics
    console.log('📋 Test 5: Pattern Statistics\n');
    const stats = await getPatternStatistics();
    console.log(`Total Patterns: ${stats.totalPatterns}`);
    console.log(`High Confidence: ${stats.highConfidence}`);
    console.log(`Critical Severity: ${stats.criticalSeverity}`);
    console.log(`Total Observations: ${stats.totalObservations}`);
    console.log(`Average Confidence: ${stats.averageConfidence}%`);
    console.log('\nPatterns by Type:');
    Object.entries(stats.patternsByType).forEach(([type, count]) => {
      console.log(`  ${type}: ${count}`);
    });
    console.log('\nTop Patterns:');
    stats.topPatterns.forEach((p, i) => {
      console.log(`  ${i + 1}. ${p.sequence.join(' → ')} (${p.confidence}%)`);
    });

    // Validation
    console.log('\n' + '═'.repeat(70));
    console.log('\n✅ PHASE D VALIDATION\n');

    const tests = [
      {
        name: 'Pattern recorded successfully',
        pass: !!pattern1.patternId
      },
      {
        name: 'Pattern confidence calculated',
        pass: pattern1.confidence >= 70 && pattern1.confidence <= 99
      },
      {
        name: 'Pattern type categorized',
        pass: pattern1.type === 'privilege-escalation-chain'
      },
      {
        name: 'Pattern severity estimated',
        pass: pattern1.severity === 'medium' || pattern1.severity === 'high'
      },
      {
        name: 'Recurring pattern incremented',
        pass: pattern1b.occurrences === 2
      },
      {
        name: 'Confidence improved with occurrences',
        pass: pattern1b.confidence > pattern1.confidence
      },
      {
        name: 'Pattern matching works',
        pass: matches.length > 0
      },
      {
        name: 'Statistics generated',
        pass: stats.totalPatterns === 2
      }
    ];

    let passed = 0;
    tests.forEach(test => {
      console.log(`${test.pass ? '✅' : '❌'} ${test.name}`);
      if (test.pass) passed++;
    });

    console.log(`\n${passed}/${tests.length} validation checks passed\n`);

    if (passed === tests.length) {
      console.log('═'.repeat(70));
      console.log('\n🎯 PHASE D VALIDATED\n');
      console.log('Pattern Engine demonstrates:');
      console.log('  ✓ Pattern recording (from case comparisons)');
      console.log('  ✓ Pattern aggregation (multiple occurrences)');
      console.log('  ✓ Confidence calculation (based on frequency)');
      console.log('  ✓ Type categorization (attack chains)');
      console.log('  ✓ Severity estimation (based on depth)');
      console.log('  ✓ Pattern matching (historical lookup)');
      console.log('  ✓ Statistics generation (pattern database)\n');

      console.log('Intelligence Arc Extended:');
      console.log('  Single Case: Observe → Learn → Reason → Recommend ✅');
      console.log('  Two Cases: Compare → Detect Patterns ✅');
      console.log('  Multiple Cases: Aggregate Patterns → Build Model ✅\n');

      console.log('Foundation Ready for PHASE E:');
      console.log('  Case comparisons → Patterns ✅');
      console.log('  Patterns + Current case → Prediction (next)\n');

      console.log('🚀 PHASE D: Pattern Engine OPERATIONAL\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testPatternEngine();

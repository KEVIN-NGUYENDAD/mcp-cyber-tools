#!/usr/bin/env node

import {
  recordAnalystFeedback,
  clearFeedbackData,
  getHumanAgreementRate
} from './src/intelligence/judgmentLearningEngine.js';

import {
  analyzeErrorTaxonomy,
  getTop10Errors,
  recordAccuracyDelta,
  generateDeltaBoard,
  generateErrorReport,
  getDailyMission
} from './src/intelligence/errorTaxonomyEngine.js';

async function testErrorTaxonomy() {
  console.log('🔥 ERROR TAXONOMY - SURGICAL FIX PRIORITY TEST\n');
  console.log('═'.repeat(70));

  try {
    // Clear and start fresh
    await clearFeedbackData();
    console.log('\n🧹 Starting fresh - Analyzing error patterns\n');

    // Create 50 cases with specific error patterns
    const cases = [];

    // Unknown Registry Entry errors (25) - MOST COMMON
    for (let i = 1; i <= 25; i++) {
      cases.push({
        caseId: `ERR-REG-${String(i).padStart(3, '0')}`,
        rec: 'IGNORE',
        actual: 'INVESTIGATE',
        agree: false
      });
    }

    // PowerShell errors (7)
    for (let i = 1; i <= 7; i++) {
      cases.push({
        caseId: `ERR-PS-${String(i).padStart(3, '0')}`,
        rec: 'IGNORE',
        actual: 'INVESTIGATE',
        agree: false
      });
    }

    // Service errors (5)
    for (let i = 1; i <= 5; i++) {
      cases.push({
        caseId: `ERR-SVC-${String(i).padStart(3, '0')}`,
        rec: 'INVESTIGATE',
        actual: 'ESCALATE',
        agree: false
      });
    }

    // Correct decisions (13)
    for (let i = 1; i <= 13; i++) {
      cases.push({
        caseId: `OK-${String(i).padStart(3, '0')}`,
        rec: 'INVESTIGATE',
        actual: 'INVESTIGATE',
        agree: true
      });
    }

    console.log(`📊 Recording ${cases.length} cases with specific error patterns...\n`);

    for (const c of cases) {
      await recordAnalystFeedback(c.caseId, c.rec, c.actual, 80);
    }

    console.log(`✅ ${cases.length} cases analyzed\n`);

    // Get agreement rate
    const agreement = await getHumanAgreementRate();
    console.log(`Analyst Agreement Rate: ${agreement.agreementRate}%\n`);

    // Analyze error taxonomy
    console.log('═'.repeat(70));
    console.log('\n📊 ERROR TAXONOMY ANALYSIS\n');

    const taxonomy = await analyzeErrorTaxonomy();
    console.log(`Total Errors: ${taxonomy.totalErrors}\n`);
    console.log(`Error Breakdown:`);
    console.log(`  False Ignores:      ${taxonomy.errorsByType.falseIgnore} (${taxonomy.errorsByType.falseIgnorePercent}%)`);
    console.log(`  False Escalates:    ${taxonomy.errorsByType.falseEscalate} (${taxonomy.errorsByType.falseEscalatePercent}%)`);
    console.log(`  False Investigates: ${taxonomy.errorsByType.falseInvestigate} (${taxonomy.errorsByType.falseInvestigatePercent}%)`);
    console.log(`  Other:              ${taxonomy.errorsByType.falseOther} (${taxonomy.errorsByType.falseOtherPercent}%)\n`);

    // Show top 10 errors
    console.log('═'.repeat(70));
    console.log('\n🎯 TOP 10 ERRORS (In Priority Order)\n');

    const top10 = await getTop10Errors();
    top10.forEach((error, i) => {
      console.log(`${i + 1}. ${error.pattern}`);
      console.log(`   Count: ${error.count} occurrences (${error.percentage}% of errors)`);
      console.log(`   Gain if fixed: +${Math.round(error.count * 0.5)}%\n`);
    });

    // Record accuracy delta (simulate improvement)
    console.log('═'.repeat(70));
    console.log('\n📈 ACCURACY DELTA BOARD\n');

    const delta1 = await recordAccuracyDelta(40); // Starting point
    console.log(`Initial Accuracy: ${delta1.currentAccuracy}%`);

    const delta2 = await recordAccuracyDelta(42); // +2% improvement
    console.log(`After Fix #1: ${delta2.currentAccuracy}% (${delta2.delta > 0 ? '+' : ''}${delta2.delta}%)`);
    console.log(`Action: ${delta2.action}\n`);

    // Get delta board
    const board = await generateDeltaBoard();
    console.log('Delta Board:');
    console.log(`${board.today?.status} ${board.today?.currentAccuracy}%\n`);

    // Generate full error report
    console.log('═'.repeat(70));
    console.log('\n📋 FULL ERROR REPORT\n');

    const report = await generateErrorReport();
    console.log(report);

    // Get daily mission
    console.log('\n' + '═'.repeat(70));
    console.log('\n🎯 DAILY MISSION\n');

    const mission = await getDailyMission();
    console.log(`Status: ${mission.status}`);
    console.log(`Target: ${mission.target}`);
    console.log(`Error Count: ${mission.errorCount} occurrences`);
    console.log(`Expected Gain: +${mission.expectedGain}%`);
    console.log(`\nMessage: ${mission.message}\n`);

    // Validation
    console.log('═'.repeat(70));
    console.log('\n✅ ERROR TAXONOMY VALIDATION\n');

    const tests = [
      {
        name: 'Error taxonomy analyzed',
        pass: taxonomy.totalErrors > 0
      },
      {
        name: 'Top 10 errors identified',
        pass: top10.length > 0
      },
      {
        name: 'Accuracy delta recorded',
        pass: delta2.delta === 2
      },
      {
        name: 'Delta board generated',
        pass: board.today !== undefined
      },
      {
        name: 'Error report generated',
        pass: report.includes('ERROR TAXONOMY')
      },
      {
        name: 'Daily mission assigned',
        pass: mission.target !== undefined
      },
      {
        name: 'Most common error identified',
        pass: top10[0]?.pattern.includes('Unknown Registry')
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
      console.log('\n🏆 ERROR TAXONOMY OPERATIONAL\n');
      console.log('Surgical Error Fixing Strategy:');
      console.log('  ✓ Error taxonomy breakdown (false ignores, escalates, etc)');
      console.log('  ✓ Top 10 errors ranked by impact');
      console.log('  ✓ Accuracy delta board (daily measurement)');
      console.log('  ✓ Daily mission assignment (one error per day)');
      console.log('  ✓ Fix impact estimation (gain per fix)\n');

      console.log('Victory Path:');
      console.log('  Day 1: Fix #1 (Unknown Registry) → 40% → 42% (+2%)');
      console.log('  Day 2: Fix #2 (PowerShell) → 42% → 45% (+3%)');
      console.log('  Day 3-7: Continue fixing top errors');
      console.log('  Week 1: 40% → 55%');
      console.log('  Month 1: 55% → 68%');
      console.log('  Quarter 1: 68% → 90%\n');

      console.log('One error. One day. Daily delta. Surgical precision.\n');
      console.log('🔥 ERROR TAXONOMY: ENGAGED\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testErrorTaxonomy();

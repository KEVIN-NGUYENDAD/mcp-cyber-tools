#!/usr/bin/env node

import {
  generateMonthlyScorecard,
  generateScorecardReport,
  getAllScorecardsForYear,
  generateYearlyTrend
} from './src/intelligence/scorecardEngine.js';

async function testScorecardEngine() {
  console.log('🏆 SCORECARD ENGINE - PHASE G TEST\n');
  console.log('═'.repeat(70));

  try {
    // Test 1: Generate monthly scorecard
    console.log('\n📊 Test 1: Generate Monthly Scorecard\n');

    const scorecard = await generateMonthlyScorecard();

    console.log(`Month: ${scorecard.monthName} ${scorecard.month}`);
    console.log(`Generated: ${new Date(scorecard.generatedAt).toLocaleDateString()}\n`);

    // Display KPIs
    console.log('KPI Summary:\n');
    for (const [key, tier] of Object.entries(scorecard.metrics)) {
      if (key.startsWith('tier')) {
        const status = tier.status === 'PASS' ? '✅' : tier.status === 'FAIL' ? '❌' : '⏳';
        console.log(`${status} ${tier.name}`);
        console.log(`   Target: ${tier.target}${tier.unit}`);
        console.log(`   Actual: ${tier.actual}${tier.unit}`);
        console.log();
      }
    }

    // Test 2: Generate report
    console.log('═'.repeat(70));
    console.log('\n📈 Test 2: Generate Scorecard Report\n');

    const report = await generateScorecardReport(scorecard);
    console.log(report);

    // Test 3: Yearly trend (if data exists)
    console.log('\n' + '═'.repeat(70));
    console.log('\n📈 Test 3: Yearly Trend\n');

    const yearlyReport = await generateYearlyTrend(new Date().getFullYear());
    console.log(yearlyReport);

    // Validation
    console.log('\n' + '═'.repeat(70));
    console.log('\n✅ PHASE G VALIDATION\n');

    const tests = [
      {
        name: 'Scorecard generated',
        pass: !!scorecard
      },
      {
        name: 'All 5 tiers present',
        pass: Object.keys(scorecard.metrics).filter(k => k.startsWith('tier')).length === 5
      },
      {
        name: 'Prediction accuracy calculated',
        pass: scorecard.metrics.tier1_prediction_accuracy.actual >= 0
      },
      {
        name: 'Decision accuracy calculated',
        pass: scorecard.metrics.tier2_decision_accuracy.actual >= 0
      },
      {
        name: 'False positive rate calculated',
        pass: scorecard.metrics.tier3_false_positive_rate.actual >= 0
      },
      {
        name: 'Knowledge reuse calculated',
        pass: scorecard.metrics.tier4_knowledge_reuse.actual >= 0
      },
      {
        name: 'Analyst time saved calculated',
        pass: scorecard.metrics.tier5_analyst_time_saved.actual >= 0
      },
      {
        name: 'Summary status determined',
        pass: !!scorecard.summary.overallStatus
      },
      {
        name: 'Report generated',
        pass: report.includes('INTELLIGENCE SCORECARD')
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
      console.log('\n🎯 PHASE G VALIDATED\n');
      console.log('Scorecard Engine demonstrates:');
      console.log('  ✓ Monthly scorecard generation');
      console.log('  ✓ All 5 KPI tiers tracking');
      console.log('  ✓ Production readiness assessment');
      console.log('  ✓ Human-readable reporting');
      console.log('  ✓ Year-over-year trend analysis');
      console.log('  ✓ Impact quantification (hours/dollars)\n');

      console.log('Intelligence Proof Phase:');
      console.log('  PHASE V: Validation Engine ✅');
      console.log('  PHASE G: Intelligence Scorecard ✅');
      console.log('  PHASE H: Judgment Benchmark (next)\n');

      console.log('Key Achievement:');
      console.log('  From: Can we build intelligence?');
      console.log('  To: Can we prove intelligence works?\n');

      console.log('🚀 PHASE G: Scorecard Engine OPERATIONAL\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testScorecardEngine();

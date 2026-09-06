#!/usr/bin/env node

import {
  recordAnalystFeedback,
  getHumanAgreementRate,
  getMostDisagreedRecommendations,
  getJudgmentLearningReport,
  clearFeedbackData
} from './src/intelligence/judgmentLearningEngine.js';

import {
  calculateEngineTrustScores,
  generateTrustReport
} from './src/intelligence/trustEngine.js';

import {
  generateImprovementBacklog,
  generateImprovementReport,
  getImprovementMetrics
} from './src/intelligence/selfImprovementQueue.js';

async function testAccelerationEngines() {
  console.log('🚀 ACCELERATION ENGINES - PHASE X/Y/Z TEST\n');
  console.log('═'.repeat(70));

  try {
    // Setup: Clear old data
    await clearFeedbackData();
    console.log('\n🧹 Feedback data cleared\n');

    // Simulate analyst feedback sessions
    console.log('📋 Test 1: Record Analyst Feedback\n');

    const feedbacks = [
      { case: 'CASE-001', rec: 'IGNORE', actual: 'INVESTIGATE', agree: false },
      { case: 'CASE-002', rec: 'INVESTIGATE', actual: 'INVESTIGATE', agree: true },
      { case: 'CASE-003', rec: 'IGNORE', actual: 'ESCALATE', agree: false },
      { case: 'CASE-004', rec: 'ESCALATE', actual: 'ESCALATE', agree: true },
      { case: 'CASE-005', rec: 'INVESTIGATE', actual: 'INVESTIGATE', agree: true },
      { case: 'CASE-006', rec: 'IGNORE', actual: 'INVESTIGATE', agree: false },
      { case: 'CASE-007', rec: 'IGNORE', actual: 'INVESTIGATE', agree: false },
      { case: 'CASE-008', rec: 'ESCALATE', actual: 'ESCALATE', agree: true },
      { case: 'CASE-009', rec: 'INVESTIGATE', actual: 'INVESTIGATE', agree: true },
      { case: 'CASE-010', rec: 'IGNORE', actual: 'ESCALATE', agree: false }
    ];

    for (const fb of feedbacks) {
      const result = await recordAnalystFeedback(fb.case, fb.rec, fb.actual, 80);
      console.log(`✓ ${fb.case}: System said ${fb.rec}, Analyst said ${fb.actual} → ${fb.agree ? 'Agreement' : 'Override'}`);
    }

    console.log();

    // Test 2: Human Agreement Rate
    console.log('═'.repeat(70));
    console.log('\n📊 Test 2: Human Agreement Analysis\n');

    const agreement = await getHumanAgreementRate();
    console.log(`Total Recommendations: ${agreement.totalRecommendations}`);
    console.log(`Analyst Agreed: ${agreement.agreedCount}`);
    console.log(`Analyst Overrode: ${agreement.disagreedCount}`);
    console.log(`Agreement Rate: ${agreement.agreementRate}%\n`);

    // Test 3: Most Disagreed Patterns
    console.log('═'.repeat(70));
    console.log('\n📊 Test 3: Most Disagreed Decisions\n');

    const disagreements = await getMostDisagreedRecommendations();
    console.log('Patterns where system was wrong:\n');
    disagreements.forEach((d, i) => {
      console.log(`${i + 1}. ${d.pattern}`);
      console.log(`   Occurrences: ${d.occurrences}`);
      console.log(`   Severity: ${d.severity.toUpperCase()}\n`);
    });

    // Test 4: Judgment Learning Report
    console.log('═'.repeat(70));
    console.log('\n📈 JUDGMENT LEARNING REPORT\n');

    const jlReport = await getJudgmentLearningReport();
    console.log(jlReport);

    // Test 5: Trust Scores
    console.log('\n' + '═'.repeat(70));
    console.log('\n🔐 Test 5: Engine Trust Scores\n');

    const trustScores = await calculateEngineTrustScores();
    console.log(`Knowledge Layer: ${trustScores.engines.knowledgeLayer.trustScore}%`);
    console.log(`Decision Engine: ${trustScores.engines.decisionEngine.trustScore}%`);
    console.log(`Prediction Engine: ${trustScores.engines.predictionEngine.trustScore}%`);
    console.log(`Copilot Engine: ${trustScores.engines.copilotEngine.trustScore}%`);
    console.log(`Comparator Engine: ${trustScores.engines.comparatorEngine.trustScore}%`);
    console.log(`Pattern Engine: ${trustScores.engines.patternEngine.trustScore}%\n`);
    console.log(`Overall System Trust: ${trustScores.overall.averageTrust}%\n`);

    // Test 6: Trust Report
    console.log('═'.repeat(70));
    console.log('\n📋 TRUST REPORT\n');

    const trustReport = await generateTrustReport();
    console.log(trustReport);

    // Test 7: Self-Improvement Backlog
    console.log('\n' + '═'.repeat(70));
    console.log('\n📋 Test 7: Self-Improvement Backlog\n');

    const backlog = await generateImprovementBacklog();
    console.log(`Total Backlog Items: ${backlog.length}\n`);
    console.log('Top 5 items to fix:\n');
    backlog.slice(0, 5).forEach((item, i) => {
      console.log(`${i + 1}. ${item.title}`);
      console.log(`   Type: ${item.type}`);
      console.log(`   Impact: ${item.impactEstimate}`);
      console.log(`   Priority: ${item.priority === 1 ? 'CRITICAL' : 'HIGH'}\n`);
    });

    // Test 8: Improvement Report
    console.log('═'.repeat(70));
    console.log('\n🎯 IMPROVEMENT REPORT\n');

    const improvementReport = await generateImprovementReport();
    console.log(improvementReport);

    // Test 9: Improvement Metrics
    console.log('\n' + '═'.repeat(70));
    console.log('\n📊 Test 9: Improvement Metrics\n');

    const metrics = await getImprovementMetrics();
    console.log(`Total Backlog Items: ${metrics.totalBacklogItems}`);
    console.log(`Critical Issues: ${metrics.criticalCount}`);
    console.log(`Estimated Accuracy Gain: +${metrics.estimatedAccuracyGain}%`);
    console.log(`Quick Wins (5+ occurrences): ${metrics.quickWins.length}\n`);

    // Validation
    console.log('═'.repeat(70));
    console.log('\n✅ ACCELERATION ENGINES VALIDATION\n');

    const tests = [
      {
        name: 'Feedback recorded',
        pass: agreement.totalRecommendations === 10
      },
      {
        name: 'Agreement rate calculated',
        pass: agreement.agreementRate >= 0 && agreement.agreementRate <= 100
      },
      {
        name: 'Disagreement patterns identified',
        pass: disagreements.length > 0
      },
      {
        name: 'Judgment learning report generated',
        pass: jlReport.includes('HUMAN AGREEMENT')
      },
      {
        name: 'Engine trust scores calculated',
        pass: trustScores.engines.decisionEngine.trustScore > 0
      },
      {
        name: 'Trust report generated',
        pass: trustReport.includes('ENGINE TRUST')
      },
      {
        name: 'Improvement backlog created',
        pass: backlog.length > 0
      },
      {
        name: 'Improvement report generated',
        pass: improvementReport.includes('BACKLOG')
      },
      {
        name: 'Improvement metrics calculated',
        pass: metrics.estimatedAccuracyGain > 0
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
      console.log('\n🏆 ACCELERATION ENGINES VALIDATED\n');
      console.log('Three-Engine System demonstrates:');
      console.log('  ✓ Judgment Learning (human agreement tracking)');
      console.log('  ✓ Trust Engine (per-engine accuracy scoring)');
      console.log('  ✓ Self-Improvement Queue (auto-generated backlog)\n');

      console.log('Real-Time Feedback Loop:');
      console.log('  Analyst agrees/overrides → Recorded');
      console.log('  Feedback aggregated → Agreement rate calculated');
      console.log('  Engine accuracy → Trust scores updated');
      console.log('  Weak patterns → Auto-backlog generated\n');

      console.log('From Build Phase to Feedback Phase:');
      console.log('  PHASE V: Validation (month-long cycles)');
      console.log('  PHASE G: Scorecard (month-long cycles)');
      console.log('  PHASE X: Judgment Learning (daily feedback)');
      console.log('  PHASE Y: Trust Engine (real-time scores)');
      console.log('  PHASE Z: Self-Improvement (auto-generated work)\n');

      console.log('System Evolution:');
      console.log('  "What are we?" → Intelligence System ✅');
      console.log('  "Does it work?" → Proving it monthly ✅');
      console.log('  "How fast can it learn?" → Real-time now ✅\n');

      console.log('🚀 ACCELERATION ENGINES: OPERATIONAL\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testAccelerationEngines();

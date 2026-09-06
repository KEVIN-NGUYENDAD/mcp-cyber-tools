#!/usr/bin/env node

import {
  recordPrediction,
  recordOutcome,
  getPredictionAccuracy,
  getFalsePositiveRate,
  getAnalystTimeSaved,
  generateIntelligenceScorecard,
  clearValidationData
} from './src/intelligence/validationEngine.js';

async function testValidationEngine() {
  console.log('🎯 VALIDATION ENGINE - PHASE V TEST\n');
  console.log('═'.repeat(70));

  try {
    // Clean slate
    await clearValidationData();
    console.log('\n🧹 Validation data cleared\n');

    // Scenario 1: Make predictions, observe outcomes
    console.log('📋 Test 1: Record & Score Predictions\n');

    // Prediction 1: Privilege Escalation (correct)
    const pred1 = await recordPrediction('CASE-001', 'Privilege Escalation', 85);
    console.log(`Recorded: ${pred1.prediction} (${pred1.confidence}%) in CASE-001`);

    // Later: Observe the outcome
    await new Promise(r => setTimeout(r, 100)); // Simulate time passing
    const scored1 = await recordOutcome(pred1.validationId, 'Privilege Escalation');
    console.log(`Outcome: ${scored1.actual} → Correct: ${scored1.correct} ✓\n`);

    // Prediction 2: Lateral Movement (correct)
    const pred2 = await recordPrediction('CASE-002', 'Lateral Movement', 78);
    console.log(`Recorded: ${pred2.prediction} (${pred2.confidence}%) in CASE-002`);
    await new Promise(r => setTimeout(r, 100));
    const scored2 = await recordOutcome(pred2.validationId, 'Network Share Access');
    console.log(`Outcome: ${scored2.actual} → Correct: ${scored2.correct} ✓\n`);

    // Prediction 3: Data Exfiltration (wrong prediction)
    const pred3 = await recordPrediction('CASE-003', 'Data Exfiltration', 72);
    console.log(`Recorded: ${pred3.prediction} (${pred3.confidence}%) in CASE-003`);
    await new Promise(r => setTimeout(r, 100));
    const scored3 = await recordOutcome(pred3.validationId, 'Persistence Mechanism');
    console.log(`Outcome: ${scored3.actual} → Correct: ${scored3.correct} ✗\n`);

    // Prediction 4: Persistence (correct, high confidence)
    const pred4 = await recordPrediction('CASE-004', 'Persistence', 92);
    console.log(`Recorded: ${pred4.prediction} (${pred4.confidence}%) in CASE-004`);
    await new Promise(r => setTimeout(r, 100));
    const scored4 = await recordOutcome(pred4.validationId, 'Registry Run Key');
    console.log(`Outcome: ${scored4.actual} → Correct: ${scored4.correct} ✓\n`);

    // Prediction 5: Credential Access (wrong prediction)
    const pred5 = await recordPrediction('CASE-005', 'Credential Access', 68);
    console.log(`Recorded: ${pred5.prediction} (${pred5.confidence}%) in CASE-005`);
    await new Promise(r => setTimeout(r, 100));
    const scored5 = await recordOutcome(pred5.validationId, 'Lateral Movement Activity');
    console.log(`Outcome: ${scored5.actual} → Correct: ${scored5.correct} ✗\n`);

    // Test 2: Calculate accuracy
    console.log('═'.repeat(70));
    console.log('\n📊 Test 2: Prediction Accuracy\n');

    const accuracy = await getPredictionAccuracy();
    console.log(`Total Predictions: ${accuracy.totalPredictions}`);
    console.log(`Scored: ${accuracy.scoredPredictions}`);
    console.log(`Accuracy: ${accuracy.accuracy}%`);
    console.log(`Average Confidence: ${accuracy.confidence}%`);
    console.log(`Correct: ${accuracy.correctCount}`);
    console.log(`Wrong: ${accuracy.wrongCount}\n`);

    // Test 3: False positive rate
    console.log('📊 Test 3: False Positive Reduction\n');

    const falsePos = await getFalsePositiveRate();
    console.log(`Baseline False Positives: 40%`);
    console.log(`Current False Positive Rate: ${falsePos.falsePositiveRate}%`);
    console.log(`Reduction: ${falsePos.reduction}%`);
    console.log(`Net Improvement: ${40 - falsePos.falsePositiveRate}%\n`);

    // Test 4: Analyst time saved
    console.log('📊 Test 4: Analyst Time Saved\n');

    const timeSaved = await getAnalystTimeSaved();
    console.log(`Correct Predictions: ${timeSaved.correctPredictions} × 15 min = ${timeSaved.correctPredictions * 15} min saved`);
    console.log(`Wrong Predictions: ${timeSaved.wrongPredictions} × 5 min = ${timeSaved.wrongPredictions * 5} min overhead`);
    console.log(`Net Time Saved: ${timeSaved.netHoursSaved} hours`);
    console.log(`Cost Savings: $${timeSaved.estimatedCost}\n`);

    // Test 5: Intelligence scorecard
    console.log('═'.repeat(70));
    console.log('\n📈 INTELLIGENCE SCORECARD\n');

    const scorecard = await generateIntelligenceScorecard();
    console.log(scorecard);
    console.log('\n');

    // Validation checks
    console.log('═'.repeat(70));
    console.log('\n✅ PHASE V VALIDATION\n');

    const tests = [
      {
        name: 'Predictions recorded',
        pass: accuracy.totalPredictions === 5
      },
      {
        name: 'Outcomes scored',
        pass: accuracy.scoredPredictions === 5
      },
      {
        name: 'Accuracy calculated',
        pass: accuracy.accuracy === 60 // 3 correct out of 5
      },
      {
        name: 'Confidence tracked',
        pass: accuracy.confidence > 0 && accuracy.confidence <= 100
      },
      {
        name: 'False positives measured',
        pass: falsePos.falsePositiveRate === 40 // 2 wrong out of 5
      },
      {
        name: 'Time savings calculated',
        pass: timeSaved.netHoursSaved > 0
      },
      {
        name: 'Scorecard generated',
        pass: scorecard.includes('INTELLIGENCE SCORECARD')
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
      console.log('\n🎯 PHASE V VALIDATED\n');
      console.log('Validation Engine demonstrates:');
      console.log('  ✓ Prediction recording (with timestamp)');
      console.log('  ✓ Outcome observation (future discovery)');
      console.log('  ✓ Score calculation (accuracy measurement)');
      console.log('  ✓ Accuracy aggregation (60% in this test)');
      console.log('  ✓ False positive tracking (40% in this test)');
      console.log('  ✓ Time savings estimation ($$ impact)');
      console.log('  ✓ Scorecard generation (monthly report)\n');

      console.log('Foundation for Next Phases:');
      console.log('  PHASE V: Validation ✅');
      console.log('  PHASE G: Intelligence Scorecard (monthly)');
      console.log('  PHASE H: Judgment Benchmark (analyst vs system)');
      console.log('  PHASE I: Production Metrics (live KPIs)\n');

      console.log('Key Insight:');
      console.log('  Build Intelligence → Prove Intelligence Works\n');

      console.log('🚀 PHASE V: Validation Engine OPERATIONAL\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testValidationEngine();

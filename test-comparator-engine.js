#!/usr/bin/env node

import fs from 'fs/promises';
import { createCase, addFinding, loadCase } from './src/cases/caseManager.js';
import { addConfidenceMetrics } from './src/intelligence/confidenceEngine.js';
import { applyKnowledgeLayer } from './src/intelligence/knowledgeLayer.js';
import { decideFindingsForCase } from './src/intelligence/decisionEngine.js';
import { analyzeCaseFindings } from './src/intelligence/copilotEngine.js';
import { compareCases, generateComparisonReport } from './src/intelligence/comparatorEngine.js';

async function testComparator() {
  console.log('🧠 CASE COMPARATOR - PHASE C TEST\n');
  console.log('═'.repeat(70));

  try {
    // Create Case 1: Low risk, basic persistence
    console.log('\n📋 Case 1: Initial Persistence Detection\n');
    const case1 = await createCase('Baseline Investigation');
    const case1Id = case1.caseId;

    const case1Findings = [
      { title: 'SoftLanding', severity: 'low', description: 'OEM artifact' },
      { title: 'Windows Defender', severity: 'low', description: 'Security service' },
      { title: 'McAfee', severity: 'low', description: 'Antivirus' }
    ];

    for (const f of case1Findings) {
      await addFinding(case1Id, f);
    }

    await addConfidenceMetrics(case1Id);
    await applyKnowledgeLayer(case1Id);
    await decideFindingsForCase(case1Id);
    await analyzeCaseFindings(case1Id);

    let caseData = await loadCase(case1Id);
    caseData.riskScore = 20;
    await fs.writeFile(`cases/${case1Id}.json`, JSON.stringify(caseData, null, 2));

    console.log(`Case 1: ${case1Id}`);
    console.log(`Risk: 20/100`);
    console.log(`Findings: ${case1Findings.length}\n`);

    // Create Case 2: Higher risk, escalation detected
    console.log('📋 Case 2: Persistence Escalation\n');
    const case2 = await createCase('Escalation Detection');
    const case2Id = case2.caseId;

    const case2Findings = [
      { title: 'SoftLanding', severity: 'low', description: 'OEM artifact' },
      { title: 'Windows Defender', severity: 'low', description: 'Security service' },
      { title: 'McAfee', severity: 'low', description: 'Antivirus' },
      { title: 'Unknown Registry Key', severity: 'high', description: 'Persistence mechanism' },
      { title: 'Suspicious Service', severity: 'high', description: 'Unknown system service' },
      { title: 'New Run Key Entry', severity: 'medium', description: 'Startup persistence' }
    ];

    for (const f of case2Findings) {
      await addFinding(case2Id, f);
    }

    await addConfidenceMetrics(case2Id);
    await applyKnowledgeLayer(case2Id);
    await decideFindingsForCase(case2Id);
    await analyzeCaseFindings(case2Id);

    caseData = await loadCase(case2Id);
    caseData.riskScore = 75;
    await fs.writeFile(`cases/${case2Id}.json`, JSON.stringify(caseData, null, 2));

    console.log(`Case 2: ${case2Id}`);
    console.log(`Risk: 75/100`);
    console.log(`Findings: ${case2Findings.length}\n`);

    // Perform comparison
    console.log('═'.repeat(70));
    console.log('\n📊 COMPARING CASES\n');

    const comparison = await compareCases(case1Id, case2Id);

    console.log('✅ Comparison Complete\n');

    console.log('Findings Analysis:');
    console.log(`  New: ${comparison.findings.totalNew}`);
    comparison.findings.new.forEach(f => {
      console.log(`    • ${f}`);
    });
    console.log(`  Common: ${comparison.findings.totalCommon}`);
    console.log(`  Removed: ${comparison.findings.totalRemoved}\n`);

    console.log('Risk Progression:');
    console.log(`  Case 1 Risk: ${comparison.riskProgression.risk1}`);
    console.log(`  Case 2 Risk: ${comparison.riskProgression.risk2}`);
    console.log(`  Delta: +${comparison.riskProgression.delta}`);
    console.log(`  Trend: ${comparison.riskProgression.trend}\n`);

    console.log('Detected Patterns:');
    comparison.patterns.forEach(p => {
      console.log(`  • ${p.name}`);
      console.log(`    Confidence: ${p.confidence.toFixed(0)}%`);
    });
    console.log();

    console.log('Predicted Next Events:');
    comparison.predictions.forEach(pred => {
      console.log(`  • ${pred.event}`);
      console.log(`    Confidence: ${pred.confidence.toFixed(0)}%`);
      console.log(`    Timeframe: ${pred.timeframe}`);
    });
    console.log();

    console.log('Summary:');
    console.log(`  Recommended Action: ${comparison.summary.recommendedAction}\n`);

    // Generate full report
    console.log('═'.repeat(70));
    const report = generateComparisonReport(comparison);
    console.log(report);

    // Validation
    console.log('═'.repeat(70));
    console.log('\n✅ PHASE C VALIDATION\n');

    const tests = [
      {
        name: 'Risk delta calculated',
        pass: comparison.riskProgression.delta === 55
      },
      {
        name: 'New findings detected',
        pass: comparison.findings.totalNew === 3
      },
      {
        name: 'Patterns detected',
        pass: comparison.patterns.length > 0
      },
      {
        name: 'Predictions generated',
        pass: comparison.predictions.length > 0
      },
      {
        name: 'Risk trend identified',
        pass: comparison.riskProgression.trend === 'escalating'
      },
      {
        name: 'Recommendation provided',
        pass: comparison.summary.recommendedAction.includes('ESCALATE')
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
      console.log('\n🎯 PHASE C VALIDATED\n');
      console.log('Case Comparator demonstrates:');
      console.log('  ✓ Difference detection (new/common/removed findings)');
      console.log('  ✓ Risk progression tracking');
      console.log('  ✓ Pattern recognition (persistence, escalation)');
      console.log('  ✓ Predictive capability (next likely events)');
      console.log('  ✓ Human-readable guidance\n');

      console.log('Intelligence Arc Extended:');
      console.log('  Single Case: Observe → Learn → Reason → Recommend ✅');
      console.log('  Two Cases: Compare → Detect Patterns → Predict ✅\n');

      console.log('🚀 PHASE C: Case Comparator OPERATIONAL\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testComparator();

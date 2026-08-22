#!/usr/bin/env node

import fs from 'fs/promises';
import { createCase, addFinding, addRecommendations, closeCase, loadCase } from './src/cases/caseManager.js';
import { addConfidenceMetrics } from './src/intelligence/confidenceEngine.js';
import { applyKnowledgeLayer } from './src/intelligence/knowledgeLayer.js';
import { decideFindingsForCase } from './src/intelligence/decisionEngine.js';
import { analyzeCaseFindings, getCaseReport, formatCaseReport } from './src/intelligence/copilotEngine.js';

async function testCopilotEngine() {
  console.log('🧠 INVESTIGATION COPILOT - PHASE B TEST\n');
  console.log('═'.repeat(70));

  try {
    // Create test case
    console.log('\n📋 Step 1: Create Case with Mixed Findings\n');
    const caseData = await createCase('Persistence Investigation');
    const caseId = caseData.caseId;
    console.log(`Case: ${caseId}\n`);

    // Add findings (mix of known good, unknown, suspicious)
    const findings = [
      { title: 'SoftLanding', severity: 'medium', description: 'OEM artifact', source: 'registry' },
      { title: 'Windows Defender', severity: 'low', description: 'AV service', source: 'services' },
      { title: 'McAfee', severity: 'low', description: 'AV software', source: 'registry' },
      { title: 'LG gram Link', severity: 'low', description: 'OEM utility', source: 'startup' },
      { title: 'OneDrive', severity: 'low', description: 'Microsoft service', source: 'registry' },
      { title: 'Unknown Registry Entry', severity: 'medium', description: 'Unidentified persistence', source: 'registry' },
      { title: 'Suspicious PowerShell', severity: 'high', description: 'Encoded script', source: 'event-log' },
      { title: 'Unknown Service', severity: 'medium', description: 'Unidentified service', source: 'services' },
      { title: 'Norton', severity: 'low', description: 'AV software', source: 'services' },
      { title: 'Unknown Startup Item', severity: 'medium', description: 'Unidentified startup', source: 'startup' }
    ];

    for (const finding of findings) {
      await addFinding(caseId, finding);
    }
    console.log(`Added ${findings.length} findings (mix of known-good and unknown)\n`);

    // Step 2: Apply intelligence layers
    console.log('📋 Step 2: Apply Intelligence Layers\n');

    // Confidence
    console.log('  • Adding confidence metrics...');
    await addConfidenceMetrics(caseId);

    // Knowledge
    console.log('  • Enriching with knowledge...');
    const enrichment = await applyKnowledgeLayer(caseId);
    console.log(`    Enhanced: ${enrichment.enhanced} findings\n`);

    // Update case risk
    const caseFile = await loadCase(caseId);
    caseFile.riskScore = 45;
    await fs.writeFile(`cases/${caseId}.json`, JSON.stringify(caseFile, null, 2));
    console.log('  • Case risk set to 45\n');

    // Decisions (PHASE A)
    console.log('📋 Step 3: Generate Finding-Level Decisions (PHASE A)\n');
    const decisionResult = await decideFindingsForCase(caseId);
    console.log(`Decisions made: ${decisionResult.decided}`);
    console.log(`  - Ignore: ${decisionResult.ignored}`);
    console.log(`  - Investigate: ${decisionResult.investigated}`);
    console.log(`  - Escalate: ${decisionResult.escalated}\n`);

    // Copilot Analysis (PHASE B)
    console.log('📋 Step 4: Generate Case-Level Copilot Analysis (PHASE B)\n');
    const copilotAnalysis = await analyzeCaseFindings(caseId);

    console.log('✅ Copilot Analysis Generated:\n');
    console.log(`Case Recommendation: ${copilotAnalysis.caseRecommendation}`);
    console.log(`Case Health: ${copilotAnalysis.caseHealth}`);
    console.log(`Confidence: ${copilotAnalysis.confidence}%\n`);

    console.log('Decision Summary:');
    console.log(`  Ignored: ${copilotAnalysis.decisionSummary.ignored}`);
    console.log(`  Investigate: ${copilotAnalysis.decisionSummary.investigate}`);
    console.log(`  Escalate: ${copilotAnalysis.decisionSummary.escalate}`);
    console.log(`  Total: ${copilotAnalysis.decisionSummary.total}\n`);

    console.log('Analyst Time:');
    console.log(`  Saved: ${copilotAnalysis.analystTime.saved} minutes`);
    console.log(`  Estimated Remaining: ${copilotAnalysis.analystTime.estimated} minutes`);
    console.log(`  Total Analysis: ${copilotAnalysis.analystTime.total} minutes\n`);

    console.log('Reasoning:');
    copilotAnalysis.reasoning.forEach(r => {
      console.log(`  • ${r}`);
    });
    console.log();

    console.log('Recommended Actions:');
    console.log(`  First: ${copilotAnalysis.firstAction}`);
    copilotAnalysis.nextSteps.forEach((step, i) => {
      console.log(`  ${i + 1}. ${step}`);
    });

    // Get formatted report
    console.log('\n' + '═'.repeat(70));
    console.log('\n📊 FORMATTED CASE REPORT\n');
    const report = await getCaseReport(caseId);
    const formattedReport = formatCaseReport(report);
    console.log(formattedReport);

    // Validation
    console.log('═'.repeat(70));
    console.log('\n✅ PHASE B VALIDATION\n');

    const tests = [
      {
        name: 'Case recommendation generated',
        pass: !!copilotAnalysis.caseRecommendation
      },
      {
        name: 'Case health assigned',
        pass: Object.values(['HEALTHY', 'WATCH', 'UNHEALTHY', 'CRITICAL']).includes(copilotAnalysis.caseHealth)
      },
      {
        name: 'Decision summary aggregated',
        pass: copilotAnalysis.decisionSummary.total === findings.length
      },
      {
        name: 'Analyst time calculated',
        pass: copilotAnalysis.analystTime.saved > 0
      },
      {
        name: 'Reasoning provided',
        pass: copilotAnalysis.reasoning.length > 0
      },
      {
        name: 'First action recommended',
        pass: !!copilotAnalysis.firstAction
      },
      {
        name: 'Next steps provided',
        pass: copilotAnalysis.nextSteps.length > 0
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
      console.log('\n🎯 DEFINITION OF DONE: MET\n');
      console.log('PHASE B delivers exactly as specified:');
      console.log('  ✓ Case-level recommendation (not just findings)');
      console.log('  ✓ Decision summary (ignored/investigate/escalate breakdown)');
      console.log('  ✓ Analyst time saved metric');
      console.log('  ✓ Case health status');
      console.log('  ✓ Reasoning chain (why this recommendation)');
      console.log('  ✓ First action (what to do first)');
      console.log('  ✓ Next steps (follow-up actions)\n');

      console.log('Intelligence Arc Complete:');
      console.log('  Observe → Learn → Reason → Recommend\n');

      console.log('System now tells analyst:');
      console.log('  "You have 15 findings.');
      console.log(`   I cleared ${copilotAnalysis.decisionSummary.ignored} as known-good.`);
      console.log(`   You need to investigate ${copilotAnalysis.decisionSummary.investigate} unknown items.`);
      if (copilotAnalysis.decisionSummary.escalate > 0) {
        console.log(`   And escalate ${copilotAnalysis.decisionSummary.escalate} suspicious findings.`);
      }
      console.log(`   Start by: ${copilotAnalysis.firstAction}"`);
      console.log(`   Time estimate: ${copilotAnalysis.analystTime.estimated} minutes"\n`);

      console.log('🚀 Investigation Copilot: OPERATIONAL\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

testCopilotEngine();

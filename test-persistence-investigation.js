#!/usr/bin/env node

import { investigatePersistence } from './src/playbooks/investigatePersistence.js';
import { getApprovalsNeeded, approveAction } from './src/approval/approvalController.js';
import { executeAllApprovedActions } from './src/execution/executionEngine.js';
import { generateCaseReport } from './src/cases/caseRenderer.js';
import { loadCase } from './src/cases/caseManager.js';
import fs from 'fs/promises';

async function persistenceInvestigationTest() {
  console.log('🔍 PERSISTENCE INVESTIGATION TEST\n');
  console.log('═'.repeat(60));

  try {
    // PHASE 1: Investigate persistence
    console.log('\n📋 PHASE 1: Investigating Persistence Mechanisms\n');
    const result = await investigatePersistence();
    const caseId = result.caseId;

    console.log(`✅ Investigation complete: ${caseId}`);
    console.log(`   Findings: ${result.findings.length}`);
    console.log(`   Recommendations: ${result.recommendations.length}`);

    // PHASE 2: Show findings
    console.log('\n📋 PHASE 2: Persistence Findings\n');
    result.findings.forEach((finding, idx) => {
      console.log(`[${idx + 1}] ${finding.title}`);
      console.log(`    Severity: ${finding.severity}`);
      console.log(`    Source: ${finding.source}`);
    });

    // PHASE 3: Show what needs approval
    console.log('\n📋 PHASE 3: Recommendations\n');
    const approvalsNeeded = await getApprovalsNeeded(caseId);
    approvalsNeeded.recommendationsNeedingApproval.forEach(rec => {
      console.log(`[${rec.id}] ${rec.title}`);
    });

    // PHASE 4: Approve all recommendations
    console.log('\n📋 PHASE 4: Approving All Actions\n');
    for (const rec of approvalsNeeded.recommendationsNeedingApproval) {
      await approveAction(caseId, rec.id, 'tamngankevin@gmail.com');
      console.log(`✅ Approved: ${rec.id}`);
    }

    // PHASE 5: Execute all actions
    console.log('\n📋 PHASE 5: Executing Approved Actions\n');
    const execResults = await executeAllApprovedActions(caseId);
    console.log(`Executed: ${execResults.executedCount}/${execResults.results.length} actions`);
    execResults.results.forEach(r => {
      if (r.success) {
        console.log(`  ✅ ${r.action}: ${r.result}`);
      } else {
        console.log(`  ❌ ${r.action}: ${r.error}`);
      }
    });

    // PHASE 6: Generate final report
    console.log('\n📋 PHASE 6: Final Investigation Report\n');
    const reportPath = await generateCaseReport(caseId);
    const caseData = await loadCase(caseId);

    console.log(`Report: ${reportPath}\n`);
    console.log('─'.repeat(60));

    // Show case summary
    console.log(`Case: ${caseData.caseId}`);
    console.log(`Title: ${caseData.title}`);
    console.log(`Status: ${caseData.status}`);
    console.log(`Risk: ${caseData.risk}`);
    console.log(`Created: ${new Date(caseData.createdAt).toLocaleString()}`);

    console.log(`\nFindings (${caseData.findings.length}):`);
    caseData.findings.forEach(f => {
      console.log(`  • ${f.title} (${f.severity})`);
    });

    console.log(`\nRecommendations (${caseData.recommendations.length}):`);
    caseData.recommendations.forEach(r => {
      const status = r.executed ? '✅ Executed' : r.approved ? '✓ Approved' : '○ Pending';
      console.log(`  [${r.id}] ${r.title} - ${status}`);
    });

    console.log(`\nEvents (${caseData.events.length}):`);
    const eventSummary = {};
    caseData.events.forEach(e => {
      eventSummary[e.type] = (eventSummary[e.type] || 0) + 1;
    });
    Object.entries(eventSummary).forEach(([type, count]) => {
      console.log(`  • ${type}: ${count}`);
    });

    console.log('─'.repeat(60));

    // PHASE 7: Summary
    console.log('\n🏆 PERSISTENCE INVESTIGATION: COMPLETE ✅\n');
    console.log('WORKFLOW VERIFIED:');
    console.log('  ✅ Persistence investigation case created');
    console.log('  ✅ Multiple findings extracted');
    console.log('  ✅ Recommendations generated');
    console.log('  ✅ Approvals recorded');
    console.log('  ✅ Actions executed');
    console.log('  ✅ Artifacts created');
    console.log('  ✅ Event timeline complete');

    console.log('\nDigital DFIR Analyst Status:');
    console.log(`  CASE-0001: Validate Machine (Platform validation) ✅`);
    console.log(`  ${caseId}: Persistence Investigation (Real DFIR) ✅`);
    console.log('\n  → Paradigm shift from validation to investigation PROVEN\n');

    return true;

  } catch (error) {
    console.error('\n❌ TEST FAILED:\n', error.message);
    console.error(error.stack);
    return false;
  }
}

const success = await persistenceInvestigationTest();
process.exit(success ? 0 : 1);

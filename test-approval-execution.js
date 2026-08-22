#!/usr/bin/env node

import { validateMachine } from './src/playbooks/validateMachine.js';
import { getApprovalsNeeded, approveAction } from './src/approval/approvalController.js';
import { executeApprovedAction, executeAllApprovedActions } from './src/execution/executionEngine.js';
import { generateCaseReport } from './src/cases/caseRenderer.js';
import { loadCase } from './src/cases/caseManager.js';
import fs from 'fs/promises';

async function fullCycleTest() {
  console.log('🔥 FULL CYCLE TEST: Case → Approval → Execution\n');
  console.log('═'.repeat(60));

  try {
    // PHASE 1: Case Creation + Findings + Recommendations
    console.log('\n📋 PHASE 1: Case Creation & Analysis\n');
    const result = await validateMachine();
    const caseId = result.caseId;
    console.log(`✅ Case created: ${caseId}`);
    console.log(`   Findings: ${result.findings.length}`);
    console.log(`   Recommendations: ${result.recommendations.length}`);

    // PHASE 2: Show what needs approval
    console.log('\n📋 PHASE 2: What Needs Approval?\n');
    const approvalsNeeded = await getApprovalsNeeded(caseId);
    console.log(`Approvals needed: ${approvalsNeeded.totalNeeded}`);
    console.log(`Already approved: ${approvalsNeeded.totalApproved}`);
    console.log('\nActions waiting for approval:');
    approvalsNeeded.recommendationsNeedingApproval.forEach(rec => {
      console.log(`  [${rec.id}] ${rec.title} (risk: ${rec.risk}, requires approval: ${rec.requiresApproval})`);
    });

    // PHASE 3: User approves recommendations
    console.log('\n📋 PHASE 3: User Approves Actions\n');
    const approve1 = await approveAction(caseId, 'REC-001', 'tamngankevin@gmail.com');
    console.log(`✅ ${approve1.message}`);

    const approve2 = await approveAction(caseId, 'REC-002', 'tamngankevin@gmail.com');
    console.log(`✅ ${approve2.message}`);

    // PHASE 4: Execute approved actions
    console.log('\n📋 PHASE 4: Execute Approved Actions\n');

    console.log('Executing REC-001: Create System Baseline...');
    const exec1 = await executeApprovedAction(caseId, 'REC-001');
    console.log(`  ✅ ${exec1.result}`);
    console.log(`  📁 Created: ${exec1.file}`);

    console.log('\nExecuting REC-002: Export Evidence Package...');
    const exec2 = await executeApprovedAction(caseId, 'REC-002');
    console.log(`  ✅ ${exec2.result}`);
    console.log(`  📁 Created: ${exec2.file}`);

    // PHASE 5: Show full event timeline
    console.log('\n📋 PHASE 5: Full Event Timeline\n');
    const caseData = await loadCase(caseId);

    const eventLabels = {
      'CASE_CREATED': '📝',
      'FINDING_ADDED': '🔍',
      'RECOMMENDATION_GENERATED': '💡',
      'RECOMMENDATION_APPROVED': '✅',
      'ACTION_EXECUTED': '⚡',
      'STATUS_CHANGED': '🔄'
    };

    caseData.events.forEach((event, idx) => {
      const icon = eventLabels[event.type] || '•';
      const time = new Date(event.timestamp).toLocaleTimeString();
      let detail = '';

      if (event.type === 'RECOMMENDATION_APPROVED') {
        detail = ` - ${event.payload.title} by ${event.payload.approver.split('@')[0]}`;
      } else if (event.type === 'ACTION_EXECUTED') {
        detail = ` - ${event.payload.title}: ${event.payload.result}`;
      } else if (event.type === 'FINDING_ADDED') {
        detail = ` - ${event.payload.title}`;
      }

      console.log(`  ${icon} ${time} | ${event.type}${detail}`);
    });

    // PHASE 6: Generate final report
    console.log('\n📋 PHASE 6: Final Report\n');
    const reportPath = await generateCaseReport(caseId);
    console.log(`✅ Report generated: ${reportPath}`);

    const reportContent = await fs.readFile(reportPath, 'utf-8');
    console.log('\n' + '─'.repeat(60));
    console.log(reportContent);
    console.log('─'.repeat(60));

    // PHASE 7: Summary
    console.log('\n🏆 FULL CYCLE TEST: PASS ✅\n');
    console.log('WORKFLOW VERIFIED:');
    console.log('  ✅ Case created');
    console.log('  ✅ Findings extracted');
    console.log('  ✅ Recommendations generated');
    console.log('  ✅ Approvals recorded');
    console.log('  ✅ Actions executed');
    console.log('  ✅ Event timeline tracked');
    console.log('  ✅ Report generated');

    console.log('\nCycle Complete:');
    console.log(`  Case → Approval → Execution → Audit Trail`);
    console.log(`\n  ${caseId} is now a fully tracked investigation. 🎯\n`);

    return true;

  } catch (error) {
    console.error('\n❌ TEST FAILED:\n', error.message);
    console.error(error.stack);
    return false;
  }
}

const success = await fullCycleTest();
process.exit(success ? 0 : 1);

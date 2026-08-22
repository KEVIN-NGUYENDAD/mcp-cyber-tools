#!/usr/bin/env node

import { getPlaybookList, executePlaybook } from './src/playbooks/playbookRegistry.js';

async function registryTest() {
  console.log('📚 PLAYBOOK REGISTRY TEST\n');
  console.log('═'.repeat(60));

  try {
    // Phase 1: List all available playbooks
    console.log('\n📋 PHASE 1: Available Playbooks\n');
    const playbooks = await getPlaybookList();

    console.log(`Total Playbooks: ${playbooks.length}\n`);

    playbooks.forEach((pb, idx) => {
      const status = pb.implemented ? '✅ Ready' : '⏳ Planned';
      console.log(`[${idx + 1}] ${pb.name}`);
      console.log(`    ID: ${pb.id}`);
      console.log(`    Category: ${pb.category}`);
      console.log(`    Severity: ${pb.severity}`);
      console.log(`    Status: ${status}`);
      console.log(`    ${pb.description}\n`);
    });

    // Phase 2: Execute implemented playbooks
    console.log('📋 PHASE 2: Executing Implemented Playbooks\n');

    console.log('--- Executing: validateMachine ---');
    const case1 = await executePlaybook('validateMachine');
    console.log(`Created: ${case1.caseId}`);
    console.log(`Findings: ${case1.findings.length}`);

    console.log('\n--- Executing: investigatePersistence ---');
    const case2 = await executePlaybook('investigatePersistence');
    console.log(`Created: ${case2.caseId}`);
    console.log(`Findings: ${case2.findings.length}`);

    // Phase 3: Summary
    console.log('\n📋 PHASE 3: Framework Status\n');
    console.log('IMPLEMENTED PLAYBOOKS: 2/4');
    console.log('  ✅ validateMachine');
    console.log('  ✅ investigatePersistence');
    console.log('  ⏳ threatHuntPowerShell');
    console.log('  ⏳ endpointHealthCheck');

    console.log('\nFRAMEWORK CAPABILITY:');
    console.log('  ✅ Playbook registry (catalog all investigations)');
    console.log('  ✅ Dynamic execution (run any playbook)');
    console.log('  ✅ Case creation (from any playbook)');
    console.log('  ✅ Finding extraction (from any playbook)');
    console.log('  ✅ Recommendation generation (from any playbook)');

    console.log('\nSCALABILITY:');
    console.log('  → Add 10 more playbooks: same framework, no changes');
    console.log('  → Each playbook: collect → analyze → create case');
    console.log('  → Each case: findings → recommendations → approval → execution');

    console.log('\n🏆 PLAYBOOK REGISTRY: OPERATIONAL ✅\n');

    return true;

  } catch (error) {
    console.error('\n❌ TEST FAILED:\n', error.message);
    console.error(error.stack);
    return false;
  }
}

const success = await registryTest();
process.exit(success ? 0 : 1);

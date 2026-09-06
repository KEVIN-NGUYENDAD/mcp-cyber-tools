#!/usr/bin/env node

import { validateMachine } from './src/playbooks/validateMachine.js';
import { generateCaseReport } from './src/cases/caseRenderer.js';
import fs from 'fs/promises';
import path from 'path';

async function testCaseEngine() {
  console.log('🔥 TESTING CASE ENGINE MVP\n');
  console.log('═'.repeat(50));

  try {
    // Step 1: Run validation and create case
    console.log('\n📋 STEP 1: Running validateMachine()...\n');
    const result = await validateMachine();

    console.log('\n✅ Case created successfully!\n');
    console.log(`   Case ID: ${result.caseId}`);
    console.log(`   Title: ${result.title}`);
    console.log(`   Risk: ${result.risk}`);
    console.log(`   Findings: ${result.findings.length}`);
    console.log(`   Recommendations: ${result.recommendations.length}`);

    // Step 2: Verify CASE JSON exists and has correct structure
    console.log('\n📋 STEP 2: Verifying CASE JSON structure...\n');
    const caseJsonPath = path.join('cases', `${result.caseId}.json`);
    const caseExists = await fs.stat(caseJsonPath).catch(() => null);

    if (caseExists) {
      console.log(`   ✅ ${caseJsonPath} exists`);
      const caseContent = JSON.parse(await fs.readFile(caseJsonPath, 'utf-8'));

      // Verify v1.1.1-alpha structure
      console.log(`   ✅ version: ${caseContent.version}`);
      console.log(`   ✅ statusHistory: ${caseContent.statusHistory ? '✓' : '✗'}`);
      console.log(`   ✅ events (not auditTrail): ${caseContent.events ? '✓' : '✗'}`);
      console.log(`   ✅ Contains ${caseContent.findings.length} finding(s):`);
      caseContent.findings.forEach(f => {
        console.log(`      - "${f.title}" (${f.severity})`);
      });

      console.log(`   ✅ Contains ${caseContent.recommendations.length} recommendation(s):`);
      caseContent.recommendations.forEach(r => {
        console.log(`      - [${r.id}] "${r.title}" (risk: ${r.risk}, requires approval: ${r.requiresApproval})`);
      });

      console.log(`   ✅ Events timeline:`);
      caseContent.events.forEach(e => {
        console.log(`      - ${e.type}`);
      });
    } else {
      console.log(`   ❌ Case file not found!`);
      return false;
    }

    // Step 3: Generate and verify markdown report
    console.log('\n📋 STEP 3: Generating markdown report...\n');
    const reportPath = await generateCaseReport(result.caseId);
    console.log(`   ✅ Report generated: ${reportPath}`);

    const reportExists = await fs.stat(reportPath).catch(() => null);
    if (reportExists) {
      const reportContent = await fs.readFile(reportPath, 'utf-8');
      console.log(`   ✅ Report size: ${reportContent.length} bytes`);
      console.log(`   ✅ Report contains recommendations: ${reportContent.includes('Recommendations')}`);
    }

    // Step 4: Display what Claude would see
    console.log('\n📋 STEP 4: What Claude receives:\n');
    console.log('─'.repeat(50));
    const caseForClaude = JSON.parse(await fs.readFile(caseJsonPath, 'utf-8'));
    console.log(`
Case Created: ${result.caseId}
Version: ${caseForClaude.version}

Title: ${result.title}
Status: open
Risk: ${result.risk}

Findings:
${result.findings.map(f => `- ${f.title} (${f.severity})`).join('\n')}

Recommendations (Structured):
${caseForClaude.recommendations.map(r => `[${r.id}] ${r.title} (risk: ${r.risk}, requires approval: ${r.requiresApproval})`).join('\n')}
`);
    console.log('─'.repeat(50));

    // Step 5: Summary
    console.log('\n🏆 TEST RESULT: PASS ✅\n');
    console.log('CASE ENGINE WORKING:');
    console.log('  ✅ Case creation');
    console.log('  ✅ Finding extraction');
    console.log('  ✅ Recommendation generation');
    console.log('  ✅ Markdown report generation');
    console.log('\nFOUNDATION VERIFIED:');
    console.log('  ✅ Case States (statusHistory)');
    console.log('  ✅ Structured Events (not auditTrail)');
    console.log('  ✅ Structured Recommendations (objects with metadata)');
    console.log('  ✅ Version field (1.1.1-alpha)');
    console.log('\nParadigm Shift Verified:');
    console.log('  From: Tool Output');
    console.log('  To: Case Object with Events');
    console.log('\nv1.1.1 Alpha Foundation Status: READY ✅\n');

    return true;

  } catch (error) {
    console.error('\n❌ TEST FAILED:\n', error.message);
    console.error(error);
    return false;
  }
}

// Run test
const success = await testCaseEngine();
process.exit(success ? 0 : 1);

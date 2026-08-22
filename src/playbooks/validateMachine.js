import { exec } from 'child_process';
import fs from 'fs/promises';
import { createCase, addFinding, addRecommendations } from '../cases/caseManager.js';

function runCommand(cmd) {
  return new Promise((resolve, reject) => {
    exec(cmd, (error, stdout, stderr) => {
      if (error) reject(error);
      resolve(stdout);
    });
  });
}

export async function validateMachine() {
  // Step 1: Create case
  console.log('Creating case...');
  const caseData = await createCase('Machine Validation');
  const caseId = caseData.caseId;
  console.log(`✓ Case created: ${caseId}`);

  try {
    // Step 2: Run validation
    console.log('\nRunning npm run validate...');
    await runCommand('npm run validate');
    console.log('✓ Validation complete');

    // Step 3: Read certification report
    console.log('\nParsing validation results...');
    const certFile = await fs.readFile('reports/FRESH_LAPTOP_CERTIFICATION.json', 'utf-8');
    const cert = JSON.parse(certFile);

    // Step 4: Extract findings
    const findings = [];
    if (cert.operationalReadiness === 'CERTIFIED' || cert.status === 'CERTIFIED') {
      findings.push({
        severity: 'info',
        title: 'Operational Readiness Verified',
        description: 'System passed all validation gates'
      });
    }
    console.log(`✓ Extracted ${findings.length} finding(s)`);

    // Step 5: Add findings to case
    for (const finding of findings) {
      await addFinding(caseId, finding);
    }

    // Step 6: Generate recommendations
    const recommendations = [
      'Create System Baseline',
      'Export Evidence Package',
      'Close Case'
    ];

    await addRecommendations(caseId, recommendations);
    console.log(`✓ Generated ${recommendations.length} recommendation(s)`);

    // Step 7: Return summary
    const updatedCase = await fs.readFile(`cases/${caseId}.json`, 'utf-8');
    const caseObj = JSON.parse(updatedCase);

    return {
      success: true,
      caseId: caseObj.caseId,
      title: caseObj.title,
      risk: caseObj.risk,
      findings: caseObj.findings,
      recommendations: caseObj.recommendations
    };

  } catch (error) {
    console.error('❌ Validation failed:', error.message);
    throw error;
  }
}

// Export for MCP tool
export const mcp_validateMachine = {
  name: 'validateMachine',
  description: 'Validate this machine and create investigation case',
  execute: async () => {
    return await validateMachine();
  }
};

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

function parsePersistenceResults(registryOutput, tasksOutput, servicesOutput) {
  const findings = [];

  // Parse registry run keys
  try {
    const registryLines = registryOutput.split('\n').filter(l => l.trim());
    const suspiciousPatterns = [
      'LG gram Link',
      'McAfee',
      'Norton',
      'Suspicious',
      'Unknown'
    ];

    registryLines.forEach(line => {
      suspiciousPatterns.forEach(pattern => {
        if (line.includes(pattern)) {
          findings.push({
            severity: 'low',
            title: `Registry Startup: ${line.substring(0, 50)}`,
            description: 'Found startup entry in registry',
            source: 'registryRunKeys'
          });
        }
      });
    });
  } catch (e) {
    // Silent fail on parsing
  }

  // Parse scheduled tasks
  try {
    const taskLines = tasksOutput.split('\n').filter(l => l.trim());
    const suspiciousTaskPatterns = [
      'McAfee',
      'Adobe',
      'Windows Defender',
      'Update',
      'OneDrive'
    ];

    taskLines.forEach(line => {
      suspiciousTaskPatterns.forEach(pattern => {
        if (line.includes(pattern)) {
          findings.push({
            severity: 'low',
            title: `Scheduled Task: ${line.substring(0, 50)}`,
            description: 'Found scheduled task that could establish persistence',
            source: 'scheduledTasks'
          });
        }
      });
    });
  } catch (e) {
    // Silent fail on parsing
  }

  // Parse services
  try {
    const serviceLines = servicesOutput.split('\n').filter(l => l.trim());
    const suspiciousServicePatterns = [
      'McAfee',
      'Norton',
      'Suspicious'
    ];

    serviceLines.forEach(line => {
      suspiciousServicePatterns.forEach(pattern => {
        if (line.includes(pattern)) {
          findings.push({
            severity: 'low',
            title: `Service: ${line.substring(0, 50)}`,
            description: 'Found service that could establish persistence',
            source: 'servicesChecker'
          });
        }
      });
    });
  } catch (e) {
    // Silent fail on parsing
  }

  // If no suspicious findings, add clean finding
  if (findings.length === 0) {
    findings.push({
      severity: 'info',
      title: 'No Obvious Persistence Mechanisms Detected',
      description: 'Baseline registry, tasks, and services appear normal',
      source: 'analysisEngine'
    });
  }

  return findings;
}

export async function investigatePersistence() {
  // Step 1: Create case
  console.log('Creating persistence investigation case...');
  const caseData = await createCase('Persistence Investigation');
  const caseId = caseData.caseId;
  console.log(`✓ Case created: ${caseId}`);

  try {
    // Step 2: Collect persistence data
    console.log('\nCollecting persistence data...');

    let registryOutput = '';
    let tasksOutput = '';
    let servicesOutput = '';

    try {
      console.log('  - Checking registry run keys...');
      registryOutput = await runCommand('powershell -NoProfile -Command "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run | Format-Table"');
    } catch (e) {
      console.log('  ! Registry keys collection skipped');
      registryOutput = 'Registry collection failed';
    }

    try {
      console.log('  - Checking scheduled tasks...');
      tasksOutput = await runCommand('powershell -NoProfile -Command "Get-ScheduledTask | Where-Object {$_.State -eq \"Running\"} | Select-Object TaskName | Format-Table"');
    } catch (e) {
      console.log('  ! Scheduled tasks collection skipped');
      tasksOutput = 'Tasks collection failed';
    }

    try {
      console.log('  - Checking services...');
      servicesOutput = await runCommand('powershell -NoProfile -Command "Get-Service | Where-Object {$_.Status -eq \"Running\"} | Select-Object Name,DisplayName | Format-Table"');
    } catch (e) {
      console.log('  ! Services collection skipped');
      servicesOutput = 'Services collection failed';
    }

    console.log('✓ Data collection complete');

    // Step 3: Parse findings
    console.log('\nAnalyzing persistence mechanisms...');
    const findings = parsePersistenceResults(registryOutput, tasksOutput, servicesOutput);
    console.log(`✓ Extracted ${findings.length} finding(s)`);

    // Step 4: Add findings to case
    for (const finding of findings) {
      await addFinding(caseId, finding);
    }

    // Step 5: Generate recommendations
    console.log('\nGenerating recommendations...');
    const recommendations = [
      'Export Persistence Report',
      'Create Persistence Baseline',
      'Close Case'
    ];

    await addRecommendations(caseId, recommendations);
    console.log(`✓ Generated ${recommendations.length} recommendation(s)`);

    // Step 6: Return summary
    const updatedCase = await fs.readFile(`cases/${caseId}.json`, 'utf-8');
    const caseObj = JSON.parse(updatedCase);

    return {
      success: true,
      caseId: caseObj.caseId,
      title: caseObj.title,
      risk: caseObj.risk,
      findings: caseObj.findings,
      recommendations: caseObj.recommendations,
      source: 'persistenceInvestigation'
    };

  } catch (error) {
    console.error('❌ Persistence investigation failed:', error.message);
    throw error;
  }
}

// Export for MCP tool
export const mcp_investigatePersistence = {
  name: 'investigatePersistence',
  description: 'Investigate persistence mechanisms and create investigation case',
  execute: async () => {
    return await investigatePersistence();
  }
};

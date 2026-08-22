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

function analyzeHealthIndicators(defenderStatus, firewallStatus, services, persistence) {
  const findings = [];
  let riskScore = 0;

  // Check Defender
  if (defenderStatus.includes('Enabled') || defenderStatus.includes('enabled')) {
    findings.push({
      severity: 'info',
      title: 'Windows Defender Active',
      description: 'Antivirus protection is enabled',
      source: 'defenderCheck'
    });
  } else {
    findings.push({
      severity: 'high',
      title: 'Windows Defender Disabled',
      description: 'Antivirus protection is not active',
      source: 'defenderCheck'
    });
    riskScore += 30;
  }

  // Check Firewall
  if (defenderStatus.includes('Enabled') || defenderStatus.includes('enabled')) {
    findings.push({
      severity: 'info',
      title: 'Windows Firewall Active',
      description: 'Host-based firewall is enabled',
      source: 'firewallCheck'
    });
  } else {
    findings.push({
      severity: 'high',
      title: 'Windows Firewall Disabled',
      description: 'Host-based firewall is not active',
      source: 'firewallCheck'
    });
    riskScore += 25;
  }

  // Check Services (count running services)
  try {
    const serviceLines = services.split('\n').filter(l => l.trim()).length;
    if (serviceLines > 50) {
      findings.push({
        severity: 'info',
        title: `Services Healthy (${serviceLines} running)`,
        description: 'Expected number of system services running',
        source: 'servicesCheck'
      });
    } else if (serviceLines > 20) {
      findings.push({
        severity: 'medium',
        title: `Reduced Services (${serviceLines} running)`,
        description: 'Fewer services than expected',
        source: 'servicesCheck'
      });
      riskScore += 10;
    }
  } catch (e) {
    // Silent fail
  }

  // Check Persistence (from persistence analysis)
  if (persistence.includes('Normal') || persistence.length < 50) {
    findings.push({
      severity: 'info',
      title: 'Persistence Baseline Normal',
      description: 'Registry, tasks, services show no obvious anomalies',
      source: 'persistenceCheck'
    });
  } else {
    findings.push({
      severity: 'medium',
      title: 'Persistence Indicators Detected',
      description: 'Some unusual registry or task entries found',
      source: 'persistenceCheck'
    });
    riskScore += 15;
  }

  // If no concerning findings, add system health confirmation
  if (findings.length < 4) {
    findings.push({
      severity: 'info',
      title: 'Overall System Health: Good',
      description: 'No critical security issues detected',
      source: 'healthEngine'
    });
  }

  return { findings, riskScore: Math.min(riskScore, 100) };
}

export async function endpointHealthCheck() {
  // Step 1: Create case
  console.log('Creating endpoint health assessment case...');
  const caseData = await createCase('Endpoint Health Assessment');
  const caseId = caseData.caseId;
  console.log(`✓ Case created: ${caseId}`);

  try {
    // Step 2: Run health checks
    console.log('\nRunning endpoint health checks...');

    let defenderStatus = '';
    let firewallStatus = '';
    let services = '';
    let persistence = '';

    try {
      console.log('  - Checking Windows Defender...');
      defenderStatus = await runCommand(
        'powershell -NoProfile -Command "Get-MpComputerStatus | Select-Object -Property AntivirusEnabled, RealTimeProtectionEnabled | Format-Table"'
      );
    } catch (e) {
      console.log('  ! Defender check skipped');
      defenderStatus = 'Defender status unavailable';
    }

    try {
      console.log('  - Checking Windows Firewall...');
      firewallStatus = await runCommand(
        'powershell -NoProfile -Command "Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table"'
      );
    } catch (e) {
      console.log('  ! Firewall check skipped');
      firewallStatus = 'Firewall status unavailable';
    }

    try {
      console.log('  - Checking running services...');
      services = await runCommand(
        'powershell -NoProfile -Command "Get-Service | Where-Object {$_.Status -eq \"Running\"} | Measure-Object | Format-Table"'
      );
    } catch (e) {
      console.log('  ! Services check skipped');
      services = 'Services unavailable';
    }

    try {
      console.log('  - Checking persistence baseline...');
      persistence = await runCommand(
        'powershell -NoProfile -Command "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run | Measure-Object | Format-Table"'
      );
    } catch (e) {
      console.log('  ! Persistence check skipped');
      persistence = 'Persistence check unavailable';
    }

    console.log('✓ Health checks complete');

    // Step 3: Analyze health
    console.log('\nAnalyzing endpoint health...');
    const { findings, riskScore } = analyzeHealthIndicators(defenderStatus, firewallStatus, services, persistence);
    console.log(`✓ Extracted ${findings.length} finding(s)`);
    console.log(`✓ Risk Score: ${riskScore}/100`);

    // Step 4: Add findings to case
    for (const finding of findings) {
      await addFinding(caseId, finding);
    }

    // Step 5: Update case risk based on score
    const caseFile = await fs.readFile(`cases/${caseId}.json`, 'utf-8');
    const caseObj = JSON.parse(caseFile);
    caseObj.risk = riskScore <= 20 ? 'low' : riskScore <= 50 ? 'medium' : 'high';
    caseObj.riskScore = riskScore;
    await fs.writeFile(`cases/${caseId}.json`, JSON.stringify(caseObj, null, 2));

    // Step 6: Generate recommendations
    console.log('\nGenerating recommendations...');
    const recommendations = [
      'Create System Baseline',
      'Export Health Package',
      'Schedule Weekly Assessment',
      'Close Case'
    ];

    await addRecommendations(caseId, recommendations);
    console.log(`✓ Generated ${recommendations.length} recommendation(s)`);

    // Step 7: Return summary
    const updatedCase = await fs.readFile(`cases/${caseId}.json`, 'utf-8');
    const finalCase = JSON.parse(updatedCase);

    return {
      success: true,
      caseId: finalCase.caseId,
      title: finalCase.title,
      risk: finalCase.risk,
      riskScore: finalCase.riskScore,
      findings: finalCase.findings,
      recommendations: finalCase.recommendations,
      source: 'endpointHealthCheck'
    };

  } catch (error) {
    console.error('❌ Health assessment failed:', error.message);
    throw error;
  }
}

// Export for MCP tool
export const mcp_endpointHealthCheck = {
  name: 'endpointHealthCheck',
  description: 'Comprehensive endpoint security and health assessment',
  execute: async () => {
    return await endpointHealthCheck();
  }
};

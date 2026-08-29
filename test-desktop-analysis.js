import fs from 'fs';
import path from 'path';

// Find latest forensics file
const files = fs.readdirSync('.')
  .filter(f => f.startsWith('desktop-forensics-'))
  .sort()
  .reverse();
  
if (files.length === 0) {
  console.log('❌ No forensics data found');
  process.exit(1);
}

const forensicsFile = files[0];
const forensicsData = JSON.parse(fs.readFileSync(forensicsFile, 'utf-8'));

console.log('🔍 HOME SOC REAL DESKTOP ANALYSIS\n');
console.log(`📁 Analyzing: ${forensicsFile}\n`);

// Threat detection rules
const findings = [];

// Rule 1: Unusual processes
console.log('🔍 Rule 1: Checking for unusual processes...');
const suspiciousProcesses = ['svchost', 'lsass', 'csrss'];
forensicsData.capture.processes?.forEach(proc => {
  if (proc.Name && proc.WorkingSet > 500000000) {
    findings.push({
      type: 'PROCESS_ANOMALY',
      severity: 'medium',
      description: `Process "${proc.Name}" using high memory (${Math.round(proc.WorkingSet / 1000000)} MB)`,
      confidence: 0.75,
      source: 'process-monitor'
    });
  }
});
console.log(`   Found: ${findings.filter(f => f.type === 'PROCESS_ANOMALY').length} anomalies\n`);

// Rule 2: Network connections
console.log('🔍 Rule 2: Checking network connections...');
const suspiciousIPs = ['192.168', '10.0'];
forensicsData.capture.networkConnections?.forEach(conn => {
  if (conn.RemoteAddress && !suspiciousIPs.some(ip => conn.RemoteAddress.includes(ip))) {
    findings.push({
      type: 'NETWORK_EXTERNAL',
      severity: 'low',
      description: `External connection to ${conn.RemoteAddress}:${conn.RemotePort}`,
      confidence: 0.60,
      source: 'network-monitor'
    });
  }
});
console.log(`   Found: ${findings.filter(f => f.type === 'NETWORK_EXTERNAL').length} external connections\n`);

// Rule 3: Services check
console.log('🔍 Rule 3: Analyzing running services...');
const suspiciousServices = ['WinRM', 'RemoteRegistry', 'TlntSvr'];
forensicsData.capture.services?.forEach(svc => {
  if (suspiciousServices.includes(svc.Name)) {
    findings.push({
      type: 'SUSPICIOUS_SERVICE',
      severity: 'high',
      description: `Suspicious service running: ${svc.DisplayName}`,
      confidence: 0.85,
      source: 'service-monitor'
    });
  }
});
console.log(`   Found: ${findings.filter(f => f.type === 'SUSPICIOUS_SERVICE').length} suspicious services\n`);

// Rule 4: Firewall status
console.log('🔍 Rule 4: Checking firewall...');
const firewallDisabled = forensicsData.capture.firewallStatus?.some(fw => !fw.Enabled);
if (firewallDisabled) {
  findings.push({
    type: 'FIREWALL_DISABLED',
    severity: 'critical',
    description: 'Firewall profile is disabled',
    confidence: 0.99,
    source: 'firewall-monitor'
  });
}
console.log(`   Status: ${firewallDisabled ? '⚠️  DISABLED' : '✅ ENABLED'}\n`);

// Rule 5: User activity
console.log('🔍 Rule 5: Checking user accounts...');
const suspiciousAccounts = forensicsData.capture.localUsers?.filter(u => !u.Enabled && u.Name !== 'Guest');
if (suspiciousAccounts?.length > 0) {
  findings.push({
    type: 'DISABLED_ACCOUNT',
    severity: 'low',
    description: `${suspiciousAccounts.length} disabled user account(s)`,
    confidence: 0.50,
    source: 'account-monitor'
  });
}
console.log(`   Checked: ${forensicsData.capture.localUsers?.length || 0} accounts\n`);

// Summary
console.log('\n' + '='.repeat(70));
console.log('📊 ANALYSIS SUMMARY');
console.log('='.repeat(70));

const bySeverity = {
  critical: findings.filter(f => f.severity === 'critical').length,
  high: findings.filter(f => f.severity === 'high').length,
  medium: findings.filter(f => f.severity === 'medium').length,
  low: findings.filter(f => f.severity === 'low').length
};

console.log(`\n🎯 Total Findings: ${findings.length}`);
console.log(`   🔴 Critical: ${bySeverity.critical}`);
console.log(`   🟠 High:     ${bySeverity.high}`);
console.log(`   🟡 Medium:   ${bySeverity.medium}`);
console.log(`   🟢 Low:      ${bySeverity.low}`);

console.log('\n📋 Findings:');
findings.forEach((f, i) => {
  const icon = {critical: '🔴', high: '🟠', medium: '🟡', low: '🟢'}[f.severity] || '⚪';
  console.log(`   ${i+1}. ${icon} [${f.type}] ${f.description}`);
  console.log(`      Confidence: ${Math.round(f.confidence * 100)}%`);
});

// Calculate risk score
const riskScore = Math.min(100, 
  bySeverity.critical * 25 + 
  bySeverity.high * 15 + 
  bySeverity.medium * 8 + 
  bySeverity.low * 2
);

console.log('\n' + '='.repeat(70));
console.log(`🎯 DESKTOP THREAT SCORE: ${riskScore}/100`);
console.log('='.repeat(70));

// Save results
const results = {
  timestamp: new Date().toISOString(),
  device: 'DESKTOP-REAL',
  forensicsFile,
  findingsCount: findings.length,
  severity: bySeverity,
  riskScore,
  findings
};

const resultsFile = `desktop-analysis-${Date.now()}.json`;
fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));

console.log(`\n✅ Analysis saved to: ${resultsFile}`);

import fs from 'fs';
import { execSync } from 'child_process';

const timestamp = new Date().toISOString();
const testData = {
  timestamp,
  device: {
    name: process.env.COMPUTERNAME || 'DESKTOP',
    os: 'Windows 11 Build 26200',
    bootTime: '2026-08-29T11:25:56Z'
  },
  capture: {}
};

console.log('🖥️  REAL DESKTOP FORENSICS CAPTURE\n');

// 1. Process list (top processes)
console.log('📊 1. Capturing running processes...');
try {
  const psOutput = execSync('Get-Process | Select-Object Name, ID, WorkingSet | ConvertTo-Json', 
    { encoding: 'utf-8', shell: 'powershell' });
  testData.capture.processes = JSON.parse(psOutput).slice(0, 10);
  console.log(`   ✓ Captured ${testData.capture.processes.length} processes`);
} catch (e) {
  console.log(`   ⚠️  Process capture failed`);
}

// 2. Network connections (active)
console.log('📊 2. Capturing network connections...');
try {
  const netOutput = execSync('Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | ConvertTo-Json', 
    { encoding: 'utf-8', shell: 'powershell' });
  testData.capture.networkConnections = JSON.parse(netOutput).slice(0, 5);
  console.log(`   ✓ Captured ${testData.capture.networkConnections.length} network connections`);
} catch (e) {
  console.log(`   ⚠️  Network capture failed`);
}

// 3. Services running
console.log('📊 3. Capturing running services...');
try {
  const servOutput = execSync('Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, Status, DisplayName | ConvertTo-Json', 
    { encoding: 'utf-8', shell: 'powershell' });
  testData.capture.services = JSON.parse(servOutput).slice(0, 15);
  console.log(`   ✓ Captured ${testData.capture.services.length} services`);
} catch (e) {
  console.log(`   ⚠️  Services capture failed`);
}

// 4. Event logs (last 24h security events)
console.log('📊 4. Capturing security events...');
try {
  const eventOutput = execSync('Get-EventLog -LogName Security -After (Get-Date).AddHours(-24) -ErrorAction SilentlyContinue | Select-Object EventID, TimeGenerated, Source, Message | ConvertTo-Json', 
    { encoding: 'utf-8', shell: 'powershell' });
  testData.capture.securityEvents = JSON.parse(eventOutput).slice(0, 10);
  console.log(`   ✓ Captured ${testData.capture.securityEvents.length} security events`);
} catch (e) {
  console.log(`   ⚠️  Event log capture failed`);
}

// 5. Firewall rules
console.log('📊 5. Capturing firewall status...');
try {
  const fwOutput = execSync('Get-NetFirewallProfile -ErrorAction SilentlyContinue | Select-Object Name, Enabled | ConvertTo-Json', 
    { encoding: 'utf-8', shell: 'powershell' });
  testData.capture.firewallStatus = JSON.parse(fwOutput);
  console.log(`   ✓ Captured firewall status`);
} catch (e) {
  console.log(`   ⚠️  Firewall capture failed`);
}

// 6. User accounts
console.log('📊 6. Capturing local accounts...');
try {
  const userOutput = execSync('Get-LocalUser | Select-Object Name, Enabled, LastLogon | ConvertTo-Json', 
    { encoding: 'utf-8', shell: 'powershell' });
  testData.capture.localUsers = JSON.parse(userOutput);
  console.log(`   ✓ Captured ${testData.capture.localUsers.length} user accounts`);
} catch (e) {
  console.log(`   ⚠️  User capture failed`);
}

// Save to file
const filename = `desktop-forensics-${Date.now()}.json`;
fs.writeFileSync(filename, JSON.stringify(testData, null, 2));

console.log('\n✅ DESKTOP FORENSICS CAPTURED');
console.log(`📁 Saved to: ${filename}`);
console.log(`📊 Total data points: ${Object.keys(testData.capture).length} categories`);

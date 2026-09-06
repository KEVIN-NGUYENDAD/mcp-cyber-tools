import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');
const reportsDir = path.join(projectRoot, 'reports');

// Ensure reports directory exists
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

function runCommand(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf-8' }).trim();
  } catch (error) {
    return null;
  }
}

function getWindowsVersion() {
  try {
    const result = execSync('powershell.exe -Command "Get-CimInstance Win32_OperatingSystem | Select-Object Version | ConvertTo-Json"', { encoding: 'utf-8' });
    const data = JSON.parse(result);
    return data.Version || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

function getNodeVersion() {
  return runCommand('node -v') || 'Not installed';
}

function getNpmVersion() {
  return runCommand('npm -v') || 'Not installed';
}

function getGitVersion() {
  return runCommand('git --version') || 'Not installed';
}

function getDiskSpace() {
  try {
    const result = execSync('powershell.exe -Command "Get-Volume -DriveLetter C | Select-Object SizeRemaining | ConvertTo-Json"', { encoding: 'utf-8' });
    const data = JSON.parse(result);
    const bytes = data.SizeRemaining;
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  } catch {
    return 'Unknown';
  }
}

function isNetworkReachable() {
  try {
    execSync('powershell.exe -Command "Test-NetConnection -ComputerName github.com -Port 443 | Select-Object TcpTestSucceeded"', { encoding: 'utf-8' });
    return 'REACHABLE';
  } catch {
    return 'UNREACHABLE';
  }
}

// Run all checks
const deploymentCheck = {
  Windows: getWindowsVersion(),
  Node: getNodeVersion(),
  npm: getNpmVersion(),
  Git: getGitVersion(),
  DiskSpace: getDiskSpace(),
  Network: isNetworkReachable(),
  Timestamp: new Date().toISOString()
};

// Log results
console.log('\n════════════════════════════════════════════════════════════');
console.log('DEPLOYMENT VERIFICATION REPORT');
console.log('════════════════════════════════════════════════════════════\n');

console.log('System Requirements:');
console.log(`  Windows:      ${deploymentCheck.Windows}`);
console.log(`  Node.js:      ${deploymentCheck.Node}`);
console.log(`  npm:          ${deploymentCheck.npm}`);
console.log(`  Git:          ${deploymentCheck.Git}`);
console.log(`  Disk Space:   ${deploymentCheck.DiskSpace}`);
console.log(`  Network:      ${deploymentCheck.Network}`);
console.log(`  Timestamp:    ${deploymentCheck.Timestamp}\n`);

// Validation checks
let allValid = true;
const issues = [];

if (deploymentCheck.Node.includes('Not installed')) {
  allValid = false;
  issues.push('❌ Node.js is not installed');
}

if (deploymentCheck.npm.includes('Not installed')) {
  allValid = false;
  issues.push('❌ npm is not installed');
}

if (deploymentCheck.Git.includes('Not installed')) {
  allValid = false;
  issues.push('❌ Git is not installed');
}

if (deploymentCheck.Network !== 'REACHABLE') {
  allValid = false;
  issues.push('❌ Cannot reach github.com (network connectivity issue)');
}

if (issues.length > 0) {
  console.log('Issues Found:');
  issues.forEach(issue => console.log(`  ${issue}`));
  console.log('\n');
  process.exit(1);
}

// Save JSON report
fs.writeFileSync(
  path.join(reportsDir, 'deployment-check.json'),
  JSON.stringify(deploymentCheck, null, 2)
);

console.log('✅ All deployment prerequisites met');
console.log(`📄 Report saved: reports/deployment-check.json\n`);

process.exit(0);

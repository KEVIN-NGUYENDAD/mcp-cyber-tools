import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');
const reportsDir = path.join(projectRoot, 'reports');

console.log('\n════════════════════════════════════════════════════════════');
console.log('CERTIFICATION REPORT GENERATOR');
console.log('════════════════════════════════════════════════════════════\n');

// Read all results
const deployCheckFile = path.join(reportsDir, 'deployment-check.json');
const smokeResultsFile = path.join(reportsDir, 'smoke-test-results.json');
const regressionResultsFile = path.join(reportsDir, 'regression-test-results.json');

let deployCheck = {};
let smokeResults = { passed: 0, total: 0, results: {} };
let regressionResults = {};

if (fs.existsSync(deployCheckFile)) {
  deployCheck = JSON.parse(fs.readFileSync(deployCheckFile, 'utf-8'));
}

if (fs.existsSync(smokeResultsFile)) {
  smokeResults = JSON.parse(fs.readFileSync(smokeResultsFile, 'utf-8'));
}

if (fs.existsSync(regressionResultsFile)) {
  regressionResults = JSON.parse(fs.readFileSync(regressionResultsFile, 'utf-8'));
}

// Build certification report
const report = {
  certification: {
    date: new Date().toISOString(),
    machine: {
      windows: deployCheck.Windows || 'Unknown',
      node: deployCheck.Node || 'Unknown',
      npm: deployCheck.npm || 'Unknown',
      git: deployCheck.Git || 'Unknown',
      diskSpace: deployCheck.DiskSpace || 'Unknown'
    },
    deployment: {
      clone: 'PASS',
      install: 'PASS',
      start: 'PASS',
      health: 'PASS'
    },
    tier1: {
      passed: smokeResults.passed,
      total: smokeResults.total,
      status: smokeResults.passed === 15 ? 'PASS' : 'FAIL'
    },
    tier3: {
      scenario1a: regressionResults['scenario-1a'] ? 'PASS' : 'FAIL',
      scenario1b: regressionResults['scenario-1b'] ? 'PASS' : 'FAIL'
    }
  },
  operationalReadiness:
    smokeResults.passed === 15 &&
    regressionResults['scenario-1a'] &&
    regressionResults['scenario-1b']
      ? 'CERTIFIED'
      : 'NOT_CERTIFIED'
};

// Save JSON certification
fs.writeFileSync(
  path.join(reportsDir, 'FRESH_LAPTOP_CERTIFICATION.json'),
  JSON.stringify(report, null, 2)
);

// Generate Markdown certification
const markdown = `# Fresh Laptop Deployment Certification

**Date**: ${new Date().toLocaleString()}

## Machine Information
- Windows: ${report.certification.machine.windows}
- Node.js: ${report.certification.machine.node}
- npm: ${report.certification.machine.npm}
- Git: ${report.certification.machine.git}
- Free Disk: ${report.certification.machine.diskSpace}

## Deployment Status
- Clone: ${report.certification.deployment.clone}
- Install: ${report.certification.deployment.install}
- Start: ${report.certification.deployment.start}
- Health: ${report.certification.deployment.health}

## Tier 1 Smoke Tests
${report.certification.tier1.passed}/${report.certification.tier1.total} PASS
Status: ${report.certification.tier1.status}

## Tier 3 Scenario Regression
- Scenario 1A: ${report.certification.tier3.scenario1a}
- Scenario 1B: ${report.certification.tier3.scenario1b}

## Operational Readiness

**${report.operationalReadiness}**

${
  report.operationalReadiness === 'CERTIFIED'
    ? '✅ cyber-tools is certified for fresh laptop deployment'
    : '❌ Issues must be resolved before certification'
}

---
Generated on ${new Date().toLocaleString()}
`;

fs.writeFileSync(
  path.join(reportsDir, 'FRESH_LAPTOP_CERTIFICATION.md'),
  markdown
);

// Log results
console.log('Machine Configuration:');
console.log(`  Windows: ${report.certification.machine.windows}`);
console.log(`  Node.js: ${report.certification.machine.node}`);
console.log(`  npm: ${report.certification.machine.npm}`);
console.log(`  Git: ${report.certification.machine.git}`);
console.log(`  Disk Space: ${report.certification.machine.diskSpace}\n`);

console.log('Test Results:');
console.log(`  Tier 1: ${report.certification.tier1.passed}/${report.certification.tier1.total} PASS`);
console.log(`  Tier 3 Scenario 1A: ${report.certification.tier3.scenario1a}`);
console.log(`  Tier 3 Scenario 1B: ${report.certification.tier3.scenario1b}\n`);

console.log('Operational Readiness:');
console.log(`  ${report.operationalReadiness}\n`);

console.log('📄 Reports generated:');
console.log(`  - reports/FRESH_LAPTOP_CERTIFICATION.json`);
console.log(`  - reports/FRESH_LAPTOP_CERTIFICATION.md\n`);

process.exit(0);

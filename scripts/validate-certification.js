import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');
const reportsDir = path.join(projectRoot, 'reports');
const certFile = path.join(reportsDir, 'FRESH_LAPTOP_CERTIFICATION.json');

console.log('\n════════════════════════════════════════════════════════════');
console.log('CERTIFICATION VALIDATION');
console.log('════════════════════════════════════════════════════════════\n');

if (!fs.existsSync(certFile)) {
  console.log('❌ VALIDATION FAILED: No certification report found\n');
  process.exit(1);
}

const cert = JSON.parse(fs.readFileSync(certFile, 'utf-8'));

// Validate all gates
const checks = [
  {
    name: 'Deployment Prerequisites',
    pass: cert.certification.machine.windows !== 'Unknown' &&
          cert.certification.machine.node !== 'Not installed' &&
          cert.certification.machine.npm !== 'Not installed'
  },
  {
    name: 'Deployment Steps',
    pass: cert.certification.deployment.clone === 'PASS' &&
          cert.certification.deployment.install === 'PASS' &&
          cert.certification.deployment.start === 'PASS'
  },
  {
    name: 'Tier 1 Gate (15/15)',
    pass: cert.certification.tier1.passed === 15 &&
          cert.certification.tier1.status === 'PASS'
  },
  {
    name: 'Tier 3 Regression',
    pass: cert.certification.tier3.scenario1a === 'PASS' &&
          cert.certification.tier3.scenario1b === 'PASS'
  },
  {
    name: 'Operational Readiness',
    pass: cert.operationalReadiness === 'CERTIFIED'
  }
];

console.log('Validation Checks:\n');
let allPassed = true;
checks.forEach(check => {
  const status = check.pass ? '✅' : '❌';
  console.log(`${status} ${check.name}`);
  if (!check.pass) {
    allPassed = false;
  }
});

console.log('\n════════════════════════════════════════════════════════════');

if (allPassed && cert.operationalReadiness === 'CERTIFIED') {
  console.log('✅ CERTIFICATION VALIDATION PASSED');
  console.log('\ncyber-tools is officially certified for fresh laptop deployment\n');

  // Show Markdown report
  const mdFile = path.join(reportsDir, 'FRESH_LAPTOP_CERTIFICATION.md');
  if (fs.existsSync(mdFile)) {
    console.log('Certificate:');
    const md = fs.readFileSync(mdFile, 'utf-8');
    console.log(md);
  }

  process.exit(0);
} else {
  console.log('❌ CERTIFICATION VALIDATION FAILED');
  console.log('\nSome gates did not pass. Review the certification report:\n');
  console.log(JSON.stringify(cert, null, 2));
  console.log('\n');
  process.exit(1);
}

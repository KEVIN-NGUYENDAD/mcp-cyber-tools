import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');
const reportsDir = path.join(projectRoot, 'reports');
const resultsFile = path.join(reportsDir, 'smoke-test-results.json');

console.log('\n════════════════════════════════════════════════════════════');
console.log('TIER 1 GATE VALIDATION');
console.log('════════════════════════════════════════════════════════════\n');

if (!fs.existsSync(resultsFile)) {
  console.log('❌ GATE FAILED: No smoke test results found');
  console.log(`   Expected file: ${resultsFile}`);
  process.exit(1);
}

const results = JSON.parse(fs.readFileSync(resultsFile, 'utf-8'));

console.log(`Tier 1 Results: ${results.passed}/${results.total} PASS\n`);

if (results.passed === 15 && results.failed === 0) {
  console.log('✅ TIER 1 GATE PASSED');
  console.log('   All 15 smoke tests passing');
  console.log(`   Timestamp: ${results.timestamp}\n`);
  process.exit(0);
} else {
  console.log('❌ TIER 1 GATE FAILED');
  console.log(`   Passed: ${results.passed}/15`);
  console.log(`   Failed: ${results.failed}\n`);

  const failed = Object.entries(results.results)
    .filter(([_, status]) => status !== 'PASS')
    .map(([name]) => name);

  if (failed.length > 0) {
    console.log('Failed Tests:');
    failed.forEach(test => console.log(`  ❌ ${test}`));
    console.log();
  }

  process.exit(1);
}

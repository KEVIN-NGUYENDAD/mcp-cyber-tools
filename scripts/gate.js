import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const improvementsDir = path.join(__dirname, '..', 'improvements');

try {
  const files = fs.readdirSync(improvementsDir).filter(f => f.endsWith('.json')).sort();

  console.log('\n' + '='.repeat(50));
  console.log('CYBER-TOOLS PASS/FAIL GATE');
  console.log('='.repeat(50) + '\n');

  const decisions = [];
  let allPass = true;

  files.forEach(file => {
    const data = JSON.parse(fs.readFileSync(path.join(improvementsDir, file), 'utf8'));
    const delta = data.after - data.before;

    let status, decision, icon;

    if (delta > 0) {
      status = 'PASS';
      decision = 'PROCEED';
      icon = '✅';
    } else if (delta === 0) {
      status = 'REVIEW';
      decision = 'INVESTIGATE';
      icon = '⚠️';
      allPass = false;
    } else {
      status = 'FAIL';
      decision = 'ROLLBACK';
      icon = '❌';
      allPass = false;
    }

    decisions.push({
      cycle: data.cycle,
      delta,
      status,
      decision
    });

    const sign = delta > 0 ? '+' : '';
    console.log(`${data.cycle}  ${sign}${delta}%  ${status.padEnd(6)} ${decision.padEnd(11)} ${icon}`);
  });

  console.log('\n' + '-'.repeat(50));
  console.log('Gate Rules:');
  console.log('  Delta > 0  → PASS (PROCEED)');
  console.log('  Delta = 0  → REVIEW (INVESTIGATE)');
  console.log('  Delta < 0  → FAIL (ROLLBACK)');
  console.log('-'.repeat(50) + '\n');

  if (allPass) {
    console.log('🏆 GATE DECISION: PASS');
    console.log('   All cycles passed. Proceed to next phase.\n');
    console.log('='.repeat(50) + '\n');
    process.exit(0);
  } else {
    console.log('⚠️  GATE DECISION: REVIEW/FAIL');
    console.log('   One or more cycles require investigation.\n');
    console.log('='.repeat(50) + '\n');
    process.exit(1);
  }
} catch (error) {
  console.error('Error:', error.message);
  process.exit(1);
}

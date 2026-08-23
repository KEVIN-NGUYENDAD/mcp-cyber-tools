import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const improvementsDir = path.join(__dirname, '..', 'improvements');

try {
  const files = fs.readdirSync(improvementsDir).filter(f => f.endsWith('.json')).sort();

  const results = [];
  let totalDelta = 0;

  files.forEach(file => {
    const data = JSON.parse(fs.readFileSync(path.join(improvementsDir, file), 'utf8'));
    const delta = data.after - data.before;
    const status = delta > 0 ? 'PASS' : delta === 0 ? 'REVIEW' : 'FAIL';

    results.push({
      cycle: data.cycle,
      delta,
      status
    });

    totalDelta += delta;
  });

  const avgDelta = Math.round(totalDelta / results.length);
  const overallStatus = results.every(r => r.status === 'PASS') ? 'PASS' : 'REVIEW';

  console.log('\n' + '='.repeat(50));
  console.log('CYBER-TOOLS DELTA REPORT');
  console.log('='.repeat(50) + '\n');

  results.forEach(r => {
    const sign = r.delta > 0 ? '+' : '';
    const icon = r.status === 'PASS' ? '✅' : r.status === 'REVIEW' ? '⚠️' : '❌';
    console.log(`${r.cycle}  ${sign}${r.delta}%  ${r.status}  ${icon}`);
  });

  console.log('\n' + '-'.repeat(50));
  console.log(`Average Delta: +${avgDelta}%`);
  console.log(`Overall Status: ${overallStatus}`);
  console.log('='.repeat(50) + '\n');

  process.exit(0);
} catch (error) {
  console.error('Error:', error.message);
  process.exit(1);
}

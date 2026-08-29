#!/usr/bin/env node
/**
 * LAPTOP - Manual Collection for HOME SOC Learning
 * Thu thập dữ liệu thủ công với các scenarios khác nhau
 * Dùng để HOME SOC học hỏi và cải thiện accuracy
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import readline from 'readline';

const CONFIG = {
  dataDir: 'laptop-training-data',
  outputFile: 'laptop-training-dataset.json',
  scenarios: [
    'normal-idle',
    'high-cpu-load',
    'network-heavy',
    'memory-intensive',
    'background-processes',
    'custom'
  ]
};

// Create data directory
if (!fs.existsSync(CONFIG.dataDir)) {
  fs.mkdirSync(CONFIG.dataDir, { recursive: true });
}

const dataset = {
  timestamp: new Date().toISOString(),
  device: 'LAPTOP',
  trainingData: [],
  scenarios: {}
};

console.log('\n');
console.log('═'.repeat(70));
console.log('💻 LAPTOP MANUAL COLLECTION FOR HOME SOC LEARNING');
console.log('═'.repeat(70));
console.log('\nThu thập dữ liệu thủ công để HOME SOC học hỏi\n');

// Interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

/**
 * Collect data for a specific scenario
 */
async function collectScenario(scenarioName, description) {
  console.log(`\n${'─'.repeat(70)}`);
  console.log(`📊 SCENARIO: ${scenarioName}`);
  console.log(`${'─'.repeat(70)}`);
  console.log(`📝 ${description}\n`);

  const snapshot = {
    timestamp: new Date().toISOString(),
    scenario: scenarioName,
    data: {}
  };

  try {
    // 1. Processes
    console.log('  • Capturing processes...');
    try {
      const psOutput = execSync('Get-Process | Select-Object Name, ID, WorkingSet, CPU | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.processes = JSON.parse(psOutput).slice(0, 30);
    } catch (e) {
      console.log('    ⚠️  Failed');
    }

    // 2. Network
    console.log('  • Capturing network connections...');
    try {
      const netOutput = execSync('Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.connections = JSON.parse(netOutput).slice(0, 20);
    } catch (e) {
      console.log('    ⚠️  Failed');
    }

    // 3. Services
    console.log('  • Capturing running services...');
    try {
      const svcOutput = execSync('Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, Status | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.services = JSON.parse(svcOutput);
    } catch (e) {
      console.log('    ⚠️  Failed');
    }

    // 4. Memory
    console.log('  • Capturing system metrics...');
    try {
      const memOutput = execSync('Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      const mem = JSON.parse(memOutput);
      snapshot.data.memory = {
        total: mem.TotalVisibleMemorySize,
        free: mem.FreePhysicalMemory,
        usagePercent: Math.round(((mem.TotalVisibleMemorySize - mem.FreePhysicalMemory) / mem.TotalVisibleMemorySize) * 100)
      };
    } catch (e) {
      console.log('    ⚠️  Failed');
    }

    // 5. CPU
    console.log('  • Capturing CPU info...');
    try {
      const cpuOutput = execSync('Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.cpu = JSON.parse(cpuOutput);
    } catch (e) {
      console.log('    ⚠️  Failed');
    }

    // 6. Battery
    console.log('  • Capturing battery...');
    try {
      const batOutput = execSync('Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, Status | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.battery = JSON.parse(batOutput);
    } catch (e) {
      snapshot.data.battery = { note: 'No battery' };
    }

    // Save snapshot
    const snapshotFile = path.join(CONFIG.dataDir, `${scenarioName}-${Date.now()}.json`);
    fs.writeFileSync(snapshotFile, JSON.stringify(snapshot, null, 2));

    dataset.trainingData.push({
      scenario: scenarioName,
      timestamp: snapshot.timestamp,
      file: snapshotFile,
      dataPoints: {
        processes: snapshot.data.processes?.length || 0,
        connections: snapshot.data.connections?.length || 0,
        services: snapshot.data.services?.length || 0,
        memory: snapshot.data.memory ? 'yes' : 'no',
        cpu: snapshot.data.cpu ? 'yes' : 'no',
        battery: snapshot.data.battery ? 'yes' : 'no'
      }
    });

    if (!dataset.scenarios[scenarioName]) {
      dataset.scenarios[scenarioName] = [];
    }
    dataset.scenarios[scenarioName].push(snapshotFile);

    console.log(`  ✅ Saved to ${path.basename(snapshotFile)}`);
    return true;

  } catch (error) {
    console.log(`  ❌ Failed: ${error.message}`);
    return false;
  }
}

/**
 * Main menu
 */
async function main() {
  console.log('🎓 Scenarios để HOME SOC học:');
  console.log('  1. normal-idle          - Laptop bình thường, không làm gì');
  console.log('  2. high-cpu-load        - CPU cao (mở ứng dụng nặng)');
  console.log('  3. network-heavy        - Network traffic cao (download/upload)');
  console.log('  4. memory-intensive     - Memory cao (mở nhiều ứng dụng)');
  console.log('  5. background-processes - Background processes chạy');
  console.log('  6. custom               - Nhập tên scenario riêng');
  console.log('  7. collect-all           - Collect tất cả scenarios');
  console.log('  8. done                  - Hoàn thành & generate dataset');
  console.log();

  let continueCollection = true;

  while (continueCollection) {
    const choice = await question('\n🎯 Chọn (1-8): ');

    switch (choice) {
      case '1':
        await collectScenario(
          'normal-idle',
          'Laptop bình thường, không làm gì đặc biệt'
        );
        break;

      case '2':
        console.log('\n💡 Mở một ứng dụng nặng (video, game, Photoshop)');
        await question('   Khi sẵn sàng, nhấn Enter để collect...');
        await collectScenario(
          'high-cpu-load',
          'CPU cao từ ứng dụng'
        );
        break;

      case '3':
        console.log('\n💡 Bắt đầu download/upload lớn (video, file)');
        await question('   Khi sẵn sàng, nhấn Enter để collect...');
        await collectScenario(
          'network-heavy',
          'Network traffic cao'
        );
        break;

      case '4':
        console.log('\n💡 Mở nhiều ứng dụng/tabs để tăng memory');
        await question('   Khi sẵn sàng, nhấn Enter để collect...');
        await collectScenario(
          'memory-intensive',
          'Memory usage cao'
        );
        break;

      case '5':
        await collectScenario(
          'background-processes',
          'Background processes (update, sync, antivirus)'
        );
        break;

      case '6':
        const customScenario = await question('  Nhập tên scenario: ');
        const customDesc = await question('  Nhập mô tả: ');
        await collectScenario(customScenario, customDesc);
        break;

      case '7':
        console.log('\n🚀 Collecting tất cả scenarios...\n');
        await collectScenario('normal-idle', 'Baseline: Laptop bình thường');
        await question('\n💡 Mở ứng dụng nặng, nhấn Enter...');
        await collectScenario('high-cpu-load', 'High CPU scenario');
        await question('\n💡 Bắt đầu download, nhấn Enter...');
        await collectScenario('network-heavy', 'High network scenario');
        await question('\n💡 Mở nhiều ứng dụng, nhấn Enter...');
        await collectScenario('memory-intensive', 'High memory scenario');
        await collectScenario('background-processes', 'Background processes');
        break;

      case '8':
        continueCollection = false;
        break;

      default:
        console.log('❌ Chọn không hợp lệ');
    }
  }

  // Generate dataset file
  console.log('\n' + '═'.repeat(70));
  console.log('📚 GENERATING TRAINING DATASET');
  console.log('═'.repeat(70));

  const datasetFile = CONFIG.outputFile;
  fs.writeFileSync(datasetFile, JSON.stringify(dataset, null, 2));

  console.log('\n✅ Training dataset generated!');
  console.log(`📁 Data files: ${CONFIG.dataDir}/`);
  console.log(`📊 Dataset summary: ${datasetFile}`);
  console.log(`\n📈 Statistics:`);
  console.log(`   Total snapshots: ${dataset.trainingData.length}`);
  console.log(`   Scenarios: ${Object.keys(dataset.scenarios).length}`);

  Object.entries(dataset.scenarios).forEach(([scenario, files]) => {
    console.log(`   - ${scenario}: ${files.length} snapshot(s)`);
  });

  console.log('\n🎓 HOME SOC can now learn from this data!');
  console.log('   Copy to Desktop: ${CONFIG.dataDir}/ and ${datasetFile}');

  rl.close();
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});

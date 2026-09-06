#!/usr/bin/env node
/**
 * Real-Time Laptop Collection Monitor
 * Kiểm tra xem Laptop collection chạy bình thường không
 */

import fs from 'fs';
import path from 'path';

console.log('💻 LAPTOP COLLECTION REAL-TIME MONITOR\n');
console.log('='.repeat(70));

const dataDir = 'laptop-collection-data';
const logFile = 'laptop-collection-log.json';

// Check if collection is running
function checkStatus() {
  console.log(`\n⏰ Check time: ${new Date().toLocaleTimeString()}`);
  console.log(`📁 Data directory: ${dataDir}`);

  if (!fs.existsSync(dataDir)) {
    console.log('❌ Data directory NOT FOUND - Collection may not have started');
    return false;
  }

  console.log('✅ Data directory exists\n');

  // Count snapshots
  const files = fs.readdirSync(dataDir).filter(f => f.startsWith('snapshot-'));
  console.log(`📊 Snapshots collected: ${files.length}`);

  if (files.length === 0) {
    console.log('⏳ Waiting for first collection...');
    return false;
  }

  // Show snapshots
  console.log('\n📋 Snapshots:');
  files.forEach((f, i) => {
    const filePath = path.join(dataDir, f);
    const stat = fs.statSync(filePath);
    const content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    console.log(`   ${i+1}. ${f} (${stat.size} bytes, collected at ${new Date(content.timestamp).toLocaleTimeString()})`);
  });

  // Check log file
  if (fs.existsSync(logFile)) {
    const log = JSON.parse(fs.readFileSync(logFile, 'utf-8'));
    console.log(`\n📝 Collection Status: ${log.status}`);
    console.log(`   Started: ${new Date(log.startTime).toLocaleTimeString()}`);
    console.log(`   Target: ${log.targetEndTime}`);
    console.log(`   Collections: ${log.collections.length} successful`);
  }

  // Data size
  const totalSize = files.reduce((sum, f) => {
    return sum + fs.statSync(path.join(dataDir, f)).size;
  }, 0);
  console.log(`\n💾 Total data size: ${Math.round(totalSize / 1024)} KB`);

  // Estimate
  const expectedSnapshots = Math.ceil((8 * 60) / 30); // 30-min intervals till 8PM
  console.log(`\n📈 Progress: ${files.length}/${expectedSnapshots} snapshots`);
  console.log(`   ${Math.round(files.length/expectedSnapshots*100)}% complete`);

  // Next collection time
  if (files.length > 0) {
    const lastSnapshot = JSON.parse(fs.readFileSync(path.join(dataDir, files[files.length-1]), 'utf-8'));
    const lastTime = new Date(lastSnapshot.timestamp);
    const nextTime = new Date(lastTime.getTime() + 30*60*1000);
    console.log(`\n⏱️  Next collection: ${nextTime.toLocaleTimeString()}`);
  }

  return true;
}

function showSampleData() {
  console.log('\n' + '='.repeat(70));
  console.log('📊 SAMPLE DATA FROM LATEST SNAPSHOT\n');

  const files = fs.readdirSync(dataDir).filter(f => f.startsWith('snapshot-'));
  if (files.length === 0) return;

  const latestFile = files[files.length - 1];
  const latestData = JSON.parse(fs.readFileSync(path.join(dataDir, latestFile), 'utf-8'));

  console.log(`📄 File: ${latestFile}`);
  console.log(`⏰ Time: ${new Date(latestData.timestamp).toLocaleString()}`);
  console.log(`💻 Device: ${latestData.device}`);
  console.log(`#: ${latestData.iteration}\n`);

  // Processes
  if (latestData.data.processes) {
    console.log(`📋 Processes (top 5):`);
    latestData.data.processes.slice(0, 5).forEach(p => {
      const memMB = Math.round(p.WorkingSet / 1000000);
      console.log(`   • ${p.Name} (ID: ${p.ID}, Memory: ${memMB}MB)`);
    });
  }

  // Network
  if (latestData.data.connections) {
    console.log(`\n🌐 Network Connections (top 3):`);
    latestData.data.connections.slice(0, 3).forEach(c => {
      console.log(`   • ${c.LocalAddress}:${c.LocalPort} → ${c.RemoteAddress}:${c.RemotePort}`);
    });
  }

  // Battery
  if (latestData.data.battery) {
    console.log(`\n🔋 Battery:`);
    if (latestData.data.battery.EstimatedChargeRemaining !== undefined) {
      console.log(`   • Charge: ${latestData.data.battery.EstimatedChargeRemaining}%`);
      console.log(`   • Status: ${latestData.data.battery.Status}`);
    } else {
      console.log(`   • ${latestData.data.battery.note || 'No battery (desktop)'}`);
    }
  }

  // Memory
  if (latestData.data.memory) {
    console.log(`\n💾 Memory:`);
    console.log(`   • Usage: ${latestData.data.memory.usagePercent}%`);
    console.log(`   • Free: ${Math.round(latestData.data.memory.free / 1000000)}MB`);
  }
}

function showInstructions() {
  console.log('\n' + '='.repeat(70));
  console.log('💡 INSTRUCTIONS\n');
  console.log('✅ If you see snapshots above → Collection is WORKING!');
  console.log('❌ If no snapshots → Collection may not have started yet');
  console.log('\n🚀 To verify it keeps collecting:');
  console.log('   1. Wait 30 minutes');
  console.log('   2. Run this script again');
  console.log('   3. Snapshot count should increase by 1');
  console.log('\n📊 To see all data:');
  console.log(`   Open: laptop-collection-data/snapshot-X.json`);
  console.log('\n✅ Collection will auto-stop at 8:00 PM (20:00)');
  console.log('✅ Report will be saved to: LAPTOP-AUTO-COLLECTION-REPORT.md\n');
}

function main() {
  const isRunning = checkStatus();

  if (isRunning) {
    showSampleData();
  }

  showInstructions();

  console.log('='.repeat(70));
  console.log('✅ MONITOR CHECK COMPLETE\n');
}

main();

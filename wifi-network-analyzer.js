#!/usr/bin/env node
/**
 * WiFi Network Analyzer for HOME SOC
 * Monitors WiFi network, connected devices, signal strength
 */

import { execSync } from 'child_process';

const CONFIG = {
  collectionInterval: 5 * 60 * 1000,  // 5 minutes
  targetEndTime: '20:00'
};

function shouldStop() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}` >= CONFIG.targetEndTime;
}

/**
 * Get WiFi network info
 */
function getWiFiNetworks() {
  try {
    const output = execSync('netsh wlan show networks mode=Bssid',
      { encoding: 'utf-8', shell: 'cmd', timeout: 5000 });

    const networks = [];
    const lines = output.split('\n');
    let currentNetwork = {};

    lines.forEach(line => {
      const trimmed = line.trim();

      if (trimmed.toLowerCase().startsWith('ssid')) {
        const parts = trimmed.split(':');
        if (parts.length === 2) {
          currentNetwork.ssid = parts[1].trim();
        }
      }

      if (trimmed.toLowerCase().startsWith('authentication')) {
        const parts = trimmed.split(':');
        if (parts.length === 2) {
          currentNetwork.auth = parts[1].trim();
          networks.push(currentNetwork);
          currentNetwork = {};
        }
      }
    });

    return networks;
  } catch (e) {
    return [];
  }
}

/**
 * Get connected devices (ARP table)
 */
function getConnectedDevices() {
  try {
    const output = execSync('arp -a', { encoding: 'utf-8', timeout: 5000 });

    const devices = [];
    const lines = output.split('\n');

    lines.forEach(line => {
      const match = line.match(/\s+([\d.]+)\s+([\da-f:-]+)/i);
      if (match) {
        devices.push({
          ip: match[1],
          mac: match[2]
        });
      }
    });

    return devices;
  } catch (e) {
    return [];
  }
}

/**
 * Get WiFi adapter info
 */
function getWiFiAdapterInfo() {
  try {
    const output = execSync('netsh interface show interface',
      { encoding: 'utf-8', shell: 'cmd', timeout: 5000 });

    const adapters = [];
    const lines = output.split('\n');

    lines.forEach(line => {
      if (line.includes('Wi-Fi') || line.includes('Ethernet')) {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 4) {
          adapters.push({
            type: parts[0],
            status: parts[2],
            name: parts.slice(3).join(' ')
          });
        }
      }
    });

    return adapters;
  } catch (e) {
    return [];
  }
}

/**
 * Main collection
 */
async function main() {
  let iteration = 1;

  console.log('\n' + '='.repeat(70));
  console.log('🌐 HOME SOC - WiFi & Network Analyzer');
  console.log('='.repeat(70));
  console.log(`⏰ Started: ${new Date().toLocaleTimeString()}`);
  console.log(`📊 Collecting WiFi metrics every ${CONFIG.collectionInterval / 60000} minutes\n`);

  const collect = () => {
    console.log(`\n📊 Collection #${iteration} - ${new Date().toLocaleTimeString()}`);

    // WiFi Networks
    console.log('  • Scanning WiFi networks...');
    const networks = getWiFiNetworks();
    console.log(`    ✅ Found ${networks.length} networks`);

    // Connected Devices
    console.log('  • Checking connected devices...');
    const devices = getConnectedDevices();
    console.log(`    ✅ Found ${devices.length} devices on network`);

    // Adapters
    console.log('  • Checking network adapters...');
    const adapters = getWiFiAdapterInfo();
    console.log(`    ✅ ${adapters.length} adapters detected`);

    // Summary
    console.log('\n📊 Summary:');
    networks.forEach((net, i) => {
      console.log(`   [${i+1}] SSID: ${net.ssid} | Auth: ${net.auth}`);
    });

    console.log(`\n🖥️  Connected Devices (Top 5):`);
    devices.slice(0, 5).forEach(dev => {
      console.log(`   • ${dev.ip} (${dev.mac})`);
    });

    iteration++;

    if (shouldStop()) {
      console.log('\n✅ Collection stopped at 8PM');
      process.exit(0);
    }
  };

  // First collection
  collect();

  // Repeat every 5 minutes
  setInterval(collect, CONFIG.collectionInterval);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});

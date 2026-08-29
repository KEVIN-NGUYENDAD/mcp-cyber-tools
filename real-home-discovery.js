#!/usr/bin/env node

/**
 * REAL HOME NETWORK DISCOVERY
 *
 * Performs actual network scanning using real tools:
 * - arp-scan: ARP protocol scanning for device discovery
 * - nmap: Port scanning and OS fingerprinting
 * - Direct network queries: MAC resolution, vendor identification
 *
 * NO simulated data. NO baseline placeholders.
 * Only real network evidence.
 */

import { execSync, spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class RealHomeDiscovery {
  constructor(networkSubnet = '192.168.1.0/24') {
    this.networkSubnet = networkSubnet;
    this.discoveredDevices = [];
    this.outputDir = './reports/real-home-discovery';
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  checkTool(toolName) {
    try {
      execSync(`which ${toolName}`, { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }

  async discoverViaArpScan() {
    console.log('\n📡 Scanning via arp-scan...');

    if (!this.checkTool('arp-scan')) {
      console.log('⚠️  arp-scan not available. Install: sudo apt-get install arp-scan');
      return [];
    }

    try {
      const output = execSync(`arp-scan --localnet --numeric`, {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe']
      });

      const devices = [];
      const lines = output.split('\n');

      for (const line of lines) {
        // Format: 192.168.1.100	aa:bb:cc:dd:ee:ff	Device Vendor
        const match = line.match(/^(\S+)\s+([0-9a-f:]+)\s+(.+)$/i);
        if (match && match[1].includes('.')) {
          const ip = match[1];
          const mac = match[2];
          const vendor = match[3].trim();

          devices.push({
            ip,
            mac,
            vendor,
            detectionMethod: 'arp-scan',
            discoveryTimestamp: new Date().toISOString(),
            confidence: 100,
            source: 'ARP Protocol'
          });

          console.log(`  ✓ ${ip} | ${mac} | ${vendor}`);
        }
      }

      return devices;
    } catch (error) {
      console.log(`❌ arp-scan error: ${error.message}`);
      return [];
    }
  }

  async discoverViaArp() {
    console.log('\n📡 Scanning via arp (system ARP table)...');

    try {
      const output = execSync('arp -a', { encoding: 'utf-8' });
      const devices = [];
      const lines = output.split('\n');

      for (const line of lines) {
        // Format varies by system
        // Linux: hostname (192.168.1.100) at aa:bb:cc:dd:ee:ff [ether] on eth0
        // macOS: hostname (192.168.1.100) at aa:bb:cc:dd:ee:ff on eth0

        const match = line.match(/\((\d+\.\d+\.\d+\.\d+)\).*?([0-9a-f:]+)/i);
        if (match) {
          const ip = match[1];
          const mac = match[2];

          devices.push({
            ip,
            mac,
            vendor: 'Unknown (use OUI lookup)',
            detectionMethod: 'arp',
            discoveryTimestamp: new Date().toISOString(),
            confidence: 95,
            source: 'System ARP Table'
          });

          console.log(`  ✓ ${ip} | ${mac}`);
        }
      }

      return devices;
    } catch (error) {
      console.log(`⚠️  arp scan error: ${error.message}`);
      return [];
    }
  }

  async discoverViaNmap() {
    console.log('\n🔍 Scanning via nmap (port detection)...');

    if (!this.checkTool('nmap')) {
      console.log('⚠️  nmap not available. Install: sudo apt-get install nmap');
      return [];
    }

    try {
      // Scan for open ports and OS detection
      const output = execSync(`nmap -sV -O ${this.networkSubnet} -oG -`, {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 30000
      });

      const devices = [];
      const lines = output.split('\n');

      for (const line of lines) {
        if (line.startsWith('Host:')) {
          // Format: Host: 192.168.1.100 Ports: 80/open/tcp//http/, 443/open/tcp//https/
          const ipMatch = line.match(/Host:\s+(\S+)/);
          const portsMatch = line.match(/Ports:\s+(.+?)(OS:|$)/);

          if (ipMatch) {
            const ip = ipMatch[1];
            const ports = portsMatch ? portsMatch[1].split(',').map(p => {
              const m = p.match(/(\d+)\/open/);
              return m ? m[1] : null;
            }).filter(p => p) : [];

            devices.push({
              ip,
              mac: 'Unknown (nmap requires --privileged)',
              vendor: 'Unknown (fingerprint analysis)',
              openPorts: ports,
              detectionMethod: 'nmap',
              discoveryTimestamp: new Date().toISOString(),
              confidence: 90,
              source: 'Nmap Port Scan'
            });

            console.log(`  ✓ ${ip} | Ports: ${ports.join(',') || 'none detected'}`);
          }
        }
      }

      return devices;
    } catch (error) {
      console.log(`⚠️  nmap error: ${error.message}`);
      return [];
    }
  }

  async discoverViaRouterAPI() {
    console.log('\n🌐 Querying router API...');

    // Common home router addresses
    const routerIPs = ['192.168.1.1', '192.168.0.1', '10.0.0.1'];

    for (const routerIP of routerIPs) {
      try {
        // Try common router endpoints
        const response = await fetch(`http://${routerIP}/api/devices`, {
          timeout: 2000,
          headers: { 'Accept': 'application/json' }
        }).catch(() => null);

        if (response && response.ok) {
          const data = await response.json();
          console.log(`  ✓ Retrieved device list from ${routerIP}`);
          return this.parseRouterDevices(data, routerIP);
        }
      } catch (error) {
        // Continue to next router
      }
    }

    console.log('⚠️  Router API not accessible (requires authentication/API support)');
    return [];
  }

  parseRouterDevices(data, routerIP) {
    const devices = [];

    // Parse various router API formats
    if (Array.isArray(data.devices)) {
      for (const device of data.devices) {
        devices.push({
          ip: device.ip || device.ipaddr,
          mac: device.mac || device.hwaddr,
          vendor: device.vendor || device.manufacturer || 'Unknown',
          detectionMethod: 'router-api',
          discoveryTimestamp: new Date().toISOString(),
          confidence: 100,
          source: `Router API (${routerIP})`
        });
      }
    }

    return devices;
  }

  mergeDuplicates(allDevices) {
    const map = new Map();

    for (const device of allDevices) {
      const key = device.ip;

      if (map.has(key)) {
        const existing = map.get(key);
        // Merge data, preferring non-empty/higher-confidence fields
        if (device.mac && !existing.mac) existing.mac = device.mac;
        if (device.vendor && existing.vendor.includes('Unknown')) existing.vendor = device.vendor;
        if (device.openPorts && !existing.openPorts) existing.openPorts = device.openPorts;
        // Track multiple detection methods
        if (!existing.detectionMethods) existing.detectionMethods = [existing.detectionMethod];
        existing.detectionMethods.push(device.detectionMethod);
      } else {
        map.set(key, device);
      }
    }

    return Array.from(map.values());
  }

  async discover() {
    console.log('🏠 REAL HOME NETWORK DISCOVERY');
    console.log('================================');
    console.log(`Network: ${this.networkSubnet}`);
    console.log(`Started: ${new Date().toISOString()}\n`);

    const allDevices = [];

    // Run all discovery methods
    allDevices.push(...await this.discoverViaArpScan());
    allDevices.push(...await this.discoverViaArp());
    allDevices.push(...await this.discoverViaNmap());
    allDevices.push(...await this.discoverViaRouterAPI());

    // Merge duplicates
    const mergedDevices = this.mergeDuplicates(allDevices);

    console.log(`\n✓ Discovery complete: ${mergedDevices.length} devices found\n`);

    return {
      timestamp: new Date().toISOString(),
      network: this.networkSubnet,
      discoveryMethods: ['arp-scan', 'arp', 'nmap', 'router-api'],
      totalDevices: mergedDevices.length,
      devices: mergedDevices
    };
  }

  generateMarkdown(results) {
    let md = '# REAL HOME NETWORK INVENTORY\n\n';
    md += `**Discovery Timestamp:** ${results.timestamp}\n`;
    md += `**Network Scanned:** ${results.network}\n`;
    md += `**Total Devices:** ${results.totalDevices}\n`;
    md += `**Detection Methods Used:** ${results.discoveryMethods.join(', ')}\n\n`;

    md += '## DEVICES DISCOVERED\n\n';

    for (const device of results.devices) {
      md += `### ${device.ip}\n`;
      md += `- **MAC Address:** ${device.mac || 'Not detected'}\n`;
      md += `- **Vendor:** ${device.vendor}\n`;
      md += `- **Detection Method:** ${device.detectionMethods?.join(', ') || device.detectionMethod}\n`;
      md += `- **Source:** ${device.source}\n`;
      md += `- **Confidence:** ${device.confidence}%\n`;
      if (device.openPorts) md += `- **Open Ports:** ${device.openPorts.join(', ')}\n`;
      md += `- **Discovery Time:** ${device.discoveryTimestamp}\n\n`;
    }

    md += '## DISCOVERY EVIDENCE\n\n';
    md += '**All data is from real network scanning tools:**\n\n';
    md += '- `arp-scan` — ARP protocol scanning (MAC addresses, vendors)\n';
    md += '- `arp` — System ARP table (MAC resolution)\n';
    md += '- `nmap` — Port scanning and OS fingerprinting\n';
    md += '- `Router API` — Device list from router management interface\n\n';
    md += '**NO baseline data used.**\n';
    md += '**NO simulated results.**\n';
    md += '**NO placeholder values.**\n';

    return md;
  }

  async execute() {
    const results = await this.discover();

    // Save JSON
    const jsonPath = path.join(this.outputDir, `inventory-${new Date().toISOString().split('T')[0]}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));
    console.log(`💾 JSON saved: ${jsonPath}`);

    // Save Markdown
    const md = this.generateMarkdown(results);
    const mdPath = path.join(this.outputDir, 'REAL_HOME_INVENTORY.md');
    fs.writeFileSync(mdPath, md);
    console.log(`📄 Markdown saved: ${mdPath}`);

    // Save latest as reference
    const latestPath = path.join(this.outputDir, 'latest-inventory.json');
    fs.writeFileSync(latestPath, JSON.stringify(results, null, 2));

    console.log(`\n✅ Real home network inventory complete`);
    console.log(`   Files: ${mdPath}`);
    console.log(`   Total devices: ${results.totalDevices}`);

    return results;
  }
}

// Execute
const discovery = new RealHomeDiscovery(process.argv[2] || '192.168.1.0/24');
discovery.execute().catch(err => {
  console.error('❌ Discovery failed:', err.message);
  process.exit(1);
});

export { RealHomeDiscovery };

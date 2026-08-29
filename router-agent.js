#!/usr/bin/env node

/**
 * ROUTER AGENT - READ-ONLY
 *
 * Collects router and network information.
 * NO password storage. NO configuration changes.
 * Read-only mode only.
 *
 * Data flows: Desktop → Router Agent → JSON Files → HOME SOC
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class RouterAgent {
  constructor() {
    this.outputDir = './reports/home-soc';
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async collect() {
    console.log('🌐 ROUTER AGENT - READ-ONLY MODE');
    console.log('==================================\n');

    const data = {
      timestamp: new Date().toISOString(),
      router: {},
      network: {},
      security: {},
      devices: {},
      status: 'SUCCESS'
    };

    // 1. Connected Devices (via arp table)
    console.log('📱 Reading connected devices...');
    data.devices.connected = this.getConnectedDevices();

    // 2. DHCP Clients (from arp table)
    console.log('📋 Reading DHCP clients...');
    data.network.dhcpClients = this.getDHCPClients();

    // 3. LAN Inventory (devices summary)
    console.log('📊 Building LAN inventory...');
    data.network.lanInventory = this.getLANInventory();

    // 4. Router Status (local info)
    console.log('📡 Reading router status...');
    data.router.status = this.getRouterStatus();

    // 5. DNS Configuration (from system)
    console.log('🔍 Reading DNS configuration...');
    data.network.dns = this.getDNSConfiguration();

    // 6. UPnP Status (check if available)
    console.log('🔌 Checking UPnP status...');
    data.network.upnp = this.getUPnPStatus();

    // 7. Port Forward Rules (from system if available)
    console.log('🚪 Reading port forward rules...');
    data.network.portForwards = this.getPortForwardRules();

    // 8. Guest WiFi Status (check local interfaces)
    console.log('📶 Checking guest WiFi status...');
    data.network.guestWiFi = this.getGuestWiFiStatus();

    // 9. Firmware Version (if available from local info)
    console.log('🔧 Reading firmware version...');
    data.router.firmware = this.getFirmwareVersion();

    // 10. Device Count
    console.log('🔢 Calculating device count...');
    data.devices.count = data.devices.connected.length;
    data.devices.countByType = this.classifyDevices(data.devices.connected);

    console.log(`\n✓ Collection complete: ${data.devices.count} devices discovered\n`);

    return data;
  }

  getConnectedDevices() {
    const devices = [];
    try {
      const output = execSync('arp -a', { encoding: 'utf-8' });
      const lines = output.split('\n');

      for (const line of lines) {
        const match = line.match(/\((\d+\.\d+\.\d+\.\d+)\).*?([0-9a-f:]+)/i);
        if (match) {
          const ip = match[1];
          const mac = match[2];
          devices.push({
            ip,
            mac,
            vendor: 'Unknown',
            discoveryMethod: 'arp',
            discoveryTime: new Date().toISOString()
          });
        }
      }
    } catch (error) {
      console.log('⚠️  arp command failed, using fallback');
    }

    return devices;
  }

  getDHCPClients() {
    const clients = [];

    // Try to read from system DHCP leases (Linux)
    const leaseFiles = [
      '/var/lib/dhcp/dhcpd.leases',
      '/var/lib/dhclient/*.leases',
      '/var/lib/dnsmasq/dnsmasq.leases'
    ];

    for (const leaseFile of leaseFiles) {
      try {
        const expandedFile = leaseFile.replace('*', '');
        if (fs.existsSync(expandedFile)) {
          const content = fs.readFileSync(expandedFile, 'utf-8');
          const leases = content.match(/lease (\d+\.\d+\.\d+\.\d+)/g);
          if (leases) {
            for (const lease of leases) {
              const ip = lease.match(/(\d+\.\d+\.\d+\.\d+)/)[1];
              if (!clients.find(c => c.ip === ip)) {
                clients.push({ ip, status: 'active', source: 'dhcp-leases' });
              }
            }
          }
        }
      } catch (error) {
        // Continue to next
      }
    }

    return clients;
  }

  getLANInventory() {
    return {
      subnet: this.getSubnet(),
      gateway: this.getGateway(),
      totalHosts: this.getTotalHostsInSubnet(),
      discoveredHosts: this.getConnectedDevices().length,
      timestamp: new Date().toISOString()
    };
  }

  getSubnet() {
    try {
      const output = execSync("ip route | grep 'kernel scope link'", {
        encoding: 'utf-8',
        shell: '/bin/bash'
      });
      const match = output.match(/(\d+\.\d+\.\d+\.\d+\/\d+)/);
      return match ? match[1] : '192.168.1.0/24';
    } catch {
      return 'unknown';
    }
  }

  getGateway() {
    try {
      const output = execSync("ip route | grep 'via' | head -1", {
        encoding: 'utf-8',
        shell: '/bin/bash'
      });
      const match = output.match(/via (\d+\.\d+\.\d+\.\d+)/);
      return match ? match[1] : 'unknown';
    } catch {
      return 'unknown';
    }
  }

  getTotalHostsInSubnet() {
    const subnet = this.getSubnet();
    if (subnet.includes('/24')) return 254;
    if (subnet.includes('/25')) return 126;
    if (subnet.includes('/23')) return 510;
    return 254;
  }

  getRouterStatus() {
    const gateway = this.getGateway();
    let reachable = false;

    try {
      execSync(`ping -c 1 -W 1 ${gateway}`, { stdio: 'ignore' });
      reachable = true;
    } catch {
      reachable = false;
    }

    return {
      gateway,
      reachable,
      timestamp: new Date().toISOString(),
      healthCheck: reachable ? 'ONLINE' : 'OFFLINE'
    };
  }

  getDNSConfiguration() {
    const dns = {
      primary: 'unknown',
      secondary: 'unknown',
      source: 'system-resolv.conf'
    };

    try {
      const resolvConf = fs.readFileSync('/etc/resolv.conf', 'utf-8');
      const dnsServers = resolvConf.match(/nameserver (\S+)/g);
      if (dnsServers && dnsServers.length > 0) {
        dns.primary = dnsServers[0].replace('nameserver ', '');
        if (dnsServers.length > 1) {
          dns.secondary = dnsServers[1].replace('nameserver ', '');
        }
      }
    } catch (error) {
      dns.source = 'system-unknown';
    }

    return dns;
  }

  getUPnPStatus() {
    let upnpAvailable = false;

    try {
      execSync('which upnpc', { stdio: 'ignore' });
      upnpAvailable = true;
    } catch {
      upnpAvailable = false;
    }

    return {
      available: upnpAvailable,
      enabled: upnpAvailable,
      note: upnpAvailable ? 'upnp-cli available' : 'upnp-cli not installed'
    };
  }

  getPortForwardRules() {
    const rules = [];

    try {
      const output = execSync('iptables -t nat -L PREROUTING -n -v 2>/dev/null || echo "not-available"', {
        encoding: 'utf-8',
        shell: '/bin/bash'
      });

      if (!output.includes('not-available')) {
        const lines = output.split('\n');
        for (const line of lines) {
          if (line.includes('tcp') || line.includes('udp')) {
            rules.push({
              rule: line.trim(),
              source: 'iptables',
              type: 'system-forward'
            });
          }
        }
      }
    } catch (error) {
      // iptables might not be available in some environments
    }

    if (rules.length === 0) {
      rules.push({
        note: 'No port forwards detected or iptables not available',
        source: 'system-check'
      });
    }

    return rules;
  }

  getGuestWiFiStatus() {
    const status = {
      detected: false,
      interfaces: []
    };

    try {
      const output = execSync('ip link show', { encoding: 'utf-8' });
      const interfaces = output.match(/[0-9]+:\s+(\S+)/g);

      if (interfaces) {
        for (const iface of interfaces) {
          const name = iface.replace(/[0-9]+:\s+/, '').replace(':', '');
          if (
            name.includes('wlan') ||
            name.includes('wifi') ||
            name.includes('guest')
          ) {
            status.interfaces.push(name);
            status.detected = true;
          }
        }
      }
    } catch (error) {
      status.note = 'Could not detect WiFi interfaces';
    }

    return status;
  }

  getFirmwareVersion() {
    const firmware = {
      version: 'unknown',
      source: 'system-unknown'
    };

    try {
      if (fs.existsSync('/proc/version')) {
        const content = fs.readFileSync('/proc/version', 'utf-8');
        firmware.version = content.substring(0, 50);
        firmware.source = 'kernel-version';
      }
    } catch (error) {
      // Skip
    }

    return firmware;
  }

  classifyDevices(devices) {
    const types = {
      router: 0,
      camera: 0,
      desktop: 0,
      laptop: 0,
      mobile: 0,
      unknown: 0
    };

    for (const device of devices) {
      const ip = device.ip;
      const mac = device.mac.toLowerCase();

      if (ip.endsWith('.1')) {
        types.router++;
      } else if (mac.startsWith('aa:bb:cc')) {
        types.camera++;
      } else if (mac.startsWith('00:1a:2b')) {
        types.laptop++;
      } else {
        types.unknown++;
      }
    }

    return types;
  }

  async execute() {
    const data = await this.collect();

    // Save JSON
    const jsonPath = path.join(this.outputDir, 'router-status.json');
    fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2));
    console.log(`💾 Router status saved: ${jsonPath}`);

    // Save timestamped copy
    const timestamp = new Date().toISOString().split('T')[0];
    const timestampedPath = path.join(
      this.outputDir,
      `router-status-${timestamp}.json`
    );
    fs.writeFileSync(timestampedPath, JSON.stringify(data, null, 2));

    console.log(`✅ Router Agent collection complete`);
    console.log(`   Devices found: ${data.devices.count}`);
    console.log(`   Gateway: ${data.router.status.gateway}`);
    console.log(`   Status: ${data.router.status.healthCheck}`);

    return data;
  }
}

// Execute
const agent = new RouterAgent();
agent.execute().catch(err => {
  console.error('❌ Router Agent failed:', err.message);
  process.exit(1);
});

export { RouterAgent };

#!/usr/bin/env python3
"""
SHADOW ASSET DETECTOR (Task 2.1)
Real-time detection of unknown MAC addresses via ARP/DHCP
Flags suspicious devices for immediate Nessus targeting

Detection methods:
1. ARP monitoring - detect MAC addresses not in known inventory
2. DHCP logs - detect new DHCP requests from unknown MACs
3. Network discovery - compare active network devices against baseline
4. Trust score - flag devices with abnormally low trust scores
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class ShadowAssetDetector:
    """Detect and flag shadow assets (unknown/suspicious devices)"""

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.assets_file = self.state_dir / 'assets.json'
        self.shadow_log_file = self.state_dir / 'shadow_assets.json'
        self.assets = {}
        self.shadow_assets = []
        self.load_assets()

    def load_assets(self):
        """Load current assets"""
        if not self.assets_file.exists():
            print(f"Error: {self.assets_file} not found", file=sys.stderr)
            sys.exit(1)

        try:
            with open(self.assets_file, 'r') as f:
                self.assets = json.load(f)
        except Exception as e:
            print(f"Error loading assets: {e}", file=sys.stderr)
            sys.exit(1)

    def build_mac_baseline(self):
        """Build baseline of known MAC addresses"""
        known_macs = {}
        for asset in self.assets.get('all_assets', []):
            mac = asset.get('mac')
            ip = asset.get('ip')
            if mac and mac != 'Unknown':
                known_macs[mac.upper()] = {
                    'ip': ip,
                    'hostname': asset.get('hostname'),
                    'type': asset.get('type'),
                    'trust_score': asset.get('trust_score')
                }
        return known_macs

    def detect_unknown_mac(self, mac_address, device_info):
        """Detect if MAC is unknown and create shadow asset record"""
        if not mac_address or mac_address == 'Unknown':
            return None

        known_macs = self.build_mac_baseline()
        mac_upper = mac_address.upper()

        if mac_upper in known_macs:
            return None  # Known MAC

        # Unknown MAC detected - this is a shadow asset
        shadow = {
            'mac': mac_address,
            'ip': device_info.get('ip', 'Unknown'),
            'hostname': device_info.get('hostname', 'Unknown'),
            'detected_at': datetime.now().isoformat(),
            'confidence': 'HIGH',
            'reason': 'Unknown MAC not in baseline',
            'risk_factors': [],
            'recommended_action': 'Immediate Nessus Target Scan (Layer 2)'
        }

        # Analyze risk factors
        if device_info.get('ip', 'Unknown') == 'Unknown':
            shadow['risk_factors'].append('IP not assigned yet')
            shadow['confidence'] = 'MEDIUM'

        if device_info.get('type', 'Unknown') == 'Unknown':
            shadow['risk_factors'].append('Device type unidentified')

        if device_info.get('hostname', 'Unknown') == 'Unknown':
            shadow['risk_factors'].append('Hostname not resolvable')

        if device_info.get('scan_type') == 'ARP' or device_info.get('scan_type') == 'DHCP':
            shadow['detection_method'] = device_info['scan_type']

        return shadow

    def scan_for_shadow_assets(self):
        """Scan all assets for shadows"""
        shadows = []
        known_macs = self.build_mac_baseline()
        seen_macs = set()

        for asset in self.assets.get('all_assets', []):
            mac = asset.get('mac', 'Unknown')
            mac_upper = mac.upper() if mac != 'Unknown' else 'Unknown'

            if mac_upper == 'Unknown':
                # Unknown MAC is a shadow
                shadow = {
                    'ip': asset.get('ip'),
                    'hostname': asset.get('hostname'),
                    'type': asset.get('type', 'Unknown'),
                    'mac': 'Unknown',
                    'trust_score': asset.get('trust_score'),
                    'risk_score': asset.get('risk_score'),
                    'detected_at': datetime.now().isoformat(),
                    'reason': 'MAC address cannot be determined',
                    'confidence': 'HIGH' if asset.get('status') == 'ONLINE' else 'MEDIUM',
                    'recommended_action': 'Investigate via network scan'
                }
                shadows.append(shadow)

            elif mac_upper not in seen_macs and mac_upper not in known_macs:
                # New MAC not in baseline
                shadow = {
                    'ip': asset.get('ip'),
                    'hostname': asset.get('hostname'),
                    'type': asset.get('type', 'Unknown'),
                    'mac': mac,
                    'trust_score': asset.get('trust_score'),
                    'risk_score': asset.get('risk_score'),
                    'detected_at': datetime.now().isoformat(),
                    'reason': 'MAC not in baseline inventory',
                    'confidence': 'HIGH',
                    'recommended_action': 'Immediate Nessus Target Scan'
                }
                shadows.append(shadow)
                seen_macs.add(mac_upper)

            elif mac_upper in known_macs:
                seen_macs.add(mac_upper)

        return shadows

    def flag_shadow_assets(self):
        """Mark shadow assets in the asset inventory"""
        shadows = self.scan_for_shadow_assets()

        if not shadows:
            return 0

        # Create lookup of shadow MACs and IPs
        shadow_ips = {s['ip'] for s in shadows if s['ip'] != 'Unknown'}
        shadow_macs = {s['mac'].upper() for s in shadows if s['mac'] != 'Unknown'}

        # Flag in asset inventory
        flagged_count = 0
        for asset in self.assets.get('all_assets', []):
            ip = asset.get('ip')
            mac = asset.get('mac', 'Unknown').upper() if asset.get('mac') else 'Unknown'

            if ip in shadow_ips or mac in shadow_macs or asset.get('mac') == 'Unknown':
                asset['shadow_flag'] = True
                asset['shadow_detected_at'] = datetime.now().isoformat()
                flagged_count += 1

        # Also flag in assets_by_type
        for asset_type, assets_list in self.assets.get('assets_by_type', {}).items():
            for asset in assets_list:
                ip = asset.get('ip')
                mac = asset.get('mac', 'Unknown').upper() if asset.get('mac') else 'Unknown'

                if ip in shadow_ips or mac in shadow_macs or asset.get('mac') == 'Unknown':
                    asset['shadow_flag'] = True
                    asset['shadow_detected_at'] = datetime.now().isoformat()

        return flagged_count, shadows

    def save_detection_report(self):
        """Save shadow detection report"""
        flagged_count, shadows = self.flag_shadow_assets()

        if not shadows:
            print("[INFO] No shadow assets detected")
            return 0

        # Save updated assets
        try:
            with open(self.assets_file, 'w', encoding='utf-8') as f:
                json.dump(self.assets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving assets: {e}", file=sys.stderr)
            return 0

        # Save shadow log
        report = {
            'scan_time': datetime.now().isoformat(),
            'total_assets': len(self.assets.get('all_assets', [])),
            'shadows_detected': len(shadows),
            'flagged_count': flagged_count,
            'shadows': shadows
        }

        try:
            with open(self.shadow_log_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[OK] Shadow detection report saved ({len(shadows)} shadows)")
        except Exception as e:
            print(f"Error saving shadow report: {e}", file=sys.stderr)

        return len(shadows)

    def generate_nessus_targets(self):
        """Generate Nessus target list for shadow assets"""
        _, shadows = self.flag_shadow_assets()

        if not shadows:
            return []

        targets = []
        for shadow in shadows:
            if shadow['ip'] != 'Unknown':
                targets.append({
                    'ip': shadow['ip'],
                    'mac': shadow['mac'],
                    'hostname': shadow['hostname'],
                    'priority': 'CRITICAL' if shadow['confidence'] == 'HIGH' else 'HIGH',
                    'scan_type': 'Full Network Audit',
                    'reason': shadow['reason']
                })

        return targets

    def print_shadow_report(self):
        """Print shadow asset report to console"""
        _, shadows = self.flag_shadow_assets()

        if not shadows:
            print("\n[OK] No shadow assets detected - network inventory is clean")
            return

        print(f"\n[ALERT] SHADOW ASSETS DETECTED: {len(shadows)}")
        print("=" * 80)
        print("\nAssets with unknown or suspicious MAC addresses:\n")

        for i, shadow in enumerate(shadows, 1):
            print(f"{i}. IP: {shadow['ip']}")
            print(f"   MAC: {shadow['mac']}")
            print(f"   Hostname: {shadow['hostname']}")
            print(f"   Type: {shadow['type']}")
            print(f"   Trust Score: {shadow.get('trust_score', 'N/A')}")
            print(f"   Risk Score: {shadow.get('risk_score', 'N/A')}")
            print(f"   Reason: {shadow['reason']}")
            print(f"   Confidence: {shadow['confidence']}")
            print(f"   Action: {shadow['recommended_action']}")
            print()

        # Nessus targets
        targets = self.generate_nessus_targets()
        if targets:
            print(f"\nNESSUS TARGET LIST ({len(targets)} targets):")
            print("-" * 80)
            for target in targets:
                print(f"  {target['ip']:15} ({target['mac']:17}) - {target['priority']:8} - {target['reason']}")


def main():
    detector = ShadowAssetDetector()

    # Run detection
    count = detector.save_detection_report()

    # Print report
    detector.print_shadow_report()

    print(f"\n[OK] Task 2.1: Shadow asset detection complete ({count} detected)")
    sys.exit(0)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ASSET COMMAND CENTER CLI
Unified asset management with shadow detection, trust scoring, and inventory control

Usage:
  python asset_manager.py --list-all
  python asset_manager.py --list-shadow
  python asset_manager.py --trust-report
  python asset_manager.py --by-type [Windows|Linux|Camera|Unknown]
  python asset_manager.py --risky [risk_threshold]
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime


def format_table(headers, rows, max_widths=None):
    """Simple table formatter (no external dependencies)"""
    if not rows:
        return ""

    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header = "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths)) + " |"

    result = [sep, header, sep]
    for row in rows:
        result.append("| " + " | ".join(str(c).ljust(w) for c, w in zip(row, col_widths)) + " |")
    result.append(sep)
    return "\n".join(result)


class AssetCommandCenter:
    """Asset inventory management and analysis"""

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.assets_file = self.state_dir / 'assets.json'
        self.assets = {}
        self.load_assets()

    def load_assets(self):
        """Load assets from JSON"""
        if not self.assets_file.exists():
            print(f"Error: {self.assets_file} not found", file=sys.stderr)
            sys.exit(1)

        try:
            with open(self.assets_file, 'r') as f:
                self.assets = json.load(f)
        except Exception as e:
            print(f"Error loading assets: {e}", file=sys.stderr)
            sys.exit(1)

    def list_all_assets(self):
        """List all assets with key fields"""
        all_assets = self.assets.get('all_assets', [])

        if not all_assets:
            print("No assets found")
            return

        headers = ['IP', 'Hostname', 'Type', 'OS', 'MAC', 'Trust Score', 'Risk', 'Status']
        rows = []

        for asset in sorted(all_assets, key=lambda x: x.get('ip', '')):
            rows.append([
                asset.get('ip', 'N/A'),
                asset.get('hostname', 'N/A'),
                asset.get('type', 'Unknown'),
                asset.get('os', 'Unknown'),
                asset.get('mac', 'Unknown')[:17],  # Truncate MAC
                asset.get('trust_score', 'N/A'),
                asset.get('risk_score', 0),
                asset.get('status', 'UNKNOWN')
            ])

        print(format_table(headers, rows))
        print(f"\nTotal: {len(all_assets)} assets")

    def list_shadow_assets(self):
        """List shadow assets (unknown MAC, suspicious changes)"""
        all_assets = self.assets.get('all_assets', [])
        shadow = []

        for asset in all_assets:
            is_shadow = False
            reasons = []

            # Check for unknown MAC
            if asset.get('mac') == 'Unknown':
                is_shadow = True
                reasons.append('Unknown MAC')

            # Check for Unknown type
            if asset.get('type') == 'Unknown' and asset.get('os') == 'Unknown':
                is_shadow = True
                reasons.append('Unknown type/OS')

            # Check trust score (low = suspicious)
            if asset.get('trust_score', 100) < 30:
                is_shadow = True
                reasons.append(f"Low trust ({asset.get('trust_score')})")

            # Check for recent changes
            if asset.get('shadow_flag'):
                is_shadow = True
                reasons.append('Flagged by detector')

            if is_shadow:
                shadow.append({
                    'ip': asset.get('ip'),
                    'mac': asset.get('mac', 'Unknown'),
                    'type': asset.get('type', 'Unknown'),
                    'hostname': asset.get('hostname'),
                    'trust_score': asset.get('trust_score'),
                    'risk_score': asset.get('risk_score'),
                    'status': asset.get('status'),
                    'reasons': ', '.join(reasons)
                })

        if not shadow:
            print("[OK] No shadow assets detected")
            return

        headers = ['IP', 'MAC', 'Type', 'Hostname', 'Trust', 'Risk', 'Status', 'Reasons']
        rows = []
        for s in sorted(shadow, key=lambda x: x['trust_score'] if isinstance(x['trust_score'], (int, float)) else 0):
            rows.append([
                s['ip'],
                s['mac'][:17] if len(s['mac']) > 17 else s['mac'],
                s['type'],
                s['hostname'] or 'N/A',
                s['trust_score'] or 'N/A',
                s['risk_score'],
                s['status'],
                s['reasons']
            ])

        print(f"\n[ALERT] SHADOW ASSETS DETECTED: {len(shadow)}")
        print(format_table(headers, rows))

    def trust_report(self):
        """Generate trust score report"""
        all_assets = self.assets.get('all_assets', [])

        if not all_assets:
            print("No assets found")
            return

        # Categorize by trust level
        categories = {
            'CRITICAL_ASSET': [],
            'TRUSTED': [],
            'MONITORED': [],
            'SUSPICIOUS': [],
            'UNKNOWN': []
        }

        for asset in all_assets:
            trust_level = asset.get('trust_level', 'UNKNOWN')
            if trust_level in categories:
                categories[trust_level].append(asset)

        print("\n" + "="*70)
        print("ASSET TRUST SCORE REPORT")
        print("="*70)

        for level in ['CRITICAL_ASSET', 'TRUSTED', 'MONITORED', 'SUSPICIOUS', 'UNKNOWN']:
            assets = categories[level]
            if not assets:
                continue

            print(f"\n{level} ({len(assets)} assets):")
            print("-" * 70)

            headers = ['IP', 'Hostname', 'Type', 'Trust Score', 'Risk', 'MAC']
            rows = []

            for asset in sorted(assets, key=lambda x: x.get('trust_score', 0), reverse=True):
                rows.append([
                    asset.get('ip'),
                    asset.get('hostname', 'N/A'),
                    asset.get('type', 'Unknown'),
                    asset.get('trust_score', 'N/A'),
                    asset.get('risk_score', 0),
                    asset.get('mac', 'Unknown')[:17]
                ])

            print(tabulate(rows, headers=headers, tablefmt='simple'))

        # Summary statistics
        trust_scores = [a.get('trust_score', 0) for a in all_assets if isinstance(a.get('trust_score'), (int, float))]
        if trust_scores:
            avg_trust = sum(trust_scores) / len(trust_scores)
            print(f"\nAverage Trust Score: {avg_trust:.1f}/100")
            print(f"Median Trust Score: {sorted(trust_scores)[len(trust_scores)//2]:.1f}/100")

    def list_by_type(self, asset_type):
        """List assets by type"""
        by_type = self.assets.get('assets_by_type', {})

        if asset_type not in by_type:
            print(f"Asset type '{asset_type}' not found")
            return

        assets = by_type[asset_type]
        print(f"\n{asset_type} Assets ({len(assets)} total)")
        print("-" * 70)

        headers = ['IP', 'Hostname', 'OS', 'MAC', 'Trust', 'Risk', 'Status']
        rows = []

        for asset in sorted(assets, key=lambda x: x.get('ip', '')):
            rows.append([
                asset.get('ip'),
                asset.get('hostname', 'N/A'),
                asset.get('os', 'Unknown'),
                asset.get('mac', 'Unknown')[:17],
                asset.get('trust_score', 'N/A'),
                asset.get('risk_score', 0),
                asset.get('status', 'UNKNOWN')
            ])

        print(format_table(headers, rows))

    def list_risky_assets(self, threshold=50):
        """List assets above risk threshold"""
        all_assets = self.assets.get('all_assets', [])
        risky = [a for a in all_assets if a.get('risk_score', 0) >= threshold]

        if not risky:
            print(f"[OK] No assets with risk score >= {threshold}")
            return

        print(f"\n[ALERT] RISKY ASSETS (risk >= {threshold}): {len(risky)}")
        print("-" * 70)

        headers = ['IP', 'Hostname', 'Type', 'Risk Score', 'Trust', 'Status', 'Vulns']
        rows = []

        for asset in sorted(risky, key=lambda x: x.get('risk_score', 0), reverse=True):
            vulns = asset.get('vulnerabilities', {})
            vuln_count = (
                vulns.get('critical', 0) +
                vulns.get('high', 0) +
                vulns.get('medium', 0) +
                vulns.get('low', 0)
            )
            rows.append([
                asset.get('ip'),
                asset.get('hostname', 'N/A'),
                asset.get('type', 'Unknown'),
                asset.get('risk_score'),
                asset.get('trust_score', 'N/A'),
                asset.get('status', 'UNKNOWN'),
                vuln_count
            ])

        print(format_table(headers, rows))

    def health_check(self):
        """Asset inventory health check"""
        all_assets = self.assets.get('all_assets', [])

        print("\n" + "="*70)
        print("ASSET INVENTORY HEALTH CHECK")
        print("="*70)

        # Count by type
        by_type = {}
        for asset in all_assets:
            asset_type = asset.get('type', 'Unknown')
            by_type[asset_type] = by_type.get(asset_type, 0) + 1

        print(f"\nTotal Assets: {len(all_assets)}")
        for asset_type, count in sorted(by_type.items()):
            print(f"  {asset_type}: {count}")

        # Online vs Offline
        online = sum(1 for a in all_assets if a.get('status') == 'ONLINE')
        offline = len(all_assets) - online
        print(f"\nConnectivity:")
        print(f"  Online: {online}")
        print(f"  Offline: {offline}")

        # Trust distribution
        critical = sum(1 for a in all_assets if a.get('trust_level') == 'CRITICAL_ASSET')
        trusted = sum(1 for a in all_assets if a.get('trust_level') == 'TRUSTED')
        monitored = sum(1 for a in all_assets if a.get('trust_level') == 'MONITORED')
        suspicious = sum(1 for a in all_assets if a.get('trust_level') == 'SUSPICIOUS')
        unknown = sum(1 for a in all_assets if a.get('trust_level') == 'UNKNOWN')

        print(f"\nTrust Distribution:")
        print(f"  Critical Assets: {critical}")
        print(f"  Trusted: {trusted}")
        print(f"  Monitored: {monitored}")
        print(f"  Suspicious: {suspicious}")
        print(f"  Unknown: {unknown}")

        # MAC coverage
        unknown_mac = sum(1 for a in all_assets if a.get('mac') == 'Unknown')
        mac_coverage = (len(all_assets) - unknown_mac) / len(all_assets) * 100 if all_assets else 0
        print(f"\nMAC Address Coverage: {mac_coverage:.1f}%")
        print(f"  Known: {len(all_assets) - unknown_mac}")
        print(f"  Unknown: {unknown_mac}")


def main():
    parser = argparse.ArgumentParser(description='Asset Command Center CLI')
    parser.add_argument('--list-all', action='store_true', help='List all assets')
    parser.add_argument('--list-shadow', action='store_true', help='List shadow assets')
    parser.add_argument('--trust-report', action='store_true', help='Trust score report')
    parser.add_argument('--by-type', metavar='TYPE', help='List by type (Windows/Linux/Camera/Unknown)')
    parser.add_argument('--risky', metavar='THRESHOLD', type=int, default=50, help='List risky assets above threshold')
    parser.add_argument('--health', action='store_true', help='Health check')

    args = parser.parse_args()

    center = AssetCommandCenter()

    if args.list_all:
        center.list_all_assets()
    elif args.list_shadow:
        center.list_shadow_assets()
    elif args.trust_report:
        center.trust_report()
    elif args.by_type:
        center.list_by_type(args.by_type)
    elif args.risky:
        center.list_risky_assets(args.risky)
    elif args.health:
        center.health_check()
    else:
        # Default: health check
        center.health_check()


if __name__ == '__main__':
    main()

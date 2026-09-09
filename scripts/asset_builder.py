#!/usr/bin/env python3
"""
UNIFIED ASSET SCHEMA & TRUST SCORE ENGINE
Calculates asset trust_score (0-100) based on:
- MAC address consistency (40 points)
- IP stability (20 points)
- Service stability (15 points)
- Vulnerability trend (15 points)
- Discovery consistency (10 points)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


class TrustScoreEngine:
    """Calculate trust score for assets"""

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.assets_file = self.state_dir / 'assets.json'
        self.trust_history_file = self.state_dir / 'asset_trust_history.json'

    def load_assets(self):
        """Load current assets from JSON"""
        if not self.assets_file.exists():
            return {}
        try:
            with open(self.assets_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"Error loading assets: {e}", file=sys.stderr)
            return {}

    def load_trust_history(self):
        """Load historical trust data"""
        if not self.trust_history_file.exists():
            return defaultdict(lambda: {'mac_changes': 0, 'ip_changes': 0, 'first_seen': None, 'observations': 0})
        try:
            with open(self.trust_history_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception:
            return defaultdict(lambda: {'mac_changes': 0, 'ip_changes': 0, 'first_seen': None, 'observations': 0})

    def calculate_mac_consistency_score(self, asset, history):
        """40 points: MAC address consistency"""
        ip = asset.get('ip')
        mac = asset.get('mac', 'Unknown')

        if mac == 'Unknown':
            return 0  # Unknown MAC = 0 points

        asset_history = history.get(ip, {})
        mac_changes = asset_history.get('mac_changes', 0)

        # Penalty for MAC changes
        if mac_changes == 0:
            return 40  # Stable MAC
        elif mac_changes == 1:
            return 30  # One change (acceptable)
        elif mac_changes <= 3:
            return 20  # Few changes
        else:
            return max(0, 40 - (mac_changes * 5))  # Multiple changes = lower score

    def calculate_ip_stability_score(self, asset, history):
        """20 points: IP address stability"""
        ip = asset.get('ip')
        asset_history = history.get(ip, {})
        ip_changes = asset_history.get('ip_changes', 0)

        # Penalty for IP changes
        if ip_changes == 0:
            return 20  # Stable IP
        elif ip_changes == 1:
            return 15  # One change
        elif ip_changes <= 2:
            return 10  # Few changes
        else:
            return max(0, 20 - (ip_changes * 3))

    def calculate_service_stability_score(self, asset):
        """15 points: Service/port consistency"""
        # Based on consistent OS and device type detection
        asset_type = asset.get('type', 'Unknown')
        os = asset.get('os', 'Unknown')

        if asset_type == 'Unknown' and os == 'Unknown':
            return 0  # Unknown device = 0 points

        if asset_type in ['Windows', 'Linux', 'Camera']:
            if os and os != 'Unknown':
                return 15  # Consistent OS = 15 points
            else:
                return 10  # Type but unknown OS
        else:
            return 5  # Partial identification

    def calculate_vulnerability_trend_score(self, asset, history):
        """15 points: Vulnerability trend stability"""
        asset_history = history.get(asset.get('ip'), {})
        risk_history = asset_history.get('risk_scores', [])

        current_risk = asset.get('risk_score', 0)

        if len(risk_history) == 0:
            # First observation - neutral
            return 8

        # Check if risk is stable or improving
        avg_past_risk = sum(risk_history[-10:]) / len(risk_history[-10:]) if risk_history else 0

        if current_risk <= avg_past_risk * 1.1:  # Within 10% of average
            return 15  # Stable or improving
        elif current_risk <= avg_past_risk * 1.5:  # Within 50%
            return 10  # Some increase
        else:
            return max(0, 15 - (current_risk - avg_past_risk))  # Degrading

    def calculate_discovery_consistency_score(self, asset, history):
        """10 points: Consistent discovery across scans"""
        ip = asset.get('ip')
        asset_history = history.get(ip, {})
        observations = asset_history.get('observations', 1)

        status = asset.get('status', 'UNKNOWN')

        if status != 'ONLINE':
            return 0  # Offline/unknown = 0 points

        # More observations = higher consistency
        if observations >= 10:
            return 10  # Consistently discovered
        elif observations >= 5:
            return 8
        elif observations >= 3:
            return 5
        else:
            return 2  # Few observations

    def calculate_trust_score(self, asset, history):
        """Calculate overall trust score (0-100)"""
        score = (
            self.calculate_mac_consistency_score(asset, history) +
            self.calculate_ip_stability_score(asset, history) +
            self.calculate_service_stability_score(asset) +
            self.calculate_vulnerability_trend_score(asset, history) +
            self.calculate_discovery_consistency_score(asset, history)
        )

        return min(100, max(0, score))  # Clamp to 0-100

    def determine_trust_level(self, score):
        """Convert score to trust level"""
        if score >= 85:
            return 'CRITICAL_ASSET'  # Known, stable, important
        elif score >= 70:
            return 'TRUSTED'
        elif score >= 50:
            return 'MONITORED'
        elif score >= 30:
            return 'SUSPICIOUS'
        else:
            return 'UNKNOWN'

    def upgrade_schema(self):
        """Add trust_score and related fields to assets"""
        assets_data = self.load_assets()

        if not assets_data or 'all_assets' not in assets_data:
            print("Error: Invalid assets.json format", file=sys.stderr)
            return False

        history = self.load_trust_history()
        now = datetime.now().isoformat()

        # Upgrade all_assets
        for asset in assets_data.get('all_assets', []):
            ip = asset.get('ip')

            # Initialize history if needed
            if ip not in history:
                history[ip] = {
                    'mac_changes': 0,
                    'ip_changes': 0,
                    'first_seen': now,
                    'observations': 1,
                    'risk_scores': [asset.get('risk_score', 0)]
                }
            else:
                history[ip]['observations'] += 1
                if 'risk_scores' not in history[ip]:
                    history[ip]['risk_scores'] = []
                history[ip]['risk_scores'].append(asset.get('risk_score', 0))

            # Calculate trust score
            trust_score = self.calculate_trust_score(asset, history)

            # Add new fields
            asset['trust_score'] = trust_score
            asset['trust_level'] = self.determine_trust_level(trust_score)
            asset['shadow_flag'] = False  # Will be updated by change_detector
            asset['first_seen'] = history[ip].get('first_seen', now)
            asset['last_change_time'] = asset.get('last_updated', now)

        # Upgrade assets_by_type
        for asset_type, assets_list in assets_data.get('assets_by_type', {}).items():
            for asset in assets_list:
                ip = asset.get('ip')
                trust_score = self.calculate_trust_score(asset, history)
                asset['trust_score'] = trust_score
                asset['trust_level'] = self.determine_trust_level(trust_score)
                asset['shadow_flag'] = False
                asset['first_seen'] = history[ip].get('first_seen', now)
                asset['last_change_time'] = asset.get('last_updated', now)

        # Save upgraded assets
        try:
            with open(self.assets_file, 'w', encoding='utf-8') as f:
                json.dump(assets_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Upgraded {len(assets_data.get('all_assets', []))} assets with trust_score")
        except Exception as e:
            print(f"Error saving assets: {e}", file=sys.stderr)
            return False

        # Save trust history
        try:
            with open(self.trust_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            print(f"[OK] Saved trust history for {len(history)} assets")
        except Exception as e:
            print(f"Error saving trust history: {e}", file=sys.stderr)
            return False

        return True


def main():
    engine = TrustScoreEngine()
    if engine.upgrade_schema():
        print("\n[SUCCESS] Task 1.1: Schema upgrade complete")
        sys.exit(0)
    else:
        print("\n[FAILED] Schema upgrade failed", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

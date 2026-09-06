#!/usr/bin/env python3
"""
CONTROL BASELINE LAYER (Phase N.10A)
Tái sử dụng logic từ Home SOC
Quản lý baseline trạng thái điều khiển và phát hiện drift
Outputs: state/baseline_controls.json, state/control_drift.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class BaselineControls:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.baseline_file = self.state_dir / 'baseline_controls.json'
        self.drift_file = self.state_dir / 'control_drift.json'

    def load_state(self, filename):
        """Tải state file"""
        fp = self.state_dir / filename
        if fp.exists():
            try:
                return json.load(open(fp, encoding='utf-8'))
            except:
                return {}
        return {}

    def load_baseline(self):
        """Tải baseline hiện tại"""
        if self.baseline_file.exists():
            try:
                return json.load(open(self.baseline_file, encoding='utf-8'))
            except:
                return None
        return None

    def extract_control_state(self):
        """Trích xuất trạng thái điều khiển từ collectors"""

        # Defender
        defender = self.load_state('defender_status.json')
        defender_enabled = defender.get('enabled', False)
        defender_threats = defender.get('threat_count', 0)

        # Firewall
        firewall = self.load_state('firewall_status.json')
        firewall_enabled = firewall.get('enabled', False)

        # System Health
        health = self.load_state('system_health.json')
        cpu_usage = health.get('cpu_usage', 0)
        disk_usage = health.get('disk_usage', 0)
        memory_usage = health.get('memory_usage', 0)

        # WAAP
        waap = self.load_state('waap_status.json')
        waap_score = waap.get('score', 50)

        # Assets
        assets = self.load_state('assets.json')
        asset_count = len(assets.get('assets', []))

        # Services
        services = self.load_state('services.json')
        service_count = len(services.get('services', []))

        # Risk Score
        risk = self.load_state('risk_score.json')
        risk_level = risk.get('risk_level', 'UNKNOWN')
        risk_score = risk.get('overall_score', 0)

        return {
            'defender': {
                'enabled': defender_enabled,
                'threat_count': defender_threats,
                'status': 'enabled' if defender_enabled else 'disabled'
            },
            'firewall': {
                'enabled': firewall_enabled,
                'status': 'enabled' if firewall_enabled else 'disabled'
            },
            'waap': {
                'score': waap_score,
                'status': 'healthy' if waap_score >= 70 else 'degraded' if waap_score >= 50 else 'critical'
            },
            'health': {
                'cpu_usage': cpu_usage,
                'disk_usage': disk_usage,
                'memory_usage': memory_usage,
                'status': 'healthy' if cpu_usage < 80 and disk_usage < 90 else 'degraded'
            },
            'assets': {
                'count': asset_count,
                'status': 'stable'
            },
            'services': {
                'count': service_count,
                'status': 'stable'
            },
            'risk': {
                'level': risk_level,
                'score': risk_score
            }
        }

    def initialize_baseline(self):
        """Khởi tạo baseline lần đầu"""
        current_state = self.extract_control_state()

        baseline = {
            'schema_version': '1.0',
            'baseline_id': f"BL-{datetime.now().strftime('%Y-%m-%d')}",
            'created_at': datetime.now().isoformat(),
            'approved_at': datetime.now().isoformat(),
            'controls': current_state,
            'note': 'Baseline khởi tạo'
        }

        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)

        return baseline

    def detect_control_drift(self):
        """Phát hiện sự thay đổi so với baseline"""

        baseline = self.load_baseline()
        if not baseline:
            # Lần đầu - khởi tạo baseline
            baseline = self.initialize_baseline()

        current_state = self.extract_control_state()
        baseline_controls = baseline.get('controls', {})

        drifts = []

        # So sánh Defender
        baseline_defender_enabled = baseline_controls.get('defender', {}).get('enabled', False)
        current_defender_enabled = current_state.get('defender', {}).get('enabled', False)
        if baseline_defender_enabled != current_defender_enabled:
            drifts.append({
                'control': 'defender',
                'type': 'STATE_CHANGE',
                'severity': 'CRITICAL',
                'old_value': 'enabled' if baseline_defender_enabled else 'disabled',
                'new_value': 'enabled' if current_defender_enabled else 'disabled',
                'description': f"Defender thay đổi từ {'bật' if baseline_defender_enabled else 'tắt'} sang {'bật' if current_defender_enabled else 'tắt'}",
                'detected_at': datetime.now().isoformat()
            })

        # So sánh Firewall
        baseline_firewall_enabled = baseline_controls.get('firewall', {}).get('enabled', False)
        current_firewall_enabled = current_state.get('firewall', {}).get('enabled', False)
        if baseline_firewall_enabled != current_firewall_enabled:
            drifts.append({
                'control': 'firewall',
                'type': 'STATE_CHANGE',
                'severity': 'CRITICAL',
                'old_value': 'enabled' if baseline_firewall_enabled else 'disabled',
                'new_value': 'enabled' if current_firewall_enabled else 'disabled',
                'description': f"Firewall thay đổi từ {'bật' if baseline_firewall_enabled else 'tắt'} sang {'bật' if current_firewall_enabled else 'tắt'}",
                'detected_at': datetime.now().isoformat()
            })

        # So sánh WAAP Score
        baseline_waap = baseline_controls.get('waap', {}).get('score', 50)
        current_waap = current_state.get('waap', {}).get('score', 50)
        waap_delta = baseline_waap - current_waap
        if abs(waap_delta) >= 20:  # 20 điểm hoặc hơn
            severity = 'HIGH' if waap_delta >= 30 else 'MEDIUM'
            drifts.append({
                'control': 'waap',
                'type': 'SCORE_CHANGE',
                'severity': severity,
                'old_value': baseline_waap,
                'new_value': current_waap,
                'delta': waap_delta,
                'description': f"WAAP score giảm từ {baseline_waap} xuống {current_waap} (Δ {waap_delta:+d})",
                'detected_at': datetime.now().isoformat()
            })

        # So sánh Risk Level
        baseline_risk = baseline_controls.get('risk', {}).get('level', 'UNKNOWN')
        current_risk = current_state.get('risk', {}).get('level', 'UNKNOWN')

        risk_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        baseline_risk_val = risk_order.get(baseline_risk, 0)
        current_risk_val = risk_order.get(current_risk, 0)

        if current_risk_val > baseline_risk_val:
            drifts.append({
                'control': 'risk_level',
                'type': 'ESCALATION',
                'severity': 'HIGH',
                'old_value': baseline_risk,
                'new_value': current_risk,
                'description': f"Risk level tăng từ {baseline_risk} lên {current_risk}",
                'detected_at': datetime.now().isoformat()
            })

        # So sánh Asset Count (phát hiện thiết bị mới)
        baseline_assets = baseline_controls.get('assets', {}).get('count', 0)
        current_assets = current_state.get('assets', {}).get('count', 0)
        asset_delta = current_assets - baseline_assets
        if asset_delta != 0:
            severity = 'MEDIUM' if asset_delta > 0 else 'LOW'
            drifts.append({
                'control': 'asset_count',
                'type': 'COUNT_CHANGE',
                'severity': severity,
                'old_value': baseline_assets,
                'new_value': current_assets,
                'delta': asset_delta,
                'description': f"Số thiết bị thay đổi từ {baseline_assets} sang {current_assets} (Δ {asset_delta:+d})",
                'detected_at': datetime.now().isoformat()
            })

        # So sánh Service Count
        baseline_services = baseline_controls.get('services', {}).get('count', 0)
        current_services = current_state.get('services', {}).get('count', 0)
        service_delta = current_services - baseline_services
        if service_delta != 0:
            severity = 'MEDIUM' if service_delta > 0 else 'LOW'
            drifts.append({
                'control': 'service_count',
                'type': 'COUNT_CHANGE',
                'severity': severity,
                'old_value': baseline_services,
                'new_value': current_services,
                'delta': service_delta,
                'description': f"Số dịch vụ thay đổi từ {baseline_services} sang {current_services} (Δ {service_delta:+d})",
                'detected_at': datetime.now().isoformat()
            })

        return drifts, current_state

    def generate_drift_report(self):
        """Tạo báo cáo drift"""
        drifts, current_state = self.detect_control_drift()

        # Thống kê drift
        by_severity = {}
        for drift in drifts:
            severity = drift.get('severity', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Tạo output
        output = {
            'timestamp': datetime.now().isoformat(),
            'schema_version': '1.0',
            'baseline_id': self.load_baseline().get('baseline_id', 'UNKNOWN'),
            'drifts_detected': len(drifts),
            'by_severity': by_severity,
            'drifts': drifts,
            'current_state': current_state,
            'has_critical_drift': any(d.get('severity') == 'CRITICAL' for d in drifts),
            'control_status_summary': {
                'defender': 'OK' if not any(d['control'] == 'defender' for d in drifts) else '⚠ DRIFT',
                'firewall': 'OK' if not any(d['control'] == 'firewall' for d in drifts) else '⚠ DRIFT',
                'waap': 'OK' if not any(d['control'] == 'waap' for d in drifts) else '⚠ DRIFT',
                'risk': 'STABLE' if not any(d['control'] == 'risk_level' for d in drifts) else '⚠ ESCALATED',
                'assets': 'STABLE' if not any(d['control'] == 'asset_count' for d in drifts) else '⚠ CHANGED',
                'services': 'STABLE' if not any(d['control'] == 'service_count' for d in drifts) else '⚠ CHANGED'
            }
        }

        # Lưu drift report
        with open(self.drift_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    def run(self):
        """Chạy baseline comparison"""
        report = self.generate_drift_report()

        return {
            'status': 'success',
            'drifts_detected': report['drifts_detected'],
            'by_severity': report['by_severity'],
            'has_critical_drift': report['has_critical_drift'],
            'control_status': report['control_status_summary']
        }

if __name__ == '__main__':
    baseline = BaselineControls()
    result = baseline.run()
    # Avoid unicode encoding issues on Windows by using ensure_ascii=True
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + '\n')
    sys.exit(0 if result.get('status') == 'success' else 1)

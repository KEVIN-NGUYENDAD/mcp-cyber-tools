#!/usr/bin/env python3
"""
CANONICAL RISK ENGINE (Sprint 6 - Risk Engine Consolidation)

Đây là engine DUY NHẤT được phép ghi state/risk_score.json.
`risk_engine.py` đã bị loại bỏ; xem docs/project/RISK_SCORING_MODEL.md.

Thang điểm: overall_score là RỦI RO tăng dần - điểm cao = nguy hiểm hơn.
  0-39 LOW | 40-59 MEDIUM | 60-79 HIGH | 80-100 CRITICAL

Mỗi thành phần tự chấm "sức khoẻ" 0-100 (cao = tốt), engine lấy trung bình có
trọng số rồi đảo thành rủi ro: overall_score = 100 - weighted_health.

Input:  state/assets.json, incidents.json, crypto_inventory.json, waap_score.json,
        defender_status.json, firewall_status.json, security_events.json,
        hunting_persistence.json, hunting_suspicious_processes.json,
        hunting_lateral_movement.json, hunting_credential_dumping.json
Output: state/risk_score.json (atomic write)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Import atomic write functions for file safety (TD-L3-001, TD-L3-002, TD-L3-003)
from state_manager import write_state_atomic, read_state_safe

ENGINE_VERSION = '2.0.0'
SCALE = 'risk_ascending'

# Trọng số. Bốn tiêu chí bắt buộc của Sprint 6 - Asset Risk, IOC, Hunting
# Findings, Incident Severity - chiếm 70%; hạ tầng phòng thủ chiếm 30%.
WEIGHTS = {
    'threat_hunting': 0.25,   # IOC + hunting findings
    'incidents': 0.25,        # incident severity
    'asset': 0.20,            # asset risk (Nessus)
    'waap': 0.10,
    'crypto': 0.06,
    'defender': 0.06,
    'firewall': 0.04,
    'security_events': 0.04,
}

HUNTING_FILES = [
    'hunting_persistence.json',
    'hunting_suspicious_processes.json',
    'hunting_lateral_movement.json',
    'hunting_credential_dumping.json',
]

# Mức trừ điểm sức khoẻ theo từng loại hunting. Credential dumping và lateral
# movement nặng hơn vì chúng là bước mở rộng xâm nhập, không phải dấu hiệu đơn lẻ.
HUNTING_PENALTY = {
    'hunting_persistence.json': {'CRITICAL': 25, 'HIGH': 15},
    'hunting_suspicious_processes.json': {'CRITICAL': 20, 'HIGH': 10},
    'hunting_lateral_movement.json': {'CRITICAL': 30, 'HIGH': 12},
    'hunting_credential_dumping.json': {'CRITICAL': 35, 'HIGH': 15},
}


def risk_level_from_score(score):
    """Thang rủi ro tăng dần - khớp với mọi consumer (portal, server, Telegram)."""
    if score >= 80:
        return 'CRITICAL'
    if score >= 60:
        return 'HIGH'
    if score >= 40:
        return 'MEDIUM'
    return 'LOW'


class RiskScoreCalculator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.factors = []
        self.notes = []
        self.coverage_blind_sources = []

    def load_state(self, filename):
        return read_state_safe(self.state_dir / filename, dict)

    # ------------------------------------------------------------------
    # COMPONENT HEALTH (0-100, cao = tốt)
    # ------------------------------------------------------------------

    def analyze_assets(self):
        assets = self.load_state('assets.json')
        crit, high = 0, 0
        for asset in assets.get('assets', []) or []:
            crit += asset.get('critical', 0) or 0
            high += asset.get('high', 0) or 0
        score = max(0, 100 - crit * 15 - high * 8)
        detail = '{} lỗ hổng CRITICAL, {} HIGH trên {} tài sản'.format(
            crit, high, len(assets.get('assets', []) or []))
        return score, detail, {'critical': crit, 'high': high}

    def analyze_incidents(self):
        """Thành phần mới của Sprint 6 - trước đây không engine nào đọc incidents."""
        incidents = self.load_state('incidents.json')
        by_severity = incidents.get('by_severity') or {}
        crit = by_severity.get('CRITICAL', 0) or 0
        high = by_severity.get('HIGH', 0) or 0
        score = max(0, 100 - crit * 15 - high * 6)
        detail = '{} sự cố CRITICAL, {} HIGH đang mở'.format(crit, high)
        return score, detail, {'critical': crit, 'high': high}

    def analyze_crypto(self):
        crypto = self.load_state('crypto_inventory.json')
        score = crypto.get('score', 50)
        return score, 'crypto inventory score {}'.format(score), {}

    def analyze_waap(self):
        waap = self.load_state('waap_score.json')
        score = waap.get('score', 50)
        return score, 'WAAP score {}'.format(score), {}

    def analyze_defender(self):
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled'):
            return 20, 'Defender đang TẮT', {}
        threats = defender.get('threat_count', 0) or 0
        if threats > 0:
            return max(0, 100 - threats * 10), '{} threat chưa xử lý'.format(threats), {}
        return 100, 'Defender bật, 0 threat', {}

    def analyze_firewall(self):
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled'):
            return 20, 'Firewall đang TẮT', {}
        return 90, 'Firewall bật', {}

    def analyze_security_events(self):
        events = self.load_state('security_events.json')
        failed = events.get('failed_logons', 0) or 0
        critical_events = events.get('critical_events', 0) or 0
        warnings = events.get('warning_events', 0) or 0
        score = max(0, 100 - failed - critical_events * 20 - warnings * 2)
        detail = '{} đăng nhập thất bại, {} sự kiện CRITICAL, {} cảnh báo'.format(
            failed, critical_events, warnings)
        return score, detail, {}

    def analyze_threat_hunting(self):
        """IOC từ cả 4 nguồn hunting."""
        score = 100
        crit_total, high_total = 0, 0
        parts = []
        simulated_sources = []
        blind_sources = []

        for filename in HUNTING_FILES:
            data = self.load_state(filename)
            if not data:
                continue

            coverage = data.get('coverage') or {}
            if coverage and not coverage.get('observable', True):
                # Trục này đang mù. Trung bình có trọng số sẽ coi 0 phát hiện là
                # 100 điểm sức khoẻ - tức là thưởng điểm cho việc không nhìn thấy.
                blind_sources.append((filename, coverage.get('reason') or ''))

            by_severity = data.get('by_severity') or {}
            crit = by_severity.get('CRITICAL', 0) or 0
            high = by_severity.get('HIGH', 0) or 0
            if crit == 0 and high == 0:
                continue

            penalty = HUNTING_PENALTY[filename]
            score -= crit * penalty['CRITICAL']
            score -= high * penalty['HIGH']
            crit_total += crit
            high_total += high

            # Sprint 6.1: nguồn hunting tự khai data_source. Điểm KHÔNG đổi theo
            # trường này - đổi cách chấm là quyết định chính sách, không phải hệ
            # quả của việc gắn nhãn - nhưng nhãn phải đi cùng con số tới mọi nơi
            # đọc nó, nếu không người xem tưởng 25% trọng số này là quan sát thật.
            simulated = data.get('data_source') == 'SIMULATED'
            if simulated:
                simulated_sources.append(filename)
            parts.append('{}: {}C/{}H{}'.format(
                filename.replace('hunting_', '').replace('.json', ''),
                crit, high, ' [MÔ PHỎNG]' if simulated else ''))

        score = max(0, score)
        detail = '; '.join(parts) if parts else 'không có IOC CRITICAL/HIGH'

        if blind_sources:
            names = ', '.join(f.replace('hunting_', '').replace('.json', '')
                              for f, _ in blind_sources)
            detail += ' | KHÔNG QUAN SÁT ĐƯỢC: {}'.format(names)
            self.notes.append(
                'Vùng mù giám sát: {}/{} nguồn hunting không đọc được nguồn dữ liệu '
                '({}). 0 phát hiện ở các nguồn này KHÔNG có nghĩa là sạch - '
                'điểm rủi ro đang lạc quan hơn thực tế. Lý do: {}'
                .format(len(blind_sources), len(HUNTING_FILES), names,
                        blind_sources[0][1]))

        if simulated_sources:
            self.notes.append(
                'Cảnh báo dữ liệu: {}/{} nguồn hunting mang data_source=SIMULATED '
                '({}). Chúng đóng góp {}% trọng số rủi ro và {} phát hiện CRITICAL '
                'kích hoạt severity floor, nhưng KHÔNG phải quan sát từ máy thật.'
                .format(len(simulated_sources), len(HUNTING_FILES),
                        ', '.join(s.replace('hunting_', '').replace('.json', '')
                                  for s in simulated_sources),
                        int(WEIGHTS['threat_hunting'] * 100), crit_total))
        return score, detail, {'critical': crit_total, 'high': high_total,
                               'simulated_sources': simulated_sources,
                               'blind_sources': [f for f, _ in blind_sources]}

    # ------------------------------------------------------------------

    def calculate(self):
        analyzers = [
            ('threat_hunting', self.analyze_threat_hunting),
            ('incidents', self.analyze_incidents),
            ('asset', self.analyze_assets),
            ('waap', self.analyze_waap),
            ('crypto', self.analyze_crypto),
            ('defender', self.analyze_defender),
            ('firewall', self.analyze_firewall),
            ('security_events', self.analyze_security_events),
        ]

        component_scores = {}
        weighted_health = 0.0
        critical_count = 0
        high_count = 0

        for name, analyzer in analyzers:
            health, detail, counts = analyzer()
            health = max(0, min(100, int(health)))
            weight = WEIGHTS[name]

            component_scores[name] = health
            weighted_health += weight * health

            # critical_count/high_count đếm PHÁT HIỆN (incidents + hunting),
            # không đếm lỗ hổng Nessus - hai thứ khác đơn vị, cộng vào là sai.
            if name in ('incidents', 'threat_hunting'):
                critical_count += counts.get('critical', 0)
                high_count += counts.get('high', 0)

            if counts.get('blind_sources'):
                self.coverage_blind_sources = counts['blind_sources']

            self.factors.append({
                'name': name,
                'health': health,
                'weight': weight,
                'risk_contribution': round(weight * (100 - health), 2),
                'detail': detail,
            })

        overall_score = int(round(100 - weighted_health))
        overall_score = max(0, min(100, overall_score))
        risk_level = risk_level_from_score(overall_score)

        # Sàn nghiêm trọng: trung bình có trọng số làm loãng sự cố CRITICAL.
        # Đây chính là lỗi đã khiến Risk Score = 1 trong khi có 7 CRITICAL.
        # Còn sự cố CRITICAL đang mở thì mức rủi ro không được thấp hơn HIGH.
        if critical_count > 0 and risk_level in ('LOW', 'MEDIUM'):
            self.notes.append(
                'Severity floor áp dụng: {} phát hiện CRITICAL nâng risk_level từ {} lên HIGH'
                .format(critical_count, risk_level))
            risk_level = 'HIGH'

        # Sàn vùng mù: không thể khẳng định "rủi ro THẤP" về những thứ không
        # nhìn thấy. Khi một nguồn hunting không đọc được, 0 phát hiện của nó
        # được phép tính là 100 điểm sức khoẻ - tức là hệ thống tự thưởng điểm
        # cho việc bị mù. Ghi chú thôi thì không đủ: thứ người trực ca nhìn trên
        # bảng điều khiển là chữ LOW, không phải dòng notes bên dưới.
        blind = self.coverage_blind_sources
        if blind and risk_level == 'LOW':
            self.notes.append(
                'Coverage floor áp dụng: {} nguồn hunting đang mù ({}), nên '
                'risk_level nâng từ LOW lên MEDIUM. Không khẳng định được rủi ro '
                'thấp khi chưa quan sát được. overall_score giữ nguyên.'
                .format(len(blind), ', '.join(
                    b.replace('hunting_', '').replace('.json', '') for b in blind)))
            risk_level = 'MEDIUM'

        self.factors.sort(key=lambda f: f['risk_contribution'], reverse=True)

        output = {
            # --- schema chuẩn Sprint 6 ---
            'overall_score': overall_score,
            'risk_level': risk_level,
            'critical_count': critical_count,
            'high_count': high_count,
            'factors': self.factors,
            'generated_at': datetime.now().isoformat(),

            # --- metadata ---
            'engine': 'calculate_risk_score',
            'engine_version': ENGINE_VERSION,
            'scale': SCALE,
            'scale_description': 'overall_score cao = rủi ro cao (0 an toàn nhất, 100 nguy hiểm nhất)',
            'notes': self.notes,

            # --- tương thích ngược: consumer cũ vẫn đọc được ---
            'timestamp': datetime.now().isoformat(),
            'threat_level': risk_level,
            'component_scores': component_scores,
            'weights': dict(WEIGHTS),
        }

        write_state_atomic(str(self.state_dir / 'risk_score.json'), output, indent=2)

        return {
            'status': 'success',
            'overall_score': overall_score,
            'risk_level': risk_level,
            'critical_count': critical_count,
            'high_count': high_count,
            'scale': SCALE,
        }


if __name__ == '__main__':
    calc = RiskScoreCalculator()
    result = calc.calculate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)

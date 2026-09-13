#!/usr/bin/env python3
"""
EXECUTIVE CORRELATION ENGINE (Sprint 5)
Tương quan đa nguồn giữa asset inventory, shadow assets, incidents và threat hunting.

Không thu thập dữ liệu mới - chỉ đọc state/ đã có và sinh ra Executive Findings
ở mức "so what?": mỗi finding là một kết luận liên kết nhiều nguồn, không phải
một IOC đơn lẻ.

Populates: state/executive_findings.json
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Atomic write / safe read (TD-L3-001, TD-L3-002, TD-L3-003)
from state_manager import write_state_atomic, read_state_safe

ENGINE_VERSION = '1.0.0'

# Các nguồn mà engine đọc. Thiếu tệp nào thì rule liên quan báo gap, không crash.
SOURCE_FILES = [
    'assets.json',
    'shadow_assets.json',
    'incidents.json',
    'defender_status.json',
    'security_events.json',
    'hunting_persistence.json',
    'hunting_credential_dumping.json',
    'hunting_lateral_movement.json',
    'hunting_suspicious_processes.json',
]

IPV4_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

# Ngưỡng cho Rule 2. Mặc định bảo thủ: 3 lần đăng nhập thất bại trong 24h
# là mức thấp nhất còn đáng ghép với dấu hiệu lateral movement.
FAILED_LOGON_THRESHOLD = 3

SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}


def extract_ips(value):
    """Trích mọi IPv4 hợp lệ từ một giá trị JSON bất kỳ (str/list/dict/scalar)."""
    found = set()

    if isinstance(value, str):
        for candidate in IPV4_RE.findall(value):
            octets = candidate.split('.')
            if all(0 <= int(o) <= 255 for o in octets):
                found.add(candidate)
    elif isinstance(value, dict):
        for item in value.values():
            found |= extract_ips(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found |= extract_ips(item)

    return found


class CorrelationEngine:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.state_dir = self.project_root / 'state'
        self.output_file = self.state_dir / 'executive_findings.json'

        self.state = {}
        self.sources = {}
        self.findings = []
        self.coverage_gaps = []
        self._seq = 0

    # ------------------------------------------------------------------
    # LOADING
    # ------------------------------------------------------------------

    def load_sources(self):
        """Đọc an toàn toàn bộ nguồn qua state_manager.read_state_safe."""
        for filename in SOURCE_FILES:
            path = self.state_dir / filename
            data = read_state_safe(path, dict)
            self.state[filename] = data

            records = 0
            if isinstance(data, dict):
                for key in ('indicators', 'incidents', 'assets', 'shadows'):
                    if isinstance(data.get(key), list):
                        records = len(data[key])
                        break

            self.sources[filename] = {
                'present': path.exists(),
                'records': records,
                'timestamp': data.get('timestamp') if isinstance(data, dict) else None,
            }

    def indicators(self, filename):
        data = self.state.get(filename) or {}
        items = data.get('indicators')
        return items if isinstance(items, list) else []

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def next_finding_id(self):
        self._seq += 1
        return 'EF-{:04d}'.format(self._seq)

    def add_finding(self, rule_id, rule_name, severity, title, summary,
                    entities, evidence, recommended_action, confidence, sources,
                    evidence_quality='REAL'):
        # evidence_quality tách "mức nghiêm trọng nếu có thật" khỏi "có thật hay
        # không". Người trực ca cần thấy cả hai trước khi đi cô lập một thiết bị.
        self.findings.append({
            'finding_id': self.next_finding_id(),
            'rule_id': rule_id,
            'rule_name': rule_name,
            'severity': severity,
            'title': title,
            'summary': summary,
            'entities': entities,
            'evidence': evidence,
            'recommended_action': recommended_action,
            'confidence': confidence,
            'evidence_quality': evidence_quality,
            'sources': sources,
            'detected_at': datetime.now().isoformat(),
        })

    def add_gap(self, rule_id, reason, detail):
        """Ghi lại lý do một rule không thể kết luận, thay vì im lặng trả 0."""
        self.coverage_gaps.append({
            'rule_id': rule_id,
            'reason': reason,
            'detail': detail,
        })

    # Các trường mô tả *phạm vi săn*, không phải *bằng chứng*. Quét IP trong đây
    # sẽ quy kết mọi chỉ báo cho mọi máy trong tầm — đúng kiểu sai lầm mà
    # Sprint 6.1 sinh ra để ngăn.
    SCOPE_FIELDS = ('hunt_scope', 'attribution', 'data_source')

    @staticmethod
    def is_simulated(indicator):
        return indicator.get('data_source') == 'SIMULATED'

    def indicator_ips(self, indicator):
        """IP gắn với một IOC.

        Sprint 6.1: chỉ báo mô phỏng KHÔNG bao giờ sinh ra quy kết thiết bị.
        Trước đây hàm này quét toàn bộ dict, nên bất kỳ IP nào lọt vào chỉ báo -
        kể cả IP hardcode hay IP của phạm vi săn - đều thành "bằng chứng".
        """
        if self.is_simulated(indicator):
            return set()

        ips = set()
        for field in ('affected_systems', 'affected_assets', 'assets', 'host', 'ip'):
            if field in indicator:
                ips |= extract_ips(indicator[field])

        # Quét phần còn lại, nhưng bỏ các trường chỉ mô tả phạm vi.
        rest = dict((k, v) for k, v in indicator.items()
                    if k not in self.SCOPE_FIELDS)
        ips |= extract_ips(rest)
        return ips

    def simulated_counts(self, filenames):
        """Đếm chỉ báo mô phỏng trong các nguồn, để giải thích vì sao rule im lặng."""
        total = 0
        simulated = 0
        for filename in filenames:
            for indicator in self.indicators(filename):
                total += 1
                if self.is_simulated(indicator):
                    simulated += 1
        return total, simulated

    def incident_ips(self, incident):
        ips = extract_ips(incident.get('assets'))
        ips |= extract_ips(incident.get('evidence'))
        return ips

    # ------------------------------------------------------------------
    # RULE 1 - COMPROMISED SHADOW
    # ------------------------------------------------------------------

    def rule_compromised_shadow(self):
        """Shadow asset đồng thời xuất hiện trong Credential Dumping hoặc Persistence IOC.

        Ý nghĩa: một thiết bị không được quản lý đang có dấu hiệu bị khai thác
        nhiều giai đoạn - đây là chuỗi xâm nhập, không phải cảnh báo rời rạc.
        """
        rule_id = 'RULE-1'
        rule_name = 'Compromised Shadow'

        shadow_data = self.state.get('shadow_assets.json') or {}
        shadows = shadow_data.get('shadows')
        shadows = shadows if isinstance(shadows, list) else []

        if not shadows:
            self.add_gap(rule_id, 'NO_SHADOW_ASSETS',
                         'state/shadow_assets.json không có mục shadows nào để tương quan.')
            return

        shadow_by_ip = {}
        for shadow in shadows:
            ip = shadow.get('ip')
            if ip:
                shadow_by_ip[ip] = shadow

        # Gom IOC theo IP, kèm nguồn để giải thích được kết luận.
        ioc_stages = [
            ('hunting_credential_dumping.json', 'Credential Dumping'),
            ('hunting_persistence.json', 'Persistence'),
        ]

        attributed = 0
        hits = {}
        for filename, stage in ioc_stages:
            for indicator in self.indicators(filename):
                ips = self.indicator_ips(indicator)
                if ips:
                    attributed += 1
                for ip in ips:
                    if ip in shadow_by_ip:
                        hits.setdefault(ip, []).append((stage, indicator))

        if not hits:
            total_iocs = sum(len(self.indicators(f)) for f, _ in ioc_stages)
            if attributed == 0 and total_iocs > 0:
                _, simulated = self.simulated_counts([f for f, _ in ioc_stages])
                if simulated == total_iocs:
                    self.add_gap(
                        rule_id, 'IOC_SIMULATED',
                        'Toàn bộ {} IOC credential-dumping/persistence mang '
                        'data_source=SIMULATED (hardcode trong script hunting), '
                        'nên không được quy kết cho {} shadow asset. Rule 1 im '
                        'lặng ở đây là ĐÚNG: quy kết chỉ báo giả vào IP thật sẽ '
                        'tạo bằng chứng xâm nhập không có thật.'
                        .format(total_iocs, len(shadow_by_ip)))
                else:
                    self.add_gap(
                        rule_id, 'IOC_NOT_IP_ATTRIBUTED',
                        '{} IOC credential-dumping/persistence không mang IP nào '
                        '(affected_systems rỗng), nên không thể ghép với {} shadow asset.'
                        .format(total_iocs, len(shadow_by_ip)))
            return

        for ip in sorted(hits):
            shadow = shadow_by_ip[ip]
            stages = sorted(set(stage for stage, _ in hits[ip]))
            evidence = []
            for stage, indicator in hits[ip]:
                evidence.append('[{}] {}: {}'.format(
                    stage,
                    indicator.get('type', 'Unknown'),
                    indicator.get('description', '')))

            multi_stage = len(stages) > 1
            self.add_finding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity='CRITICAL',
                title='Thiết bị {} có dấu hiệu bị xâm nhập chuỗi (Multi-stage Compromise)'.format(ip),
                summary=(
                    'IP {} đang bị gắn cờ Shadow Asset (trust_score={}, lý do: {}) '
                    'và đồng thời xuất hiện trong {} IOC thuộc {}. '
                    'Thiết bị không được quản lý đang bị khai thác{}.'
                ).format(
                    ip,
                    shadow.get('trust_score', 'n/a'),
                    shadow.get('reason', 'n/a'),
                    len(hits[ip]),
                    ' + '.join(stages),
                    ' qua nhiều giai đoạn' if multi_stage else ''),
                entities={
                    'ip': ip,
                    'hostname': shadow.get('hostname'),
                    'type': shadow.get('type'),
                    'trust_score': shadow.get('trust_score'),
                    'stages': stages,
                },
                evidence=evidence,
                recommended_action=(
                    '1. Cô lập {} khỏi mạng ngay | '
                    '2. Thu thập memory + timeline trước khi tắt máy | '
                    '3. Reset toàn bộ credentials đã dùng trên thiết bị này'
                ).format(ip),
                confidence='HIGH' if multi_stage else 'MEDIUM',
                sources=[f for f, _ in ioc_stages] + ['shadow_assets.json'],
            )

    # ------------------------------------------------------------------
    # RULE 2 - LATERAL MOVEMENT PROBE
    # ------------------------------------------------------------------

    def rule_lateral_movement_probe(self):
        """Kết nối mạng bất thường (lateral movement IOC) + đăng nhập thất bại.

        Một trong hai tín hiệu đứng riêng là nhiễu thường gặp. Đi cùng nhau thì
        đó là hành vi dò quét để di chuyển ngang.
        """
        rule_id = 'RULE-2'
        rule_name = 'Lateral Movement Probe'

        lateral = self.indicators('hunting_lateral_movement.json')
        events = self.state.get('security_events.json') or {}
        failed_logons = events.get('failed_logons')

        if not lateral:
            self.add_gap(rule_id, 'NO_LATERAL_IOC',
                         'state/hunting_lateral_movement.json không có indicator nào.')
            return

        if not isinstance(failed_logons, int):
            self.add_gap(rule_id, 'NO_FAILED_LOGON_DATA',
                         'state/security_events.json thiếu trường failed_logons dạng số.')
            return

        if failed_logons < FAILED_LOGON_THRESHOLD:
            self.add_gap(
                rule_id, 'BELOW_THRESHOLD',
                'failed_logons={} dưới ngưỡng {}, không ghép với {} lateral IOC.'
                .format(failed_logons, FAILED_LOGON_THRESHOLD, len(lateral)))
            return

        # Ưu tiên kết luận theo từng IP khi IOC có quy kết tài sản.
        by_ip = {}
        for indicator in lateral:
            for ip in self.indicator_ips(indicator):
                by_ip.setdefault(ip, []).append(indicator)

        known_assets = set()
        assets_data = self.state.get('assets.json') or {}
        for asset in assets_data.get('assets', []) or []:
            if asset.get('ip'):
                known_assets.add(asset['ip'])

        period = events.get('period', 'last_24_hours')

        for ip in sorted(by_ip):
            indicators = by_ip[ip]
            techniques = sorted(set(i.get('type', 'Unknown') for i in indicators))
            critical = any(i.get('severity') == 'CRITICAL' for i in indicators)

            self.add_finding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity='CRITICAL' if critical else 'HIGH',
                title='Dò quét di chuyển ngang nhắm vào {}'.format(ip),
                summary=(
                    '{} kỹ thuật lateral movement ({}) quy kết về {} trùng thời điểm '
                    'với {} lần đăng nhập thất bại trong {}. '
                    'Đây là mẫu dò credential để mở rộng chỗ đứng.'
                ).format(len(indicators), ', '.join(techniques), ip,
                         failed_logons, period),
                entities={
                    'ip': ip,
                    'is_known_asset': ip in known_assets,
                    'techniques': techniques,
                    'failed_logons': failed_logons,
                },
                evidence=(
                    ['[Lateral] {}: {}'.format(i.get('type', 'Unknown'),
                                               i.get('description', ''))
                     for i in indicators]
                    + ['[Security Events] failed_logons={} trong {}'.format(failed_logons, period)]
                ),
                recommended_action=(
                    '1. Kiểm tra Event ID 4625/4768 cho {} | '
                    '2. Chặn SMB/WinRM/RDP từ nguồn lạ | '
                    '3. Reset mật khẩu các tài khoản bị dò'
                ).format(ip),
                confidence='HIGH' if ip in known_assets else 'MEDIUM',
                sources=['hunting_lateral_movement.json', 'security_events.json'],
            )

        # Không IOC nào quy kết được IP: vẫn kết luận ở mức hệ thống, mức thấp hơn.
        if not by_ip:
            techniques = sorted(set(i.get('type', 'Unknown') for i in lateral))
            simulated = sum(1 for i in lateral if self.is_simulated(i))
            all_simulated = simulated == len(lateral)

            if all_simulated:
                # Bằng chứng hoàn toàn là mô phỏng. Vẫn xuất phát hiện - im lặng
                # thì không ai biết nhánh này tồn tại - nhưng không được để nó
                # nằm cùng mức với sự cố có thật.
                quality = 'SIMULATED'
                severity = 'INFO'
                title = ('Lateral movement: chỉ có bằng chứng MÔ PHỎNG, '
                         'không kết luận được')
                summary = (
                    '{} kỹ thuật lateral movement ({}) đều mang '
                    'data_source=SIMULATED - chúng là dữ liệu hardcode trong '
                    'hunt_lateral_movement.py, không phải quan sát từ mạng thật. '
                    '{} lần đăng nhập thất bại trong {} là số liệu thật, nhưng '
                    'một mình nó chưa đủ để kết luận.'
                ).format(len(lateral), ', '.join(techniques), failed_logons, period)
                action = (
                    '1. Nối hunt_lateral_movement với MCP huntLateralMovement để '
                    'có IOC thật | '
                    '2. Rà Event ID 4625 thủ công cho {} lần đăng nhập thất bại | '
                    '3. Không cô lập thiết bị nào dựa trên phát hiện này'
                ).format(failed_logons)
            else:
                quality = 'REAL'
                severity = 'HIGH'
                title = 'Dò quét di chuyển ngang ở mức hệ thống (chưa quy kết được thiết bị)'
                summary = (
                    '{} kỹ thuật lateral movement ({}) cùng tồn tại với {} lần đăng nhập '
                    'thất bại trong {}, nhưng không IOC nào mang IP nên chưa khoanh được '
                    'thiết bị nguồn.'
                ).format(len(lateral), ', '.join(techniques), failed_logons, period)
                action = (
                    '1. Bật quy kết tài sản cho hunt_lateral_movement | '
                    '2. Rà Event ID 4625 để tìm nguồn | '
                    '3. Soát lại quyền truy cập admin share'
                )

            self.add_finding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                evidence_quality=quality,
                title=title,
                summary=summary,
                entities={
                    'ip': None,
                    'techniques': techniques,
                    'failed_logons': failed_logons,
                    'simulated_indicators': simulated,
                },
                evidence=(
                    ['[Lateral] {}: {}'.format(i.get('type', 'Unknown'),
                                               i.get('description', ''))
                     for i in lateral]
                    + ['[Security Events] failed_logons={} trong {}'.format(failed_logons, period)]
                ),
                recommended_action=action,
                confidence='LOW',
                sources=['hunting_lateral_movement.json', 'security_events.json'],
            )

    # ------------------------------------------------------------------
    # RULE 3 - HIGH-RISK CLUSTER
    # ------------------------------------------------------------------

    def rule_high_risk_cluster(self):
        """Mã độc Defender phát hiện + tiến trình chạy ẩn/bất thường.

        Defender bắt được file, còn hunting bắt được hành vi. Trùng nhau nghĩa là
        payload đã chạy chứ không chỉ nằm trên đĩa.
        """
        rule_id = 'RULE-3'
        rule_name = 'High-Risk Cluster'

        defender = self.state.get('defender_status.json') or {}
        processes = self.indicators('hunting_suspicious_processes.json')

        if not processes:
            self.add_gap(rule_id, 'NO_PROCESS_IOC',
                         'state/hunting_suspicious_processes.json không có indicator nào.')
            return

        threat_count = defender.get('threat_count', 0) or 0
        quarantined = defender.get('quarantined_count', 0) or 0
        malware_signal = threat_count + quarantined

        if malware_signal == 0:
            self.add_gap(
                rule_id, 'NO_DEFENDER_DETECTION',
                'Defender báo 0 threat / 0 quarantine (status={}), nên {} tiến trình '
                'bất thường chưa đủ cơ sở để kết luận cụm rủi ro cao.'
                .format(defender.get('status', 'UNKNOWN'), len(processes)))
            return

        # Chỉ giữ các tiến trình thực sự đáng ngờ để cụm không bị loãng.
        elevated = [p for p in processes
                    if p.get('severity') in ('CRITICAL', 'HIGH')]
        cluster = elevated if elevated else processes

        categories = sorted(set(p.get('category', 'Unknown') for p in cluster))
        process_names = sorted(set(p.get('process', 'Unknown') for p in cluster))

        self.add_finding(
            rule_id=rule_id,
            rule_name=rule_name,
            severity='CRITICAL',
            title='Cụm rủi ro cao: mã độc Defender đi kèm {} tiến trình chạy ẩn'.format(len(cluster)),
            summary=(
                'Defender ghi nhận {} threat và {} mục cách ly, đồng thời có {} tiến trình '
                'bất thường ({}) thuộc nhóm {}. Payload nhiều khả năng đã thực thi, '
                'không chỉ nằm trên đĩa.'
            ).format(threat_count, quarantined, len(cluster),
                     ', '.join(process_names), ', '.join(categories)),
            entities={
                'defender_threats': threat_count,
                'defender_quarantined': quarantined,
                'defender_status': defender.get('status'),
                'processes': process_names,
                'categories': categories,
            },
            evidence=(
                ['[Defender] threat_count={}, quarantined_count={}, status={}'.format(
                    threat_count, quarantined, defender.get('status'))]
                + ['[Process] {} ({}): {}'.format(
                    p.get('process', 'Unknown'),
                    p.get('category', 'Unknown'),
                    p.get('command_line', p.get('description', '')))
                   for p in cluster]
            ),
            recommended_action=(
                '1. Quét Defender full scan | '
                '2. Terminate + thu thập image các tiến trình: {} | '
                '3. Đối chiếu hash payload với lịch sử quarantine'
            ).format(', '.join(process_names)),
            confidence='HIGH',
            # Defender là quan sát thật; danh sách tiến trình thì chưa chắc.
            # Cụm chỉ đáng tin khi cả hai vế đều thật.
            evidence_quality=('SIMULATED'
                              if all(self.is_simulated(p) for p in cluster)
                              else 'REAL'),
            sources=['defender_status.json', 'hunting_suspicious_processes.json'],
        )

    # ------------------------------------------------------------------
    # RUN
    # ------------------------------------------------------------------

    def record_coverage_gaps(self):
        """Nguồn hunting nào đang mù thì nói ra, trước khi rule nào kết luận.

        Một rule im lặng vì "không thấy gì" và một rule im lặng vì "không nhìn
        được" trông giống hệt nhau trong báo cáo, nhưng ý nghĩa thì ngược nhau.
        """
        for filename in SOURCE_FILES:
            if not filename.startswith('hunting_'):
                continue
            data = self.state.get(filename) or {}
            coverage = data.get('coverage') or {}
            if coverage and not coverage.get('observable', True):
                self.add_gap(
                    'SOURCE', 'NOT_OBSERVABLE',
                    '{}: {}'.format(filename, coverage.get('reason') or
                                    'nguồn dữ liệu không đọc được'))

    def run(self):
        self.load_sources()

        self.record_coverage_gaps()
        self.rule_compromised_shadow()
        self.rule_lateral_movement_probe()
        self.rule_high_risk_cluster()

        self.findings.sort(key=lambda f: SEVERITY_ORDER.get(f['severity'], 9))

        by_severity = {}
        by_rule = {}
        by_quality = {}
        for finding in self.findings:
            by_severity[finding['severity']] = by_severity.get(finding['severity'], 0) + 1
            by_rule[finding['rule_id']] = by_rule.get(finding['rule_id'], 0) + 1
            quality = finding.get('evidence_quality', 'REAL')
            by_quality[quality] = by_quality.get(quality, 0) + 1

        report = {
            'timestamp': datetime.now().isoformat(),
            'engine': 'correlation_engine',
            'version': ENGINE_VERSION,
            'question': 'Nhiều nguồn cùng chỉ về một thiết bị nào không?',
            'rules_evaluated': 3,
            'total_findings': len(self.findings),
            'by_severity': by_severity,
            'by_rule': by_rule,
            'by_evidence_quality': by_quality,
            'sources': self.sources,
            'coverage_gaps': self.coverage_gaps,
            'findings': self.findings,
        }

        write_state_atomic(self.output_file, report, indent=2)
        return report


def main():
    engine = CorrelationEngine()
    report = engine.run()

    print(json.dumps({
        'status': 'success',
        'total_findings': report['total_findings'],
        'by_severity': report['by_severity'],
        'by_rule': report['by_rule'],
        'by_evidence_quality': report['by_evidence_quality'],
        'coverage_gaps': len(report['coverage_gaps']),
        'output': str(engine.output_file),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main())

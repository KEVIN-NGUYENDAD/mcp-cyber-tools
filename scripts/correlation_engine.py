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

    def incidents_for_ip(self, ip):
        """Sự cố đang ghi nhận cùng một IP.

        Sprint 11.2 dùng nó để nối vế thứ ba: Shadow + IOC là một giả thuyết;
        thêm một incident đang mở thì đó là việc đang diễn ra và đã có người
        nhìn thấy từ hướng khác.
        """
        data = self.state.get('incidents.json') or {}
        incidents = data.get('incidents')
        if not isinstance(incidents, list):
            return []
        return [incident for incident in incidents
                if ip in self.incident_ips(incident)]

    # ------------------------------------------------------------------
    # RULE 1 - COMPROMISED SHADOW
    # ------------------------------------------------------------------

    # Sprint 11.2: một thiết bị lạ có thể lộ ra theo HAI đường, và trước đây
    # rule này chỉ nhìn một.
    #
    #   ARP  thiết bị trả lời arp -a nhưng không có trong kho tài sản.
    #   IOC  một IP xuất hiện với vai trò REMOTE_PEER trong chỉ báo, và IP đó
    #        không có trong kho tài sản.
    #
    # Đường thứ hai không phải phiên bản yếu hơn của đường thứ nhất — nó thấy
    # được thứ ARP không bao giờ thấy. `arp -a` chỉ nhìn được phân đoạn L2 cục
    # bộ và chỉ những thiết bị vừa hoạt động; một máy ở subnet khác xác thực vào
    # đây lúc 3 giờ sáng sẽ không có mặt trong bảng ARP lúc quét, nhưng nó nằm
    # rành rành trong Security log.
    IOC_STAGES = [
        ('hunting_credential_dumping.json', 'Credential Dumping'),
        ('hunting_persistence.json', 'Persistence'),
        ('hunting_lateral_movement.json', 'Lateral Movement'),
        ('hunting_suspicious_processes.json', 'Suspicious Process'),
    ]

    def unknown_peers(self):
        """IP đóng vai REMOTE_PEER trong IOC mà kho tài sản không biết tới.

        Đọc `attribution.systems` do Sprint 11.1 dựng, chứ không tự đoán lại từ
        affected_systems: danh sách phẳng đó giờ luôn chứa cả máy cục bộ, và máy
        cục bộ thì không bao giờ là thiết bị lạ.
        """
        peers = {}
        for filename, stage in self.IOC_STAGES:
            for indicator in self.indicators(filename):
                if self.is_simulated(indicator):
                    continue
                systems = (indicator.get('attribution') or {}).get('systems') or []
                for system in systems:
                    if system.get('scope') != 'REMOTE_PEER':
                        continue
                    if system.get('in_inventory'):
                        continue
                    ip = system.get('ip')
                    if not ip:
                        continue
                    entry = peers.setdefault(ip, {
                        'ip': ip,
                        'hostname': 'Unknown',
                        'type': 'Unknown',
                        'discovered_by': 'IOC',
                        'discovered_in': set(),
                        'reason': ('Xuất hiện trong nội dung sự kiện bảo mật '
                                   'nhưng không có trong kho tài sản'),
                    })
                    entry['discovered_in'].add(stage)
        for entry in peers.values():
            entry['discovered_in'] = sorted(entry['discovered_in'])
        return peers

    def rule_compromised_shadow(self):
        """Thiết bị lạ đồng thời mang IOC — và, nếu có, gắn với incident đang mở.

        Ý nghĩa: một thiết bị không được quản lý đang có dấu hiệu bị khai thác
        nhiều giai đoạn - đây là chuỗi xâm nhập, không phải cảnh báo rời rạc.
        """
        rule_id = 'RULE-1'
        rule_name = 'Compromised Shadow'

        shadow_data = self.state.get('shadow_assets.json') or {}
        arp_shadows = shadow_data.get('shadows')
        arp_shadows = arp_shadows if isinstance(arp_shadows, list) else []

        shadow_by_ip = {}
        for shadow in arp_shadows:
            ip = shadow.get('ip')
            if ip:
                entry = dict(shadow)
                entry['discovered_by'] = 'ARP'
                entry['discovered_in'] = ['arp -a']
                shadow_by_ip[ip] = entry

        ioc_derived = self.unknown_peers()
        for ip, entry in ioc_derived.items():
            if ip in shadow_by_ip:
                # Cả hai đường cùng chỉ vào một IP: bằng chứng mạnh hơn hẳn,
                # phải giữ lại chứ không để đường này ghi đè đường kia.
                shadow_by_ip[ip]['discovered_by'] = 'ARP+IOC'
                shadow_by_ip[ip]['discovered_in'] = (
                    shadow_by_ip[ip]['discovered_in'] + entry['discovered_in'])
            else:
                shadow_by_ip[ip] = entry

        if not shadow_by_ip:
            self.add_gap(
                rule_id, 'NO_SHADOW_ASSETS',
                'Không có thiết bị lạ nào để tương quan: arp -a thấy {} thiết bị '
                'và tất cả đều có trong kho tài sản; {} IOC không chứa REMOTE_PEER '
                'nào ngoài kho. Đây là kết quả ĐÃ KIỂM, không phải rule im lặng.'
                .format(shadow_data.get('arp_devices_seen', '?'),
                        sum(len(self.indicators(f)) for f, _ in self.IOC_STAGES)))
            return

        attributed = 0
        hits = {}
        for filename, stage in self.IOC_STAGES:
            for indicator in self.indicators(filename):
                ips = self.indicator_ips(indicator)
                if ips:
                    attributed += 1
                for ip in ips:
                    if ip in shadow_by_ip:
                        hits.setdefault(ip, []).append((stage, indicator))

        # Một thiết bị lạ do chính IOC phát hiện KHÔNG được lấy đúng IOC đó làm
        # bằng chứng nó bị xâm nhập — đó là lập luận vòng tròn: "IP này đáng ngờ
        # vì nó nằm trong một chỉ báo, và chỉ báo đó chứng minh nó đáng ngờ".
        # Nó phải được chứng thực bởi một giai đoạn KHÁC giai đoạn đã phát hiện.
        circular = []
        for ip in list(hits):
            shadow = shadow_by_ip[ip]
            if shadow.get('discovered_by') != 'IOC':
                continue
            # Thiết bị này lộ ra CHÍNH VÌ nó nằm trong IOC, nên mọi giai đoạn
            # phát hiện nó đều nằm sẵn trong `discovered_in`. Không thể đòi một
            # giai đoạn "ngoài" tập đó — sẽ không bao giờ có. Điều kiện đúng là
            # số giai đoạn PHÂN BIỆT: xuất hiện ở đúng một giai đoạn thì bằng
            # chứng duy nhất ta có chính là lý do ta biết tới nó; xuất hiện ở hai
            # giai đoạn khác nhau thì giai đoạn này chứng thực cho giai đoạn kia.
            distinct_stages = set(stage for stage, _ in hits[ip])
            if len(distinct_stages) < 2:
                circular.append(ip)
                del hits[ip]

        if circular:
            self.add_gap(
                rule_id, 'IOC_SELF_REFERENCE',
                '{} IP ({}) lộ ra qua IOC nhưng chỉ xuất hiện trong đúng giai đoạn '
                'đã phát hiện chúng, nên chưa đủ để kết luận bị xâm nhập. Chúng vẫn '
                'là thiết bị ngoài kho tài sản và cần được xác minh.'
                .format(len(circular), ', '.join(sorted(circular))))

        if not hits:
            total_iocs = sum(len(self.indicators(f)) for f, _ in self.IOC_STAGES)
            if attributed == 0 and total_iocs > 0:
                _, simulated = self.simulated_counts([f for f, _ in self.IOC_STAGES])
                if simulated == total_iocs:
                    self.add_gap(
                        rule_id, 'IOC_SIMULATED',
                        'Toàn bộ {} IOC mang data_source=SIMULATED (hardcode trong '
                        'script hunting), nên không được quy kết cho {} thiết bị lạ. '
                        'Rule 1 im lặng ở đây là ĐÚNG: quy kết chỉ báo giả vào IP '
                        'thật sẽ tạo bằng chứng xâm nhập không có thật.'
                        .format(total_iocs, len(shadow_by_ip)))
                else:
                    self.add_gap(
                        rule_id, 'IOC_NOT_IP_ATTRIBUTED',
                        '{} IOC không mang IP nào (affected_systems rỗng), nên không '
                        'thể ghép với {} thiết bị lạ.'
                        .format(total_iocs, len(shadow_by_ip)))
            elif not circular:
                self.add_gap(
                    rule_id, 'NO_IOC_ON_SHADOW',
                    '{} thiết bị lạ ({}) không xuất hiện trong IOC nào. Chúng vẫn '
                    'nằm ngoài kho tài sản và cần xác minh, nhưng chưa có dấu hiệu '
                    'bị khai thác.'
                    .format(len(shadow_by_ip), ', '.join(sorted(shadow_by_ip))))
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

            # Sprint 11.2: gắn thêm incident đang mở cho cùng IP. Một thiết bị lạ
            # mang IOC là một giả thuyết; cũng thiết bị đó đã có incident mở là
            # một việc đang diễn ra mà ai đó đã nhìn thấy từ hướng khác.
            related = self.incidents_for_ip(ip)
            if related:
                evidence.append('[Incident] {} sự cố đang ghi nhận cùng IP: {}'.format(
                    len(related),
                    ', '.join(i.get('incident_id', '?') for i in related[:5])))

            # Hai đường phát hiện độc lập cùng chỉ vào một IP đáng tin hơn hẳn
            # một đường; và incident đang mở lại nâng thêm một bậc nữa.
            dual_discovery = shadow.get('discovered_by') == 'ARP+IOC'
            if related or (multi_stage and dual_discovery):
                # Hai đường phát hiện độc lập + nhiều giai đoạn tấn công đã đủ
                # mạnh mà không cần incident: ARP và Security log không thể cùng
                # sai theo cùng một cách.
                confidence = 'HIGH'
            elif multi_stage or dual_discovery or related:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

            self.add_finding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity='CRITICAL',
                title='Thiết bị {} có dấu hiệu bị xâm nhập chuỗi (Multi-stage Compromise)'.format(ip),
                summary=(
                    'IP {} là thiết bị ngoài kho tài sản (phát hiện qua {}: {}) '
                    'và đồng thời xuất hiện trong {} IOC thuộc {}{}. '
                    'Thiết bị không được quản lý đang bị khai thác{}.'
                ).format(
                    ip,
                    shadow.get('discovered_by', 'ARP'),
                    ', '.join(shadow.get('discovered_in') or ['n/a']),
                    len(hits[ip]),
                    ' + '.join(stages),
                    '' if not related else ', và có {} sự cố đang mở cùng IP'.format(len(related)),
                    ' qua nhiều giai đoạn' if multi_stage else ''),
                entities={
                    'ip': ip,
                    'hostname': shadow.get('hostname'),
                    'type': shadow.get('type'),
                    'discovered_by': shadow.get('discovered_by'),
                    'discovered_in': shadow.get('discovered_in'),
                    'stages': stages,
                    'incidents': [i.get('incident_id') for i in related],
                },
                evidence=evidence,
                recommended_action=(
                    '1. Cô lập {} khỏi mạng ngay | '
                    '2. Thu thập memory + timeline trước khi tắt máy | '
                    '3. Reset toàn bộ credentials đã dùng trên thiết bị này'
                ).format(ip),
                confidence=confidence,
                sources=([f for f, _ in self.IOC_STAGES]
                         + ['shadow_assets.json', 'incidents.json']),
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

    def attach_ioc_quality(self):
        """Gắn chất lượng IOC vào từng phát hiện cấp điều hành.

        Một phát hiện CRITICAL không kèm chất lượng dữ liệu là thứ khó đọc nhất
        trên bàn của người trực ca: nó nói chuyện gì nghiêm trọng, nhưng không
        nói nó dựa trên cái gì. Ba con số dưới đây tách ba câu hỏi khác nhau mà
        một chữ "CRITICAL" gộp làm một:

            severity            nghiêm trọng tới đâu NẾU nó có thật
            confidence_score    dữ liệu dựng nên nó chắc tới đâu
            attribution_quality có biết nó nói về máy nào không

        Khớp theo IP vì cả bốn rule hiện tại đều lấy thiết bị làm trung tâm. Rule
        nào sau này không như vậy sẽ nhận `indicator_count: 0` và một câu nói rõ
        là không khớp được — chứ không phải một điểm số bịa ra.
        """
        try:
            import ioc_quality
        except ImportError:
            return

        by_ip = {}
        for filename, _stage in self.IOC_STAGES:
            for indicator in self.indicators(filename):
                for ip in ioc_quality.systems_of(indicator):
                    by_ip.setdefault(ip, []).append(indicator)

        for finding in self.findings:
            ips = extract_ips(finding.get('entities') or {})
            techniques = set(str(t) for t in
                             ((finding.get('entities') or {}).get('techniques') or []))
            matched = []
            seen = set()
            for ip in ips:
                for indicator in by_ip.get(ip, []):
                    # Khớp theo IP một mình là không đủ khi IP đó là CHÍNH MÁY
                    # NÀY: mọi chỉ báo trên máy đều mang IP của máy, nên bộ lọc
                    # sẽ gom cả 593 mục và "mắt xích yếu nhất" thành mắt xích
                    # yếu nhất của toàn bộ máy — một con số đúng về một câu hỏi
                    # không ai hỏi. Khi phát hiện có khai kỹ thuật, kỹ thuật là
                    # thứ thu hẹp lại đúng phần bằng chứng đã dựng nên nó.
                    if techniques and str(indicator.get('type')) not in techniques:
                        continue
                    key = id(indicator)
                    if key not in seen:
                        seen.add(key)
                        matched.append(indicator)
            quality = ioc_quality.summarize(matched)
            quality['matched_by'] = ('ip + technique' if techniques else 'ip')
            finding['ioc_quality'] = quality
            finding['confidence_score'] = quality['confidence_score']
            finding['attribution_quality'] = quality['attribution_quality']
            # `evidence_quality` da ton tai voi nghia "REAL / SIMULATED". Khong
            # ghi de no: hai truong noi hai chuyen khac nhau, va gop lai se lam
            # mat dung cai phan biet ma Sprint truoc dung len.
            finding['evidence_completeness'] = quality['evidence_quality']

            # Mot phat hien HIGH/CRITICAL dung tren du lieu diem thap van co the
            # dung — nhung nguoi doc phai thay dieu do TRUOC khi di co lap mot
            # thiet bi. Khong tu ha severity: muc do nghiem trong va do chac chan
            # la hai truc, va tron chung lai chinh la thu ca sprint nay di tach.
            score = quality.get('confidence_score')
            if score is not None and score < ioc_quality.BAND_MEDIUM:
                finding['quality_warning'] = (
                    'Phát hiện mức %s nhưng bằng chứng yếu nhất chỉ đạt %d/100'
                    '%s. Mức nghiêm trọng và độ chắc chắn là hai trục khác nhau.'
                    % (finding.get('severity'), score,
                       (' — %d/%d đầu vào là tiếng ồn đã bị hạ cấp'
                        % (quality.get('suppressed_inputs') or 0,
                           quality.get('indicator_count') or 0))
                       if quality.get('suppressed_inputs') else ''))

    def run(self):
        self.load_sources()

        self.record_coverage_gaps()
        self.rule_compromised_shadow()
        self.rule_lateral_movement_probe()
        self.rule_high_risk_cluster()

        self.attach_ioc_quality()
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
            'by_confidence': dict(
                (f.get('ioc_quality', {}).get('confidence') or 'UNKNOWN',
                 len([g for g in self.findings
                      if (g.get('ioc_quality') or {}).get('confidence')
                      == (f.get('ioc_quality', {}).get('confidence') or 'UNKNOWN')]))
                for f in self.findings),
            'quality_warnings': len([f for f in self.findings
                                     if f.get('quality_warning')]),
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

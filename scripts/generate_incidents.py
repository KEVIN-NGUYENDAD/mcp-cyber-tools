#!/usr/bin/env python3
"""
INCIDENT ENGINE - Automated Incident Creation (Phase N.9)
Tự động tạo Incidents dựa trên phát hiện kết hợp
Populates: state/incidents.json

Quy tắc tạo Incident:
1. New Device + Failed Logons + New Service → INCIDENT HIGH
2. Risk LOW → HIGH → INCIDENT HIGH
3. Defender Disabled → INCIDENT CRITICAL
4. Firewall Disabled → INCIDENT HIGH
5. Weak Cipher + WAAP thấp → INCIDENT MEDIUM
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Import atomic write functions for file safety (TD-L3-001, TD-L3-002, TD-L3-003)
from state_manager import write_state_atomic, read_state_safe
import ioc_attribution
import run_context

# AQ-039. Những tệp state này KHÔNG phải quan sát — chúng là kết quả của một
# phép tính trên các quan sát khác. Tạo sự cố từ chúng đóng một vòng phản hồi:
#
#     generate_incidents  đọc risk_score.json  -> tạo sự cố
#     calculate_risk_score đọc incidents.json  -> sự cố nâng rủi ro
#
# Hai stage chạy trong cùng một pipeline (:472 rồi :486), nên sự cố nuôi rủi ro
# trong lần chạy này và rủi ro nuôi sự cố ở lần chạy sau. Vòng phản hồi dương
# trễ một nhịp, và mức nền chỉ có thể đi lên: mỗi dương tính giả để lại một
# khoản nợ vĩnh viễn trên điểm rủi ro.
#
# Điều đó đã xảy ra. Sáu chỉ báo self-observation (AQ-036 — bình luận giải thích
# luật phát hiện, viết qua PowerShell, bị Event 4688 ghi lại) đẩy risk_level lên
# HIGH. Chỉ báo được sửa; hai sự cố nó sinh ra thì không, và chúng chiếm 50%
# điểm rủi ro với bằng chứng ghi "Risk Score: 31" (thật: 6) và "Thành phần yếu:
# threat_hunting" (thật: mạnh nhất, health 100).
DERIVED_STATE = {
    'risk_score.json': 'điểm rủi ro là kết quả tính từ các quan sát khác, '
                       'không phải một quan sát',
}

# Cùng lý do, ở đường vòng: `collect_timeline_events.detect_risk_changes()` đọc
# risk_score.json rồi phát một sự kiện CRITICAL "Level Change". Sự kiện đó là
# risk_score.json nói lại bằng lời — chặn đường thẳng mà để hở đường này thì
# vòng phản hồi vẫn nguyên.
DERIVED_EVENT_CATEGORIES = {'Risk'}


class IncidentEngine:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.incidents = []
        self.incident_counter = 1
        # Luat khong chay duoc phai di kem ket qua. "0 su co" tren mot luat
        # khong danh gia duoc doc y het "0 su co" tren mot may sach.
        self.skipped_rules = []
        # Luat bi TU CHOI theo thiet ke khac voi luat khong chay duoc. Ghi rieng,
        # kem ly do, de khong ai phuc hoi no ma khong doc ly do.
        self.declined_rules = []
        self.run_id = run_context.run_id()
        self.previous = []
        self.incidents_file = self.state_dir / 'incidents.json'
        self.load_existing_incidents()

    def load_state(self, filename):
        fp = self.state_dir / filename
        return json.load(open(fp, encoding='utf-8')) if fp.exists() else {}

    def load_existing_incidents(self):
        """Tải incidents hiện có: giữ số đếm VÀ giữ chính các sự cố.

        Bản cũ chỉ lấy số đếm rồi ghi đè toàn bộ tệp. Hệ quả là một sự cố không
        còn được phát hiện sẽ **biến mất không dấu vết** — không ai biết nó từng
        tồn tại, tại sao nó mở, hay vì sao nó hết. Đó là mặt còn lại của AQ-039:
        hệ thống không có đường thu hồi, nên nó chọn giữa "để nguyên mãi mãi" và
        "xoá sạch", cả hai đều không kiểm lại được.
        """
        if not self.incidents_file.exists():
            return
        try:
            data = json.load(open(self.incidents_file, encoding='utf-8'))
        except (ValueError, IOError, OSError):
            return
        self.previous = data.get('incidents') or []
        highest = 0
        for incident in self.previous:
            try:
                highest = max(highest, int(str(incident.get('incident_id', '')).split('-')[1]))
            except (IndexError, ValueError):
                continue
        self.incident_counter = highest + 1

    @staticmethod
    def fingerprint(source_state, source_key, severity):
        """Định danh QUAN SÁT đứng sau sự cố, không phải nội dung sự cố.

        Phải ổn định qua các lần chạy (nếu không thì mỗi lần chạy sinh một sự cố
        "mới" cho cùng một sự việc) và phải đổi khi quan sát đổi (nếu không thì
        không phát hiện được lúc nguồn biến mất). Nên nó băm nguồn + khoá nguồn,
        không băm bằng chứng — bằng chứng chứa số liệu thay đổi mỗi lần chạy.
        """
        raw = '%s|%s|%s' % (source_state, source_key, severity)
        return 'FP-' + hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]

    def create_incident(self, severity, title, assets, evidence, recommended_action,
                        reason, source_state=None, source_key=None):
        """Tạo incident mới"""
        if source_state in DERIVED_STATE:
            self.declined_rules.append(
                'Tu choi tao su co tu %s: %s (AQ-039).'
                % (source_state, DERIVED_STATE[source_state]))
            return None

        marker = self.fingerprint(source_state or 'unknown',
                                  source_key or title, severity)

        # Sự cố cho cùng một quan sát phải giữ nguyên định danh qua các lần chạy.
        carried = next((i for i in self.previous
                        if i.get('fingerprint') == marker), None)
        if carried is not None:
            incident_id = carried.get('incident_id')
            created_at = carried.get('created_at')
            first_run = carried.get('source_run_id')
        else:
            incident_id = f"INC-{self.incident_counter:04d}"
            self.incident_counter += 1
            created_at = None
            first_run = self.run_id

        resolved = assets if isinstance(assets, list) else [assets] if assets else []
        scope = 'ATTRIBUTED'
        if not resolved:
            # Sprint 11.1 mở rộng xuống incident: Defender bị tắt, đĩa đầy, CPU
            # cao, risk level tăng — tất cả đều là sự cố CỦA MÁY NÀY. Để assets
            # rỗng thì hạ nguồn hiển thị một sự cố không thuộc về ai, và mọi
            # tương quan theo IP bỏ qua nó hoàn toàn.
            #
            # Máy cục bộ là quy kết kiểm chứng được, không phải phỏng đoán.
            resolved = list(ioc_attribution.local_host_identity()['ips'] or [])
            scope = 'LOCAL_HOST' if resolved else 'UNATTRIBUTED'

        now = datetime.now().isoformat()
        incident = {
            'incident_id': incident_id,
            'severity': severity,
            'status': 'OPEN',
            'title': title,
            'description': reason,
            'assets': resolved,
            'asset_scope': scope,
            'evidence': evidence if isinstance(evidence, list) else [evidence] if evidence else [],
            'recommended_action': recommended_action,
            'created_at': created_at or now,
            # Nguồn gốc, ghi cùng chỗ với kết luận. Không có ba trường này thì
            # không ai rà lại được một sự cố khi quan sát đứng sau nó bị rút.
            'fingerprint': marker,
            'source_state': source_state,
            'source_key': source_key,
            'source_run_id': first_run,
            'last_seen_run_id': self.run_id,
            'last_seen_at': now,
        }

        self.incidents.append(incident)
        return incident_id

    def invalidate_stale(self):
        """Sự cố mà quan sát nguồn không còn -> INVALIDATED, giữ lại, ghi lý do.

        Không xoá: một sự cố biến mất không dấu vết là thứ khiến AQ-039 mất sáu
        vòng mới bị nhìn thấy. Giữ bản ghi thì lần sau có cái để đối chiếu.
        """
        live = set(i['fingerprint'] for i in self.incidents)
        now = datetime.now().isoformat()
        retired = []
        for incident in self.previous:
            marker = incident.get('fingerprint')
            if marker and marker in live:
                continue
            if incident.get('status') in ('INVALIDATED', 'RESOLVED', 'CLOSED'):
                retired.append(incident)
                continue

            record = dict(incident)
            record['status'] = 'INVALIDATED'
            record['invalidated_at'] = now
            record['invalidated_run_id'] = self.run_id
            if not marker:
                # Sự cố sinh ra trước khi có dấu nguồn. Không thể đối chiếu nó
                # với state, và một sự cố không đối chiếu được thì không được
                # tiếp tục cộng vào điểm rủi ro chỉ vì nó cũ.
                record['invalidated_reason'] = (
                    'Sự cố được tạo trước khi hệ thống ghi nguồn gốc '
                    '(fingerprint), nên không đối chiếu được với state hiện '
                    'tại. Đóng lại thay vì tiếp tục tính điểm trên một bằng '
                    'chứng không kiểm được.')
            else:
                record['invalidated_reason'] = (
                    'Quan sát nguồn (%s) không còn trong state của lần chạy '
                    'này.' % (incident.get('source_state') or 'không rõ'))
            retired.append(record)
        self.incidents.extend(retired)

    def detect_device_service_logon_anomaly(self):
        """Quy tắc 1: New Device + Failed Logons + New Service"""
        timeline = self.load_state('timeline.json')
        events = timeline.get('events', [])

        new_devices = [e for e in events if e.get('type') == 'New Device']
        new_services = [e for e in events if e.get('type') == 'New Service']

        security_events = self.load_state('security_events.json')
        failed_logons = security_events.get('failed_logons', 0)

        if new_devices and new_services and failed_logons > 10:
            device_ips = [e.get('details', {}).get('ip') for e in new_devices if e.get('details', {}).get('ip')]
            evidence = [
                f"{len(new_devices)} thiết bị mới",
                f"{len(new_services)} service mới",
                f"{failed_logons} failed logons"
            ]

            self.create_incident(
                severity='HIGH',
                title='Hoạt động bất thường: Thiết bị mới + Failed Logons + Service mới',
                assets=device_ips,
                evidence=evidence,
                recommended_action='Kiểm tra thiết bị mới, xác thực người dùng, kiểm tra dịch vụ',
                reason='Kết hợp: New Device + High Failed Logons + New Service',
                source_state='timeline.json',
                source_key='device+logon+service'
            )

    def detect_risk_escalation(self):
        """Quy tắc 2 — ĐÃ GỠ BỎ theo AQ-039.

        Quy tắc này đọc `risk_score.json` và tạo sự cố khi `risk_level == HIGH`.
        `calculate_risk_score.py` thì đọc `incidents.json` và nâng rủi ro theo số
        sự cố đang mở. Hai chiều đó khép thành vòng.

        Ngoài chuyện vòng lặp, còn một lý do đứng riêng: **đây là sự cố về một
        con số, không phải về một sự việc.** Không có gì xảy ra trên máy khi
        `overall_score` đi từ 29 lên 31; thứ xảy ra là một phép tính cho ra kết
        quả khác. Mọi quan sát thật đứng sau con số đó đã có luật riêng ở dưới —
        Defender tắt, firewall tắt, lỗ hổng, persistence, lateral movement — nên
        luật này không thêm thông tin nào, nó chỉ đếm lại.

        Bằng chứng nó để lại trong INC-0002 cho thấy hậu quả: `"Risk Score: 31"`
        và `"Thành phần yếu: threat_hunting"` — cả hai dòng đều sai khi đọc lại
        (risk là 6; `threat_hunting` health 100, thành phần mạnh nhất). Một sự cố
        chụp lại con số của lần chạy trước rồi sống tiếp như một sự thật.

        `calculate_risk_score.py` là nơi duy nhất được diễn giải risk_level.
        """
        self.declined_rules.append(
            'Quy tac 2 (Risk Level = HIGH -> su co): da go bo. Su co ve mot con '
            'so tinh ra, khong phai ve mot quan sat; va no khep vong phan hoi '
            'incidents <-> risk_score (AQ-039).')

    def detect_defender_disabled(self):
        """Quy tắc 3: Defender Disabled → INCIDENT CRITICAL"""
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled'):
            self.create_incident(
                severity='CRITICAL',
                title='HỆ THỐNG BẤT ĐỮC BẢO VỆ: Defender bị tắt',
                assets=[],
                evidence=['Microsoft Defender disabled'],
                recommended_action='Bật ngay Microsoft Defender',
                reason='Critical: Defender disabled',
                source_state='defender_status.json',
                source_key='defender_disabled'
            )

    def detect_firewall_disabled(self):
        """Quy tắc 4: Firewall Disabled → INCIDENT HIGH"""
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled'):
            self.create_incident(
                severity='HIGH',
                title='Mạng không được bảo vệ: Firewall bị tắt',
                assets=[],
                evidence=['Windows Firewall disabled'],
                recommended_action='Bật Windows Firewall ngay',
                reason='Firewall disabled',
                source_state='firewall_status.json',
                source_key='firewall_disabled'
            )

    def detect_weak_crypto_plus_waap_low(self):
        """Quy tắc 5: Weak Cipher + WAAP thấp → INCIDENT MEDIUM"""
        crypto = self.load_state('crypto_inventory.json')
        waap = self.load_state('waap_score.json')

        weak_ciphers = crypto.get('severity_breakdown', {}).get('CRITICAL', 0)

        # SPRINT B. Dong nay tung la `waap.get('score', 100)`. Khoa `score` khong
        # ton tai — ten that la `health_score` — nen moi lan chay deu nhan 100,
        # va dieu kien `waap_score < 60` KHONG BAO GIO dung. Quy tac 5 da chet tu
        # luc doi ten, im lang, khong mot dong log.
        #
        # Gia tri mac dinh 100 o day khong chi lam sai mot con so: no tat han mot
        # luat phat hien. Khong doc duoc thi bo qua luat va NOI RA, thay vi cho
        # no chay voi mot gia tri gia va bao "khong co gi".
        waap_score = waap.get('health_score', waap.get('score'))
        if waap_score is None:
            self.skipped_rules.append(
                'Quy tac 5 (weak crypto + WAAP thap): waap_score.json khong co '
                '`health_score` lan `score`, khong danh gia duoc.')
            return

        if weak_ciphers > 0 and waap_score < 60:
            self.create_incident(
                severity='MEDIUM',
                title='Mã hóa yếu + WAAP thấp: Rủi ro bảo mật',
                assets=[],
                evidence=[
                    f'{weak_ciphers} weak crypto findings',
                    f'WAAP Score: {waap_score}/100'
                ],
                recommended_action='Cập nhật cipher suites, cải thiện WAAP score',
                reason='Combination: Weak Cipher + Low WAAP',
                source_state='crypto_inventory.json',
                source_key='weak_cipher+low_waap'
            )

    def detect_system_resource_critical(self):
        """Phát hiện: System resources critical"""
        health = self.load_state('system_health.json')
        disk_usage = health.get('disk_usage', 0)
        cpu_usage = health.get('cpu_usage', 0)

        if disk_usage > 95:
            self.create_incident(
                severity='HIGH',
                title='Tài nguyên hệ thống cần khẩn cấp: Đĩa đầy',
                assets=[],
                evidence=[f'Disk usage: {disk_usage}%'],
                recommended_action='Dọn dẹp đĩa ngay lập tức',
                reason='Critical disk usage',
                source_state='system_health.json',
                source_key='disk_usage'
            )

        if cpu_usage > 95:
            self.create_incident(
                severity='MEDIUM',
                title='CPU sử dụng cao: Cần kiểm tra',
                assets=[],
                evidence=[f'CPU usage: {cpu_usage}%'],
                recommended_action='Kiểm tra processes, tối ưu hóa',
                reason='High CPU usage',
                source_state='system_health.json',
                source_key='cpu_usage'
            )

    def detect_multiple_vulnerabilities(self):
        """Phát hiện: Asset với nhiều critical/high vulnerabilities"""
        assets = self.load_state('assets.json')

        for asset in assets.get('assets', []):
            critical_count = asset.get('critical', 0)
            high_count = asset.get('high', 0)
            ip = asset.get('ip')

            if critical_count > 3:
                self.create_incident(
                    severity='CRITICAL',
                    title=f'Asset có nhiều Critical vulnerabilities: {ip}',
                    assets=[ip],
                    evidence=[
                        f'{critical_count} critical vulnerabilities',
                        f'{high_count} high vulnerabilities'
                    ],
                    recommended_action=f'Patch ngay các lỗ hổng trên {ip}',
                    reason='Multiple critical vulnerabilities',
                    source_state='assets.json',
                    source_key='vuln_critical|%s' % ip
                )
            elif critical_count > 0 or high_count > 5:
                self.create_incident(
                    severity='HIGH',
                    title=f'Asset có high-severity vulnerabilities: {ip}',
                    assets=[ip],
                    evidence=[
                        f'{critical_count} critical vulnerabilities',
                        f'{high_count} high vulnerabilities'
                    ],
                    recommended_action=f'Lập kế hoạch patch cho {ip}',
                    reason='High-severity vulnerabilities detected',
                    source_state='assets.json',
                    source_key='vuln_high|%s' % ip
                )

    def detect_suspicious_events(self):
        """Phát hiện: Sự kiện lạ từ timeline"""
        timeline = self.load_state('timeline.json')
        critical_events = [e for e in timeline.get('events', []) if e.get('severity') == 'CRITICAL']

        # AQ-039, đường vòng. `detect_risk_changes()` trong
        # `collect_timeline_events.py` phát một sự kiện CRITICAL mỗi khi
        # `risk_level` đổi bậc — chính là risk_score.json nói lại. Đó là cách
        # INC-0003 ra đời ("Sự kiện nghi ngờ: Level Change") sau khi luật trực
        # tiếp đã bị gỡ. Chặn một đầu mà để hở đầu kia thì vòng vẫn khép.
        derived = [e for e in critical_events
                   if e.get('category') in DERIVED_EVENT_CATEGORIES]
        if derived:
            self.declined_rules.append(
                'Bo qua %d su kien timeline thuoc nhom %s: chung la risk_score '
                'noi lai, khong phai quan sat moi (AQ-039).'
                % (len(derived), '/'.join(sorted(DERIVED_EVENT_CATEGORIES))))
        critical_events = [e for e in critical_events
                           if e.get('category') not in DERIVED_EVENT_CATEGORIES]

        for event in critical_events[:3]:  # Top 3 critical
            self.create_incident(
                severity='HIGH',
                title=f"Sự kiện nghi ngờ: {event.get('type')}",
                assets=event.get('details', {}).get('ip', []) if isinstance(event.get('details', {}), dict) else [],
                evidence=[event.get('description')],
                recommended_action='Điều tra sự kiện',
                reason=event.get('type'),
                source_state='timeline.json',
                source_key='%s|%s' % (event.get('category'), event.get('type'))
            )

    def detect_persistence_threats(self):
        """Phát hiện: Persistence threat indicators (Phase N.9A)"""
        persistence = self.load_state('hunting_persistence.json')

        for indicator in persistence.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"PERSISTENCE THREAT: {indicator.get('type')}",
                    assets=[],
                    evidence=indicator.get('evidence', []),
                    recommended_action=indicator.get('recommendation', 'Điều tra persistence'),
                    reason=f"Persistence type: {indicator.get('type')}",
                    source_state='hunting_persistence.json',
                    source_key=str(indicator.get('type'))
                )

    def detect_suspicious_processes(self):
        """Phát hiện: Suspicious process execution (Phase N.9A)"""
        processes = self.load_state('hunting_suspicious_processes.json')

        for indicator in processes.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"SUSPICIOUS PROCESS: {indicator.get('process')}",
                    assets=[],
                    evidence=[
                        f"Process: {indicator.get('process')}",
                        f"Command: {indicator.get('command_line')}"
                    ],
                    recommended_action=indicator.get('recommendation', 'Điều tra process'),
                    reason=f"Suspicious pattern: {indicator.get('category')}",
                    source_state='hunting_suspicious_processes.json',
                    source_key='%s|%s' % (indicator.get('category'), indicator.get('process'))
                )

    def detect_lateral_movement_threats(self):
        """Phát hiện: Lateral movement indicators (Phase N.9B)"""
        lateral = self.load_state('hunting_lateral_movement.json')

        for indicator in lateral.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"LATERAL MOVEMENT THREAT: {indicator.get('type')}",
                    assets=indicator.get('affected_assets', []),
                    evidence=indicator.get('evidence', []),
                    recommended_action=indicator.get('recommendation', 'Điều tra lateral movement'),
                    reason=f"Lateral movement pattern: {indicator.get('type')}",
                    source_state='hunting_lateral_movement.json',
                    source_key=str(indicator.get('type'))
                )

    def detect_credential_dumping_threats(self):
        """Phát hiện: Credential dumping indicators (Phase N.9B)"""
        credential = self.load_state('hunting_credential_dumping.json')

        for indicator in credential.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"CREDENTIAL DUMPING: {indicator.get('type')}",
                    assets=indicator.get('affected_systems', []),
                    evidence=indicator.get('evidence', []),
                    recommended_action=indicator.get('recommendation', 'Reset passwords ngay'),
                    reason=f"Credential threat: {indicator.get('type')}",
                    source_state='hunting_credential_dumping.json',
                    source_key=str(indicator.get('type'))
                )

    def generate(self):
        """Phát hiện tất cả incidents"""
        self.detect_defender_disabled()
        self.detect_firewall_disabled()
        self.detect_risk_escalation()
        self.detect_device_service_logon_anomaly()
        self.detect_weak_crypto_plus_waap_low()
        self.detect_system_resource_critical()
        self.detect_multiple_vulnerabilities()
        self.detect_suspicious_events()
        # Phase N.9A: Threat Hunting Integration
        self.detect_persistence_threats()
        self.detect_suspicious_processes()
        # Phase N.9B: Advanced Threat Hunting
        self.detect_lateral_movement_threats()
        self.detect_credential_dumping_threats()

        # Loại bỏ duplicates (kiểm tra title + severity)
        seen = set()
        unique_incidents = []
        for incident in self.incidents:
            key = (incident['title'], incident['severity'])
            if key not in seen:
                seen.add(key)
                unique_incidents.append(incident)

        self.incidents = unique_incidents

        # Đường thu hồi: những gì lần chạy trước mở mà lần này không còn quan sát
        # nguồn. Chạy SAU khi đã chốt danh sách phát hiện được, TRƯỚC khi đếm.
        self.invalidate_stale()

        # Sắp xếp: CRITICAL → HIGH → MEDIUM → LOW
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.incidents.sort(key=lambda x: severity_order.get(x.get('severity'), 99))

        open_incidents = [i for i in self.incidents if i.get('status') == 'OPEN']

        # Tạo output
        output = {
            'timestamp': datetime.now().isoformat(),
            'run_id': self.run_id,
            'question': 'Có sự cố gì cần xử lý?',
            # `total_incidents` luôn có nghĩa "đang mở". Bản ghi INVALIDATED nằm
            # trong mảng để rà lại được, nhưng chúng KHÔNG phải việc cần xử lý,
            # và mọi consumer đếm từ trường này.
            'total_incidents': len(open_incidents),
            'total_records': len(self.incidents),
            'by_severity': {},
            'by_severity_all': {},
            'by_status': {},
            'skipped_rules': self.skipped_rules,
            'declined_rules': self.declined_rules,
            'incidents': self.incidents
        }

        # Thống kê by severity — CHỈ trên sự cố đang mở.
        for incident in self.incidents:
            severity = incident.get('severity', 'UNKNOWN')
            status = incident.get('status', 'UNKNOWN')
            output['by_status'][status] = output['by_status'].get(status, 0) + 1
            output['by_severity_all'][severity] = \
                output['by_severity_all'].get(severity, 0) + 1
            if status == 'OPEN':
                output['by_severity'][severity] = \
                    output['by_severity'].get(severity, 0) + 1

        # Atomic write for file safety (TD-L3-001: atomic writes, TD-L3-002: file locking)
        write_state_atomic(str(self.incidents_file), output, indent=2)

        return {
            'status': 'success',
            'total_incidents': len(open_incidents),
            'invalidated': output['by_status'].get('INVALIDATED', 0),
            'critical': output['by_severity'].get('CRITICAL', 0),
            'high': output['by_severity'].get('HIGH', 0),
            'medium': output['by_severity'].get('MEDIUM', 0),
            'declined_rules': len(self.declined_rules)
        }

if __name__ == '__main__':
    engine = IncidentEngine()
    result = engine.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)

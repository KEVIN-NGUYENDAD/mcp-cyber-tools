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

# AQ-047. `sensor_coverage.json` tách hai câu hỏi khác nhau và trả lời cả hai:
#
#   summary            {'covered': 8, 'partial': 0, 'blind': 0}   <- theo NGUỒN
#   capability_summary {'covered': 3, 'partial': 0, 'blind': 2}   <- theo NĂNG LỰC
#
# Cột thứ nhất hỏi "nguồn có mở được không"; cột thứ hai hỏi "thứ ta cần có được
# ghi không". Engine rủi ro chỉ đọc cột thứ nhất, nên hai năng lực đang mù —
# Scheduled Task Execution và USB Device Activity — không chạm tới điểm số, không
# sinh một lời rào nào, và đầu ra là `LOW`.
#
# Đáng chú ý: nguồn `persistence` = covered trong khi năng lực *Scheduled Task
# Execution* = blind. Scheduled Task là một trong những kỹ thuật duy trì phổ biến
# nhất; hệ thống công bố "persistence: covered" trên một máy nó không thấy tác vụ
# định kỳ.
#
# Ánh xạ dưới đây nói mỗi năng lực nuôi thành phần nào. Nó phải được viết ra chứ
# không suy được từ tên: `usb_device_activity` nuôi `security_events` vì câu hỏi
# "cái gì đã được cắm vào máy này" chỉ có log sự kiện trả lời được.
CAPABILITY_COMPONENT = {
    'security_log': 'security_events',
    'process_creation': 'threat_hunting',
    'script_block_logging': 'threat_hunting',
    'scheduled_task_execution': 'threat_hunting',
    'usb_device_activity': 'security_events',
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


# Bản quét lỗ hổng cũ hơn ngưỡng này thì kết luận từ nó phải tự khai tuổi.
ASSET_SCAN_STALE_HOURS = 48


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

    def required(self, data, key, filename):
        """Một khoá BẮT BUỘC. Thiếu thì nói ra, không thay bằng một con số.

        AQ-003. `waap.get('score', 50)` đã chạy như vậy trong nhiều sprint:
        `calculate_waap_score.py` đổi tên `score` -> `health_score`, consumer
        không đổi theo, và mặc định 50 nhận lấy chỗ trống. Điểm WAAP thật là 80.
        Năm phần trăm rủi ro — 38% của tổng điểm 13 — là một hằng số fallback
        đeo nhãn số đo.

        Đây chính là điều `.get(key, default)` làm: nó biến "trường này không tồn
        tại" thành một giá trị trông như đã đo được. Không có ngoại lệ nào đáng
        để giữ hành vi đó cho một trường bắt buộc: một con số sai đi xa hơn
        nhiều so với một stage đỏ.
        """
        if key in data:
            return data[key], None
        note = ('%s thiếu khoá bắt buộc "%s" (có: %s)'
                % (filename, key, ', '.join(sorted(data.keys())[:8]) or 'rỗng'))
        self.notes.append(note)
        return None, note

    # ------------------------------------------------------------------
    # COMPONENT HEALTH (0-100, cao = tốt)
    # ------------------------------------------------------------------

    def analyze_assets(self):
        """AQ-021. Thành phần này (20% trọng số) chấm 100/100 trên một bản quét
        157 giờ tuổi, và câu "0 lỗ hổng CRITICAL, 0 HIGH" — một phát biểu về
        ngày 7/9 — được trình bày như trạng thái hôm nay.

        Một lỗ hổng CRITICAL xuất hiện hôm nay sẽ không chạm tới điểm rủi ro cho
        tới lần quét kế tiếp, và không có gì nói cho người đọc biết điều đó.
        Tuổi của bằng chứng là một phần của kết luận, không phải chú thích.
        """
        assets = self.load_state('assets.json')
        crit, high = 0, 0
        for asset in assets.get('assets', []) or []:
            crit += asset.get('critical', 0) or 0
            high += asset.get('high', 0) or 0
        score = max(0, 100 - crit * 15 - high * 8)
        detail = '{} lỗ hổng CRITICAL, {} HIGH trên {} tài sản'.format(
            crit, high, len(assets.get('assets', []) or []))

        nessus = self.load_state('nessus_status.json')
        age = nessus.get('scan_age_hours')
        if isinstance(age, (int, float)):
            detail += ' — bản quét %0.0f giờ tuổi' % age
            if age > ASSET_SCAN_STALE_HOURS:
                # Không hạ điểm: dữ liệu cũ không chứng minh máy kém an toàn
                # hơn. Nhưng nó cũng không chứng minh máy AN TOÀN, và đó mới là
                # điều con số 100 đang nói. Ghi chú để dòng đó không đọc như một
                # phép đo hôm nay.
                self.notes.append(
                    'Thành phần `asset` dựa trên bản quét Nessus %0.0f giờ tuổi '
                    '(ngưỡng %d): "0 CRITICAL" là phát biểu về lúc quét, không '
                    'phải về hôm nay.' % (age, ASSET_SCAN_STALE_HOURS))
        else:
            detail += ' — không rõ tuổi bản quét'
            self.notes.append(
                'nessus_status.json không khai `scan_age_hours`; không biết dữ '
                'liệu lỗ hổng cũ bao nhiêu.')
        return score, detail, {'critical': crit, 'high': high}

    def analyze_incidents(self):
        """Thành phần mới của Sprint 6 - trước đây không engine nào đọc incidents."""
        incidents = self.load_state('incidents.json')

        # AQ-039. Đếm từ chính mảng sự cố, lọc theo `status`, thay vì tin vào
        # `by_severity` do stage trước tổng kết.
        #
        # Lý do không phải là nghi ngờ stage đó: lý do là hai stage này khép một
        # vòng phản hồi (sự cố nâng rủi ro, rủi ro từng sinh sự cố), và trong một
        # vòng như vậy thì phía tiêu thụ phải tự đọc được điều kiện nó dựa vào.
        # Câu "N sự cố đang mở" giờ có một phép đếm đứng sau, không phải một
        # trường được truyền tay.
        records = incidents.get('incidents')
        if isinstance(records, list):
            open_records = [i for i in records
                            if (i or {}).get('status') == 'OPEN']
            crit = len([i for i in open_records if i.get('severity') == 'CRITICAL'])
            high = len([i for i in open_records if i.get('severity') == 'HIGH'])
            retired = len(records) - len(open_records)
        else:
            by_severity = incidents.get('by_severity') or {}
            crit = by_severity.get('CRITICAL', 0) or 0
            high = by_severity.get('HIGH', 0) or 0
            retired = 0

        score = max(0, 100 - crit * 15 - high * 6)
        detail = '{} sự cố CRITICAL, {} HIGH đang mở'.format(crit, high)
        if retired:
            detail += ' ({} bản ghi đã đóng/thu hồi, không tính điểm)'.format(retired)
        return score, detail, {'critical': crit, 'high': high, 'retired': retired}

    def analyze_crypto(self):
        crypto = self.load_state('crypto_inventory.json')
        score, missing = self.required(crypto, 'score', 'crypto_inventory.json')
        if score is None:
            return None, 'Crypto: {}'.format(missing), {}
        return score, 'crypto inventory score {}'.format(score), {}

    def analyze_waap(self):
        waap = self.load_state('waap_score.json')
        # `health_score` la ten that trong waap_score.json. Bo tro `score` KHONG
        # phai de phong ho: no de mot tep cu (truoc lan doi ten) van doc duoc, va
        # neu ca hai deu vang thi ham tra ve None -> thanh phan nay bi loai khoi
        # phep tinh thay vi duoc doan la 50.
        score, missing = self.required(waap, 'health_score', 'waap_score.json')
        if score is None and 'score' in waap:
            score = waap['score']
            missing = None
        if score is None:
            return None, 'WAAP: {}'.format(missing), {}
        return score, 'WAAP health_score {}'.format(score), {}

    def analyze_defender(self):
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled'):
            return 20, 'Defender đang TẮT', {}
        threats = defender.get('threat_count', 0) or 0
        if threats > 0:
            return max(0, 100 - threats * 10), '{} threat chưa xử lý'.format(threats), {}
        return 100, 'Defender bật, 0 threat', {}

    def analyze_firewall(self):
        """AQ-023. Trước đây hàm này trả về hằng số 90 cho mọi tường lửa đang bật.

        Một thành phần chỉ có hai giá trị khả dĩ (20 hoặc 90) không đo được gì
        giữa hai trạng thái đó — và `firewall_status.json` có ba profile riêng
        biệt cùng số kết nối bị chặn, tức là có dữ liệu để phân biệt.

        "Bật" không phải một trạng thái. Một máy bật Domain profile nhưng tắt
        Public profile đang mở đúng chỗ nguy hiểm nhất, và bản cũ chấm nó bằng
        điểm với một máy bật cả ba.
        """
        firewall = self.load_state('firewall_status.json')
        if not firewall:
            return None, 'Không đọc được firewall_status.json', {}
        if firewall.get('enabled') is None:
            return None, 'firewall_status.json thiếu trường `enabled`', {}
        if not firewall.get('enabled'):
            return 20, 'Firewall đang TẮT', {}

        profiles = [('domain_profile', 'Domain'), ('private_profile', 'Private'),
                    ('public_profile', 'Public')]
        known = [(key, label) for key, label in profiles
                 if firewall.get(key) is not None]
        if not known:
            # Bật, nhưng không biết profile nào. Không đoán: nói ra.
            return 70, 'Firewall bật, không đọc được profile nào', {}

        on = [label for key, label in known if firewall.get(key)]
        off = [label for key, label in known if not firewall.get(key)]
        # 70 điểm nền cho việc bật, 30 điểm chia đều cho các profile ĐỌC ĐƯỢC.
        score = int(round(70 + 30.0 * len(on) / len(known)))
        detail = 'Firewall bật, %d/%d profile bật%s' % (
            len(on), len(known), '' if not off else ' (tắt: %s)' % ', '.join(off))
        return score, detail, {}

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

            # AQ-045 (vá Bài 3, lớp hai). `ioc_quality.score_file` đã tính lại
            # `by_severity` trên tập đã lọc — nhưng điều đó chỉ đúng cho tệp
            # đã đi qua stage đó. Một tệp hunting ghi trực tiếp (cuộc săn lỗi
            # nửa chừng, tệp chép tay, phiên bản cũ) vẫn mang bảng đếm trước
            # lọc. Bộ chấm không được tin bảng tổng kết khi nó còn giữ được
            # danh sách chỉ báo để tự đếm.
            indicators = data.get('indicators')
            if isinstance(indicators, list) and indicators:
                signal = [i for i in indicators
                          if isinstance(i, dict) and not i.get('suppressed')]
                crit = sum(1 for i in signal if i.get('severity') == 'CRITICAL')
                high = sum(1 for i in signal if i.get('severity') == 'HIGH')
            else:
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

    def blind_capabilities(self):
        """Năng lực phát hiện đang mù, đọc từ `sensor_coverage.json` (AQ-047).

        Đây là tệp DUY NHẤT ghi nhận "nguồn mở được nhưng thứ ta cần không được
        ghi". Engine rủi ro trước đây không đọc nó, nên câu trả lời đã được đo
        và đã được ghi vẫn nằm lại trong tệp.
        """
        coverage = self.load_state('sensor_coverage.json')
        return [capability
                for capability in (coverage.get('detection_capabilities') or [])
                if capability.get('status') == 'blind']

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

        weight_available = 0.0
        unmeasurable = []

        # AQ-047. Năng lực mù rút trọng số của thành phần nó nuôi, theo TỈ LỆ số
        # năng lực mù trên tổng số năng lực nuôi thành phần đó.
        #
        # Rút trọn trọng số thì sai theo hướng ngược lại: `threat_hunting` còn
        # được nuôi bởi Process Creation và Script Block Logging, cả hai đang
        # covered, và bỏ hết phần đóng góp của chúng là vứt đi những quan sát có
        # thật. Giữ nguyên trọng số cũng sai — đó chính là lỗi đang sửa.
        #
        # Tỉ lệ là phép chia duy nhất mà dữ liệu chống đỡ được: 1 trong 3 năng
        # lực nuôi `threat_hunting` bị mù thì một phần ba câu trả lời của thành
        # phần đó không tồn tại.
        blind_capabilities = self.blind_capabilities()
        degraded = {}
        if blind_capabilities:
            per_component = {}
            for key, component in CAPABILITY_COMPONENT.items():
                per_component.setdefault(component, []).append(key)
            for capability in blind_capabilities:
                component = CAPABILITY_COMPONENT.get(capability['key'])
                if not component:
                    continue
                degraded.setdefault(component, {'blind': [], 'total': len(
                    per_component.get(component) or [1])})
                degraded[component]['blind'].append(capability)

        for name, analyzer in analyzers:
            health, detail, counts = analyzer()
            weight = WEIGHTS[name]

            if health is None:
                # AQ-003. Thành phần không đo được phải rời khỏi CẢ tử số lẫn
                # mẫu số — đúng kỷ luật `points_available`. Cho nó một giá trị
                # mặc định là cách cũ: điểm rủi ro vẫn ra một con số đẹp, và
                # không ai biết một phần của con số đó chưa từng được đo.
                unmeasurable.append(name)
                component_scores[name] = None
                self.factors.append({
                    'name': name,
                    'health': None,
                    'weight': weight,
                    'weight_counted': 0.0,
                    'risk_contribution': None,
                    'detail': detail,
                    'measurable': False,
                })
                continue

            health = max(0, min(100, int(health)))

            # AQ-047. Phần trọng số ứng với các năng lực mù rời khỏi CẢ tử số
            # lẫn mẫu số — y hệt cách một thành phần không đo được rời đi ở
            # trên. Phần còn lại vẫn được tính, vì phần đó vẫn quan sát được.
            blind_here = degraded.get(name)
            if blind_here:
                kept = 1.0 - (len(blind_here['blind']) / float(blind_here['total']))
                blind_here['weight_dropped'] = weight * (1.0 - kept)
                blind_here['health_claimed'] = health
                weight = weight * kept

            weight_available += weight
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
                'measurable': True,
            })

        # Chuẩn hoá theo trọng số THỰC SỰ đo được. Nếu không, mỗi thành phần
        # không đo được sẽ lặng lẽ đóng góp 0 điểm sức khoẻ và đẩy rủi ro lên —
        # một vùng mù đọc y hệt một mối nguy.
        if weight_available <= 0:
            overall_score = None
            risk_level = 'UNMEASURED'
        else:
            overall_score = int(round(100 - weighted_health / weight_available))
            overall_score = max(0, min(100, overall_score))
        if unmeasurable:
            self.notes.append(
                'Không đo được {} thành phần ({}); điểm được chuẩn hoá trên {:.0%} '
                'trọng số còn lại thay vì đoán giá trị thay thế.'
                .format(len(unmeasurable), ', '.join(unmeasurable), weight_available))
        # AQ-047. Mỗi năng lực mù được GỌI TÊN trong notes. Một dòng nói "2 năng
        # lực mù" không giúp ai đi bật kênh log nào.
        for component, info in sorted(degraded.items()):
            for capability in info['blind']:
                self.notes.append(
                    'Năng lực "{}" đang MÙ nên thành phần `{}` chỉ được tính trên '
                    '{:.0%} trọng số của nó. {} Sức khoẻ {} mà thành phần này khai '
                    'chỉ nói về phần còn quan sát được.'
                    .format(capability.get('label') or capability.get('key'),
                            component,
                            1.0 - info.get('weight_dropped', 0) / WEIGHTS[component],
                            capability.get('action') or capability.get('reason') or '',
                            info.get('health_claimed')))

        if overall_score is not None:
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
        # AQ-047. Cùng một lập luận, áp cho NĂNG LỰC thay vì nguồn: không khẳng
        # định được "rủi ro THẤP" về một kỹ thuật mà máy không ghi lại. Scheduled
        # Task là một trong những kỹ thuật duy trì phổ biến nhất, và chữ người
        # trực ca đọc trên bảng là `LOW`, không phải dòng notes bên dưới.
        if blind_capabilities and risk_level == 'LOW':
            self.notes.append(
                'Capability floor áp dụng: {} năng lực phát hiện đang mù ({}), '
                'nên risk_level nâng từ LOW lên MEDIUM. overall_score giữ nguyên.'
                .format(len(blind_capabilities),
                        ', '.join(c.get('label') or c.get('key')
                                  for c in blind_capabilities)))
            risk_level = 'MEDIUM'

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

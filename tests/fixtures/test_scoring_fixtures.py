# -*- coding: utf-8 -*-
"""
Hồi quy bằng FIXTURE — vòng audit 5 (AQ-031, AQ-019, AQ-023).

Vì sao bộ kiểm này không được đọc `state/`
-------------------------------------------
Điểm rủi ro của hệ thống này dao động theo nhiễu thu thập: 436 → 356 → 266 chỉ
báo trong ba lần chạy liên tiếp, không đổi một dòng mã, không lỗi,
`coverage: OBSERVED` cả ba lần. Risk 10 → 3 → 31 trong hai giờ trên một máy không
đổi cấu hình.

Hệ quả cho việc kiểm thử là dứt khoát: **một bộ kiểm đọc state sống không phân
biệt được "bản vá có tác dụng" với "hôm nay dữ liệu khác".** Nó sẽ xanh vì lý do
sai, rồi đỏ vì lý do sai, và cả hai lần đều không nói gì về mã.

Nên mọi ca ở đây dựng đầu vào cố định và khẳng định đầu ra. Nếu một hàm chấm
điểm biến thành hằng số, ca tương ứng phải đỏ — kể cả khi máy thật hôm đó sạch.

Ca quan trọng nhất trong tệp này
---------------------------------
`self_observation_catches_new_modules`. Danh sách gợi ý tự quan sát trước đây
được viết tay với 13 tên và không bao giờ được cập nhật. Mọi module thêm vào sau
— `ioc_quality`, `sprint_gate`, `evidence_manifest` — đều không có trong đó.

Và điều đó đã gây ra đúng chuyện này, trong chính sprint viết ra bộ kiểm này:
câu bình luận giải thích vì sao `lsass` là từ khoá mơ hồ, viết vào
`ioc_quality.py` qua một lệnh PowerShell, bị Event 4688 ghi lại, rồi bị chính
cuộc săn credential dumping khớp — 6 chỉ báo CRITICAL, risk_level LOW → HIGH.

Viết lời giải thích về luật phát hiện đã kích hoạt luật phát hiện.
"""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
for path in (SCRIPTS_DIR, os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import detection_quality as dq  # noqa: E402
import ioc_quality as iq  # noqa: E402
import calculate_risk_score as crs  # noqa: E402


SYSTEM_LOGON_EVIDENCE = (
    'A logon was attempted using explicit credentials.\r\n\r\n'
    'Subject:\r\n\tSecurity ID:\t\tS-1-5-18\r\n'
    '\tAccount Name:\t\tKEVIN$\r\n\tAccount Domain:\t\tWORKGROUP\r\n'
)


def run():
    suite = Suite('scoring fixtures (AQ-019, 023, 031)')

    # -- 1. tu quan sat phai bat duoc MODULE MOI ---------------------------
    for module in ('ioc_quality', 'sprint_gate', 'evidence_manifest',
                   'pipeline_field_audit', 'generate_handoff',
                   'hunt_credential_dumping'):
        suite.check('Nhan ra "%s" la script giam sat' % module,
                    module in dq.SELF_OBSERVATION_HINTS)

    # Chinh dong lenh da sinh ra 6 CRITICAL gia.
    own_edit = ("python - << EOF\\np = 'scripts/ioc_quality.py'\\n"
                "# phan biet tu khoa mo ho (lsass) voi token cong cu\\nEOF")
    suite.check('Lenh sua chinh script giam sat -> tu quan sat',
                bool(dq.is_self_observation(own_edit)),
                str(dq.is_self_observation(own_edit))[:70])

    # Va mot cuoc tan cong THAT thi KHONG duoc coi la tu quan sat.
    real_attack = 'C:\\\\Temp\\\\m.exe sekurlsa::logonpasswords /target:lsass.exe'
    suite.check('Lenh tan cong that KHONG bi nham la tu quan sat',
                dq.is_self_observation(real_attack) is None,
                str(dq.is_self_observation(real_attack))[:70])

    # Danh sach phai duoc SUY RA, khong viet tay — neu khong no se troi lai sau.
    source = open(os.path.join(SCRIPTS_DIR, 'detection_quality.py'),
                  encoding='utf-8').read()
    suite.check('Danh sach goi y duoc suy ra tu thu muc scripts/',
                'def _module_names(' in source)
    suite.check('  -> va dai hon danh sach viet tay cu (13 ten)',
                len(dq.SELF_OBSERVATION_HINTS) > 13,
                '%d ten' % len(dq.SELF_OBSERVATION_HINTS))

    # -- 2. AQ-019: su that dut khoat ap o MOI muc --------------------------
    # `s-1-5-18` la SID cua tai khoan SYSTEM — mot su that ve chu the, khong
    # phai phong doan theo ten tien trinh. No khong doi nghia khi severity doi.
    system_high = {'severity': 'HIGH', 'type': 'Explicit Credential Logon',
                   'evidence': [SYSTEM_LOGON_EVIDENCE]}
    klass, reason = iq.noise_class(system_high, 'lateral_movement')
    suite.check('4648 cua tai khoan SYSTEM o muc HIGH -> van bi ha xuong tieng on',
                klass == iq.NOISE_ROUTINE, '%s / %s' % (klass, reason))
    suite.check('  -> va ly do noi ro muc cao den tu Event ID',
                bool(reason) and 'Event ID' in str(reason), str(reason)[:80])

    system_info = dict(system_high, severity='INFO')
    suite.check('CUNG bang chung o muc INFO -> cung ket qua',
                iq.noise_class(system_info, 'lateral_movement')[0] == iq.NOISE_ROUTINE)

    # Nhung phong doan theo TEN TIEN TRINH thi van duoc mien tru o muc cao: mot
    # ke tan cong dung dung nhung nhi phan ma lap trinh vien dung.
    dev_high = {'severity': 'CRITICAL', 'process': 'node',
                'evidence': ['Path=C:\\\\tools\\\\node.exe']}
    suite.check('Phong doan theo ten tien trinh o muc CRITICAL -> KHONG loc',
                iq.noise_class(dev_high, 'suspicious_processes')[0] is None)
    dev_info = dict(dev_high, severity='INFO')
    suite.check('  -> nhung o muc INFO thi co loc',
                iq.noise_class(dev_info, 'suspicious_processes')[0] == iq.NOISE_DEV)

    # -- 3. AQ-023: cham diem phai PHAN BIET DUOC ---------------------------
    # Mot ham tra ve hang so se lam moi ca duoi day giong nhau.
    calculator = crs.RiskScoreCalculator()

    def firewall_score(state):
        calculator.load_state = lambda name: state
        return calculator.analyze_firewall()[0]

    all_on = firewall_score({'enabled': True, 'domain_profile': True,
                             'private_profile': True, 'public_profile': True})
    public_off = firewall_score({'enabled': True, 'domain_profile': True,
                                 'private_profile': True, 'public_profile': False})
    one_on = firewall_score({'enabled': True, 'domain_profile': True,
                             'private_profile': False, 'public_profile': False})
    off = firewall_score({'enabled': False})

    suite.check('Tuong lua tat -> diem thap', off == 20, str(off))
    suite.check('Bat het profile -> diem cao nhat', all_on == 100, str(all_on))
    # Day la ca that su quan trong: mot may tat Public profile dang mo dung cho
    # nguy hiem nhat, va ban cu cham no BANG DIEM voi may bat ca ba.
    suite.check('Tat mot profile -> diem THAP HON bat het',
                public_off < all_on, '%s < %s' % (public_off, all_on))
    suite.check('Chi bat mot profile -> thap hon nua',
                one_on < public_off, '%s < %s' % (one_on, public_off))
    suite.check('Khong doc duoc trang thai -> None, khong doan',
                firewall_score({}) is None)

    # -- 4. thanh phan khong do duoc roi khoi CA tu so lan mau so ----------
    suite.check('required() thieu khoa -> None kem ly do',
                calculator.required({'a': 1}, 'b', 'x')[0] is None)
    suite.check('required() co khoa -> tra ve gia tri that',
                calculator.required({'b': 7}, 'b', 'x')[0] == 7)

    # -- 5. AQ-031: diem tin cay phai phan biet duoc tren FIXTURE -----------
    inventory = {'10.0.0.9': {'ip': '10.0.0.9', 'hostname': 'FILESERVER'}}
    strong = iq.score_indicator({
        'type': 'Remote Logon', 'severity': 'INFO',
        'timestamp': '2026-09-14T07:00:00', 'event_id': 4624,
        'source_log': 'Security', 'matched_text': '10.0.0.9',
        'evidence': ['An account was logged on from 10.0.0.9'],
        'data_source': 'LIVE_OBSERVED',
        'attribution': {'systems': [{'ip': '10.0.0.9', 'scope': 'REMOTE_PEER'}]},
    }, 'lateral_movement', inventory)
    weak = iq.score_indicator({'type': 'Unknown', 'evidence': [],
                               'data_source': 'SIMULATED'},
                              'lateral_movement', {})
    suite.check('Fixture manh -> HIGH', strong['confidence'] == 'HIGH',
                str(strong['confidence_score']))
    suite.check('Fixture yeu -> LOW', weak['confidence'] == 'LOW',
                str(weak['confidence_score']))
    suite.check('  -> hai diem cach nhau ro ret',
                strong['confidence_score'] - weak['confidence_score'] >= 40,
                '%d vs %d' % (strong['confidence_score'],
                              weak['confidence_score']))

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))

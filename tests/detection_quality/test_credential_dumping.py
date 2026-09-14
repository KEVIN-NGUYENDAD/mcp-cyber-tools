# -*- coding: utf-8 -*-
"""
hunt_credential_dumping — bộ kiểm dương tính giả.

Đây là cuộc săn đã hỏng thật: ngay sau khi Sprint 9 mở audit 4688, nó nhảy từ 0
lên 15 chỉ báo CRITICAL và lật máy từ LOW sang HIGH. Cả 15 đều khớp vào dòng
lệnh của chính người đang điều tra nó.

Ba nhóm ca, và ranh giới giữa chúng là toàn bộ giá trị của bộ kiểm này:

    TẤN CÔNG    phải ra CRITICAL/HIGH
    NHIỄU       phải bị HẠ CẤP, không được xoá
    TỰ QUAN SÁT phải bị loại, kèm lý do

Nhóm giữa đáng chú ý nhất. Xoá hẳn nhiễu thì cũng xoá luôn một lệnh tấn công
đang núp trong tham số của lệnh khác — nên nhiễu phải còn lại dưới dạng manh mối
cần xác minh, không biến mất.
"""

from harness import Suite, event_4688

import hunt_credential_dumping as hcd


def classify(event):
    hunter = hcd.CredentialDumpingHunter()
    hunter.build_indicators([event])
    if hunter.indicators:
        return 'INDICATOR', hunter.indicators[0]
    if hunter.self_log.entries:
        return 'SELF', hunter.self_log.entries[0]
    return 'NONE', None


ATTACKS = [
    ('mimikatz chay nhu mot tien trinh',
     r'C:\tools\mimikatz.exe', r'"C:\tools\mimikatz.exe" sekurlsa::logonpasswords'),
    ('procdump do bo nho lsass',
     r'C:\tools\procdump64.exe', r'procdump64.exe -ma lsass.exe out.dmp'),
    ('comsvcs.dll MiniDump',
     r'C:\Windows\System32\rundll32.exe',
     r'rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump 660 lsass.dmp full'),
    ('ntdsutil trich NTDS',
     r'C:\Windows\System32\ntdsutil.exe', r'ntdsutil.exe "ac i ntds" "ifm" q q'),
    ('mimikatz doi ten van bi bat qua dong lenh',
     r'C:\Users\Public\svchost.exe', r'svchost.exe mimikatz sekurlsa::logonpasswords'),
]

NOISE = [
    ('grep tim chu lsass trong ma nguon',
     r'C:\Program Files\Git\usr\bin\grep.exe', r'"grep.exe" -n lsass scripts/x.py'),
    ('mo tai lieu co ten nhac toi lsass',
     r'C:\Windows\notepad.exe', r'notepad.exe lsass-notes.txt'),
    ('duong dan chua chu procdump',
     r'C:\Windows\explorer.exe', r'explorer.exe C:\Downloads\procdump-docs\readme.md'),
]

SELF = [
    ('goi thang script san',
     r'C:\Python\python.exe', r'python scripts/hunt_credential_dumping.py'),
    ('truyen chuoi nhan dang',
     r'C:\Python\python.exe', r"python -c \"re.compile('lsass|mimikatz|ntdsutil')\""),
    ('chay pipeline',
     r'C:\Python\python.exe', r'python scripts/run_intelligence_pipeline.py'),
    ('chay tool validator',
     r'C:\Python\python.exe', r'python scripts/tool_validator.py'),
]


def run():
    suite = Suite('hunt_credential_dumping')

    for label, process, command in ATTACKS:
        kind, payload = classify(event_4688(process, command))
        suite.check('TAN CONG bat duoc: %s' % label,
                    kind == 'INDICATOR' and payload['severity'] in ('CRITICAL', 'HIGH'),
                    'nhan %s %s' % (kind, payload and payload.get('severity')))
        if kind == 'INDICATOR':
            evidence = ' '.join(payload.get('evidence') or []).lower()
            suite.check('  -> evidence chua trigger: %s' % label,
                        (payload.get('matched_text') or '').lower() in evidence)

    for label, process, command in NOISE:
        kind, payload = classify(event_4688(process, command))
        suite.check('NHIEU khong len muc cao: %s' % label,
                    kind != 'INDICATOR'
                    or payload['severity'] not in ('CRITICAL', 'HIGH'),
                    'nhan %s %s' % (kind, payload and payload.get('severity')))
        # Hạ cấp chứ không xoá: một lệnh tấn công núp trong tham số của lệnh khác
        # cũng nằm đúng hình dạng này, nên nó phải còn lại để người ta xem.
        if kind == 'INDICATOR':
            suite.check('  -> giu lai de xac minh: %s' % label,
                        payload.get('status') == 'REQUIRES_VERIFICATION',
                        payload.get('status'))

    for label, process, command in SELF:
        kind, payload = classify(event_4688(process, command))
        suite.check('TU QUAN SAT bi loai: %s' % label, kind == 'SELF',
                    'nhan %s' % kind)
        if kind == 'SELF':
            suite.check('  -> co ly do: %s' % label, bool(payload.get('reason')))

    kind, _ = classify(event_4688(r'C:\Windows\notepad.exe', 'notepad.exe a.txt'))
    suite.check('Su kien khong lien quan khong sinh chi bao', kind == 'NONE',
                'nhan %s' % kind)

    return suite

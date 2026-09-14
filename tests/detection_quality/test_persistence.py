# -*- coding: utf-8 -*-
"""
hunt_persistence_indicators — phân mức và bộ lọc tự quan sát.

Rủi ro riêng của cuộc săn này: nếu ai đó đặt lịch chạy `run_intelligence_pipeline.py`
thì chính bộ máy giám sát trở thành một mục tự khởi động, và cuộc săn sẽ báo nó
là chỉ báo persistence — mỗi ngày, mãi mãi, không bao giờ tự hết.
"""

from harness import Suite

import hunt_persistence_indicators as hpi


def build(records):
    hunter = hpi.PersistenceHunter()
    hunter.build_indicators(records)
    return hunter


def task(name, command, location=r'C:\Windows\System32'):
    return {'Kind': 'ScheduledTask', 'Name': name, 'Location': location,
            'Command': command, '_tool': 'huntSuspiciousTasks'}


def run():
    suite = Suite('hunt_persistence_indicators')

    # -- phân mức phải KIẾM ĐƯỢC, không mặc định cao ------------------------
    hunter = build([task('OneDrive', r'C:\Program Files\OneDrive\OneDrive.exe')])
    suite.check('Muc tu khoi dong binh thuong -> INFO',
                hunter.indicators[0]['severity'] == 'INFO',
                hunter.indicators[0]['severity'])

    hunter = build([task('Updater',
                         r'powershell.exe -EncodedCommand SQBFAFgAIAAoAE4A')])
    suite.check('Lenh ma hoa base64 -> CRITICAL',
                hunter.indicators[0]['severity'] == 'CRITICAL',
                hunter.indicators[0]['severity'])

    hunter = build([task('Helper', r'C:\Users\Public\run.exe',
                         location=r'C:\Users\Public')])
    suite.check('Tu khoi dong tu thu muc cong cong -> HIGH',
                hunter.indicators[0]['severity'] == 'HIGH',
                hunter.indicators[0]['severity'])

    # -- tự quan sát --------------------------------------------------------
    hunter = build([task('SentinelOps Pipeline',
                         r'python C:\GitHub\mcp-cyber-tools\scripts\run_intelligence_pipeline.py')])
    suite.check('Tac vu chay chinh pipeline bi loai',
                len(hunter.indicators) == 0 and len(hunter.self_log.entries) == 1,
                '%d chi bao, %d loai' % (len(hunter.indicators),
                                         len(hunter.self_log.entries)))
    if hunter.self_log.entries:
        suite.check('  -> ghi lai ly do va mau',
                    bool(hunter.self_log.entries[0].get('reason'))
                    and bool(hunter.self_log.entries[0].get('sample')))

    hunter = build([task('Backup', r'C:\Program Files\Backup\backup.exe')])
    suite.check('Tac vu binh thuong KHONG bi loai nham',
                len(hunter.self_log.entries) == 0,
                '%d bi loai' % len(hunter.self_log.entries))

    # Một tác vụ độc hại có tên GẦN GIỐNG script giám sát vẫn phải lọt qua bộ
    # lọc: bộ lọc khớp trên đường dẫn script thật, không trên chữ rời rạc.
    hunter = build([task('hunt', r'C:\Users\Public\hunt.exe -stealth',
                         location=r'C:\Users\Public')])
    suite.check('Ten gan giong khong lam bo loc nuot mat chi bao that',
                len(hunter.indicators) == 1,
                '%d chi bao, %d loai' % (len(hunter.indicators),
                                         len(hunter.self_log.entries)))

    # -- bằng chứng ---------------------------------------------------------
    hunter = build([task('Updater', r'powershell.exe -EncodedCommand SQBFAFgA')])
    evidence = ' '.join(hunter.indicators[0]['evidence'])
    suite.check('Bang chung chua chinh lenh da bi gan co',
                'EncodedCommand' in evidence)

    return suite

# -*- coding: utf-8 -*-
"""
hunt_lateral_movement — quy kết, trích đoạn, và bộ lọc tự quan sát.

Hai thứ được kiểm ở đây từng sai thật:

  * 283/428 chỉ báo có `affected_systems` rỗng, vì cuộc săn chỉ quy kết IP từ
    xa. Đăng nhập cục bộ vẫn xảy ra TRÊN máy này — rỗng là một câu sai.

  * Trích đoạn bằng chứng dùng `message[:600]`, trong khi địa chỉ mạng nằm ở
    CUỐI sự kiện đăng nhập. Quy kết bằng một IP mà bằng chứng không chứa IP đó
    là một kết luận không ai bác bỏ được.
"""

from harness import Suite, logon_event

import hunt_lateral_movement as hlm


def build(events):
    hunter = hlm.LateralMovementHunter()
    hunter.build_indicators(events)
    return hunter


def run():
    suite = Suite('hunt_lateral_movement')

    # -- quy kết ----------------------------------------------------------
    hunter = build([logon_event(4624, source_ip='192.168.9.9')])
    suite.check('Co IP tu xa -> giu lai lam trigger',
                hunter.indicators and hunter.indicators[0].get('matched_text') == '192.168.9.9',
                str(hunter.indicators[0].get('matched_text')) if hunter.indicators else 'rong')

    evidence = ' '.join(hunter.indicators[0]['evidence'])
    suite.check('Trich doan chua IP da dung de quy ket',
                '192.168.9.9' in evidence)

    # Sự kiện dài: IP bị đẩy ra ngoài 600 ký tự đầu. Đây đúng là hình dạng đã
    # từng làm bằng chứng mất trigger.
    long_event = logon_event(4624, source_ip='10.9.9.9')
    long_event['Message'] = long_event['Message'].replace(
        'Logon Information:', ('padding ' * 120) + '\r\nLogon Information:')
    hunter = build([long_event])
    evidence = ' '.join(hunter.indicators[0]['evidence'])
    suite.check('Su kien dai: trich doan VAN chua IP', '10.9.9.9' in evidence)
    suite.check('  -> message[:600] thi khong chua (bug cu tai hien duoc)',
                '10.9.9.9' not in long_event['Message'][:600])

    # -- đăng nhập cục bộ ---------------------------------------------------
    hunter = build([logon_event(4624, source_ip=None)])
    suite.check('Dang nhap cuc bo van sinh chi bao',
                len(hunter.indicators) == 1, str(len(hunter.indicators)))
    suite.check('  -> khong co trigger IP',
                hunter.indicators[0].get('matched_text') is None)

    # -- cơ sở mức độ -------------------------------------------------------
    hunter = build([logon_event(4648, source_ip=None)])
    indicator = hunter.indicators[0]
    suite.check('4648 la HIGH', indicator['severity'] == 'HIGH', indicator['severity'])
    suite.check('  -> khai co so muc do (severity_basis)',
                bool(indicator.get('severity_basis')),
                str(indicator.get('severity_basis')))

    # -- tự quan sát --------------------------------------------------------
    hunter = build([logon_event(4648, process=r'python.exe scripts/hunt_lateral_movement.py')])
    suite.check('Su kien do chinh script san sinh ra bi loai',
                len(hunter.indicators) == 0 and len(hunter.self_log.entries) == 1,
                '%d chi bao, %d loai' % (len(hunter.indicators), len(hunter.self_log.entries)))

    hunter = build([logon_event(4624, source_ip='192.168.9.9')])
    suite.check('Su kien binh thuong KHONG bi loai nham',
                len(hunter.self_log.entries) == 0,
                '%d bi loai' % len(hunter.self_log.entries))

    return suite

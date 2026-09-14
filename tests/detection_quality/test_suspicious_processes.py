# -*- coding: utf-8 -*-
"""
hunt_suspicious_processes — đường dẫn đáng ngờ, trigger, và tự quan sát.

Rủi ro riêng: bộ máy giám sát LÀ những tiến trình đang chạy — node chạy MCP
server, python chạy các script săn. Cuộc săn liệt kê tiến trình thì nó nhìn thấy
chính mình trong danh sách, mỗi lần chạy.

Và một kết luận HIGH ở đây nói "chạy từ thư mục tạm/tải về/công cộng" — nhưng
trước Sprint 12 nó không nói ĐOẠN NÀO của đường dẫn là đáng ngờ, nên người đọc
phải tự dò.
"""

from harness import Suite

import hunt_suspicious_processes as hsp


def build(lolbins=(), beacons=(), unusual=()):
    hunter = hsp.SuspiciousProcessHunter()
    hunter.build_indicators(list(lolbins), list(beacons), list(unusual))
    return hunter


def run():
    suite = Suite('hunt_suspicious_processes')

    # -- LOLBin -------------------------------------------------------------
    hunter = build(lolbins=[{'Name': 'certutil.exe', 'Id': 100,
                             'Path': r'C:\Users\Public\certutil.exe'}])
    indicator = hunter.indicators[0]
    suite.check('LOLBin o thu muc cong cong -> HIGH',
                indicator['severity'] == 'HIGH', indicator['severity'])
    suite.check('  -> khai doan duong dan da kich hoat ket luan',
                bool(indicator.get('matched_text')),
                str(indicator.get('matched_text')))
    evidence = ' '.join(indicator['evidence'])
    suite.check('  -> trigger co trong bang chung',
                (indicator.get('matched_text') or '') in evidence)

    hunter = build(lolbins=[{'Name': 'certutil.exe', 'Id': 101,
                             'Path': r'C:\Windows\System32\certutil.exe'}])
    suite.check('LOLBin o vi tri he thong khong len HIGH',
                hunter.indicators[0]['severity'] != 'HIGH',
                hunter.indicators[0]['severity'])

    # -- binary bất thường ---------------------------------------------------
    hunter = build(unusual=[{'Name': 'a.exe', 'Id': 102,
                             'Path': r'C:\Users\tamng\Downloads\a.exe'}])
    suite.check('Binary trong Downloads -> HIGH',
                hunter.indicators[0]['severity'] == 'HIGH',
                hunter.indicators[0]['severity'])

    hunter = build(unusual=[{'Name': 'Code.exe', 'Id': 103,
                             'Path': r'C:\Users\tamng\AppData\Local\Programs\Code.exe'}])
    suite.check('Cai dat theo nguoi dung (Programs) khong len HIGH',
                hunter.indicators[0]['severity'] != 'HIGH',
                hunter.indicators[0]['severity'])

    # -- tự quan sát ---------------------------------------------------------
    hunter = build(unusual=[{'Name': 'python.exe', 'Id': 104,
                             'Path': r'C:\GitHub\mcp-cyber-tools\scripts\hunt_persistence_indicators.py'}])
    suite.check('Tien trinh cua chinh bo may giam sat bi loai',
                len(hunter.indicators) == 0 and len(hunter.self_log.entries) == 1,
                '%d chi bao, %d loai' % (len(hunter.indicators),
                                         len(hunter.self_log.entries)))

    hunter = build(beacons=[{'Process': 'node.exe', 'Path': r'C:\tools\mcp_bridge\node.exe',
                             'RemoteAddress': '8.8.8.8', 'RemotePort': 443,
                             'LocalPort': 5000, 'ProcessId': 105}])
    suite.check('Ket noi cua bo may giam sat bi loai',
                len(hunter.indicators) == 0,
                '%d chi bao' % len(hunter.indicators))

    hunter = build(beacons=[{'Process': 'chrome.exe', 'Path': r'C:\Program Files\Chrome\chrome.exe',
                             'RemoteAddress': '142.250.0.1', 'RemotePort': 443,
                             'LocalPort': 5001, 'ProcessId': 106}])
    suite.check('Ket noi binh thuong KHONG bi loai nham',
                len(hunter.indicators) == 1 and len(hunter.self_log.entries) == 0,
                '%d chi bao, %d loai' % (len(hunter.indicators),
                                         len(hunter.self_log.entries)))

    # -- gộp trùng -----------------------------------------------------------
    same = {'Name': 'zalo.exe', 'Id': 107, 'Path': r'C:\Users\tamng\Downloads\zalo.exe'}
    hunter = build(unusual=[dict(same), dict(same), dict(same)])
    suite.check('Ban ghi trung duoc gop, khong lam loang bao cao',
                len(hunter.indicators) == 1,
                '%d chi bao' % len(hunter.indicators))

    return suite

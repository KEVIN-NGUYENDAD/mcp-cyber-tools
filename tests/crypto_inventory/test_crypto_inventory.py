# -*- coding: utf-8 -*-
"""
Crypto Inventory — khoá severity, khong phai ten truong (AQ-020 / AQ-032 / AQ-041).

Loi goc: Nessus ghi `severity` la SO NGUYEN (0=info...4=critical). Bo dem cong
vao khoa dung nhu nhan duoc (int `0`, `2`...) roi doc ra bang
`severity_counts.get('CRITICAL', 0)` -- mot chuoi. Khoa int khong bao gio khop
khoa str, nen ca ba phep tru luon nhan voi 0 va `crypto_score` la hang so 100
bat ke quet ra gi, trong khi `total_findings` van dem dung.

Fixture nay khoa lai bat bien: mot phat hien CRITICAL/HIGH (khai bang so
nguyen, dung dinh dang Nessus that) PHAI keo `crypto_score` xuong duoi 100, va
`sum(severity_breakdown.values())` PHAI khop `len(findings)` -- day chinh la
phep kiem da bat duoc loi khoa int/str truoc day (tong 0 canh total_findings
19).
"""

from __future__ import print_function

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
from collect_crypto_inventory import CryptoInventory  # noqa: E402


def vuln(plugin_family, plugin_name, severity):
    return {'plugin_family': plugin_family, 'plugin_name': plugin_name,
            'severity': severity}


def run():
    suite = Suite('crypto inventory (AQ-020/AQ-032/AQ-041)')
    collector = CryptoInventory()

    # -- 1. normalize_severity: dinh dang Nessus that la SO NGUYEN -----------
    suite.check('int 4 -> CRITICAL',
                collector.normalize_severity(4) == 'CRITICAL')
    suite.check('int 3 -> HIGH', collector.normalize_severity(3) == 'HIGH')
    suite.check('int 2 -> MEDIUM', collector.normalize_severity(2) == 'MEDIUM')
    suite.check('int 1 -> LOW', collector.normalize_severity(1) == 'LOW')
    suite.check('int 0 -> INFO', collector.normalize_severity(0) == 'INFO')
    suite.check('int ngoai thang (99) -> UNKNOWN, khong bia',
                collector.normalize_severity(99) == 'UNKNOWN')
    suite.check('chuoi so "3" -> HIGH (dinh dang the thay the)',
                collector.normalize_severity('3') == 'HIGH')
    suite.check('chuoi nhan "high" -> HIGH',
                collector.normalize_severity('high') == 'HIGH')
    suite.check('bool KHONG duoc doc nhu int (True != 1 -> HIGH sai)',
                collector.normalize_severity(True) == 'UNKNOWN')
    suite.check('None -> UNKNOWN, khong loi',
                collector.normalize_severity(None) == 'UNKNOWN')

    # -- 2. analyze_crypto voi severity SO NGUYEN (dung Nessus that) ---------
    # Day la fixture tai hien chinh xac loi goc: severity la int, khong phai
    # chuoi 'CRITICAL'/'HIGH' nhu mot nguoi test ngay tho co the viet nham.
    scan_data = {'vulnerabilities': [
        vuln('SSL', 'SSL Certificate Expired', 4),      # crypto, CRITICAL
        vuln('Web Servers', 'Weak Cipher Suite', 3),     # crypto, HIGH
        vuln('General', 'MD5 hash in use', 2),           # crypto, MEDIUM
        vuln('DNS', 'DNS Server Detection', 2),          # KHONG phai crypto
        vuln('SSL', 'TLS handshake', 0),                 # crypto, INFO
    ]}
    analysis = collector.analyze_crypto(scan_data)

    suite.check('Chi giu finding lien quan crypto (loc DNS ra)',
                len(analysis['findings']) == 4,
                '%d finding' % len(analysis['findings']))

    breakdown = analysis['severity_breakdown']
    suite.check('severity_breakdown tong khop so finding (bat bien AQ-041)',
                sum(breakdown.values()) == len(analysis['findings']),
                'tong=%d vs findings=%d' % (sum(breakdown.values()),
                                            len(analysis['findings'])))
    suite.check('CRITICAL dem dung 1 (khong phai 0 do khoa int/str lech)',
                breakdown['CRITICAL'] == 1, str(breakdown))
    suite.check('HIGH dem dung 1', breakdown['HIGH'] == 1, str(breakdown))
    suite.check('MEDIUM dem dung 1', breakdown['MEDIUM'] == 1, str(breakdown))

    # -- 3. crypto_score PHAI phan anh finding, khong duoc la hang so 100 ----
    # Day chinh la trieu chung da do duoc: "crypto_score constant 100" canh
    # "severity_breakdown sum 0" trong khi total_findings 19.
    suite.check('Co CRITICAL+HIGH -> crypto_score PHAI tut duoi 100',
                analysis['score'] < 100, '%d' % analysis['score'])
    expected = max(0, 100 - 1 * 20 - 1 * 10 - 1 * 5)
    suite.check('crypto_score dung cong thuc (100 - 20*C - 10*H - 5*M)',
                analysis['score'] == expected,
                '%d (ky vong %d)' % (analysis['score'], expected))

    # -- 4. khong finding crypto nao -> score 100 la THAT, khong phai loi ----
    clean = collector.analyze_crypto({'vulnerabilities': [
        vuln('DNS', 'DNS Server Detection', 2),
    ]})
    suite.check('Khong finding crypto -> 0 finding, score 100 (sach that)',
                len(clean['findings']) == 0 and clean['score'] == 100,
                str(clean))
    suite.check('  -> nhung breakdown van tong bang 0 (khong bia UNKNOWN)',
                sum(clean['severity_breakdown'].values()) == 0)

    # -- 5. severity khong doc duoc -> UNKNOWN, van nam trong tong, khong roi --
    unreadable = collector.analyze_crypto({'vulnerabilities': [
        vuln('SSL', 'SSL weirdness', 'not-a-severity'),
    ]})
    suite.check('Severity la chuoi khong hop le -> UNKNOWN, khong crash',
                unreadable['severity_breakdown']['UNKNOWN'] == 1,
                str(unreadable['severity_breakdown']))
    suite.check('  -> va van tinh vao tong (khong lang le mat 1 finding)',
                sum(unreadable['severity_breakdown'].values())
                == len(unreadable['findings']))

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))

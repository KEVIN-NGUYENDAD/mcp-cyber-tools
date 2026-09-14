# -*- coding: utf-8 -*-
"""
Telegram Truth — mỗi lệnh phải nói đúng thứ có trong state.

Khác portal ở một điểm quyết định: một ô sai trên portal còn nằm cạnh chín ô
đúng để người xem đối chiếu. Một tin nhắn Telegram đi tới điện thoại một mình,
giữa đêm, không có gì để so.

Hai lỗi đã tìm thấy ở Sprint 14, cả hai đều im lặng:

    /executive   doc `waap.health_score` -> undefined -> WAAP luon mau do
    /evidence    doc `notificationHistory.notifications` -> luon 0 bao cao
"""

import io
import json
import os
import re
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
for path in (SCRIPTS_DIR, os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import telegram_field_audit as tfa  # noqa: E402

BOT_JS = os.path.join(SCRIPTS_DIR, 'telegram', 'telegramBot.js')
DELIVERY_JS = os.path.join(SCRIPTS_DIR, 'telegram', 'alertDelivery.js')


def read(path):
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def state(filename):
    path = os.path.join(PROJECT_ROOT, 'state', filename)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def run():
    suite = Suite('telegram truth')
    bot = read(BOT_JS)
    delivery = read(DELIVERY_JS)

    # -- bộ kiểm trường, chạy trên mã thật ---------------------------------
    findings = tfa.audit()
    missing = [f for f in findings if f['level'] == 'MISSING']
    suite.check('Khong con truong doc tu state khong ton tai',
                not missing,
                '; '.join('%s:%s' % (f['file'], f['field']) for f in missing[:4]))
    suite.check('Bo kiem co quet duoc gi do (khong phai 0 truy cap)',
                len(findings) >= 10, '%d truy cap' % len(findings))

    # -- WAAP: một cách tính duy nhất --------------------------------------
    # Bỏ dòng bình luận khi đếm: chính lời giải thích về lỗi cũ cũng chứa tên
    # trường đó, và một bộ kiểm bắt nhầm lời giải thích sẽ ép người ta xoá lời
    # giải thích — tức là xoá đúng thứ đáng giữ nhất.
    bot_code = '\n'.join(line for line in bot.splitlines()
                         if not line.strip().startswith('//'))
    suite.check('Khong con doc waap.health_score',
                'health_score' not in bot_code,
                'van con %d lan' % bot_code.count('health_score'))
    suite.check('Co ham waapScoreFrom dung chung',
                'function waapScoreFrom(' in bot)
    suite.check('/executive va /analytics deu goi cung ham do',
                bot.count('waapScoreFrom(waap)') >= 3,
                '%d lan goi' % bot.count('waapScoreFrom(waap)'))

    waap = state('waap_status.json') or {}
    summary = waap.get('security_summary') or {}
    expected = ((60 if summary.get('ssl_valid') else 0)
                + (15 if summary.get('waf_active') else 0)
                + (15 if summary.get('cdn_active') else 0)
                + (10 if summary.get('protection_active') else 0))
    # Neu diem that > 0 thi ban cu (undefined) chac chan da noi sai.
    suite.check('WAAP score tinh tu state that ra so co nghia',
                expected > 0, 'diem=%d, summary=%s' % (expected, summary))

    # -- lịch sử cảnh báo: một tên duy nhất --------------------------------
    history = state('notification_history.json') or {}
    suite.check('notification_history dung khoa sent_alerts',
                'sent_alerts' in history, 'khoa: %s' % sorted(history.keys()))
    suite.check('Khong con doc notificationHistory.notifications',
                'notificationHistory.notifications' not in bot)
    suite.check('Co ham sentAlerts dung chung trong bot',
                'function sentAlerts(' in bot)
    suite.check('alertDelivery ghi vao sent_alerts',
                "const ALERT_LIST_KEY = 'sent_alerts'" in delivery)
    suite.check('alertDelivery khong con push thang vao history.alerts',
                'history.alerts.push(' not in delivery)

    # Doc van phai chap nhan ten cu, neu khong lich su da gui se bien mat.
    for name in ('alerts', 'notifications'):
        suite.check('Van doc duoc lich su cu mang khoa "%s"' % name,
                    ('history.%s' % name) in delivery)

    # -- /executive phải đọc executive_findings ----------------------------
    # Một lệnh tên "executive" báo cáo mọi thứ TRỪ các phát hiện cấp điều hành
    # là thứ không ai phát hiện ra bằng mắt: màn hình đầy số, chỉ thiếu đúng cái
    # đáng lẽ phải ở đó.
    suite.check('/executive co doc executive_findings.json',
                'paths.executiveFindings' in bot)
    findings = state('executive_findings.json') or {}
    for field in ('findings', 'coverage_gaps'):
        suite.check('executive_findings.json co khoa "%s"' % field,
                    field in findings, 'khoa: %s' % sorted(findings.keys())[:8])
    for field in ('confidence_score', 'evidence_completeness',
                  'attribution_quality'):
        suite.check('/executive hien %s' % field, field in bot)

    rows = findings.get('findings') or []
    if rows:
        missing = [r for r in rows if 'confidence_score' not in r]
        suite.check('Moi phat hien mang confidence_score',
                    not missing, '%d thieu' % len(missing))
        suite.check('Moi phat hien mang attribution_quality',
                    not [r for r in rows if not r.get('attribution_quality')])

    # -- AQ-006: không khẳng định thứ không có -----------------------------
    # `custodyValid = reportCount > 0` từng sinh ra bốn dòng: hash PASSED,
    # tamper-proof, chữ ký đã xác minh, sẵn sàng phân tích. Không một hàm băm
    # nào tồn tại trong repo, và `reportCount` còn đếm nhầm nguồn.
    # `findings` o tren da bi khoi /executive gan de bang du lieu khac — goi lai
    # ro rang thay vi dua vao thu tu cac khoi trong ham.
    claims = [f for f in tfa.audit() if f['level'] == 'CLAIM']
    suite.check('Khong con khang dinh nao thieu du lieu phia sau',
                not claims,
                '; '.join('%s:%s' % (f['file'], f['line']) for f in claims[:4]))
    suite.check('/evidence khong con suy custody tu `reportCount > 0`',
                'custodyValid = reportCount > 0' not in bot_code)
    suite.check('/evidence doc evidence_manifest.json',
                'paths.evidenceManifest' in bot)

    manifest = state('evidence_manifest.json')
    suite.check('evidence_manifest.json ton tai', manifest is not None)
    if manifest:
        for field in ('total', 'verified', 'changed', 'signature_status',
                      'integrity_scope'):
            suite.check('  manifest co truong "%s"' % field, field in manifest)
        # Thu KHONG co phai duoc noi thang, khong duoc de mot dau tick noi ho.
        suite.check('  chu ky so khai dung la CHUA CO',
                    manifest.get('signature_status') == 'NOT_IMPLEMENTED',
                    str(manifest.get('signature_status')))
        # Bam that, khong phai chuoi giu cho.
        artifacts = manifest.get('artifacts') or {}
        if artifacts:
            first = list(artifacts.values())[0]
            digest = str(first.get('sha256') or '')
            suite.check('  bam la SHA-256 that (64 ky tu hex)',
                        len(digest) == 64
                        and all(c in '0123456789abcdef' for c in digest),
                        digest[:20])

    # /analytics: bon phan tram viet cung, mot muc khong ton tai trong repo.
    suite.check('/analytics khong con "Privilege Escalation" (khong co hunt nao)',
                'Privilege Escalation' not in bot_code)
    suite.check('/analytics tinh Top Risks tu tep hunting that',
                'function topRisks(' in bot)
    suite.check('  -> va bo qua muc da ha xuong tieng on',
                'i.suppressed' in bot)

    # -- không còn giá trị xanh viết cứng ----------------------------------
    hardcoded = re.findall(r"'(?:ONLINE|ACTIVE|READY|HEALTHY|SECURE)'", bot)
    suite.check('Chu trang thai viet cung khong duoc dung lam GIA TRI mac dinh',
                'health_score: 0' not in bot and 'tool_count: \'90+\'' not in bot,
                '%d chuoi trang thai xuat hien (phan lon la nhan hien thi)'
                % len(hardcoded))

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))

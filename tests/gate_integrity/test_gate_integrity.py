# -*- coding: utf-8 -*-
"""
Vòng audit 2 — AQ-013 … AQ-018.

Điểm chung của cả sáu: một giá trị mặc định đứng vào chỗ của một phép đo, và
không có gì trên màn hình nói rằng phép đo đó chưa từng chạy.

Nặng nhất là AQ-013, vì nó nằm **bên trong chính cổng merge**:

    failed_stages = [s for s in stages if not s.get('success', True)]

Bộ ghi pipeline ghi khoá `status`, không ghi `success`. 0/28 stage có trường đó,
nên danh sách thất bại KHÔNG BAO GIỜ có thể khác rỗng. Con số "0 thất bại" in ra
suốt nhiều sprint là `len([])` — không phải một phép đo. Đây là nơi duy nhất
trong repo mà một default xanh tuyệt đối không được phép tồn tại: bộ phận quyết
định mã có được ship hay không.
"""

import io
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
for path in (SCRIPTS_DIR, os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import sprint_gate  # noqa: E402
import pipeline_field_audit as pfa  # noqa: E402


def read(name, folder='scripts'):
    with io.open(os.path.join(PROJECT_ROOT, folder, name), encoding='utf-8') as h:
        return h.read()


def state(filename, folder='state'):
    try:
        with io.open(os.path.join(PROJECT_ROOT, folder, filename),
                     encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def base_data():
    """Dữ liệu cổng tối thiểu, đủ để gọi evaluate() mà không chạy lại gì."""
    now = '2026-09-14T08:00:00'
    return {
        'report': {'generated_at': now, 'summary': {'PASS': 1, 'EMPTY': 0,
                                                    'BLIND': 0, 'FAIL': 0}},
        'coverage': {'probe_generated_at': now},
        'pipeline': {'timestamp': now,
                     'stages': [{'name': 'A', 'status': 'success'},
                                {'name': 'B', 'status': 'success'}]},
        'integrity': {'ok': True, 'total_violations': 0},
        'tests_ok': True, 'tests_detail': '',
        'portal': [], 'telegram': [], 'pipeline_fields': [], 'escapes': [],
    }


def run():
    suite = Suite('gate integrity (AQ-013..018)')

    # -- AQ-013: cong merge phai doc DUNG khoa, va thieu = CHAN --------------
    gate_src = read('sprint_gate.py')
    # Bỏ dòng bình luận: chính lời giải thích về lỗi cũ chứa nguyên văn đoạn mã
    # cũ, và một bộ kiểm bắt nhầm lời giải thích sẽ ép người ta xoá lời giải
    # thích — tức là xoá đúng thứ đáng giữ nhất.
    gate_code = '\n'.join(line for line in gate_src.splitlines()
                          if not line.strip().startswith('#'))
    suite.check('Cong merge khong con doc khoa "success" khong ton tai',
                "s.get('success', True)" not in gate_code)

    # Stage that bai PHAI bi bat. Neu ca nay xanh tren mot ham `return []` thi
    # phep kiem pipeline lai tro ve dung trang thai cu.
    data = base_data()
    suite.check('Moi stage success -> khong blocker nao',
                not sprint_gate.evaluate(data)['blockers'],
                str(sprint_gate.evaluate(data)['blockers'])[:80])

    failed = base_data()
    failed['pipeline']['stages'][0]['status'] = 'failed'
    blockers = sprint_gate.evaluate(failed)['blockers']
    suite.check('Mot stage failed -> BI CHAN',
                any('that bai' in b for b in blockers), str(blockers)[:90])

    missing = base_data()
    del missing['pipeline']['stages'][1]['status']
    blockers = sprint_gate.evaluate(missing)['blockers']
    suite.check('Stage THIEU truong trang thai -> BI CHAN, khong phai dat',
                any('khong khai trang thai' in b for b in blockers),
                str(blockers)[:90])

    empty = base_data()
    empty['pipeline']['stages'] = []
    suite.check('Khong co stage nao -> BI CHAN',
                any('khong co stage' in b
                    for b in sprint_gate.evaluate(empty)['blockers']))

    # Con so that trong log phai co truong trang thai, neu khong thi phep kiem
    # tren khong doc duoc gi.
    pipeline = state('pipeline_results.json', folder='logs') or {}
    stages = pipeline.get('stages') or pipeline.get('results') or []
    suite.check('logs/pipeline_results.json co stage', bool(stages),
                '%d stage' % len(stages))
    if stages:
        without = [s for s in stages if 'status' not in s]
        suite.check('  -> moi stage khai truong `status`',
                    not without, '%d thieu' % len(without))

    # -- AQ-017: tuoi dau vao ----------------------------------------------
    suite.check('Cong merge co kiem tuoi dau vao',
                'MAX_INPUT_AGE_HOURS' in gate_src)
    suite.check('  -> dung cung nguong 24h ma portal dang dung',
                sprint_gate.MAX_INPUT_AGE_HOURS == 24,
                str(sprint_gate.MAX_INPUT_AGE_HOURS))

    stale = base_data()
    stale['report']['generated_at'] = '2026-09-01T00:00:00'
    suite.check('Dau vao qua han -> BI CHAN',
                any('gio tuoi' in b for b in sprint_gate.evaluate(stale)['blockers']),
                str(sprint_gate.evaluate(stale)['blockers'])[:90])

    undated = base_data()
    undated['report'].pop('generated_at')
    suite.check('Dau vao khong khai thoi diem sinh -> BI CHAN',
                any('khong khai thoi diem' in b
                    for b in sprint_gate.evaluate(undated)['blockers']))

    # -- AQ-014: bo audit phai quet TAT CA, khong phai mot danh sach tay -----
    audit_src = read('pipeline_field_audit.py')
    suite.check('Bo audit tu liet ke tep Python, khong dung danh sach viet tay',
                'def python_files(' in audit_src)
    suite.check('  -> va quet nhieu hon 4 tep',
                len(pfa.FILES) > 4, '%d tep' % len(pfa.FILES))
    for name in ('collect_timeline_events.py', 'run_intelligence_pipeline.py',
                 'generate_daily_brief.py'):
        suite.check('  -> co soi %s' % name, name in pfa.FILES)

    findings = pfa.audit()
    fabricated = [f for f in findings if f['level'] == 'FABRICATED']
    suite.check('Khong con so lieu gia trong pipeline Python',
                not fabricated,
                '; '.join('%s:%s' % (f['file'], f['field'])
                          for f in fabricated[:4]))

    # Mac dinh KHAI BAO SU VANG MAT khong phai so lieu gia — do la ranh gioi
    # that cua lop loi nay.
    suite.check('`.get(k, "UNKNOWN")` khong bi tinh la so lieu gia',
                pfa.declares_absence(pfa.ast.Str(s='UNKNOWN')))
    suite.check('`.get(k, 50)` VAN bi tinh la so lieu gia',
                not pfa.declares_absence(pfa.ast.Num(n=50)))

    # -- AQ-014: cac consumer WAAP -----------------------------------------
    waap = state('waap_score.json') or {}
    suite.check('waap_score.json co `health_score`, khong co `score`',
                'health_score' in waap and 'score' not in waap,
                'khoa: %s' % sorted(waap.keys())[:6])
    for name in ('collect_timeline_events.py', 'run_intelligence_pipeline.py'):
        source = read(name)
        suite.check('%s doc `health_score`' % name, "'health_score'" in source)
    pipeline_summary = (pipeline.get('summary') or {})
    if 'waap_score' in pipeline_summary and waap.get('health_score') is not None:
        suite.check('Log van hanh in dung diem WAAP that',
                    pipeline_summary['waap_score'] == waap['health_score'],
                    'log=%s vs state=%s' % (pipeline_summary['waap_score'],
                                            waap['health_score']))

    # -- AQ-015: Daily Brief khong in so 0 cho truong chua doc --------------
    brief_src = read('generate_daily_brief.py')
    for old_field in ('service_count', 'service_inventory', 'certificate_count',
                      'cipher_suite_count'):
        suite.check('Brief khong con doc truong "%s" (khong ton tai)' % old_field,
                    "'%s'" % old_field not in brief_src)
    suite.check('Muc khong doc duoc thi bi BO HAN kem ly do, khong in so 0',
                "'unavailable': True" in brief_src)

    import glob
    briefs = sorted(glob.glob(os.path.join(PROJECT_ROOT, 'daily_brief', '*.json')))
    if briefs:
        with io.open(briefs[-1], encoding='utf-8') as handle:
            brief = json.load(handle)
        services = state('services.json') or {}
        service_summary = brief.get('service_summary') or {}
        if services.get('total_services') is not None \
                and not service_summary.get('unavailable'):
            suite.check('Brief bao dung so dich vu that',
                        service_summary.get('total_services')
                        == services['total_services'],
                        'brief=%s vs state=%s'
                        % (service_summary.get('total_services'),
                           services['total_services']))
        crypto = state('crypto_inventory.json') or {}
        crypto_summary = brief.get('crypto_summary') or {}
        if crypto.get('score') is not None and not crypto_summary.get('unavailable'):
            suite.check('Brief bao dung diem crypto that',
                        crypto_summary.get('health_score') == crypto['score'],
                        'brief=%s vs state=%s' % (crypto_summary.get('health_score'),
                                                  crypto['score']))

    # -- AQ-018: unknown khong duoc thanh false -----------------------------
    status = state('waap_status.json') or {}
    summary = status.get('security_summary') or {}
    suite.check('security_summary giu ba gia tri (co truong null)',
                any(v is None for v in summary.values())
                or status.get('protection_status') == 'active',
                json.dumps(summary))
    if status.get('protection_status') == 'unknown':
        suite.check('  -> `unknown` KHONG bi quy thanh false',
                    summary.get('protection_active') is None,
                    repr(summary.get('protection_active')))

    # -- AQ-016: mot WAAP score duy nhat ------------------------------------
    coverage = status.get('protection_coverage') or {}
    suite.check('waap_status.json co khoi protection_coverage da tinh san',
                'score' in coverage, str(sorted(coverage.keys()))[:70])
    if coverage:
        suite.check('  -> thanh phan chua do duoc roi khoi MAU SO',
                    coverage.get('points_available', 100)
                    <= coverage.get('points_possible', 100),
                    '%s / %s' % (coverage.get('points_available'),
                                 coverage.get('points_possible')))
        if coverage.get('unmeasured'):
            suite.check('  -> va mau so nho hon tong khi co thu chua do duoc',
                        coverage['points_available'] < coverage['points_possible'],
                        '%s < %s' % (coverage['points_available'],
                                     coverage['points_possible']))

    app = read('app.js', folder='web')
    bot = read('telegramBot.js', folder=os.path.join('scripts', 'telegram'))
    app_code = '\n'.join(l for l in app.splitlines()
                         if not l.strip().startswith('//'))
    bot_code = '\n'.join(l for l in bot.splitlines()
                         if not l.strip().startswith('//'))
    suite.check('Portal khong con tu cham WAAP (0 ban sao cong thuc)',
                'waapScore += 60' not in app_code and 'score += 60' not in app_code)
    suite.check('Bot khong con tu cham WAAP',
                'summary.ssl_valid ? 60' not in bot_code)
    suite.check('Portal doc protection_coverage da tinh san',
                'protection_coverage' in app)
    suite.check('Portal co duong doc health_score chinh thuc',
                'function waapHealth(' in app)

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))

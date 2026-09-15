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
        'portal': [], 'telegram': [], 'pipeline_fields': [], 'pipeline_fields_scope': {'findings': [], 'traced': 0, 'total_gets': 0, 'file_count': 0}, 'escapes': [],
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

    audit_result = pfa.audit()
    findings = audit_result['findings'] if isinstance(audit_result, dict) else audit_result
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

    # -- AQ-046: hai tep sinh cung mot lan chay phai khai cung mot ket luan ---
    # Ngay 14/09 luc 13:41:52, `TECHNICAL_DEBT.md` ket luan "Du dieu kien merge:
    # KHONG" trong khi `HANDOFF.md` — sinh cung giay, tu cung nguon — in bon con
    # so dep va khuyen "chay `npm run gate` truoc khi mo PR". Khong tep nao noi
    # doi ve mot con so; tep thu hai chi khong mang theo CAU TRA LOI.
    #
    # Do la tep dau vao cua moi phien, nen im lang o day doc len la "dang on".
    import generate_handoff

    blocked = {'merge_ready': False, 'summary': {},
               'blockers': ['bo kiem phat hien truot (TONG: 337/340 dat)']}
    text = generate_handoff.build(blocked)
    suite.check('Cong chan -> HANDOFF in ro KHONG du dieu kien merge',
                '**Đủ điều kiện merge** | **KHÔNG**' in text,
                'khong tim thay hang ket luan')
    suite.check('Cong chan -> HANDOFF liet ke blocker',
                '337/340' in text, 'blocker khong duoc chep sang')
    nextup = text[text.index('## Việc tiếp theo'):]
    suite.check('Cong chan -> viec dau tien la blocker, khong phai "chay gate"',
                nextup.index('Cổng đang chặn') < nextup.index('AUDIT_QUEUE'),
                'loi khuyen dung truoc blocker')

    passing = {'merge_ready': True, 'summary': {}, 'blockers': []}
    suite.check('Cong mo -> HANDOFF in ro CO du dieu kien merge',
                '**Đủ điều kiện merge** | **CÓ**' in generate_handoff.build(passing))

    # Chay tay, ngoai mot lan chay cong: khong co ket luan nao de chep. Bang cong
    # khi do la mot nua cau tra loi, va nua cau tra loi o day doc giong "dang on"
    # — nen phai khai thang la chua biet, khong duoc im.
    standalone = generate_handoff.build(None)
    suite.check('Khong co verdict -> KHAI la chua biet, khong im lang',
                'Chưa biết cổng có cho merge hay không' in standalone)
    suite.check('Khong co verdict -> KHONG bia ra mot ket luan',
                'Đủ điều kiện merge' not in standalone)

    # -- AQ-047: nang luc mu phai cham toi diem rui ro -----------------------
    # `sensor_coverage.json` tach "nguon co mo duoc khong" khoi "thu ta can co
    # duoc ghi khong", va noi thang hai nang luc dang mu. Roi khong ai doc: engine
    # rui ro chi biet mot loai mu, nen dau ra la LOW tren mot may khong thay tac
    # vu dinh ky — mot trong nhung ky thuat duy tri pho bien nhat.
    import calculate_risk_score as crs

    coverage = state('sensor_coverage.json') or {}
    caps = coverage.get('detection_capabilities') or []
    blind_caps = [c for c in caps if c.get('status') == 'blind']
    suite.check('Moi nang luc deu duoc anh xa ve mot thanh phan rui ro',
                all(c.get('key') in crs.CAPABILITY_COMPONENT for c in caps),
                str([c.get('key') for c in caps
                     if c.get('key') not in crs.CAPABILITY_COMPONENT]))
    suite.check('Moi thanh phan duoc anh xa toi deu co trong WEIGHTS',
                all(v in crs.WEIGHTS for v in crs.CAPABILITY_COMPONENT.values()))

    risk = state('risk_score.json') or {}
    notes = ' '.join(risk.get('notes') or [])
    if blind_caps:
        for capability in blind_caps:
            label = capability.get('label') or capability.get('key')
            suite.check('Nang luc mu "%s" duoc GOI TEN trong notes' % label,
                        label in notes,
                        'mot dong "2 nang luc mu" khong giup ai di bat kenh nao')
        suite.check('Con nang luc mu -> risk_level KHONG duoc la LOW',
                    risk.get('risk_level') != 'LOW',
                    'nhan %r' % risk.get('risk_level'))
        suite.check('  -> va co dong giai thich vi sao khong LOW',
                    'Capability floor' in notes)
    else:
        suite.check('Khong con nang luc mu -> khong can san nang muc', True)

    # -- AQ-043 / AQ-044: bo audit khong chay duoc PHAI noi ra ---------------
    # Vong 9 do `0/7 tep co dau` va vong 10-11 do `7/7`; ca hai lan
    # `run_coherence_audit` deu ket luan "0 vi pham". Cung ma, cung ket luan, du
    # lieu nguoc nhau — vi bo do chi biet noi "khong thay vi pham", va cau do
    # khong phan biet duoc "da soi, sach" voi "khong soi duoc gi".
    #
    # Nua con lai nam o `state_manager`: `except ImportError: pass` bo dau lan
    # chay im lang, nen import hong -> moi tep khong dau -> phep so khong kich
    # hoat -> cong xanh vi dung cai ly do le ra phai chan no.
    import run_coherence_audit

    unstamped_state = {name: {'present': True, 'run_id': None}
                       for name in ('risk_score.json', 'incidents.json')}
    real_run_ids = run_coherence_audit.run_ids
    try:
        run_coherence_audit.run_ids = lambda: unstamped_state
        findings, _ = run_coherence_audit.audit_runs()
    finally:
        run_coherence_audit.run_ids = real_run_ids
    levels = [f['level'] for f in findings]
    suite.check('Moi tep deu KHONG dau -> UNEVALUABLE, khong phai "0 vi pham"',
                'UNEVALUABLE' in levels, str(levels))

    mixed_state = {'risk_score.json': {'present': True, 'run_id': 'RUN-A'},
                   'incidents.json': {'present': True, 'run_id': None}}
    try:
        run_coherence_audit.run_ids = lambda: mixed_state
        findings, _ = run_coherence_audit.audit_runs()
    finally:
        run_coherence_audit.run_ids = real_run_ids
    suite.check('Mot phan khong dau -> UNSTAMPED, khong lang le roi khoi mau so',
                'UNSTAMPED' in [f['level'] for f in findings])

    try:
        run_coherence_audit.run_ids = lambda: {}
        findings, _ = run_coherence_audit.audit_runs()
    finally:
        run_coherence_audit.run_ids = real_run_ids
    suite.check('Khong doc duoc tep nao -> UNEVALUABLE',
                'UNEVALUABLE' in [f['level'] for f in findings])

    # Ca hai muc do phai CHAN merge, khong chi hien ra bang.
    for level in ('UNEVALUABLE', 'UNSTAMPED'):
        data = base_data()
        data['coherence'] = [{'level': level, 'file': 'state/',
                              'field': 'run_id', 'detail': 'gia lap'}]
        data['coherence_scope'] = {}
        suite.check('%s -> BI CHAN' % level,
                    any(level in b for b in sprint_gate.evaluate(data)['blockers']),
                    str(sprint_gate.evaluate(data)['blockers'])[:90])

    # AQ-043: mat dau lan chay phai duoc GHI VAO TEP, khong duoc nuot.
    manager_src = read('state_manager.py')
    manager_code = '\n'.join(l for l in manager_src.splitlines()
                             if not l.strip().startswith('#'))
    suite.check('state_manager khong con nuot ImportError bang `pass`',
                'except ImportError:\n        pass' not in manager_code)
    suite.check('  -> va khai `UNSTAMPED` thay vi im lang',
                "'UNSTAMPED'" in manager_code)

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))

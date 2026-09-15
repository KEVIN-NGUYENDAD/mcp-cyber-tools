#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPRINT GATE (Sprint 12 — TASK 4, 5, 6)

Một lệnh trả lời hai câu hỏi kết thúc mỗi sprint:

    Sprint này có được merge không?
    Còn nợ gì?

    python scripts/sprint_gate.py            đọc kết quả kiểm gần nhất
    python scripts/sprint_gate.py --validate  chạy lại tool_validator trước (chậm)

Thoát 0 nghĩa là ĐỦ ĐIỀU KIỆN MERGE. Khác 0 thì không, và lý do được in ra.

Vì sao cổng chặn phải là một tệp chứ không phải một thói quen
-------------------------------------------------------------
Điều kiện merge của dự án này là FAIL=0 và BLIND=0. Nhớ kiểm hai con số đó mỗi
lần là một thói quen, và thói quen hỏng đúng vào hôm mệt. Một lệnh có mã thoát
thì không.

Cổng này cố ý KHÔNG tự merge. Nó trả lời "có đạt không"; quyết định đẩy mã lên
nhánh chung vẫn là của con người, và đó là ranh giới nên giữ.
"""

from __future__ import print_function

import io
import json
import os
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs', 'project')
DEBT_FILE = os.path.join(DOCS_DIR, 'TECHNICAL_DEBT.md')
TEST_RUNNER = os.path.join(PROJECT_ROOT, 'tests', 'detection_quality', 'run_all.py')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import detection_quality  # noqa: E402
import portal_field_audit  # noqa: E402
import telegram_field_audit  # noqa: E402
import pipeline_field_audit  # noqa: E402
import portal_escape_audit  # noqa: E402
import run_coherence_audit  # noqa: E402
import deploy_truth_audit  # noqa: E402
import schema_reconcile_audit  # noqa: E402
import tool_validator  # noqa: E402


def _read_json(path):
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def run_tests():
    """Bộ kiểm dương tính giả. Không chạy được cũng là TRƯỢT."""
    if not os.path.exists(TEST_RUNNER):
        return False, 'khong tim thay tests/detection_quality/run_all.py'
    try:
        process = subprocess.Popen(
            [sys.executable, TEST_RUNNER],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT)
        raw, _ = process.communicate()
    except OSError as error:
        return False, 'khong chay duoc bo kiem: %s' % error

    text = raw.decode('utf-8', 'replace')
    tail = [line for line in text.splitlines() if line.startswith('TONG:')]
    return process.returncode == 0, (tail[-1] if tail else text.strip()[-120:])


def collect(validate=False):
    """Mọi con số cổng chặn cần, ở một chỗ."""
    if validate:
        report = tool_validator.validate()
        coverage = tool_validator.sensor_coverage(report)
        tool_validator._write_json(
            os.path.join(STATE_DIR, 'tool_validation.json'), report)
        tool_validator._write_json(
            os.path.join(STATE_DIR, 'sensor_coverage.json'), coverage)
    else:
        report = _read_json(os.path.join(STATE_DIR, 'tool_validation.json'))
        coverage = _read_json(os.path.join(STATE_DIR, 'sensor_coverage.json'))

    tests_ok, tests_detail = run_tests()
    integrity = detection_quality.audit_state()
    # Portal doc truong khong ton tai la mot lop loi DA xay ra bon lan trong
    # repo nay, va lan nao cung im lang. No thuoc ve cong chan, khong phai mot
    # lan don dep.
    portal = portal_field_audit.audit()
    # Lop Telegram nguy hiem hon portal o mot diem: mot tin nhan sai di toi
    # dien thoai mot minh, khong co o nao ben canh de doi chieu.
    telegram = telegram_field_audit.audit()
    # SPRINT B. Lop Python la lop TINH ra so, khong chi hien thi no. Mot truong
    # doc sai o day khong lam hong mot o — no lam hong con so, roi con so do di
    # tiep vao portal, Telegram va bao cao, tat ca cung hien dung mot gia tri sai
    # mot cach nhat quan. Ca hai bo audit truoc chi soi JavaScript, va do dung la
    # ly do `waap.get('score', 50)` song sot qua nhieu sprint voi gate xanh.
    pipeline_fields_result = pipeline_field_audit.audit()
    pipeline_fields = pipeline_fields_result['findings']
    # AQ-009. Portal DFIR hien ten tien trinh, dong lenh va duong dan tep thu tu
    # may DANG BI THEO DOI. Neu may do bi xam nhap thi ke tan cong kiem soat noi
    # dung cac truong do, va dashboard cua nguoi truc ca la noi chung duoc render.
    escapes = portal_escape_audit.audit()
    # AQ-039/AQ-040. Hai bat bien ma ca sau bo audit trc do khong the thay,
    # vi chung khong ve mot TRUONG nao ca: state co thuoc mot lan chay duy nhat
    # khong, va su co dang mo co truy nguoc ve mot quan sat con ton tai khong.
    coherence, coherence_scope = run_coherence_audit.audit()
    # AQ-007/AQ-030. Sau vong audit deu xanh trong khi Render chay mot tep khac
    # voi tep duoc soi. Cac bo kia hoi "cai nay co dung khong"; bo nay hoi "cai
    # gi dang chay" — va khong bo nao trong so do tra loi duoc cau thu hai.
    deploy, deploy_scope = deploy_truth_audit.audit()
    # AQ-041. Ba muc CRITICAL dung yen ba vong deu cung mot ho: mot phep anh xa
    # sai giua hai luoc do, khong ai doi chieu hai dau. Chung khong phai ten
    # truong doc sai nen `portal_field_audit` mu; khong phai `.get(k, mac dinh)`
    # nen `pipeline_field_audit` mu. Bo nay cong hai dau roi so.
    reconcile, reconcile_scope = schema_reconcile_audit.audit()
    pipeline = _read_json(os.path.join(PROJECT_ROOT, 'logs', 'pipeline_results.json'))

    return {
        'report': report,
        'coverage': coverage,
        'integrity': integrity,
        'tests_ok': tests_ok,
        'tests_detail': tests_detail,
        'pipeline': pipeline,
        'portal': portal,
        'telegram': telegram,
        'pipeline_fields': pipeline_fields,
        'pipeline_fields_scope': pipeline_fields_result,
        'escapes': escapes,
        'coherence': coherence,
        'coherence_scope': coherence_scope,
        'deploy': deploy,
        'deploy_scope': deploy_scope,
        'reconcile': reconcile,
        'reconcile_scope': reconcile_scope,
    }


# AQ-017. Cổng merge không hề kiểm tuổi của bất kỳ đầu vào nào. `npm run gate`
# (không có `--validate`) đọc kết quả từ đĩa và tuyên bố "đủ điều kiện merge" dựa
# trên chúng, dù chúng cũ bao nhiêu.
#
# Mỉa mai ở chỗ portal ĐÃ có đúng phép kiểm này (`tools_age_hours > 24` -> cảnh
# báo vàng). Portal biết dữ liệu validator có thể cũ; cổng merge thì không —
# nên hai nơi trả lời khác nhau cho cùng một câu hỏi, và nơi có quyền chặn code
# lại là nơi không biết.
#
# Dùng đúng ngưỡng 24 giờ mà portal đang dùng.
MAX_INPUT_AGE_HOURS = 24


def _age_hours(timestamp):
    if not timestamp:
        return None
    try:
        then = datetime.fromisoformat(str(timestamp).replace('Z', ''))
    except (ValueError, TypeError):
        return None
    return round((datetime.now() - then).total_seconds() / 3600.0, 1)


def input_ages(data):
    """Tuổi từng đầu vào của cổng. None = không khai thời điểm sinh."""
    report = data.get('report') or {}
    pipeline = data.get('pipeline') or {}
    coverage = data.get('coverage') or {}
    return [
        ('tool_validation.json', _age_hours(report.get('generated_at'))),
        ('pipeline_results.json', _age_hours(pipeline.get('timestamp')
                                             or pipeline.get('generated_at')
                                             or pipeline.get('started_at'))),
        ('sensor_coverage.json', _age_hours(coverage.get('probe_generated_at')
                                            or coverage.get('generated_at'))),
    ]


def evaluate(data):
    """Điều kiện merge, và lý do cụ thể khi không đạt."""
    blockers = []
    report = data['report']

    if not report:
        blockers.append('chua co state/tool_validation.json — chay `npm run validate`')
        summary = {}
    else:
        summary = report.get('summary') or {}
        if summary.get('FAIL', 0):
            blockers.append('%d tool FAIL' % summary['FAIL'])
        if summary.get('BLIND', 0):
            blockers.append('%d tool BLIND' % summary['BLIND'])
        if not summary.get('PASS', 0):
            blockers.append('khong tool nao PASS')

    for name, age in input_ages(data):
        if age is None:
            blockers.append('%s khong khai thoi diem sinh — khong biet no cu bao '
                            'nhieu, nen khong dung lam can cu merge duoc' % name)
        elif age > MAX_INPUT_AGE_HOURS:
            blockers.append('%s da %0.1f gio tuoi (nguong %d) — chay lai truoc khi '
                            'merge' % (name, age, MAX_INPUT_AGE_HOURS))

    if not data['tests_ok']:
        blockers.append('bo kiem phat hien truot (%s)' % data['tests_detail'])

    integrity = data['integrity']
    if not integrity.get('ok'):
        blockers.append('%d vi pham toan ven bang chung'
                        % integrity.get('total_violations', 0))

    portal_missing = [f for f in (data.get('portal') or [])
                      if f['level'] == 'MISSING']
    if portal_missing:
        blockers.append('%d truong portal doc tu state khong ton tai'
                        % len(portal_missing))

    telegram_missing = [f for f in (data.get('telegram') or [])
                        if f['level'] == 'MISSING']
    if telegram_missing:
        blockers.append('%d truong telegram doc tu state khong ton tai'
                        % len(telegram_missing))

    fabricated = [f for f in (data.get('pipeline_fields') or [])
                  if f['level'] == 'FABRICATED']
    if fabricated:
        blockers.append('%d so lieu gia trong pipeline Python (%s)'
                        % (len(fabricated),
                           ', '.join('%s:%s' % (f['file'], f['field'])
                                     for f in fabricated[:3])))

    unescaped = [f for f in (data.get('escapes') or [])
                 if f['level'] == 'UNESCAPED']
    if unescaped:
        blockers.append('%d bieu thuc chua escape di vao innerHTML (%s)'
                        % (len(unescaped),
                           ', '.join(f['expression'][:24] for f in unescaped[:3])))

    # AQ-039/AQ-040. Ba vi pham, ba lop loi khac nhau, cung mot goc: khong co
    # duong noi giua mot ket luan va quan sat sinh ra no.
    coherence = data.get('coherence') or []
    # AQ-043/AQ-044. `UNEVALUABLE` va `UNSTAMPED` la blocker, khong phai canh
    # bao: ca hai deu co nghia la phep kiem gan ket KHONG chay duoc, va mot bo
    # audit khong chay duoc ma de merge di qua thi no khong phai mot cong.
    blind_audit = [f for f in coherence
                   if f['level'] in ('UNEVALUABLE', 'UNSTAMPED')]
    for finding in blind_audit:
        blockers.append('gan ket lan chay [%s] %s'
                        % (finding['level'], finding['detail']))

    mixed = [f for f in coherence if f['level'] == 'MIXED_RUN']
    if mixed:
        blockers.append('state tron nhieu lan chay (%s) — moi ket luan rut ra '
                        'tu tap nay dang tron hai lan quan sat'
                        % '; '.join(f['detail'][:60] for f in mixed))
    manifest_incomplete = [f for f in coherence if f['level'] == 'MANIFEST_INCOMPLETE']
    if manifest_incomplete:
        blockers.append('manifest khong toan ven — thieu file trong run_manifest.json')
    orphan = [f for f in coherence if f['level'] in ('NO_PROVENANCE', 'SOURCE_MISSING')]
    if orphan:
        blockers.append('%d su co dang mo khong truy nguoc duoc ve quan sat (%s)'
                        % (len(orphan), ', '.join(f['field'] for f in orphan[:3])))
    derived = [f for f in coherence if f['level'] == 'DERIVED_SOURCE']
    if derived:
        blockers.append('%d su co sinh tu mot con so tinh ra, khong phai quan '
                        'sat (%s) — vong phan hoi incidents<->risk'
                        % (len(derived), ', '.join(f['field'] for f in derived[:3])))

    # AQ-007/AQ-030. Lech diem vao la blocker tuyet doi: khi no do thi moi ket
    # qua xanh cua cac bo khac deu noi ve mot artifact khong ai mo.
    for finding in (data.get('deploy') or []):
        blockers.append('deploy truth [%s] %s'
                        % (finding['level'], finding['detail']))

    # AQ-041. Hai dau mot phep cong khong khop nghia la mot con so cong bo dang
    # noi ve mot tap khac voi tap no trich dan.
    for finding in (data.get('reconcile') or []):
        blockers.append('schema reconcile [%s] %s'
                        % (finding['level'], finding['detail']))

    pipeline = data['pipeline'] or {}
    stages = pipeline.get('stages') or pipeline.get('results') or []
    # AQ-013. Dong nay tung la `not s.get('success', True)`. Bo ghi pipeline
    # ghi khoa `status`, khong ghi `success` — nen 0/28 stage co truong do va
    # mac dinh `True` nuot tron su khac biet ten truong. Danh sach that bai
    # KHONG BAO GIO co the khac rong: con so "0 that bai" in ra suot nhieu sprint
    # la `len([])`, khong phai mot phep do.
    #
    # Day la default xanh nam trong chinh bo phan quyet dinh ma co duoc ship hay
    # khong — noi duy nhat trong repo ma mot default xanh tuyet doi khong duoc
    # phep ton tai. Nen o day: thieu du lieu = CHAN.
    failed_stages = []
    unknown_stages = []
    for stage in stages:
        status = stage.get('status')
        if status is None:
            unknown_stages.append(stage.get('name') or '?')
        elif str(status).lower() not in ('success', 'ok', 'passed', 'skipped'):
            failed_stages.append(stage)
    if failed_stages:
        blockers.append('%d stage pipeline that bai (%s)'
                        % (len(failed_stages),
                           ', '.join(str(s.get('name')) for s in failed_stages[:3])))
    if unknown_stages:
        blockers.append('%d stage khong khai trang thai (%s) — thieu du lieu la '
                        'CHAN, khong phai dat'
                        % (len(unknown_stages), ', '.join(unknown_stages[:3])))
    if not stages:
        blockers.append('khong co stage pipeline nao trong logs/pipeline_results.json')

    return {
        'merge_ready': not blockers,
        'blockers': blockers,
        'summary': summary,
        'stages': len(stages),
        'failed_stages': len(failed_stages),
        'unknown_stages': len(unknown_stages),
    }


# --------------------------------------------------------------------------
# TASK 5 — TECHNICAL_DEBT.md sinh tự động
# --------------------------------------------------------------------------

def debt_rows(data):
    """Nợ ĐO ĐƯỢC từ lần chạy này, cộng nợ đã ghi tay trong tool_validator.

    Tách hai loại vì chúng già đi theo hai cách khác nhau: nợ đo được tự biến
    mất khi vấn đề hết, còn nợ ghi tay chỉ mất khi có người xoá nó — và một bảng
    nợ toàn mục ghi tay là bảng sẽ nói sai trước tiên.
    """
    measured = []
    report = data['report'] or {}
    summary = report.get('summary') or {}

    if summary.get('FAIL', 0):
        measured.append(('Tool FAIL', '%d tool báo lỗi khi gọi thật'
                         % summary['FAIL'], 'CHẶN MERGE'))
    if summary.get('BLIND', 0):
        measured.append(('Tool BLIND', '%d tool không quan sát được nguồn'
                         % summary['BLIND'], 'CHẶN MERGE'))
    if summary.get('EMPTY', 0):
        measured.append((
            'Tool EMPTY', '%d tool đọc được nguồn nhưng không có bản ghi nào khớp'
            % summary['EMPTY'],
            'Không phải nợ — đây là "đã nhìn, không có gì". Ghi ra để không ai '
            'nhầm nó với BLIND.'))

    integrity = data['integrity']
    if not integrity.get('ok'):
        measured.append((
            'Toàn vẹn bằng chứng',
            '%d chỉ báo kết luận điều mà bằng chứng của nó không chứng minh được'
            % integrity.get('total_violations', 0), 'CHẶN MERGE'))

    coverage = data['coverage'] or {}
    for key, detail in (coverage.get('details') or {}).items():
        if detail.get('status') != 'covered':
            measured.append(('Cảm biến: %s' % detail.get('label', key),
                             detail.get('reason') or detail.get('status'),
                             detail.get('status', '').upper()))

    for capability in (coverage.get('detection_capabilities') or []):
        if capability.get('status') != 'covered':
            measured.append(('Năng lực: %s' % capability.get('label'),
                             ' '.join((capability.get('reason') or '').split())[:220],
                             capability.get('status', '').upper()))

    for row in (data['report'] or {}).get('results', []):
        if row.get('variants_failed'):
            measured.append(('Tham số: %s' % row['tool'],
                             '%d biến thể tham số lỗi' % len(row['variants_failed']),
                             'CẦN SỬA'))

    return measured


def write_debt(data, verdict):
    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    lines = []
    add = lines.append
    add('# Technical Debt')
    add('')
    add('Sinh tự động bởi `scripts/sprint_gate.py`. Đừng sửa tay — sửa nguồn.')
    add('')
    add('Cập nhật: %s' % datetime.now().isoformat(timespec='seconds'))
    add('')
    add('## Cổng merge')
    add('')
    add('| | |')
    add('|---|---|')
    add('| Đủ điều kiện merge | **%s** |'
        % ('CÓ' if verdict['merge_ready'] else 'KHÔNG'))
    summary = verdict['summary']
    add('| PASS | %s |' % summary.get('PASS', '?'))
    add('| EMPTY | %s |' % summary.get('EMPTY', '?'))
    add('| BLIND | %s |' % summary.get('BLIND', '?'))
    add('| FAIL | %s |' % summary.get('FAIL', '?'))
    add('| Bộ kiểm phát hiện | %s |'
        % ('ĐẠT' if data['tests_ok'] else 'TRƯỢT'))
    add('| Toàn vẹn bằng chứng | %d vi phạm / %d chỉ báo |'
        % (data['integrity'].get('total_violations', 0),
           data['integrity'].get('total_indicators', 0)))
    pipeline_note = '%d stage, %d thất bại%s' % (
        verdict['stages'], verdict['failed_stages'],
        '' if not verdict.get('unknown_stages')
        else ', %d không khai trạng thái' % verdict['unknown_stages'])
    add('| Pipeline | %s |' % pipeline_note)
    # AQ-034. Moi hang duoi day tung in mot con so tran: `0`. Mot bang no in
    # `0` khong noi duoc su khac nhau giua "da soi 86 cho, sach ca 86" va "khong
    # soi cho nao". Hai truong hop do doc len giong het nhau, va truong hop thu
    # hai la truong hop nguy hiem.
    #
    # Nen tu day moi hang mang MAU SO cua chinh no, va ten hang noi dung pham vi
    # bo audit do soi duoc — khong hua rong hon.
    portal_missing = [f for f in (data.get('portal') or [])
                      if f['level'] == 'MISSING']
    add('| Trường portal đọc từ state không tồn tại | %d / %d truy cập soi được |'
        % (len(portal_missing), len(data.get('portal') or [])))
    telegram_missing = [f for f in (data.get('telegram') or [])
                        if f['level'] == 'MISSING']
    add('| Trường Telegram đọc từ state không tồn tại | %d / %d truy cập soi được |'
        % (len(telegram_missing), len(data.get('telegram') or [])))
    for name, age in input_ages(data):
        add('| Tuổi `%s` | %s |'
            % (name, 'KHÔNG RÕ' if age is None else '%.1f giờ' % age))
    escapes = data.get('escapes') or []
    add('| Biểu thức innerHTML chưa escape | %d / %d biểu thức trong sink |'
        % (len([f for f in escapes if f['level'] == 'UNESCAPED']), len(escapes)))
    pipeline_fields = data.get('pipeline_fields') or []
    scope = data.get('pipeline_fields_scope') or {}
    traced = scope.get('traced', len(pipeline_fields))
    total_gets = scope.get('total_gets', 0)
    coverage_pct = (traced * 100.0 / total_gets) if total_gets > 0 else 0
    add('| `.get(khoá, mặc định)` bịa số trong Python | %d / %d kiểm / %d lời gọi (%.1f%%) |'
        % (len([f for f in pipeline_fields if f['level'] == 'FABRICATED']),
           traced, total_gets, coverage_pct))
    # AQ-039/AQ-040.
    scope = data.get('coherence_scope') or {}
    deploy_scope_debt = data.get('deploy_scope') or {}
    runs = scope.get('runs') or {}
    inc = scope.get('incidents') or {}
    add('| State cùng một lần chạy | %d / %d tệp có dấu, %d lần chạy khác nhau |'
        % (runs.get('files_stamped', 0), runs.get('files_present', 0),
           len(runs.get('distinct_runs') or [])))
    reconcile_debt = data.get('reconcile_scope') or {}
    add('| Tổng crypto khớp số finding | %s |' % reconcile_debt.get('crypto', '-'))
    add('| Đơn vị lỗ hổng đối chiếu được | %s |' % reconcile_debt.get('vulns', '-'))
    add('| Nguồn hostname sau quy kết | %s |' % reconcile_debt.get('attribution', '-'))
    add('| Điểm vào triển khai khớp `package.json` | %s |'
        % ('có — %s' % (deploy_scope_debt.get('entrypoint') or '?')
           if not (data.get('deploy') or []) else 'KHÔNG — %d vi phạm'
           % len(data.get('deploy') or [])))
    add('| Sự cố đang mở truy nguợc được về quan sát | %d / %d |'
        % (inc.get('checked', 0), inc.get('open', 0)))
    if inc.get('invalidated'):
        add('| Sự cố đã thu hồi (giữ lại để rà) | %d |' % inc['invalidated'])
    add('')
    add('Mỗi hàng trên là **phạm vi của một bộ audit cụ thể**, không phải của cả')
    add('hệ thống. Một hàng `0 / 86` nghĩa là bộ đó soi 86 chỗ và cả 86 đều sạch;')
    add('nó không nói gì về những chỗ bộ đó không soi tới. AQ-038/AQ-041 liệt kê')
    add('các lớp lỗi nằm ngoài mọi hàng ở đây.')
    add('')

    if verdict['blockers']:
        add('### Đang chặn')
        add('')
        for blocker in verdict['blockers']:
            add('- %s' % blocker)
        add('')

    measured = debt_rows(data)
    add('## Nợ đo được trong lần chạy này')
    add('')
    if measured:
        add('| Hạng mục | Chi tiết | Mức |')
        add('|---|---|---|')
        for title, detail, level in measured:
            add('| %s | %s | %s |' % (title, detail, level))
    else:
        add('Không có. Mọi thứ đo được đều đạt.')
    add('')

    add('## Nợ đã ghi nhận nhưng chưa trả')
    add('')
    add('Những món này không suy ra được từ số liệu — chúng là quyết định đã')
    add('hoãn lại, kèm lý do. Danh sách nằm trong `scripts/tool_validator.py`.')
    add('')
    add('| # | Món nợ | Vì sao chưa trả |')
    add('|---:|---|---|')
    index = 0
    settled = []
    for entry in tool_validator.REMAINING_DEBT:
        item, reason = entry[0], entry[1]
        resolved_when = entry[2] if len(entry) > 2 else None
        if resolved_when is not None and data['report'] \
                and not resolved_when(data['report']):
            settled.append(item)
            continue
        index += 1
        add('| %d | %s | %s |' % (index, item, reason))
    add('')
    if settled:
        add('Đã trả (đo được trong lần chạy này):')
        add('')
        for item in settled:
            add('- ✅ %s' % item)
        add('')

    with io.open(DEBT_FILE, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    return DEBT_FILE


def main():
    validate = '--validate' in sys.argv[1:]

    print('=' * 64)
    print('SPRINT GATE')
    print('=' * 64)

    data = collect(validate=validate)
    verdict = evaluate(data)
    path = write_debt(data, verdict)

    # AQ-011. HANDOFF.md duoc SINH RA cung luc voi TECHNICAL_DEBT.md, tu cung
    # mot nguon. Ban viet tay truoc do cong bo Risk Score 74 trong khi state noi
    # 10 — va no van duoc quy trinh chi dinh la tep phai doc dau moi phien.
    try:
        import generate_handoff
        # AQ-046. Truyen KET LUAN sang, khong de HANDOFF tu tinh lai: hai phep
        # tinh doc lap tren cung mot du lieu la dung cach de hai tep lech nhau
        # lan nua, va lan truoc chung da lech.
        generate_handoff.main(verdict)
    except Exception as error:  # noqa: BLE001
        print('[WARN] khong sinh duoc HANDOFF.md: %s' % error, file=sys.stderr)

    summary = verdict['summary']
    print('')
    print('PASS %s | EMPTY %s | BLIND %s | FAIL %s' % (
        summary.get('PASS', '?'), summary.get('EMPTY', '?'),
        summary.get('BLIND', '?'), summary.get('FAIL', '?')))
    print('Bộ kiểm phát hiện : %s  (%s)'
          % ('ĐẠT' if data['tests_ok'] else 'TRƯỢT', data['tests_detail']))
    print('Toàn vẹn bằng chứng: %d vi phạm / %d chỉ báo'
          % (data['integrity'].get('total_violations', 0),
             data['integrity'].get('total_indicators', 0)))
    print('Pipeline           : %d stage, %d thất bại%s'
          % (verdict['stages'], verdict['failed_stages'],
             '' if not verdict.get('unknown_stages')
             else ', %d không khai trạng thái' % verdict['unknown_stages']))
    portal_missing = [f for f in (data.get('portal') or [])
                      if f['level'] == 'MISSING']
    print('Trường portal      : %d đọc sai / %d truy cập'
          % (len(portal_missing), len(data.get('portal') or [])))
    telegram_missing = [f for f in (data.get('telegram') or [])
                        if f['level'] == 'MISSING']
    print('Trường Telegram    : %d đọc sai / %d truy cập'
          % (len(telegram_missing), len(data.get('telegram') or [])))
    pipeline_fields = data.get('pipeline_fields') or []
    scope = data.get('pipeline_fields_scope') or {}
    fabricated = [f for f in pipeline_fields if f['level'] == 'FABRICATED']
    traced = scope.get('traced', len(pipeline_fields))
    total_gets = scope.get('total_gets', 0)
    coverage_pct = (traced * 100.0 / total_gets) if total_gets > 0 else 0
    print('Trường Python      : %d số liệu giả / %d kiểm / %d lời gọi (%.1f%%)'
          % (len(fabricated), traced, total_gets, coverage_pct))
    escapes = data.get('escapes') or []
    print('Portal escape      : %d chưa escape / %d biểu thức innerHTML'
          % (len([f for f in escapes if f['level'] == 'UNESCAPED']), len(escapes)))
    # AQ-039/AQ-040. Hai bất biến này chặn được merge, nên chúng phải đọc được
    # ở bản tóm tắt — một blocker chỉ hiện lúc đã đỏ thì không ai biết nó tồn
    # tại cho tới lần đầu nó chặn.
    scope = data.get('coherence_scope') or {}
    runs = scope.get('runs') or {}
    inc = scope.get('incidents') or {}
    print('Gắn kết lần chạy   : %d/%d tệp có dấu, %d lần chạy khác nhau'
          % (runs.get('files_stamped', 0), runs.get('files_present', 0),
             len(runs.get('distinct_runs') or [])))
    print('Nguồn gốc sự cố    : %d/%d sự cố đang mở truy ngược được%s'
          % (inc.get('checked', 0), inc.get('open', 0),
             ', %d đã thu hồi' % inc['invalidated'] if inc.get('invalidated') else ''))
    deploy_scope = data.get('deploy_scope') or {}
    print('Điểm vào triển khai: %s (%d vi phạm, %d route đối chiếu)'
          % (deploy_scope.get('entrypoint') or 'KHONG XAC DINH',
             len(data.get('deploy') or []), deploy_scope.get('routes_checked', 0)))
    reconcile_scope = data.get('reconcile_scope') or {}
    # AQ-045. Dòng này in phạm vi của HAI bất biến trong khi bộ dò chạy BỐN.
    # `attribution` và `suppressed` — hai bất biến vừa đóng AQ-002 và AQ-045 —
    # chạy thật nhưng không xuất hiện ở đâu trên màn hình cổng, nên không ai
    # đối chiếu được chúng đã đo cái gì. Một phép kiểm chạy mà không khai phạm
    # vi đọc lên giống hệt một phép kiểm không chạy: đúng lớp lỗi mà chính bộ
    # dò này tồn tại để bắt. In đủ bốn, theo đúng thứ tự `INVARIANTS`.
    print('Đối chiếu lược đồ  : %d vi phạm | crypto %s | vuln %s'
          % (len(data.get('reconcile') or []),
             reconcile_scope.get('crypto', '-'), reconcile_scope.get('vulns', '-')))
    print('                     quy kết %s'
          % reconcile_scope.get('attribution', '-'))
    print('                     lọc nhiễu %s'
          % reconcile_scope.get('suppressed', '-'))
    print('Tuổi đầu vào       : %s'
          % ' | '.join('%s %s' % (name.replace('.json', ''),
                                  'KHONG RO' if age is None else '%.1fh' % age)
                       for name, age in input_ages(data)))
    print('Nợ kỹ thuật        : %s' % os.path.relpath(path, PROJECT_ROOT))
    print('')

    if verdict['merge_ready']:
        print('KET QUA: DU DIEU KIEN MERGE')
        return 0

    print('KET QUA: CHUA DU DIEU KIEN MERGE')
    for blocker in verdict['blockers']:
        print('  - %s' % blocker)
    return 1


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

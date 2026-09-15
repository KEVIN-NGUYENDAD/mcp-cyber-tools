#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HANDOFF GENERATOR (AQ-011)

`docs/project/HANDOFF.md` — tệp mà quy trình yêu cầu đọc mỗi phiên — không tồn
tại. Hai tệp gần nhất (`AI_HANDOFF.md`, `SESSION_STATE.md`) được viết tay ngày
2026-09-07 và chưa bao giờ được sinh lại. Chúng nói:

    Risk Score      74/100        state thật:  10
    Open Incidents  18            state thật:   1
    Critical        7             state thật:   0
    Threat Level    HIGH          state thật:  LOW

Bất kỳ ai onboard theo đúng hướng dẫn sẽ khởi động với một bức tranh rủi ro sai
lệch nhiều lần — và sẽ tin nó, vì nó nằm trong tệp mà quy trình bảo phải đọc.

Đây không phải lỗi của người viết. Đây là điều luôn xảy ra với một tài liệu viết
tay công bố số liệu mà state đã trả lời: nó đúng đúng một ngày, rồi sai mãi mãi,
và không có gì đánh dấu thời điểm nó ngừng đúng.

`TECHNICAL_DEBT.md` không gặp vấn đề đó vì nó được sinh ra từ `sprint_gate.py`.
Tệp này áp dụng đúng cách chữa đó cho handoff: mọi con số đọc thẳng từ `state/`
tại thời điểm chạy. Không có chỗ nào để gõ tay một con số vào.
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
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs', 'project')
HANDOFF_FILE = os.path.join(DOCS_DIR, 'HANDOFF.md')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import run_context  # noqa: E402


def read_json(name, folder='state'):
    path = os.path.join(PROJECT_ROOT, folder, name)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def git(*args):
    try:
        out = subprocess.check_output(['git'] + list(args), cwd=PROJECT_ROOT,
                                      stderr=subprocess.STDOUT)
        return out.decode('utf-8', 'replace').strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def _age_hours(timestamp):
    """Tuổi của một mốc thời gian, tính bằng giờ. None = không khai mốc."""
    if not timestamp:
        return None
    try:
        then = datetime.fromisoformat(str(timestamp).replace('Z', ''))
    except (ValueError, TypeError):
        return None
    return (datetime.now() - then).total_seconds() / 3600.0


def unknown(value, suffix=''):
    """Thiếu dữ liệu đọc ra UNKNOWN, không đọc ra 0.

    Cùng một luật với Sprint A. Một bản handoff báo "Risk Score: 0" cho một tệp
    không đọc được sẽ khiến người tiếp nhận yên tâm về đúng thứ họ chưa hề đo.
    """
    if value is None:
        return 'UNKNOWN'
    return '%s%s' % (value, suffix)


def build(verdict=None):
    validation = read_json('tool_validation.json') or {}
    summary = validation.get('summary') or {}
    risk = read_json('risk_score.json') or {}
    incidents = read_json('incidents.json') or {}
    findings = read_json('executive_findings.json') or {}
    coverage = read_json('sensor_coverage.json') or {}
    pipeline = read_json('pipeline_results.json', folder='logs') or {}

    lines = []
    add = lines.append

    add('# HANDOFF')
    add('')
    add('Sinh tự động bởi `scripts/generate_handoff.py`. **Đừng sửa tay** — mọi '
        'con số dưới đây đọc thẳng từ `state/` lúc chạy.')
    add('')
    add('Cập nhật: %s' % datetime.now().isoformat())
    add('')

    # AQ-033 / AQ-037. Tiêu đề cũ là "Sprint vừa xong", và bảng dưới nó khai
    # `HEAD` lúc chạy. Hai thứ đó không bao giờ là một: tệp này sinh ra TRƯỚC
    # commit của chính sprint đang làm, nên `HEAD` ở đây luôn là sprint TRƯỚC.
    #
    # Ba vòng audit đọc nó như một con số trễ và đề nghị chạy lại sau commit.
    # Nhưng chạy lại sau commit thì HANDOFF phải được commit tiếp, và commit đó
    # lại làm HANDOFF trễ lần nữa — đuổi theo cái đuôi của chính nó.
    #
    # Nên không đuổi. Tệp này khai đúng điều nó biết: đây là trạng thái kho lúc
    # cổng chạy, và commit của sprint này nằm sau nó.
    add('## Trạng thái kho lúc chạy cổng')
    add('')
    add('| | |')
    add('|---|---|')
    add('| Commit lúc chạy | `%s` |'
        % (git('rev-parse', '--short', 'HEAD') or 'UNKNOWN'))
    add('| Branch | `%s` |' % (git('rev-parse', '--abbrev-ref', 'HEAD') or 'UNKNOWN'))
    add('| Tiêu đề | %s |' % (git('log', '-1', '--pretty=%s') or 'UNKNOWN'))
    dirty = bool(git('status', '--porcelain'))
    add('| Cây làm việc | %s |'
        % ('sạch' if not dirty else 'CÓ THAY ĐỔI CHƯA COMMIT'))
    add('')
    if dirty:
        add('Cây làm việc có thay đổi chưa commit, nên commit ở trên là của sprint')
        add('**trước**; công của sprint này chưa có định danh. Đó là thứ tự đúng —')
        add('cổng chạy trước khi commit — không phải một con số trễ.')
        add('')

    # AQ-046. Tệp này in bảng cổng — PASS/EMPTY/BLIND/FAIL — nhưng không in KẾT
    # LUẬN của cổng. Ngày 14/09 lúc 13:41:52, cùng một lần chạy sinh ra
    # `TECHNICAL_DEBT.md` nói "Đủ điều kiện merge: KHÔNG" và tệp này in bốn con
    # số, ba trong đó là `0`, rồi khuyên "chạy `npm run gate` trước khi mở PR" —
    # trong khi cổng vừa chạy và vừa trượt.
    #
    # Không con số nào sai. Tệp chỉ đơn giản không mang theo câu trả lời, và nó
    # là tệp ĐẦU VÀO của mỗi phiên: người đọc nó sẽ tin mình đang ở trạng thái
    # ship được.
    #
    # Mười ba vòng qua hàng đợi này đóng nhiều mục bằng cách khai vắng mặt thay
    # vì lấp (`run_scope: STANDALONE`, `Commit lúc chạy`). Đây là mặt còn lại
    # của cùng kỷ luật: khai KẾT LUẬN, đừng chỉ khai số.
    #
    # `verdict` đến thẳng từ `sprint_gate.evaluate()` của chính lần chạy này —
    # không tính lại, vì hai phép tính độc lập là đúng cách để hai tệp lại lệch
    # nhau lần nữa.
    add('## Cổng merge')
    add('')
    if verdict is None:
        # Chạy tay `generate_handoff.py` thì không có kết luận nào để in. Bảng
        # cổng khi đó là một nửa câu trả lời, và nửa câu trả lời ở đây đọc lên
        # giống hệt "đang ổn" — nên nói thẳng là chưa biết.
        add('> **Chưa biết cổng có cho merge hay không.** Tệp này được sinh ngoài')
        add('> một lần chạy cổng, nên không có kết luận nào để chép lại. Các con số')
        add('> dưới đây là của lần đo gần nhất, không phải một phán quyết.')
        add('>')
        add('> Chạy `npm run gate` để có kết luận.')
        add('')
    else:
        ready = verdict.get('merge_ready')
        add('| | |')
        add('|---|---|')
        add('| **Đủ điều kiện merge** | **%s** |'
            % ('CÓ' if ready else 'KHÔNG'))
        if not ready:
            add('')
            add('### Đang chặn')
            add('')
            for blocker in verdict.get('blockers') or []:
                add('- %s' % blocker)
        add('')
    add('| | |')
    add('|---|---|')
    for key in ('PASS', 'EMPTY', 'BLIND', 'FAIL'):
        add('| %s | %s |' % (key, unknown(summary.get(key))))
    stages = pipeline.get('stages') or pipeline.get('results') or []
    # AQ-026. Ban dau dong nay la ban sao cua chinh loi AQ-013: doc khoa
    # `success` ma bo ghi pipeline khong bao gio ghi, voi mac dinh True. Toi sua
    # o `sprint_gate.py` va de nguyen ban sao o day — dung kieu sai ma vong audit
    # truoc vua chung minh la khong scale.
    #
    # Thieu truong trang thai KHONG duoc tinh la dat; no duoc dem rieng.
    failed = [s for s in stages
              if str(s.get('status', '')).lower()
              not in ('success', 'ok', 'passed', 'skipped')
              and 'status' in s]
    unstated = [s for s in stages if 'status' not in s]
    add('| Pipeline | %d stage, %d thất bại%s |'
        % (len(stages), len(failed),
           '' if not unstated else ', %d không khai trạng thái' % len(unstated)))
    # AQ-033. Hàng này đọc từ `tool_validation.json`, còn mọi hàng quanh nó đọc
    # từ state vừa ghi trong lần chạy này. Khi validator không chạy cùng lượt,
    # nó in một con số nhiều giờ tuổi ngay cạnh các con số tươi, và không có gì
    # trên bảng nói ra điều đó — vòng 7 thấy `434 chỉ báo` trong khi cổng cùng
    # lúc đếm 573.
    #
    # Trộn hai thời điểm trong một bảng là một lỗi truth, kể cả khi cả hai số
    # đều đúng vào lúc chúng được đo. Nên tuổi đi kèm số.
    integrity = validation.get('detection_integrity') or {}
    age = _age_hours(validation.get('generated_at'))
    add('| Toàn vẹn bằng chứng | %s vi phạm / %s chỉ báo%s |'
        % (unknown(integrity.get('total_violations')),
           unknown(integrity.get('total_indicators')),
           '' if age is None else
           ' _(đo cách đây %.1f giờ)_' % age if age >= 1.0 else ' _(vừa đo)_'))
    add('')

    add('## Trạng thái thật (đọc từ state/)')
    add('')
    add('| | |')
    add('|---|---|')
    # Điểm rủi ro có thể là None khi engine không đo được thành phần nào — và
    # None phải đọc ra UNKNOWN, không phải 0.
    add('| Risk Score | %s |' % unknown(risk.get('overall_score'), '/100'))
    add('| Risk Level | %s |' % (risk.get('risk_level') or 'UNKNOWN'))
    by_severity = incidents.get('by_severity') or {}
    add('| Sự cố đang mở | %s |' % unknown(incidents.get('total_incidents')))
    add('| └ CRITICAL | %s |' % by_severity.get('CRITICAL', 0))
    add('| └ HIGH | %s |' % by_severity.get('HIGH', 0))
    add('| Phát hiện cấp điều hành | %s |'
        % unknown(findings.get('total_findings')))
    add('| └ cảnh báo chất lượng | %s |' % findings.get('quality_warnings', 0))
    add('| Rule không kết luận được | %s |'
        % len(findings.get('coverage_gaps') or []))
    add('')

    skipped = incidents.get('skipped_rules') or []
    if skipped:
        add('> ⚠ **%d luật phát hiện không đánh giá được lần này.** "0 sự cố" '
            'trên một luật không chạy được đọc y hệt "0 sự cố" trên một máy '
            'sạch — nên chúng được liệt kê ra:' % len(skipped))
        add('>')
        for item in skipped:
            add('> - %s' % item)
        add('')

    # AQ-047 (3). Hai bảng này từng bị gộp thành một cột tên `Trạng thái`, và cả
    # hai cùng dùng chữ `blind` — chữ mà bảng cổng bên trên vừa dùng cho một
    # phép đếm khác hẳn (`| BLIND | 0 |` là tool-BLIND).
    #
    # Ba phép đếm khác đơn vị mang cùng một cái tên. Hệ quả cụ thể: nguồn
    # `persistence` đọc là `covered` ngay phía trên năng lực *Scheduled Task
    # Execution* đọc là `blind`, và không có gì nói rằng hai dòng đó trả lời hai
    # câu hỏi khác nhau — nên chúng đọc như mâu thuẫn, rồi bị bỏ qua.
    add('## Vùng quan sát')
    add('')
    add('Hai bảng dưới đây trả lời hai câu hỏi khác nhau, và một bảng xanh không')
    add('bù được cho bảng kia đỏ.')
    add('')
    add('### Mù nguồn — nguồn có mở để đọc được không')
    add('')
    add('| Nguồn | Trạng thái |')
    add('|---|---|')
    for key in ('defender', 'firewall', 'security_log', 'event_logs',
                'persistence', 'processes', 'network', 'ioc'):
        add('| `%s` | %s |' % (key, coverage.get(key) or 'UNKNOWN'))
    add('')
    add('### Mù năng lực — thứ ta cần có được ghi lại không')
    add('')
    capabilities = coverage.get('detection_capabilities') or []
    blind_caps = [c for c in capabilities if c.get('status') == 'blind']
    add('| Năng lực | Trạng thái | Cách sửa |')
    add('|---|---|---|')
    for capability in capabilities:
        status = capability.get('status') or 'UNKNOWN'
        add('| %s | %s | %s |'
            % (capability.get('label'),
               '**%s**' % status if status == 'blind' else status,
               capability.get('action') or '—' if status != 'covered' else '—'))
    add('')
    if blind_caps:
        add('> **%d năng lực đang mù.** Một nguồn `covered` KHÔNG có nghĩa là kỹ'
            % len(blind_caps))
        add('> thuật tương ứng quan sát được: `persistence` mở được, nhưng')
        add('> *Scheduled Task Execution* thì không được ghi ở đâu cả. Điểm rủi ro')
        add('> đã rút trọng số tương ứng và không được phép xuống `LOW`.')
        add('')
    if coverage.get('freshness_note'):
        add('_%s_' % coverage['freshness_note'])
        add('')

    add('## Việc tiếp theo')
    add('')
    # AQ-046 (3). Khi cổng đang chặn, việc đầu tiên là cái đang chặn — không
    # phải lời khuyên chạy cổng, vì cổng vừa chạy xong và đã trả lời.
    if verdict is not None and not verdict.get('merge_ready'):
        blockers = verdict.get('blockers') or []
        add('**Cổng đang chặn. Không mở PR cho tới khi %d mục dưới đây hết:**'
            % len(blockers))
        add('')
        for index, blocker in enumerate(blockers, 1):
            add('%d. %s' % (index, blocker))
        add('')
        add('Sau đó:')
        add('')
        add('- Đọc `docs/project/AUDIT_QUEUE.md` — còn CRITICAL/HIGH thì sửa trước.')
        add('- Đọc `docs/project/TECHNICAL_DEBT.md` — nợ đo được và nợ ghi nhận.')
    else:
        add('1. Đọc `docs/project/AUDIT_QUEUE.md` — còn CRITICAL/HIGH thì sửa trước.')
        add('2. Đọc `docs/project/TECHNICAL_DEBT.md` — nợ đo được và nợ ghi nhận.')
        if verdict is None:
            add('3. `npm run gate` — tệp này chưa biết cổng có cho merge không.')
        else:
            add('3. `npm run gate` trước khi mở PR.')
    add('')
    add('## Tài liệu handoff viết tay')
    add('')
    add('`AI_HANDOFF.md` và `SESSION_STATE.md` là bản viết tay ngày 2026-09-07. '
        'Chúng **không được cập nhật theo state** và số liệu trong đó đã sai '
        'nhiều lần. Đọc tệp này thay cho chúng.')
    add('')
    return '\n'.join(lines) + '\n'


def _record_stage(duration, handoff_path):
    """AQ-050. Ghi stage nay vao ban ghi pipeline — CHI khi no thuoc ve lan chay do.

    Truoc day doan nay append vo dieu kien. Nhung `generate_handoff` khong phai
    mot stage cua `run_intelligence_pipeline`: no chay tu `npm run handoff` va tu
    `sprint_gate`. Moi lan goi cong them mot dong `Generate Handoff` vao ban ghi
    cua mot lan chay DA KET THUC, nen so stage tang dan qua cac lan chay cong —
    36, roi 41, roi 43 — trong khi pipeline van lam dung bay nhieu viec. Do that:
    45 dong ghi cho 29 stage, `Generate Handoff` 17 lan.

    Con so bi thoi phong nay khong vo hai: no la MAU SO cua dong "0 that bai".

    Nen dieu kien o day la `run_id` cua tien trinh nay bang `run_id` trong tep:
    cung mot lan chay thi ghi, khac hoac vang mat thi khong dong vao. Va ghi la
    GHI DE theo ten stage chu khong phai them — goi hai lan trong cung lan chay
    van la mot stage.
    """
    mine = run_context.run_id()
    if not mine:
        return 'STANDALONE'          # chay tay: khong co lan chay nao de ghi vao

    pipeline_results_path = os.path.join(PROJECT_ROOT, 'logs', 'pipeline_results.json')
    pipeline_data = read_json('pipeline_results.json', 'logs')
    if not pipeline_data or not isinstance(pipeline_data.get('stages'), list):
        return 'KHONG DOC DUOC'
    if pipeline_data.get('run_id') != mine:
        return 'LAN CHAY KHAC'       # ban ghi cua lan chay khac, khong phai cua ta

    entry = {
        'name': 'Generate Handoff',
        'status': 'success',
        'duration': duration,
        'run_id': mine,
        'output': {'status': 'success', 'handoff': handoff_path},
    }
    stages = pipeline_data['stages']
    for index, stage in enumerate(stages):
        if stage.get('name') == 'Generate Handoff':
            stages[index] = entry
            break
    else:
        stages.append(entry)
    try:
        with io.open(pipeline_results_path, 'w', encoding='utf-8') as handle:
            json.dump(pipeline_data, handle, indent=2, ensure_ascii=False)
    except (IOError, OSError):
        return 'KHONG GHI DUOC'
    return 'DA GHI'


def main(verdict=None):
    """AQ-046. `verdict` là kết quả `sprint_gate.evaluate()` của CHÍNH lần chạy
    này. Không có nó thì tệp phải nói là không có — xem `build()`."""
    import time
    start_time = time.time()

    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    with io.open(HANDOFF_FILE, 'w', encoding='utf-8') as handle:
        handle.write(build(verdict))

    duration = time.time() - start_time
    handoff_path = os.path.relpath(HANDOFF_FILE, PROJECT_ROOT)

    _record_stage(duration, handoff_path)

    print(json.dumps({'status': 'success',
                      'handoff': handoff_path},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

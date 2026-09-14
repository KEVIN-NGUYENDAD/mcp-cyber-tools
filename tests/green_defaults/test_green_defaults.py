# -*- coding: utf-8 -*-
"""
Sprint A + B — giá trị mặc định màu xanh, và lớp Python tính ra số.

Một hệ thống giám sát có thể sai theo hai hướng, và hai hướng đó KHÔNG đối xứng:

    sai thành ồn ào  -> ai đó bực mình, mở ra xem, sửa trong một phút
    sai thành im lặng -> không ai mở ra xem, vì màn hình đang báo bình thường

`risk = { overall_score: 0 }` cộng `score >= 40 ? ... : 'LOW'` là hướng thứ hai ở
dạng thuần khiết nhất: không đọc được dữ liệu rủi ro thì màn hình báo **rủi ro
thấp**. Kết quả an toàn nhất có thể có, sinh ra từ việc không biết gì cả.

`waap.get('score', 50)` cũng vậy, ở tầng tính toán. Và ở đó nó tệ hơn: portal chỉ
*hiển thị* số, Python *tính* ra chúng — nên một trường đọc sai không làm hỏng một
ô mà làm hỏng con số, rồi con số đó đi tiếp vào mọi bề mặt cùng một lúc, nhất
quán, và vì thế thuyết phục.
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
import pipeline_field_audit as pfa  # noqa: E402
import calculate_risk_score as crs  # noqa: E402

APP_JS = os.path.join(PROJECT_ROOT, 'web', 'app.js')
BOT_JS = os.path.join(PROJECT_ROOT, 'scripts', 'telegram', 'telegramBot.js')


def read(path):
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def code_only(text, comment_prefixes):
    """Bỏ dòng bình luận trước khi tìm mẫu cũ.

    Chính lời giải thích về lỗi cũ có chứa nguyên văn đoạn mã cũ — và một bộ
    kiểm bắt nhầm lời giải thích sẽ ép người ta xoá lời giải thích, tức là xoá
    đúng thứ đáng giữ nhất. Bài học này đã học một lần ở Sprint 14; ghi lại đây
    để lần sau không phải học lại.
    """
    fences = (chr(34) * 3, chr(39) * 3)
    kept = []
    open_fence = None
    for line in text.splitlines():
        stripped = line.strip()
        # Docstring cũng là lời giải thích. `calculate_risk_score` mô tả chính
        # đoạn mã cũ bên trong docstring của `required()`, và một phép tìm thô
        # sẽ bắt lấy nó — rồi ép xoá đúng đoạn nói VÌ SAO bản vá tồn tại.
        if open_fence:
            if open_fence in line:
                open_fence = None
            continue
        started = None
        for fence in fences:
            if stripped.startswith(fence):
                rest = stripped.split(fence, 1)[1]
                if fence not in rest:
                    started = fence
                break
        if started:
            open_fence = started
            continue
        if any(stripped.startswith(prefix) for prefix in comment_prefixes):
            continue
        kept.append(line)
    return '\n'.join(kept)


def state(filename):
    try:
        with io.open(os.path.join(PROJECT_ROOT, 'state', filename),
                     encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def run():
    suite = Suite('green defaults (Sprint A + B)')
    app = read(APP_JS)
    bot = read(BOT_JS)
    app_code = code_only(app, ('//',))
    bot_code = code_only(bot, ('//',))

    # -- SPRINT A.1: waap.get('score', 50) ---------------------------------
    risk_src = read(os.path.join(SCRIPTS_DIR, 'calculate_risk_score.py'))
    risk_code = code_only(risk_src, ('#',))
    suite.check('calculate_risk_score khong con doc waap.get("score", 50)',
                "waap.get('score', 50)" not in risk_code)
    suite.check('  -> doc dung ten that `health_score`',
                "'health_score'" in risk_src)

    waap = state('waap_score.json') or {}
    risk = state('risk_score.json') or {}
    factors = {f['name']: f for f in (risk.get('factors') or [])}
    if 'waap' in factors and waap.get('health_score') is not None:
        suite.check('Diem WAAP trong risk_score khop waap_score.json',
                    factors['waap']['health'] == waap['health_score'],
                    'risk=%s vs waap=%s' % (factors['waap']['health'],
                                            waap['health_score']))
        # Day la con so cu. Neu no quay lai, gia tri mac dinh da quay lai.
        suite.check('  -> va KHONG con la hang so fallback 50',
                    factors['waap']['health'] != 50 or waap['health_score'] == 50)

    # -- SPRINT A.2: thanh phan khong do duoc roi khoi CA tu so lan mau so ---
    calculator = crs.RiskScoreCalculator()
    value, missing = calculator.required({'health_score': 80}, 'health_score', 'x')
    suite.check('required() tra ve gia tri khi khoa co that', value == 80)
    value, missing = calculator.required({'other': 1}, 'health_score', 'x')
    suite.check('required() thieu khoa -> None + ly do',
                value is None and bool(missing), str(missing)[:70])
    suite.check('  -> va KHONG bia ra mot con so', value is not 0 and value is None)

    # -- SPRINT A.3: LOW khong duoc la mac dinh khi thieu du lieu ------------
    suite.check('Python: khong do duoc thanh phan nao -> UNMEASURED',
                "'UNMEASURED'" in risk_src)

    # Portal: `{ overall_score: 0 }` la gia tri du phong cu.
    suite.check('Portal khong con du phong { overall_score: 0 }',
                'overall_score: 0 }' not in app_code)
    suite.check('Portal co ham riskView tap trung', 'function riskView(' in app)
    suite.check('Portal: bandFromScore tra UNKNOWN khi khong phai so',
                "return 'UNKNOWN';" in app)
    # `default: return 'Acceptable risk level'` tung nuot UNKNOWN vao nhanh muc
    # thap — mot cau tra loi cho mot phep do CHUA duoc lam.
    suite.check('Portal: UNKNOWN khong roi vao "Acceptable risk level"',
                "case 'UNKNOWN': return 'Chua doc duoc du lieu rui ro"
                in app or "'UNKNOWN': return 'Chua doc" in app)

    # Telegram: mot tin nhan sai di toi dien thoai mot minh, khong co gi de so.
    suite.check('Telegram khong con du phong { overall_score: 0 }',
                'overall_score: 0 }' not in bot_code)
    suite.check('Telegram co ham riskView tap trung', 'function riskView(' in bot)
    suite.check('Telegram: thieu du lieu -> chuoi UNKNOWN',
                "level: 'UNKNOWN'" in bot)

    # Khong con bieu thuc ba ngoi tu tinh muc rui ro trong hai handler chinh:
    # moi ban sao cua no la mot cho nua co the tut ve LOW.
    inline_bands = len(re.findall(
        r"score >= 40 \? 'MEDIUM' : 'LOW'", bot_code))
    suite.check('Telegram: khong con nhan ban bieu thuc xep hang rui ro',
                inline_bands == 0, '%d ban sao' % inline_bands)

    # -- SPRINT B: bo audit lop Python --------------------------------------
    findings = pfa.audit()
    fabricated = [f for f in findings if f['level'] == 'FABRICATED']
    suite.check('Khong con so lieu gia trong pipeline Python',
                not fabricated,
                '; '.join('%s:%s' % (f['file'], f['field'])
                          for f in fabricated[:4]))
    suite.check('Bo audit co quet duoc gi do (khong phai 0 truy cap)',
                len(findings) >= 20, '%d truy cap' % len(findings))

    # Bo audit phai TU KHAI pham vi cua no. Sprint 17 vua day bai nay: mot bo
    # kiem lang le thu hep pham vi ma van bao dat la mot bo kiem da ngung kiem.
    audit_src = read(os.path.join(SCRIPTS_DIR, 'pipeline_field_audit.py'))
    suite.check('Bo audit tu khai pham vi (lan duoc bao nhieu / tong bao nhieu)',
                'PHAM VI:' in audit_src)
    total_gets = sum(pfa.coverage(name) for name in pfa.FILES)
    suite.check('  -> va tong so loi goi .get(k, default) dem duoc > 0',
                total_gets > 0, '%d' % total_gets)
    suite.check('  -> pham vi lan duoc nho hon tong (bo audit khong tu nhan la du)',
                len(findings) <= total_gets,
                '%d / %d' % (len(findings), total_gets))

    # Bo audit phai bat duoc loi that. Dung `generate_incidents.py` lam ca thu:
    # khoa `score` trong waap_score.json khong ton tai.
    waap_state = state('waap_score.json') or {}
    suite.check('waap_score.json THUC SU khong co khoa "score"',
                'score' not in waap_state,
                'khoa: %s' % sorted(waap_state.keys())[:6])
    suite.check('  -> va co khoa that `health_score`',
                'health_score' in waap_state)

    # Quy tac 5 cua generate_incidents tung chet vi mac dinh 100.
    incidents_src = read(os.path.join(SCRIPTS_DIR, 'generate_incidents.py'))
    suite.check('generate_incidents khong con waap.get("score", 100)',
                "waap.get('score', 100)" not in code_only(incidents_src, ('#',)))
    suite.check('  -> luat khong danh gia duoc thi ghi vao skipped_rules',
                'skipped_rules' in incidents_src)
    incidents = state('incidents.json') or {}
    suite.check('incidents.json cong bo skipped_rules',
                'skipped_rules' in incidents,
                'khoa: %s' % sorted(incidents.keys())[:8])

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REFRESH SENSOR COVERAGE (Sprint 15)

Làm mới `state/sensor_coverage.json` sau mỗi lần chạy pipeline.

Vì sao trước đây không làm mới
-------------------------------
`tool_validator.py` gọi THẬT cả 99 tool, mất khoảng 5 phút và có tác dụng phụ
(ghi báo cáo, chạy quét). Đưa nguyên nó vào pipeline là không được, nên
`sensor_coverage.json` đứng yên giữa các lần kiểm tay — Portal phải hiển thị
tuổi của dữ liệu kèm cảnh báo quá 24 giờ để bù.

Nhưng tệp đó trộn HAI câu trả lời có giá rất khác nhau:

    "nguồn này có mở được không?"    <- sensor_probe.py, ~10 giây, không tác dụng phụ
    "tool nào trả về bằng chứng?"    <- 99 lời gọi thật, ~5 phút, có tác dụng phụ

Nửa đắt tiền là lý do cả tệp đứng yên. Nửa rẻ tiền mới là nửa thay đổi thường
xuyên: một log bị tắt, một quyền bị thu hồi, một dịch vụ dừng — tất cả xảy ra
giữa hai lần kiểm tay, và tất cả đều thuộc nửa rẻ.

Cái bẫy phải tránh
------------------
Cách làm sai hiển nhiên là làm mới nửa rẻ rồi đóng dấu thời gian MỚI lên cả tệp.
Khi đó phần kết quả tool cũ ba ngày sẽ đọc như vừa đo xong — và đó đúng là kiểu
nói dối mà mọi sprint trước đã đi xoá.

Nên tệp mang HAI mốc thời gian, và phần nào cũ thì tự khai là cũ.

Sprint 16 — nửa đắt cũng tự làm mới
-----------------------------------
Hai mốc thời gian nói THẬT về việc nửa tool đang cũ, nhưng không ai đi làm cho
nó mới. Một con số trung thực về một thứ không bao giờ được sửa vẫn là nợ; nó
chỉ là món nợ được dán nhãn đúng.

Nên `--auto-validate` làm việc còn lại: khi nửa tool quá STALE_HOURS, nó khởi
chạy `tool_validator.py` ở NỀN, tách hẳn khỏi pipeline, rồi trả quyền điều khiển
về ngay. Lần chạy pipeline kế tiếp sẽ đọc được kết quả mới.

Ba điều cố tình làm theo cách này:

  * Chạy nền, không chờ. Thêm 5 phút vào mỗi lần chạy pipeline là cách chắc chắn
    nhất khiến người ta tắt pipeline.
  * Một khoá tiến trình. Hai validator chạy chồng nhau sẽ giành cùng một tệp
    state và cùng một hàng đợi PowerShell.
  * Nói thẳng về tác dụng phụ: validator gọi THẬT cả 99 tool, trong đó có
    `defenderQuickScan`. Tự động hoá nó nghĩa là một lần quét nhanh Defender mỗi
    ngày. Đó là hệ quả có thật, và chỗ của nó là bảng nợ, không phải phần chú
    thích không ai đọc.
"""

from __future__ import print_function

import ctypes
import io
import json
import os
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
VALIDATION_FILE = os.path.join(STATE_DIR, 'tool_validation.json')
COVERAGE_FILE = os.path.join(STATE_DIR, 'sensor_coverage.json')
LOCK_FILE = os.path.join(STATE_DIR, '.tool_validation.lock')
AUTO_LOG = os.path.join(STATE_DIR, 'logs', 'tool_validation_auto.log')

# Nửa tool được coi là cũ sau bao lâu. 20 giờ chứ không phải 24: pipeline chạy
# hằng ngày sẽ không rơi đúng vào cùng một phút mỗi lần, và một ngưỡng đúng 24
# giờ sẽ trượt qua đều đặn rồi không bao giờ kích hoạt.
STALE_HOURS = 20

# Một lần validate mất ~5 phút. Quá 20 phút thì không còn là "đang chạy" nữa,
# đó là một tiến trình đã chết để lại khoá.
MAX_RUN_MINUTES = 20

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import sensor_probe  # noqa: E402
import tool_validator  # noqa: E402


def _read_json(path):
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def _age_hours(timestamp):
    if not timestamp:
        return None
    try:
        then = datetime.fromisoformat(str(timestamp).replace('Z', ''))
    except ValueError:
        return None
    return round((datetime.now() - then).total_seconds() / 3600.0, 1)


def _pid_alive(pid):
    """Tiến trình này còn sống không?

    KHÔNG dùng `os.kill(pid, 0)` trên Windows: CPython hiện thực nó bằng
    `TerminateProcess(handle, sig)`, nên tín hiệu 0 — thứ chỉ có nghĩa "hỏi thăm"
    trên POSIX — sẽ GIẾT tiến trình với mã thoát 0. Một phép kiểm tra vô hại ở
    hệ điều hành này là một phép giết người ở hệ điều hành kia.
    """
    if not pid:
        return False
    if sys.platform != 'win32':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    SYNCHRONIZE = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def _lock_holder():
    """Ai đang chạy validator, nếu có. Trả None nếu khoá trống hoặc đã chết."""
    info = _read_json(LOCK_FILE)
    if not isinstance(info, dict):
        return None
    age = _age_hours(info.get('started_at'))
    if age is not None and age * 60 > MAX_RUN_MINUTES:
        return None
    if not _pid_alive(info.get('pid')):
        return None
    return info


def _spawn_validator():
    """Chạy tool_validator ở nền, tách hẳn khỏi tiến trình này.

    Tách hẳn là chủ ý: pipeline kết thúc trước validator, và một tiến trình con
    còn gắn với cha đã chết sẽ hoặc bị giết giữa chừng, hoặc giữ pipeline lại
    không cho thoát. Cả hai đều tệ hơn việc để nó chạy riêng.
    """
    log_dir = os.path.dirname(AUTO_LOG)
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    handle = io.open(AUTO_LOG, 'a', encoding='utf-8', errors='replace')
    handle.write('\n=== %s: tu dong chay tool_validator ===\n'
                 % datetime.now().isoformat())
    handle.flush()

    kwargs = {'stdout': handle, 'stderr': subprocess.STDOUT,
              'stdin': subprocess.PIPE, 'cwd': PROJECT_ROOT}
    if sys.platform == 'win32':
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs['creationflags'] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    child = subprocess.Popen(
        [sys.executable, os.path.join(SCRIPT_DIR, 'tool_validator.py')], **kwargs)

    with io.open(LOCK_FILE, 'w', encoding='utf-8') as lock:
        lock.write(json.dumps({'pid': child.pid,
                               'started_at': datetime.now().isoformat(),
                               'started_by': 'refresh_sensor_coverage --auto-validate'},
                              indent=2))
    return child.pid


def auto_validate(coverage):
    """Nửa tool quá cũ thì tự làm mới nó — ở nền, và chỉ một bản một lúc.

    Trả về phán quyết để ghi thẳng vào coverage. Bốn trạng thái, và bốn trạng
    thái đó phải phân biệt được với nhau trên màn hình: "còn mới", "đang chạy",
    "vừa khởi chạy", "không khởi chạy được" nói bốn điều khác nhau về mức độ tin
    được của nửa tool.
    """
    age = coverage.get('tools_age_hours')
    holder = _lock_holder()

    if holder is not None:
        return {'state': 'running', 'pid': holder.get('pid'),
                'started_at': holder.get('started_at'),
                'note': 'Một lần validate đang chạy — không khởi chạy thêm.'}

    if age is not None and age < STALE_HOURS:
        return {'state': 'fresh', 'age_hours': age,
                'note': 'Kết quả tool còn trong ngưỡng %d giờ.' % STALE_HOURS}

    try:
        pid = _spawn_validator()
    except (OSError, IOError) as error:
        # Không khởi chạy được là một sự thật phải nói ra. Im lặng ở đây sẽ để
        # nửa tool già đi vô hạn sau một dòng "tự động" mà không ai kiểm lại.
        return {'state': 'failed', 'error': str(error)[:160],
                'note': 'Không khởi chạy được tool_validator — nửa tool sẽ tiếp '
                        'tục cũ đi cho tới khi có người chạy `npm run validate`.'}

    return {'state': 'started', 'pid': pid,
            'age_hours': age,
            'log': os.path.relpath(AUTO_LOG, PROJECT_ROOT),
            'note': 'Kết quả tool đã quá %d giờ. Đã khởi chạy validate ở nền; '
                    'lần chạy pipeline kế tiếp sẽ đọc được kết quả mới.'
                    % STALE_HOURS}


def refresh(auto=False):
    """Dò lại cảm biến, dựng lại coverage, giữ nguyên phần kết quả tool.

    `auto=True` thêm một việc: nếu phần kết quả tool đã quá cũ, khởi chạy
    validate ở nền để lần sau nó không còn cũ nữa.
    """
    probes = sensor_probe.probe_all()

    previous = _read_json(VALIDATION_FILE)
    if previous is None:
        # Chưa từng chạy tool_validator. Vẫn làm mới được phần cảm biến — và
        # nói thẳng là phần tool chưa có, thay vì báo 0 tool PASS (đọc y hệt
        # "mọi tool đều hỏng").
        rows = []
        tools_at = None
    else:
        rows = previous.get('results') or []
        tools_at = previous.get('generated_at')

    now = datetime.now().isoformat()
    report = {
        'version': tool_validator.VERSION,
        'generated_at': now,
        'tools_registered': (previous or {}).get('tools_registered', len(rows)),
        'probes': probes,
        'event_4688': sensor_probe.security_log_summary(probes),
        'access_diagnosis': sensor_probe.access_diagnosis(probes),
        'fallback_sources': sensor_probe.fallback_summary(probes),
        'detection_capabilities': sensor_probe.capability_summary(probes),
        'results': rows,
        'summary': tool_validator._summarize(rows),
    }

    coverage = tool_validator.sensor_coverage(report)

    # Hai mốc thời gian, tách bạch — và đóng dấu bằng ĐÚNG hàm mà tool_validator
    # dùng. Trước Sprint 16 chỗ này có bản sao riêng, còn validator thì không
    # đóng dấu gì cả: mỗi lần validate chạy là hai mốc biến mất khỏi tệp. Lỗi đó
    # nằm im được vì validate hiếm khi chạy; tự động hoá nó biến nó thành
    # thường trực.
    tool_validator.stamp_freshness(coverage, now, tools_at,
                                   'refresh_sensor_coverage')

    if auto:
        coverage['tools_refresh'] = auto_validate(coverage)

    with io.open(COVERAGE_FILE, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(coverage, indent=2, ensure_ascii=False))

    return coverage


REPORTED = ['defender', 'firewall', 'security_log', 'event_logs',
            'persistence', 'processes', 'network', 'ioc']


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    coverage = refresh(auto='--auto-validate' in argv)

    flat = {key: coverage.get(key) for key in REPORTED}
    print(json.dumps({
        'status': 'success',
        'coverage': flat,
        'capabilities': {c['key']: c['status']
                         for c in coverage.get('detection_capabilities') or []},
        'event_4688': coverage['event_4688']['observable'],
        'tools_age_hours': coverage.get('tools_age_hours'),
        'tools_refresh': coverage.get('tools_refresh'),
    }, indent=2, ensure_ascii=False))

    # Nguồn mù là một sự thật cần biết, KHÔNG phải lỗi của pipeline. Thoát 0 để
    # một cảm biến mù không làm cả pipeline đỏ — chỗ báo động đúng là bảng
    # coverage, không phải mã thoát của một stage.
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

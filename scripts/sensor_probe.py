#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENSOR PROBE (Sprint 8: Sensor Visibility & Tool Validation)

Trả lời MỘT câu hỏi duy nhất cho mỗi nguồn dữ liệu: **đọc được hay không?**

Vì sao cần một lớp riêng cho câu hỏi này
----------------------------------------
Một tool trả về rỗng có thể mang hai nghĩa ngược nhau:

    "đã nhìn, không có gì"   -> máy sạch, kết quả đáng tin
    "không nhìn được"        -> mù, kết quả vô nghĩa

Bản thân tool không phân biệt được, vì phần lớn truy vấn dùng
`-ErrorAction SilentlyContinue`: cả hai trường hợp đều ra chuỗi rỗng. Muốn biết
sự khác nhau thì phải hỏi thẳng nguồn dữ liệu, và phải xem **văn bản lỗi**.

Ranh giới với MCP server (quan trọng)
-------------------------------------
File này CHỈ hỏi câu hỏi năng lực: "tôi có mở được nguồn này không?".
Nó KHÔNG BAO GIỜ hỏi câu hỏi phát hiện: "trong nguồn này có gì đáng ngờ?".

Mọi truy vấn phát hiện vẫn sống độc quyền trong `modules/*.js` của MCP server.
Giữ ranh giới này để không lặp lại sai lầm hai-nguồn-sự-thật mà repo đã trả giá
ba lần (risk_engine.py, assets.json, shadow_asset_detector.py).

Cái bẫy mà lớp này tồn tại để gỡ
--------------------------------
`Get-WinEvent -LogName 'Security'` báo đúng lý do: *"Attempted to perform an
unauthorized operation."*

`Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688}` trên **cùng một
máy, cùng một quyền** lại báo: *"No events were found that match the specified
selection criteria."*

Thông báo thứ hai đọc như "máy sạch" nhưng thật ra là "không mở được log".
Mọi tool lọc theo Id trên log Security đều rơi vào bẫy này. Nên thứ tự phán
quyết ở đây là: hỏi log trước, hỏi Id sau — và nếu log không mở được thì mọi
kết luận về Id đều bị vô hiệu.
"""

from __future__ import print_function

import base64
import io
import json
import os
import subprocess
import sys

# (khoá, biểu thức PowerShell). Mỗi biểu thức phải rẻ và chỉ đọc.
PROBES = [
    ('is_admin',
     "([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent())"
     ".IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"),
    ('security_log',
     "(Get-WinEvent -LogName 'Security' -MaxEvents 1 -ErrorAction Stop).Id"),
    ('security_4688',
     "(Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} -MaxEvents 1 -ErrorAction Stop).Id"),
    ('security_4624',
     "(Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} -MaxEvents 1 -ErrorAction Stop).Id"),
    ('security_4625',
     "(Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 1 -ErrorAction Stop).Id"),
    ('event_log_system',
     "(Get-WinEvent -LogName 'System' -MaxEvents 1 -ErrorAction Stop).Id"),
    ('event_log_application',
     "(Get-WinEvent -LogName 'Application' -MaxEvents 1 -ErrorAction Stop).Id"),
    ('event_log_powershell',
     "(Get-WinEvent -LogName 'Windows PowerShell' -MaxEvents 1 -ErrorAction Stop).Id"),
    ('event_log_ps_operational',
     "(Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104} "
     "-MaxEvents 1 -ErrorAction Stop).Id"),
    ('defender',
     "(Get-MpComputerStatus -ErrorAction Stop).AntivirusEnabled"),
    ('firewall',
     "@(Get-NetFirewallProfile -ErrorAction Stop).Count"),
    ('process_table',
     "@(Get-Process -ErrorAction Stop).Count"),
    ('scheduled_tasks',
     "@(Get-ScheduledTask -ErrorAction Stop).Count"),
    ('registry_run',
     "@(Get-Item -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction Stop).Count"),
    ('wmi_subscriptions',
     "@(Get-WmiObject -Namespace root\\subscription -Class __EventFilter -ErrorAction Stop).Count"),
    ('network_stack',
     "@(Get-NetTCPConnection -ErrorAction Stop).Count"),
    ('filesystem_user',
     "@(Get-ChildItem -Path $env:USERPROFILE -Force -ErrorAction Stop).Count"),
    ('audit_policy',
     "(auditpol /get /subcategory:'Process Creation' 2>&1 | Out-String).Trim()"),
]

# Vì sao không đọc được. Suy ra từ văn bản lỗi, không đoán.
REASON_ACCESS_DENIED = 'ACCESS_DENIED'
REASON_NOT_FOUND = 'NOT_FOUND'
REASON_NO_EVENTS = 'NO_EVENTS'
REASON_ERROR = 'ERROR'


def _powershell_script():
    """Sinh một script duy nhất chạy hết mọi probe và in JSON.

    Một tiến trình cho tất cả: mỗi lần khởi động PowerShell tốn ~0.5s, và
    18 probe không đáng phải trả 18 lần.
    """
    lines = [
        "$ErrorActionPreference = 'Stop'",
        "$ProgressPreference = 'SilentlyContinue'",
        "$out = @{}",
    ]
    for key, expr in PROBES:
        lines.append("try {")
        lines.append("  $v = %s" % expr)
        lines.append("  $out['%s'] = @{ ok = $true; value = ([string]$v) }" % key)
        lines.append("} catch {")
        lines.append("  $out['%s'] = @{ ok = $false; value = ''; "
                     "error = ([string]$_.Exception.Message) }" % key)
        lines.append("}")
    lines.append("Write-Output ($out | ConvertTo-Json -Depth 4 -Compress)")
    return '\n'.join(lines)


def _run_probes(timeout=120):
    script = _powershell_script()
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    try:
        raw = subprocess.check_output(
            ['powershell', '-NoProfile', '-NonInteractive',
             '-EncodedCommand', encoded],
            stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.CalledProcessError as error:
        raw = error.output or b''
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'_probe_error': str(error)}

    text = raw.decode('utf-8', 'replace').strip()
    try:
        return json.loads(text)
    except ValueError:
        return {'_probe_error': 'Không phân tích được JSON: %s' % text[:300]}


# Mã lỗi Win32 nói "thiếu quyền" nhưng văn bản kèm theo không chứa chữ nào gợi ý
# điều đó. auditpol trả về đúng dạng này: "Error 0x00000522 occurred:" — nếu không
# tra mã thì probe bị xếp nhầm thành ERROR chung chung và mất luôn nguyên nhân thật.
PRIVILEGE_CODES = (
    '0x00000522',  # ERROR_PRIVILEGE_NOT_HELD
    '0x00000005',  # ERROR_ACCESS_DENIED
    '0x80070005',  # E_ACCESSDENIED
)


def _classify_error(message):
    low = (message or '').lower()
    if any(code in low for code in PRIVILEGE_CODES):
        return REASON_ACCESS_DENIED
    if 'unauthorized' in low or 'access is denied' in low or 'không được phép' in low:
        return REASON_ACCESS_DENIED
    if 'no events were found' in low:
        return REASON_NO_EVENTS
    if 'cannot find' in low or 'does not exist' in low or 'not find path' in low:
        return REASON_NOT_FOUND
    return REASON_ERROR


def probe_all():
    """Chạy mọi probe và trả về bản đồ nguồn -> khả năng quan sát."""
    raw = _run_probes()
    probes = {}
    for key, _expr in PROBES:
        entry = raw.get(key) or {}
        ok = bool(entry.get('ok'))
        error = entry.get('error') or ''
        probes[key] = {
            'readable': ok,
            'value': entry.get('value', ''),
            'error': error,
            'reason': None if ok else _classify_error(error),
        }
    if '_probe_error' in raw:
        probes['_probe_error'] = raw['_probe_error']

    _apply_security_log_verdict(probes)
    return probes


def _apply_security_log_verdict(probes):
    """Sửa lại phán quyết cho các probe lọc theo Id trên log Security.

    Nếu bản thân log không mở được thì "No events were found" KHÔNG phải bằng
    chứng vắng mặt — nó là cùng một sự từ chối, chỉ đội một thông báo khác.
    Để nguyên thì báo cáo sẽ nói "không có 4688 nào" trong khi sự thật là
    "chưa từng nhìn thấy log".
    """
    base = probes.get('security_log') or {}
    if base.get('readable'):
        return
    for key in ('security_4688', 'security_4624', 'security_4625'):
        entry = probes.get(key)
        if not entry or entry.get('readable'):
            continue
        entry['reason'] = REASON_ACCESS_DENIED
        entry['masked_by'] = 'security_log'
        entry['note'] = ('PowerShell báo "No events were found" nhưng log '
                         'Security không mở được — đây là từ chối quyền, '
                         'không phải bằng chứng vắng mặt')


def security_log_summary(probes):
    """Câu trả lời cho câu hỏi Event ID 4688: observable true hay false, vì sao."""
    base = probes.get('security_log') or {}
    admin = (probes.get('is_admin') or {}).get('value', '').strip().lower() == 'true'
    e4688 = probes.get('security_4688') or {}

    if base.get('readable'):
        if e4688.get('readable'):
            return {
                'event_id': 4688,
                'observable': True,
                'status': 'OBSERVED',
                'reason': 'Log Security đọc được và có sự kiện 4688',
                'is_admin': admin,
            }
        return {
            'event_id': 4688,
            'observable': False,
            'status': 'AUDIT_DISABLED',
            'reason': ('Log Security đọc được nhưng không có sự kiện 4688 nào: '
                       'chính sách audit "Process Creation" đang tắt'),
            'remediation': 'auditpol /set /subcategory:"Process Creation" /success:enable (cần Administrator)',
            'is_admin': admin,
        }

    return {
        'event_id': 4688,
        'observable': False,
        'status': 'ACCESS_DENIED',
        'reason': ('Không mở được log Security: "%s". Log Security đòi quyền '
                   'Administrator, nên chưa thể biết audit 4688 bật hay tắt.'
                   % (base.get('error') or 'unknown')[:120]),
        'remediation': ('Chạy pipeline dưới quyền Administrator, rồi kiểm tra lại; '
                        'nếu vẫn trống thì bật audit "Process Creation".'),
        'is_admin': admin,
        'trap': ('Truy vấn lọc theo Id trên log này trả về "No events were found" '
                 'thay vì báo từ chối quyền — mọi tool dựa vào đó sẽ trông như '
                 '"sạch" trong khi thực ra đang mù.'),
    }


def main():
    probes = probe_all()
    print(json.dumps({
        'probes': probes,
        'event_4688': security_log_summary(probes),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

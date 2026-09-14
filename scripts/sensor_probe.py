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
    # `is_admin` trả lời "tiến trình này CÓ ĐANG chạy với quyền admin không",
    # KHÔNG phải "tài khoản này có quyền admin không". Hai câu khác hẳn nhau, và
    # Sprint 8 đã gộp chúng: báo cáo ghi `is_admin: false` rồi kết luận "thiếu
    # quyền Administrator", trong khi sự thật là tài khoản CÓ quyền, chỉ là tiến
    # trình chưa nâng quyền. Hai chẩn đoán đó dẫn tới hai cách sửa khác nhau.
    ('is_admin',
     "([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent())"
     ".IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"),
    # Tài khoản có nằm trong nhóm Administrators không — kể cả khi token hiện tại
    # đang bị UAC lọc. Có nghĩa: chỉ cần nâng quyền là xong.
    #
    # KHÔNG hỏi qua WindowsIdentity.Groups: UAC đánh dấu S-1-5-32-544 là "deny
    # only" trong token đã lọc, và .NET bỏ hẳn SID deny-only khỏi danh sách. Hỏi
    # cách đó thì một tài khoản admin chưa nâng quyền trả lời "không phải admin"
    # — đúng theo token, sai theo câu hỏi ta đang hỏi. Phải hỏi thẳng nhóm cục bộ.
    ('account_in_administrators',
     "$me = [Security.Principal.WindowsIdentity]::GetCurrent().Name; "
     "[bool](@(Get-LocalGroupMember -Group 'Administrators' -ErrorAction Stop | "
     "ForEach-Object { $_.Name }) -contains $me)"),
    # Mức toàn vẹn của tiến trình. Medium = chưa nâng quyền, High = đã nâng.
    #
    # Gọi whoami bằng ĐƯỜNG DẪN TUYỆT ĐỐI. Gọi trần `whoami` thì PATH thừa kế từ
    # tiến trình cha có thể khiến PowerShell bắt phải `whoami` của Git Bash —
    # lệnh đó không hiểu `/groups`, ghi lỗi ra stderr, và dòng lỗi ấy đủ để làm
    # hỏng JSON đầu ra của toàn bộ probe.
    #
    # WindowsIdentity.Groups KHÔNG chứa SID nhãn toàn vẹn (S-1-16-*), nên không
    # đọc được mức này từ .NET mà không P/Invoke.
    ('integrity_level',
     "$w = Join-Path $env:SystemRoot 'System32\\whoami.exe'; "
     "$line = (& $w /groups | Select-String 'Mandatory Level' | "
     "Select-Object -First 1); "
     "if ($line) { ($line.ToString() -split '\\s{2,}')[0].Trim() } else { 'unknown' }"),
    # Nhóm Event Log Readers cho phép đọc log Security mà KHÔNG cần nâng quyền.
    # Đây là con đường sửa vĩnh viễn: nâng quyền một lần để thêm thành viên, sau
    # đó mọi lần chạy pipeline bình thường đều đọc được.
    ('event_log_readers',
     "@(Get-LocalGroupMember -Group 'Event Log Readers' -ErrorAction Stop | "
     "ForEach-Object { $_.Name }) -join ', '"),
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
    # Các log thay thế ĐỌC ĐƯỢC mà không cần nâng quyền. Chúng không thay được
    # log Security, nhưng chúng là thứ duy nhất đang thực sự nhìn thấy gì đó khi
    # log Security đóng — và trước Sprint 9 không nguồn nào trong pipeline dùng.
    ('rdp_session_log',
     "(Get-WinEvent -LogName "
     "'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational' "
     "-MaxEvents 1 -ErrorAction Stop).Id"),
    ('ntlm_log',
     "(Get-WinEvent -LogName 'Microsoft-Windows-NTLM/Operational' "
     "-MaxEvents 1 -ErrorAction Stop).Id"),
    ('winrm_log',
     "(Get-WinEvent -LogName 'Microsoft-Windows-WinRM/Operational' "
     "-MaxEvents 1 -ErrorAction Stop).Id"),
]

# Log cần biết TRẠNG THÁI CẤU HÌNH, không chỉ đọc được hay không.
#
# `Get-WinEvent -LogName X` trả về "No events were found" cho CẢ HAI trường hợp
# "log đang tắt" và "log đang bật nhưng rỗng". Hai điều đó khác nhau: log rỗng
# nghĩa là đã nhìn và không có gì; log tắt nghĩa là chưa bao giờ có ai ghi.
# `Get-WinEvent -ListLog` phân biệt được, và chạy được không cần nâng quyền.
LOG_STATES = [
    ('security_log', 'Security'),
    ('event_log_system', 'System'),
    ('event_log_application', 'Application'),
    ('event_log_ps_operational', 'Microsoft-Windows-PowerShell/Operational'),
    ('rdp_session_log',
     'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational'),
    ('ntlm_log', 'Microsoft-Windows-NTLM/Operational'),
    ('winrm_log', 'Microsoft-Windows-WinRM/Operational'),
    ('task_scheduler_log', 'Microsoft-Windows-TaskScheduler/Operational'),
    ('usb_driver_log', 'Microsoft-Windows-DriverFrameworks-UserMode/Operational'),
]

# Vì sao không đọc được. Suy ra từ văn bản lỗi, không đoán.
REASON_ACCESS_DENIED = 'ACCESS_DENIED'
REASON_NOT_FOUND = 'NOT_FOUND'
REASON_NO_EVENTS = 'NO_EVENTS'
REASON_DISABLED = 'DISABLED'
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
        # `& { ... }` chứ không phải `$v = <expr>`: có probe cần nhiều câu lệnh,
        # và `$v =` chỉ gán cho câu ĐẦU TIÊN. Những câu sau đổ thẳng ra pipeline,
        # in một dòng lạc vào trước JSON và làm hỏng toàn bộ đầu ra — cả 24 probe
        # cùng lúc trở thành "không đọc được" vì một dấu chấm phẩy.
        lines.append("  $v = & { %s }" % expr)
        lines.append("  $out['%s'] = @{ ok = $true; value = ([string]$v) }" % key)
        lines.append("} catch {")
        lines.append("  $out['%s'] = @{ ok = $false; value = ''; "
                     "error = ([string]$_.Exception.Message) }" % key)
        lines.append("}")

    # Trạng thái cấu hình log, tách khỏi việc đọc được hay không.
    lines.append("$state = @{}")
    for key, log_name in LOG_STATES:
        lines.append("try {")
        lines.append("  $l = Get-WinEvent -ListLog '%s' -ErrorAction Stop" % log_name)
        lines.append("  $state['%s'] = @{ ok = $true; enabled = [bool]$l.IsEnabled; "
                     "records = ([string]$l.RecordCount) }" % key)
        lines.append("} catch {")
        lines.append("  $state['%s'] = @{ ok = $false; "
                     "error = ([string]$_.Exception.Message) }" % key)
        lines.append("}")
    lines.append("$out['_log_state'] = $state")

    lines.append("Write-Output ($out | ConvertTo-Json -Depth 5 -Compress)")
    return '\n'.join(lines)


def _run_probes(timeout=120):
    script = _powershell_script()
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    # stderr đi đường riêng, KHÔNG gộp vào stdout. Gộp lại thì bất cứ dòng cảnh
    # báo nào — kể cả từ một lệnh ngoài bị PATH bắt nhầm — cũng dán vào trước
    # JSON và giết toàn bộ kết quả.
    try:
        process = subprocess.Popen(
            ['powershell', '-NoProfile', '-NonInteractive',
             '-EncodedCommand', encoded],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw, raw_err = process.communicate(timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'_probe_error': str(error)}

    text = raw.decode('utf-8', 'replace').strip()
    try:
        return json.loads(text)
    except ValueError:
        pass

    # Vẫn cứu được: lấy đúng object JSON ngoài cùng, bỏ mọi dòng rác quanh nó.
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except ValueError:
            pass

    stderr_text = raw_err.decode('utf-8', 'replace').strip()
    return {'_probe_error': 'Không phân tích được JSON. stdout=%s stderr=%s'
                            % (text[:200], stderr_text[:200])}


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

    _apply_log_state(probes, raw.get('_log_state') or {})
    _apply_security_log_verdict(probes)
    return probes


def _apply_log_state(probes, state):
    """Gắn trạng thái cấu hình log vào probe, và tách DISABLED khỏi NO_EVENTS.

    Một log đang TẮT và một log đang BẬT nhưng rỗng đều trả về "No events were
    found". Nhưng log rỗng nghĩa là "đã nhìn, không có gì" — còn log tắt nghĩa
    là "chưa bao giờ có ai ghi vào đây". Gọi cái thứ hai là "rỗng" chính là kiểu
    tự trấn an mà cả hai sprint này tồn tại để chấm dứt.
    """
    for key, log_name in LOG_STATES:
        entry = probes.get(key)
        if entry is None:
            # Log này chưa có probe đọc thử. Trạng thái cấu hình của nó vẫn là
            # thông tin thật — bỏ đi thì một log đang TẮT sẽ biến mất khỏi báo
            # cáo hoàn toàn, thay vì hiện ra như một vùng mù đã biết.
            info = state.get(key) or {}
            if not info.get('ok'):
                continue
            enabled = bool(info.get('enabled'))
            probes[key] = {
                'readable': False,
                'value': '',
                'error': '',
                'reason': None if enabled else REASON_DISABLED,
                'log_name': log_name,
                'log_enabled': enabled,
                'log_records': info.get('records'),
                'log_state': 'enabled' if enabled else 'disabled',
                'probe_only_state': True,
            }
            continue
        info = state.get(key) or {}
        if not info.get('ok'):
            entry['log_state'] = 'unknown'
            continue

        enabled = bool(info.get('enabled'))
        records = info.get('records')
        entry['log_enabled'] = enabled
        entry['log_records'] = records
        entry['log_state'] = 'enabled' if enabled else 'disabled'

        # Log tắt: rỗng ở đây không phải bằng chứng vắng mặt.
        if not enabled and not entry.get('readable'):
            entry['reason'] = REASON_DISABLED
            entry['note'] = ('Log đang TẮT — không có bản ghi nào vì chưa bao giờ '
                             'có ai ghi vào, không phải vì không có gì xảy ra')


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


def _bool_value(probes, key):
    return (probes.get(key) or {}).get('value', '').strip().lower() == 'true'


def access_diagnosis(probes):
    """Vì sao log Security đóng, và chính xác cần làm gì để mở.

    Sprint 8 dừng ở "cần quyền Administrator". Câu đó đúng nhưng vô dụng, vì nó
    không phân biệt ba tình huống đòi ba cách sửa khác hẳn nhau:

        tài khoản không có quyền admin   -> phải nhờ người khác, hoặc chịu
        tài khoản CÓ quyền, chưa nâng    -> nâng quyền một lần là xong
        đã nâng quyền mà vẫn đóng        -> log thật sự hỏng, tìm chỗ khác

    Ở trường hợp giữa còn một cách sửa tốt hơn cả nâng quyền: thêm tài khoản vào
    nhóm `Event Log Readers`. Nâng quyền chỉ sửa cho lần chạy đó; thành viên
    nhóm sửa vĩnh viễn cho mọi lần chạy KHÔNG nâng quyền về sau.
    """
    elevated = _bool_value(probes, 'is_admin')
    in_admins = _bool_value(probes, 'account_in_administrators')
    readers_entry = probes.get('event_log_readers') or {}
    readers = (readers_entry.get('value') or '').strip()
    integrity = (probes.get('integrity_level') or {}).get('value', '').strip()

    if elevated:
        return {
            'can_fix': False,
            'situation': 'ELEVATED_BUT_STILL_DENIED',
            'reason': 'Tiến trình đã chạy quyền Administrator mà log vẫn đóng.',
            'action': 'Kiểm tra ACL của log Security (wevtutil gl Security) — '
                      'đây không còn là vấn đề quyền thông thường.',
        }
    if not in_admins:
        return {
            'can_fix': False,
            'situation': 'NO_ADMIN_RIGHTS',
            'reason': 'Tài khoản không thuộc nhóm Administrators.',
            'action': 'Cần một quản trị viên thêm tài khoản này vào nhóm '
                      '"Event Log Readers".',
        }
    return {
        'can_fix': True,
        'situation': 'HAS_RIGHTS_NOT_ELEVATED',
        'reason': ('Tài khoản CÓ trong nhóm Administrators nhưng tiến trình chưa '
                   'nâng quyền (%s). UAC lọc token thành "deny only", nên quyền '
                   'có mà không dùng được.' % (integrity or 'mức toàn vẹn Medium')),
        'action': ('Chạy `scripts/enable_security_log_access.ps1` MỘT LẦN dưới '
                   'quyền Administrator. Nó thêm tài khoản vào nhóm '
                   '"Event Log Readers" — sau đó mọi lần chạy pipeline bình '
                   'thường (không nâng quyền) đều đọc được log Security.'),
        'event_log_readers_members': readers or '(trống)',
        'note': ('Nâng quyền chỉ sửa cho một lần chạy. Thành viên nhóm sửa vĩnh '
                 'viễn — và pipeline chạy theo lịch thì không ai bấm UAC được.'),
    }


def security_log_summary(probes):
    """Câu trả lời cho câu hỏi Event ID 4688: observable true hay false, vì sao."""
    base = probes.get('security_log') or {}
    admin = _bool_value(probes, 'is_admin')
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

    diagnosis = access_diagnosis(probes)
    return {
        'event_id': 4688,
        'observable': False,
        'status': 'ACCESS_DENIED',
        'reason': ('Không mở được log Security: "%s". %s Vì log không mở được nên '
                   'chưa thể biết audit 4688 bật hay tắt.'
                   % ((base.get('error') or 'unknown')[:80], diagnosis['reason'])),
        'remediation': diagnosis['action'],
        'fixable_here': diagnosis['can_fix'],
        'situation': diagnosis['situation'],
        'is_admin': admin,
        'trap': ('Truy vấn lọc theo Id trên log này trả về "No events were found" '
                 'thay vì báo từ chối quyền — mọi tool dựa vào đó sẽ trông như '
                 '"sạch" trong khi thực ra đang mù.'),
    }


# Nguồn thay thế: đọc được KHÔNG cần nâng quyền, và che được một phần vùng mù.
# Không nguồn nào trong đây thay được log Security. Chúng chỉ làm vùng mù nhỏ
# lại, và nói rõ phần nào vẫn mù.
FALLBACK_SOURCES = [
    ('rdp_session_log',
     'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational',
     'Phiên RDP: đăng nhập, đăng xuất, kết nối lại (ID 21/22/23/24/25/39/40)',
     ['rdpLogs', 'huntRemoteDesktop']),
    ('ntlm_log', 'Microsoft-Windows-NTLM/Operational',
     'Xác thực NTLM đi và đến — tín hiệu di chuyển ngang',
     ['huntLateralMovement']),
    ('winrm_log', 'Microsoft-Windows-WinRM/Operational',
     'Thực thi từ xa qua WinRM/PowerShell Remoting',
     ['huntLateralMovement']),
    ('event_log_ps_operational', 'Microsoft-Windows-PowerShell/Operational',
     'Script block logging (4104): nội dung lệnh PowerShell đã chạy — '
     'che được phần PowerShell của vùng mù 4688, không che phần còn lại',
     ['huntEncodedPowerShell']),
]


def fallback_summary(probes):
    """Nguồn thay thế nào đang thật sự đọc được, và chúng che được gì.

    Quan trọng: đây KHÔNG phải "đã hết mù". Nó là "mù ít hơn, và biết chính xác
    phần nào còn mù". Gọi nhầm hai thứ này là cách một hệ thống giám sát tự cấp
    cho mình một chứng chỉ mà nó chưa đạt.
    """
    out = []
    for key, log_name, covers, tools in FALLBACK_SOURCES:
        entry = probes.get(key) or {}
        out.append({
            'probe': key,
            'log': log_name,
            'readable': bool(entry.get('readable')),
            'records': entry.get('log_records'),
            'covers': covers,
            'used_by': tools,
        })
    return out


def main():
    probes = probe_all()
    print(json.dumps({
        'probes': probes,
        'event_4688': security_log_summary(probes),
        'access_diagnosis': access_diagnosis(probes),
        'fallback_sources': fallback_summary(probes),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

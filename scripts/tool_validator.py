#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOOL VALIDATOR (Sprint 8 dung len, Sprint 9 mo rong)

Gọi thật từng tool của MCP server, rồi phán quyết mỗi tool vào một trong bốn ô:

    PASS   tool chạy và trả về bằng chứng thật (>= 1 bản ghi)
    EMPTY  tool chạy, không có gì để trả về, và nguồn dữ liệu ĐỌC ĐƯỢC
           -> "đã nhìn, máy sạch": rỗng ở đây là một câu trả lời đáng tin
    BLIND  tool chạy, không có gì để trả về, nhưng nguồn dữ liệu KHÔNG đọc được
           -> "không nhìn được": rỗng ở đây không có nghĩa gì cả
    FAIL   tool báo lỗi, hết giờ, hoặc trả về thứ không phân tích được

Vì sao EMPTY và BLIND phải tách đôi
-----------------------------------
Chúng trông giống hệt nhau trong mọi log, mọi dashboard, mọi báo cáo — nhưng
nói hai điều ngược nhau. Gộp chúng lại là cách một hệ thống giám sát tự trấn an
mình: 0 phát hiện trên một cảm biến đã chết đọc y như 0 phát hiện trên một máy
sạch. Sprint trước đã dựng `coverage` cho bốn cuộc săn; sprint này áp cùng kỷ
luật đó cho toàn bộ 99 tool.

Phán quyết BLIND không đến từ bản thân tool (tool không biết nó đang mù) mà từ
`sensor_probe.py`, lớp duy nhất được phép hỏi "nguồn này có mở được không".

Đầu ra
------
    state/tool_validation.json          ma trận đầy đủ, máy đọc
    state/sensor_coverage.json          COVERED / PARTIAL / BLIND theo nguồn
    docs/project/TOOL_VALIDATION_REPORT.md   bản người đọc
"""

from __future__ import print_function

import io
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from mcp_bridge import McpBridge, McpBridgeError, as_list  # noqa: E402
import sensor_probe  # noqa: E402

try:
    from state_manager import write_state_atomic
except ImportError:
    write_state_atomic = None

VERSION = '2.0.0'
CALL_TIMEOUT = 90

STATUS_PASS = 'PASS'
STATUS_EMPTY = 'EMPTY'
STATUS_BLIND = 'BLIND'
STATUS_FAIL = 'FAIL'

COVERED = 'covered'
PARTIAL = 'partial'
BLIND = 'blind'

BACKSLASH = chr(92)
BACKTICK = chr(96)

# --------------------------------------------------------------------------
# Đối số an toàn cho những tool đòi tham số.
# Nguyên tắc: chỉ đọc, trỏ vào thứ chắc chắn tồn tại, không chạm mạng ngoài.
# --------------------------------------------------------------------------
TOOL_ARGS = {
    'ping': {'host': '127.0.0.1', 'count': 1},
    'tracert': {'host': '127.0.0.1'},
    'nslookup': {'host': 'localhost'},
    'scanPort': {'host': '127.0.0.1', 'port': 135},
    'processByPid': {'pid': 4},                      # PID 4 = System, luôn có
    'checkHash': {'path': os.path.join(PROJECT_ROOT, 'package.json')},
    'fileMetadata': {'path': os.path.join(PROJECT_ROOT, 'package.json')},
    'readLogFile': {'path': os.path.join(PROJECT_ROOT, 'package.json'), 'lines': 5},
    'collectEvidence': {'incidentId': 'VALIDATION-PROBE'},
    'eventLogs': {'logName': 'System', 'count': 10},
    'timeline': {'days': 1},
    'securityAudit': {'auditType': 'quick'},
    'processDetails': {'processId': 4},               # PID 4 = System, luôn có
    'get_asset_status': {'source': 'defender_status'},
}

# --------------------------------------------------------------------------
# Tool -> nguồn cảm biến. Đây là bản đồ quyết định EMPTY hay BLIND, nên nó phải
# viết tay: không suy được từ tên tool.
# --------------------------------------------------------------------------
SENSOR_OF = {
    # Defender
    'defenderStatus': 'defender', 'defenderThreats': 'defender',
    'defenderHistory': 'defender', 'defenderExclusions': 'defender',
    'defenderQuickScan': 'defender', 'collectDefender': 'defender',
    # Firewall
    'firewallStatus': 'firewall', 'firewallRules': 'firewall',
    'inboundRules': 'firewall', 'outboundRules': 'firewall',
    'disabledFirewallRules': 'firewall', 'collectFirewall': 'firewall',
    # Security log (đòi Administrator)
    'securityLogs': 'security_log', 'failedLogons': 'security_log',
    'successfulLogons': 'security_log', 'rdpLogs': 'security_log',
    'huntCredentialDumping': 'security_log', 'huntLateralMovement': 'security_log',
    'huntRemoteDesktop': 'security_log', 'timeline': 'security_log',
    # collectLogs mặc định logName='Security' — nguồn của nó là log Security,
    # không phải event log nói chung. Xếp nhầm sẽ làm một tool mù trông như một
    # tool hỏng, và làm event_logs trông tệ hơn sự thật.
    'collectLogs': 'security_log',
    # Event log khác (System / Application / Windows PowerShell)
    'eventLogs': 'event_logs', 'systemLogs': 'event_logs',
    'applicationLogs': 'event_logs', 'powershellLogs': 'event_logs',
    'usbLogs': 'event_logs', 'serviceLogs': 'event_logs',
    'huntEncodedPowerShell': 'event_logs',
    # Persistence
    'startupPrograms': 'persistence', 'startupFolders': 'persistence',
    'scheduledTasks': 'persistence', 'registryRunKeys': 'persistence',
    'registryRunOnce': 'persistence', 'wmiPersistence': 'persistence',
    'servicePersistence': 'persistence', 'browserPersistence': 'persistence',
    'dllHijackLocations': 'persistence', 'persistenceAudit': 'persistence',
    'collectStartupItems': 'persistence', 'huntPersistence': 'persistence',
    'huntSuspiciousTasks': 'persistence', 'huntSuspiciousServices': 'persistence',
    'servicesChecker': 'persistence', 'runningServices': 'persistence',
    'stoppedServices': 'persistence', 'autoStartServices': 'persistence',
    'disabledServices': 'persistence', 'collectServices': 'persistence',
    # Processes
    'tasklist': 'processes', 'processMonitor': 'processes',
    'processDetails': 'processes', 'processTree': 'processes',
    'processByPid': 'processes', 'runningProcesses': 'processes',
    'cpuUsage': 'processes', 'memoryUsage': 'processes',
    'topProcesses': 'processes', 'suspiciousProcesses': 'processes',
    'collectProcesses': 'processes', 'huntLivingOffTheLand': 'processes',
    # Network
    'ipconfig': 'network', 'netstat': 'network', 'arp': 'network',
    'routePrint': 'network', 'dnsCache': 'network', 'ping': 'network',
    'tracert': 'network', 'nslookup': 'network', 'scanPort': 'network',
    'activeConnections': 'network', 'collectNetworkState': 'network',
    'huntNetworkBeacons': 'network',
    # IOC / filesystem forensics
    'huntIndicators': 'ioc', 'suspiciousExecutables': 'ioc',
    'alternateDataStreams': 'ioc', 'tempFiles': 'ioc',
    'downloadsFolder': 'ioc', 'desktopFiles': 'ioc',
    'recentFiles': 'ioc', 'recycleBin': 'ioc',
    'checkHash': 'ioc', 'fileMetadata': 'ioc', 'readLogFile': 'ioc',
    # Host inventory (không nằm trong 7 nguồn báo cáo, vẫn phải kiểm)
    'whoami': 'host', 'hostname': 'host', 'systemInfo': 'host',
    'localUsers': 'host', 'localAdmins': 'host', 'installedSoftware': 'host',
    'sharedFolders': 'host', 'environmentVars': 'host',
    'userProfiles': 'host', 'loggedOnUsers': 'host',
    # Tổng hợp / đọc state, không phải cảm biến PowerShell
    'collectEvidence': 'composite', 'securityAudit': 'composite',
    'get_security_score': 'internal_state', 'get_daily_brief': 'internal_state',
    'get_recent_incidents': 'internal_state', 'get_asset_status': 'internal_state',
}

# Nguồn -> các probe phải đọc được. Nguồn nào thiếu probe thì coi như đọc được
# (không có cách nào phủ định nó).
SENSOR_PROBES = {
    'defender': ['defender'],
    'firewall': ['firewall'],
    'security_log': ['security_log'],
    'event_logs': ['event_log_system', 'event_log_application',
                   'event_log_powershell', 'event_log_ps_operational'],
    'persistence': ['scheduled_tasks', 'registry_run', 'wmi_subscriptions'],
    'processes': ['process_table'],
    'network': ['network_stack'],
    'ioc': ['filesystem_user', 'process_table'],
    'host': ['process_table'],
    'composite': [],
    'internal_state': [],
}

# Bảy nguồn người dùng yêu cầu báo cáo, cộng security_log tách riêng vì nó là
# nguồn duy nhất đang mù và gộp nó vào event_logs sẽ giấu mất điều đó.
REPORTED_SENSORS = ['defender', 'firewall', 'security_log', 'event_logs',
                    'persistence', 'processes', 'network', 'ioc']

SENSOR_LABEL = {
    'defender': 'Defender', 'firewall': 'Firewall',
    'security_log': 'Security Event Log', 'event_logs': 'Event Logs (System/App/PS)',
    'persistence': 'Persistence', 'processes': 'Processes',
    'network': 'Network', 'ioc': 'IOC / Filesystem',
    'host': 'Host inventory', 'composite': 'Tổng hợp',
    'internal_state': 'State nội bộ',
}

# Tool chỉ trả về đường dẫn tới báo cáo vừa ghi, không trả về quan sát nào cho
# người gọi. Không thể tính là PASS: không có bằng chứng nào đi ra khỏi tool.
#
# Sprint 10 đã dọn sạch danh sách này: `timeline`, `collectEvidence`,
# `collectLogs` và `securityAudit` nay trả về bằng chứng thật kèm đường dẫn,
# nên chúng được phán quyết bằng đúng luật như 95 tool còn lại.
#
# Giữ lại cái bảng rỗng thay vì xoá hẳn: cửa này sẽ mở lại nếu có ai thêm một
# tool chỉ ghi file, và luật "không có bằng chứng đi ra thì không phải PASS"
# vẫn phải có chỗ để sống.
REPORT_WRITERS = {}


# --------------------------------------------------------------------------
# Nợ kỹ thuật đã nhìn thấy nhưng chưa trả. Viết ra đây thay vì để trong đầu:
# một món nợ không được ghi sẽ được phát hiện lại từ đầu ở sprint sau.
# --------------------------------------------------------------------------
# Mot so mon no co the duoc tra bang mot hanh dong NGOAI ma nguon (chay script
# nang quyen, bat mot chinh sach). Mot bang no viet cung se van liet ke chung
# sau khi chung da duoc tra — va mot bang no noi sai thi khong ai tin nua.
#
# Nen moi muc co the kem mot ham doc trang thai DO DUOC trong chinh lan chay
# nay. Muc nao da tra thi roi khoi bang, va hien o dong tong ket ngay duoi.
def _debt_security_log_closed(report):
    return not (report['probes'].get('security_log') or {}).get('readable')


def _debt_script_block_partial(report):
    for cap in report.get('detection_capabilities') or []:
        if cap.get('key') == 'script_block_logging':
            return cap.get('status') != COVERED
    return True


REMAINING_DEBT = [
    ('Log Security vẫn đóng — 5 tool còn mù, và chưa thể biết audit 4688 bật hay tắt',
     'Không phải lỗi mã, và Sprint 9 đã dựng sẵn cách sửa: chạy MỘT LẦN '
     '`scripts/enable_security_log_access.ps1` dưới quyền Administrator. '
     'Script sửa hệ thống thì phải do người quyết định chạy, không phải pipeline.',
     _debt_security_log_closed),
    ('Log `Microsoft-Windows-TaskScheduler/Operational` và '
     '`Microsoft-Windows-DriverFrameworks-UserMode/Operational` đang TẮT',
     'Bật chúng là thay đổi cấu hình máy. Cho tới lúc đó, "không có bản ghi nào" '
     'ở hai nguồn này nghĩa là chưa ai từng ghi, không phải không có gì xảy ra.'),
    ('Nguồn thay thế chỉ che được MỘT PHẦN vùng mù: TerminalServices thấy phiên '
     'chứ không thấy chi tiết xác thực; NTLM thấy NTLM chứ không thấy Kerberos',
     'Đây là giới hạn của chính các log đó, không sửa được bằng mã. Mọi bản ghi '
     'từ nguồn thay thế đều mang cờ `Fallback = true` để không ai nhầm bớt mù '
     'với hết mù.'),
    ('Script Block Logging chỉ PARTIAL: log `PowerShell/Operational` đọc được và '
     'có sự kiện 4104, nhưng chính sách `EnableScriptBlockLogging` đang TẮT',
     'Khi chính sách tắt, PowerShell vẫn tự ghi 4104 cho những khối lệnh NÓ cho '
     'là đáng ngờ — nên "có bản ghi" ở đây không đồng nghĩa "đang ghi đầy đủ". '
     'Đây chính là lý do phải có ô ⚠ PARTIAL: một cột hai giá trị sẽ tô xanh '
     'chỗ này. Bật chính sách là thay đổi cấu hình máy, phải do người quyết định.',
     _debt_script_block_partial),
    ('`state/sensor_coverage.json` không tự làm mới theo pipeline',
     'tool_validator.py gọi thật 99 tool và có tác dụng phụ (ghi báo cáo, quét). '
     'Portal hiển thị tuổi của dữ liệu và cảnh báo khi quá 24 giờ.'),
    ('`assets.json` có hai người ghi: asset_builder.py ghi `all_assets`, '
     'extract_asset_intelligence.py ghi `assets`',
     'Tồn tại từ trước Sprint 8, đã ghi nhận, chưa gộp.'),
]


# --------------------------------------------------------------------------
# Kiểm kê tĩnh: tool nào truyền script nhiều dòng vào runPowerShell
# --------------------------------------------------------------------------

def _template_scripts(body):
    """Lấy nội dung mọi runPowerShell(`...`) trong thân tool."""
    out = []
    for match in re.finditer(r'runPowerShell\(\s*' + BACKTICK, body):
        k = match.end()
        while k < len(body):
            if body[k] == BACKSLASH:
                k += 2
                continue
            if body[k] == BACKTICK:
                break
            k += 1
        out.append(body[match.end():k])
    return out


def static_inventory(modules_dir=None):
    """Đọc modules/*.js, trả về tool -> cách nó dựng lệnh.

    `43 tool multi-line` của các sprint trước là số **lời gọi** lúc đó: 9 trong
    hunting.js cộng 34 ở nơi khác. hunting.js nay dựng script qua jsonOrEmpty()
    nên script không còn nằm thẳng trong lời gọi — vẫn là script nhiều dòng, chỉ
    là kiểm kê tĩnh phải đếm nó ở dạng `variable`. Tổng vẫn là 43.
    """
    modules_dir = modules_dir or os.path.join(PROJECT_ROOT, 'modules')
    tool_re = re.compile(r'server\.tool\(\s*"([A-Za-z0-9_]+)"')
    inventory = {}

    for filename in sorted(os.listdir(modules_dir)):
        if not filename.endswith('.js'):
            continue
        source = io.open(os.path.join(modules_dir, filename), encoding='utf-8').read()
        marks = [(m.start(), m.group(1)) for m in tool_re.finditer(source)]
        for index, (pos, name) in enumerate(marks):
            end = marks[index + 1][0] if index + 1 < len(marks) else len(source)
            body = source[pos:end]
            scripts = _template_scripts(body)
            multiline = sum(1 for s in scripts if '\n' in s.strip())
            inline = len(scripts) - multiline
            # runPowerShell(biến) — hunting.js sau khi viết lại
            indirect = len(re.findall(
                r'runPowerShell\(\s*[^' + BACKTICK + r'\s]', body))

            if multiline:
                style = 'multiline'
            elif indirect:
                style = 'multiline_indirect'
            elif inline:
                style = 'inline'
            elif re.search(r'runCmd\(', body):
                style = 'cmd'
            else:
                style = 'none'

            inventory[name] = {
                'module': filename,
                'script_style': style,
                'ps_multiline': multiline,
                'ps_inline': inline,
                'ps_indirect': indirect,
                'run_cmd': len(re.findall(r'runCmd\(', body)),
            }
    return inventory


# --------------------------------------------------------------------------
# Đếm bằng chứng
# --------------------------------------------------------------------------

# Tool trả về một envelope có tóm tắt thì SỐ QUAN SÁT nằm trong envelope, không
# phải là "1 object". Đếm envelope là 1 sẽ làm một tool thu được 300 sự kiện đọc
# y hệt một tool thu được 0 — và cái thứ hai đáng lẽ phải là EMPTY.
ENVELOPE_COUNT_KEYS = ('recordCount', 'logCount', 'eventCount', 'returned')


def evidence_count(result):
    """Bao nhiêu bản ghi quan sát thật sự đi ra khỏi tool."""
    parsed = result.get('parsed')
    if parsed is not None:
        if isinstance(parsed, list):
            return len(parsed)
        if isinstance(parsed, dict):
            for key in ENVELOPE_COUNT_KEYS:
                if isinstance(parsed.get(key), int):
                    return parsed[key]
            return 1 if parsed else 0
        return 1 if parsed not in ('', None) else 0

    text = (result.get('raw_text') or '').strip()
    if not text or text == '[]':
        return 0
    return len([line for line in text.splitlines() if line.strip()])


def sensor_readable(sensor, probes):
    """Nguồn này có mở được không, và probe nào nói ngược lại."""
    keys = SENSOR_PROBES.get(sensor, [])
    if not keys:
        return True, []
    dead = [k for k in keys if not (probes.get(k) or {}).get('readable', True)]
    return (len(dead) < len(keys)), dead


# Tool mà nguồn dữ liệu phụ thuộc vào ĐỐI SỐ, không phải vào tên tool.
# `eventLogs(logName='Security')` và `eventLogs(logName='System')` là hai cảm
# biến khác nhau: một cái đòi nâng quyền, một cái không. Tra nguồn chỉ theo tên
# tool sẽ gọi lần gọi thứ nhất là FAIL, trong khi sự thật là BLIND — và FAIL
# nghĩa là "có gì đó cần sửa trong mã", một việc không tồn tại ở đây.
ARG_SENSOR = {
    'eventLogs': ('logName', {'Security': 'security_log'}),
    'collectLogs': ('logName', {'Security': 'security_log',
                                'System': 'event_logs',
                                'Application': 'event_logs'}),
}


def sensor_for(tool, args):
    rule = ARG_SENSOR.get(tool)
    if rule and args:
        field, mapping = rule
        override = mapping.get(args.get(field))
        if override:
            return override
    return SENSOR_OF.get(tool, 'composite')


def classify(tool, result, probes, args=None):
    """Bốn ô: PASS / EMPTY / BLIND / FAIL. Kèm lý do khi không phải PASS."""
    sensor = sensor_for(tool, args)
    count = evidence_count(result)

    if result.get('error') or not result.get('ok'):
        # Một tool hỏng *vì* nguồn của nó không mở được thì không phải tool hỏng:
        # nó là tool mù. Gọi nó là FAIL sẽ sinh ra một danh sách sửa lỗi gồm
        # toàn những thứ không có gì để sửa trong mã, và giấu mất lý do thật là
        # thiếu quyền. Nên hỏi probe trước khi kết luận.
        readable, dead = sensor_readable(sensor, probes)
        if not readable:
            reasons = ['%s: %s' % (k, (probes.get(k) or {}).get('reason')
                                   or 'không đọc được') for k in dead]
            return STATUS_BLIND, 0, '; '.join(reasons)
        return STATUS_FAIL, count, (result.get('error') or 'tool báo lỗi')[:200]

    if tool in REPORT_WRITERS:
        return STATUS_EMPTY, 0, REPORT_WRITERS[tool]

    if count > 0:
        return STATUS_PASS, count, None

    readable, dead = sensor_readable(sensor, probes)
    if not readable:
        reasons = []
        for key in dead:
            entry = probes.get(key) or {}
            reasons.append('%s: %s' % (key, entry.get('reason') or 'không đọc được'))
        return STATUS_BLIND, 0, '; '.join(reasons)

    # Trường hợp riêng: tool lọc Id trên log Security. Nguồn của nó là
    # security_log và đã bị bắt ở trên; nếu lọt xuống đây thì log đọc được thật.
    return STATUS_EMPTY, 0, 'nguồn đọc được, không có bản ghi nào khớp'


# --------------------------------------------------------------------------
# Chạy
# --------------------------------------------------------------------------

# Giá trị thử cho tham số, suy từ tên và kiểu trong inputSchema.
# Cố ý KHÁC mặc định: mục đích là đi vào nhánh mà lần gọi mặc định không đi qua.
PARAM_PROBE_VALUES = {
    'limit': 3, 'count': 3, 'lines': 3, 'days': 2, 'top': 3, 'maxEvents': 3,
    'port': 135, 'threshold': 1, 'minutes': 5, 'hours': 1,
}


def param_variants(tool, schema):
    """Sinh các bộ đối số KHÁC mặc định để kiểm cả nhánh có tham số.

    Sprint 8 gọi mỗi tool đúng một lần bằng đối số mặc định. Điều đó chứng minh
    được một điều duy nhất: đường mặc định chạy. Một tool nhận `limit` có thể
    chạy hoàn hảo khi không ai truyền gì và vỡ với mọi giá trị được truyền vào —
    và trong một lần kiểm chỉ dùng mặc định, nó hiện lên là PASS.
    """
    props = (schema or {}).get('properties') or {}
    if not props:
        return []

    base = dict(TOOL_ARGS.get(tool) or {})
    variants = []

    numeric_args = dict(base)
    touched = []
    enum_fields = []

    for name, spec in props.items():
        if not isinstance(spec, dict):
            continue
        if spec.get('enum'):
            enum_fields.append((name, spec['enum']))
            continue
        kind = spec.get('type')
        if name in PARAM_PROBE_VALUES and kind in ('number', 'integer', None):
            numeric_args[name] = PARAM_PROBE_VALUES[name]
            touched.append(name)

    if touched:
        variants.append(('tham số: %s' % ', '.join(sorted(touched)), numeric_args))

    # Mỗi giá trị enum là một nhánh mã riêng — nhánh không được gọi là nhánh
    # không được kiểm.
    for name, values in enum_fields:
        for value in values:
            if base.get(name) == value:
                continue
            args = dict(base)
            args[name] = value
            variants.append(('%s=%s' % (name, value), args))

    return variants


def validate(verbose=True):
    probes = sensor_probe.probe_all()
    event_4688 = sensor_probe.security_log_summary(probes)
    inventory = static_inventory()

    rows = []
    with McpBridge() as bridge:
        definitions = bridge.list_tool_defs()
        available = [d['name'] for d in definitions]
        schemas = {d['name']: d.get('inputSchema') for d in definitions}

        def call(name, args):
            try:
                return bridge.call_tool(name, args, timeout=CALL_TIMEOUT)
            except McpBridgeError as error:
                return {'tool': name, 'ok': False, 'empty': True, 'raw_text': '',
                        'parsed': None, 'error': str(error)[:200], 'duration': None}

        for name in available:
            args = TOOL_ARGS.get(name)
            result = call(name, args)
            status, count, reason = classify(name, result, probes, args)

            # Nhánh có tham số. Hỏng ở đây KHÔNG đổi status chính: status chính
            # trả lời "tool có quan sát được gì không", còn đây trả lời "tool có
            # chịu được đối số không". Gộp hai câu lại thì mất cả hai.
            variants = []
            for label, variant_args in param_variants(name, schemas.get(name)):
                variant_result = call(name, variant_args)
                variant_status, variant_count, variant_reason = classify(
                    name, variant_result, probes, variant_args)
                variants.append({
                    'label': label,
                    'args': variant_args,
                    'status': variant_status,
                    'evidence_count': variant_count,
                    'note': variant_reason,
                })

            broken = [v for v in variants if v['status'] == STATUS_FAIL]
            meta = inventory.get(name, {})
            rows.append({
                'tool': name,
                'module': meta.get('module', '?'),
                'script_style': meta.get('script_style', '?'),
                'sensor': sensor_for(name, args),
                'status': status,
                'evidence_count': count,
                'duration': result.get('duration'),
                'args_used': args or {},
                'note': reason,
                'variants_tested': len(variants),
                'variants_failed': [
                    {'label': v['label'], 'note': v['note']} for v in broken],
            })
            if verbose:
                flag = ''
                if broken:
                    flag = '  [%d/%d biến thể hỏng: %s]' % (
                        len(broken), len(variants),
                        ', '.join(v['label'] for v in broken))
                print('  %-26s %-6s %5s  %s%s' % (
                    name, status, count, reason or '', flag))
                sys.stdout.flush()

    missing = sorted(set(inventory) - set(available))
    unmapped = sorted(r['tool'] for r in rows if r['tool'] not in SENSOR_OF)

    return {
        'version': VERSION,
        'generated_at': datetime.now().isoformat(),
        'tools_registered': len(available),
        'tools_in_source': len(inventory),
        'tools_not_registered': missing,
        'tools_without_sensor_map': unmapped,
        'probes': probes,
        'event_4688': event_4688,
        'access_diagnosis': sensor_probe.access_diagnosis(probes),
        'fallback_sources': sensor_probe.fallback_summary(probes),
        'detection_capabilities': sensor_probe.capability_summary(probes),
        'results': rows,
        'summary': _summarize(rows),
    }


def _summarize(rows):
    summary = {STATUS_PASS: 0, STATUS_EMPTY: 0, STATUS_BLIND: 0, STATUS_FAIL: 0}
    for row in rows:
        summary[row['status']] = summary.get(row['status'], 0) + 1
    summary['total'] = len(rows)
    summary['evidence_records'] = sum(r['evidence_count'] for r in rows)
    summary['variants_tested'] = sum(r.get('variants_tested', 0) for r in rows)
    summary['tools_with_param_defects'] = sum(
        1 for r in rows if r.get('variants_failed'))
    return summary


# --------------------------------------------------------------------------
# Coverage theo nguồn
# --------------------------------------------------------------------------

def sensor_coverage(report):
    """COVERED / PARTIAL / BLIND cho từng nguồn.

    COVERED  nguồn đọc được, có tool trả bằng chứng, không tool nào hỏng
    PARTIAL  nguồn đọc được nhưng có tool hỏng, hoặc chỉ đọc được một phần,
             hoặc không tool nào lấy được bằng chứng dù nguồn mở
    BLIND    không mở được nguồn
    """
    probes = report['probes']
    by_sensor = {}
    for row in report['results']:
        by_sensor.setdefault(row['sensor'], []).append(row)

    details = {}
    for sensor in REPORTED_SENSORS:
        rows = by_sensor.get(sensor, [])
        keys = SENSOR_PROBES.get(sensor, [])
        dead = [k for k in keys if not (probes.get(k) or {}).get('readable', True)]

        counts = {}
        for row in rows:
            counts[row['status']] = counts.get(row['status'], 0) + 1

        if keys and len(dead) == len(keys):
            status = BLIND
        elif dead:
            status = PARTIAL
        elif counts.get(STATUS_FAIL):
            status = PARTIAL
        elif counts.get(STATUS_PASS):
            status = COVERED
        else:
            status = PARTIAL

        reason = None
        if status == BLIND:
            entry = probes.get(dead[0]) or {}
            reason = entry.get('error') or entry.get('reason')
        elif dead:
            reason = 'đọc được một phần; mù: %s' % ', '.join(dead)
        elif counts.get(STATUS_FAIL):
            reason = '%d tool hỏng' % counts[STATUS_FAIL]
        elif not counts.get(STATUS_PASS):
            reason = 'nguồn mở nhưng không tool nào trả về bằng chứng'

        details[sensor] = {
            'label': SENSOR_LABEL.get(sensor, sensor),
            'status': status,
            'tools': len(rows),
            'pass': counts.get(STATUS_PASS, 0),
            'empty': counts.get(STATUS_EMPTY, 0),
            'blind': counts.get(STATUS_BLIND, 0),
            'fail': counts.get(STATUS_FAIL, 0),
            'evidence_records': sum(r['evidence_count'] for r in rows),
            'probes_dead': dead,
            'reason': reason,
        }

    flat = {sensor: details[sensor]['status'] for sensor in REPORTED_SENSORS}
    coverage = {'generated_at': report['generated_at'], 'version': VERSION}
    coverage.update(flat)
    coverage['summary'] = {
        'covered': sum(1 for s in flat.values() if s == COVERED),
        'partial': sum(1 for s in flat.values() if s == PARTIAL),
        'blind': sum(1 for s in flat.values() if s == BLIND),
    }
    coverage['event_4688'] = report['event_4688']
    coverage['details'] = details
    coverage['tool_summary'] = _tool_summary(report)
    # Portal can biet KHONG CHI "nguon nao mu" ma con "co sua duoc khong".
    # Mot o do khong kem loi khuyen thi chi la mot o do.
    coverage['access_diagnosis'] = report.get('access_diagnosis')
    coverage['fallback_sources'] = report.get('fallback_sources')
    # Ba nang luc phat hien duoc goi ten. Chung KHONG trung voi bang nguon o
    # tren: nguon tra loi "co mo duoc khong", nang luc tra loi "co dang ghi thu
    # ta can khong". `event_logs` dang COVERED trong khi Script Block Logging chi
    # PARTIAL — dung mot cot thi mat han su khac nhau do.
    capabilities = report.get('detection_capabilities') or []
    coverage['detection_capabilities'] = capabilities
    coverage['capability_summary'] = {
        'covered': sum(1 for c in capabilities if c.get('status') == COVERED),
        'partial': sum(1 for c in capabilities if c.get('status') == PARTIAL),
        'blind': sum(1 for c in capabilities if c.get('status') == BLIND),
    }
    return coverage


def _tool_summary(report):
    """Những con số mà Portal từng viết cứng thành ONLINE / 90+ / ACTIVE.

    Mỗi cờ `*_active` ở đây phải trả lời được câu hỏi "dựa vào đâu": nó là
    "có ít nhất một tool thuộc nhóm này trả về bằng chứng thật trong lần kiểm
    gần nhất", không phải một hằng số viết trong HTML.
    """
    summary = report['summary']
    by_module = {}
    for row in report['results']:
        by_module.setdefault(row['module'], []).append(row)

    def any_pass(module):
        return any(r['status'] == STATUS_PASS for r in by_module.get(module, []))

    return {
        'status': 'VERIFIED' if summary[STATUS_FAIL] == 0 else 'DEGRADED',
        'tool_count': report['tools_registered'],
        'pass': summary[STATUS_PASS],
        'empty': summary[STATUS_EMPTY],
        'blind': summary[STATUS_BLIND],
        'fail': summary[STATUS_FAIL],
        'evidence_records': summary['evidence_records'],
        'threat_hunting_active': any_pass('hunting.js'),
        'dfir_active': any_pass('forensics.js') or any_pass('incident.js'),
        'event_hub_active': any_pass('eventHub.js'),
        'last_sync': report['generated_at'],
    }


# --------------------------------------------------------------------------
# Ghi
# --------------------------------------------------------------------------

def _write_json(path, payload):
    if write_state_atomic:
        write_state_atomic(path, payload)
        return
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False))


ICON = {STATUS_PASS: '✅', STATUS_EMPTY: '⚪', STATUS_BLIND: '❌', STATUS_FAIL: '🔴'}
COVERAGE_ICON = {COVERED: '✅', PARTIAL: '⚠', BLIND: '❌'}


def render_markdown(report, coverage):
    out = []
    add = out.append
    summary = report['summary']

    add('# TOOL VALIDATION REPORT')
    add('')
    add('**Sprint**: 8 — Sensor Visibility & Tool Validation  ')
    add('**Sinh tự động bởi**: `scripts/tool_validator.py` v%s  ' % VERSION)
    add('**Thời điểm**: %s  ' % report['generated_at'])
    add('**Máy**: %s (Administrator: %s)' % (
        os.environ.get('COMPUTERNAME', '?'),
        report['event_4688'].get('is_admin')))
    add('')
    add('Đừng sửa tay file này — chạy lại `python scripts/tool_validator.py`.')
    add('')
    add('## Bốn ô phán quyết')
    add('')
    add('| Ô | Nghĩa |')
    add('|---|---|')
    add('| ✅ PASS | Tool chạy, trả về bằng chứng thật (≥ 1 bản ghi) |')
    add('| ⚪ EMPTY | Tool chạy, không có gì để trả về, **và nguồn đọc được** — "đã nhìn, sạch" |')
    add('| ❌ BLIND | Tool chạy, không có gì để trả về, **nguồn không đọc được** — rỗng vô nghĩa |')
    add('| 🔴 FAIL | Tool báo lỗi, hết giờ, hoặc trả về thứ không phân tích được |')
    add('')
    add('EMPTY và BLIND trông giống hệt nhau ở mọi nơi khác trong hệ thống, nhưng')
    add('nói hai điều ngược nhau. Phán quyết BLIND không đến từ bản thân tool —')
    add('tool không biết nó đang mù — mà từ `scripts/sensor_probe.py`.')
    add('')
    add('## Tổng')
    add('')
    add('| | Số lượng |')
    add('|---|---:|')
    add('| Tool đăng ký | %d |' % report['tools_registered'])
    add('| ✅ PASS | %d |' % summary[STATUS_PASS])
    add('| ⚪ EMPTY | %d |' % summary[STATUS_EMPTY])
    add('| ❌ BLIND | %d |' % summary[STATUS_BLIND])
    add('| 🔴 FAIL | %d |' % summary[STATUS_FAIL])
    add('| Tổng bản ghi thu được | %d |' % summary['evidence_records'])
    add('| Biến thể tham số đã kiểm | %d |' % summary.get('variants_tested', 0))
    add('| Tool lỗi khi truyền tham số | %d |' %
        summary.get('tools_with_param_defects', 0))
    add('')
    add('Kiểm bằng đúng đối số mặc định chỉ chứng minh được đường mặc định chạy.')
    add('Mỗi tool có tham số còn được gọi lại với giá trị khác mặc định và với')
    add('từng giá trị enum — nhánh không được gọi là nhánh không được kiểm.')
    add('')

    caps = report.get('detection_capabilities') or []
    if caps:
        add(u'## Năng lực phát hiện')
        add('')
        add(u'Bảng "Sensor coverage" bên dưới trả lời: **mở được nguồn không?**')
        add(u'Bảng này trả lời một câu khác hẳn: **nguồn đó có đang GHI thứ ta**')
        add(u'**cần không?** Hai câu này không thay nhau được. Ngay trên máy này, nguồn')
        add(u'`event_logs` đang ✅ COVERED trong khi Script Block Logging chỉ ⚠ PARTIAL:')
        add(u'log đọc được toàn bộ, nhưng thứ được ghi vào đó lại có chọn lọc. Đọc hết')
        add(u'một cuốn sổ ghi chép có chọn lọc không phải là nhìn thấy mọi thứ.')
        add('')
        add(u'| Năng lực | Trạng thái | Nguồn | Vì sao |')
        add('|---|---|---|---|')
        for cap in caps:
            add('| **%s** | %s %s | %s | %s |' % (
                cap['label'], COVERAGE_ICON.get(cap['status'], '?'),
                cap['status'].upper(), cap.get('detail', ''),
                ' '.join((cap.get('reason') or '').split())))
        add('')
        actionable = [c for c in caps if c.get('action')]
        if actionable:
            add(u'Cách mở từng vùng mù:')
            add('')
            for cap in actionable:
                add('- **%s** — %s' % (cap['label'], cap['action']))
            add('')

    add('## Sensor coverage')
    add('')
    add('| Nguồn | Trạng thái | Tool | PASS | EMPTY | BLIND | FAIL | Bản ghi | Ghi chú |')
    add('|---|---|---:|---:|---:|---:|---:|---:|---|')
    for sensor in REPORTED_SENSORS:
        d = coverage['details'][sensor]
        add('| %s | %s %s | %d | %d | %d | %d | %d | %d | %s |' % (
            d['label'], COVERAGE_ICON[d['status']], d['status'].upper(),
            d['tools'], d['pass'], d['empty'], d['blind'], d['fail'],
            d['evidence_records'], d['reason'] or ''))
    add('')

    e = report['event_4688']
    add('## Event ID 4688 — Process Creation')
    add('')
    add('| | |')
    add('|---|---|')
    add('| `observable` | **%s** |' % str(e['observable']).lower())
    add('| Trạng thái | `%s` |' % e['status'])
    add('| Quyền Administrator | %s |' % e.get('is_admin'))
    add('| Nguyên nhân | %s |' % e['reason'])
    if e.get('remediation'):
        add('| Khắc phục | %s |' % e['remediation'])
    add('')
    if e.get('trap'):
        add('> **Cái bẫy**: %s' % e['trap'])
        add('')

    diag = report.get('access_diagnosis') or {}
    if diag:
        add('## Chẩn đoán quyền truy cập')
        add('')
        add('Sprint 8 dừng ở "cần quyền Administrator". Câu đó đúng nhưng không')
        add('dùng được, vì nó gộp ba tình huống đòi ba cách sửa khác hẳn nhau.')
        add('')
        add('| | |')
        add('|---|---|')
        add('| Tình huống | `%s` |' % diag.get('situation'))
        add('| Sửa được tại đây | **%s** |' % str(diag.get('can_fix')).lower())
        add('| Nguyên nhân | %s |' % diag.get('reason'))
        add('| Cách sửa | %s |' % diag.get('action'))
        if diag.get('event_log_readers_members'):
            add('| Thành viên nhóm "Event Log Readers" | %s |'
                % diag['event_log_readers_members'])
        add('')
        if diag.get('note'):
            add('> %s' % diag['note'])
            add('')

    fallbacks = report.get('fallback_sources') or []
    if fallbacks:
        add('## Nguồn thay thế (đọc được, không cần nâng quyền)')
        add('')
        add('Đây **không phải** "đã hết mù". Đây là "mù ít hơn, và biết chính xác')
        add('phần nào còn mù". Mọi bản ghi từ các nguồn này mang cờ `Fallback = true`.')
        add('')
        add('| Log | Đọc được | Bản ghi | Che được gì | Tool dùng |')
        add('|---|---|---:|---|---|')
        for item in fallbacks:
            add('| `%s` | %s | %s | %s | %s |' % (
                item['log'].split('/')[-1] if '/' in item['log'] else item['log'],
                '✅' if item['readable'] else '❌',
                item.get('records') or '-',
                item['covers'],
                ', '.join('`%s`' % t for t in item['used_by'])))
        add('')

    add('## Ma trận tool')
    add('')
    add('| Tool | Module | Kiểu lệnh | Nguồn | Trạng thái | Bản ghi | Biến thể | Ghi chú |')
    add('|---|---|---|---|---|---:|---:|---|')
    for row in sorted(report['results'],
                      key=lambda r: (r['module'], r['tool'])):
        tested = row.get('variants_tested', 0)
        failed = row.get('variants_failed') or []
        variant_cell = '-' if not tested else (
            '%d ✅' % tested if not failed
            else '%d/%d 🔴' % (len(failed), tested))
        note = (row['note'] or '')[:110]
        if failed:
            note = (note + ' | lỗi khi: ' +
                    ', '.join(v['label'] for v in failed))[:180]
        add('| `%s` | %s | %s | %s | %s %s | %d | %s | %s |' % (
            row['tool'], row['module'].replace('.js', ''), row['script_style'],
            row['sensor'], ICON[row['status']], row['status'],
            row['evidence_count'], variant_cell, note))
    add('')

    add('## Technical debt còn lại')
    add('')
    add('Những thứ lần kiểm này phát hiện nhưng KHÔNG sửa, kèm lý do.')
    add('')
    add('Bảng lọc theo trạng thái ĐO ĐƯỢC của chính lần chạy này. Món nợ nào đã')
    add('trả thì rời khỏi bảng — một bảng nợ liệt kê thứ đã sửa xong là một bảng')
    add('không ai còn tin, và nó sẽ âm thầm che luôn những món chưa trả.')
    add('')
    add('| # | Món nợ | Vì sao chưa trả |')
    add('|---:|---|---|')
    outstanding, settled = [], []
    for entry in REMAINING_DEBT:
        item, reason = entry[0], entry[1]
        resolved_when = entry[2] if len(entry) > 2 else None
        if resolved_when is not None and not resolved_when(report):
            settled.append(item)
        else:
            outstanding.append((item, reason))
    for index, (item, reason) in enumerate(outstanding, 1):
        add('| %d | %s | %s |' % (index, item, reason))
    add('')
    if settled:
        add('Đã trả trong lần chạy này:')
        add('')
        for item in settled:
            add('- ✅ %s' % item)
        add('')

    add('## Probe cảm biến thô')
    add('')
    add('| Probe | Đọc được | Giá trị / Lỗi |')
    add('|---|---|---|')
    for key, _expr in sensor_probe.PROBES:
        p = report['probes'].get(key) or {}
        detail = p.get('value') if p.get('readable') else (p.get('error') or '')
        add('| `%s` | %s | %s |' % (
            key, '✅' if p.get('readable') else '❌', str(detail)[:110]))
    add('')
    return '\n'.join(out) + '\n'


def main():
    print('=' * 64)
    print('TOOL VALIDATION — gọi thật từng tool MCP')
    print('=' * 64)

    report = validate()

    coverage = sensor_coverage(report)

    state_dir = os.path.join(PROJECT_ROOT, 'state')
    docs_dir = os.path.join(PROJECT_ROOT, 'docs', 'project')
    if not os.path.isdir(docs_dir):
        os.makedirs(docs_dir)

    _write_json(os.path.join(state_dir, 'tool_validation.json'), report)
    _write_json(os.path.join(state_dir, 'sensor_coverage.json'), coverage)

    markdown = render_markdown(report, coverage)
    with io.open(os.path.join(docs_dir, 'TOOL_VALIDATION_REPORT.md'),
                 'w', encoding='utf-8') as handle:
        handle.write(markdown)

    s = report['summary']
    print('')
    print('PASS %d | EMPTY %d | BLIND %d | FAIL %d  (tổng %d tool, %d bản ghi)' % (
        s[STATUS_PASS], s[STATUS_EMPTY], s[STATUS_BLIND], s[STATUS_FAIL],
        s['total'], s['evidence_records']))
    print('Coverage: %s' % json.dumps(
        {k: coverage[k] for k in REPORTED_SENSORS}, ensure_ascii=False))
    print('Event 4688: observable=%s (%s)' % (
        report['event_4688']['observable'], report['event_4688']['status']))
    # In riêng ba năng lực phát hiện. Dòng "Coverage" ở trên nói nguồn nào MỞ
    # ĐƯỢC; dòng này nói nguồn nào đang GHI thứ ta cần. Trên máy này hai dòng đó
    # mâu thuẫn nhau (event_logs=covered, script_block=partial) — và chính chỗ
    # mâu thuẫn là chỗ đáng đọc.
    print('Năng lực: %s' % ' | '.join(
        '%s=%s' % (c['key'], c['status'])
        for c in (report.get('detection_capabilities') or [])))
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

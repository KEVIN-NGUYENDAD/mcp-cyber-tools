#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IOC QUALITY (Sprint 17)

Một điểm tin cậy 0–100 cho mọi chỉ báo, và hai phán quyết đi kèm nó: bằng chứng
có đủ không, và nó nói về MÁY NÀO.

Vì sao không dùng một danh sách bốn trường cho tất cả
-----------------------------------------------------
Yêu cầu ban đầu là mọi IOC phải có `matched_text`, `source_log`, `event_id`,
`timestamp`, thiếu thì trừ điểm. Áp thẳng bốn trường đó cho tất cả sẽ hỏng ngay
ở chỉ báo đầu tiên: một tác vụ theo lịch KHÔNG có Event ID, vì nó không đến từ
event log. Trừ điểm nó vì thiếu một trường không thể tồn tại sẽ dẫn tới đúng một
trong hai kết cục, và cả hai đều tệ:

    hoặc người ta điền một giá trị giả cho qua,
    hoặc cả một lớp chỉ báo đúng đắn bị dìm xuống LOW vĩnh viễn.

Nên mỗi chỉ báo khai LỚP BẰNG CHỨNG của nó, và chỉ bị chấm trên những trường mà
lớp đó CÓ THỂ cung cấp. Đây đúng là kỷ luật của `trust_basis.points_available` ở
Sprint 11: thứ không quan sát được phải rời khỏi cả tử số lẫn mẫu số, chứ không
phải ở lại mẫu số và kéo điểm xuống.

`confidence_basis` ghi lại từng thành phần kiếm được bao nhiêu trên bao nhiêu, để
một con số 68 luôn truy ngược được về lý do — thay vì phải tin nó.
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
REPORT_FILE = os.path.join(PROJECT_ROOT, 'docs', 'project', 'IOC_QUALITY_REPORT.md')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import detection_quality  # noqa: E402

VERSION = '1.0.0'

HUNT_FILES = [
    ('credential_dumping', 'hunting_credential_dumping.json'),
    ('persistence', 'hunting_persistence.json'),
    ('lateral_movement', 'hunting_lateral_movement.json'),
    ('suspicious_processes', 'hunting_suspicious_processes.json'),
]

# --------------------------------------------------------------------------
# Lớp bằng chứng: mỗi lớp CÓ THỂ cung cấp những trường nào
# --------------------------------------------------------------------------
CLASS_EVENT_LOG = 'EVENT_LOG'
CLASS_PROCESS = 'PROCESS_TABLE'
CLASS_REGISTRY = 'REGISTRY'
CLASS_TASK = 'SCHEDULED_TASK'
CLASS_SERVICE = 'SERVICE'
CLASS_FILESYSTEM = 'FILESYSTEM'
CLASS_UNKNOWN = 'UNKNOWN'

# `event_id` CHỈ có mặt ở lớp EVENT_LOG. Đó là toàn bộ lý do bảng này tồn tại.
CLASS_FIELDS = {
    CLASS_EVENT_LOG: ('matched_text', 'source_log', 'event_id', 'timestamp'),
    CLASS_PROCESS: ('matched_text', 'source_log', 'timestamp'),
    CLASS_REGISTRY: ('matched_text', 'source_log', 'timestamp'),
    CLASS_TASK: ('matched_text', 'source_log', 'timestamp'),
    CLASS_SERVICE: ('matched_text', 'source_log', 'timestamp'),
    CLASS_FILESYSTEM: ('matched_text', 'source_log', 'timestamp'),
    CLASS_UNKNOWN: ('matched_text', 'timestamp'),
}

# Gợi ý suy ra lớp từ chính chỉ báo. Thứ tự có ý nghĩa: `event_id` là bằng chứng
# dứt khoát nhất và được hỏi trước mọi phép đoán theo tên.
TYPE_HINTS = [
    (CLASS_TASK, ('scheduledtask', 'scheduled task')),
    (CLASS_REGISTRY, ('registry', 'runkey', 'run key', 'runonce', 'wmi')),
    (CLASS_SERVICE, ('service',)),
    (CLASS_PROCESS, ('process', 'lolbin', 'living off the land', 'binary')),
    (CLASS_FILESYSTEM, ('startupfolder', 'startup folder', 'browser')),
]

# Nguồn cụ thể của từng lớp, dùng khi chính cuộc săn không khai `source_log`.
CLASS_SOURCE = {
    CLASS_PROCESS: 'ProcessTable (Get-CimInstance Win32_Process)',
    CLASS_REGISTRY: 'Registry (HKLM/HKCU Run, RunOnce, WMI subscriptions)',
    CLASS_TASK: 'TaskScheduler (Get-ScheduledTask)',
    CLASS_SERVICE: 'ServiceControlManager (Get-CimInstance Win32_Service)',
    CLASS_FILESYSTEM: 'Filesystem (Startup folders, user profile)',
}

EVENT_LOG_OF = {
    'credential_dumping': 'Security',
    'lateral_movement': 'Security',
}


def evidence_class(indicator, hunt):
    """Chỉ báo này đến từ loại nguồn nào."""
    if indicator.get('event_id'):
        return CLASS_EVENT_LOG
    haystack = ' '.join(str(indicator.get(key) or '')
                        for key in ('type', 'category', 'detection_method',
                                    'description')).lower()
    for klass, hints in TYPE_HINTS:
        if any(hint in haystack for hint in hints):
            return klass
    if hunt in EVENT_LOG_OF:
        return CLASS_EVENT_LOG
    return CLASS_UNKNOWN


def derive_source_log(indicator, klass, hunt):
    """`source_log` mà cuộc săn không khai — suy ra, và nói rõ là suy ra."""
    if indicator.get('source_log'):
        return indicator['source_log'], False
    if klass == CLASS_EVENT_LOG:
        return EVENT_LOG_OF.get(hunt, 'Security'), True
    return CLASS_SOURCE.get(klass), True


def derive_matched_text(indicator, klass):
    """Đoạn văn bản đã kích hoạt chỉ báo này.

    Với lớp không phải event log, thứ "khớp" là chính định danh của đối tượng —
    tên tác vụ, đường dẫn tiến trình, khoá registry. Nó phải là thứ TÌM LẠI ĐƯỢC
    trong evidence, nếu không thì bất biến của Sprint 12 sẽ (đúng đắn) từ chối nó.
    """
    if indicator.get('matched_text'):
        return indicator['matched_text'], False
    evidence = ' '.join(str(part) for part in (indicator.get('evidence') or []))
    for field in ('name', 'process', 'command_line', 'command', 'location'):
        value = indicator.get(field)
        if value and str(value) in evidence:
            return str(value), True
    return None, False


# --------------------------------------------------------------------------
# Quy kết: IP + hostname + asset_id
# --------------------------------------------------------------------------
SCOPE_LOCAL = 'LOCAL_HOST'
SCOPE_REMOTE = 'REMOTE_PEER'

ATTR_FULL = 'FULL'
ATTR_PARTIAL = 'PARTIAL'
ATTR_NONE = 'UNATTRIBUTED'


def asset_id_for(ip):
    """Định danh tài sản ổn định, suy ra từ IP.

    Suy ra chứ không phát sinh ngẫu nhiên: cùng một IP phải cho cùng một mã ở
    mọi lần chạy và trên mọi tiến trình, nếu không thì hai nửa hệ thống sẽ nói
    về cùng một máy bằng hai cái tên.
    """
    if not ip:
        return None
    digest = hashlib.sha1(str(ip).encode('utf-8')).hexdigest()[:8].upper()
    return 'ASSET-%s' % digest


def load_inventory():
    """IP -> bản ghi tài sản, kèm lỗi nếu kho không đọc được.

    Trả về LUÔN cả lỗi thay vì nuốt nó. Một kho tài sản không đọc được sẽ khiến
    mọi chỉ báo thành UNATTRIBUTED — nếu lý do bị nuốt, bảng chất lượng sẽ nói
    "không quy kết được máy nào" trong khi sự thật là "không mở được kho".
    Hai câu đó cần hai hành động khác nhau.
    """
    import asset_store
    assets, _meta, error = asset_store.read_assets_safe()
    inventory = dict((a.get('ip'), a) for a in assets if a.get('ip'))
    return inventory, error


def real_hostname(asset):
    """Tên máy THẬT, hay chỉ là IP chép sang một cột khác?

    `extract_asset_intelligence` đọc trường `hostname` của Nessus, mà trường đó
    chứa IP, rồi ghi nó vào cả `ip` lẫn `hostname`. Một cột "Hostname" hiển thị
    `192.168.0.10` trông như đã phân giải được tên, trong khi nó chỉ là ô bên
    cạnh chép sang. Ở đây gọi thẳng nó là chưa phân giải.
    """
    if not asset:
        return None
    hostname = asset.get('hostname')
    if not hostname:
        return None
    if str(hostname).strip() == str(asset.get('ip') or '').strip():
        return None
    return hostname


def local_identity():
    """Tên và IP của chính máy đang chạy. Nhớ lại một lần, dùng nhiều lần."""
    global _LOCAL
    if _LOCAL is None:
        try:
            import ioc_attribution
            _LOCAL = ioc_attribution.local_host_identity()
        except Exception:  # noqa: BLE001
            _LOCAL = {'hostname': None, 'ips': []}
    return _LOCAL


_LOCAL = None


def enrich_systems(systems, inventory):
    """Thêm hostname + asset_id vào từng hệ thống, và nói rõ thiếu cái gì.

    Máy cục bộ được xử lý riêng, và đó không phải một ngoại lệ cho tiện: kho tài
    sản dựng từ một lần quét mạng, mà một lần quét mạng không bao giờ biết tên
    của máy vừa chạy nó rõ bằng chính máy đó. Bắt máy cục bộ phải chờ kho xác
    nhận tên của nó là vứt đi nguồn đáng tin nhất đang có trong tay.
    """
    local = local_identity()
    enriched = []
    for system in systems or []:
        ip = system.get('ip')
        asset = inventory.get(ip)
        hostname = real_hostname(asset)
        if not hostname and system.get('scope') == SCOPE_LOCAL:
            hostname = local.get('hostname') or None
        asset_id = asset_id_for(ip)

        missing = []
        if not ip:
            missing.append('ip')
        if not hostname:
            missing.append('hostname')
        if not asset_id:
            missing.append('asset_id')

        row = dict(system)
        row['asset_id'] = asset_id
        row['hostname'] = hostname
        row['hostname_resolved'] = hostname is not None
        row['hostname_source'] = (
            'local host' if (hostname and system.get('scope') == SCOPE_LOCAL
                             and not real_hostname(asset))
            else ('asset inventory' if hostname else 'unresolved'))
        row['in_inventory'] = ip in inventory if ip else False
        row['identified'] = not missing
        row['missing_identity'] = missing
        enriched.append(row)
    return enriched


def attribution_quality(systems):
    """FULL / PARTIAL / UNATTRIBUTED cho cả chỉ báo."""
    if not systems:
        return ATTR_NONE, 'Không có hệ thống nào được quy kết'
    with_ip = [s for s in systems if s.get('ip')]
    if not with_ip:
        return ATTR_NONE, 'Không hệ thống nào có IP'
    full = [s for s in systems if s.get('identified') and s.get('hostname_source') != 'unresolved']
    if len(full) == len(systems):
        return ATTR_FULL, '%d hệ thống đủ IP + hostname + asset_id' % len(full)
    missing = sorted(set(m for s in systems for m in s.get('missing_identity') or []))
    unresolved = [s.get('ip') for s in systems if s.get('hostname_source') == 'unresolved']
    if full or unresolved:
        reason = '%d/%d hệ thống đủ định danh' % (len(full), len(systems))
        if missing:
            reason += '; số còn lại thiếu %s' % ', '.join(missing)
        if unresolved:
            reason += '; %d chưa phân giải hostname: %s' % (len(unresolved), ', '.join(unresolved[:3]))
        return ATTR_PARTIAL, reason
    return (ATTR_PARTIAL,
            'Có IP và asset_id nhưng thiếu %s' % ', '.join(missing))


# --------------------------------------------------------------------------
# Tiếng ồn: thứ có thật, nhưng không phải phát hiện
# --------------------------------------------------------------------------
NOISE_SELF = 'SELF_OBSERVATION'
NOISE_DEV = 'DEVELOPER_ACTIVITY'
NOISE_ROUTINE = 'ROUTINE_OS_ACTIVITY'

DEV_HINTS = ('node.exe', 'python.exe', 'git.exe', 'code.exe', 'msbuild.exe',
             'powershell_ise.exe', 'windowsterminal.exe', 'conhost.exe')

# Tài khoản máy đăng nhập vào chính nó là hoạt động nền của Windows, xảy ra hàng
# nghìn lần mỗi ngày. Nó KHÔNG bị xoá — chỉ bị hạ xuống tiếng ồn, kèm lý do.
ROUTINE_HINTS = ('logon type:\t\t5', 's-1-5-18', 'security id:\t\ts-1-5-19',
                 'security id:\t\ts-1-5-20')


def noise_class(indicator, hunt):
    """Chỉ báo này là tiếng ồn loại nào, hay không phải tiếng ồn.

    Cố ý KHÔNG xoá. Một chỉ báo biến mất khỏi tệp thì không ai kiểm lại được
    quyết định loại nó, và bộ lọc tiếng ồn chính là chỗ dễ giấu một phát hiện
    thật nhất. Nó ở lại, mang cờ `suppressed` và một câu lý do đọc được.
    """
    haystack = ' '.join(str(part) for part in (indicator.get('evidence') or []))
    haystack += ' ' + str(indicator.get('command_line') or '')
    haystack += ' ' + str(indicator.get('process') or '')
    lowered = haystack.lower()

    reason = detection_quality.is_self_observation(haystack)
    if reason:
        return NOISE_SELF, reason

    high_severity = indicator.get('severity') in ('CRITICAL', 'HIGH')

    # AQ-019. Miễn trừ này trước đây phủ CẢ HAI bảng gợi ý, và đó là chỗ sai.
    #
    # Lập luận ban đầu — "kẻ tấn công dùng đúng những nhị phân mà lập trình viên
    # dùng" — đúng cho DEV_HINTS: `node.exe` trong evidence là một PHỎNG ĐOÁN
    # theo tên tiến trình, và một tên tiến trình có thể bị đặt trùng. Lọc theo
    # phỏng đoán ở mức cao là tự bịt mắt đúng chỗ đáng nhìn nhất.
    #
    # Nhưng nó không đúng cho ROUTINE_HINTS. `s-1-5-18` không phải một phỏng
    # đoán theo tên — đó là SID của tài khoản SYSTEM, một sự thật dứt khoát về
    # chủ thể của sự kiện. `logon type 5` là một sự thật về loại phiên. Những
    # thứ này không đổi nghĩa khi severity đổi.
    #
    # Hậu quả của việc gộp hai bảng: hai sự kiện 4648 — Windows đăng nhập người
    # dùng vào chính tài khoản Microsoft của họ trên localhost — mang nhãn HIGH
    # vì Event ID, nên được miễn trừ, nên thoát bộ lọc, nên chiếm 58% điểm rủi
    # ro toàn hệ thống. Bản ghi cần soi lại nhất là bản ghi chắc chắn thoát.
    #
    # Đây đúng là phân biệt đã rút ra ở Sprint 17 giữa từ khoá mơ hồ (`lsass`)
    # và token công cụ (`mimikatz`), áp vào một chỗ khác.
    if not high_severity:
        for hint in DEV_HINTS:
            if hint in lowered:
                return NOISE_DEV, 'công cụ phát triển trên chính máy này: %s' % hint

    # ROUTINE_HINTS áp ở MỌI mức: chúng là sự thật về chủ thể, không phải
    # phỏng đoán theo tên.
    for hint in ROUTINE_HINTS:
        if hint in lowered:
            return NOISE_ROUTINE, (
                'hoạt động nền của Windows: %s%s'
                % (' '.join(hint.split()),
                   ' (mức %s do Event ID, nhưng chủ thể là tài khoản hệ thống)'
                   % indicator.get('severity') if high_severity else ''))

    return None, None


# --------------------------------------------------------------------------
# Điểm tin cậy
# --------------------------------------------------------------------------
MAX_EVIDENCE = 40
MAX_INTEGRITY = 20
MAX_ATTRIBUTION = 25
MAX_SOURCE = 15

SOURCE_POINTS = {
    'LIVE_OBSERVED': MAX_SOURCE,
    'OBSERVED': 12,
    'DERIVED': 6,
    'SIMULATED': 0,
}

BAND_HIGH = 75
BAND_MEDIUM = 50


def band(score):
    if score >= BAND_HIGH:
        return 'HIGH'
    if score >= BAND_MEDIUM:
        return 'MEDIUM'
    return 'LOW'


def score_indicator(indicator, hunt, inventory):
    """Chấm một chỉ báo, sửa nó tại chỗ, trả về chính nó."""
    klass = evidence_class(indicator, hunt)
    required = CLASS_FIELDS[klass]

    source_log, source_derived = derive_source_log(indicator, klass, hunt)
    if source_log:
        indicator['source_log'] = source_log
    matched, matched_derived = derive_matched_text(indicator, klass)
    if matched and not indicator.get('matched_text'):
        indicator['matched_text'] = matched

    present, missing = [], []
    for field in required:
        if indicator.get(field):
            present.append(field)
        else:
            missing.append(field)

    components = []

    def add(name, earned, maximum, note):
        components.append({'name': name, 'earned': round(earned, 1),
                           'max': maximum, 'note': note})

    add('evidence_fields',
        MAX_EVIDENCE * len(present) / float(len(required)), MAX_EVIDENCE,
        '%d/%d trường của lớp %s%s' % (len(present), len(required), klass,
                                       ('; thiếu %s' % ', '.join(missing))
                                       if missing else ''))

    violations = detection_quality.verify_indicator(indicator)
    add('evidence_integrity', 0 if violations else MAX_INTEGRITY, MAX_INTEGRITY,
        'evidence chứa đủ mọi thứ chỉ báo viện dẫn' if not violations
        else '%d vi phạm: %s' % (len(violations), violations[0][:80]))

    systems = enrich_systems(
        (indicator.get('attribution') or {}).get('systems') or [], inventory)
    quality, why = attribution_quality(systems)
    attribution_points = {ATTR_FULL: MAX_ATTRIBUTION,
                          ATTR_PARTIAL: MAX_ATTRIBUTION * 0.6,
                          ATTR_NONE: 0.0}[quality]
    add('attribution', attribution_points, MAX_ATTRIBUTION, '%s — %s' % (quality, why))

    source = indicator.get('data_source') or 'UNKNOWN'
    add('source_trust', SOURCE_POINTS.get(source, 0), MAX_SOURCE,
        'data_source = %s' % source)

    earned = sum(c['earned'] for c in components)
    raw = int(round(earned))
    score = raw

    noise, noise_reason = noise_class(indicator, hunt)
    if noise:
        # Tiếng ồn không được mang điểm cao. Nhưng điểm THÔ vẫn giữ lại: nếu sau
        # này một mục bị lọc nhầm, phải thấy được nó vốn đáng bao nhiêu.
        score = min(score, BAND_MEDIUM - 1)

    if indicator.get('attribution') is not None:
        indicator['attribution']['systems'] = systems
    indicator['evidence_class'] = klass
    indicator['evidence_quality'] = ('COMPLETE' if not missing and not violations
                                     else ('PARTIAL' if present else 'MISSING'))
    indicator['attribution_quality'] = quality
    indicator['confidence_score'] = score
    indicator['confidence'] = band(score)
    indicator['confidence_basis'] = {
        'components': components,
        'raw_score': raw,
        'evidence_class': klass,
        'required_fields': list(required),
        'missing_fields': missing,
        'source_log_derived': source_derived,
        'matched_text_derived': matched_derived,
    }
    if noise:
        indicator['suppressed'] = True
        indicator['noise_class'] = noise
        indicator['suppression_reason'] = noise_reason
        indicator['confidence_basis']['capped_for_noise'] = True
    else:
        indicator['suppressed'] = False
    return indicator


def _mean(indicators):
    if not indicators:
        return None
    return round(sum(i.get('confidence_score') or 0 for i in indicators)
                 / float(len(indicators)), 1)


def _variance(indicators):
    """Phương sai điểm. 0 nghĩa là thang điểm chưa phân biệt được gì ở đây.

    AQ-008 / AQ-012. Một chỉ số mà 96/96 bản ghi đạt đúng 100 không phải một
    chỉ số tốt — nó là một hằng số đội lốt phép đo. Ghi phương sai ra cạnh
    trung bình để không ai đọc `average_score: 100.0` như một thành tích.
    """
    if len(indicators) < 2:
        return None
    scores = [i.get('confidence_score') or 0 for i in indicators]
    mean = sum(scores) / float(len(scores))
    return round(sum((x - mean) ** 2 for x in scores) / float(len(scores)), 2)


def _class_variance(indicators):
    """Phương sai theo từng lớp bằng chứng, kèm cờ "chưa phân biệt được"."""
    groups = {}
    for indicator in indicators:
        groups.setdefault(indicator.get('evidence_class') or 'UNKNOWN',
                          []).append(indicator)
    out = {}
    for klass, rows in sorted(groups.items()):
        variance = _variance(rows)
        out[klass] = {
            'count': len(rows),
            'mean': _mean(rows),
            'variance': variance,
            # Mot lop chi co mot ban ghi thi chua noi duoc gi; mot lop nhieu ban
            # ghi ma phuong sai 0 thi da noi ro: thang diem khong tach duoc
            # chung. Hai truong hop do khac nhau va khong duoc gop.
            'discriminating': None if variance is None else variance > 0.0,
        }
    return out


def _count(indicators, field):
    out = {}
    for indicator in indicators:
        key = indicator.get(field) or 'UNKNOWN'
        out[key] = out.get(key, 0) + 1
    return out


def _count_systems(indicators, field):
    """Đếm theo HỆ THỐNG được quy kết, không theo chỉ báo (AQ-002).

    Một chỉ báo có thể quy kết về nhiều máy, và nhãn `attribution_quality` là
    của cả chỉ báo. Muốn giải thích nhãn đó thì phải xuống một cấp — nguồn tên
    của từng máy — nên phép đếm này có mẫu số riêng, và mẫu số ấy khác mẫu số
    của `by_attribution`.
    """
    out = {}
    for indicator in indicators:
        for system in (indicator.get('attribution') or {}).get('systems') or []:
            key = system.get('hostname_source') or 'không khai'
            out[key] = out.get(key, 0) + 1
    return out


def score_file(path, hunt, inventory):
    with io.open(path, encoding='utf-8') as handle:
        data = json.load(handle)

    indicators = data.get('indicators') or []
    for indicator in indicators:
        score_indicator(indicator, hunt, inventory)

    kept = [i for i in indicators if not i.get('suppressed')]
    data['ioc_quality'] = {
        'version': VERSION,
        'scored_at': datetime.now().isoformat(),
        'total': len(indicators),
        'suppressed': len(indicators) - len(kept),
        'by_noise_class': _count([i for i in indicators if i.get('suppressed')],
                                 'noise_class'),
        # AQ-001. Moi khoi thong ke phai TU KHAI mau so cua no. Ban dau khoi nay
        # de `total: 455` canh cac phan phoi cong lai bang 228 va mot
        # `average_score` tinh tren 228 — hai mau so, mot object, khong nhan.
        # Con so 96.3 dung tren tap cua no; doc canh `total: 455` no thanh 96.3
        # cua 455, lech 23.6 diem. Khong ai lam gi sai; cai ten da noi doi.
        'scored_population': len(kept),
        'population_note': ('Mọi phân phối và `average_score` tính trên %d chỉ '
                            'báo còn lại sau lọc tiếng ồn, KHÔNG trên %d tổng. '
                            'Số trên toàn bộ nằm ở `*_all`.'
                            % (len(kept), len(indicators))),
        'by_confidence': _count(kept, 'confidence'),
        'by_attribution': _count(kept, 'attribution_quality'),
        # AQ-002, vong thu muoi mot. Hang doi doc `FULL: 424 / 426` canh
        # `assets.json` voi `hostname_source: {unresolved: 11}` va ket luan nhan
        # `FULL` la bia. Do lai thi khong phai: gan nhu moi `FULL` la CHINH MAY
        # DANG CHAY, va ten cua no den tu `local_host_identity()`, khong tu kho
        # quet mang. Moi peer o xa khong phan giai duoc deu dang la `PARTIAL`.
        #
        # Nhung hang doi dung o mot diem: ngoai le do NGAM. No chi doc duoc bang
        # cach di vao `enrich_systems()`, con mot nguoi doc state thi khong thay
        # gi ngoai hai con so khong giai thich duoc cho nhau. Muoi mot vong lap
        # lai cung mot ket luan sai la cai gia cua viec bat nguoi doc phai suy.
        #
        # Nen khai ra: nguon cua tung hostname, dem ngay canh nhan chat luong.
        'by_hostname_source': _count_systems(kept, 'hostname_source'),
        'attribution_note': (
            'Hau het `FULL` den tu `hostname_source: local host` — may dang chay '
            'tu biet ten no, va mot lan quet mang khong bao gio biet ten do ro '
            'hon. Day la ngoai le HOP LE va co y, khong phai nhan suy tu '
            '`assets.json`: moi he thong o xa khong phan giai duoc ten deu la '
            '`PARTIAL`. Doi chieu bang nay voi `by_attribution` — `FULL` ma nguon '
            'la `unresolved` moi la nhan bia.'),
        'by_evidence': _count(kept, 'evidence_quality'),
        'by_confidence_all': _count(indicators, 'confidence'),
        'average_score': _mean(kept),
        'average_score_all': _mean(indicators),
        'score_variance': _variance(kept),
        'by_class_variance': _class_variance(kept),
    }

    # AQ-045. `by_severity` ở CẤP TỆP được đếm trong chính cuộc săn
    # (`hunt_lateral_movement.py:221-227`), trên toàn bộ chỉ báo. Cuộc săn chạy ở
    # stage sớm; cờ `suppressed` được gắn ở đây, stage sau. Nên cuộc săn không
    # THỂ biết chỉ báo nào sẽ bị hạ xuống tiếng ồn — và trước đây không ai tính
    # lại con số đó.
    #
    # Hậu quả đo được: 6 chỉ báo `ROUTINE_OS_ACTIVITY` (tài khoản máy đăng nhập
    # vào chính nó — hoạt động nền của Windows) vẫn đứng trong `by_severity` là
    # `HIGH: 6`. `calculate_risk_score` đọc bảng tổng kết trước lọc đó và cho
    # `threat_hunting` health 28, contribution 18.0 trên tổng 23 — **78% điểm rủi
    # ro của cả hệ thống đến từ tiếng ồn đã được nhận diện là tiếng ồn.**
    #
    # Chỗ sửa không phải `analyze_threat_hunting`. Chỗ sửa là đây: nơi duy nhất
    # biết chỉ báo nào bị lọc. Khuôn `average_score` / `average_score_all` mà
    # chính tệp này đã dùng ở AQ-001 áp thẳng sang: tên trần mang số SAU lọc,
    # hậu tố `_including_noise` giữ số trước lọc để còn rà lại được.
    published = data.get('by_severity')
    if published is not None:
        data['by_severity_including_noise'] = published
    data['by_severity'] = _count(kept, 'severity')
    data['by_severity_note'] = (
        '`by_severity` đếm %d chỉ báo còn lại sau lọc tiếng ồn. Số trên toàn bộ '
        '%d chỉ báo nằm ở `by_severity_including_noise`. Mọi consumer chấm điểm '
        'phải dùng số đã lọc: một chỉ báo mang `suppressed: true` đã được kết '
        'luận là không phải phát hiện.' % (len(kept), len(indicators)))

    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def score_all():
    inventory, inventory_error = load_inventory()
    result = {'version': VERSION, 'generated_at': datetime.now().isoformat(),
              'inventory_size': len(inventory),
              'inventory_error': inventory_error,
              'hunts': {}, 'indicators': []}
    for hunt, filename in HUNT_FILES:
        path = os.path.join(STATE_DIR, filename)
        if not os.path.exists(path):
            result['hunts'][hunt] = {'error': 'không có tệp %s' % filename}
            continue
        data = score_file(path, hunt, inventory)
        result['hunts'][hunt] = data['ioc_quality']
        for indicator in data.get('indicators') or []:
            row = dict(indicator)
            row['hunt'] = hunt
            result['indicators'].append(row)
    return result


# --------------------------------------------------------------------------
# Tổng hợp chất lượng cho một phát hiện cấp điều hành
# --------------------------------------------------------------------------
EVIDENCE_ORDER = ['MISSING', 'PARTIAL', 'COMPLETE']
ATTR_ORDER = [ATTR_NONE, ATTR_PARTIAL, ATTR_FULL]


def summarize(indicators):
    """Chất lượng của một phát hiện, suy từ những chỉ báo dựng nên nó.

    Lấy MẮT XÍCH YẾU NHẤT, không lấy trung bình. Một phát hiện được dựng từ mười
    chỉ báo tốt và một chỉ báo không quy kết được thì không đáng tin bằng chín
    phần mười — nó đáng tin đúng bằng chỗ nó sẽ gãy. Trung bình cộng ở đây là
    cách một mắt xích yếu biến mất sau chín mắt xích khoẻ.
    """
    if not indicators:
        return {
            'confidence_score': None,
            'evidence_quality': 'UNKNOWN',
            'attribution_quality': ATTR_NONE,
            'basis': 'Không khớp được chỉ báo nào đã chấm điểm cho phát hiện này',
            'indicator_count': 0,
        }

    scored = [i for i in indicators if i.get('confidence_score') is not None]
    if not scored:
        return {
            'confidence_score': None,
            'evidence_quality': 'UNKNOWN',
            'attribution_quality': ATTR_NONE,
            'basis': '%d chỉ báo khớp nhưng chưa chỉ báo nào được chấm điểm'
                     % len(indicators),
            'indicator_count': len(indicators),
        }

    worst_evidence = min((i.get('evidence_quality') or 'MISSING' for i in scored),
                         key=lambda v: EVIDENCE_ORDER.index(v)
                         if v in EVIDENCE_ORDER else 0)
    worst_attr = min((i.get('attribution_quality') or ATTR_NONE for i in scored),
                     key=lambda v: ATTR_ORDER.index(v) if v in ATTR_ORDER else 0)
    lowest = min(i['confidence_score'] for i in scored)
    suppressed = len([i for i in scored if i.get('suppressed')])

    return {
        'confidence_score': lowest,
        'confidence': band(lowest),
        'evidence_quality': worst_evidence,
        'attribution_quality': worst_attr,
        'indicator_count': len(scored),
        'suppressed_inputs': suppressed,
        'basis': ('Mắt xích yếu nhất trong %d chỉ báo: điểm thấp nhất %d, '
                  'bằng chứng kém nhất %s, quy kết kém nhất %s%s'
                  % (len(scored), lowest, worst_evidence, worst_attr,
                     ('; %d đầu vào đã bị hạ xuống tiếng ồn' % suppressed)
                     if suppressed else '')),
    }


def systems_of(indicator):
    """Mọi IP mà một chỉ báo nói tới."""
    ips = set()
    for system in (indicator.get('attribution') or {}).get('systems') or []:
        if system.get('ip'):
            ips.add(system['ip'])
    for ip in indicator.get('affected_systems') or []:
        if isinstance(ip, str):
            ips.add(ip)
    return ips


# --------------------------------------------------------------------------
# Báo cáo
# --------------------------------------------------------------------------
def _table(rows, headers):
    out = ['| %s |' % ' | '.join(headers),
           '|%s|' % '|'.join(['---'] * len(headers))]
    for row in rows:
        out.append('| %s |' % ' | '.join(str(cell) for cell in row))
    return out


def render_report(result):
    out = []
    add = out.append

    add('# IOC Quality Report')
    add('')
    add('Sinh tự động bởi `scripts/ioc_quality.py`. Đừng sửa tay — sửa nguồn.')
    add('')
    add('Cập nhật: %s' % result['generated_at'])
    add('')
    add('> **`confidence_score` KHÔNG phải mức độ nguy hiểm.** Nó trả lời một câu '
        'hẹp hơn nhiều: *quan sát này có đúng như nó tự nói không*. Một lần đăng '
        'nhập nền của Windows hoàn toàn có thể đạt 100 điểm tin cậy — đó là một '
        'quan sát chắc chắn về một việc hoàn toàn bình thường. Đọc một con số '
        'cao ở đây thành "nguy hiểm" là cách nhanh nhất để biến bảng này thành '
        'thứ ngược lại với mục đích của nó.')
    add('')

    indicators = result['indicators']
    kept = [i for i in indicators if not i.get('suppressed')]
    suppressed = [i for i in indicators if i.get('suppressed')]

    add('## Tóm tắt')
    add('')
    add('| | |')
    add('|---|---|')
    add('| Tổng chỉ báo | **%d** |' % len(indicators))
    add('| Còn lại sau lọc tiếng ồn | **%d** |' % len(kept))
    add('| Bị hạ xuống tiếng ồn | %d |' % len(suppressed))
    for level in ('HIGH', 'MEDIUM', 'LOW'):
        add('| %s confidence | %d |'
            % (level, len([i for i in kept if i.get('confidence') == level])))
    for level in (ATTR_FULL, ATTR_PARTIAL, ATTR_NONE):
        add('| Quy kết %s | %d |'
            % (level, len([i for i in kept if i.get('attribution_quality') == level])))
    add('| Kho tài sản đọc được | %d máy |' % result['inventory_size'])
    add('')
    if result.get('inventory_error'):
        add('> ⚠ **Kho tài sản KHÔNG đọc được:** %s' % result['inventory_error'])
        add('>')
        add('> Mọi con số quy kết dưới đây vì thế nói về việc *không mở được kho*, '
            'không phải về việc *không tìm được máy*. Hai câu đó cần hai hành '
            'động khác nhau.')
        add('')

    add('## Theo cuộc săn')
    add('')
    rows = []
    for hunt, _ in HUNT_FILES:
        summary = result['hunts'].get(hunt) or {}
        if 'error' in summary:
            rows.append([hunt, '—', '—', '—', summary['error']])
            continue
        confidence = summary.get('by_confidence') or {}
        rows.append([
            '`%s`' % hunt, summary.get('total', 0), summary.get('suppressed', 0),
            summary.get('average_score', 0),
            'H %d / M %d / L %d' % (confidence.get('HIGH', 0),
                                    confidence.get('MEDIUM', 0),
                                    confidence.get('LOW', 0)),
        ])
    out.extend(_table(rows, ['Cuộc săn', 'Tổng', 'Tiếng ồn', 'Điểm TB',
                             'Phân bố tin cậy']))
    add('')

    for level, title in (('HIGH', 'High Confidence (≥ %d)' % BAND_HIGH),
                         ('MEDIUM', 'Medium Confidence (%d–%d)'
                          % (BAND_MEDIUM, BAND_HIGH - 1)),
                         ('LOW', 'Low Confidence (< %d)' % BAND_MEDIUM)):
        group = [i for i in kept if i.get('confidence') == level]
        add('## %s — %d chỉ báo' % (title, len(group)))
        add('')
        if not group:
            add('_Không có._')
            add('')
            continue
        # Gop cac dong giong het nhau. Liet ke 25 lan cung mot dong
        # "Persistence: ScheduledTask | INFO | 100" khong noi them dieu gi sau
        # dong thu nhat, va no day het cho cua nhung dong thuc su khac.
        buckets = {}
        for indicator in group:
            key = (indicator.get('confidence_score'), indicator.get('hunt'),
                   str(indicator.get('type'))[:42], indicator.get('severity'),
                   indicator.get('evidence_class'),
                   indicator.get('evidence_quality'),
                   indicator.get('attribution_quality'))
            buckets[key] = buckets.get(key, 0) + 1
        rows = [[key[0], count, '`%s`' % key[1]] + list(key[2:])
                for key, count in sorted(buckets.items(),
                                         key=lambda kv: (-kv[0][0], -kv[1]))]
        out.extend(_table(rows[:25],
                          ['Điểm', 'Số', 'Cuộc săn', 'Loại', 'Mức',
                           'Lớp bằng chứng', 'Bằng chứng', 'Quy kết']))
        if len(rows) > 25:
            add('')
            add('_... và %d dạng chỉ báo nữa cùng nhóm._' % (len(rows) - 25))
        add('')

    unattributed = [i for i in kept
                    if i.get('attribution_quality') == ATTR_NONE]
    add('## Unattributed IOC — %d' % len(unattributed))
    add('')
    add('Một chỉ báo không quy kết được về máy nào thì không hành động được: '
        'không biết cách ly cái gì, không biết hỏi ai.')
    add('')
    if not unattributed:
        add('_Không có chỉ báo nào bị bỏ lại không quy kết._')
    else:
        rows = [[ '`%s`' % i.get('hunt'), str(i.get('type'))[:44],
                  i.get('confidence_score'),
                  (i.get('confidence_basis') or {}).get('components', [{}])[2]
                  .get('note', '')[:60]]
                for i in unattributed[:25]]
        out.extend(_table(rows, ['Cuộc săn', 'Loại', 'Điểm', 'Vì sao']))
    add('')

    add('## Tiếng ồn bị hạ cấp — %d' % len(suppressed))
    add('')
    add('Những mục này **vẫn nằm trong tệp state**, mang cờ `suppressed: true` '
        'kèm lý do. Xoá hẳn sẽ khiến không ai kiểm lại được quyết định lọc — và '
        'bộ lọc tiếng ồn chính là chỗ dễ giấu một phát hiện thật nhất.')
    add('')
    counts = {}
    for indicator in suppressed:
        key = indicator.get('noise_class') or 'UNKNOWN'
        counts[key] = counts.get(key, 0) + 1
    if counts:
        out.extend(_table(sorted(counts.items()), ['Loại tiếng ồn', 'Số lượng']))
    else:
        add('_Không có._')
    add('')

    add('## Phân bố điểm')
    add('')
    add('Một thang 0–100 mà mọi bản ghi đều rơi vào một ô thì không đo được gì. '
        'Bảng dưới đây để đọc chính điều đó — nếu chỉ có một hàng, thang điểm '
        'đang không phân biệt gì trên tập dữ liệu này, và đó là thông tin về '
        '*tập dữ liệu*, không phải về thang điểm.')
    add('')
    histogram = {}
    for indicator in kept:
        bucket = (indicator.get('confidence_score') or 0) // 10 * 10
        histogram[bucket] = histogram.get(bucket, 0) + 1
    out.extend(_table(
        [['%d–%d' % (b, b + 9), n, '█' * min(40, max(1, n * 40 // max(1, len(kept))))]
         for b, n in sorted(histogram.items(), reverse=True)],
        ['Khoảng điểm', 'Số chỉ báo', '']))
    add('')

    add('## Cách tính điểm')
    add('')
    out.extend(_table(
        [['`evidence_fields`', MAX_EVIDENCE,
          'Tỉ lệ trường có mặt **trên những trường lớp đó CÓ THỂ có**'],
         ['`evidence_integrity`', MAX_INTEGRITY,
          'Evidence có chứa mọi thứ chỉ báo viện dẫn không (bất biến Sprint 12)'],
         ['`attribution`', MAX_ATTRIBUTION,
          'FULL = IP + hostname + asset_id; PARTIAL = 60%; UNATTRIBUTED = 0'],
         ['`source_trust`', MAX_SOURCE,
          'LIVE_OBSERVED %d · OBSERVED 12 · DERIVED 6 · SIMULATED 0' % MAX_SOURCE]],
        ['Thành phần', 'Tối đa', 'Đo cái gì']))
    add('')
    add('Một chỉ báo bị đánh dấu tiếng ồn bị chặn trần dưới %d điểm, nhưng '
        '`confidence_basis.raw_score` giữ nguyên điểm thô — nếu có mục bị lọc '
        'nhầm, phải thấy được nó vốn đáng bao nhiêu.' % BAND_MEDIUM)
    add('')
    return '\n'.join(out) + '\n'


def main():
    result = score_all()

    docs_dir = os.path.dirname(REPORT_FILE)
    if not os.path.isdir(docs_dir):
        os.makedirs(docs_dir)
    with io.open(REPORT_FILE, 'w', encoding='utf-8') as handle:
        handle.write(render_report(result))

    indicators = result['indicators']
    kept = [i for i in indicators if not i.get('suppressed')]
    summary = {
        'status': 'success',
        'total': len(indicators),
        'kept': len(kept),
        'suppressed': len(indicators) - len(kept),
        'by_confidence': _count(kept, 'confidence'),
        'by_attribution': _count(kept, 'attribution_quality'),
        # AQ-002, vong thu muoi mot. Hang doi doc `FULL: 424 / 426` canh
        # `assets.json` voi `hostname_source: {unresolved: 11}` va ket luan nhan
        # `FULL` la bia. Do lai thi khong phai: gan nhu moi `FULL` la CHINH MAY
        # DANG CHAY, va ten cua no den tu `local_host_identity()`, khong tu kho
        # quet mang. Moi peer o xa khong phan giai duoc deu dang la `PARTIAL`.
        #
        # Nhung hang doi dung o mot diem: ngoai le do NGAM. No chi doc duoc bang
        # cach di vao `enrich_systems()`, con mot nguoi doc state thi khong thay
        # gi ngoai hai con so khong giai thich duoc cho nhau. Muoi mot vong lap
        # lai cung mot ket luan sai la cai gia cua viec bat nguoi doc phai suy.
        #
        # Nen khai ra: nguon cua tung hostname, dem ngay canh nhan chat luong.
        'by_hostname_source': _count_systems(kept, 'hostname_source'),
        'attribution_note': (
            'Hau het `FULL` den tu `hostname_source: local host` — may dang chay '
            'tu biet ten no, va mot lan quet mang khong bao gio biet ten do ro '
            'hon. Day la ngoai le HOP LE va co y, khong phai nhan suy tu '
            '`assets.json`: moi he thong o xa khong phan giai duoc ten deu la '
            '`PARTIAL`. Doi chieu bang nay voi `by_attribution` — `FULL` ma nguon '
            'la `unresolved` moi la nhan bia.'),
        'by_evidence': _count(kept, 'evidence_quality'),
        'average_score': (round(sum(i['confidence_score'] for i in kept)
                                / float(len(kept)), 1) if kept else 0.0),
        'report': os.path.relpath(REPORT_FILE, PROJECT_ROOT),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # Chất lượng thấp KHÔNG phải lỗi của stage. Chỗ báo động đúng là bảng chất
    # lượng, không phải mã thoát — một pipeline đỏ vì dữ liệu thật đang kém sẽ
    # bị người ta tắt đi trước khi dữ liệu kịp tốt lên.
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())

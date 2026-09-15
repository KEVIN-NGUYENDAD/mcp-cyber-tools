# -*- coding: utf-8 -*-
"""
IOC Quality — điểm tin cậy, chất lượng bằng chứng, chất lượng quy kết.

Ba điều bộ kiểm này canh, và cả ba đều là những cách một thang điểm chất lượng
lặng lẽ ngừng đo cái nó nói là đang đo:

  1. Thang điểm phải PHÂN BIỆT ĐƯỢC. Một thang 0–100 mà mọi bản ghi đều cho ra
     một giá trị là một hằng số đội lốt phép đo. Trên máy này dữ liệu thật đang
     rất đồng đều, nên nếu chỉ kiểm dữ liệu thật thì một hàm `return 100` cũng
     xanh hết. Vì vậy phải có đầu vào tổng hợp đã cố tình làm hỏng.

  2. Không được trừ điểm vì thiếu một trường KHÔNG THỂ tồn tại. Một tác vụ theo
     lịch không có Event ID. Bắt nó phải có sẽ dẫn tới một trong hai kết cục,
     và cả hai đều tệ: điền giá trị giả, hoặc dìm cả một lớp chỉ báo đúng đắn.

  3. Bộ lọc tiếng ồn không được nuốt mức cao. Kẻ tấn công dùng đúng những nhị
     phân mà lập trình viên dùng; lọc theo tên tiến trình ở mức CRITICAL là tự
     bịt mắt đúng chỗ đáng nhìn nhất.
"""

import io
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import ioc_quality as iq  # noqa: E402

HUNT_FILES = [name for _, name in iq.HUNT_FILES]


def complete_event_indicator():
    """Một chỉ báo event log đầy đủ mọi thứ nó có thể có."""
    return {
        'type': 'Remote Logon',
        'severity': 'INFO',
        'timestamp': '2026-09-14T07:00:00',
        'event_id': 4624,
        'source_log': 'Security',
        'matched_text': '10.0.0.9',
        'evidence': ['An account was successfully logged on from 10.0.0.9'],
        'data_source': 'LIVE_OBSERVED',
        'attribution': {'systems': [{'ip': '10.0.0.9', 'scope': 'REMOTE_PEER'}]},
    }


def run():
    suite = Suite('ioc quality (Sprint 17)')

    inventory = {'10.0.0.9': {'ip': '10.0.0.9', 'hostname': 'FILESERVER'}}

    # -- 1. thang diem phai phan biet duoc ----------------------------------
    good = iq.score_indicator(complete_event_indicator(), 'lateral_movement',
                              inventory)
    bare = iq.score_indicator({'type': 'Unknown thing', 'evidence': [],
                               'data_source': 'SIMULATED'},
                              'lateral_movement', {})
    suite.check('Chi bao day du -> HIGH',
                good['confidence'] == 'HIGH', '%d' % good['confidence_score'])
    suite.check('Chi bao rong, nguon mo phong -> LOW',
                bare['confidence'] == 'LOW', '%d' % bare['confidence_score'])
    suite.check('Hai dau vao khac han -> hai diem khac han',
                good['confidence_score'] - bare['confidence_score'] >= 40,
                '%d vs %d' % (good['confidence_score'], bare['confidence_score']))

    # Từng thành phần phải thực sự tham gia. Bỏ đi một thứ thì điểm phải tụt —
    # nếu không, thành phần đó chỉ là đồ trang trí trong `confidence_basis`.
    base = good['confidence_score']
    for field, label in (('data_source', 'nguon'),
                         ('attribution', 'quy ket'),
                         ('event_id', 'event_id')):
        broken = complete_event_indicator()
        broken.pop(field, None)
        scored = iq.score_indicator(broken, 'lateral_movement', inventory)
        suite.check('Bo "%s" -> diem tut xuong' % label,
                    scored['confidence_score'] < base,
                    '%d (goc %d)' % (scored['confidence_score'], base))

    # -- 2. khong tru diem vi mot truong khong the ton tai ------------------
    task = {
        'type': 'Persistence: ScheduledTask',
        'severity': 'INFO',
        'timestamp': '2026-09-14T07:00:00',
        'name': 'Adobe Update',
        # IP cua REMOTE_PEER phai co mat trong evidence, neu khong bat bien
        # cua Sprint 12 se (dung dan) tru diem toan ven.
        'evidence': ['Kind=ScheduledTask', 'Name=Adobe Update', 'Host=10.0.0.9'],
        'data_source': 'LIVE_OBSERVED',
        'attribution': {'systems': [{'ip': '10.0.0.9', 'scope': 'REMOTE_PEER'}]},
    }
    scored_task = iq.score_indicator(dict(task), 'persistence', inventory)
    suite.check('Tac vu theo lich -> lop SCHEDULED_TASK',
                scored_task['evidence_class'] == iq.CLASS_TASK,
                scored_task['evidence_class'])
    suite.check('Lop do KHONG doi event_id',
                'event_id' not in scored_task['confidence_basis']['required_fields'],
                str(scored_task['confidence_basis']['required_fields']))
    suite.check('Nen no van dat diem day du du khong co event_id',
                scored_task['confidence_score'] == 100,
                '%d' % scored_task['confidence_score'])

    # Nguoc lai: mot chi bao EVENT_LOG thieu event_id THI PHAI bi tru.
    no_id = complete_event_indicator()
    no_id.pop('event_id')
    no_id['type'] = 'Logon Activity'
    scored_no_id = iq.score_indicator(no_id, 'lateral_movement', inventory)
    suite.check('Chi bao tu event log ma thieu event_id -> bi tru',
                scored_no_id['confidence_score'] < 100
                and 'event_id' in scored_no_id['confidence_basis']['missing_fields'],
                '%d, thieu %s' % (scored_no_id['confidence_score'],
                                  scored_no_id['confidence_basis']['missing_fields']))

    # -- 3. hostname: IP chep sang mot cot khac KHONG phai ten may ----------
    suite.check('hostname == ip -> coi la chua phan giai',
                iq.real_hostname({'ip': '192.168.0.10',
                                  'hostname': '192.168.0.10'}) is None)
    suite.check('hostname that -> giu nguyen',
                iq.real_hostname({'ip': '10.0.0.9',
                                  'hostname': 'FILESERVER'}) == 'FILESERVER')

    # -- 4. asset_id: mot cong thuc, moi noi giong nhau ---------------------
    first = iq.asset_id_for('192.168.0.51')
    suite.check('asset_id on dinh giua hai lan goi',
                first == iq.asset_id_for('192.168.0.51'), first)
    suite.check('asset_id khac nhau cho hai IP khac nhau',
                first != iq.asset_id_for('192.168.0.52'))
    suite.check('Khong co IP thi khong bia ra asset_id',
                iq.asset_id_for(None) is None)

    # Bo sinh ma trong extract_asset_intelligence phai cho CUNG ket qua, neu
    # khong thi kho tai san va lop IOC se goi cung mot may bang hai cai ten.
    try:
        import extract_asset_intelligence as eai
        suite.check('extract_asset_intelligence dung cung cong thuc asset_id',
                    eai.asset_identifier('192.168.0.51') == first,
                    '%s vs %s' % (eai.asset_identifier('192.168.0.51'), first))
    except ImportError as error:
        suite.check('extract_asset_intelligence nap duoc', False, str(error)[:80])

    # -- 5. quy ket: ba manh, thieu manh nao noi manh do --------------------
    full = iq.enrich_systems([{'ip': '10.0.0.9', 'scope': 'REMOTE_PEER'}], inventory)
    suite.check('Du IP + hostname + asset_id -> FULL',
                iq.attribution_quality(full)[0] == iq.ATTR_FULL,
                iq.attribution_quality(full)[1])

    partial = iq.enrich_systems([{'ip': '10.0.0.77', 'scope': 'REMOTE_PEER'}], {})
    quality, why = iq.attribution_quality(partial)
    suite.check('Thieu hostname -> PARTIAL, khong phai FULL',
                quality == iq.ATTR_PARTIAL, why)
    suite.check('  -> va noi ro thieu cai gi',
                'hostname' in why, why)

    suite.check('Khong he thong nao -> UNATTRIBUTED',
                iq.attribution_quality([])[0] == iq.ATTR_NONE)

    # -- 6. tong hop cho phat hien: MAT XICH YEU NHAT, khong phai trung binh --
    strong = [dict(complete_event_indicator(), confidence_score=100,
                   evidence_quality='COMPLETE', attribution_quality=iq.ATTR_FULL)
              for _ in range(9)]
    weak = dict(complete_event_indicator(), confidence_score=20,
                evidence_quality='PARTIAL', attribution_quality=iq.ATTR_NONE)
    summary = iq.summarize(strong + [weak])
    suite.check('Chin manh mot yeu -> lay diem cua cai YEU',
                summary['confidence_score'] == 20,
                str(summary['confidence_score']))
    suite.check('  -> va lay quy ket kem nhat',
                summary['attribution_quality'] == iq.ATTR_NONE,
                summary['attribution_quality'])
    # Trung binh cong se ra 92 — day dung la cach mot mat xich yeu bien mat sau
    # chin mat xich khoe.
    suite.check('  -> KHONG phai trung binh cong',
                summary['confidence_score'] != 92)

    empty = iq.summarize([])
    suite.check('Khong khop duoc chi bao nao -> noi thang, khong bia diem',
                empty['confidence_score'] is None and bool(empty['basis']),
                str(empty)[:80])

    # -- 7. loc tieng on: KHONG duoc nuot muc cao --------------------------
    dev_low = {'severity': 'INFO', 'evidence': ['Path=C:\\tools\\node.exe'],
               'process': 'node'}
    klass, reason = iq.noise_class(dev_low, 'suspicious_processes')
    suite.check('Cong cu phat trien o muc INFO -> bi ha xuong tieng on',
                klass == iq.NOISE_DEV, str(klass))

    dev_high = dict(dev_low, severity='CRITICAL')
    klass_high, _ = iq.noise_class(dev_high, 'suspicious_processes')
    suite.check('CUNG binh phan do o muc CRITICAL -> KHONG bi loc',
                klass_high is None, str(klass_high))

    suite.check('Tu quan sat van bi bat o moi muc',
                iq.noise_class({'severity': 'CRITICAL',
                                'evidence': ['scripts/hunt_credential_dumping.py '
                                             '-> mimikatz']},
                               'credential_dumping')[0] == iq.NOISE_SELF)

    # AQ-019/AQ-031 fixture. Su co goc: 4648 logon vao chinh SYSTEM account
    # (SID s-1-5-18) mang nhan HIGH vi Event ID, duoc MIEN TRU khoi loc, chiem
    # 58% risk score toan he thong. ROUTINE_HINTS la su that ve CHU THE (SID),
    # khong phai phong doan theo ten tien trinh nhu DEV_HINTS -- nen no phai
    # loc o MOI muc, ke ca HIGH/CRITICAL. Day la fixture khoa lai hanh vi do,
    # de mot lan sua sau nay khong lam risk score dao dong lai (10->3, 436->
    # 356->266 chi bao giua cac lan chay) ma khong ai phat hien qua code review.
    routine_high = {'severity': 'HIGH',
                     'evidence': ['Logon Type:\t\t5', 'Security ID:\t\ts-1-5-18']}
    klass_routine_high, reason_routine_high = iq.noise_class(routine_high,
                                                              'lateral_movement')
    suite.check('SYSTEM SID (s-1-5-18) o muc HIGH -> VAN bi loc la ROUTINE',
                klass_routine_high == iq.NOISE_ROUTINE, str(klass_routine_high))
    suite.check('  -> ly do noi ro la hoat dong nen, khong phai bia',
                bool(reason_routine_high) and 'hệ thống' in reason_routine_high,
                reason_routine_high)

    routine_critical = dict(routine_high, severity='CRITICAL')
    klass_routine_crit, _ = iq.noise_class(routine_critical, 'lateral_movement')
    suite.check('Cung SID o muc CRITICAL -> VAN bi loc (khac DEV_HINTS)',
                klass_routine_crit == iq.NOISE_ROUTINE, str(klass_routine_crit))

    # Doi chieu: DEV_HINTS van duoc mien tru o HIGH/CRITICAL (hanh vi co y,
    # khong phai loi) -- hai bang gop khong con gop nua.
    dev_critical = {'severity': 'CRITICAL', 'evidence': ['Path=C:\\tools\\git.exe']}
    klass_dev_crit, _ = iq.noise_class(dev_critical, 'suspicious_processes')
    suite.check('DEV_HINTS o CRITICAL van duoc mien tru (khong giong ROUTINE_HINTS)',
                klass_dev_crit is None, str(klass_dev_crit))

    # Tieng on bi chan tran, nhung diem tho phai con de kiem lai duoc.
    noisy = iq.score_indicator(
        dict(complete_event_indicator(), process='node',
             evidence=['Path=C:\\tools\\node.exe 10.0.0.9']),
        'suspicious_processes', inventory)
    suite.check('Tieng on bi chan duoi nguong MEDIUM',
                noisy['confidence_score'] < iq.BAND_MEDIUM,
                '%d' % noisy['confidence_score'])
    suite.check('  -> nhung raw_score giu nguyen de kiem lai',
                noisy['confidence_basis']['raw_score'] > noisy['confidence_score'],
                '%d vs %d' % (noisy['confidence_basis']['raw_score'],
                              noisy['confidence_score']))
    suite.check('  -> va co ly do doc duoc', bool(noisy.get('suppression_reason')))

    # -- 8. state that ------------------------------------------------------
    total = 0
    for filename in HUNT_FILES:
        path = os.path.join(PROJECT_ROOT, 'state', filename)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        indicators = data.get('indicators') or []
        total += len(indicators)

        missing = [i for i in indicators if i.get('confidence_score') is None]
        suite.check('%s: moi chi bao co confidence_score' % filename,
                    not missing, '%d thieu' % len(missing))

        bad_range = [i for i in indicators
                     if not (0 <= (i.get('confidence_score') or -1) <= 100)]
        suite.check('%s: diem nam trong 0-100' % filename,
                    not bad_range, '%d ngoai khoang' % len(bad_range))

        mismatched = [i for i in indicators
                      if i.get('confidence') != iq.band(i.get('confidence_score', 0))]
        suite.check('%s: nhan HIGH/MEDIUM/LOW khop voi diem' % filename,
                    not mismatched, '%d lech' % len(mismatched))

        no_attr = [i for i in indicators if not i.get('attribution_quality')]
        suite.check('%s: moi chi bao co attribution_quality' % filename,
                    not no_attr, '%d thieu' % len(no_attr))

        if data.get('ioc_quality'):
            declared = data['ioc_quality']['total']
            suite.check('%s: so tong khai bao khop so chi bao thuc' % filename,
                        declared == len(indicators),
                        '%d khai vs %d that' % (declared, len(indicators)))

    suite.check('Co chi bao that de kiem (khong phai 0)', total > 0, '%d' % total)

    # Tieng on bi HA CAP chu khong bi XOA. Neu no bi xoa, khong ai kiem lai duoc
    # quyet dinh loc — va bo loc tieng on la cho de giau mot phat hien that nhat.
    suppressed_kept = 0
    for filename in HUNT_FILES:
        path = os.path.join(PROJECT_ROOT, 'state', filename)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        suppressed_kept += len([i for i in (data.get('indicators') or [])
                                if i.get('suppressed')])
        declared = (data.get('ioc_quality') or {}).get('suppressed', 0)
        suite.check('%s: so tieng on khai bao khop so muc con nam trong tep'
                    % filename,
                    declared == len([i for i in (data.get('indicators') or [])
                                     if i.get('suppressed')]),
                    '%d khai' % declared)

    # -- 9. bao cao ---------------------------------------------------------
    if os.path.exists(iq.REPORT_FILE):
        with io.open(iq.REPORT_FILE, encoding='utf-8') as handle:
            report = handle.read()
        suite.check('Bao cao co canh bao confidence KHAC muc nguy hiem',
                    'KHÔNG phải mức độ nguy hiểm' in report)
        for heading in ('High Confidence', 'Medium Confidence',
                        'Low Confidence', 'Unattributed IOC'):
            suite.check('Bao cao co muc "%s"' % heading, heading in report)
    else:
        suite.check('docs/project/IOC_QUALITY_REPORT.md ton tai', False,
                    iq.REPORT_FILE)

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))

# -*- coding: utf-8 -*-
"""
detection_quality — hai bất biến, tách khỏi bất kỳ cuộc săn cụ thể nào.

Nếu những ca ở đây đỏ thì mọi cuộc săn đều đang sai, kể cả khi bộ kiểm riêng của
từng cuộc săn vẫn xanh.
"""

from harness import Suite

import detection_quality as dq


def run():
    suite = Suite('detection_quality (bat bien)')

    # -- evidence_excerpt ---------------------------------------------------
    message = ('A new process has been created.\r\n' + ('x' * 900)
               + '\r\n\tProcess Command Line:\tmimikatz.exe sekurlsa')
    suite.check('Bug cu tai hien duoc: message[:600] khong chua trigger',
                'mimikatz' not in message[:600])
    excerpt = dq.evidence_excerpt(message, 'mimikatz')
    suite.check('evidence_excerpt luon chua trigger', 'mimikatz' in excerpt)
    suite.check('evidence_excerpt khong vuot gioi han',
                len(excerpt) <= dq.EVIDENCE_WIDTH, 'len=%d' % len(excerpt))
    suite.check('Trigger o dau thong diep van hoat dong',
                'A new process' in dq.evidence_excerpt(message, 'A new process'))
    suite.check('Trigger rong -> van tra ve doan dung duoc',
                len(dq.evidence_excerpt(message, None)) > 0)
    suite.check('Trigger khong ton tai -> van tra ve doan dung duoc',
                len(dq.evidence_excerpt(message, 'khong-he-co')) > 0)
    suite.check('Thong diep rong khong lam no',
                dq.evidence_excerpt('', 'x') == '')

    # -- verify_indicator ---------------------------------------------------
    good = {
        'severity': 'CRITICAL',
        'matched_text': 'mimikatz',
        'evidence': ['... mimikatz.exe sekurlsa::logonpasswords ...'],
        'attribution': {'systems': [{'ip': '10.0.0.1', 'scope': 'LOCAL_HOST'}]},
    }
    suite.check('Chi bao dat -> khong vi pham',
                dq.verify_indicator(good) == [], str(dq.verify_indicator(good)))

    suite.check('Bat duoc trigger vang mat trong evidence',
                any('matched_text' in v for v in
                    dq.verify_indicator(dict(good, evidence=['khong co gi']))))

    peer = {'severity': 'HIGH', 'evidence': ['Logon from somewhere'],
            'severity_basis': 'Event 4648',
            'attribution': {'systems': [{'ip': '192.168.1.50', 'scope': 'REMOTE_PEER'}]}}
    suite.check('Bat duoc REMOTE_PEER vang mat trong evidence',
                any('remote_peer' in v for v in dq.verify_indicator(peer)))

    local = {'severity': 'INFO', 'evidence': ['Local logon'],
             'attribution': {'systems': [{'ip': '192.168.1.50', 'scope': 'LOCAL_HOST'}]}}
    # Máy cục bộ được quy kết vì cuộc săn CHẠY ở đó, không phải vì tên nó nằm
    # trong thông điệp — đòi nó có mặt trong evidence là đòi sai chỗ.
    suite.check('LOCAL_HOST khong bi doi phai co trong evidence',
                dq.verify_indicator(local) == [], str(dq.verify_indicator(local)))

    suite.check('Bat duoc CRITICAL khong co attribution',
                any('attribution' in v for v in
                    dq.verify_indicator({'severity': 'CRITICAL', 'evidence': ['x']})))

    no_basis = {'severity': 'HIGH', 'evidence': ['mot su kien'],
                'attribution': {'systems': [{'ip': '10.0.0.1', 'scope': 'LOCAL_HOST'}]}}
    suite.check('Bat duoc HIGH khong khai co so',
                any('severity_basis' in v for v in dq.verify_indicator(no_basis)))
    suite.check('severity_basis dang sieu du lieu duoc chap nhan',
                dq.verify_indicator(dict(no_basis, severity_basis='Event ID 4648')) == [])
    suite.check('Bat duoc chi bao khong co evidence',
                any('evidence' in v for v in
                    dq.verify_indicator({'severity': 'INFO', 'evidence': []})))
    # INFO không bị đòi khai cơ sở: mức thấp không phải một cáo buộc.
    suite.check('INFO khong bi doi khai co so',
                dq.verify_indicator({'severity': 'INFO', 'evidence': ['co gi do']}) == [])

    # -- is_self_observation ------------------------------------------------
    suite.check('Nhan ra loi goi script giam sat',
                dq.is_self_observation('python scripts/hunt_lateral_movement.py') is not None)
    suite.check('Nhan ra chuoi nhan dang noi bang |',
                dq.is_self_observation("grep -E 'lsass|mimikatz'") is not None)
    suite.check('Khong bao nham lenh tan cong that',
                dq.is_self_observation('mimikatz.exe sekurlsa::logonpasswords') is None)
    suite.check('Khong bao nham chuoi rong', dq.is_self_observation('') is None)
    suite.check('Tra ve LY DO chu khong phai True',
                isinstance(dq.is_self_observation('python scripts/mcp_bridge.py'), str))

    # -- SelfObservationLog -------------------------------------------------
    log = dq.SelfObservationLog()
    suite.check('Log: khong loai lenh binh thuong',
                log.check('notepad.exe a.txt') is False)
    suite.check('Log: loai lenh cua bo may giam sat',
                log.check('python scripts/tool_validator.py', kind='task') is True)
    report = log.report('thu nghiem')
    suite.check('Log: bao cao dung so luong',
                report['self_observed_excluded'] == 1, str(report))
    suite.check('Log: co mau de doi chieu',
                bool(report['self_observed_samples'][0].get('sample')))
    suite.check('Log: khong loai gi thi note rong',
                dq.SelfObservationLog().report('x')['self_observation_note'] is None)

    return suite

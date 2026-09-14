# -*- coding: utf-8 -*-
"""
Trạng thái THẬT trên máy này, không phải dữ liệu dựng sẵn.

Các tệp kiểm khác chứng minh luật đúng với đầu vào tổng hợp. Tệp này hỏi một câu
khác: dữ liệu đang nằm trong `state/` ngay lúc này có tuân luật không.

Cả hai đều cần. Luật đúng trên dữ liệu tổng hợp mà sai trên dữ liệu thật thì vẫn
là sai — và dữ liệu thật là thứ đi vào báo cáo.
"""

from harness import Suite

import detection_quality as dq


def run():
    suite = Suite('trang thai that (state/hunting_*.json)')

    report = dq.audit_state()

    suite.check('Khong co vi pham bat bien nao',
                report['total_violations'] == 0,
                '%d vi pham tren %d chi bao'
                % (report['total_violations'], report['total_indicators']))

    suite.check('Doc duoc it nhat mot tep hunting',
                len(report['files']) > 0, '%d tep' % len(report['files']))

    for entry in report['files']:
        suite.check('Doc duoc %s' % entry['file'], 'error' not in entry,
                    entry.get('error', ''))

    # Mọi cuộc săn phải KHAI báo cáo tự-quan-sát, kể cả khi nó loại 0 mục. Không
    # khai nghĩa là cuộc săn đó chưa có bộ lọc — và đó chính là lỗ hổng cũ.
    for entry in report['files']:
        if 'error' in entry:
            continue
        suite.check('%s co khai bo loc tu quan sat' % entry['file'],
                    entry.get('self_observed_excluded') is not None,
                    'thieu truong self_observation')

    return suite

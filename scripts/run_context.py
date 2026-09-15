# -*- coding: utf-8 -*-
"""
RUN CONTEXT (AQ-035 / AQ-040) — mỗi tệp state phải nói nó thuộc lần chạy nào.

Vấn đề mà vòng 6 và vòng 7 nhìn thấy hai câu trả lời khác nhau
---------------------------------------------------------------
Vòng 6 đọc state và thấy `risk_score 08:11:54` đứng cạnh
`hunting_credential_dumping 08:12:27` — rủi ro được tính TRƯỚC cuộc săn mà nó
trích dẫn. Vòng 7 đọc state và thấy mọi thứ đúng thứ tự.

Không có bản vá nào giữa hai vòng. Khác biệt duy nhất là vòng 6 rơi đúng lúc hai
lần chạy chồng lên nhau. Nói cách khác: **state có thể pha trộn nhiều lần chạy
và không có gì trong tệp nói ra điều đó.** Ai đọc cũng phải tự suy từ dấu thời
gian, và suy sai thì không có gì phản đối.

Dấu thời gian không thay được lần chạy: hai stage của cùng một lần chạy cách nhau
vài chục giây, còn hai lần chạy chồng nhau cũng cách nhau vài chục giây. Chỉ có
một định danh chung mới phân biệt được.

Vì sao không tự sinh `run_id` khi thiếu
----------------------------------------
Cám dỗ rõ ràng là: nếu không có biến môi trường thì sinh một id mới cho tiến
trình này. Làm vậy thì mọi tệp đều CÓ `run_id`, mọi bảng đều xanh, và phép kiểm
"cả state có cùng một lần chạy" trở thành luôn luôn đỏ theo một cách vô nghĩa —
mỗi script chạy tay sẽ tự xưng một lần chạy riêng.

Nên ở đây: chạy trong pipeline thì có `run_id` thật; chạy tay thì `run_id: null`
kèm `run_scope: STANDALONE`. Vắng mặt được khai báo, không được lấp.

Đây cũng là tiền đề kỹ thuật của AQ-039: không có `source_run_id` thì không thể
rút lại những gì một lần chạy đã sinh ra.
"""

from __future__ import print_function

import os
import uuid
from datetime import datetime

ENV_RUN_ID = 'CYBER_RUN_ID'
ENV_RUN_STARTED = 'CYBER_RUN_STARTED'

SCOPE_PIPELINE = 'PIPELINE'
SCOPE_STANDALONE = 'STANDALONE'


def new_run_id():
    """Định danh cho một lần chạy pipeline. Đọc được bằng mắt, so được bằng ==."""
    return 'RUN-%s-%s' % (datetime.now().strftime('%Y%m%dT%H%M%S'),
                          uuid.uuid4().hex[:6])


def run_id():
    """`run_id` của lần chạy hiện tại, hoặc None nếu script này chạy một mình."""
    value = os.environ.get(ENV_RUN_ID)
    return value if value else None


def run_started():
    value = os.environ.get(ENV_RUN_STARTED)
    return value if value else None


def run_scope():
    return SCOPE_PIPELINE if run_id() else SCOPE_STANDALONE


def begin_run(run=None):
    """Mở một lần chạy: đặt biến môi trường cho mọi tiến trình con kế thừa."""
    value = run or new_run_id()
    os.environ[ENV_RUN_ID] = value
    os.environ[ENV_RUN_STARTED] = datetime.now().isoformat()
    return value


def stamp(payload):
    """Đóng dấu lần chạy lên một payload state.

    Không ghi đè `run_id` đã có: một stage cố ý mang theo lần chạy khác (ví dụ
    bản ghi lịch sử) phải giữ được lần chạy của nó.
    """
    if not isinstance(payload, dict):
        return payload
    if 'run_id' not in payload:
        payload['run_id'] = run_id()
    if 'run_scope' not in payload:
        payload['run_scope'] = run_scope()
    return payload

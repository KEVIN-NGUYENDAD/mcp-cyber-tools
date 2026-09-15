# AUDIT_QUEUE_ACTIVE.md
**Last updated:** 2026-09-14 (vòng 15, BUILDER TEAM B) · **Status:** LOOP MODE · **Context:** Distilled for token efficiency

> **Cảnh báo về chính tệp này.** Bản trước của nó mô tả trạng thái vòng 7 và liệt kê
> `0 CRITICAL + 8 HIGH` với các ID (AQ-030/033/034/024/016–018/029) đã đóng từ lâu,
> trong khi `AUDIT_QUEUE.md` đã chạy tới vòng 14 với một tập mục hoàn toàn khác.
> Một Builder đọc tệp này sẽ sửa nhầm tám mục đã xong và bỏ sót sáu mục đang mở.
> Đây là cùng lỗi AQ-046 ở một tệp khác: tệp tóm tắt tụt lại sau nguồn của nó.
> **Quy tắc từ đây: tệp này chỉ được cập nhật trong cùng lần chạy với vòng audit mới.**

---

## TỒN ĐỌNG — 0 CRITICAL · 2 HIGH (hạ tầng bộ kiểm + bản ghi pipeline)

| ID | Hạng | Trạng thái vòng 15 |
|---|---|---|
| **AQ-046** | CRITICAL | ✅ `generate_handoff.build(verdict)` in `Đủ điều kiện merge` + khối `Đang chặn` từ chính `sprint_gate.evaluate()`; `verdict=None` (chạy tay) nói thẳng "chưa biết" thay vì in nửa câu trả lời. Khoá bằng `tests/gate_integrity/test_gate_integrity.py:250` — kiểm **cả hai nhánh** chặn/thông cộng nhánh standalone, đúng điều kiện nghiệm thu vòng 14 đặt ra |
| **AQ-045** | CRITICAL | ✅ `ioc_quality.py:601` ghi lại `by_severity` sau lọc, số trước lọc chuyển sang `by_severity_including_noise` + `by_severity_note`. Đo thật: `{INFO 226}` / `{INFO 422, HIGH 6}`, HIGH trong kept = **0**, Risk **23 → 5**. Bất biến `sum(by_severity) == len(kept)` nằm trong `schema_reconcile_audit.check_suppressed_severity`, cổng chặn trên `SUPPRESSED_COUNTED` / `NOISE_SCORED` |
| **AQ-002** | CRITICAL | ✅ (14 vòng) Bất biến đúng không phải `%FULL <= %asset có hostname` — tiền đề đó sai vì `assets.json` là kho một lần quét, còn 616/618 `FULL` là chính máy đang chạy. Bất biến đã cài: **`FULL` phải đi kèm hostname có nguồn ghi rõ**. Đo thật: `FULL 224 / PARTIAL 2` khớp `local host 226 / unresolved 2` — 0 `unresolved` lọt vào `FULL` |
| **AQ-047** | HIGH | ✅ `calculate_risk_score.py` đọc `capability_summary`; mỗi năng lực mù rút trọng số thành phần tương ứng (`security_events` 50%, `threat_hunting` 67%) và sinh `notes` nêu **tên** năng lực; capability floor nâng `LOW → MEDIUM` khi còn năng lực mù |
| **AQ-044** | HIGH | ✅ `run_coherence_audit.py` có `UNEVALUABLE` (3 chỗ); `sprint_gate.py:256` coi `UNEVALUABLE` và `UNSTAMPED` là **blocker**, không phải cảnh báo |
| **AQ-043** | HIGH | ✅ `state_manager.py:103` — `except ImportError` thôi nuốt: ghi `run_scope: 'UNSTAMPED'` + `run_scope_reason`. `UNSTAMPED` khác `STANDALONE`: cái sau là chạy tay có chủ ý, cái này là sự cố hạ tầng |

| **AQ-048** | HIGH | ❌ **MỚI, chưa sửa.** Bộ kiểm trượt một lần trong bốn, **không do mã**: `test_sqlite_mirror` → `PermissionError [WinError 32]`, kéo theo `test_deploy_truth` trượt vì `tests/deploy_truth/_fixture/` là thư mục **cố định** chứ không phải `mkdtemp()`. Ba lần chạy sau: `472/472` ×3; riêng từng bộ: 11/11 và 29/29. Chi tiết + sprint đề xuất ở `AUDIT_QUEUE.md` · AQ-048 |

| **AQ-050** | HIGH | ❌ **MỚI, chưa sửa** (mở trong DB-1 · TASK 4). Số stage pipeline tự phình mỗi lần chạy **cổng**, không có stage mới thật: git HEAD `34 stage / 29 tên`, cây làm việc `45 stage / 29 tên`, `"Generate Handoff" x6 → x17`; cổng in `36 → 41 → 43` trong một phiên không chạy pipeline lần nào. Nguyên nhân: `generate_handoff.py:335` `append` vào bản ghi của lần chạy **trước** (giữ nguyên `run_id`, `timestamp`, `duration 28.83s`). `gate_integrity:109` không bắt vì chỉ hỏi `bool(stages)`. Chi tiết + sprint đề xuất ở `AUDIT_QUEUE.md` · AQ-050. **AQ-049 không tồn tại** — khoảng trống có chủ ý |

**Đang mở: 2 (0 CRITICAL, 2 HIGH — AQ-048, AQ-050). Đã trả tích luỹ: 41.**

> **Mục tiêu `CRITICAL = 0, HIGH = 0` đạt được trên hàng đợi nhận vào đầu vòng 15**
> (AQ-046/045/002/047/044/043 — toàn bộ đóng, có bằng chứng). AQ-048 là mục **phát
> sinh trong chính vòng này**, tìm ra nhờ chạy bộ kiểm nhiều lần. Nó không được sửa
> ở đây vì nằm ngoài phạm vi và chạm vào hai bộ kiểm không liên quan tới hàng đợi —
> báo ra thay vì lặng lẽ để đó, vì một cổng thỉnh thoảng đỏ vì lý do không phải lỗi
> mã sẽ bị học cách chạy lại cho tới khi xanh.

---

## VIỆC VÒNG 15 LÀM — bịt lỗ hổng cuối: bộ dò chưa từng được kiểm

Sáu mục trên đã có bản sửa trong mã tại HEAD. Vòng 14 đo trên commit cũ hơn nên
báo chúng còn mở — đó là chênh lệch giữa auditor và cây làm việc, không phải nợ.

Nhưng khi đối chiếu *bản sửa* với *bằng chứng bản sửa được giữ*, còn đúng một lỗ:

**`scripts/schema_reconcile_audit.py` giữ bốn bất biến mà cổng chặn merge trên đó —
và chính nó chưa có một phép kiểm nào.** Nó in `TONG: 0 vi pham`. Câu đó có thể
nghĩa là "hai đầu mọi phép cộng khớp", hoặc nghĩa là "không phép kiểm nào chạy".
Nhìn từ cổng, hai câu trả lời giống hệt nhau. Đó đúng là lớp lỗi AQ-030 đã dạy, và
là lý do AQ-045/AQ-002 chưa thể đóng: bất biến của chúng đúng **hôm nay**, không có
gì khoá lại cho ngày mai.

**Đã thêm:** `tests/schema_reconcile/test_schema_reconcile.py` — **21/21**.
Không ca nào hỏi "hôm nay có vi phạm không". Mỗi ca tiêm đúng một loại lệch vào một
`state/` giả trong thư mục tạm rồi hỏi bộ dò **có báo không**, và gỡ ra rồi hỏi nó
**có im lại không**:

- `SUPPRESSED_COUNTED` + `NOISE_SCORED` (AQ-045), kèm hai ca âm: chỉ báo bị lọc
  *tồn tại* là bình thường — phải im; còn một `HIGH` thật thì khai `HIGH` là đúng —
  cũng phải im (không dương tính giả).
- `ATTRIBUTION_UNBACKED` (AQ-002), kèm ngoại lệ hợp lệ `local host` phải im và
  `PARTIAL` trên peer `unresolved` phải im.
- `SUM_MISMATCH` / `CONSTANT_SCORE` / `NO_TOTAL` (AQ-020), gồm đúng hình dạng
  `score 100` trên `19 finding` chưa phân loại.
- `UNIT_UNDECLARED` / `UNIT_MISSING` / `UNIT_MISMATCH` (AQ-021), gồm ca `399 luot`
  cạnh `64 plugin` **khai đủ đơn vị → phải im**: đây chính là con số tám vòng audit
  gọi nhầm là "lỗi đếm".
- Vắng mặt không được đọc thành sạch: không có state → `KHONG DOC DUOC`, không bịa.
- `len(INVARIANTS) == 4` và cả bốn đều khai phạm vi — thêm một check mà quên nối vào
  `INVARIANTS` sẽ không còn im lặng.

**Đã kiểm chứng phép kiểm bắt được thật (mutation):** vô hiệu hoá `if counted != kept`
trong bộ dò → suite tụt `21/21 → 20/21`; phục hồi → `21/21`. Một fixture chưa từng
được chứng minh là **trượt được** thì chưa phải bằng chứng.

**Đã sửa kèm:** `sprint_gate.py:600` in phạm vi của **hai** bất biến trong khi bộ dò
chạy **bốn** — `attribution` và `suppressed` chạy thật nhưng không hiện ở đâu trên
màn hình cổng. Cùng một lỗi: phép kiểm chạy mà không khai phạm vi đọc lên giống hệt
phép kiểm không chạy. Nay in đủ bốn dòng.

---

## CỔNG — 2026-09-14, vòng 15

    PASS 93 | EMPTY 6 | BLIND 0 | FAIL 0
    Bộ kiểm phát hiện : ĐẠT  (TONG: 472/472 dat)      <- 451 + 21 mới
    Toàn vẹn bằng chứng: 0 vi phạm / 570 chỉ báo
    Pipeline           : 38 stage, 0 thất bại
    Đối chiếu lược đồ  : 0 vi phạm | crypto 19/19, score 90 | vuln assets 399 luot
                         quy kết   570 chi bao | local host 570, unresolved 2
                         lọc nhiễu lateral 226/226 | persistence 96/96 | proc 46/46
    Gắn kết lần chạy   : 7/7 tệp có dấu
    KET QUA: DU DIEU KIEN MERGE

---

## NEXT AUDIT FOCUS

Hàng đợi hết CRITICAL và HIGH. Hai chỗ đáng soi tiếp, **không phải** để mở rộng
phạm vi mà vì cả hai là cùng một câu hỏi "bộ dò có báo được không":

1. **Độ phủ trường Python 16.7%** (109 kiểm / 652 lời gọi). Mẫu số đã được in ra
   (AQ-034), nên con số này trung thực — nhưng 543 lời gọi đọc state vẫn ngoài tầm
   đối chiếu. Đây là nợ đã ghi nhận, không phải drift.
2. **Các bộ dò khác chưa có mutation test.** `schema_reconcile` vừa được chứng minh
   là trượt được; `deploy_truth`, `run_coherence_audit`, `portal_escape_audit` thì
   chưa. Cùng lập luận vừa dùng ở đây áp thẳng sang chúng.

---

*Token-efficient tracking. Lịch sử đầy đủ ở `AUDIT_QUEUE.md` (vòng 1–15).*

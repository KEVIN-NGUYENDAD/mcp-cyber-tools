# AUDIT_QUEUE

Vòng audit: 2026-09-14
Builder commit được audit: `a0b8262` (PR #41, Sprint 17 — "improve IOC quality, attribution and confidence scoring")
HEAD: `1c8a386` · branch `develop` · working tree sạch
Auditor: READ ONLY. Không sửa file production, không commit, không push, không merge.

Chỉ ghi CRITICAL và HIGH. LOW không ghi.
`[MỚI]` = sinh ra hoặc lộ ra từ Sprint 17. `[TỒN]` = đã báo vòng trước, chưa trả.

---

## GHI CHÚ QUY TRÌNH

`docs/project/HANDOFF.md` **không tồn tại**. Hai tệp gần nhất (`AI_HANDOFF.md`,
`SESSION_STATE.md`) được dùng thay và cả hai sai lệch nặng — xem AQ-011.
Vòng này audit trực tiếp từ `git log` + state đã commit.

---

## AQ-001 · [MỚI] · Ưu tiên 1 — Schema Drift

**Issue:**
`ioc_quality.average_score` và toàn bộ phân phối chất lượng được tính trên mẫu số
**228**, nằm cạnh `total: 455` trong cùng một object. Điểm trung bình công bố là
**96.3**; điểm trung bình thật trên 455 chỉ báo là **72.7**.

**Severity:** CRITICAL

**Root Cause:**
`ioc_quality.py` loại 227 chỉ báo `suppressed` khỏi mọi phân phối nhưng giữ nguyên
`total` đếm cả 455. Chính Sprint 17 tạo ra lớp noise này, rồi công bố chỉ số chất
lượng của phần còn lại dưới cái tên "average_score" mà không nhãn mẫu số. Cùng tệp
đó, `by_severity` lại dùng mẫu số 455. Hai mẫu số, một tệp, không nhãn.

**Evidence:**
`state/hunting_lateral_movement.json` → `ioc_quality`:

    total: 455          suppressed: 227
    by_confidence   -> tổng 228
    by_attribution  -> tổng 228
    by_evidence     -> tổng 228
    average_score   -> 96.3
    by_severity (cấp tệp) -> {INFO: 453, HIGH: 2} = tổng 455

Kiểm lại trực tiếp trên mảng `indicators`:

    n=455  mean=72.7      <- sự thật
    n=228  mean=96.3      <- con số được công bố

Chênh **+23.6 điểm**. Bất kỳ ai tính phần trăm từ tệp này đều ra số sai.

`tests/ioc_quality/test_ioc_quality.py:258-271` có kiểm `suppressed` khớp số đếm,
nhưng **không** kiểm mẫu số của `average_score`. Bộ test mới xác minh sổ sách,
không xác minh tính đúng của chỉ số.

**Suggested Sprint:** SPRINT ONE-DENOMINATOR — mọi khối thống kê phải tự khai mẫu
số (`scored_population: 228 / 455`), hoặc đổi tên thành
`average_score_excluding_noise` kèm `average_score_all`. Thêm test: tổng mọi phân
phối phải bằng một mẫu số đã khai báo trong cùng object.

---

## AQ-002 · [MỚI] · Ưu tiên 1 — Schema Drift

**Issue:**
Commit message Sprint 17 tuyên bố *"Attribution quality fell as a result — that is
the real number appearing, not quality dropping."* Trong dữ liệu nó sinh ra,
attribution **không hề giảm**: **600 / 602** chỉ báo vẫn khai `FULL`.

**Severity:** CRITICAL

**Root Cause:**
Bản vá hostname được áp ở phía tài sản (`extract_asset_intelligence.py` +
`asset_builder.py`) — và ở đó nó chạy đúng: cả 11 tài sản giờ là
`hostname: null, hostname_source: "unresolved"`. Nhưng `ioc_quality.py` chấm
`attribution_quality` bằng **sự hiện diện của IP**, không bằng hostname đã phân
giải. Hai nửa của cùng một bản vá không nối với nhau, nên kết quả được tuyên bố
trong commit message không tồn tại trong state.

**Evidence:**
`state/assets.json` — 11/11 tài sản:

    192.168.0.1    hostname=None  hostname_source=unresolved
    ... (cả 11 dòng giống hệt)

`state/hunting_*.json` — `attribution_quality`:

    lateral_movement : FULL 453 / PARTIAL 2
    persistence      : FULL  96
    suspicious_proc  : FULL  51
    -> FULL 600 / 602 = 99.7%

Không một máy nào phân giải được tên, nhưng 99.7% chỉ báo khai "đã quy kết đầy đủ".
Commit message cũng viết *"The local host still resolves fully"* — trong state
không có máy nào resolve, kể cả local host.

**Suggested Sprint:** SPRINT ATTRIBUTION-TRUTH — `attribution_quality` phải đọc
`hostname_source`. `FULL` chỉ khi định danh máy được phân giải; IP một mình là
`PARTIAL`. Gate bổ sung: `%FULL attribution` không được vượt
`%assets có hostname_source != unresolved`.

---

## AQ-003 · [TỒN] · Ưu tiên 3 — Risk Consistency

**Issue:**
`calculate_risk_score.py` đọc khoá `score` từ `waap_score.json`. Khoá đó không tồn
tại. Hệ số WAAP (weight 0.10) đã luôn là hằng số mặc định `50`.

**Severity:** CRITICAL

**Root Cause:**
`calculate_waap_score.py` đổi tên `score` → `health_score`; consumer không được
cập nhật. `.get(key, default)` biến lỗi thành một con số trông hợp lệ. Sprint 17
không chạm tệp này (`git log -- scripts/calculate_risk_score.py` → lần cuối `ada0785`).

**Evidence:**
`scripts/calculate_risk_score.py:115`

    score = waap.get('score', 50)

`state/waap_score.json` keys: `checks, component_scores, domain, grade,
health_score, issue_count, issues, recommendations, status, timestamp` —
**không có `score`**. `health_score = 80` (grade B).

`state/risk_score.json` factor:

    {"name":"waap","health":50,"weight":0.1,"risk_contribution":5.0,"detail":"WAAP score 50"}
    overall_score = 13

**5.0 / 13 = 38% điểm rủi ro hiện tại là một hằng số fallback, dán nhãn là số đo.**

Ba định nghĩa WAAP đang cùng tồn tại: `calculate_waap_score` = 80,
`calculate_risk_score` = 50, `web/app.js:216-219` tự tính lại = 60.

**Suggested Sprint:** SPRINT NO-SILENT-DEFAULT — khoá bắt buộc phải raise, không
`.get(k, default)`. Đồng thời mở rộng field audit sang **pipeline Python** — hiện
`portal_field_audit.py` và `telegram_field_audit.py` chỉ soi JavaScript, còn mọi
con số thì được tính bằng Python. Đây chính là lý do lỗi này sống sót qua merge
gate xanh.

---

## AQ-004 · [TỒN → LEO THANG BỞI SPRINT 17] · Ưu tiên 4 — Correlation Integrity

**Issue:**
`correlation_engine.py` ghi hai giá trị confidence mâu thuẫn vào cùng một bản ghi
và publish giá trị sai. Sprint 17 vừa đưa bản ghi đó lên **trang đầu portal**.

**Severity:** CRITICAL

**Root Cause:**
`correlation_engine.py:522` — `confidence='HIGH' if ip in known_assets else 'MEDIUM'`.
Confidence được suy từ *"IP này có trong kho tài sản không"* — một thuộc tính của
kho, không phải của bằng chứng. `attach_ioc_quality()` chạy **sau** khi finding đã
dựng xong (`run()`, dòng 775), tính điểm thật rồi ghi vào một khoá **khác**. Không
có vòng phản hồi. Consumer đọc khoá cấp cao.

Sprint 17 thêm `renderExecutiveFindings()` (`web/app.js:472+`), nên mâu thuẫn này
không còn nằm trong một tệp không ai đọc — nó đang hiển thị cho analyst.

**Evidence:**
`state/executive_findings.json` → `EF-0002`:

    severity                 HIGH
    confidence               HIGH      <- consumer đọc cái này
    confidence_score         49
    ioc_quality.confidence   LOW       <- engine tự biết
    ioc_quality.basis        "...điểm thấp nhất 49... 227 đầu vào đã bị hạ xuống tiếng ồn"
    by_confidence (tổng kết) {HIGH: 1, LOW: 1}   <- tổng kết đếm giá trị thật

Engine biết finding này là LOW, ghi hiểu biết đó vào tệp, rồi ship `HIGH` ở đúng
trường mà portal và Telegram đọc.

**Suggested Sprint:** SPRINT CONFIDENCE-SINGLE-SOURCE — chuyển `attach_ioc_quality()`
lên **trước** khi dựng finding; `severity` và `confidence` phải suy ra **từ** điểm
bằng chứng. Xoá `'HIGH' if ip in known_assets`. Cấm hai trường confidence trong một
bản ghi.

---

## AQ-005 · [TỒN] · Ưu tiên 4 — Correlation Integrity

**Issue:**
227 chỉ báo đã bị chính hệ thống đánh dấu `suppressed: true` /
`noise_class: ROUTINE_OS_ACTIVITY` vẫn được dùng để dựng một finding **HIGH**.

**Severity:** CRITICAL

**Root Cause:**
`correlation_engine.py:101-104` — `indicators()` không lọc `suppressed`.
Gán severity ở dòng 497: `'CRITICAL' if critical else 'HIGH'` — bất cứ thứ gì không
CRITICAL đều thành **HIGH**, kể cả khi toàn bộ đầu vào là INFO.

**Evidence:**
`EF-0002` dựng từ 455 chỉ báo lateral, trong đó **227 suppressed**.
`hunting_lateral_movement.json → by_severity = {INFO: 453, HIGH: 2}`.
→ **453 chỉ báo INFO sinh ra một finding HIGH.**
`ioc_quality.suppressed_inputs: 227` được ghi ngay trong finding đó rồi bỏ qua.

Kèm theo: mảng `evidence` của `EF-0002` có **456 phần tử, 11 phần tử duy nhất** —
445 dòng lặp nguyên văn `[Lateral] Remote Logon: Remote Logon (Event 4624)`.

**Suggested Sprint:** SPRINT CORRELATION-HONESTY — lọc `suppressed` trong
`indicators()` (một dòng, loại 227 đầu vào ma). Severity phải kế thừa severity đầu
vào: 453 INFO không được ra HIGH. Dedup `evidence`, giữ số đếm (`x445`).

---

## AQ-006 · [TỒN] · Ưu tiên 6 — Telegram Truth

**Issue:**
`/evidence` khẳng định hash verification PASSED, container tamper-proof và chữ ký số
đã được xác minh. `/analytics` in bốn phần trăm hardcode như thể là phát hiện.

**Severity:** CRITICAL

**Root Cause:**
`telegramBot.js:800-823` — toàn bộ chuỗi khẳng định chain-of-custody có đúng một đầu
vào: `custodyValid = reportCount > 0`. Không có hash nào được tính trong repo. Không
có chữ ký nào được xác minh ở đâu.
`telegramBot.js:619-623` — bốn hằng số, đặt ngay dưới risk score thật và WAAP score
thật, định dạng giống hệt.

`telegram_field_audit.py` **về cấu trúc không thể** bắt lớp lỗi này: nó kiểm các
trường được *đọc*. Output bịa không đọc trường nào, nên một tin nhắn hoàn toàn bịa
đặt đạt điểm audit tuyệt đối.

**Evidence:**

    telegramBot.js:800  const custodyValid = reportCount > 0;
    telegramBot.js:805  *Status*: ${custodyValid ? 'VERIFIED' : ...}
    telegramBot.js:809  Hash Verification: ${custodyValid ? 'PASSED' : ...}
    telegramBot.js:816  Tamper-proof container
    telegramBot.js:817  Digital signature verified

    telegramBot.js:619-623
      • Persistence Mechanisms (23%)
      • Lateral Movement (18%)
      • Credential Access (15%)
      • Privilege Escalation (14%)     <- repo không có hunt "Privilege Escalation"

**Suggested Sprint:** SPRINT DELETE-FABRICATION — thuần xoá. Bỏ bốn phần trăm. Bỏ
khối hash/chữ ký, hoặc tính SHA-256 thật, hoặc ghi
`Chain of custody: NOT IMPLEMENTED`. Thêm lint: không literal số hay dấu tick nào
trong template bot mà không truy được về một trường state.

---

## AQ-007 · [TỒN] · Ưu tiên 7 — Deployment Truth

**Issue:**
Portal được audit không phải portal được deploy.

**Severity:** CRITICAL

**Root Cause:**
`render.yaml` → `startCommand: node web-server.js`.
`package.json` → `"start": "node web/server.js"`.
`web-server.js` chỉ phục vụ `/`, `/latest`, `/brief/:date`, `/api/briefs`,
`/health` — **thuần HTML daily brief**. Nó không bao giờ phục vụ `web/index.html`,
`web/app.js`, hay `/api/state/*`.

`portal_field_audit.py` soi `web/app.js` đối chiếu `web/server.js`. **Không tệp nào
trong hai tệp đó chạy trên production.** `TECHNICAL_DEBT.md` báo
`Trường portal đọc sai: 0` cho một bề mặt Render không phục vụ.

**Evidence:**

    render.yaml:  startCommand: node web-server.js   branch: develop
    package.json: "start": "node web/server.js"
    web-server.js: grep 'web/app.js' -> không có kết quả
    daily_brief/latest.html -> chứa 2026-09-13
    daily_brief/2026-09-14.json tồn tại; 2026-09-14.html KHÔNG tồn tại

Trang duy nhất người dùng thật sự chạm tới đang cũ một ngày và không nói ra điều đó.

Kèm theo: 5 entrypoint server cùng tồn tại (`server.js`, `server_v2.js`,
`server_backup_v1.js` — byte-identical với v2 —, `web-server.js`, `web/server.js`).

**Suggested Sprint:** SPRINT DEPLOY-TRUTH — chốt một entrypoint, đồng bộ
`render.yaml` với `package.json`, xoá ba server chết. Sửa sinh `latest.html`, đóng
dấu tuổi dữ liệu lên trang. Sau đó quyết định: hoặc deploy `web/server.js` (khi đó
AQ-009 và vấn đề không-auth/CORS-wildcard thành release blocker), hoặc ngừng audit
nó và chuyển `portal_field_audit.py` sang bộ sinh brief HTML.

---

## AQ-008 · [MỚI] · Ưu tiên 3 — Risk Consistency

**Issue:**
`trust_score` = **100** cho cả 11/11 tài sản. `trust_level` = **CRITICAL_ASSET**
cho cả 11/11. Một chỉ số có phương sai bằng không trên 100% mẫu.

**Severity:** HIGH

**Root Cause:**
`asset_builder.py:185-204` — `mac_consistency` là thành phần lớn nhất (**40/100
điểm**) và luôn `observable: false` vì *"assets.json không mang trường MAC"*. Kỷ
luật `points_available` loại nó khỏi **cả tử số lẫn mẫu số**, nên mọi máy được chấm
60/60 → chuẩn hoá thành 100. `MIN_BASIS_POINTS = 40` nên 60 vẫn lọt, không ai bị
gắn `INSUFFICIENT_DATA`.

Kỷ luật này đúng về nguyên tắc. Áp ở đây nó xoá mất chính biến phân biệt lớn nhất,
và sinh ra một điểm tin cậy không phân biệt được máy nào với máy nào.

Vấn đề thứ hai, riêng: ngưỡng `score >= 85 -> 'CRITICAL_ASSET'` gộp hai câu hỏi khác
nhau — *"ta tin định danh máy này tới đâu"* và *"máy này quan trọng tới đâu"*. Nhãn
đọc lên là câu thứ hai; công thức tính câu thứ nhất.

**Evidence:**

    trust_level : Counter({'CRITICAL_ASSET': 11})
    trust_score : Counter({100: 11})
    trust_basis : points_available=60, points_possible=100,
                  unobservable=['mac_consistency']  (max 40)
    asset_builder.py:55   MIN_BASIS_POINTS = 40
    asset_builder.py:208  if score >= 85: return 'CRITICAL_ASSET'

Bán kính ảnh hưởng hiện giới hạn: `trust_level` chỉ được đọc bởi
`scripts/asset_manager.py` (CLI). Portal, Telegram, risk engine, correlation đều
không đọc. Nhưng chỉ số vẫn đang được sinh, commit và báo cáo như một số đo thật.

**Suggested Sprint:** SPRINT TRUST-VARIANCE — hoặc thu thập MAC (ARP đã có sẵn,
`shadow_asset_detector.py` đang đọc nó) để khôi phục 40 điểm, hoặc nâng
`MIN_BASIS_POINTS` trên 60 để 11 máy này được gắn đúng `INSUFFICIENT_DATA`. Đổi tên
`CRITICAL_ASSET` → `IDENTITY_VERIFIED`. Thêm gate: chỉ số có phương sai 0 trên toàn
bộ mẫu phải được báo là chưa phân biệt được, không được báo là 100.

---

## AQ-009 · [MỚI] · Ưu tiên 5 — Portal Truth

**Issue:**
Sprint 17 thêm `escapeHtmlSafe()` và áp nó cho **đúng một panel mới**. 26 sink
`innerHTML` có sẵn — gồm sink nhận command line và tên tiến trình thu từ máy được
giám sát — vẫn không escape.

**Severity:** HIGH

**Root Cause:**
Hàm escape được viết cho panel đang xây, không được coi là bản vá cho lớp lỗi. Sau
Sprint 17 repo có một helper chứng minh đội đã biết rủi ro, áp dụng ở 1/26 chỗ. Dữ
liệu DFIR bị đối xử như dữ liệu nội bộ đáng tin; nó là đầu vào **không đáng tin**
theo đúng định nghĩa.

**Evidence:**

    web/app.js:627  function escapeHtmlSafe(text)   <- MỚI, Sprint 17
    grep -c escapeHtmlSafe -> 15 lần dùng, toàn bộ trong renderExecutiveFindings()
    grep -c innerHTML      -> 26 sink

    web/app.js:1579-1585  (KHÔNG đổi trong Sprint 17)
      indicators.slice(0, 10).map(ind => `
        ...${ind?.type || ind?.process || ind?.pattern || 'Unknown'}...`)
      el.innerHTML = html

`ind.process` / `ind.command_line` đến từ tiến trình và scheduled task trên host
được giám sát. Một tiến trình đặt tên `<img src=x onerror=...>` thực thi trong
dashboard của analyst.

**Suggested Sprint:** SPRINT ESCAPE-ALL — áp `escapeHtmlSafe` cho cả 26 sink, hoặc
chuyển sang `textContent`. Thêm lint chặn `innerHTML` với template literal chứa biến
chưa escape.

---

## AQ-010 · [TỒN] · Ưu tiên 5 — Portal Truth

**Issue:**
KPI `threats-total` đếm **602** trong khi con số thật là **375**. Bốn danh sách
top-10 lấy `.slice(0, 10)` trên mảng **chưa sắp xếp**.

**Severity:** HIGH

**Root Cause:**
`web/app.js:1553-1568` gộp bốn mảng `indicators` không lọc `suppressed`
(grep `suppressed` trong `web/app.js` → 0 kết quả). Sprint 17 có sửa `web/app.js`
(+80 dòng) nhưng không chạm hàm này.

**Evidence:**

    web/app.js:1564  'threats-total': allIndicators.length          -> 602
    suppressed thật  : 227  ->  con số trung thực là 375
    web/app.js:1579  indicators.slice(0, 10)   <- không sort
    hunting_lateral_movement: by_severity = {INFO: 453, HIGH: 2}

Hai chỉ báo `HIGH` thật nằm ở vị trí bất kỳ trong 455 phần tử. Panel gần như chắc
chắn hiển thị mười mục INFO và giấu cả hai HIGH.

**Suggested Sprint:** SPRINT PORTAL-SIGNAL — lọc `suppressed`, sort theo severity rồi
mới `.slice(0, 10)`. Hiển thị `375 (+227 noise)` thay vì `602`.

---

## AQ-011 · [MỚI] · Ưu tiên 2 — Source of Truth Drift

**Issue:**
`docs/project/HANDOFF.md` — tệp mà quy trình audit yêu cầu đọc mỗi phiên — **không
tồn tại**. Hai tệp handoff đang có mô tả một hệ thống khác với hệ thống đang chạy.

**Severity:** HIGH

**Root Cause:**
Handoff được viết tay trong phiên 2026-09-07 và không bao giờ được sinh lại từ
state. `TECHNICAL_DEBT.md` được sinh tự động từ `sprint_gate.py` và chính xác;
handoff thì không, và không có gì đánh dấu sự khác biệt đó.

**Evidence:**

    ls docs/project/HANDOFF.md -> No such file or directory

`docs/project/SESSION_STATE.md` (đề ngày 2026-09-07) so với state hôm nay:

                        HANDOFF nói     STATE thật
    Risk Score          74/100          13
    Open Incidents      18              1
    Critical Count      7               0
    Threat Level        HIGH            LOW

`docs/project/AI_HANDOFF.md` khai `develop @ 41dc197`; HEAD thật là `1c8a386`
(cách 40+ commit). Cũng khai *"4 CRITICAL issues fixed in code but NOT deployed"* —
không khớp bất cứ mục nào trong hàng đợi này.

Bất kỳ Builder hay AI nào onboard theo đúng hướng dẫn sẽ khởi động với một bức
tranh rủi ro sai lệch gấp 5.7 lần.

**Suggested Sprint:** SPRINT HANDOFF-GENERATED — sinh `HANDOFF.md` từ
`sprint_gate.py` như `TECHNICAL_DEBT.md`, đọc thẳng từ `state/`. Lưu trữ
`SESSION_STATE.md` và `AI_HANDOFF.md` vào `docs/archive/` kèm ngày, hoặc xoá. Không
để tài liệu viết tay nào công bố số liệu mà state đã trả lời.

---

## AQ-012 · [MỚI] · Ưu tiên 1 — Schema Drift

**Issue:**
`hunting_persistence.json`: **96/96** chỉ báo có `confidence_score` đúng bằng 100,
`confidence: HIGH`, `attribution_quality: FULL`, `evidence_quality: COMPLETE` —
trong khi `by_severity` của chính tệp đó là `{INFO: 96}`.

**Severity:** HIGH

**Root Cause:**
Cùng bệnh phương sai-bằng-không với AQ-008: thang điểm chỉ chấm những trường mà
evidence class đó cấp được, nên mọi chỉ báo cùng class đều đạt tuyệt đối. Với
persistence, mọi chỉ báo đều cùng một class → mọi chỉ báo đều 100.

Thêm nữa: 96 chỉ báo `severity: INFO` mang `confidence: HIGH` cạnh nhau. Sprint 17
tách severity khỏi confidence một cách có chủ đích và đó là quyết định đúng — nhưng
hệ quả chưa được xử lý ở tầng hiển thị, nơi cả hai từ cùng xuất hiện mà không có gì
giải thích chúng trả lời hai câu hỏi khác nhau.

**Evidence:**

    hunting_persistence.json
      n=96
      confidence         : Counter({'HIGH': 96})
      confidence_score   : Counter({100: 96})
      attribution_quality: Counter({'FULL': 96})
      evidence_quality   : Counter({'COMPLETE': 96})
      by_severity        : {'INFO': 96}
      ioc_quality.average_score: 100.0

Một tệp mà toàn bộ 96 bản ghi đạt điểm tối đa ở cả bốn chiều thì bốn chiều đó không
phân loại được gì trong tệp này.

**Suggested Sprint:** SPRINT SCORE-DISCRIMINATION — với mỗi evidence class, báo
phương sai điểm. Class có phương sai 0 phải bị gắn cờ "chưa phân biệt được" trong
`ioc_quality`, không được báo `average_score: 100.0`. Ở tầng hiển thị, không đặt
severity cạnh confidence mà thiếu nhãn nói rõ hai câu hỏi.

---

## TỔNG KẾT VÒNG NÀY

| | |
|---|---|
| CRITICAL | **7** (AQ-001, 002, 003, 004, 005, 006, 007) |
| HIGH | **5** (AQ-008, 009, 010, 011, 012) |
| Mới từ Sprint 17 | 5 (AQ-001, 002, 008, 009, 012) + AQ-011 (quy trình) |
| Tồn từ vòng trước, chưa trả | 6 (AQ-003, 004, 005, 006, 007, 010) |
| Leo thang bởi Sprint 17 | AQ-004 — mâu thuẫn confidence nay hiển thị trên portal |

**Đánh giá về Sprint 17.**
Ba việc Builder làm là đúng và nên giữ: bản vá hostname ở phía tài sản là trung thực
(`unresolved` thay vì IP copy); `escapeHtmlSafe` là đúng hàm; và việc đưa
`executive_findings.json` lên portal đã sửa một tệp không ai đọc. Kỷ luật
`points_available` cũng là nguyên tắc đúng.

Nhưng cả ba đều dừng ở nửa đường: bản vá hostname không nối sang `ioc_quality.py`
(AQ-002), hàm escape chỉ áp cho panel mới (AQ-009), và panel mới publish một bản ghi
mà engine tự biết là LOW (AQ-004). Còn kỷ luật `points_available`, áp vào cả
`trust_score` lẫn `ioc_quality`, đã sinh ra hai chỉ số có phương sai bằng không
(AQ-008, AQ-012) và một điểm trung bình lệch 23.6 điểm (AQ-001).

**Nguyên nhân gốc không đổi so với vòng trước:** mọi bộ audit trong repo hỏi
*"trường này có tồn tại không?"*. Chưa bộ nào hỏi *"con số này có đúng không?"*.
Merge gate vẫn xanh trên cả 12 mục ở trên.

**Đề xuất thứ tự trả nợ:** AQ-003 → AQ-001 → AQ-002 → AQ-006 → AQ-004/005 → AQ-007
→ AQ-009/010 → AQ-008/012 → AQ-011.
AQ-003 trước tiên vì nó đang làm sai 38% điểm rủi ro và bản vá là một dòng. AQ-006
là thuần xoá, không rủi ro, và loại bỏ hai lời nói dối nghiêm trọng nhất mà hệ thống
đang phát ra.

---

*Sinh bởi vòng CHIEF AUDITOR 2026-09-14. Read-only: không file production nào bị
sửa, không commit, không push, không merge.*


---
---

# VÒNG 2 — 2026-09-14 (tiếp)

Phạm vi săn theo yêu cầu: **Schema Drift · Truth Gap · Fallback giả · Default xanh giả**.
Thứ tự ưu tiên: 1. Kill Green Defaults · 2. Pipeline Field Audit · 3. Correlation Honesty.
**Executive Narrative: CHƯA LÀM** — đúng như chỉ đạo. Sửa sự thật trước, kể chuyện sau.

Auditor vẫn READ ONLY. Không file production nào bị sửa, không commit, không push, không merge.

---

## TRẠNG THÁI VÒNG 1 (working tree, CHƯA commit)

Builder đang sửa trong lúc audit. Đối chiếu trực tiếp với state vừa sinh lúc 07:49:

| Mục | Trạng thái | Bằng chứng |
|---|---|---|
| AQ-001 | ✅ **ĐÃ TRẢ** | `ioc_quality` nay có `average_score_all: 72.7`, `scored_population: 228`, `population_note`, `by_confidence_all` |
| AQ-003 | ✅ **ĐÃ TRẢ** | `required()` thay `.get(k, default)`; risk factor waap health=**80**; `overall_score` 13 → **10**; renormalize theo `weight_available` |
| AQ-008 | ✅ **ĐÃ TRẢ (mức trung thực)** | `CRITICAL_ASSET` → `IDENTITY_VERIFIED`; `trust_summary.variance: 0.0, discriminating: false` + ghi chú mẫu số khác nhau (60 vs 100). Điểm vẫn 100×11 nhưng **không còn nói dối về điều đó** |
| AQ-012 | ✅ **ĐÃ TRẢ (mức trung thực)** | `by_class_variance` → `REGISTRY/SCHEDULED_TASK: discriminating: false` |
| AQ-002 | ❌ **CÒN NGUYÊN** | `attribution_quality` vẫn `FULL 453 / PARTIAL 2` trong khi 11/11 tài sản `hostname_source: unresolved` |
| AQ-004, 005, 006, 007, 009, 010, 011 | ❌ **chưa chạm** | |

Bốn mục đã trả đều trả **đúng cách**: không bịa ra con số đẹp hơn, mà công bố phương
sai và mẫu số để người đọc tự thấy chỉ số chưa phân biệt được gì. Đó là chuẩn nên
giữ cho các mục còn lại.

---

## AQ-013 · [MỚI] · Ưu tiên 1 — Default xanh giả

**Issue:**
Cổng merge đọc khoá `success` trên mỗi stage pipeline. Bộ ghi pipeline ghi khoá
`status`. `.get('success', True)` khiến **cả 27/27 stage mặc định là ĐẠT**. Phép
kiểm pipeline của cổng merge **chưa bao giờ có khả năng thất bại**.

**Severity:** CRITICAL

**Root Cause:**
`sprint_gate.py:152` — `failed_stages = [s for s in stages if not s.get('success', True)]`.
`run_intelligence_pipeline.py` ghi mỗi stage với các khoá `duration, name, output, status`.
Không stage nào có khoá `success`. Mặc định `True` nuốt trọn sự khác biệt tên trường.

Đây là default xanh giả nằm **bên trong chính bộ phận quyết định mã có được ship hay
không** — nơi duy nhất trong repo mà một default xanh không được phép tồn tại.

**Evidence:**

    sprint_gate.py:152   [s for s in stages if not s.get('success', True)]

    logs/pipeline_results.json
      n_stages = 27
      keys of stage[0] = ['duration', 'name', 'output', 'status']
      stages KHÔNG có khoá 'success' = 27   (toàn bộ)

`docs/project/TECHNICAL_DEBT.md` in ra:

    | Pipeline | 27 stage, 0 thất bại |

Con số **0** đó không phải số đo. Nó là `len([])` trên một danh sách không thể khác
rỗng. Hiện tại cả 27 stage đều thật sự `status: success`, nên default này chưa che
giấu một thất bại nào — nhưng nó **không có khả năng phát hiện** thất bại nào, và
"0 thất bại" đang được in ra như một kết luận đã kiểm.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (ưu tiên 1) — cổng merge phải đọc
đúng khoá `status`, và một stage **thiếu** trường trạng thái phải là BLOCKER, không
phải PASS. Nguyên tắc: trong `sprint_gate.py` cấm mọi default mang nghĩa "đạt";
thiếu dữ liệu = chặn.

---

## AQ-014 · [MỚI] · Ưu tiên 2 — Pipeline Field Audit

**Issue:**
Một lần đổi tên khoá (`score` → `health_score`) đã âm thầm làm hỏng **năm** consumer.
Vòng 1 chỉ đích danh một. Builder đã sửa đúng một. **Bốn cái còn lại vẫn đang chạy**,
mỗi cái với một default giả theo một hướng khác nhau.

**Severity:** CRITICAL

**Root Cause:**
`calculate_waap_score.py` ghi `health_score`. Không consumer nào được cập nhật. Mỗi
consumer tự chọn một default riêng, nên cùng một metric cho ra năm con số khác nhau
mà không tầng nào báo lỗi. Không có bộ audit nào soi pipeline Python — hiện chỉ
`portal_field_audit.py` và `telegram_field_audit.py` tồn tại, cả hai đều soi JavaScript.

**Evidence:**
Sự thật: `state/waap_score.json` → `health_score: 80`, `grade: "B"`, `status: "healthy"`.
Khoá `score` **không tồn tại**.

| consumer | dòng | default | giá trị chạy | hậu quả |
|---|---|---|---|---|
| `calculate_risk_score.py` | :115 | `50` | 50 | 38% điểm rủi ro là hằng số — ✅ **Builder đã sửa** |
| `generate_incidents.py` | :169 | `100` | 100 | **Quy tắc 5 chết hẳn** |
| `collect_timeline_events.py` | :109-110 | `0` | 0 | **Phát hiện thay đổi WAAP chết hẳn** |
| `run_intelligence_pipeline.py` | :170 | `0` | 0 | log vận hành in `WAAP Score: 0` |
| `telegramBot.js` + `web/app.js` ×5 | — | — | 60 | công thức khác, tệp nguồn khác (AQ-016) |

Chi tiết hai cái chết hẳn:

`generate_incidents.py:169-171`

    waap_score = waap.get('score', 100)
    if weak_ciphers > 0 and waap_score < 60:

`100 < 60` luôn False → quy tắc "Weak Cipher + WAAP thấp" **không thể kích hoạt**,
bất kể crypto tệ đến đâu.

`collect_timeline_events.py:109-113`

    current_score  = current.get('score', 0)
    previous_score = previous.get('score', 0)
    if previous_score and current_score != previous_score:

`previous_score = 0` là falsy → nhánh **không bao giờ chạy**. WAAP rơi từ 80 xuống
10 không sinh sự kiện timeline nào, mãi mãi.

`logs/pipeline_results.json` → `summary.waap_score: 0` (sự thật: 80).

**Suggested Sprint:** SPRINT PIPELINE-FIELD-AUDIT (ưu tiên 2) — bộ audit trường cho
**toàn bộ pipeline Python**, cùng hình dạng với hai bộ JS đã có: mọi
`<state>.get('key'...)` đối chiếu với schema thật của tệp được load, chạy trong
`sprint_gate.py`, MISSING = blocker. Bộ này sẽ bắt cả 4 chỗ còn lại trong một lần
chạy. Sửa tay từng chỗ khi Auditor chỉ đích danh là cách làm đã chứng minh không
scale: 1/5 trong vòng này.

---

## AQ-015 · [MỚI] · Ưu tiên 1 — Truth Gap

**Issue:**
Hai mục nguyên vẹn của Daily Brief — `service_summary` và `crypto_summary` — có
**100% số liệu là giá trị mặc định**. Không một trường nào trong mười trường đó từng
được đọc thành công.

**Severity:** CRITICAL

**Root Cause:**
`generate_daily_brief.py` đọc tên trường của một lược đồ cũ. Không trường nào tồn
tại trong tệp state tương ứng, và mọi `.get(key, 0)` / `.get(key, {})` trả về default.
Brief in ra mười con số 0 với định dạng hệt như số đã đo.

**Evidence:**

`generate_daily_brief.py:148-149` đọc từ `services.json`
(khoá thật: `services, timestamp, total_services`):

    'total_services': services_data.get('service_count', 0)        <- KHÔNG TỒN TẠI
    'service_types' : len(services_data.get('service_inventory', {}))  <- KHÔNG TỒN TẠI

`generate_daily_brief.py:188-191` đọc từ `crypto_inventory.json`
(khoá thật: `findings, score, severity_breakdown, timestamp, total_findings`):

    'health_score'      : crypto_data.get('health_score', 0)        <- KHÔNG TỒN TẠI
    'certificate_count' : crypto_data.get('certificate_count', 0)   <- KHÔNG TỒN TẠI
    'cipher_suite_count': crypto_data.get('cipher_suite_count', 0)  <- KHÔNG TỒN TẠI
    'weak_cipher_count' : crypto_data.get('weak_cipher_count', 0)   <- KHÔNG TỒN TẠI

Đối chiếu `daily_brief/2026-09-14.json` với `state/`:

    BRIEF service_summary : {"total_services": 0, "service_types": 0, ...}
    STATE services.json   : total_services = 10, len(services) = 10

    BRIEF crypto_summary  : {"health_score": 0, "certificate_count": 0,
                             "cipher_suite_count": 0, "weak_cipher_count": 0, ...}
    STATE crypto_inventory: score = 100, total_findings = 19

`weak_cipher_count: 0` là default xanh giả điển hình: brief báo với người đọc rằng
**không có cipher yếu nào**, trong khi trường đó chưa từng được đọc. `health_score: 0`
sai theo hướng ngược lại — báo động giả trên một hệ thống đang 100.

Nghiêm trọng hơn vì AQ-007: Daily Brief HTML là **thứ duy nhất production thật sự
phục vụ** (`render.yaml` → `web-server.js` → `/latest`). Dashboard đầy đủ không được
deploy. Vậy nên hai mục hỏng hoàn toàn này chính là phần lớn những gì người dùng thấy.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (ưu tiên 1) — gộp với AQ-013.
`generate_daily_brief.py` phải dùng cùng kỷ luật `required()` mà Builder vừa áp cho
`calculate_risk_score.py`. Mục nào không đọc được trường bắt buộc thì **bỏ hẳn mục
đó khỏi brief** kèm một dòng nói vì sao — không in số 0.

---

## AQ-016 · [MỚI] · Ưu tiên 2 — Schema Drift / Source of Truth Drift

**Issue:**
Cụm từ "WAAP Score /100" hiện mang **năm giá trị khác nhau** trong cùng một hệ thống
tại cùng một thời điểm: **80, 100, 0, 0, 60**. Công thức cho ra 60 được sao chép
nguyên văn **sáu lần**.

**Severity:** HIGH

**Root Cause:**
Hai metric khác nhau cùng tên. `calculate_waap_score.py` chấm **6 thành phần**
(`ssl_status, ssl_expiry, http_status, https_status, dns_status, security_headers`)
từ `waap_score.json`. Portal và bot chấm **4 thứ khác hẳn** (`ssl_valid, waf_active,
cdn_active, protection_active`) từ `waap_status.json` — một tệp khác. Hai bên chỉ
chung đúng **một** đầu vào là `ssl_valid`.

Đây không phải hai trọng số khác nhau của cùng một phép đo. Đây là hai phép đo khác
nhau, cùng tên, cùng đơn vị `/100`, hiển thị cạnh nhau.

**Evidence:**

    state/waap_score.json   health_score = 80  grade = B  status = healthy
      component_scores: ssl_status 100, ssl_expiry 80, http_status 80,
                        https_status 100, dns_status 100, security_headers 25

    state/waap_status.json  security_summary = {ssl_valid: true, waf_active: false,
                                                cdn_active: false, protection_active: false}
      -> công thức 60/15/15/10 = 60

Sáu bản sao nguyên văn của công thức 60/15/15/10:

    web/app.js:216-221      web/app.js:306-311     web/app.js:960-964
    web/app.js:1104-1108    web/app.js:1233-1237
    scripts/telegram/telegramBot.js:15-21  (waapScoreFrom)

Hiện sáu bản còn giống hệt nhau. Sửa một bản là năm panel im lặng bất đồng.

**Suggested Sprint:** SPRINT ONE-WAAP — `calculate_waap_score.py` là nơi duy nhất
được phép chấm WAAP (cùng kỷ luật đã áp cho risk engine ở sprint hợp nhất
`calculate_risk_score.py`). Portal và bot đọc `health_score`, không tự tính. Nếu
`waf/cdn/protection` là chỉ số riêng thì đặt tên riêng — `protection_coverage` —
không dùng lại chữ "WAAP Score".

---

## AQ-017 · [MỚI] · Ưu tiên 1 — Default xanh giả

**Issue:**
Cổng merge không kiểm tuổi của bất kỳ đầu vào nào. `npm run gate` (không có
`--validate`) đọc `tool_validation.json` và `logs/pipeline_results.json` từ đĩa và
công bố "Đủ điều kiện merge: CÓ" dựa trên chúng, dù chúng cũ bao nhiêu.

**Severity:** HIGH

**Root Cause:**
`sprint_gate.py:87-88` đọc `tool_validation.json` / `sensor_coverage.json` từ đĩa khi
không có cờ `--validate`; dòng 99 đọc `logs/pipeline_results.json`. Không đường dẫn
nào có kiểm `generated_at` / `timestamp`. Không blocker nào liên quan tuổi dữ liệu.

Mỉa mai: `web/app.js:563-586` **đã có** đúng phép kiểm này (`tools_age_hours > 24` →
cảnh báo vàng). Portal biết dữ liệu validator có thể cũ; cổng merge thì không.

**Evidence:**

    sprint_gate.py:87   report   = _read_json(STATE_DIR/'tool_validation.json')
    sprint_gate.py:88   coverage = _read_json(STATE_DIR/'sensor_coverage.json')
    sprint_gate.py:99   pipeline = _read_json(PROJECT_ROOT/'logs/pipeline_results.json')
    grep 'age|stale|generated_at' scripts/sprint_gate.py -> không có kiểm tuổi nào

    web/app.js:568      const stale = toolsAgeH === null || toolsAgeH > 24;   <- portal CÓ

Hiện cả ba tệp đều mới (07:41 hôm nay) nên default này chưa che giấu gì. Nhưng
`npm run gate` là lệnh mặc định trong `package.json`, và nó có thể tuyên bố
merge-ready từ một lần validate của tuần trước mà không nói một lời.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (ưu tiên 1) — gộp với AQ-013/AQ-015.
Cổng phải in tuổi của từng đầu vào và **chặn** khi quá ngưỡng. Tái dùng đúng ngưỡng
24h mà portal đang dùng, để hai nơi không trả lời khác nhau cho cùng câu hỏi.

---

## AQ-018 · [MỚI] · Ưu tiên 1 — Truth Gap

**Issue:**
`protection_status: "unknown"` bị quy thành `protection_active: false`, rồi bị trừ
điểm như một kết quả đo được là "không có bảo vệ".

**Severity:** HIGH

**Root Cause:**
`collect_waap_snapshot.py` không phân giải được trạng thái bảo vệ và ghi `"unknown"`.
`security_summary` gập ba trạng thái (`true` / `false` / `unknown`) xuống hai giá trị
boolean. Mọi consumer sau đó — sáu bản sao ở AQ-016 cộng `web/app.js:762` và `:1178` —
đọc `false` và hiển thị `⚠️` / `✗`, không phân biệt được "đã đo, không có bảo vệ" với
"chưa đo được".

Đây là mặt trái của cùng một lỗi: AQ-015 là chưa-biết hiển thị thành xanh, còn đây là
chưa-biết hiển thị thành đỏ. Cả hai đều là chưa-biết bị ép thành một kết luận.

**Evidence:**

    state/waap_status.json
      protection_status : "unknown"          <- sự thật
      waf_enabled       : False
      cdn_enabled       : False
      security_summary  : {..., "protection_active": false}   <- unknown -> false

    web/app.js:762   ${...protection_active ? '✅' : '⚠️'}
    web/app.js:1178  const protActive = ...protection_active ? '✓' : '✗';
    telegramBot.js:20  + (summary.protection_active ? 10 : 0)

Hệ quả: 10 điểm bị trừ và hai chỉ dấu đỏ được hiển thị cho một thuộc tính mà hệ thống
tự khai là chưa đo được.

Chính repo này đã làm đúng chuyện đó ở chỗ khác: `sensor_coverage` phân biệt rạch ròi
`BLIND` (chưa nhìn) với `EMPTY` (đã nhìn, không có gì), và `TECHNICAL_DEBT.md` ghi rõ
*"đây là kết quả ĐÃ KIỂM, không phải rule im lặng"*. Kỷ luật đã có; nó chưa được áp
cho WAAP.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (ưu tiên 1) — `security_summary` giữ
trạng thái ba giá trị. `unknown` không được cộng hay trừ điểm: nó rời khỏi cả tử số
lẫn mẫu số (đúng kỷ luật `points_available` mà `asset_builder.py` đang dùng), và hiển
thị là `?` chứ không phải `✗`.

---

## TỔNG KẾT VÒNG 2

| | |
|---|---|
| CRITICAL mới | **3** (AQ-013, 014, 015) |
| HIGH mới | **3** (AQ-016, 017, 018) |
| Vòng 1 đã trả | 4 (AQ-001, 003, 008, 012) |
| Vòng 1 còn nguyên | 8 (AQ-002, 004, 005, 006, 007, 009, 010, 011) |
| **Tổng đang mở** | **14** (7 CRITICAL, 7 HIGH) |

### Điều vòng này chứng minh

Vòng 1 chỉ đích danh **một** chỗ hỏng vì `score` → `health_score`. Builder sửa đúng
một chỗ. Vòng 2 tìm ra **năm** chỗ — bốn cái còn lại vẫn đang chạy, một cái làm chết
hẳn một quy tắc phát hiện sự cố, một cái làm chết hẳn phát hiện thay đổi WAAP.

Đó là lập luận đầy đủ cho **ưu tiên 2 — Pipeline Field Audit**: sửa theo từng mục
Auditor chỉ ra không scale được, vì Auditor tìm bằng mắt còn lỗi thì nhân bản bằng
copy-paste.

Và AQ-013 là lý do **ưu tiên 1 — Kill Green Defaults** phải đi trước tất cả: default
xanh giả đã lọt vào bên trong chính cổng merge. Mọi kết luận "Đủ điều kiện merge: CÓ"
từ trước tới nay đều mang trong nó một phép kiểm pipeline không có khả năng thất bại.

### Về Executive Narrative

**Chưa làm, và chưa nên làm.** Hai vòng audit đã chỉ ra 14 chỗ mà số liệu "đúng field
nhưng sai sự thật": brief in `total_services: 0` khi có 10, in `weak_cipher_count: 0`
trên một trường chưa từng được đọc, cổng merge in "0 thất bại" từ một danh sách không
thể khác rỗng, và năm con số cùng tên "WAAP Score".

Một tầng narrative dựng trên nền này sẽ không kể sai — nó sẽ kể **trôi chảy và thuyết
phục** một điều sai. Đó là trạng thái tệ hơn hiện tại, vì hiện tại ít nhất các con số
còn trần trụi đủ để một Auditor bắt được.

Thứ tự đúng: **AQ-013 → AQ-014/AQ-015 → AQ-017/AQ-018 → AQ-016 → AQ-002 → AQ-004/005
→ AQ-006 → AQ-007 → AQ-009/010 → AQ-011 → rồi mới Narrative.**

---

*Vòng 2, CHIEF AUDITOR 2026-09-14. Read-only: không file production nào bị sửa, không
commit, không push, không merge. Lưu ý working tree đang có sửa đổi CHƯA COMMIT của
Builder (`asset_builder.py`, `calculate_risk_score.py`, `ioc_quality.py`) — mọi nhận
định về trạng thái vòng 1 ở trên đối chiếu với working tree đó, không phải với HEAD.*


---
---

# VÒNG 3 — 2026-09-14 · "TẠI SAO LÀ 10?"

Câu hỏi duy nhất của vòng này: hệ thống nói **Risk = 10**. Chứng minh được không?
Không hỏi "trường có tồn tại không". Chỉ hỏi "con số này có đúng không".

Đã đọc: `HANDOFF.md` · `TECHNICAL_DEBT.md` · `TOOL_VALIDATION_REPORT.md` · `IOC_QUALITY_REPORT.md`
Đã audit: `risk_score.json` · `executive_findings.json` · `incidents.json` · `daily_brief/*.json` · `web/app.js` · `web/server.js` · `telegramBot.js` · `alertDelivery.js` · `incidentAlerter.js`

Auditor READ ONLY. Không sửa file, không commit, không push, không merge.

---

## PHÉP TÍNH: ĐÚNG. ĐẦU VÀO: KHÔNG.

Số học nội bộ của `risk_score.json` kiểm được và khớp:

    weighted_health = Σ(weight × health) = 89.58
    weight_available = 1.0
    overall = 100 − 89.58 / 1.0 = 10.42  →  10   ✅

Tổng trọng số = 1.0. Tổng `risk_contribution` = 10.42. Không có lỗi số học.

Nhưng "Risk = 10" không phải một phép tính — nó là một **tuyên bố về hệ thống này**.
Truy ngược từng đầu vào của tám thành phần cho kết quả:

| Thành phần | w | health | điểm rủi ro | đầu vào có đúng không |
|---|---|---|---|---|
| `threat_hunting` | 0.25 | 76 | **6.00** | ❌ **AQ-019** — 2 chỉ báo dán nhãn sai |
| `waap` | 0.10 | 80 | 2.00 | ✅ đúng (Builder vừa sửa) |
| `incidents` | 0.25 | 94 | 1.50 | ⚠️ thiếu — Quy tắc 5 chết (AQ-014) |
| `security_events` | 0.04 | 87 | 0.52 | ✅ đúng |
| `firewall` | 0.04 | 90 | 0.40 | ❌ **AQ-023** — hằng số |
| `asset` | 0.20 | 100 | 0.00 | ❌ **AQ-021** — quét cũ 157h, hai tổng mâu thuẫn |
| `crypto` | 0.06 | 100 | 0.00 | ❌ **AQ-020** — không thể khác 100 |
| `defender` | 0.06 | 100 | 0.00 | ✅ đúng |

**6.00 / 10.42 = 58% điểm rủi ro đến từ hai bản ghi. Cả hai đều dán nhãn sai.**
**0.40 là hằng số. 0.00 của crypto là một hàm không thể trả về giá trị khác.**

Kết luận: **không chứng minh được "Risk = 10"** → CRITICAL, theo đúng tiêu chí đề ra.

---

## AQ-019 · Fake Severity · Số liệu sai

**Issue:**
58% điểm rủi ro toàn hệ thống đến từ **hai** sự kiện Windows 4648, và cả hai là việc
Windows đăng nhập người dùng vào chính tài khoản Microsoft của họ trên `localhost`.
Chúng được dán nhãn `severity: HIGH`, `hunting_type: lateral_movement`, và được **miễn
trừ** khỏi bộ lọc tiếng ồn đúng vì chúng mang nhãn HIGH.

**Severity:** CRITICAL

**Root Cause:**
`ioc_quality.py:307`

    if indicator.get('severity') in ('CRITICAL', 'HIGH'):
        return None, None      # mức cao không bị lọc tự động

Severity được gán **trước**, một cách máy móc, từ Event ID (`severity_basis:
"Event ID 4648 — Explicit Credential Logon"`). Bộ lọc tiếng ồn chạy **sau**, và được
lệnh không đụng vào HIGH. Bản ghi cần soi lại nhất là bản ghi chắc chắn thoát.

Lập luận trong chú thích — *"kẻ tấn công dùng đúng những nhị phân mà lập trình viên
dùng"* — đúng cho `DEV_HINTS` (lọc theo tên tiến trình). Nhưng miễn trừ này cũng phủ
luôn `ROUTINE_HINTS`, trong đó có `s-1-5-18` — **tài khoản SYSTEM**, không phải một
heuristic tên tiến trình. Nếu hai bản ghi này là INFO, `s-1-5-18` trong evidence sẽ
khiến chúng bị hạ xuống `ROUTINE_OS_ACTIVITY` như 208 bản ghi khác.

**Evidence:**

    state/hunting_lateral_movement.json — cả 2 chỉ báo severity HIGH:

    type            : "Explicit Credential Logon"
    severity        : HIGH
    severity_basis  : "Event ID 4648 — Explicit Credential Logon"
    suppressed      : false
    noise_class     : null
    evidence[0]     : "...Security ID:  S-1-5-18
                       Account Name:   KEVIN$
                       Account Domain: WORKGROUP
                       Account Whose Credentials Were Used:
                         Account Name:   tamngankevin@gmail.com
                         Account Domain: MicrosoftAccount
                       Target Server Name: localhost
                       Process Name:   C:\Windows\System32\lsass.exe"   (bản 2: svchost.exe)
    attribution.scope  : ["LOCAL_HOST"]
    attribution.reason : "Đăng nhập cục bộ: không có máy thứ hai trong sự kiện"

`S-1-5-18` có mặt trong `ROUTINE_HINTS` (`ioc_quality.py:288`). `Target Server Name:
localhost`. Và chính bản ghi tự khai **"không có máy thứ hai trong sự kiện"** — trong
khi loại của nó là *lateral movement*, tức là chuyển động **giữa** các máy.

Phép tính chịu ảnh hưởng:

    HUNTING_PENALTY['hunting_lateral_movement.json']['HIGH'] = 12
    threat_hunting health = 100 − 2 × 12 = 76
    risk_contribution     = 0.25 × (100 − 76) = 6.00

    Nếu 2 bản ghi này được lọc đúng như 208 bản ghi cùng loại:
    threat_hunting health = 100  →  contribution = 0.00
    overall = 10.42 − 6.00 = 4.42  →  Risk = 4

**Business Impact:**
Điểm rủi ro của toàn bộ hệ thống bị thổi lên **gấp 2.4 lần** (10 thay vì 4) bởi việc
chủ máy đăng nhập vào tài khoản Microsoft của chính mình. Cùng hai bản ghi này cũng
sinh ra `EF-0001`/`EF-0002` — hai phát hiện cấp điều hành mức HIGH mang tiêu đề
*"Dò quét di chuyển ngang nhắm vào 192.168.0.51"*, trong đó `192.168.0.51` **chính là
máy đang chạy hệ thống**. Chúng cũng là "0C/2H" trong `HANDOFF.md` và `high_count: 3`
trong `risk_score.json`.

Hệ quả vận hành: mỗi lần chủ máy đăng nhập Windows, điểm rủi ro tăng. Một analyst đi
theo `recommended_action` của EF sẽ *"Chặn SMB/WinRM/RDP"* và *"Reset mật khẩu các tài
khoản bị dò"* để đối phó với việc chính mình đăng nhập. Đây là dạng cảnh báo giả tốn
kém nhất: nó có bằng chứng thật, có điểm tin cậy 90 chính đáng, và vẫn hoàn toàn sai
về ý nghĩa.

**Suggested Sprint:** SPRINT SEVERITY-AFTER-NOISE —
(1) Bỏ miễn trừ ở `ioc_quality.py:307` **đối với `ROUTINE_HINTS`**; giữ miễn trừ cho
`DEV_HINTS` (lập luận ở đó đúng). `s-1-5-18` / logon type 5 là hoạt động nền của HĐH
bất kể severity.
(2) `lateral_movement` không được kết luận khi `attribution.scope == ['LOCAL_HOST']`
và `Target Server Name` là `localhost` — đó là định nghĩa của *không* lateral.
(3) Thứ tự đúng: gán severity **sau** phân loại tiếng ồn, không phải trước.
(4) Gate: một chỉ báo `suppressed=false` mà evidence khớp `ROUTINE_HINTS` phải là
blocker cho tới khi có lý do ghi rõ.

---

## AQ-020 · Green Default · Số liệu sai

**Issue:**
`crypto_score` **không thể nhận giá trị nào khác 100**. Hàm chấm điểm đếm severity
bằng khoá chuỗi trên một dict được ghi bằng khoá số nguyên, nên mọi bộ đếm luôn là 0.

**Severity:** CRITICAL

**Root Cause:**
`collect_crypto_inventory.py:121` lấy `severity` từ Nessus — một **số nguyên** 0–4.
Dòng 137 ghi `severity_counts[severity] += 1`, tức khoá là `0`, `2`, ...
Dòng 147-149 đọc lại bằng **chuỗi**: `severity_counts.get('CRITICAL', 0)`,
`.get('HIGH', 0)`, `.get('MEDIUM', 0)` → luôn `0`.
Dòng 152-156: `crypto_score = 100 − 0 − 0 − 0 = 100`, mãi mãi.

Drift số nguyên ↔ chuỗi trong cùng một hàm, giữa chỗ ghi và chỗ đọc.

**Evidence:**

    state/crypto_inventory.json
      n_findings          = 19
      severity values     = Counter({0: 17, 2: 2})     <- CÓ 2 finding MEDIUM
      severity_breakdown  = {CRITICAL:0, HIGH:0, MEDIUM:0, LOW:0, INFO:0}
      SUM(severity_breakdown) = 0        <- trên 19 finding
      score               = 100

Điểm đúng phải là `100 − 2 × 5 = 90`.
Và `severity_breakdown` công bố tổng **0** cạnh `total_findings: 19` trong cùng object.

Hệ quả trong `risk_score.json`: `crypto health=100, weight 0.06, contribution 0.00`.
Kể cả 50 finding CRITICAL về mã hoá, con số này vẫn là 100 và vẫn đóng góp 0.

Thêm một lớp nữa: finding đầu tiên là
`"Target Credential Status by Authentication Protocol - No Credentials Provided"` —
bản quét Nessus **không có credential**. Một bảng kiểm kê mã hoá dựng từ quét không
xác thực, báo sức khoẻ 100, thực chất đang nói *"không nhìn được, nên hoàn hảo"*.

**Business Impact:**
6% trọng số rủi ro bị khoá cứng ở "hoàn hảo". Hệ thống không có khả năng phát hiện
bất kỳ vấn đề mã hoá nào — cipher yếu, chứng chỉ hết hạn, TLS cũ — và vẫn in ra
`crypto inventory score 100` như một kết luận đã đo. `generate_incidents.py` Quy tắc 5
(*"Weak Cipher + WAAP thấp"*) đọc `severity_breakdown['CRITICAL']` — luôn 0 — nên quy
tắc đó chết theo, cộng dồn với default `100` ở AQ-014.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS — ánh xạ số nguyên Nessus → tên
severity ở đúng một chỗ, dùng chung cho `collect_crypto_inventory.py`,
`collect_nessus_snapshot.py`, `extract_asset_intelligence.py`. Thêm bất biến:
`sum(severity_breakdown.values()) == total_findings`, sai là blocker. Và một quét
không có credential phải hạ `crypto` xuống UNKNOWN, không phải 100.

---

## AQ-021 · Nguồn sự thật trùng lặp · Truth Gap

**Issue:**
Hai tệp state báo hai tổng lỗ hổng khác nhau cho **cùng một bản quét**: **399** và
**64**. Daily Brief in cả hai trên **cùng một trang** và tự mâu thuẫn. Bản quét đó đã
**157 giờ tuổi** và thành phần `asset` (20% trọng số) vẫn chấm nó 100/100.

**Severity:** CRITICAL

**Root Cause:**
`extract_asset_intelligence.py` và `collect_nessus_snapshot.py` cùng đọc Nessus nhưng
tổng hợp theo hai phạm vi khác nhau, ghi vào hai tệp, và không tầng nào đối chiếu.
`calculate_risk_score.py:analyze_assets` đọc `assets.json` mà **không kiểm tuổi** —
`scan_age_hours: 157.3` không xuất hiện ở bất kỳ đâu trong `risk_score.json`.

**Evidence:**

    state/assets.json        (cộng dồn 11 máy)
      vulnerability_count tổng = 399
      critical 0 · high 0 · medium 4 · low 9 · info 386

    state/nessus_status.json (cùng scan "Home Network Discovery")
      total 64
      critical 0 · high 0 · medium 3 · low 2 · info 59
      last_scan       = 2026-09-07T18:35:32
      scan_age_hours  = 157.3
      scanner_status  = "running"

    daily_brief/2026-09-14.json — MỘT tài liệu, HAI con số:
      vulnerability_summary.total_findings                     = 64
      asset_summary.top_vulnerable_devices[0].vulnerability_count = 215   (192.168.0.51)

Một thiết bị đơn lẻ mang 215 lỗ hổng trong khi tổng của cả bản quét là 64. Chênh
**3.4 lần**, trong cùng một tài liệu điều hành, không có ghi chú nào.

    state/risk_score.json
      {"name":"asset","health":100,"weight":0.2,"risk_contribution":0.0,
       "detail":"0 lỗ hổng CRITICAL, 0 HIGH trên 11 tài sản"}

Câu "0 lỗ hổng CRITICAL, 0 HIGH" là một phát biểu về **ngày 7/9**, trình bày như trạng
thái hôm nay. 20% trọng số rủi ro đang dựa trên dữ liệu gần 7 ngày tuổi, từ một scanner
mà chính state khai là `"running"` (tức bản quét có thể chưa xong).

**Business Impact:**
Thành phần trọng số lớn thứ hai (0.20) đóng góp **0.00 điểm rủi ro** dựa trên một bản
quét tuần trước. Một lỗ hổng CRITICAL xuất hiện hôm nay sẽ không chạm tới điểm rủi ro
cho tới lần quét kế tiếp — và không có gì trong hệ thống nói cho người đọc biết điều
đó. Đồng thời bất kỳ ai đối chiếu hai mục của Daily Brief đều mất niềm tin vào cả hai:
khi một tài liệu tự mâu thuẫn 3.4 lần, người đọc không có cách nào biết mục nào đúng.

**Suggested Sprint:** SPRINT ONE-VULN-TOTAL — một nơi duy nhất tổng hợp Nessus; hai
tệp còn lại đọc từ đó. Bất biến: `sum(assets[].vulnerability_count) == nessus_status.total`,
lệch là blocker. Thành phần `asset` phải mang `scan_age_hours` vào `detail` và hạ
xuống UNKNOWN khi quá ngưỡng (đề xuất 48h) thay vì chấm 100.

---

## AQ-022 · Schema Drift · Truth Gap

**Issue:**
`HANDOFF.md` — tài liệu mà quy trình audit đọc đầu tiên mỗi phiên — mở đầu bằng
*"mọi con số dưới đây đọc thẳng từ `state/` lúc chạy"*. Dòng ngay bên dưới công bố
**602 chỉ báo**. Giá trị thật lúc chạy là **577**. `TECHNICAL_DEBT.md`, sinh cùng giây,
in **577**.

**Severity:** HIGH

**Root Cause:**
`generate_handoff.py:115` đọc `validation.get('detection_integrity')` — tức từ
**`state/tool_validation.json` đã cache**, ghi lúc 07:38:17.
`sprint_gate.py` gọi `detection_quality.audit_state()` **trực tiếp** → 577.

Hai tài liệu, cùng một chỉ số, hai nguồn khác nhau, cùng một dấu thời gian
`Cập nhật: 2026-09-14T07:54:38`.

**Evidence:**

    docs/project/HANDOFF.md:25        | Toàn vẹn bằng chứng | 0 vi phạm / 602 chỉ báo |
    docs/project/TECHNICAL_DEBT.md:17 | Toàn vẹn bằng chứng | 0 vi phạm / 577 chỉ báo |
    docs/project/IOC_QUALITY_REPORT.md| Tổng chỉ báo: 577
    mtime cả hai tệp                  : 07:55:09

    Đếm trực tiếp state/ lúc audit:
      credential 0 + lateral 436 + persistence 96 + processes 45 = 577
    detection_quality.audit_state() chạy live -> total_indicators = 577

Không chỉ một dòng: `PASS 94 / EMPTY 5 / BLIND 0 / FAIL 0` trong `HANDOFF.md` cũng đến
từ cùng cache 07:38 đó. Toàn bộ bảng "Cổng merge" của HANDOFF là ảnh chụp **16 phút
trước**, dán nhãn "lúc chạy".

Thêm: `generate_handoff.py:112` lặp lại nguyên văn khiếm khuyết AQ-013 —
`[s for s in stages if not s.get('success', True)]` trong khi bộ ghi dùng khoá
`status`. Dòng **"Pipeline | 27 stage, 0 thất bại"** là giả ở **cả hai** tài liệu.

**Business Impact:**
Tài liệu onboarding chính thức chứa số liệu cũ dưới một lời cam kết là số liệu tươi.
Vòng 1 của chính cuộc audit này đã bị chệch vì `SESSION_STATE.md` cũ; `HANDOFF.md` được
sinh ra để chấm dứt chuyện đó và đang tái lập nó ở quy mô nhỏ hơn nhưng khó thấy hơn —
vì lần này con số *gần đúng*, và nó tự nhận là đọc trực tiếp.

**Suggested Sprint:** SPRINT HANDOFF-LIVE — `generate_handoff.py` gọi cùng hàm
`collect()` mà `sprint_gate.py` dùng, hoặc in kèm tuổi của `tool_validation.json` bên
cạnh mỗi con số lấy từ đó. Bất biến CI: hai tài liệu sinh trong cùng một lần chạy
không được lệch nhau ở bất kỳ chỉ số chung nào.

---

## AQ-023 · Fake Confidence · Green Default

**Issue:**
Thành phần `firewall` trả về **hằng số 90** khi tường lửa bật. Nó không đọc ba profile,
không đọc `blocked_connections`. 0.40 điểm rủi ro là một hằng số đeo nhãn số đo.

**Severity:** HIGH

**Root Cause:**
`calculate_risk_score.py:159-163`

    def analyze_firewall(self):
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled'):
            return 20, 'Firewall đang TẮT', {}
        return 90, 'Firewall bật', {}

Hàm này chỉ có hai đầu ra: 20 hoặc 90. Nó bỏ qua toàn bộ dữ liệu đã thu được.

**Evidence:**

    state/firewall_status.json (07:53:43)
      enabled          : true
      domain_profile   : true
      private_profile  : true
      public_profile   : true      <- cả ba profile BẬT
      blocked_connections : 42
      status           : "ACTIVE"

    state/risk_score.json
      {"name":"firewall","health":90,"weight":0.04,"risk_contribution":0.4,
       "detail":"Firewall bật"}

Một máy có đủ ba profile bật vẫn bị trừ 10 điểm sức khoẻ. Ngược lại, nếu
`public_profile` tắt — cấu hình nguy hiểm nhất trong ba — điểm vẫn đúng 90, vì hàm
không bao giờ đọc trường đó. Hệ thống **thu thập** dữ liệu profile và
`blocked_connections`, ghi vào state, rồi vứt đi khi chấm điểm.

**Business Impact:**
Cùng bệnh với AQ-003 (`waap.get('score', 50)`) nhưng do thiết kế chứ không do drift:
một hằng số được trình bày như kết quả đo. Sự khác biệt quan trọng — AQ-003 đã có thể
phát hiện bằng audit trường, cái này thì không: không có trường nào bị đọc sai, đơn
giản là **không có trường nào được đọc**. Đây là lớp lỗi mà `pipeline_field_audit.py`
mới không bắt được, và là lý do phải có thêm một phép kiểm khác: *thành phần này có
thay đổi khi đầu vào thay đổi không?*

**Suggested Sprint:** SPRINT MEASURED-NOT-DECLARED — `analyze_firewall` chấm theo
profile và `blocked_connections`. Và một phép kiểm mới trong `sprint_gate.py`: với mỗi
thành phần rủi ro, đảo đầu vào trong bộ nhớ và khẳng định điểm đổi. Thành phần có điểm
bất biến trước mọi đầu vào là hằng số, không phải số đo, và phải bị gắn cờ.

---

## AQ-024 · Fake Severity · Portal Truth

**Issue:**
Portal in `threats-total` = **577** trong khi số thật sau lọc tiếng ồn là **369**. Và
một chỉ báo thiếu trường `severity` được portal hiển thị là **MEDIUM** — một mức
nghiêm trọng do portal bịa ra, không có trong dữ liệu.

**Severity:** HIGH

**Root Cause:**
`web/app.js:1607` gộp bốn mảng `indicators` không lọc `suppressed` (grep `suppressed`
trong `web/app.js` → 0 kết quả). `web/app.js:1630-1631` dùng `|| 'medium'` / `|| 'MEDIUM'`
làm giá trị thay thế khi trường vắng mặt.

Đây là mục AQ-010 của vòng 1, chưa trả, cộng thêm một lớp mới: default không chỉ làm
sai **số đếm**, nó còn chế ra một **phán quyết**.

**Evidence:**

    web/app.js:1613  'threats-total': allIndicators.length            -> 577
    state/ thật     : 577 tổng, 208 suppressed  ->  369 là con số trung thực
    IOC_QUALITY_REPORT.md khai đúng: "Tổng 577 | Còn lại sau lọc 369 | Hạ xuống tiếng ồn 208"

    web/app.js:1630  <span class="badge badge-${ind?.severity?.toLowerCase() || 'medium'}">
    web/app.js:1631  ${ind?.severity || 'MEDIUM'}

    web/app.js:1628  indicators.slice(0, 10)    <- vẫn không sort theo severity

Portal và `IOC_QUALITY_REPORT.md` đọc **cùng một tệp state** và công bố hai con số khác
nhau cho cùng câu hỏi "có bao nhiêu chỉ báo". Báo cáo nói đúng; màn hình thì không.

**Business Impact:**
Người dùng nhìn portal mỗi ngày thấy 577 mối đe doạ, gần 36% trong đó chính hệ thống
đã kết luận là tiếng ồn nền của Windows. Tệ hơn, bốn danh sách top-10 vẫn lấy 10 phần
tử đầu của mảng **chưa sắp xếp** — trong 436 chỉ báo lateral có đúng 2 mức HIGH
(chính là hai bản ghi sai ở AQ-019), nên panel gần như chắc chắn hiển thị mười dòng
INFO. Con số thì phóng đại, danh sách thì rỗng nghĩa: hai lỗi ngược chiều trên cùng
một panel.

**Suggested Sprint:** SPRINT PORTAL-SIGNAL (đã đề xuất ở AQ-010, chưa làm) — lọc
`suppressed`, sort theo severity trước khi `.slice(0,10)`, hiển thị `369 (+208 tiếng ồn)`.
Bỏ `|| 'MEDIUM'`: chỉ báo thiếu severity hiển thị `?`, không phải một mức bịa ra.

---

## TRẠNG THÁI CÁC VÒNG TRƯỚC

| Mục | Trạng thái |
|---|---|
| AQ-001, 003, 008, 012 | ✅ đã trả (vòng 1) |
| AQ-006 | ✅ **đã trả** — `/analytics` và `/evidence` không còn bịa; chú thích giải thích lý do đã thay chỗ đoạn mã cũ |
| AQ-014 | 🔶 một phần — `scripts/pipeline_field_audit.py` đã có (chưa track); `TECHNICAL_DEBT.md` in "Số liệu giả trong pipeline Python: 0" |
| AQ-002, 004, 005, 007, 009, 010, 011, 013, 015, 016, 017, 018 | ❌ còn nguyên |

⚠️ Lưu ý về AQ-014: `TECHNICAL_DEBT.md` công bố **"Số liệu giả trong pipeline Python | 0"**.
Vòng này tìm thấy bốn số liệu giả trong pipeline Python: AQ-019 (miễn trừ lọc tiếng ồn),
AQ-020 (khoá int/str), AQ-021 (không kiểm tuổi quét), AQ-023 (hằng số 90). Bộ audit mới
kiểm *tên trường có tồn tại không* — nó không kiểm *giá trị có đúng không*, mà đó là
đúng ranh giới vòng này được giao. Con số 0 ấy đang đúng trong phạm vi của nó và **sai
trong phạm vi mà tên gọi của nó gợi ra**.

---

# TOP 3 CRITICAL ISSUES

### 1. AQ-019 — Risk = 10 vì chủ máy đăng nhập vào máy của chính mình
58% điểm rủi ro (6.00/10.42) đến từ hai sự kiện 4648 `Target Server Name: localhost`,
tài khoản `tamngankevin@gmail.com`, tiến trình `lsass.exe`/`svchost.exe`. Chính bản ghi
tự khai *"không có máy thứ hai trong sự kiện"* — trong khi loại của nó là *lateral
movement*. Chúng thoát bộ lọc tiếng ồn **đúng vì** mang nhãn HIGH
(`ioc_quality.py:307`). Lọc đúng → **Risk = 4, không phải 10**.

### 2. AQ-020 — `crypto_score` là hằng số 100, không phải số đo
Khoá `severity_counts` ghi bằng int Nessus (0,2), đọc bằng chuỗi (`'MEDIUM'`).
19 finding, `severity_breakdown` tổng **0**, 2 finding MEDIUM vô hình. Hàm chấm điểm
**không thể trả về giá trị nào khác 100**. Và bản quét nguồn không có credential.

### 3. AQ-021 — 399 vs 64 lỗ hổng, và Daily Brief tự mâu thuẫn 3.4 lần
`assets.json` cộng ra 399; `nessus_status.json` nói 64. Daily Brief in `total_findings: 64`
cạnh một thiết bị đơn lẻ có `vulnerability_count: 215`. Bản quét **157 giờ tuổi**,
`scanner_status: "running"`, và thành phần `asset` (20% trọng số) vẫn chấm 100/100 mà
không nhắc tới tuổi.

---

# TOP 3 HIGH ISSUES

### 1. AQ-022 — `HANDOFF.md` in số cache dưới lời cam kết "đọc thẳng từ state/"
602 vs 577 thật, cùng dấu thời gian với `TECHNICAL_DEBT.md` in 577. Cả bảng "Cổng merge"
của HANDOFF là ảnh chụp 16 phút trước. Và nó lặp lại lỗi `s.get('success', True)` nên
dòng "0 thất bại" là giả ở cả hai tài liệu.

### 2. AQ-023 — Thành phần `firewall` là hằng số 90
Không đọc ba profile, không đọc `blocked_connections` — dù cả hai đã được thu thập và
ghi vào state. Chỉ có hai đầu ra: 20 hoặc 90. `pipeline_field_audit.py` không bắt được
lớp này vì **không trường nào bị đọc sai — đơn giản là không trường nào được đọc**.

### 3. AQ-024 — Portal in 577 mối đe doạ; sự thật là 369
Cùng tệp state, `IOC_QUALITY_REPORT.md` nói đúng (369 + 208 tiếng ồn), màn hình nói sai.
Kèm `|| 'MEDIUM'`: chỉ báo thiếu severity được portal **bịa** cho một mức nghiêm trọng.

---

## KẾT LUẬN VÒNG 3

Yêu cầu đặt ra: *nếu hệ thống nói Risk = 10 thì phải chứng minh được tại sao là 10.*

Chứng minh được **phép tính** (10.42 → 10, trọng số tổng 1.0, không sai số học).
**Không** chứng minh được **con số**: 58% của nó dựng trên hai bản ghi dán nhãn sai,
4% là hằng số, 6% đến từ một hàm không thể trả về giá trị khác, và 20% dựa trên dữ liệu
157 giờ tuổi không được khai báo là cũ.

**Risk = 10 là một con số có thật về một hệ thống không tồn tại.** Giá trị đúng, với
cùng công thức và cùng dữ liệu đã lọc đúng, là **4**.

Đây chính xác là điều đã dự báo ở cuối vòng 2 khi hoãn Executive Narrative: số liệu
"đúng field nhưng sai sự thật". Vòng 3 đo được mức lệch — **2.4 lần** — và định vị
được nó nằm ở hai bản ghi cụ thể trong một tệp cụ thể tại một dòng mã cụ thể.

Thứ tự đề xuất: **AQ-019 → AQ-020 → AQ-021 → AQ-013 → AQ-022 → AQ-023 → AQ-024 →**
phần còn lại của vòng 1–2 → **rồi mới Narrative.**

---

*Vòng 3, CHIEF AUDITOR 2026-09-14. Read-only: không file production nào bị sửa, không
commit, không push, không merge. Mọi con số đối chiếu với `state/` lúc 07:53–07:55 và
với working tree chưa commit của Builder.*

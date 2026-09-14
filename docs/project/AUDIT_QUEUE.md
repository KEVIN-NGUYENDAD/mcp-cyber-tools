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


---
---

# VÒNG 4 — 2026-09-14 · audit PR #42 "kill green defaults"

Đọc `HANDOFF.md` trước. HEAD: `e8ba09b` (PR #42 merged). Builder commit được audit:
`204bda0` — *"fix(truth): kill green defaults, audit the Python layer, make correlation consistent"* (Sprint A + B + C).

Auditor READ ONLY. Không code, không commit, không push, không merge.

---

## ĐÃ TRẢ TRONG PR #42 — kiểm chứng được

| Mục | Bằng chứng kiểm lại |
|---|---|
| AQ-003 | `required()` thay `.get(k, default)`; thành phần không đo được rời khỏi cả tử lẫn mẫu; `UNMEASURED` khi không còn gì đo |
| AQ-005 | `correlation_engine.indicators()` nay lọc `suppressed`; `suppressed_excluded: {lateral: 128}` được ghi ra |
| AQ-006 | `/analytics` và `/evidence` không còn bịa |
| AQ-009 | `portal_escape_audit.py` → **86 biểu thức innerHTML / 86 an toàn / 0 chưa escape** |
| AQ-010 | `kept = list.filter(i => !i?.suppressed)`; `ranked` sort theo severity **trước** `.slice(0,10)`; `threats-total` in kèm số tiếng ồn |
| AQ-014 (một phần) | `generate_incidents.py:181` nay `waap.get('health_score', ...)` |
| AQ-004 | `EF-0001` xuống LOW; `confidence` khớp `ioc_quality.confidence`; evidence dedup 10/10 duy nhất |

Đây là công việc thật, kiểm được, và làm đúng hướng. Sáu trong tám mục còn nguyên ở
cuối vòng 3 đã đóng.

**Nhưng:** ba mục nghiêm trọng nhất vẫn nguyên, và vòng này tìm thấy ba mục mới —
trong đó có một mục nằm ngay trong công cụ mà PR #42 vừa xây để chống lại chính lớp
lỗi này.

---

## AQ-025 · Truth Gap · Schema Drift

**Issue:**
`pipeline_field_audit.py` — công cụ trung tâm của Sprint B — **không nhìn thấy 6 trong
9 tệp nó tự khai là đang quét**. Sáu tệp đó trả về **0 truy cập**. Cổng merge công bố
kết quả là `Số liệu giả trong pipeline Python | 0`.

**Severity:** CRITICAL

**Root Cause:**
`pipeline_field_audit.py:82`

    LOADERS = ('load_state', 'read_state_safe', 'read_json', '_read_json')

`generate_daily_brief.py:27` đặt tên hàm nạp state của nó là **`load_json`** — lệch
đúng một từ so với `read_json` trong danh sách. Bộ audit không phân giải được binding,
nên **toàn bộ** bề mặt đọc state của tệp đó vô hình — trong khi tệp vẫn nằm trong
`FILES`, trông như đã được phủ.

Không có cảnh báo nào khi một tệp trong danh sách trả về 0 truy cập. Im lặng đọc ra
"sạch".

**Evidence:**

    scripts/pipeline_field_audit.py -- kiểm đếm theo từng tệp:

      calculate_risk_score.py           8 truy cập
      generate_priority_queue.py        9 truy cập
      generate_incidents.py            17 truy cập
      correlation_engine.py             0 truy cập   <-- IM LẶNG HOÀN TOÀN
      daily_brief_generator.py          0 truy cập   <-- IM LẶNG HOÀN TOÀN
      generate_daily_brief.py           0 truy cập   <-- IM LẶNG HOÀN TOÀN
      calculate_waap_score.py           0 truy cập   <-- IM LẶNG HOÀN TOÀN
      asset_builder.py                  0 truy cập   <-- IM LẶNG HOÀN TOÀN
      ioc_quality.py                    0 truy cập   <-- IM LẶNG HOÀN TOÀN

      -> 3 / 9 tệp thật sự được audit

Sáu trường giả của **AQ-015** nằm trong `generate_daily_brief.py` — một tệp CÓ trong
danh sách và KHÔNG được đọc dòng nào:

    generate_daily_brief.py:148  services_data.get('service_count', 0)      <- không tồn tại
    generate_daily_brief.py:149  services_data.get('service_inventory', {}) <- không tồn tại
    generate_daily_brief.py:188  crypto_data.get('health_score', 0)         <- không tồn tại
    generate_daily_brief.py:189  crypto_data.get('certificate_count', 0)    <- không tồn tại
    generate_daily_brief.py:190  crypto_data.get('cipher_suite_count', 0)   <- không tồn tại
    generate_daily_brief.py:191  crypto_data.get('weak_cipher_count', 0)    <- không tồn tại

    daily_brief/2026-09-14.json vẫn in:
      service_summary = {"total_services": 0, ...}        state: 10 dịch vụ
      crypto_summary  = {"health_score": 0, "weak_cipher_count": 0, ...}   state: score 100

Công cụ **tự nói ra** giới hạn của mình, và nói rất trung thực:

    PHAM VI: lan duoc 34 / 230 loi goi `.get(key, default)` trong 9 tep.
             196 loi goi con lai doc state qua duong khac ... bo audit nay KHONG thay.

**14.8% độ phủ.** Nhưng `docs/project/TECHNICAL_DEBT.md:21` chỉ in:

    | Số liệu giả trong pipeline Python | 0 |

Không có mẫu số. Không có dòng phạm vi. Chính xác cùng một mẫu đã ghi ở AQ-SD-5 vòng 1:
**công cụ trung thực, tiêu đề không trung thực.**

**Suggested Sprint:** SPRINT AUDIT-THE-AUDIT —
(1) Tệp trong `FILES` trả về 0 truy cập phải là **cảnh báo**, không phải im lặng: *"đã
liệt kê nhưng không phân giải được binding nào"*.
(2) Phát hiện hàm nạp state theo cấu trúc (hàm nào mở tệp dưới `state/`) thay vì theo
danh sách tên cứng.
(3) `TECHNICAL_DEBT.md` phải in `0 / 34 kiểm / 230 lời gọi (14.8%)`, không in `0` trần.
Một con số 0 cạnh độ phủ 14.8% là một câu trả lời cho câu hỏi chưa ai hỏi.

---

## AQ-026 · Green Default · Truth Gap

**Issue:**
Sprint mang tên **"kill green defaults"** để nguyên default xanh nằm **trong chính cổng
merge**. `s.get('success', True)` vẫn còn ở cả hai nơi. Phép kiểm pipeline vẫn không có
khả năng thất bại.

**Severity:** CRITICAL

**Root Cause:**
Đây là AQ-013 của vòng 2, chưa trả. Bộ ghi (`run_intelligence_pipeline.py`) dùng khoá
`status`; hai bộ đọc dùng khoá `success` với mặc định `True`.

Sprint A đã áp đúng kỷ luật `required()` cho `calculate_risk_score.py` — nhưng chỉ cho
tệp đó. Cổng merge, nơi duy nhất trong repo mà một default xanh tuyệt đối không được
phép tồn tại, không nằm trong phạm vi sprint.

**Evidence:**

    scripts/sprint_gate.py:181      failed_stages = [s for s in stages if not s.get('success', True)]
    scripts/generate_handoff.py:112 failed        = [s for s in stages if not s.get('success', True)]

    logs/pipeline_results.json -> khoá mỗi stage: ['duration','name','output','status']
    -> 27/27 stage KHÔNG có khoá `success` -> toàn bộ mặc định ĐẠT

    docs/project/TECHNICAL_DEBT.md | Pipeline | 27 stage, 0 thất bại |
    docs/project/HANDOFF.md        | Pipeline | 27 stage, 0 thất bại |

Con số **0** in ở hai tài liệu là `len([])` trên một danh sách không thể khác rỗng.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (phần còn lại) — đọc đúng khoá
`status`; stage **thiếu** trường trạng thái là BLOCKER, không phải PASS. Quy tắc trong
`sprint_gate.py` và `generate_handoff.py`: cấm mọi mặc định mang nghĩa "đạt".

---

## AQ-027 · Correlation Integrity · Fake Severity

**Issue:**
Sprint C làm lớp tương quan **nhất quán nội bộ** mà không sửa đầu vào. Kết quả:
`EF-0002` — phát hiện dựng trên hai sự kiện đăng nhập cục bộ dán nhãn sai (AQ-019) —
nay **đáng tin hơn trước**: severity HIGH, confidence HIGH, `confidence_score 90`,
`ioc_quality.confidence` khớp, evidence dedup 10/10 duy nhất, 128 chỉ báo tiếng ồn đã
loại. Risk vẫn **10**.

**Severity:** CRITICAL

**Root Cause:**
AQ-019 chưa được chạm. `ioc_quality.py` vẫn miễn trừ mức HIGH khỏi bộ lọc tiếng ồn, nên
hai sự kiện 4648 `Target Server Name: localhost` vẫn `suppressed: false`, vẫn HIGH, vẫn
gánh 6.00 trong 10.42 điểm rủi ro.

Sprint C dọn sạch mọi tín hiệu cảnh báo **quanh** một kết luận sai: trước đây EF-0002
mang `confidence_score 49` cạnh nhãn HIGH, và mâu thuẫn đó chính là thứ tố cáo nó.
Mâu thuẫn đã được gỡ; kết luận sai thì ở lại.

**Evidence:**

    state/hunting_lateral_movement.json (sau PR #42)
      n = 356   by_severity = {INFO: 354, HIGH: 2}   suppressed = 128

      Cả 2 chỉ báo HIGH:
        type        : "Explicit Credential Logon"
        suppressed  : False        noise_class : None
        'S-1-5-18' trong evidence : True     <- có trong ROUTINE_HINTS
        'localhost' trong evidence: True
        attribution.scope         : ['LOCAL_HOST']

    state/executive_findings.json
      EF-0002  sev HIGH  conf HIGH  score 90  ioc_conf HIGH  evidence 10/10 duy nhất
               title: "Dò quét di chuyển ngang nhắm vào 192.168.0.51"

    state/risk_score.json
      threat_hunting  health 76  contribution 6.00   detail "lateral_movement: 0C/2H"
      overall_score   10

`192.168.0.51` là **chính máy đang chạy hệ thống**. Một phát hiện "di chuyển ngang"
nhắm vào máy cục bộ, dựng từ hai sự kiện mà `attribution.reason` của chúng ghi *"không
có máy thứ hai trong sự kiện"*.

So sánh hai vòng:

    Vòng 3: EF-0002 = HIGH nhưng confidence_score 49, ioc_conf LOW, 456 evidence lặp
            -> sai, và TRÔNG như sai
    Vòng 4: EF-0002 = HIGH, confidence_score 90, ioc_conf HIGH, 10 evidence sạch
            -> vẫn sai, và TRÔNG như đúng

**Suggested Sprint:** SPRINT SEVERITY-AFTER-NOISE (đã đề xuất ở AQ-019, chưa làm) — bỏ
miễn trừ `ROUTINE_HINTS` ở `ioc_quality.py:307`; `lateral_movement` không kết luận khi
`attribution.scope == ['LOCAL_HOST']`; gán severity **sau** phân loại tiếng ồn.
**Ưu tiên trên mọi việc dọn dẹp lớp tương quan tiếp theo** — mỗi vòng làm lớp trình bày
sạch hơn mà không sửa đầu vào là một vòng làm kết luận sai khó bị bắt hơn.

---

## AQ-028 · Truth Gap · Schema Drift

**Issue:**
`HANDOFF.md` — tệp mở đầu mỗi phiên audit — khai sprint vừa xong là `1c8a386`. HEAD
thật là `e8ba09b`. Nó chưa được sinh lại sau khi PR #42 merge, và vẫn in **602 chỉ báo**
trong khi giá trị thật là 356 + 96 + 45 + 0.

**Severity:** HIGH

**Root Cause:**
Hai nguyên nhân chồng lên nhau:

(1) `generate_handoff.py` không chạy tự động sau merge. Nó là lệnh thủ công
(`npm run handoff`), không phải một stage trong pipeline, và không có hook nào gọi nó.
(2) AQ-022 chưa trả: `generate_handoff.py:115` đọc `detection_integrity` từ
`state/tool_validation.json` đã cache thay vì gọi `detection_quality.audit_state()` live.

**Evidence:**

    docs/project/HANDOFF.md
      Cập nhật : 2026-09-14T07:54:38
      Commit   : 1c8a386
      Tiêu đề  : Merge pull request #41 ...

    git log -1 --format=%h  ->  e8ba09b   (Merge pull request #42)

    HANDOFF.md | Toàn vẹn bằng chứng | 0 vi phạm / 602 chỉ báo |
    Đếm state/ lúc audit: 0 + 356 + 96 + 45 = 497

Tệp mở đầu bằng lời cam kết **"mọi con số dưới đây đọc thẳng từ `state/` lúc chạy"**.
Bảng "Sprint vừa xong" đang mô tả sprint TRƯỚC sprint vừa xong; hàng "Toàn vẹn bằng
chứng" lệch 105 chỉ báo; và hàng Pipeline là giả theo AQ-026.

Hệ quả cho chính vòng lặp này: quy trình audit yêu cầu *"Đọc lại HANDOFF.md sau mỗi
thay đổi"*. Đọc nó sau PR #42 cho ra bức tranh của trước PR #42.

**Suggested Sprint:** SPRINT HANDOFF-LIVE — `generate_handoff.py` gọi cùng `collect()`
mà `sprint_gate.py` dùng (hết cache), và chạy như stage cuối của pipeline hoặc trong
hook post-merge. Bất biến CI: `HANDOFF.md` khai commit khác `git rev-parse HEAD` là
blocker.

---

## AQ-029 · Schema Drift · Green Default

**Issue:**
Hai trong bốn instance `waap.get('score', ...)` của AQ-014 vẫn nguyên, và cả hai tệp
chứa chúng **không nằm trong `FILES`** của bộ audit mới.

**Severity:** HIGH

**Root Cause:**
Sprint B sửa `generate_incidents.py` vì nó nằm trong danh sách quét. Hai tệp còn lại
không nằm trong danh sách, nên không ai nhìn thấy chúng — và danh sách đó là tay viết,
không suy ra từ pipeline.

**Evidence:**

    scripts/collect_timeline_events.py:109   current_score  = current.get('score', 0)
    scripts/collect_timeline_events.py:110   previous_score = previous.get('score', 0)
    scripts/collect_timeline_events.py:112   if previous_score and current_score != previous_score:

    -> previous_score = 0 (falsy) -> nhánh KHÔNG BAO GIỜ chạy.
       WAAP rơi từ 80 xuống 10 không sinh sự kiện timeline nào.

    scripts/run_intelligence_pipeline.py:170 waap_score_val = waap_score.get('score', 0)
    -> logs/pipeline_results.json  summary.waap_score = 0   (sự thật: 80)

    Cả hai tệp KHÔNG có trong pipeline_field_audit.FILES (9 tệp).

`collect_timeline_events.py` là một stage của pipeline; `run_intelligence_pipeline.py`
**là** pipeline. Danh sách quét bỏ sót chính bộ điều phối.

**Suggested Sprint:** SPRINT AUDIT-THE-AUDIT (gộp với AQ-025) — `FILES` phải suy ra từ
danh sách stage trong `run_intelligence_pipeline.py`, không viết tay. Mọi script được
pipeline gọi đều phải nằm trong phạm vi audit, cộng thêm chính bộ điều phối.

---

## AQ-030 · Deployment Truth

**Issue:**
Ba vòng audit, không một dòng nào của Deployment Truth được chạm. Portal được deploy
vẫn không phải portal được audit, `/latest` vẫn phục vụ bản ngày **13/09**, và bộ sinh
HTML cho nó **không nằm trong pipeline**.

**Severity:** HIGH

**Root Cause:**
`render.yaml` → `startCommand: node web-server.js`; `package.json` → `"start": "node web/server.js"`.
`web-server.js` chỉ phục vụ HTML daily brief.

Phần mới: bộ ghi HTML là `send_daily_brief_telegram.py:278-296` — **không** nằm trong
27 stage của pipeline. Nó được gọi từ `run_daily_brief.py`, một đường chạy riêng theo
lịch. Pipeline chạy đủ 27 stage và sinh ra `daily_brief/2026-09-14.json` **tươi**, trong
khi HTML mà production phục vụ dừng ở 13/09.

Đây là dạng lệch khó thấy nhất: **tệp JSON tươi che cho tệp HTML cũ.** Mọi bảng trạng
thái đọc JSON đều xanh; thứ người dùng mở thì cũ một ngày.

**Evidence:**

    render.yaml:9    startCommand: node web-server.js
    render.yaml:16   branch: develop
    package.json:7   "start": "node web/server.js"

    daily_brief/ :
      2026-09-12.html   (mtime 09-12)
      2026-09-13.html   (mtime 09-13)
      latest.html       (mtime 09-13, nội dung 2026-09-13)
      2026-09-14.json   (07:54 hôm nay)
      2026-09-14.html   -> KHÔNG TỒN TẠI

    Bộ ghi HTML: scripts/send_daily_brief_telegram.py:293  latest_html_path
    -> KHÔNG có trong 27 stage của run_intelligence_pipeline.py

Toàn bộ thành quả portal của PR #42 — `portal_escape_audit` 86/86, `riskView()` với
UNKNOWN, lọc `suppressed`, sort theo severity — nằm trong `web/app.js`, tệp mà Render
**không phục vụ**.

**Suggested Sprint:** SPRINT DEPLOY-TRUTH (đã đề xuất ở AQ-007 vòng 1, chưa làm) —
(1) Chốt một entrypoint; đồng bộ `render.yaml` với `package.json`; xoá ba server chết.
(2) Đưa bộ sinh brief HTML vào pipeline, hoặc đóng dấu tuổi lên chính trang.
(3) Quyết định dứt khoát: hoặc deploy `web/app.js` (và thu hoạch toàn bộ công của PR #42),
hoặc ngừng audit nó và chuyển `portal_field_audit` + `portal_escape_audit` sang bộ sinh
brief HTML — nơi người dùng thật sự đọc.

---

## TỒN ĐỌNG SAU VÒNG 4

| Mục | Hạng | Trạng thái |
|---|---|---|
| AQ-019 / AQ-027 | CRITICAL | ❌ Risk = 10 vẫn 58% từ 2 bản ghi localhost |
| AQ-020 | CRITICAL | ❌ `crypto_score` vẫn là hằng số 100 (khoá int/str) |
| AQ-021 | CRITICAL | ❌ 399 vs 64 lỗ hổng; brief tự mâu thuẫn 3.4 lần; quét 157h |
| AQ-013 / AQ-026 | CRITICAL | ❌ `s.get('success', True)` trong cổng merge |
| AQ-025 | CRITICAL | ❌ 6/9 tệp im lặng trong bộ audit mới |
| AQ-015 | CRITICAL | ❌ brief `service_summary` + `crypto_summary` vẫn 100% mặc định |
| AQ-002 | CRITICAL | ❌ attribution FULL trong khi hostname `unresolved` |
| AQ-007 / AQ-030 | HIGH | ❌ Deployment Truth, 3 vòng chưa chạm |
| AQ-011 / AQ-022 / AQ-028 | HIGH | ❌ HANDOFF cũ, cache, sai commit |
| AQ-016 | HIGH | ❌ 5 giá trị "WAAP Score"; 6 bản sao công thức |
| AQ-017 | HIGH | ❌ cổng merge không kiểm tuổi đầu vào |
| AQ-018 | HIGH | ❌ `protection_status: unknown` → `false` |
| AQ-023 | HIGH | ❌ `analyze_firewall` hằng số 90 |
| AQ-024 | HIGH | 🔶 số đếm đã sửa; `\|\| 'MEDIUM'` (app.js:1689) vẫn bịa severity |
| AQ-029 | HIGH | ❌ 2 instance `.get('score', 0)` ngoài phạm vi audit |

**Đang mở: 16 (7 CRITICAL, 9 HIGH). Đã trả tích luỹ: 11.**

---

## NHẬN ĐỊNH VÒNG 4

PR #42 là sprint tốt nhất từ đầu cuộc audit: bảy mục đóng, và đóng đúng cách. Lập luận
trong commit message — *"a wrong field at the display layer breaks one cell; a wrong
field at the compute layer breaks the number, and the number then travels ... showing
the same wrong value consistently, and therefore convincingly"* — là chẩn đoán chính xác
về bệnh của hệ thống này.

Nhưng ba quan sát phải nói thẳng:

**Một.** Công cụ được xây để chữa bệnh đó đang mắc đúng bệnh đó. `pipeline_field_audit.py`
liệt kê 9 tệp, đọc được 3, phủ 14.8% số lời gọi, và kết quả được công bố là `0`. Công cụ
tự in ra dòng phạm vi trung thực; `TECHNICAL_DEBT.md` bỏ dòng đó đi. **Số 0 trần bên
cạnh độ phủ 14.8% là một default xanh, sinh ra bởi sprint kill-green-defaults.**

**Hai.** Sprint C dọn sạch mọi tín hiệu mâu thuẫn quanh EF-0002 mà không chạm đầu vào.
Vòng 3, phát hiện đó sai **và trông như sai** (`confidence_score 49` cạnh nhãn HIGH).
Vòng 4, nó sai **và trông như đúng**. Dọn lớp trình bày trước khi sửa đầu vào không
trung lập — nó làm kết luận sai khó bị bắt hơn.

**Ba.** Toàn bộ công portal của PR #42 nằm trên một tệp Render không phục vụ, và trang
người dùng thật sự mở vẫn là bản 13/09 do một script ngoài pipeline sinh ra. Deployment
Truth đứng yên suốt ba vòng trong khi ba lớp bên trên nó liên tục được cải thiện.

**Đề xuất thứ tự cho vòng tới:** AQ-027/019 → AQ-026/013 → AQ-025 → AQ-020 → AQ-015 →
AQ-021 → AQ-030/007 → AQ-028.

AQ-027 đứng đầu vì nó là con số duy nhất người ngoài nhìn thấy (Risk = 10) và vì mỗi
sprint dọn dẹp tiếp theo sẽ làm nó thuyết phục hơn.
AQ-026 và AQ-025 đứng ngay sau vì cho tới khi hai mục đó đóng, **cổng merge và bộ audit
pipeline đều không có khả năng nói "không"** — và mọi kết luận "đủ điều kiện merge" từ
đây tới đó đều mang trong nó hai phép kiểm không thể thất bại.

---

*Vòng 4, CHIEF AUDITOR 2026-09-14. Read-only: không code, không commit, không push,
không merge. Đối chiếu với HEAD `e8ba09b` và `state/` lúc audit. Working tree có thay
đổi chưa commit của Builder.*


---
---

# VÒNG 5 — 2026-09-14 · PR #43 + working tree · LOOP MODE BẬT

HEAD: `4668b96` (PR #43 `telegram-truth-portal-hardening`). Audit cả PR #43 và các thay
đổi chưa commit trong working tree. Auditor READ ONLY.

---

## ĐÃ TRẢ — kiểm chứng được

| Mục | Bằng chứng |
|---|---|
| AQ-006 | `state/evidence_manifest.json`: SHA-256 thật, 349 hiện vật, `signature_status: NOT_IMPLEMENTED`, `integrity_scope` nói rõ "so với lần ĐẦU TIÊN hệ thống nhìn thấy". Logic TOFU đúng: tệp lần đầu tính `new`, KHÔNG tính `verified` |
| AQ-015 | `daily_brief` nay in `total_services: 10` (thật), `service_types: 3`, `top_services` có dữ liệu; `crypto_summary.health_score: 100` |
| AQ-025 | Phạm vi audit 9 tệp → **76 tệp**; 34 → **106** truy cập |
| AQ-029 | `collect_timeline_events.py` và `run_intelligence_pipeline.py` đã sửa và đã vào phạm vi audit |

---

## AQ-031 · Truth Gap · ƯU TIÊN CAO NHẤT VÒNG NÀY

**Issue:**
`Risk` tụt từ **10 → 3**, và `threat_hunting` từ 6.00 → **0.00**. Nhìn từ ngoài, đây
đúng là kết quả mà AQ-019 dự báo. **Nó không phải một bản sửa.** Không một dòng mã nào
liên quan thay đổi. Hai chỉ báo gây ra 58% điểm rủi ro chỉ đơn giản **không còn trong
cửa sổ log** của lần chạy này.

**Severity:** CRITICAL

**Root Cause:**
`ioc_quality.py:308` — miễn trừ mức HIGH khỏi bộ lọc tiếng ồn — **nguyên vẹn**:

    if indicator.get('severity') in ('CRITICAL', 'HIGH'):
        return None, None

`ROUTINE_HINTS` vẫn chứa `s-1-5-18` ở dòng 288 và vẫn không với tới được các bản ghi
HIGH. Cơ chế sinh ra dương tính giả còn nguyên; chỉ có dữ liệu đầu vào đổi.

**Evidence:**

    git diff HEAD -- scripts/ioc_quality.py scripts/hunt_lateral_movement.py
    -> RỖNG. Không tệp nào trong hai tệp này thay đổi.

    state/hunting_lateral_movement.json (08:06:22)
      n = 266     by_severity = {INFO: 266}     suppressed = 40
      Chỉ báo type == "Explicit Credential Logon" : 0        <- BIẾN MẤT, không phải bị lọc
      data_source : LIVE_OBSERVED      errors : []
      coverage    : {"observable": true, "status": "OBSERVED"}
      tools_used  : huntLateralMovement ok 217 bản ghi · huntRemoteDesktop ok 49 bản ghi

    state/risk_score.json
      threat_hunting  health 100  contribution 0.00
      overall_score   3

Cuộc săn chạy sạch, không lỗi, nguồn đọc được. Hai sự kiện 4648 chỉ là không xuất hiện
trong lần đọc này.

Diễn biến số chỉ báo lateral qua bốn lần chạy, **không có thay đổi mã nào giữa chúng**:

    436  ->  356  ->  266
    suppressed: 208 -> 128 -> 40

**Business Impact:**
Nếu AQ-019 được đóng dựa trên `Risk = 3`, nó sẽ được đóng trên một sự trùng hợp. Lần
tiếp theo Windows ghi một sự kiện 4648 `Explicit Credential Logon` — tức lần tiếp theo
chủ máy đăng nhập vào tài khoản Microsoft của mình — chỉ báo đó lại là HIGH, lại được
miễn trừ khỏi bộ lọc tiếng ồn, lại nhân với `HUNTING_PENALTY 12`, và Risk lại nhảy từ
3 lên ~9.

Nguy hiểm hơn: điểm rủi ro của hệ thống đang **dao động theo cửa sổ log chứ không theo
tư thế bảo mật**. Trong hai giờ, cùng một máy, không thay đổi cấu hình nào, Risk đã đi
10 → 3. Một chỉ số biến động 3.3 lần vì nhiễu thu thập thì không dùng được để ra quyết
định, và cũng không dùng được để đo tiến bộ giữa các sprint.

**Suggested Sprint:** SPRINT SEVERITY-AFTER-NOISE (AQ-019, vẫn chưa làm) —
(1) Bỏ miễn trừ `ROUTINE_HINTS` ở `ioc_quality.py:308`.
(2) `lateral_movement` không kết luận khi `attribution.scope == ['LOCAL_HOST']`.
(3) Thêm một bộ kiểm hồi quy **dùng dữ liệu cố định**: nạp một sự kiện 4648
`Target Server Name: localhost` + `S-1-5-18` và khẳng định nó bị `suppressed`. Chỉ có
fixture mới phân biệt được "đã sửa" với "hôm nay không gặp".
(4) **Không đóng AQ-019 dựa trên `Risk = 3`.**

---

## AQ-032 · Schema Drift · Fake Executive Claim

**Issue:**
AQ-020 chưa trả, và bản sửa AQ-015 vừa **mang mâu thuẫn đó lên trang điều hành**.
`crypto_summary` nay in `total_findings: 19` **nằm cạnh** `severity_breakdown` có tổng
bằng **0**, trong cùng một object.

**Severity:** CRITICAL

**Root Cause:**
`collect_crypto_inventory.py:137` ghi `severity_counts[severity] += 1` với `severity` là
**số nguyên** Nessus (0–4); dòng 147-149 đọc lại bằng khoá **chuỗi**
(`'CRITICAL'`/`'HIGH'`/`'MEDIUM'`) → luôn 0. `crypto_score = 100 − 0 − 0 − 0` không thể
khác 100.

Sprint sửa daily brief đã làm đúng việc của nó — đọc đúng trường thật thay vì mặc định.
Nhưng trường thật ấy vốn đã hỏng, nên bản sửa chuyển một con số 0 giả từ chỗ khuất ra
chỗ sáng nhất.

**Evidence:**

    state/crypto_inventory.json
      total_findings     = 19
      severity values    = Counter({0: 17, 2: 2})     <- CÓ 2 finding MEDIUM
      severity_breakdown = {CRITICAL:0, HIGH:0, MEDIUM:0, LOW:0, INFO:0}   tổng = 0
      score              = 100        (đúng phải là 100 − 2×5 = 90)

    daily_brief/2026-09-14.json  crypto_summary:
      {"health_score": 100, "total_findings": 19, "certificate_findings": 4,
       "weak_cipher_count": 0,
       "severity_breakdown": {"CRITICAL":0,"HIGH":0,"MEDIUM":0,"LOW":0,"INFO":0}}

`19` và `tổng 0` cách nhau hai trường trong cùng một dict. Người đọc có thể tự thấy mâu
thuẫn — đó là điểm cộng so với trước — nhưng con số được công bố vẫn sai.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (phần còn lại) — ánh xạ số nguyên
Nessus → tên severity ở một chỗ dùng chung. Bất biến:
`sum(severity_breakdown.values()) == total_findings`, lệch là blocker. Bất biến này bắt
được AQ-032 ngay, và cũng bắt được AQ-021.

---

## AQ-033 · Truth Gap · Schema Drift

**Issue:**
`HANDOFF.md` sai ở **ba** chỉ số cùng lúc, vòng thứ ba liên tiếp. Lần này nó công bố
`Risk Score 10/100` trong khi state ghi **3**.

**Severity:** HIGH

**Root Cause:**
AQ-022 + AQ-028 chưa trả, và nay lộ thêm một mặt: `generate_handoff.py` không chạy sau
merge và cũng không chạy sau khi pipeline sinh state mới. Nó là lệnh thủ công
(`npm run handoff`), không phải stage, không có hook.

**Evidence:**

    docs/project/HANDOFF.md  (Cập nhật: 2026-09-14T08:02:15)
      | Commit                | e8ba09b |          HEAD thật: 4668b96
      | Risk Score            | 10/100  |          state thật: 3
      | Toàn vẹn bằng chứng   | 602 chỉ báo |      đếm thật: 0+266+96+44 = 406
      | Pipeline              | 28 stage, 0 thất bại |  <- giả theo AQ-026

Bốn hàng, bốn sai. Tệp mở đầu bằng **"mọi con số dưới đây đọc thẳng từ `state/` lúc chạy"**.

Hệ quả trực tiếp cho vòng lặp audit này: quy trình yêu cầu *"Đọc lại HANDOFF.md sau mỗi
thay đổi"*. Ở vòng 4 nó khai `1c8a386` khi HEAD là `e8ba09b`; ở vòng 5 nó khai `e8ba09b`
khi HEAD là `4668b96`. Nó luôn trễ đúng một sprint — tức là ở chế độ LOOP, nó **không
bao giờ** mô tả trạng thái đang được audit.

**Suggested Sprint:** SPRINT HANDOFF-LIVE — `generate_handoff.py` thành stage cuối của
`run_intelligence_pipeline.py`, đọc live thay vì cache. Bất biến CI: `HANDOFF.md` khai
commit khác `git rev-parse HEAD` là blocker.

---

## AQ-034 · Truth Gap

**Issue:**
Bộ audit pipeline mở rộng từ 9 lên 76 tệp — nhưng độ phủ theo lời gọi vẫn là
**106 / 619 = 17.1%**. `TECHNICAL_DEBT.md` vẫn in `0` trần, không mẫu số.

**Severity:** HIGH

**Root Cause:**
AQ-025 mới trả một nửa: phạm vi tệp đã mở, nhưng 513 lời gọi vẫn đọc state qua đường bộ
audit không lần được (`self.state[...]`, tham số hàm, lớp bọc). Công cụ tự in dòng phạm
vi; tài liệu công bố bỏ nó đi.

**Evidence:**

    scripts/pipeline_field_audit.py
      TONG: 106 truy cap | 98 dung | 0 so lieu gia | 3 thieu khoa | 5 khong kiem duoc
      PHAM VI: lan duoc 106 / 619 loi goi trong 76 tep.
               513 loi goi con lai ... bo audit nay KHONG thay.

    docs/project/TECHNICAL_DEBT.md
      | Số liệu giả trong pipeline Python | 0 |

Bốn số liệu giả vòng 3–5 tìm được đều nằm ngoài 17% đó: AQ-020 (khoá int/str, không
phải `.get` thiếu khoá), AQ-021 (không kiểm tuổi), AQ-023 (hằng số 90), AQ-031 (miễn trừ
lọc tiếng ồn). Không lỗi nào thuộc dạng `.get(key, default)` — nên kể cả 100% độ phủ,
bộ audit này cũng không bắt được chúng.

**Suggested Sprint:** SPRINT AUDIT-THE-AUDIT (phần còn lại) —
(1) `TECHNICAL_DEBT.md` in `0 / 106 kiểm / 619 lời gọi (17.1%)`.
(2) Đổi tên hàng: nó đo *khoá thiếu có mặc định*, không đo *số liệu giả*. Tên hiện tại
hứa nhiều hơn phép đo.
(3) Thêm một phép kiểm khác hẳn cho lớp lỗi còn lại: với mỗi thành phần điểm, đảo đầu
vào và khẳng định điểm đổi (xem AQ-023). Hằng số và hàm chỉ-một-giá-trị chỉ lộ ra bằng
cách đó.

---

## TỒN ĐỌNG SAU VÒNG 5

| Mục | Hạng | Trạng thái |
|---|---|---|
| AQ-019 / AQ-031 | CRITICAL | ❌ cơ chế nguyên vẹn; Risk giảm do trùng hợp |
| AQ-020 / AQ-032 | CRITICAL | ❌ `crypto_score` hằng số 100; mâu thuẫn nay lên trang điều hành |
| AQ-021 | CRITICAL | ❌ 399 vs 64 lỗ hổng |
| AQ-013 / AQ-026 | CRITICAL | ❌ `s.get('success', True)` ở cả 2 nơi |
| AQ-002 | CRITICAL | ❌ attribution FULL vs hostname `unresolved` |
| AQ-007 / AQ-030 | HIGH | ❌ Deployment Truth, 4 vòng chưa chạm |
| AQ-022 / AQ-028 / AQ-033 | HIGH | ❌ HANDOFF trễ một sprint, 3 vòng liên tiếp |
| AQ-016 | HIGH | ❌ 5 giá trị "WAAP Score" |
| AQ-017 | HIGH | ❌ cổng merge không kiểm tuổi |
| AQ-018 | HIGH | ❌ `protection_status: unknown` → `false` |
| AQ-023 | HIGH | ❌ `analyze_firewall` hằng số 90 |
| AQ-024 | HIGH | 🔶 `\|\| 'MEDIUM'` vẫn bịa severity |
| AQ-025 / AQ-034 | HIGH | 🔶 phạm vi mở, độ phủ 17.1%, tiêu đề vẫn `0` trần |

**Đang mở: 13 (5 CRITICAL, 8 HIGH). Đã trả tích luỹ: 15.**

---

## NHẬN ĐỊNH VÒNG 5

Bốn mục đóng, đóng đúng. `evidence_manifest.py` đặc biệt tốt: TOFU đúng chiều (lần đầu
là `new`, không phải `verified`), `signature_status: NOT_IMPLEMENTED` viết thẳng, và
`integrity_scope` tự giới hạn phạm vi lời khẳng định. Đó là mẫu mực cho phần còn lại.

Nhưng phát hiện quan trọng nhất vòng này là một phát hiện **ngược**: con số tốt nhất
trong báo cáo — `Risk 10 → 3` — **không phải thành quả**. `git diff` trên hai tệp liên
quan rỗng. Hai chỉ báo gây ra 58% điểm rủi ro biến mất khỏi cửa sổ log, không bị lọc.

Điều đó đặt ra một câu hỏi lớn hơn AQ-019: **điểm rủi ro của hệ thống này đang dao động
theo nhiễu thu thập.** 436 → 356 → 266 chỉ báo trong ba lần chạy liên tiếp, không thay
đổi mã, không lỗi, `coverage: OBSERVED` cả ba lần. Risk 10 → 3 trong hai giờ trên một
máy không đổi cấu hình.

Ở chế độ LOOP, điều này đáng ngại gấp đôi: nếu mỗi vòng audit đọc một giá trị Risk khác
nhau vì lý do không liên quan tới sprint vừa chạy, thì **không thể dùng Risk để đo tiến
bộ**, và một mục CRITICAL có thể tự đóng rồi tự mở lại giữa hai vòng. Bộ kiểm hồi quy
bằng fixture (đề xuất ở AQ-031) là điều kiện cần trước khi đóng bất kỳ mục nào liên
quan tới điểm số.

**Thứ tự vòng tới:** AQ-031/019 (kèm fixture) → AQ-026/013 → AQ-032/020 → AQ-021 →
AQ-033 → AQ-030/007 → AQ-034.

---

*Vòng 5, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only: không code, không commit,
không push, không merge.*


---
---

# VÒNG 6 — 2026-09-14 08:13 · PR #44 `gate-integrity` + working tree

HEAD `ba86908`. Auditor READ ONLY.

---

## ĐÃ TRẢ — kiểm chứng được

| Mục | Bằng chứng |
|---|---|
| **AQ-013 / AQ-026** | `sprint_gate.py:239` đọc `status`; `status is None` → **BLOCKER** (`"thiếu dữ liệu là CHẶN, không phải đạt"`); `not stages` → BLOCKER. `generate_handoff.py:119` cũng đọc `status`. Đúng y đề xuất |
| **AQ-019 / AQ-031** | `ioc_quality.py:329-341` — `DEV_HINTS` vẫn miễn trừ HIGH (phỏng đoán theo tên), `ROUTINE_HINTS` nay áp ở **mọi mức** kèm lý do ghi rõ `"(mức %s do Event ID, nhưng chủ thể là tài khoản hệ thống)"`. Đây là phân biệt đúng, không phải nới lỏng |
| **AQ-023** | `analyze_firewall` chấm theo 3 profile; `enabled is None` → None chứ không đoán. Live: `health=100, "Firewall bật, 3/3 profile bật"` — hằng số 90 đã hết |
| **AQ-021** (một nửa) | `ASSET_SCAN_STALE_HOURS = 48`; live note: *"bản quét Nessus 158 giờ tuổi (ngưỡng 48): \"0 CRITICAL\" là phát biểu về lúc quét, không phải về hôm nay"* |

Bốn mục, bốn bản sửa đúng gốc. `sprint_gate.py` giờ **có khả năng nói không** — lần đầu tiên kể từ vòng 2.

---

## AQ-035 · Risk Consistency · Truth Gap

**Issue:**
`state/` không có ranh giới giữa các lần chạy pipeline. Ngay lúc audit,
`risk_score.json` công bố **Risk 31 / HIGH** với lý do `credential_dumping: 6C/0H`,
trong khi `hunting_credential_dumping.json` — chính tệp nó trích dẫn — chứa **0 chỉ
báo**. Hai tệp thuộc hai lần chạy khác nhau và không có gì nói ra điều đó.

**Severity:** CRITICAL

**Root Cause:**
Pipeline ghi thẳng vào `state/` theo từng stage, không có ảnh chụp nguyên tử và không
đóng dấu `run_id` lên tệp nào. Khi lần chạy N+1 bắt đầu trong lúc lần N vừa xong, các
tệp bị ghi đè **lệch pha**: hunt (stage sớm) đã là N+1, risk (stage muộn) vẫn là N.

Thứ tự stage trong `run_intelligence_pipeline.py` là đúng
(`hunt_credential_dumping` :430 → `ioc_quality` :444 → `generate_incidents` :472 →
`calculate_risk_score` :486 → `correlation_engine` :500). Vấn đề không phải thứ tự —
mà là **không có gì ngăn hai lần chạy chồng lên nhau**, và không có gì cho phép người
đọc phát hiện ra.

**Evidence:**

    Dấu thời gian trong state/ lúc audit:
      hunting_persistence.json          08:11:34
      hunting_suspicious_processes.json 08:11:37
      hunting_lateral_movement.json     08:11:39
      incidents.json                    08:11:47
      executive_findings.json           08:11:47
      risk_score.json                   08:11:54   <- lần chạy N
      hunting_credential_dumping.json   08:12:27   <- lần chạy N+1, MUỘN HƠN 33 GIÂY

    logs/pipeline_results.json : end_time 08:11:54, status success, 28 stage
    tasklist -> 2 tiến trình python đang chạy (lần N+1 đang bay)

    state/risk_score.json  (đang phục vụ mọi consumer)
      overall_score  31      risk_level HIGH
      threat_hunting health 0   contribution 25.0   detail "credential_dumping: 6C/0H"

    state/hunting_credential_dumping.json (08:12:27)
      n_indicators = 0     by_severity = {}     errors = []
      tools_used: huntCredentialDumping ok, 17 bản ghi

`25.0 / 31 = 81%` điểm rủi ro đang trích dẫn 6 chỉ báo mà tệp được trích dẫn không còn
chứa. Không có `run_id`, không có ảnh chụp, không có cảnh báo lệch pha. Portal,
Telegram, `HANDOFF.md`, daily brief đều đang đọc hỗn hợp hai lần chạy.

Thêm: `state/history/` **không có** `hunting_credential_dumping.json.prev`, nên bằng
chứng của 6 chỉ báo đó đã mất khỏi `state/`. Chỉ còn lại trong
`docs/project/IOC_QUALITY_REPORT.md` — một tài liệu, không phải state.

**Suggested Sprint:** SPRINT RUN-ISOLATION —
(1) Mỗi lần chạy sinh `run_id`; mọi tệp state mang `run_id` + `pipeline_started_at`.
(2) Consumer (portal, Telegram, handoff, gate) kiểm `run_id` đồng nhất; lệch pha là
cảnh báo hiển thị, không phải im lặng.
(3) Khoá chạy (lock file): lần chạy thứ hai từ chối khởi động khi lần trước chưa xong.
(4) `sprint_gate.py` thêm blocker: state chứa nhiều hơn một `run_id`.

---

## AQ-036 · Correlation Integrity · Truth Gap

**Issue:**
Sáu chỉ báo **CRITICAL "LSASS Memory Access"** xuất hiện ở một lần chạy và biến mất
hoàn toàn ở lần chạy kế tiếp, **33 giây sau**, không có thay đổi mã và không có lỗi thu
thập. Chúng đưa Risk từ **3 lên 31 (LOW → HIGH)**.

**Severity:** CRITICAL

**Root Cause:**
Cùng lớp bất ổn đã ghi ở AQ-031, nay ở mức CRITICAL và ở thành phần chi phối. Nguồn là
Security log — một cửa sổ trượt. Cuộc săn đọc "những gì còn trong log lúc đọc", không
đọc "những gì đã xảy ra trong khoảng thời gian X". Không có mốc con trỏ (bookmark /
last_record_id), nên hai lần đọc cách nhau 33 giây trả về hai tập sự kiện khác nhau và
cả hai đều được ghi là `LIVE_OBSERVED, errors: []`.

**Evidence:**

    docs/project/IOC_QUALITY_REPORT.md (lần chạy N)
      | credential_dumping | 6 | 0 | 100.0 | H 6 / M 0 / L 0 |
      | 100 | 6 | credential_dumping | LSASS Memory Access | CRITICAL | EVENT_LOG | COMPLETE | FULL |

    state/history/risk_score.json.prev
      overall 31   threat_hunting health 0   "credential_dumping: 6C/0H"

    state/hunting_credential_dumping.json (33 giây sau)
      n = 0    by_severity = {}    data_source LIVE_OBSERVED    errors []
      tools_used: huntCredentialDumping ok, 17 bản ghi, 5.05s

    state/history/hunting_credential_dumping.json.prev -> KHÔNG TỒN TẠI

    git diff HEAD -- scripts/hunt_credential_dumping.py -> không nằm trong danh sách sửa

Diễn biến Risk trong ~4 giờ, cùng một máy, không đổi cấu hình:

    10  ->  3  ->  31  ->  (?)
    nguyên nhân: 2 chỉ báo 4648 biến mất, rồi 6 chỉ báo LSASS xuất hiện rồi biến mất

**Business Impact:**
Một trong hai điều đúng, và cả hai đều nghiêm trọng:

- **6 chỉ báo đó là thật** — LSASS Memory Access CRITICAL, confidence 100, bằng chứng
  COMPLETE, quy kết FULL. Vậy hệ thống vừa phát hiện một sự kiện truy cập bộ nhớ LSASS
  rồi **tự xoá bằng chứng** 33 giây sau, không lưu `.prev`, không mở incident nào tồn
  tại qua lần chạy kế. Một phát hiện credential dumping không tái lập được là một phát
  hiện không dùng được.
- **6 chỉ báo đó là dương tính giả** — thì Risk đã nhảy LOW → HIGH và `severity floor`
  đã kích hoạt (*"7 phát hiện CRITICAL nâng risk_level từ LOW lên HIGH"*) trên cơ sở sai.

Không có cách nào phân biệt hai khả năng từ state hiện tại, vì bằng chứng đã mất. Đó
chính là vấn đề.

**Suggested Sprint:** SPRINT HUNT-REPRODUCIBILITY —
(1) Cuộc săn đọc log theo **khoảng thời gian khai báo** (`from`/`to`), không theo "còn
gì trong log lúc đọc"; ghi khoảng đó vào `hunt_scope`.
(2) Mốc con trỏ bền (last_record_id) để hai lần chạy liên tiếp không bỏ sót sự kiện.
(3) Mọi tệp hunting phải có `.prev` — `state/history/` hiện thiếu credential_dumping.
(4) Bộ kiểm hồi quy bằng **fixture** (đã đề xuất ở AQ-031, vẫn chưa làm): chạy hai lần
trên cùng fixture phải cho cùng kết quả. Chỉ fixture mới tách được "đã sửa" khỏi "hôm
nay dữ liệu khác" — và vòng này chứng minh điều đó áp dụng cho cả chiều ngược lại.
(5) Chỉ báo CRITICAL biến mất giữa hai lần chạy phải sinh cảnh báo, không im lặng.

---

## AQ-037 · Truth Gap

**Issue:**
`HANDOFF.md` công bố **Risk Score 3/100 · LOW**. State công bố **31 · HIGH**. Chênh
một bậc mức độ, trên tệp mà quy trình audit đọc đầu tiên mỗi vòng.

**Severity:** HIGH

**Root Cause:**
AQ-033 chưa trả. `generate_handoff.py` chạy thủ công, không phải stage, nên mỗi lần
pipeline sinh state mới nó lại trễ. Vòng này trễ thêm một mức: không chỉ trễ một sprint
(`4668b96` vs HEAD `ba86908`) mà trễ cả **phân loại rủi ro**.

Phần chỉ số đã khá hơn: `406 chỉ báo` và `Risk 3` là số ĐÚNG của lần chạy trước — cache
`tool_validation.json` không còn là nguyên nhân. Nguyên nhân còn lại thuần là thời điểm
chạy.

**Evidence:**

    docs/project/HANDOFF.md (Cập nhật 08:09:43)
      | Commit     | 4668b96 |        HEAD thật: ba86908
      | Risk Score | 3/100   |        state thật: 31
      | Risk Level | LOW     |        state thật: HIGH

Một người đọc HANDOFF lúc 08:13 thấy "LOW, 3/100". `risk_score.json` cùng lúc đó nói
"HIGH, 31", kèm note *"Severity floor áp dụng: 7 phát hiện CRITICAL nâng risk_level từ
LOW lên HIGH"*. Đây là khoảng cách tồi nhất có thể: tài liệu nói an toàn đúng lúc state
nói nguy hiểm.

**Suggested Sprint:** SPRINT HANDOFF-LIVE (AQ-033, chưa làm) — `generate_handoff.py`
thành stage cuối của pipeline. Bất biến CI: `HANDOFF.md` khai `risk_level` khác
`state/risk_score.json` là blocker. Gộp với AQ-035: handoff cũng phải in `run_id`.

---

## AQ-038 · Schema Drift · Truth Gap

**Issue:**
AQ-020 và AQ-034 chưa trả, và cả hai nay đứng cạnh những mục đã trả — nên trông như đã
xong. `crypto_score` vẫn là hằng số 100; độ phủ audit pipeline vẫn **17.3%** in ra thành
`0` trần.

**Severity:** HIGH

**Root Cause:**
Không đổi so với vòng 3 và vòng 5. `collect_crypto_inventory.py:137` ghi khoá số nguyên,
dòng 147-149 đọc khoá chuỗi. `TECHNICAL_DEBT.md:25` in kết quả bộ audit không kèm mẫu số.

**Evidence:**

    state/crypto_inventory.json
      total_findings = 19      severity values = {0: 17, 2: 2}
      severity_breakdown tổng = 0        score = 100   (đúng: 90)

    state/risk_score.json   crypto health 100, contribution 0.0

    scripts/pipeline_field_audit.py
      TONG: 107 truy cap | 0 so lieu gia
      PHAM VI: 107 / 617 loi goi (17.3%) — 510 loi goi KHONG thay

    docs/project/TECHNICAL_DEBT.md:25   | Số liệu giả trong pipeline Python | 0 |

Lưu ý quan trọng cho việc xếp ưu tiên: **không một mục nào trong AQ-035, AQ-036, AQ-020,
AQ-021 thuộc dạng `.get(key, default)`.** Kể cả đạt 100% độ phủ, `pipeline_field_audit.py`
cũng không bắt được chúng. Hàng `Số liệu giả trong pipeline Python` đang hứa nhiều hơn
phép đo của nó — và bốn số liệu giả nghiêm trọng nhất đang nằm ngoài nó.

Đối chiếu: `assets.json` cộng ra **399** lỗ hổng, `nessus_status.json` nói **64** —
AQ-021 nửa còn lại, chưa chạm.

**Suggested Sprint:** SPRINT KILL-GREEN-DEFAULTS (phần cuối) + SPRINT AUDIT-THE-AUDIT —
(1) Ánh xạ severity Nessus int→tên ở một chỗ dùng chung.
(2) Bất biến `sum(severity_breakdown.values()) == total_findings` (bắt AQ-020 và AQ-021
cùng lúc).
(3) `TECHNICAL_DEBT.md` in `0 / 107 kiểm / 617 lời gọi (17.3%)`; đổi tên hàng thành
*"Khoá thiếu có mặc định"* — đúng thứ nó đo.
(4) Phép kiểm khác cho lớp còn lại: đảo đầu vào từng thành phần điểm, khẳng định điểm
đổi. Đó là cách duy nhất lộ ra hằng số và hàm chỉ-một-giá-trị.

---

## TỒN ĐỌNG SAU VÒNG 6

| Mục | Hạng | Trạng thái |
|---|---|---|
| AQ-035 | CRITICAL | 🆕 state trộn hai lần chạy; risk 31 trích dẫn 6 chỉ báo không còn tồn tại |
| AQ-036 | CRITICAL | 🆕 6 CRITICAL LSASS xuất hiện/biến mất trong 33 giây; bằng chứng đã mất |
| AQ-020 / AQ-032 / AQ-038 | CRITICAL | ❌ `crypto_score` hằng số 100 |
| AQ-021 | CRITICAL | 🔶 staleness đã thêm; 399 vs 64 vẫn nguyên |
| AQ-002 | CRITICAL | ❌ attribution FULL vs hostname `unresolved` |
| AQ-007 / AQ-030 | HIGH | ❌ Deployment Truth, 5 vòng chưa chạm |
| AQ-033 / AQ-037 | HIGH | ❌ HANDOFF: LOW 3 vs state HIGH 31 |
| AQ-016 | HIGH | ❌ 5 giá trị "WAAP Score" |
| AQ-017 | HIGH | ❌ cổng merge không kiểm tuổi đầu vào |
| AQ-018 | HIGH | ❌ `protection_status: unknown` → `false` |
| AQ-024 | HIGH | 🔶 `\|\| 'MEDIUM'` vẫn bịa severity |
| AQ-034 / AQ-038 | HIGH | ❌ độ phủ 17.3%, tiêu đề `0` trần |

**Đang mở: 12 (5 CRITICAL, 7 HIGH). Đã trả tích luỹ: 19.**

---

## NHẬN ĐỊNH VÒNG 6

PR #44 sửa đúng gốc bốn mục, trong đó `sprint_gate.py` lần đầu **có khả năng nói không**
kể từ vòng 2 — `status is None` là BLOCKER, danh sách stage rỗng là BLOCKER. Bản sửa
`ROUTINE_HINTS` giữ đúng phân biệt giữa phỏng đoán theo tên và sự thật về chủ thể, thay
vì nới lỏng toàn bộ miễn trừ. Đó là đọc kỹ chứ không phải làm cho xong.

Nhưng vòng này lộ ra một lớp vấn đề chưa từng thấy trong năm vòng trước, và nó lớn hơn
mọi mục còn lại trong hàng đợi:

**Hệ thống không có ranh giới giữa các lần chạy.** Ngay lúc audit, `state/` chứa tệp của
hai lần chạy khác nhau, và con số quan trọng nhất — `Risk 31 HIGH` — đang trích dẫn 6
chỉ báo mà tệp được trích dẫn không còn chứa. Không `run_id`, không ảnh chụp nguyên tử,
không khoá chạy, không cảnh báo lệch pha.

**Và các cuộc săn không tái lập được.** Risk đã đi `10 → 3 → 31` trong bốn giờ trên một
máy không đổi cấu hình, mỗi lần vì một tập chỉ báo khác nhau xuất hiện rồi biến mất khỏi
cửa sổ Security log. Sáu chỉ báo CRITICAL "LSASS Memory Access" sống đúng 33 giây và
không để lại `.prev`.

Điều này định lại thứ tự ưu tiên. Vòng 5 đã cảnh báo *"không thể dùng Risk để đo tiến
bộ"*; vòng 6 cho thấy hệ quả mạnh hơn: **không thể đóng bất kỳ mục nào dựa trên một con
số đọc từ `state/`**, vì không ai biết con số đó thuộc lần chạy nào. Điều đó áp cho cả
Builder lẫn Auditor — kể cả bảng tồn đọng ở trên.

`run_id` + fixture là điều kiện cần trước mọi việc khác.

**Thứ tự vòng tới:** AQ-035 → AQ-036 (kèm fixture) → AQ-020/038 → AQ-021 → AQ-037 →
AQ-030/007 → AQ-034.

---

*Vòng 6, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*


---
---

# VÒNG 7 — 2026-09-14 08:17 · PR #45 `self-observation-and-scoring`

HEAD `484f00b`. Working tree sạch phần mã. Auditor READ ONLY.

---

## ĐÃ TRẢ — kiểm chứng được

| Mục | Bằng chứng |
|---|---|
| **AQ-036** | Nguyên nhân đã tìm ra và sửa tận gốc. `SELF_OBSERVATION_HINTS` nay **sinh ra từ tên module thật** (`_module_names()`) thay vì danh sách 13 tên viết tay. Thêm `SIGNATURE_RE` bắt chuỗi từ khoá nối bằng `\|` — mẫu nhận dạng của người phòng thủ, không phải câu lệnh của kẻ tấn công |
| **AQ-031** (phương pháp) | `tests/fixtures/test_scoring_fixtures.py` (+173 dòng) — đúng bộ kiểm bằng fixture đã đề xuất, và nó **có** ca `"4648 cua tai khoan SYSTEM o muc HIGH -> van bi ha xuong tieng on"` |
| **AQ-016** | `waapScoreFrom` nay đọc `protection_coverage.score` và trả `null` khi vắng. Công thức 60/15/15/10 đã xoá khỏi `web/app.js` (0 bản sao còn lại) và khỏi bot. Chỉ số được **đổi tên** thành `protection_coverage` — không còn tranh tên với WAAP health |
| **AQ-017** | `sprint_gate.py:140-190` — `_age_hours()` kiểm tuổi `tool_validation.json`, `pipeline_results.json`, `sensor_coverage.json`; quá ngưỡng là **blocker** |

### Ghi nhận riêng về AQ-036

Builder tự tìm ra nguyên nhân và ghi thẳng vào commit message:

> *"Writing the comment that explains the detection rule triggered the detection rule.
> The comment in ioc_quality.py explaining why `lsass` is an ambiguous keyword was
> applied via a PowerShell heredoc. Event 4688 recorded that command line. The credential
> dumping hunt matched `lsass` in it. Six CRITICAL indicators, and risk_level went
> LOW -> HIGH on a machine where nothing had happened."*

Vòng 6 đặt câu hỏi *"một trong hai điều đúng: 6 chỉ báo đó là thật, hay là dương tính
giả?"*. Câu trả lời: **dương tính giả, và nguyên nhân là chính quá trình sửa lỗi**.
Đây là kiểu bằng chứng tốt nhất một hàng đợi audit có thể nhận — không suy diễn, có
đường dẫn nhân quả đầy đủ.

---

## AQ-039 · Correlation Integrity · Risk Consistency

**Issue:**
Dương tính giả ở AQ-036 đã được sửa tại bộ phát hiện, nhưng **hai sự cố nó sinh ra vẫn
đang MỞ**, và hai sự cố đó hiện chiếm **50% điểm rủi ro (3.0 / 6.0)**. Bằng chứng ghi
trong chúng đã sai ở thời điểm đọc.

**Severity:** CRITICAL

**Root Cause:**
Vòng phản hồi giữa hai stage của pipeline, không có đường thu hồi:

    generate_incidents.py:119-137   đọc  risk_score.json  ->  tạo sự cố khi risk_level HIGH
    calculate_risk_score.py          đọc  incidents.json   ->  sự cố đang mở nâng risk

Thứ tự stage: `generate_incidents` (:472) → `calculate_risk_score` (:486). Sự cố nuôi
rủi ro **trong cùng lần chạy**; rủi ro nuôi sự cố ở **lần chạy sau**. Đây là vòng phản
hồi dương trễ một nhịp.

Khi chỉ báo nguồn bị vô hiệu — ở đây là bị nhận ra là self-observation — **không có cơ
chế nào rút lại các artifact nó đã sinh**. Sự cố không mang con trỏ về chỉ báo nguồn,
nên không có gì để rà lại.

**Evidence:**

    state/incidents.json (2 sự cố, cả hai OPEN, cả hai HIGH)

    INC-0002  "Rủi ro tăng vọt: Risk Level = HIGH"
      created_at : 2026-09-14T08:13:19.562925
      evidence   : ["Risk Score: 31", "Thành phần yếu: threat_hunting"]

    INC-0003  "Sự kiện nghi ngờ: Level Change"
      evidence   : ["Mức rủi ro thay đổi: LOW → HIGH"]

    state/risk_score.json (đọc cùng lúc)
      overall_score  6        risk_level LOW
      threat_hunting health 100   "không có IOC CRITICAL/HIGH"
      incidents      health 88    contribution 3.0    "0 sự cố CRITICAL, 2 HIGH đang mở"

Đối chiếu từng dòng bằng chứng của INC-0002 với state hiện tại:

    "Risk Score: 31"              -> thật: 6
    "Thành phần yếu: threat_hunting" -> thật: threat_hunting health 100, mạnh nhất

Cả hai dòng bằng chứng đều sai. Và sự cố ấy đang đóng góp vào chính con số nó trích dẫn
sai: `3.0 / 6.0 = 50%` điểm rủi ro hiện tại đến từ hai sự cố sinh ra bởi một dương tính
giả đã được thừa nhận.

INC-0002 tự trích dẫn `threat_hunting` là "thành phần yếu"; `threat_hunting` nay là 100.
Sự cố sống sót qua chính điều kiện tạo ra nó.

**Business Impact:**
Risk hiện tại là **6**, đúng ra phải là **3**. Một nửa điểm rủi ro của hệ thống là tiếng
vọng của một lỗi đã sửa. Tệ hơn, cơ chế này tự duy trì: chừng nào hai sự cố còn mở,
`incidents` còn giữ health 88; nếu risk_level lại chạm HIGH vì bất kỳ lý do gì,
`generate_incidents` sẽ tạo thêm INC mới, và mức nền lại dâng thêm một bậc. Mỗi dương
tính giả để lại một khoản nợ vĩnh viễn trên điểm rủi ro.

**Suggested Sprint:** SPRINT INVALIDATION-PATH —
(1) Mỗi sự cố mang `source_indicators: [id...]` và `source_run_id`.
(2) Khi chỉ báo nguồn bị đánh `suppressed` / self-observation / biến mất, sự cố phái
sinh tự chuyển `INVALIDATED` kèm lý do — không xoá, để còn rà lại được.
(3) Cắt vòng phản hồi: `generate_incidents` **không** được tạo sự cố từ `risk_level` —
đó là sự cố về một con số, không phải về một quan sát. `calculate_risk_score` là nơi
duy nhất diễn giải risk_level.
(4) Bất biến trong `sprint_gate.py`: mọi sự cố OPEN phải có bằng chứng đối chiếu được
với state hiện tại; bằng chứng mâu thuẫn là blocker.

---

## AQ-040 · Truth Gap · Risk Consistency

**Issue:**
AQ-035 chưa trả: `run_id` **là `None` trên mọi tệp state**. Lần này các dấu thời gian
tình cờ nhất quán, nên state đang mạch lạc — nhưng cơ chế bảo đảm điều đó vẫn không tồn
tại.

**Severity:** CRITICAL

**Root Cause:**
Không đổi so với vòng 6. Pipeline ghi thẳng từng stage vào `state/`, không ảnh chụp
nguyên tử, không khoá chạy, không đóng dấu lần chạy.

**Evidence:**

    state/risk_score.json                    run_id = None   ts 08:13:19
    state/hunting_credential_dumping.json    run_id = None   ts 08:13:18
    state/hunting_lateral_movement.json      run_id = None   ts 08:13:13
    state/hunting_persistence.json           run_id = None   ts 08:13:07
    state/hunting_suspicious_processes.json  run_id = None   ts 08:13:11

Lần này thứ tự đúng (mọi hunt trước risk). Vòng 6 thì không:
`risk_score 08:11:54` đứng cạnh `hunting_credential_dumping 08:12:27`.

Sự khác nhau giữa hai vòng **không phải do bản sửa nào** — vòng 6 có hai lần chạy chồng
lên nhau, vòng 7 thì không. Đó đúng là loại "đã sửa hay hôm nay dữ liệu khác" mà vòng
lặp này phải phân biệt, và ở đây câu trả lời là **hôm nay dữ liệu khác**.

AQ-039 cho thấy hậu quả thực tế của việc thiếu `run_id`: không có `source_run_id` thì
không thể rút lại artifact của một lần chạy bị vô hiệu.

**Suggested Sprint:** SPRINT RUN-ISOLATION (AQ-035, chưa làm) — `run_id` trên mọi tệp
state; khoá chạy; consumer kiểm `run_id` đồng nhất; blocker trong gate khi state chứa
nhiều hơn một `run_id`. Đây là tiền đề kỹ thuật của AQ-039 nên hai mục nên làm cùng
sprint.

---

## AQ-041 · Schema Drift · Truth Gap

**Issue:**
Ba mục cũ chưa trả, và đều đã đứng yên từ ba vòng trở lên: `crypto_score` hằng số 100
(AQ-020), 399 vs 64 lỗ hổng (AQ-021), attribution `FULL` trên kho không phân giải được
tên nào (AQ-002).

**Severity:** CRITICAL

**Root Cause:**
Không đổi. Cả ba thuộc cùng một họ: **một phép ánh xạ sai giữa hai lược đồ, không ai đối
chiếu hai đầu.** Không mục nào thuộc dạng `.get(key, default)` nên
`pipeline_field_audit.py` không thấy chúng — đã ghi ở AQ-034/AQ-038.

**Evidence:**

    AQ-020  state/crypto_inventory.json
            total_findings 19 · severity {0: 17, 2: 2} · breakdown tổng 0 · score 100
            (đúng: 90). `collect_crypto_inventory.py:137` ghi khoá int, :147-149 đọc khoá str

    AQ-021  assets.json cộng vuln = 399   |   nessus_status.json total = 64
            Chênh 6.2 lần trên cùng một bản quét

    AQ-002  assets.json  hostname_source = {unresolved: 11}   (11/11)
            attribution_quality:
              lateral    FULL 258 / PARTIAL 2
              persistence FULL 96
              processes   FULL 78
            -> FULL 432 / 434 = 99.5% "đã quy kết đầy đủ" trên kho không máy nào có tên

**Suggested Sprint:** SPRINT SCHEMA-RECONCILE — một bất biến duy nhất đóng được cả ba:
với mỗi cặp (nguồn, dẫn xuất), tổng phải khớp.
(1) `sum(severity_breakdown.values()) == total_findings` → bắt AQ-020.
(2) `sum(assets[].vulnerability_count) == nessus_status.total` → bắt AQ-021.
(3) `%FULL attribution <= %assets có hostname_source != unresolved` → bắt AQ-002.
Cả ba là phép so tổng, không phải phép kiểm tên trường — nên chúng thuộc một bộ audit
**khác** với `pipeline_field_audit.py`, không phải phần mở rộng của nó.

---

## AQ-042 · Portal Truth · Deployment Truth

**Issue:**
Ba mục hiển thị chưa trả, trong đó Deployment Truth nay là **6 vòng liên tiếp** không
được chạm.

**Severity:** HIGH

**Root Cause & Evidence:**

**AQ-018 (một nửa).** State đã sửa đúng: `protection_active` nay là `None` thay vì
`false` — chưa-biết không còn bị ép thành đã-đo. `web/app.js:765` cũng đã sửa:
`=== true ? '✅' : '⚠️'`. Nhưng `web/app.js:1177` chưa:

    const protActive = stateData.waap?.security_summary?.protection_active ? '✓' : '✗';

`None` là falsy → hiển thị **`✗`** = "đã đo, không có bảo vệ". Một nửa portal nói
"chưa biết", nửa kia nói "không có".

**AQ-024.** `web/app.js:1703` vẫn:

    const severity = ind?.severity || 'MEDIUM';

Chỉ báo thiếu severity vẫn được portal **bịa** cho một mức.

**AQ-007 / AQ-030.** Không thay đổi từ vòng 1:

    render.yaml:9      startCommand: node web-server.js
    package.json:7     "start": "node web/server.js"
    daily_brief/latest.html -> 2026-09-13   (hôm nay 14/09)

Toàn bộ công portal của bốn PR gần nhất — `portal_escape_audit` 86/86, `riskView()`,
lọc `suppressed`, xoá 5 bản sao công thức WAAP — nằm trong `web/app.js`, tệp Render
không phục vụ. Trang người dùng thật sự mở vẫn là bản hôm qua.

**AQ-033 / AQ-037.** `HANDOFF.md` khai `ba86908`; HEAD là `484f00b`. Phần chỉ số đã
khớp (Risk 6 = 6, 434 chỉ báo), nên nguyên nhân còn lại thuần là thời điểm chạy — nó
không phải stage của pipeline.

**AQ-034.** `TECHNICAL_DEBT.md:25` vẫn in `| Số liệu giả trong pipeline Python | 0 |`,
không mẫu số, không dòng phạm vi. Vòng này lại thêm bằng chứng cho luận điểm ở AQ-038:
**AQ-039, AQ-040 và cả ba mục AQ-041 đều nằm ngoài dạng lỗi mà hàng đó đo.**

**Suggested Sprint:** SPRINT DEPLOY-TRUTH (AQ-007, sáu vòng chưa làm) — đây nay là mục
có tỉ lệ giá trị trên công sức cao nhất trong hàng đợi: nó quyết định toàn bộ công
portal của bốn sprint vừa qua có tới được người dùng hay không. Kèm hai sửa một dòng
(`web/app.js:1177`, `:1703`) và `generate_handoff.py` thành stage cuối pipeline.

---

## TỒN ĐỌNG SAU VÒNG 7

| Mục | Hạng | Trạng thái |
|---|---|---|
| AQ-039 | CRITICAL | 🆕 2 sự cố từ dương tính giả vẫn OPEN, chiếm 50% điểm rủi ro; vòng phản hồi incidents↔risk |
| AQ-035 / AQ-040 | CRITICAL | ❌ `run_id: None`; vòng 7 mạch lạc do may, không do sửa |
| AQ-020 / AQ-041 | CRITICAL | ❌ `crypto_score` hằng số 100 |
| AQ-021 / AQ-041 | CRITICAL | ❌ 399 vs 64 |
| AQ-002 / AQ-041 | CRITICAL | ❌ FULL 432/434 trên kho 11/11 `unresolved` |
| AQ-007 / AQ-030 | HIGH | ❌ **6 vòng** chưa chạm |
| AQ-018 | HIGH | 🔶 state + app.js:765 đã sửa; app.js:1177 vẫn `None → ✗` |
| AQ-024 | HIGH | ❌ `\|\| 'MEDIUM'` tại app.js:1703 |
| AQ-033 / AQ-037 | HIGH | 🔶 chỉ số đã khớp; commit vẫn trễ một sprint |
| AQ-034 / AQ-038 | HIGH | ❌ `0` trần, không mẫu số |

**Đang mở: 10 (5 CRITICAL, 5 HIGH). Đã trả tích luỹ: 23.**

---

## NHẬN ĐỊNH VÒNG 7

Bốn mục đóng, và cách đóng AQ-036 là phần đáng chú ý nhất: Builder không chỉ sửa triệu
chứng mà truy ra đường nhân quả đầy đủ — bình luận giải thích luật phát hiện, viết bằng
PowerShell heredoc, bị Event 4688 ghi lại, bị chính luật đó khớp. Rồi sửa tận gốc
(`SELF_OBSERVATION_HINTS` sinh từ tên module thật thay vì danh sách viết tay) và thêm
fixture để nó không quay lại. Đó là mẫu cho mọi mục còn lại.

Nhưng chính sự cố đó để lại một vết mà sprint không dọn, và vết đó là phát hiện lớn
nhất vòng này: **hệ thống không có đường thu hồi.** Sáu chỉ báo self-observation đã sinh
ra hai sự cố; chỉ báo bị vô hiệu, sự cố thì không. Hai sự cố ấy hiện chiếm **một nửa
điểm rủi ro**, và bằng chứng ghi trong chúng — `"Risk Score: 31"`, `"Thành phần yếu:
threat_hunting"` — cả hai dòng đều sai khi đọc lại: risk là 6, `threat_hunting` là thành
phần **mạnh nhất** với health 100.

Đằng sau nó là một vòng phản hồi có thật giữa hai stage: `generate_incidents` đọc
`risk_score.json`, `calculate_risk_score` đọc `incidents.json`. Mỗi dương tính giả để
lại một khoản nợ vĩnh viễn trên điểm rủi ro, và mức nền chỉ có thể đi lên.

Điều này nối thẳng với AQ-040: không có `run_id` thì không có `source_run_id`, và không
có `source_run_id` thì không thể rút lại artifact của một lần chạy bị vô hiệu. Hai mục
là một bài toán.

Và ghi nhận một quan sát về chính vòng lặp này: vòng 6 báo state lệch pha, vòng 7 báo
mạch lạc — **không phải vì có bản sửa nào**, mà vì vòng 6 rơi vào lúc hai lần chạy chồng
nhau. Đúng loại nhầm lẫn mà bước 3 của quy trình được đặt ra để chặn.

**Thứ tự vòng tới:** AQ-039 + AQ-040 (một sprint) → AQ-041 (ba bất biến so tổng) →
AQ-007/030 → AQ-018/024 (hai dòng) → AQ-037 → AQ-034.

---

*Vòng 7, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*


---
---

# VÒNG 8 — 2026-09-14 08:22 · working tree (chưa commit)

HEAD `484f00b` — **không có commit mới**. Thay đổi nằm trong working tree:
`scripts/run_context.py` (mới), `state_manager.py`, `generate_incidents.py`,
`calculate_risk_score.py`, `run_intelligence_pipeline.py`. Auditor READ ONLY.

---

## ĐÃ TRẢ — kiểm chứng được

### AQ-039 ✅ — đường thu hồi đã có, và Risk về đúng 3

Vòng 7 kết luận: *"Risk hiện tại là 6, đúng ra phải là 3."* Đo lại sau bản sửa:

    state/risk_score.json      overall_score 3   risk_level LOW
      incidents  health 100  contribution 0.0
                 "0 sự cố CRITICAL, 0 HIGH đang mở (2 bản ghi đã đóng...)"

    state/incidents.json
      total_incidents 0   by_severity {}   by_status {'INVALIDATED': 2}
      INC-0002  INVALIDATED   "Rủi ro tăng vọt: Risk Level = HIGH"
      INC-0003  INVALIDATED   "Sự kiện nghi ngờ: Level Change"

Ba điểm làm đúng:
1. **Giữ lại, không xoá** — `INVALIDATED` kèm lý do, nên quyết định còn rà lại được.
2. **Cắt vòng phản hồi ở gốc** — `risk_score.json` vào danh sách nguồn bị cấm với lý do
   viết thẳng: *"điểm rủi ro là kết quả tính từ các quan sát khác"*.
3. **Chặn cả đường vòng** — commit ghi rõ đường gián tiếp qua timeline
   (`collect_timeline_events` đọc `risk_score.json` rồi phát CRITICAL "Level Change")
   cũng bị chặn: *"chặn đường thẳng mà để hở đường này thì..."*.

### AQ-035 / AQ-040 ✅ — `run_id` đặt ở cửa ra duy nhất

`scripts/run_context.py` mới, và điều đáng ghi nhận nhất là **chỗ đặt nó**:

    state_manager.write_state_atomic():
        import run_context
        data = run_context.stamp(data)

    # "40 script ghi state qua hàm này. Sửa từng script là cách đã chứng minh
    #  không scale ở AQ-014: một lần đổi khoá làm hỏng năm consumer và Builder
    #  sửa được một. Ở đây có đúng một cửa ra, nên dấu lần chạy đặt ở cửa đó."

Kiểm lại độc lập: **0 script ghi JSON vào `state/` mà không qua `state_manager`.** Cửa
ra thật sự là duy nhất, nên việc đóng dấu là cấu trúc chứ không phải thói quen.

Và quyết định không tự sinh `run_id` khi thiếu là đúng:

    # "Cám dỗ rõ ràng là: nếu không có biến môi trường thì sinh một id mới...
    #  Làm vậy thì mọi tệp đều CÓ run_id, mọi bảng đều xanh, và phép kiểm
    #  'cả state có cùng một lần chạy' trở thành luôn luôn đỏ theo một cách vô nghĩa."

Live: `risk_score.json` và `incidents.json` mang `run_id: null, run_scope: STANDALONE` —
vắng mặt được **khai báo**, không bị lấp. Đó chính là kỷ luật mà cả hàng đợi này đòi
hỏi, lần này áp cho chính cơ chế chống lấp.

Còn lại: 5 tệp state sinh lúc 08:13 vẫn `run_scope: None` vì chưa chạy lại. Đó là lan
truyền, không phải thiếu sót thiết kế.

---

## AQ-043 · Green Default · Truth Gap

**Issue:**
Cơ chế vừa xây để chặn suy giảm âm thầm **tự suy giảm âm thầm**. Nếu `run_context`
không import được, `state_manager` nuốt lỗi và ghi state **không có dấu lần chạy**,
không cảnh báo, không ghi log.

**Severity:** HIGH

**Root Cause:**
`scripts/state_manager.py`

    try:
        import run_context
        data = run_context.stamp(data)
    except ImportError:
        # state_manager được import từ nhiều thư mục; thiếu run_context thì ghi
        # state vẫn phải chạy — mất dấu lần chạy, không mất dữ liệu.
        pass

Đánh đổi được cân nhắc có ý thức và ghi ra — hơn hẳn mặc định ngầm. Nhưng kết quả cuối
cùng vẫn là dạng đã ghi ở AQ-003, AQ-013, AQ-026: **một tệp state thiếu `run_id` trông
giống hệt một tệp chạy tay hợp lệ** (`run_scope: STANDALONE`, `run_id: null`). Người đọc
không phân biệt được "chạy tay, đã khai" với "chạy trong pipeline, mất dấu".

Đây đúng là điều `run_context` tồn tại để chặn, áp vào chính nó thì hở.

**Evidence:**

    scripts/state_manager.py   except ImportError: pass        <- không log, không cờ

    Hai trạng thái không phân biệt được ở phía người đọc:
      (a) chạy tay hợp lệ        -> run_id null, run_scope STANDALONE
      (b) pipeline, import hỏng  -> run_id null, run_scope thiếu/None

    state/ hiện có cả hai dạng:
      risk_score.json               run_scope STANDALONE   (dạng a)
      hunting_lateral_movement.json run_scope None         (dạng — chưa chạy lại)

Blocker dự kiến của AQ-040 là *"state chứa nhiều hơn một `run_id`"*. Với nhánh này,
một lần chạy mất dấu hoàn toàn sẽ **lọt** phép kiểm đó thay vì kích hoạt nó — đúng chiều
sai nguy hiểm nhất.

**Suggested Sprint:** SPRINT RUN-ISOLATION (phần cuối) — `except ImportError` phải ghi
`run_scope: 'UNSTAMPED'` kèm lý do vào chính tệp, không im lặng. `sprint_gate.py` coi
`UNSTAMPED` là blocker. Nếu `run_context` là bắt buộc — và nó nên là, vì AQ-039 phụ
thuộc `source_run_id` — thì thiếu nó là lỗi khởi động, không phải điều bỏ qua.

---

## AQ-041 · Schema Drift — KHÔNG ĐỔI, vòng thứ tư

**Issue:** Ba mục cùng họ, đứng yên từ vòng 3/5/6 tới nay. Đo lại vòng này, không con số
nào thay đổi.

**Severity:** CRITICAL

**Root Cause:** Không đổi — ánh xạ sai giữa hai lược đồ, không ai đối chiếu hai đầu.
Không mục nào thuộc dạng `.get(key, default)` nên `pipeline_field_audit.py` không thấy.

**Evidence:**

    AQ-020  crypto score 100 · severity_breakdown tổng 0 · total_findings 19   (đúng: 90)
    AQ-021  assets vuln tổng 399   |   nessus_status.total 64      (chênh 6.2 lần)
    AQ-002  hostname_source = {unresolved: 11}   (11/11)
            attribution_quality lateral = {FULL: 258, PARTIAL: 2}

**Suggested Sprint:** SPRINT SCHEMA-RECONCILE — ba bất biến so tổng (đã nêu ở vòng 7):
`sum(severity_breakdown) == total_findings` · `sum(assets[].vulnerability_count) ==
nessus.total` · `%FULL attribution <= %hostname đã phân giải`.

Ghi chú xếp ưu tiên: hai sprint vừa rồi (AQ-039, AQ-040) đều là **cơ chế** — đường thu
hồi, dấu lần chạy. Ba mục này là **số liệu sai đang hiển thị**. Cơ chế đã đủ tốt để đỡ
chúng; giờ là lúc sửa chính con số.

---

## AQ-042 · Portal / Deployment Truth — KHÔNG ĐỔI, vòng thứ bảy

**Issue:** Deployment Truth chưa được chạm lần nào kể từ vòng 1. Hai sửa một dòng ở
portal cũng chưa.

**Severity:** HIGH

**Evidence:**

    render.yaml:9            startCommand: node web-server.js
    package.json:7           "start": "node web/server.js"
    daily_brief/latest.html  2026-09-13          (hôm nay 14/09)

    web/app.js:1177  protection_active ? '✓' : '✗'      <- None -> '✗'
    web/app.js:1703  ind?.severity || 'MEDIUM'          <- bịa severity

    docs/project/TECHNICAL_DEBT.md:25  | Số liệu giả trong pipeline Python | 0 |
                                       (thật: 0 / 107 kiểm / 617 lời gọi = 17.3%)

    HANDOFF.md  Commit ba86908   |   HEAD 484f00b

Năm sprint liên tiếp đã cải thiện `web/app.js`. Không sprint nào làm cho tệp đó được
phục vụ. Tỉ lệ giá trị trên công sức của AQ-007 nay là cao nhất trong hàng đợi: nó
quyết định toàn bộ công portal đã tích luỹ có tới được người dùng hay không.

**Suggested Sprint:** SPRINT DEPLOY-TRUTH — chốt entrypoint, đồng bộ `render.yaml` với
`package.json`, đưa bộ sinh brief HTML vào pipeline, đóng dấu tuổi lên trang. Kèm hai
sửa một dòng ở portal, `generate_handoff.py` thành stage cuối, và mẫu số cho hàng
`TECHNICAL_DEBT.md:25`.

---

## TỒN ĐỌNG SAU VÒNG 8

| Mục | Hạng | Trạng thái |
|---|---|---|
| AQ-020 / AQ-041 | CRITICAL | ❌ `crypto_score` hằng số 100 — **4 vòng** |
| AQ-021 / AQ-041 | CRITICAL | ❌ 399 vs 64 — **6 vòng** |
| AQ-002 / AQ-041 | CRITICAL | ❌ FULL 258/260 trên kho 11/11 `unresolved` — **8 vòng** |
| AQ-043 | HIGH | 🆕 `except ImportError: pass` bỏ dấu lần chạy trong im lặng |
| AQ-007 / AQ-030 / AQ-042 | HIGH | ❌ Deployment Truth — **7 vòng** |
| AQ-018 | HIGH | 🔶 `app.js:1177` vẫn `None → ✗` |
| AQ-024 | HIGH | ❌ `\|\| 'MEDIUM'` tại `app.js:1703` |
| AQ-033 / AQ-037 | HIGH | 🔶 chỉ số khớp; commit trễ một sprint |
| AQ-034 / AQ-038 | HIGH | ❌ `0` trần, không mẫu số |

**Đang mở: 9 (3 CRITICAL, 6 HIGH). Đã trả tích luỹ: 25.**

---

## NHẬN ĐỊNH VÒNG 8

Hai mục CRITICAL đóng, và cả hai đóng theo cách đáng ghi nhận.

AQ-039 khép lại bằng một con số kiểm được: vòng 7 tuyên bố *"Risk đúng phải là 3"*, vòng
8 đo được **3**. Dự báo và kết quả khớp, nên bản sửa là bản sửa — không phải dữ liệu đổi.

AQ-040 đóng ở đúng chỗ. `run_context.stamp()` đặt trong `state_manager.write_state_atomic()`
thay vì rải khắp 40 script, và commit trích dẫn thẳng bài học AQ-014 làm lý do. Kiểm độc
lập: **0 script ghi state vòng qua cửa đó.** Đây là lần đầu trong tám vòng một bản sửa
được thiết kế từ chính lịch sử lỗi của hàng đợi này thay vì từ triệu chứng.

Quyết định **không tự sinh `run_id`** cũng đúng, và vì một lý do sâu: tự sinh sẽ làm mọi
tệp "có `run_id`", mọi bảng xanh, và phép kiểm mất nghĩa. Đó chính xác là hình dạng của
AQ-003, AQ-013, AQ-026 — lần này được nhận ra **trước** khi viết.

Nhưng cùng bản sửa đó để hở một chỗ theo đúng hình dạng cũ: `except ImportError: pass`
(AQ-043). Cơ chế chống lấp-chỗ-trống tự lấp chỗ trống của chính nó, im lặng, và một lần
chạy mất dấu sẽ **lọt** phép kiểm thay vì kích hoạt nó.

Quan sát về xu hướng: tám vòng, 25 mục đã trả. Nhưng ba mục CRITICAL còn lại đã đứng yên
lần lượt **4, 6 và 8 vòng**, và Deployment Truth đứng yên **7 vòng**. Các sprint đang
chọn việc theo độ mới thay vì theo tuổi nợ. Cả bốn mục đó đều là số liệu sai đang hiển
thị, không phải cơ chế — và cơ chế thì nay đã đủ tốt để đỡ chúng.

**Thứ tự vòng tới:** AQ-041 (ba bất biến so tổng, một sprint) → AQ-042/AQ-007 →
AQ-043 → AQ-018/AQ-024 (hai dòng) → AQ-037 → AQ-034.

---

*Vòng 8, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*


---
---

# VÒNG 9 — 2026-09-14 08:27 · working tree (chưa commit)

HEAD `484f00b` — không commit mới. Thay đổi mới so với vòng 8:
`scripts/run_coherence_audit.py` (mới), `sprint_gate.py`, `web/app.js`, `web/index.html`.
Auditor READ ONLY.

---

## ĐÃ TRẢ

| Mục | Bằng chứng |
|---|---|
| **AQ-018** | `web/app.js:765` dùng `=== true ? '✅' : '⚠️'`; dòng `protection_active ? '✓' : '✗'` ở `:1177` đã xoá. `None` không còn hiển thị thành "đã đo, không có bảo vệ" |
| **AQ-024** | `web/app.js:1713` — `\|\| 'MEDIUM'` đã bỏ, kèm chú thích viện dẫn AQ-024 |

---

## AQ-044 · Truth Gap · Green Default

**Issue:**
`run_coherence_audit.py` — bộ kiểm mới, đã nối vào cổng merge — báo **"TONG: 0 vi pham"**
trong khi chính dòng phạm vi của nó nói **0/7 tệp có dấu lần chạy**. Không tệp nào được
đóng dấu, nên không có gì để đối chiếu, nên không thể có vi phạm.

**Severity:** CRITICAL

**Root Cause:**
Bộ kiểm đối chiếu `run_id` giữa các tệp trong "tập gắn kết". Khi **không** tệp nào mang
`run_id`, tập so sánh rỗng và kết quả là 0. Không có nhánh nào phân biệt *"đã kiểm, nhất
quán"* với *"không kiểm được, không có dữ liệu"*.

Đây là lần thứ **tư** cùng một hình dạng xuất hiện trong repo này:

| Bộ kiểm | Phạm vi thật | Tiêu đề công bố |
|---|---|---|
| `portal_field_audit` (vòng 1) | 29 / 122 truy cập | `0` |
| `pipeline_field_audit` (vòng 4–8) | 107 / 617 lời gọi | `0` |
| `run_coherence_audit` (vòng này) | **0 / 7 tệp** | `0 vi phạm` |

Và nó nay nằm trong `sprint_gate.py:115` — tức là một tiêu chí merge **không có khả năng
thất bại** ở trạng thái hiện tại. Đúng hình dạng AQ-013, mục vừa được sửa ở vòng 6 vì lý
do y hệt.

**Evidence:**

    scripts/run_coherence_audit.py  (chạy lúc audit)
      PHAM VI: 0/7 tep trong tap gan ket co dau lan chay;
               0 su co dang mo, 0 truy nguoc duoc; 2 ban ghi da thu hoi.
      KHONG DAU: executive_findings.json, hunting_credential_dumping.json,
                 hunting_lateral_movement.json, hunting_persistence.json,
                 hunting_suspicious_processes.json, incidents.json, risk_score.json
      TONG: 0 vi pham

    scripts/sprint_gate.py:50   import run_coherence_audit
    scripts/sprint_gate.py:115  coherence, coherence_scope = run_coherence_audit.audit()

Bảy tệp liệt kê là **toàn bộ** tập gắn kết. `0/7` không phải lan truyền chậm ở một góc —
đó là 100% tập chưa có dữ liệu để kiểm.

Lưu ý phân biệt "đã sửa mã" với "hôm nay dữ liệu khác": lý do 0/7 là các tệp sinh lúc
08:13 có trước `run_context`, còn `risk_score.json` chạy tay nên `run_scope: STANDALONE`,
`run_id: null` một cách hợp lệ. Cơ chế đóng dấu (AQ-040) **đúng**. Vấn đề nằm ở chỗ bộ
kiểm báo tình trạng đó là `0 vi phạm` thay vì `không đánh giá được`.

**Business Impact:**
Cổng merge vừa mọc thêm một tiêu chí xanh vĩnh viễn. Tệ hơn: nếu AQ-043 xảy ra thật —
`run_context` không import được và `state_manager` nuốt lỗi — mọi tệp sẽ mất dấu, bộ
kiểm này sẽ báo `0 vi phạm`, và cổng sẽ xanh. Hai lỗ hổng cộng lại thành một đường thẳng
từ hỏng-âm-thầm tới merge-được.

**Suggested Sprint:** SPRINT RUN-ISOLATION (phần cuối, gộp AQ-043) —
(1) `run_coherence_audit` trả ba trạng thái: `COHERENT` / `INCOHERENT` / `UNEVALUABLE`.
`0/7 có dấu` là `UNEVALUABLE`, và `UNEVALUABLE` là **blocker**, không phải pass.
(2) In tỉ lệ ngay cạnh con số ở mọi nơi công bố: `0 vi phạm / 0 trên 7 tệp kiểm được`.
(3) Áp cùng quy tắc cho ba bộ kiểm còn lại — đây là lần thứ tư, nên nó là quy ước dự án
chứ không phải một bản vá lẻ: **một bộ kiểm không được in con số vi phạm mà không in mẫu
số bên cạnh.**

---

## AQ-043 · Green Default — KHÔNG ĐỔI

**Issue:** `state_manager.write_state_atomic()` nuốt `ImportError` khi nạp `run_context`
và ghi state không dấu, im lặng.

**Severity:** HIGH

**Evidence:**

    scripts/state_manager.py:67-70
        except ImportError:
            # ... mất dấu lần chạy, không mất dữ liệu.
            pass

Không log, không cờ. Với AQ-044, một lần chạy mất dấu hoàn toàn sẽ **lọt** phép kiểm gắn
kết thay vì kích hoạt nó.

**Suggested Sprint:** Gộp vào SPRINT RUN-ISOLATION — ghi `run_scope: 'UNSTAMPED'` kèm lý
do vào chính tệp; gate coi `UNSTAMPED` là blocker.

---

## AQ-041 · Schema Drift — KHÔNG ĐỔI, vòng thứ năm

**Issue:** Ba số liệu sai, đo lại vòng này không con số nào thay đổi.

**Severity:** CRITICAL

**Evidence:**

    crypto score 100 · severity_breakdown tổng 0 · total_findings 19     (đúng: 90)
    assets vuln tổng 399   |   nessus_status.total 64                     (chênh 6.2 lần)
    hostname_source {unresolved: 11}  ·  attribution {FULL: 258, PARTIAL: 2}

**Suggested Sprint:** SPRINT SCHEMA-RECONCILE — ba bất biến so tổng (nêu từ vòng 7):
`sum(severity_breakdown) == total_findings` · `sum(assets[].vulnerability_count) ==
nessus.total` · `%FULL attribution <= %hostname đã phân giải`.

---

## AQ-042 · Deployment Truth — KHÔNG ĐỔI, vòng thứ tám

**Issue:** Portal được deploy vẫn không phải portal được sửa.

**Severity:** HIGH

**Evidence:**

    render.yaml:9            startCommand: node web-server.js
    package.json:7           "start": "node web/server.js"
    daily_brief/latest.html  2026-09-13            (hôm nay 14/09)
    HANDOFF.md  Commit ba86908  ·  Risk 6/100      (HEAD 484f00b · state 3)
    TECHNICAL_DEBT.md:25  | Số liệu giả trong pipeline Python | 0 |

Vòng này `web/app.js` lại được sửa (AQ-018, AQ-024) — sprint thứ **sáu** liên tiếp cải
thiện một tệp Render không phục vụ.

**Suggested Sprint:** SPRINT DEPLOY-TRUTH — chốt entrypoint, đưa bộ sinh brief HTML vào
pipeline, `generate_handoff.py` thành stage cuối, mẫu số cho `TECHNICAL_DEBT.md:25`.

---

## TỒN ĐỌNG SAU VÒNG 9

| Mục | Hạng | Tuổi |
|---|---|---|
| AQ-044 | CRITICAL | 🆕 `run_coherence_audit` báo `0 vi phạm` trên `0/7` tệp kiểm được |
| AQ-020 / AQ-041 | CRITICAL | ❌ 5 vòng |
| AQ-021 / AQ-041 | CRITICAL | ❌ 7 vòng |
| AQ-002 / AQ-041 | CRITICAL | ❌ 9 vòng |
| AQ-043 | HIGH | ❌ 2 vòng |
| AQ-007 / AQ-042 | HIGH | ❌ **8 vòng** |
| AQ-033 / AQ-037 | HIGH | ❌ 3 vòng |
| AQ-034 / AQ-038 | HIGH | ❌ 5 vòng |

**Đang mở: 8 (4 CRITICAL, 4 HIGH). Đã trả tích luỹ: 27.**

---

## NHẬN ĐỊNH VÒNG 9

Hai mục đóng, cả hai là sửa một dòng ở portal — đúng loại việc lẽ ra nên xong từ lâu.

Phát hiện chính vòng này là một mẫu lặp lại lần thứ tư. `run_coherence_audit.py` được
viết để phát hiện state pha trộn nhiều lần chạy, và nó báo `0 vi phạm` trong lúc chính
dòng phạm vi của nó nói không tệp nào có dấu để so. Cùng hình dạng với
`portal_field_audit` (29/122 → `0`) và `pipeline_field_audit` (107/617 → `0`).

Ba lần là trùng hợp; bốn lần là thói quen. Và lần này nó nằm **trong cổng merge**, đúng
chỗ mà AQ-013 vừa được sửa ở vòng 6 vì lý do y hệt — bộ phận quyết định ship không được
có tiêu chí không thể đỏ.

Cộng với AQ-043, hai mục tạo thành một đường liền: `run_context` không import được →
`state_manager` nuốt lỗi im lặng → mọi tệp mất dấu → `run_coherence_audit` báo `0 vi
phạm` → cổng xanh. Không bước nào trong chuỗi đó phát ra tiếng.

Về xu hướng: chín vòng, 27 mục đã trả — nhịp tốt. Nhưng ba mục CRITICAL của AQ-041 đã
đứng yên **5, 7 và 9 vòng**, và Deployment Truth **8 vòng**. Sáu sprint liên tiếp đã cải
thiện `web/app.js`; không sprint nào làm cho tệp đó được phục vụ. Các sprint vẫn chọn
việc theo độ mới thay vì theo tuổi nợ, và khoảng cách đang giãn ra chứ không thu lại.

**Thứ tự vòng tới:** AQ-044 + AQ-043 (một sprint, cùng cơ chế) → AQ-041 (ba bất biến) →
AQ-042/AQ-007 → AQ-037 → AQ-034.

---

*Vòng 9, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*


---
---

# VÒNG 10 — 2026-09-14 13:29 · commit `f0b8ba7` + working tree

HEAD `f0b8ba7` *"cut the incidents<->risk feedback loop, stamp every state file with its run"*.
Working tree: `render.yaml`, `web/server.js`, **`web-server.js` ĐÃ XOÁ**,
`scripts/deploy_truth_audit.py` (mới), 5 script daily_brief, `sprint_gate.py`.
Auditor READ ONLY.

---

## ĐÃ TRẢ

### AQ-007 / AQ-030 / AQ-042 ✅ — Deployment Truth, sau **8 vòng**

    render.yaml:  startCommand: npm start        (từng là `node web-server.js`)
    web-server.js: ĐÃ XOÁ
    web/server.js:279  app.get('/latest', ...)   — route không mất
    scripts/deploy_truth_audit.py (mới, nối vào gate)
      PHAM VI: render.yaml -> 'npm start' | package.json -> 'node web/server.js'
               | diem vao web/server.js | 5 route doi chieu
      TONG: 0 vi pham

Chỗ làm đúng nhất là **không ghi lại đường dẫn** trong `render.yaml`:

    # "Không ghi lại đường dẫn ở đây: ghi hai lần thì trôi lần nữa. `npm start`
    #  để `package.json` là chỗ duy nhất nói đâu là điểm vào."

Đó là chẩn đoán đúng gốc: vấn đề không phải giá trị sai, mà **hai nơi cùng khai một sự
thật**. Kiểm lại: `/latest` vẫn được phục vụ, không có route nào mất khi xoá server cũ.

### AQ-034 / AQ-038 ✅ — mẫu số đã có ở mọi hàng

`docs/project/TECHNICAL_DEBT.md` nay in:

    | Trường portal đọc từ state không tồn tại      | 0 / 28 truy cập soi được |
    | Trường Telegram đọc từ state không tồn tại    | 0 / 15 truy cập soi được |
    | Biểu thức innerHTML chưa escape               | 0 / 85 biểu thức trong sink |
    | `.get(khoá, mặc định)` bịa số trong Python    | 0 / 106 lời gọi lần được |
    | State cùng một lần chạy                       | 7 / 7 tệp có dấu |
    | Sự cố đang mở truy nguợc được về quan sát     | 1 / 1 |
    | Tuổi `tool_validation.json`                   | 5.2 giờ |

Không còn một con số `0` trần nào. Đây là mục đã nêu ở vòng 1, 4, 5, 8 và 9 — đóng trọn.

### AQ-040 ✅ lan truyền xong

    state/risk_score.json   run_id RUN-20260914T132454-cb565f   run_scope PIPELINE
    run_coherence_audit:    7/7 tệp có dấu, 1 sự cố truy nguợc được, 0 vi phạm

---

## AQ-045 · Risk Consistency · Truth Gap

**Issue:**
**82% điểm rủi ro hiện tại (18.0 / 22) đến từ 6 chỉ báo mà chính hệ thống đã đánh dấu
`suppressed: true`, `noise_class: ROUTINE_OS_ACTIVITY`.** Bộ lọc tiếng ồn chạy đúng; bộ
chấm rủi ro không đọc kết quả của nó.

**Severity:** CRITICAL

**Root Cause:**
`by_severity` được tổng kết **trước** khi lọc tiếng ồn, và `calculate_risk_score.py:275`
đọc đúng bảng tổng kết đó thay vì đọc mảng `indicators`:

    calculate_risk_score.py:155   # `by_severity` do stage trước tổng kết.
    calculate_risk_score.py:275   by_severity = data.get('by_severity') or {}

Đây là AQ-005 tái xuất ở một consumer khác. Vòng 6 đã sửa `correlation_engine.indicators()`
để lọc `suppressed`. Không ai sửa **nơi sinh ra `by_severity`**, nên mọi consumer đọc
bảng tổng kết vẫn thấy con số trước lọc — và bộ chấm rủi ro là một trong số đó.

Bản sửa AQ-019 ở vòng 6 hoạt động đúng: cả 6 chỉ báo đều được nhận ra là hoạt động nền
của Windows. Nhưng nhận ra rồi không dùng đến.

**Evidence:**

    state/hunting_lateral_movement.json  (run_id RUN-20260914T132454-cb565f)
      tổng 425   suppressed 199   kept 226

      by_severity CÔNG BỐ        : {'INFO': 419, 'HIGH': 6}
      by_severity nếu chỉ tính kept: {'INFO': 226}
      HIGH trong kept             : 0          <- KHÔNG CÓ chỉ báo HIGH nào sống sót

    Cả 6 chỉ báo HIGH:
      type        Explicit Credential Logon
      suppressed  True
      noise_class ROUTINE_OS_ACTIVITY
      scope       ['LOCAL_HOST']
      evidence chứa 'S-1-5-18' và 'localhost'

    state/risk_score.json
      threat_hunting  health 28   contribution 18.0   "lateral_movement: 0C/6H"
      overall_score   22

Phép tính: `health = 100 − 6 × 12 = 28` · `contribution = 0.25 × 72 = 18.0` ·
`18.0 / 22 = 82%`.

Nếu `by_severity` tính sau lọc: `health 100`, `contribution 0.0`, **Risk = 4**.

**Business Impact:**
Risk đã đi `10 → 3 → 22` trong một ngày trên một máy không đổi cấu hình, và lần này
nguyên nhân không phải nhiễu thu thập mà là **một lỗi nhất quán**: cứ mỗi lần chủ máy
đăng nhập vào tài khoản Microsoft, thêm một sự kiện 4648, thêm 12 điểm sức khoẻ bị trừ.
Điểm rủi ro tăng tuyến tính theo số lần người dùng đăng nhập vào máy của họ.

Nghiêm trọng hơn dạng cũ: trước đây bộ lọc không nhận ra chúng, nay nhận ra và vẫn tính.
Hệ thống có đủ thông tin để đúng và vẫn công bố sai — đúng mô tả trong commit message
của PR #42: *"the number then travels to portal, Telegram, reports and the debt table,
all showing the same wrong value consistently, and therefore convincingly."*

**Suggested Sprint:** SPRINT SUPPRESSED-AT-SOURCE —
(1) `by_severity` tính **sau** lọc tiếng ồn; giữ số trước lọc ở khoá riêng
(`by_severity_including_noise`) đúng kỷ luật `*_all` đã áp cho `average_score` ở AQ-001.
(2) `analyze_threat_hunting` đọc mảng `indicators` đã lọc, không đọc bảng tổng kết —
hoặc `by_severity` phải bảo đảm đã lọc, một trong hai, không để mơ hồ.
(3) Rà mọi consumer khác của `by_severity`: portal KPI, Telegram, daily brief.
(4) Bất biến trong gate: `sum(by_severity.values()) == len([i for i in indicators
if not i.suppressed])`. Bất biến này bắt được lớp lỗi ở mọi tệp hunting cùng lúc.

---

## AQ-044 · Green Default — chưa sửa cấu trúc

**Issue:**
`run_coherence_audit` nay báo `7/7 tệp có dấu, 0 vi phạm` — **nhưng vì dữ liệu đã lan
truyền, không phải vì mã đã sửa.** Không có trạng thái `UNEVALUABLE`.

**Severity:** HIGH *(hạ từ CRITICAL: mẫu số nay hiện trong `TECHNICAL_DEBT.md`)*

**Root Cause:**
`grep -n "UNEVALUABLE\|unevaluable" scripts/run_coherence_audit.py scripts/sprint_gate.py`
→ **không kết quả**. Nhánh "không đánh giá được" chưa tồn tại. Vòng 9 đo `0/7 → 0 vi
phạm`; vòng 10 đo `7/7 → 0 vi phạm`. Cùng một mã, hai đầu vào.

Theo đúng quy tắc bước 3 của vòng lặp này: **đây là "hôm nay dữ liệu khác", không phải
"đã sửa mã"** — nên mục ở lại.

**Evidence:**

    Vòng 9: PHAM VI 0/7 tep co dau lan chay  ->  TONG: 0 vi pham
    Vòng 10: PHAM VI 7/7 tep co dau lan chay ->  TONG: 0 vi pham

    UNEVALUABLE trong mã: không có

Giảm nhẹ có thật: `TECHNICAL_DEBT.md` nay in `7 / 7 tệp có dấu` cạnh kết quả, nên người
đọc thấy mẫu số. Nếu tụt về `0 / 7` thì bảng sẽ nói ra — con số không còn trần. Đó là lý
do hạ xuống HIGH.

Nhưng **cổng merge vẫn pass** ở trạng thái `0/7`, và với AQ-043 (`except ImportError:
pass`) thì đường từ hỏng-âm-thầm tới merge-được vẫn liền.

**Suggested Sprint:** SPRINT RUN-ISOLATION (phần cuối, gộp AQ-043) — ba trạng thái
`COHERENT` / `INCOHERENT` / `UNEVALUABLE`; `UNEVALUABLE` là blocker; `except ImportError`
ghi `run_scope: 'UNSTAMPED'` thay vì im lặng.

---

## AQ-041 · Schema Drift — KHÔNG ĐỔI, vòng thứ sáu

**Issue:** Ba số liệu sai, đo lại không con số nào thay đổi.

**Severity:** CRITICAL

**Evidence:**

    crypto score 100 · severity_breakdown tổng 0 · total_findings 19    (đúng: 90)
    assets vuln tổng 399   |   nessus_status.total 64                    (chênh 6.2 lần)
    hostname_source {unresolved: 11}  ·  attribution {FULL: 423, PARTIAL: 2}

Ghi chú: `TECHNICAL_DEBT.md` vòng này thêm bảy hàng mẫu số mới, không hàng nào chạm ba
số liệu này. Bộ kiểm đang phủ ngày càng rộng lớp lỗi *"đọc trường không tồn tại"* trong
khi ba lỗi *"hai lược đồ không khớp"* đứng yên từ vòng 3.

**Suggested Sprint:** SPRINT SCHEMA-RECONCILE — ba bất biến so tổng (nêu từ vòng 7), giờ
thêm bất biến thứ tư từ AQ-045: `sum(by_severity) == len(kept indicators)`. Bốn bất biến
cùng một hình dạng — **so tổng giữa nguồn và dẫn xuất** — nên chúng là một sprint, và là
lớp kiểm còn thiếu duy nhất trong bảng nợ.

---

## TỒN ĐỌNG SAU VÒNG 10

| Mục | Hạng | Tuổi |
|---|---|---|
| AQ-045 | CRITICAL | 🆕 82% điểm rủi ro từ 6 chỉ báo đã đánh dấu là tiếng ồn |
| AQ-020 / AQ-041 | CRITICAL | ❌ 6 vòng |
| AQ-021 / AQ-041 | CRITICAL | ❌ 8 vòng |
| AQ-002 / AQ-041 | CRITICAL | ❌ 10 vòng |
| AQ-044 | HIGH | 🔶 hạ từ CRITICAL; chưa có `UNEVALUABLE` |
| AQ-043 | HIGH | ❌ 3 vòng |
| AQ-033 / AQ-037 | HIGH | 🔶 HANDOFF `f0b8ba7` = HEAD; Risk 22 = 22 — **khớp lần đầu** |

**Đang mở: 6 (4 CRITICAL, 2–3 HIGH). Đã trả tích luỹ: 31.**

Ghi nhận AQ-037: `HANDOFF.md` vòng này khai `Commit f0b8ba7` = HEAD, `Risk 22/100` =
state. Lần đầu trong bảy vòng nó khớp. Nhưng `generate_handoff.py` vẫn chưa là stage của
pipeline, nên đây có thể lại là thời điểm chạy trùng nhau — giữ 🔶 tới khi thấy nó khớp
qua một lần merge nữa.

---

## NHẬN ĐỊNH VÒNG 10

Vòng tốt nhất từ đầu cuộc audit về khối lượng đóng: Deployment Truth sau **8 vòng**, và
mẫu số ở mọi hàng của bảng nợ sau **5 vòng** nhắc lại. Cả hai đều đóng đúng gốc —
`npm start` bỏ hẳn nguồn sự thật thứ hai thay vì sửa giá trị; bảng nợ không còn một con
số `0` trần nào.

Nhưng phát hiện chính vòng này là loại nguy hiểm nhất mà hàng đợi từng ghi: **hệ thống
đã có đủ thông tin để đúng, và vẫn công bố sai.**

Sáu chỉ báo 4648 được nhận diện chính xác là hoạt động nền của Windows —
`suppressed: true`, `noise_class: ROUTINE_OS_ACTIVITY`, `scope: LOCAL_HOST`. Bản sửa
AQ-019 ở vòng 6 làm đúng việc của nó. Nhưng `by_severity` được tổng kết **trước** khi
lọc, và bộ chấm rủi ro đọc bảng tổng kết đó. Kết quả: `health 28`, `contribution 18.0`,
**82% điểm rủi ro đến từ chính những bản ghi hệ thống đã gắn nhãn tiếng ồn.**

Hệ quả vận hành đáng nói: điểm rủi ro nay tăng **tuyến tính theo số lần chủ máy đăng
nhập vào tài khoản Microsoft của họ**. Không phải nhiễu như vòng 5 và 6 — đây là một lỗi
nhất quán, lặp lại được, và vì thế thuyết phục hơn nhiều.

Đây là AQ-005 tái xuất ở consumer khác: vòng 6 sửa `correlation_engine.indicators()`,
không ai sửa nơi **sinh ra** `by_severity`. Cùng hình dạng với AQ-014, nơi một lần đổi
khoá làm hỏng năm consumer và sprint sửa được một. Bài học đó đã được viết vào
`state_manager.py` ở vòng 8 (*"sửa từng script là cách đã chứng minh không scale"*) —
nhưng chưa được áp cho lớp tổng kết.

Và AQ-041 nay đã đứng yên 6, 8 và 10 vòng. Bảng nợ vòng này thêm **bảy** hàng mẫu số
mới; không hàng nào chạm ba số liệu đó. Bốn bất biến so tổng — gồm bất biến mới từ
AQ-045 — là lớp kiểm còn thiếu duy nhất, và là một sprint.

**Thứ tự vòng tới:** AQ-045 → AQ-041 (bốn bất biến, cùng sprint) → AQ-044 + AQ-043 →
AQ-037 (xác nhận qua một merge nữa).

---

*Vòng 10, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*


---
---

# VÒNG 11 — 2026-09-14 13:33 · ba commit mới, working tree sạch

HEAD `fc0441c`. Commit mới từ vòng 10: `671c6b4` (deploy), `6e61795` (schema),
`fc0441c` (handoff). Auditor READ ONLY.

---

## ĐÃ TRẢ

### AQ-020 ✅ — `crypto_score` không còn là hằng số

    state/crypto_inventory.json
      score               90        (từng bị ghim ở 100 qua nhiều sprint)
      severity_breakdown  {CRITICAL:0, HIGH:0, MEDIUM:2, LOW:0, INFO:17, UNKNOWN:0}
      tổng breakdown      19  ==  total_findings 19        <- bất biến đã khớp

    scripts/collect_crypto_inventory.py
      NESSUS_SEVERITY = {0:'INFO', 1:'LOW', 2:'MEDIUM', 3:'HIGH', 4:'CRITICAL'}
      # "Severity của Nessus -> nhãn. Không đọc được thì nói, không đoán."

Hai finding MEDIUM ẩn từ vòng 3 nay hiện ra, và điểm tụt từ 100 xuống đúng `100 − 2×5 = 90`.
Thêm ô `UNKNOWN` để giá trị không ánh xạ được không bị nuốt — đúng kỷ luật "vắng mặt
được khai báo".

### AQ-021 ✅ — và phát hiện của Auditor cần đính chính

`399 vs 64` **không phải hai tổng mâu thuẫn**. Đó là hai **đơn vị** khác nhau không được
gọi tên: 64 = số plugin phân biệt, 399 = số lượt trên 11 máy.

    state/nessus_status.json
      total            64
      total_unit       "distinct_plugins"
      distinct_plugins 64
      total_instances  399          <- khớp đúng tổng của assets.json

    docs/project/TECHNICAL_DEBT.md:28
      | Đơn vị lỗ hổng đối chiếu được | assets 399 luot | nessus 64 plugin, 399 luot |

Ghi nhận thẳng: vòng 3 tới vòng 10 tôi mô tả mục này là *"hai tổng mâu thuẫn, chênh 6.2
lần"*. Con số thì đúng, cách gọi thì không — không có tổng nào sai, có hai đơn vị không
nhãn. Bản chất lỗi vẫn là drift có thật (không ai đọc được tệp nào đang đếm gì, và Daily
Brief in cả hai cạnh nhau), nhưng **cách trả là đặt tên đơn vị, không phải đối chiếu lại
số**. Builder chẩn đoán đúng hơn mô tả trong hàng đợi.

### AQ-033 / AQ-037 ✅ — HANDOFF thôi khẳng định điều nó không biết

    | Commit lúc chạy | `6e61795` |
    | Cây làm việc    | CÓ THAY ĐỔI CHƯA COMMIT |

    "Cây làm việc có thay đổi chưa commit, nên commit ở trên là của sprint TRƯỚC;
     công của sprint này chưa có định danh. Đó là thứ tự đúng — cổng chạy trước
     khi commit — không phải một con số trễ."

    | Toàn vẹn bằng chứng | 0 vi phạm / 434 chỉ báo _(đo cách đây 5.3 giờ)_ |

Bản sửa nhắm vào **lời khẳng định**, không nhắm vào giá trị: đổi nhãn từ `Commit` thành
`Commit lúc chạy`, giải thích vì sao nó là commit trước, và đóng dấu tuổi lên hàng lấy
từ cache. Bảy vòng tôi báo "HANDOFF trễ một sprint"; câu trả lời đúng là nó **không thể**
biết commit của sprint đang chạy, và điều cần sửa là đừng vờ như biết.

---

## AQ-045 · Risk Consistency — KHÔNG ĐỔI, và đã định vị được dòng gây lỗi

**Issue:**
**78% điểm rủi ro (18.0 / 23) vẫn đến từ 6 chỉ báo mang `suppressed: true`,
`noise_class: ROUTINE_OS_ACTIVITY`.**

**Severity:** CRITICAL

**Root Cause (định vị chính xác vòng này):**

    scripts/hunt_lateral_movement.py:221-227
        'by_severity': {},
        ...
        output['by_severity'][sev] = output['by_severity'].get(sev, 0) + 1

`by_severity` được đếm trong **chính cuộc săn**, trên toàn bộ chỉ báo. Cuộc săn chạy ở
stage sớm; `ioc_quality.py` gắn cờ `suppressed` ở stage sau. Nên cuộc săn **không thể**
biết chỉ báo nào sẽ bị hạ xuống tiếng ồn — và không ai tính lại `by_severity` sau đó.

`calculate_risk_score.py:275` đọc bảng tổng kết trước lọc đó.

Đây không phải lỗi ở `analyze_threat_hunting`. Chỗ sửa là `ioc_quality.py`: sau khi gắn
cờ, nó phải ghi lại `by_severity` (đã lọc) và giữ số cũ ở `by_severity_including_noise`
— đúng khuôn `average_score` / `average_score_all` mà chính nó đã dùng ở AQ-001.

**Evidence:**

    state/hunting_lateral_movement.json (run_id đồng nhất, 7/7 tệp có dấu)
      tổng 426   suppressed 200   kept 226
      by_severity CÔNG BỐ          : {'INFO': 420, 'HIGH': 6}
      HIGH trong kept              : 0
      khoá liên quan có trong tệp  : chỉ `by_severity` — không có biến thể `*_all`

    state/risk_score.json
      threat_hunting  health 28   contribution 18.0   "lateral_movement: 0C/6H"
      overall_score   23

    18.0 / 23 = 78%.   Nếu tính sau lọc: health 100, contribution 0 -> Risk = 5.

**Suggested Sprint:** SPRINT SUPPRESSED-AT-SOURCE —
(1) `ioc_quality.py` ghi lại `by_severity` sau khi gắn cờ; số trước lọc chuyển sang
`by_severity_including_noise`.
(2) Bất biến trong gate: `sum(by_severity.values()) == len([i for i in indicators if not
i.suppressed])`. Bất biến này cùng hình dạng với hai bất biến vừa đóng AQ-020 và AQ-021 —
nên nó thuộc đúng sprint vừa chứng minh là hiệu quả.
(3) Rà consumer còn lại của `by_severity`: portal KPI, Telegram, daily brief.

---

## AQ-002 · Schema Drift — KHÔNG ĐỔI, vòng thứ mười một

**Issue:** `attribution_quality: FULL` trên **424 / 426** chỉ báo, trong khi **11/11** tài
sản có `hostname_source: unresolved`.

**Severity:** CRITICAL

**Root Cause:** `ioc_quality.py` chấm attribution bằng sự hiện diện của IP, không bằng
hostname đã phân giải. Bản vá hostname ở Sprint 17 áp phía tài sản, không nối sang phía
chỉ báo. Không đổi từ vòng 1.

**Evidence:**

    state/assets.json      hostname_source = {unresolved: 11}
    hunting_lateral_movement  attribution_quality = {FULL: 424, PARTIAL: 2}

    -> 99.5% chỉ báo khai "đã quy kết đầy đủ" trên một kho không máy nào có tên.

`docs/project/TECHNICAL_DEBT.md` đã ghi nhận nợ này ở bảng "nợ đã ghi nhận" (mục 2, cần
nguồn tên thật: DNS ngược / DHCP). Nhưng **nhãn `FULL` vẫn đang được phát ra** — nợ hạ
tầng không biện minh cho một nhãn chất lượng sai.

**Suggested Sprint:** SPRINT SCHEMA-RECONCILE (phần cuối) — bất biến thứ ba cùng hình
dạng: `%FULL attribution <= %assets có hostname_source != unresolved`. Với dữ liệu hôm
nay vế phải là 0%, nên mọi chỉ báo về máy ở xa phải là `PARTIAL`. Máy cục bộ là ngoại lệ
hợp lệ vì nó tự biết tên mình — và ngoại lệ đó phải khai rõ, không ngầm.

---

## AQ-044 · Green Default — KHÔNG ĐỔI cấu trúc

**Issue:** `run_coherence_audit` vẫn không có trạng thái `UNEVALUABLE`.

**Severity:** HIGH

**Evidence:** `grep -c UNEVALUABLE scripts/run_coherence_audit.py scripts/sprint_gate.py`
→ **0 và 0**. Vòng 9 đo `0/7 → 0 vi phạm`; vòng 10–11 đo `7/7 → 0 vi phạm`. Cùng mã, dữ
liệu khác.

**Suggested Sprint:** SPRINT RUN-ISOLATION (phần cuối, gộp AQ-043).

---

## AQ-043 · Green Default — KHÔNG ĐỔI

**Issue:** `state_manager.py:67-70` — `except ImportError: pass` bỏ dấu lần chạy im lặng.

**Severity:** HIGH

**Evidence:** Không đổi. Cùng AQ-044 tạo đường liền: import hỏng → mất dấu → coherence
báo `0 vi phạm` → cổng xanh.

**Suggested Sprint:** SPRINT RUN-ISOLATION — ghi `run_scope: 'UNSTAMPED'`; gate coi
`UNSTAMPED` và `UNEVALUABLE` là blocker.

---

## TỒN ĐỌNG SAU VÒNG 11

| Mục | Hạng | Tuổi |
|---|---|---|
| AQ-045 | CRITICAL | ❌ 2 vòng — 78% điểm rủi ro từ chỉ báo đã gắn nhãn tiếng ồn |
| AQ-002 | CRITICAL | ❌ **11 vòng** |
| AQ-044 | HIGH | ❌ 3 vòng |
| AQ-043 | HIGH | ❌ 4 vòng |

**Đang mở: 4 (2 CRITICAL, 2 HIGH). Đã trả tích luỹ: 34.**

---

## NHẬN ĐỊNH VÒNG 11

Ba mục đóng, và hai trong ba đóng theo cách đáng học.

**AQ-021** cho thấy hàng đợi này có thể mô tả sai một lỗi có thật. Tôi gọi nó là *"hai
tổng mâu thuẫn, chênh 6.2 lần"* suốt tám vòng. Không tổng nào sai — có hai đơn vị không
nhãn, và bản sửa đúng là đặt tên (`total_unit: distinct_plugins`, `total_instances: 399`)
chứ không phải đối chiếu lại số. Bằng chứng tôi đưa ra đúng; kết luận tôi rút ra thì
không hoàn toàn. Ghi ra đây để lần sau phân biệt "hai số khác nhau" với "hai câu hỏi
khác nhau" trước khi gọi là drift.

**AQ-037** đóng bằng cách sửa **lời khẳng định** thay vì giá trị. Bảy vòng tôi báo
"HANDOFF trễ một sprint". Câu trả lời đúng: nó *không thể* biết commit của sprint đang
chạy — cổng chạy trước khi commit — nên việc cần làm là đổi nhãn thành `Commit lúc chạy`
và nói ra lý do, cộng đóng dấu tuổi lên hàng lấy từ cache. Đó là cùng một kỷ luật đã
dùng cho `run_scope: STANDALONE` và `signature_status: NOT_IMPLEMENTED`: **khai vắng mặt,
đừng lấp.**

Còn lại bốn mục, và chúng chia làm hai cặp rõ ràng:

**AQ-045 + AQ-002** là hai bất biến so tổng cuối cùng. Sprint vừa rồi đã chứng minh hình
dạng này hiệu quả: `sum(severity_breakdown) == total_findings` đóng AQ-020 ngay, và việc
gọi tên đơn vị đóng AQ-021. Hai bất biến còn lại —
`sum(by_severity) == len(kept)` và `%FULL <= %hostname đã phân giải` — cùng khuôn, cùng
một sprint.

**AQ-043 + AQ-044** là một đường liền từ hỏng-âm-thầm tới merge-được, và cả hai là cùng
một quyết định: cơ chế `run_id` phải nói ra khi nó không hoạt động, ở cả hai đầu (nơi
ghi và nơi kiểm).

Hai sprint, bốn mục, và hàng đợi hết CRITICAL/HIGH. AQ-002 đã mở **11 vòng** — đây là
mục cũ nhất còn sống, và nay nó là một dòng bất biến chứ không còn là một bài toán hạ
tầng.

---

*Vòng 11, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*


---
---

# VÒNG 13 — 2026-09-14 13:43 · working tree mới (sprint đóng dấu tuổi)

HEAD vẫn `fc0441c`. Working tree đổi so với vòng 12: `scripts/tool_validator.py`,
`tests/sensor_coverage/test_coverage_refresh.py`, `state/sensor_coverage.json`,
`state/tool_validation.json`, `docs/project/TECHNICAL_DEBT.md`, `HANDOFF.md`.
Auditor READ ONLY.

---

## GHI NHẬN — bản sửa đúng chỗ, và phép kiểm đúng loại

`tool_validator.py` chuyển `stamp_freshness()` từ `main()` vào `sensor_coverage()`,
tức từ **nơi ghi** về **nơi tạo**. Lý do nêu trong mã đúng: `sprint_gate.py:86` gọi
thẳng `sensor_coverage()` rồi tự ghi tệp ở `:90`, nên đường `gate:full` trước đây sinh
ra tệp không dấu. Cùng bài học `write_state_atomic` (AQ-014).

Phép kiểm mới cũng đúng loại: nó gọi thẳng hàm tạo thay vì đọc tệp đã ghi — vì tệp
trên đĩa chỉ nói được về đường đi vừa chạy. Đó là phép kiểm bắt được *lớp* lỗi,
không phải bắt được *lần* lỗi.

**Nhưng chưa có bằng chứng bản sửa đã chạy.** `state/sensor_coverage.json` ghi lúc
`13:41:50`; `tool_validator.py` sửa lúc `13:42:48`. Tệp trên đĩa **thiếu cả bốn
trường** `probe_generated_at` / `tools_generated_at` / `freshness_note` /
`refreshed_by`. Đây là "dữ liệu cũ hơn mã", không phải bản sửa hỏng — nhưng nó có
nghĩa là mọi thứ đọc tệp đó lúc này (gate, HANDOFF, portal) vẫn đang đọc bản không
dấu, và `sprint_gate.py:182` lấp chỗ trống bằng `probe_generated_at or generated_at`
nên tuổi vẫn hiện `0.0 giờ` như thể có dấu.

---

## AQ-046 · Source of Truth Drift — MỚI

**Issue:**
Cùng một lần chạy cổng lúc `13:41:52`, `TECHNICAL_DEBT.md` kết luận
**"Đủ điều kiện merge: KHÔNG"**, còn `HANDOFF.md` — tệp được chỉ định là nguồn đọc
đầu tiên của mỗi phiên — **không hề nhắc rằng cổng đang chặn.**

**Severity:** CRITICAL

**Root Cause:**
`generate_handoff.py:133` in tiêu đề `## Cổng merge` rồi liệt kê PASS / EMPTY /
BLIND / FAIL, nhưng trong toàn tệp **không có** từ `merge` nào khác, không có
`blockers`, không có trường "đủ điều kiện". Tìm `merge|blocker|chặn` trên tệp sinh
trả về đúng **một** dòng — chính dòng tiêu đề. Kết luận của cổng nằm ở
`sprint_gate`, và chỉ `TECHNICAL_DEBT.md` in nó ra.

**Evidence:**

    docs/project/TECHNICAL_DEBT.md   (13:41:52)
      | Đủ điều kiện merge | **KHÔNG** |
      | Bộ kiểm phát hiện  | TRƯỢT     |
      ### Đang chặn
      - bo kiem phat hien truot (TONG: 337/340 dat)

    docs/project/HANDOFF.md          (13:41:52 — CÙNG lần chạy)
      ## Cổng merge
      | PASS  | 93 |
      | EMPTY | 6  |
      | BLIND | 0  |
      | FAIL  | 0  |
      (hết bảng — không có hàng nào nói cổng đang chặn)

      ## Việc tiếp theo
      3. `npm run gate` trước khi mở PR.

Một người đọc HANDOFF thấy bốn hàng, ba trong đó là `0`, và một lời khuyên chạy
cổng "trước khi mở PR" — trong khi cổng **vừa chạy và vừa trượt**.

**Business Impact:**
Đây là lỗi nguy hiểm nhất trong bảy trục, vì nó nằm ở tệp *đầu vào* của mọi phiên
làm việc. HANDOFF tự khai "mọi con số dưới đây đọc thẳng từ `state/` lúc chạy" và
"Đọc tệp này thay cho `AI_HANDOFF.md`/`SESSION_STATE.md`". Nó giữ lời về số, nhưng
bỏ mất **kết luận**. Một sprint đọc HANDOFF sẽ tin mình đang ở trạng thái ship được.

**Suggested Sprint:** SPRINT GATE-SINGLE-VOICE —
(1) `generate_handoff.py` in hàng `Đủ điều kiện merge` và khối `Đang chặn` từ cùng
kết quả `sprint_gate.evaluate()` mà `TECHNICAL_DEBT.md` dùng; không tự tính lại.
(2) Bất biến: hai tệp sinh trong cùng lần chạy phải khai cùng kết luận merge —
nếu một tệp không in được kết luận thì nó không được in bảng cổng.
(3) Khi chặn, `## Việc tiếp theo` phải mở đầu bằng blocker, không bằng lời khuyên
chạy cổng.

---

## AQ-047 · Risk Consistency — MỚI

**Issue:**
Hai năng lực phát hiện đang **blind**, và điều đó không chạm tới điểm rủi ro, không
sinh ra một lời rào nào. Risk vẫn `23/100 LOW`.

**Severity:** HIGH

**Root Cause:**
`calculate_risk_score.py` chỉ biết một loại mù: `coverage.observable` trong các tệp
`hunting_*.json` (dòng 262–323, 423–430). Nó **không đọc** `sensor_coverage.json`,
nên `detection_capabilities` — nơi duy nhất ghi nhận "nguồn mở nhưng thứ ta cần
không được ghi" — nằm ngoài tầm engine. Tìm trong `risk_score.json` các chuỗi
`blind` / `mù` / `coverage` / `Scheduled` / `USB`: **không chuỗi nào có mặt**.

**Evidence:**

    state/sensor_coverage.json
      summary            {'covered': 8, 'partial': 0, 'blind': 0}   <- theo NGUỒN
      capability_summary {'covered': 3, 'partial': 0, 'blind': 2}   <- theo NĂNG LỰC
      blind: Scheduled Task Execution, USB Device Activity

    state/risk_score.json
      overall_score 23   risk_level LOW
      notes: ["Thành phần `asset` dựa trên bản quét Nessus 163 giờ tuổi..."]
      -> lời rào duy nhất là về tuổi Nessus. Không lời nào về hai năng lực mù.

Đáng chú ý: nguồn `persistence` = **covered**, trong khi năng lực *Scheduled Task
Execution* = **blind**. Mã đã tự nói rõ hai cột này trả lời hai câu khác nhau
(`tool_validator.py:709-712`) — nhưng `HANDOFF.md:46-60` in cả hai vào **một** cột
tên `Trạng thái`, và dùng lại chữ `blind` mà dòng 26 vừa dùng để chỉ một thứ khác
(`| BLIND | 0 |` là tool-BLIND). Cùng hình dạng AQ-021: hai câu hỏi, một nhãn.

**Business Impact:**
Scheduled Task là một trong những kỹ thuật duy trì phổ biến nhất. Hệ thống công bố
`persistence: covered` và `Risk LOW` trên một máy mà nó **không thấy** tác vụ định
kỳ. Đây đúng loại lỗi mà kỷ luật `points_available` sinh ra để chặn: thành phần
không quan sát được phải rời **cả tử số lẫn mẫu số**, chứ không được im lặng tính
là an toàn.

**Suggested Sprint:** SPRINT COVERAGE-INTO-RISK —
(1) `calculate_risk_score.py` đọc `capability_summary`; mỗi năng lực `blind` rút
trọng số của thành phần tương ứng khỏi `weight_available` và sinh một dòng `notes`
nêu tên năng lực.
(2) Giữ `risk_level` không được xuống `LOW` khi còn năng lực mù — cùng cơ chế sàn
đã dùng cho CRITICAL.
(3) `HANDOFF.md` tách hai bảng và đặt tên khác nhau: `mù nguồn` / `mù năng lực`;
không dùng lại chữ `BLIND` cho hai phép đếm khác đơn vị.

---

## BỐN MỤC CŨ — KHÔNG ĐỔI

`git diff --stat HEAD` trên `ioc_quality.py`, `state_manager.py`,
`run_coherence_audit.py`, `hunt_lateral_movement.py` → **rỗng**. Không tệp nào được sửa.

| Mục | Đo lại vòng 13 |
|---|---|
| **AQ-045** CRITICAL | `by_severity {INFO 420, HIGH 6}` · kept 226 · HIGH trong kept **0** · Risk 23, threat_hunting health 28 |
| **AQ-002** CRITICAL | `attribution {FULL 424, PARTIAL 2}` · `hostname_source {unresolved: 11}` |
| **AQ-043** HIGH | `except ImportError` trong `state_manager.py`: 1 |
| **AQ-044** HIGH | `UNEVALUABLE` trong `run_coherence_audit.py`: 0 |

---

## TỒN ĐỌNG SAU VÒNG 13

| Mục | Hạng | Tuổi |
|---|---|---|
| AQ-046 | CRITICAL | 🆕 HANDOFF im lặng trong khi cổng đang chặn |
| AQ-045 | CRITICAL | ❌ 4 vòng |
| AQ-002 | CRITICAL | ❌ **13 vòng** |
| AQ-047 | HIGH | 🆕 hai năng lực mù không chạm tới Risk |
| AQ-044 | HIGH | ❌ 5 vòng |
| AQ-043 | HIGH | ❌ 6 vòng |

**Đang mở: 6 (3 CRITICAL, 3 HIGH). Đã trả tích luỹ: 34.**

---

## NHẬN ĐỊNH VÒNG 13

Sprint này sửa đúng thứ nó nhắm: dấu tuổi chuyển về cửa tạo, và phép kiểm gọi thẳng
hàm tạo thay vì đọc tệp. Đó là cách viết kiểm bắt được lớp lỗi. Ghi nhận.

Nhưng chính lần chạy cổng ấy phơi ra hai chỗ hở lớn hơn, và cả hai cùng một bản
chất: **kết luận không đi cùng số liệu.**

`TECHNICAL_DEBT.md` nói "KHÔNG merge được"; `HANDOFF.md`, sinh cùng giây, in bốn
con số đẹp và khuyên "chạy cổng trước khi mở PR". Không tệp nào nói dối về một con
số — tệp thứ hai chỉ đơn giản không mang theo câu trả lời. Mười ba vòng qua hàng
đợi này đã đóng nhiều mục bằng cách **khai vắng mặt thay vì lấp** (`run_scope:
STANDALONE`, `signature_status: NOT_IMPLEMENTED`, `Commit lúc chạy`). AQ-046 là mặt
còn lại của cùng kỷ luật: **khai kết luận, đừng chỉ khai số.**

AQ-047 cũng vậy. `sensor_coverage.json` đã làm đúng phần khó — nó tách "nguồn có mở
không" khỏi "thứ ta cần có được ghi không", và nói thẳng hai năng lực đang mù. Rồi
không ai đọc. Engine rủi ro chỉ biết một loại mù, HANDOFF gộp hai cột thành một, và
đầu ra cuối cùng là `LOW`. Sự thật được đo, được ghi, và bị bỏ lại trong tệp.

Ba sprint là hết hàng đợi: **GATE-SINGLE-VOICE** (AQ-046) · **COVERAGE-INTO-RISK**
(AQ-047, cùng họ với AQ-045 vì cả hai là "điểm rủi ro đọc sai bảng tổng kết") ·
**RUN-ISOLATION** (AQ-043 + AQ-044). AQ-002 vẫn là mục cũ nhất — **13 vòng** — và
vẫn chỉ cần một dòng bất biến.

---

*Vòng 13, CHIEF AUDITOR 2026-09-14. LOOP MODE. Read-only.*

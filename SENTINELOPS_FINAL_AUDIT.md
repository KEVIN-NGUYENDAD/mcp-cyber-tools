# SENTINELOPS_FINAL_AUDIT.md

Biên soạn 2026-09-04. Chỉ đọc và phân tích — không sửa code, không
sửa file khác, không tạo file nào ngoài file này. Bằng chứng: toàn bộ
`docs/*.md`, `PROJECT_STATUS.md`, `NEXT_STEPS.md`,
`ARCHITECTURE_SUMMARY.md`, `SENTINELOPS_DISCOVERY_TIMELINE.md`,
`SENTINELOPS_DEEP_CONTEXT.md`, `DOMAIN_AND_VNETWORK_ASSESSMENT.md`,
số liệu `wc -lw` thực tế đo được phiên này, và toàn bộ repo/DNS/HTTP
evidence đã thu thập trong các lần kiểm toán trước.

**Lưu ý bắt buộc:** `HANDOFF.md` được nhắc đến trong yêu cầu **không
tồn tại** trong repo (`ls HANDOFF.md` → "No such file or directory").
Không suy đoán nội dung file này — chỉ ghi nhận nó không tồn tại.

---

# PHẦN 1 — KIỂM TOÁN TOKEN

## Số liệu thực đo (không ước lượng)

| File | Dòng | Từ | Ghi chú |
|---|---|---|---|
| `PROJECT_STATUS.md` | 633 | 3,741 | |
| `NEXT_STEPS.md` | 111 | 758 | |
| `ARCHITECTURE_SUMMARY.md` | 759 | 6,017 | |
| `SENTINELOPS_DISCOVERY_TIMELINE.md` | 384 | 2,165 | |
| `SENTINELOPS_DEEP_CONTEXT.md` | 1,301 | 9,102 | File lớn nhất |
| `DOMAIN_AND_VNETWORK_ASSESSMENT.md` | 517 | 4,016 | |
| **Tổng root** | **3,705** | **25,799** | |
| `docs/HOME_SOC_SOURCE_DISCOVERY.md` | 113 | 679 | |
| `docs/MVP2_REAL_ALERT_SOURCE.md` | 119 | 553 | |
| `docs/MVP3_WAZUH_INVESTIGATION.md` | 96 | 542 | |
| `docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` | 205 | 1,419 | |
| `docs/MVP_NOTIFICATION_FLOW.md` | 97 | 416 | |
| `docs/VNETWORK_API_DISCOVERY.md` | 225 | 1,902 | |
| `docs/VNETWORK_CAPABILITY_ASSESSMENT.md` | 496 | 3,036 | |
| `docs/VNETWORK_PRODUCT_DISCOVERY.md` | 180 | 1,243 | |
| `docs/WAAP_LOG_SEARCH_SCHEMA.md` | 656 | 4,255 | |
| **Tổng docs/** | **2,187** | **14,045** | |
| **TỔNG TOÀN BỘ** | **5,892** | **39,844** | ≈ 52,000–55,000 token nếu một AI đọc toàn bộ (quy đổi ~1.3 token/từ cho văn bản kỹ thuật tiếng Anh) |

## File nào quan trọng nhất

- **`WAAP_LOG_SEARCH_SCHEMA.md`** — không thể thay thế. Đây là nơi
  duy nhất chứa schema request/response nguyên văn, payload mẫu, và
  toàn bộ chuỗi xác minh trực tiếp (§7–§8). Không file nào khác có
  thông tin này ở mức chi tiết tương đương.
- **`DOMAIN_AND_VNETWORK_ASSESSMENT.md`** — không thể thay thế, vì
  chứa bằng chứng DNS/HTTP sống thu thập trực tiếp phiên này (phát
  hiện `www.sentinelops.fyi` không đi qua VNETWORK) — **chưa từng
  xuất hiện ở bất kỳ file nào khác**, kể cả `SENTINELOPS_DEEP_CONTEXT.md`
  (file này được viết **trước** phát hiện DNS, nên đã lỗi thời một
  phần — xem Phần 2).
- **`NEXT_STEPS.md`** — nhỏ (758 từ) nhưng là file duy nhất mang tính
  "hướng tới tương lai," không chỉ tường thuật lịch sử.
- **`PROJECT_STATUS.md`** — là sổ nhật ký theo trình tự thời gian duy
  nhất ghi lại đầy đủ diễn biến (kể cả việc tự sửa sai — ví dụ mục
  "Root Cause Identified" bị chính mục "Post-Onboarding
  Re-Verification" ngay sau đó điều chỉnh lại). Giá trị nằm ở tính
  trung thực theo trình tự, không phải ở việc không trùng lặp.

## File nào bị trùng lặp

Đây là phát hiện lớn nhất của Phần 1: **cùng một chuỗi sự kiện
VNETWORK/WAAP đã được thuật lại toàn bộ hoặc một phần ở tối thiểu
10 file khác nhau** — `VNETWORK_API_DISCOVERY.md`,
`VNETWORK_PRODUCT_DISCOVERY.md`, `VNETWORK_CAPABILITY_ASSESSMENT.md`,
`WAAP_LOG_SEARCH_SCHEMA.md`, `PROJECT_STATUS.md` (5 mục riêng),
`NEXT_STEPS.md`, `ARCHITECTURE_SUMMARY.md` (§9–§10),
`SENTINELOPS_DISCOVERY_TIMELINE.md` (Phase 3–10),
`SENTINELOPS_DEEP_CONTEXT.md` (§8–§9),
`DOMAIN_AND_VNETWORK_ASSESSMENT.md` (§3–§5). Một AI đọc toàn bộ
"39,844 từ" ở trên thực chất đọc phần lõi WAAP/VNETWORK **nhiều lần
lặp lại**, không phải 39,844 từ thông tin riêng biệt.

Cụ thể:
- `SENTINELOPS_DISCOVERY_TIMELINE.md` (2,165 từ) **gần như trùng
  hoàn toàn** với nội dung đã có trong `PROJECT_STATUS.md` +
  `docs/*.md` — giá trị riêng duy nhất là cách trình bày theo "Phase"
  và sơ đồ phụ thuộc, không có sự kiện/bằng chứng mới nào.
- `VNETWORK_API_DISCOVERY.md`, `VNETWORK_PRODUCT_DISCOVERY.md`,
  `VNETWORK_CAPABILITY_ASSESSMENT.md` (tổng 6,181 từ) — kết luận của
  cả ba đã được gộp và cô đọng lại đầy đủ trong
  `DOMAIN_AND_VNETWORK_ASSESSMENT.md` §3 (VNETWORK Inventory) và
  `WAAP_LOG_SEARCH_SCHEMA.md`.

## File nào nên gộp

- `SENTINELOPS_DISCOVERY_TIMELINE.md` nên được gộp trở lại vào
  `PROJECT_STATUS.md` (hoặc archive hoàn toàn) — không mang thông
  tin nào PROJECT_STATUS.md chưa có.

## File nào nên archive

- `docs/VNETWORK_API_DISCOVERY.md`, `docs/VNETWORK_PRODUCT_DISCOVERY.md`,
  `docs/VNETWORK_CAPABILITY_ASSESSMENT.md` — giữ lại vì lý do lịch sử
  (git history), nhưng **không nên đưa vào ngữ cảnh mặc định cho AI
  nữa** — mọi kết luận của cả ba đã có trong
  `DOMAIN_AND_VNETWORK_ASSESSMENT.md` §3–§4.
- `docs/MVP2_REAL_ALERT_SOURCE.md`, `docs/MVP_NOTIFICATION_FLOW.md` —
  **không nên archive** dù nhỏ (416–553 từ): đây là hai file **duy
  nhất** ghi chi tiết MVP #1/#2 — `PROJECT_STATUS.md` chỉ liệt kê
  chúng trong danh sách "Completed," không thuật lại chi tiết. Giữ
  lại, chi phí token thấp, giá trị thay thế bằng không.

## Bộ tài liệu tối thiểu để AI hiểu 100% SentinelOps

| # | File | Từ | Lý do bắt buộc |
|---|---|---|---|
| 1 | `NEXT_STEPS.md` | 758 | Ưu tiên hiện tại |
| 2 | `PROJECT_STATUS.md` | 3,741 | Sổ nhật ký trình tự thời gian, kể cả tự sửa sai |
| 3 | `SENTINELOPS_DEEP_CONTEXT.md` | 9,102 | Tổng hợp mật độ cao nhất — nhưng **cần cập nhật** phát hiện domain DNS (Phần 2) |
| 4 | `DOMAIN_AND_VNETWORK_ASSESSMENT.md` | 4,016 | Bằng chứng DNS/HTTP mới nhất, không thể thay thế |
| 5 | `docs/WAAP_LOG_SEARCH_SCHEMA.md` | 4,255 | Schema/payload nguyên văn — bắt buộc nếu build tích hợp |

**Tổng bộ tối thiểu: 21,872 từ (≈ 29,000 token) — giảm ~45% so với
đọc toàn bộ 39,844 từ**, mà không mất bất kỳ sự kiện hay bằng chứng
nào (chỉ mất phần trùng lặp).

---

# PHẦN 2 — KIỂM TOÁN TRI THỨC

"Những gì Claude biết nhưng Copilot chưa biết" — tức là: kiến thức
**chỉ tồn tại** trong `SENTINELOPS_DEEP_CONTEXT.md` và
`DOMAIN_AND_VNETWORK_ASSESSMENT.md` (hai file mới nhất), và **sẽ bị
bỏ lỡ** nếu Copilot chỉ đọc bốn file cũ hơn
(`PROJECT_STATUS.md`/`NEXT_STEPS.md`/`ARCHITECTURE_SUMMARY.md`/
`SENTINELOPS_DISCOVERY_TIMELINE.md`).

**Home-SOC:**
- `security-watch.js` và `export-home-soc-reports.js` — hai script
  chịu trách nhiệm chính — **không tồn tại trong local checkout đã
  review**, chỉ output của chúng được xác nhận. Chỉ ghi trong
  `SENTINELOPS_DEEP_CONTEXT.md` §5/§17.
- Có hai pipeline Home-SOC hoàn toàn khác nhau dưới cùng một tên, một
  cái dormant (`home-soc-state`, từ 2026-08-29).

**MCP:**
- `server_v2.js`/`server_backup_v1.js` — trùng byte-for-byte, không
  được tham chiếu ở bất kỳ đâu — chỉ ghi trong `SENTINELOPS_DEEP_CONTEXT.md` §6.
- Script tạo incident **không chạy qua MCP** — là hai code path tách
  biệt hoàn toàn, dù cùng nằm trong một repo.

**Incident Pipeline:**
- `sentinelops-security-incidents` — repo rỗng, tên gây hiểu nhầm là
  đích đến thật của incident. Đích thật là GitHub Issues trên chính
  `mcp-cyber-tools`.

**WAAP — đây là khoảng trống lớn nhất và mới nhất:**
- **`PROJECT_STATUS.md` và `NEXT_STEPS.md` — hai file mà một AI mới
  thường đọc đầu tiên — CHƯA HỀ được cập nhật với phát hiện DNS quan
  trọng nhất: `www.sentinelops.fyi` (domain đã WAAP-onboard, Service
  ID `95743`) không hề đi qua mạng VNETWORK — nó redirect 301 về
  domain gốc qua Cloudflare/Render.** Phát hiện này chỉ tồn tại trong
  `DOMAIN_AND_VNETWORK_ASSESSMENT.md`. Ngay cả `SENTINELOPS_DEEP_CONTEXT.md`
  §8 (viết trước phát hiện DNS) vẫn chỉ liệt kê "account/token scope
  mismatch" là giả thuyết hàng đầu, **không có** phát hiện DNS mới
  hơn — nghĩa là **chính tài liệu tổng hợp toàn diện nhất của dự án
  cũng đã lỗi thời** trên đúng điểm quan trọng nhất.

**VNETWORK:**
- Gap `{{URL}}` trong bộ Postman collection công khai của VNETWORK (3
  trong 106 endpoint dùng biến chưa xác định) — chỉ ghi trong
  `WAAP_LOG_SEARCH_SCHEMA.md` §7.1.
- Chỉ có **một** Service ID từng được quan sát (`95743`), và nó gắn
  với domain không hoạt động — chỉ ghi trong
  `DOMAIN_AND_VNETWORK_ASSESSMENT.md`.

**Domain:**
- `soc.sentinelops.fyi` và `mcp.sentinelops.fyi` — xuất hiện trong
  `content.js` nhưng trỏ về trang parking mặc định của Porkbun, không
  có dịch vụ thật. Phát hiện hoàn toàn mới, chưa từng có ở bất kỳ tài
  liệu nào trước `DOMAIN_AND_VNETWORK_ASSESSMENT.md`.
- Porkbun là nhà đăng ký/DNS/email thật của toàn bộ domain — chưa
  từng được ghi nhận trước phiên kiểm toán domain.

**GitHub Workflow:**
- Thư mục gốc `mcp-cyber-tools` còn chứa một sáng kiến hoàn toàn khác,
  không liên quan (`EXECUTION_DISCIPLINE.md`, `BUG_TRACKER.md`, các
  file TIER/QA — một sprint "v1.0.2 QA phase" riêng biệt, có quy tắc
  "NO SCOPE CHANGES" riêng). Một AI mới có thể nhầm quy tắc này vẫn
  đang áp dụng cho công việc WAAP hiện tại. Chỉ ghi trong
  `SENTINELOPS_DEEP_CONTEXT.md` §17.

---

# PHẦN 3 — KIỂM TOÁN DOMAIN

| Domain | Đang chạy thật? | Chưa tồn tại? | Chỉ xuất hiện trên website? |
|---|---|---|---|
| `sentinelops.fyi` | **Có** — `200 OK`, Cloudflare→Render, nội dung thật | — | — |
| `www.sentinelops.fyi` | Có DNS/HTTP hoạt động, nhưng **chỉ là redirect 301** về domain gốc — không phải dịch vụ độc lập | — | — |
| `audit.sentinelops.fyi` | **Có** — `200 OK`, thật sự đi qua VNETWORK edge, backend Render chưa xác định chủ sở hữu | — | — |
| `soc.sentinelops.fyi` | Không | **Chưa từng được build** — chỉ trỏ về trang parking Porkbun | **Có** — chỉ là nhãn "Home-SOC Dashboard" trong `content.js`, không có `href` |
| `mcp.sentinelops.fyi` | Không | **Chưa từng được build** — giống hệt `soc.` | **Có** — nhãn "MCP Portal," không có `href` |

**ROI cao nhất:** `audit.sentinelops.fyi` — là domain duy nhất vừa
thật, vừa đi qua VNETWORK, vừa là mục tiêu chính thức của cả kế hoạch
WAAP lẫn kế hoạch Healthcheck webhook. Chi phí để khai thác thêm gần
như bằng không (chỉ cần xác nhận chủ sở hữu backend và Service ID
VNETWORK thật của nó — không cần hạ tầng mới).

---

# PHẦN 4 — KIỂM TOÁN VNETWORK

**Đã được chứng minh (bằng chứng trực tiếp, không suy đoán):**
- Token API còn hiệu lực, xác thực được (lỗi có cấu trúc riêng theo
  từng sản phẩm, không phải lỗi đồng nhất).
- Schema request/response của `bsearch` đúng và hợp lệ — chưa từng
  bị từ chối vì sai định dạng (`400`).
- `audit.sentinelops.fyi` thật sự đi qua hạ tầng edge của VNETWORK
  (xác nhận DNS hai lần, hai thời điểm khác nhau).
- `www.sentinelops.fyi` — domain duy nhất từng được WAAP-onboard
  (Service ID `95743`) — **không hề đi qua mạng VNETWORK ở bất kỳ
  bước DNS nào.**
- Truy cập bị từ chối giống hệt nhau trên Compute (`403`), CDN
  (`404`), WAAP (`401`) — lặp lại qua hai token khác nhau và trước/sau
  khi hoàn tất onboarding.
- Có lỗ hổng thật trong Postman collection công khai của VNETWORK
  (biến `{{URL}}` chưa xác định trên 3/106 endpoint).

**Chỉ là giả thuyết (chưa được xác minh độc lập bởi công cụ của dự
án):**
- `audit.sentinelops.fyi` có thật sự đang bật rule WAF/mitigation hay
  không — DNS/HTTP chỉ chứng minh việc định tuyến qua VNETWORK, không
  chứng minh rule đang thực thi.
- Các con số cụ thể trong `wafCaseStudy` và Threat Report #001 (100%
  traffic, 0 direct-to-origin, 6 request bị chặn) — chưa từng được
  project tự tạo ra hay xác minh lại qua API.
- Giả thuyết "account/token scope mismatch" là nguyên nhân duy nhất —
  không loại trừ khả năng nguyên nhân domain-DNS (đã chứng minh) và
  nguyên nhân entitlement tài khoản (chưa chứng minh) cùng tồn tại
  song song.

**Chưa điều tra:**
- Certificates (sản phẩm quản lý chứng chỉ SSL/TLS thật, chưa từng
  gọi thử).
- Multi-CDN Orchestration (metrics API đã xác nhận tồn tại, chưa từng
  gọi thử).
- Object Storage (dùng credential hoàn toàn khác — Access Key/Secret
  — chưa từng được lấy).
- "Web Application Firewall" (mục nav tách biệt với "WAAP" trong docs
  VNETWORK) — chưa xác định là sản phẩm riêng hay chỉ là alias.
- Partner Portal — chưa bao giờ truy cập được trực tiếp bằng công cụ
  của dự án; mọi thông tin portal đều do Kevin tự kiểm tra và báo lại.

---

# PHẦN 5 — KIỂM TOÁN NGÔN NGỮ

Giả định: chuyển SentinelOps sang "Tiếng Việt là ngôn ngữ chính."

**Lợi ích:**
- Tác giả viết thoải mái hơn bằng tiếng mẹ đẻ.
- VNETWORK (nhà cung cấp) có gốc Việt Nam — bằng chứng: giá trị mặc
  định `"time_zone": "Asia/Saigon"` trong chính request template của
  `bsearch` (`docs/WAAP_LOG_SEARCH_SCHEMA.md` §5) — giao tiếp
  support/portal bằng tiếng Việt có thể thuận lợi hơn.
- Đã có tiền lệ code song ngữ tự nhiên: comment tiếng Việt xuất hiện
  sẵn trong `network-security-audit-frontend/backend/app.py`
  ("Quét cổng mở trên thiết bị") và
  `cybersecurity-labs/utils.py` ("Đọc file trong repo để agent phân
  tích") — cho thấy việc trộn ngôn ngữ trong code không phải điều xa
  lạ với tác giả.

**Rủi ro:**
- Toàn bộ portfolio công khai hiện tại là **100% tiếng Anh** —
  `content.js`, README của mọi repo đã kiểm tra, GitHub profile,
  LinkedIn. Chuyển ngôn ngữ chính sẽ phá vỡ tính nhất quán này.
- `profile.summary` hiện ghi rõ bằng tiếng Anh "I'm a cybersecurity
  student..." — không có bằng chứng nào trong repo giới hạn đối
  tượng tuyển dụng chỉ ở Việt Nam; ngược lại, `role`: "Building an AI
  Security Operations Platform" và `LinkedIn` là các tín hiệu hướng
  tới thị trường tuyển dụng quốc tế.
- Đã có ~39,844 từ tài liệu discovery bằng tiếng Anh (Phần 1) — dịch
  lại toàn bộ là khối lượng công việc rất lớn.
- **Nếu dịch song song mọi tài liệu (giữ cả hai bản Anh + Việt) sẽ
  trực tiếp làm trầm trọng thêm vấn đề "lãng phí token" đã nêu ở Phần
  1** — gần như nhân đôi kích thước bộ tài liệu.

**Ảnh hưởng tới AI:** tài liệu kỹ thuật bảo mật bằng tiếng Anh thường
được các công cụ AI (kể cả Claude, Copilot) xử lý chính xác hơn — bản
thân API docs của chính VNETWORK (bộ Postman collection đã đọc toàn
bộ trong `WAAP_LOG_SEARCH_SCHEMA.md`) cũng viết 100% bằng tiếng Anh,
kể cả với origin Việt Nam của nhà cung cấp. Thuật ngữ ngành (WAF, IOC,
CVE, entitlement...) là tiếng Anh chuẩn ngành; dịch sang tiếng Việt có
nguy cơ gây mơ hồ thuật ngữ.

**Ảnh hưởng tới tuyển dụng:** thu hẹp đáng kể phạm vi nếu chuyển hẳn
sang tiếng Việt, đi ngược lại chính mục tiêu đã nêu trong "Real
Mission" (portfolio chứng minh kỹ năng cho nhà tuyển dụng, không giới
hạn địa lý theo bằng chứng hiện có).

**Ảnh hưởng tới GitHub:** mọi issue/label/comment tự động do pipeline
tạo ra hiện là tiếng Anh (`build_issue()`, `build_analysis_comment()`
— xem `SENTINELOPS_DEEP_CONTEXT.md` §7); chuyển ngôn ngữ đòi hỏi sửa
cả code sinh nội dung, không chỉ tài liệu.

**Ảnh hưởng tới documentation:** dịch toàn bộ kho tài liệu discovery
hiện có là chi phí rất lớn so với lợi ích, và **mâu thuẫn trực tiếp**
với khuyến nghị "giảm trùng lặp token" đã đưa ra ở Phần 1 nếu làm
song song hai bản.

**Đề xuất: Song ngữ có chọn lọc — không phải dịch toàn bộ.**
- Giữ **100% tiếng Anh** cho: mã nguồn, tên biến, toàn bộ tài liệu
  discovery kỹ thuật (`docs/*.md`, `PROJECT_STATUS.md`, v.v.), và
  trang portfolio công khai `sentinelops.fyi` — vì đối tượng đã xác
  định là tuyển dụng quốc tế.
- Cho phép tiếng Việt tự nhiên ở: giao tiếp trực tiếp với VNETWORK
  (đã là ngôn ngữ của nhà cung cấp), ghi chú cá nhân không công khai.
- **Không nên chọn "100% tiếng Việt"** — mâu thuẫn trực tiếp với mục
  tiêu tuyển dụng quốc tế đã thể hiện rõ trong chính nội dung repo, và
  tạo chi phí dịch thuật rất lớn cho lợi ích không rõ ràng.
- **Không nên chọn "song ngữ đầy đủ" (dịch trùng mọi tài liệu)** — sẽ
  làm trầm trọng thêm chính vấn đề lãng phí token đã xác định ở
  Phần 1.

---

# PHẦN 6 — SỰ THẬT CUỐI CÙNG

Chỉ dựa trên code, repo, discovery, evidence — không dựa trên
marketing hay nội dung website.

## 1. Trạng thái hiện tại

SentinelOps là một hệ thống kỹ thuật **có thật, đang hoạt động ở quy
mô nhỏ**: pipeline cảnh báo → GitHub incident (Windows Defender +
`security-watch.js`) đã được build và xác minh với sự kiện thật (Issue
#6, `PROJECT_STATUS.md`), đóng băng milestone từ 2026-09-04. Song song
đó là một track nghiên cứu VNETWORK/WAAP được thiết kế đầy đủ nhưng
**chưa hoạt động được một lần nào** qua API thật. Trang portfolio công
khai đưa ra nhiều tuyên bố cụ thể (Wazuh SIEM, cảm biến Suricata/Zeek,
honeypot, "100%" audit coverage) mà chính các tài liệu discovery của
dự án này đã trực tiếp bác bỏ hoặc không thể xác minh.

## 2. Điểm mạnh nhất

**Kỷ luật "xác minh trước khi xây dựng."** Đây không phải một lần
tình cờ — nó lặp lại nhất quán qua hơn 10 cuộc điều tra độc lập: kiểm
tra Wazuh bằng nhiều phương pháp thay vì giả định; kiểm tra DNS/HTTP
thật cho cả hai domain thay vì suy luận từ tên; xoay vòng token ngay
khi bị lộ và kiểm tra lại trước khi tin; và quan trọng nhất — kiểm tra
lại sau khi hoàn tất WAAP onboarding thay vì giả định đã sửa xong, và
chính bước kiểm tra lại đó phát hiện ra việc "sửa" không hề có tác
dụng. Đây là năng lực kỹ thuật đáng tin cậy nhất của toàn bộ dự án.

## 3. Điểm yếu nhất

**Khoảng cách giữa những gì đã chứng minh được và những gì đang được
công bố công khai.** Trang `sentinelops.fyi` — chính là sản phẩm cốt
lõi để chứng minh năng lực thật — lại chứa các tuyên bố cụ thể mà
chính dự án đã tự tay bác bỏ (Wazuh không tồn tại, Suricata không tồn
tại, TheWall thực chất là game Godot xác nhận qua `gh api`) hoặc chưa
từng xác minh được (Threat Report #001, các subdomain `soc.`/`mcp.`
chỉ là trang parking). Điều này làm suy yếu chính giá trị cốt lõi mà
dự án tồn tại để chứng minh: "thật, không phải mô phỏng."

## 4. Blocker lớn nhất

**Tích hợp WAAP không hoạt động — không phải vì thiết kế sai, mà vì
hai lỗi tầng truy cập độc lập, cả hai đều đã được chứng minh bằng
bằng chứng trực tiếp:** (1) domain từng được WAAP-onboard
(`www.sentinelops.fyi`, Service ID `95743`) về mặt cấu trúc DNS không
thể mang traffic WAAP — nó chỉ redirect qua Cloudflare/Render; (2) tài
khoản/token đồng thời bị từ chối trên cả Compute và CDN — hai sản
phẩm hoàn toàn không liên quan gì đến việc onboard WAAP — cho thấy có
thể còn một vấn đề entitlement rộng hơn ở cấp tài khoản.

## 5. Cơ hội lớn nhất

**Cách khắc phục gần như miễn phí.** Cả hai gap lớn nhất — gap tường
thuật công khai và gap truy cập WAAP — đều có thể giải quyết mà không
cần hạ tầng mới, không cần dịch vụ trả phí mới:
- Gap tường thuật: chỉ là chỉnh sửa nội dung `content.js` cho khớp
  với thực tế đã được chứng minh.
- Gap WAAP: chỉ cần (a) trỏ đúng domain đã thật sự đi qua VNETWORK
  (`audit.sentinelops.fyi`) thay vì domain redirect, và (b) một cuộc
  kiểm tra entitlement tài khoản — cả hai đều là hành động xác minh,
  không phải kỹ thuật xây dựng mới.

Một khi cả hai được giải quyết, nguồn dữ liệu ROI cao nhất từng được
tìm thấy trong toàn bộ quá trình nghiên cứu VNETWORK (log WAAP thật)
sẽ sẵn sàng sử dụng, dùng đúng pipeline đã có, đúng tài sản đã sở hữu.

## Kết luận như một CTO

SentinelOps là một dự án kỹ thuật thật, có kỷ luật xác minh nghiêm
túc hiếm thấy, và một pipeline vận hành thật đã được kiểm chứng bằng
sự kiện thật — không phải một bản demo. Nhưng giá trị thật đó hiện
đang bị hai khoảng trống hoàn toàn có thể khắc phục che khuất: một
khoảng trống về tính trung thực của tường thuật công khai, và một
khoảng trống về truy cập kỹ thuật vào nguồn dữ liệu quan trọng nhất đã
được xác định. Không khoảng trống nào trong hai điều này đòi hỏi hạ
tầng mới, dịch vụ trả phí mới, hay công sức kỹ thuật lớn — cả hai đều
là quyết định và xác minh, không phải xây dựng. Đây là ưu tiên đúng
cho bước tiếp theo, trước khi mở rộng thêm bất kỳ năng lực mới nào.

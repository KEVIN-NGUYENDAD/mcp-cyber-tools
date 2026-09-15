# PRODUCT ROADMAP (Research Only — No Code)

Context: Decision Accuracy ~60% (gate: 90% × 3 tháng). Expansion còn khoá.
Nguyên tắc: không việc nào dưới đây được bắt đầu nếu nó làm chậm đường tới 90%.

## NOW (làm được ngay, không phá gate)

1. **SQLite Mirror**
   - Value: query/đo accuracy nhanh; hết scan JSON; nền cho mọi thứ sau.
   - Risk: thấp — mirror read-only, JSON vẫn là source of truth.
   - Effort: S (1 sprint). Priority: **P0 — ROI cao nhất.**

2. **Licensing (chỉ thiết kế: license key + feature flags)**
   - Value: quyết định sớm tránh phải refactor auth về sau.
   - Risk: thấp nếu chỉ là spec, cao nếu code sớm.
   - Effort: S (spec). Priority: P1.

## NEXT (sau khi accuracy ≥ 90%)

3. **Installer (MSI/EXE + PM2 service)**
   - Value: mở cửa cho khách đầu tiên; hiện tại cài tay = không bán được.
   - Risk: trung bình — Windows signing, quyền admin.
   - Effort: M. Priority: P1 (ngay khi gate mở).

4. **Customer Onboarding (10 phút đến brief đầu tiên)**
   - Value: giữ khách; quyết định sống/chết của bản pilot.
   - Risk: trung bình — cần installer trước.
   - Effort: M. Priority: P2.

5. **Agent Architecture (collector agent tách khỏi MCP host)**
   - Value: multi-host thật; hiện chỉ chạy máy local.
   - Risk: cao — transport, auth, versioning agent.
   - Effort: L. Priority: P2.

## LATER (chưa nên làm)

6. **PostgreSQL Migration** — chỉ khi >1 writer hoặc dữ liệu vượt SQLite.
   Value trung bình, Risk cao (ops + backup), Effort L. Priority: P3.

7. **Multi-Tenant Design** — cần Postgres + licensing + agent trước.
   Làm sớm = rebuild. Risk rất cao, Effort XL. Priority: P4.

## KẾT LUẬN
- Nên làm tiếp: SQLite Mirror, rồi spec Licensing.
- Chưa nên làm: Postgres, Multi-Tenant, Agent.
- ROI cao nhất: **SQLite Mirror** — phục vụ trực tiếp việc đo accuracy đang chặn mọi thứ.

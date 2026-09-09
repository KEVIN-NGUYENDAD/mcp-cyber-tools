# START HERE

Đây là điểm bắt đầu duy nhất cho mọi AI và developer.

---

## Repository Source of Truth

**Primary Branch**: `develop`  
**Status**: Production-ready, continuously updated  
**Last Update**: 2026-09-08

**⚠️ IMPORTANT**: Do NOT use `docs-sync` as primary data source. See [GIT_BRANCH_ANALYSIS.md](GIT_BRANCH_ANALYSIS.md) for details.

---

## Bắt buộc đọc theo thứ tự

1. **PROJECT_INDEX.md** - Điểm định hướng
2. **M365_COPILOT_CONTEXT.md** - Tóm tắt hoàn chỉnh (5 phút)
3. **SESSION_STATE.md** - Tình trạng hiện tại
4. **DEPLOYMENT.md** - Quy trình triển khai
5. **TROUBLESHOOTING.md** - Xử lý sự cố

---

## Quy Tắc Dự Án

### Ngôn ngữ
Tiếng Việt

### Workflow
- **TEAM A**: Audit
- **TEAM B**: Fix
- **LOOP**: Audit → Fix → Audit (liên tục)

### Ưu Tiên
1. Production (ổn định)
2. Deployment (hoạt động)
3. Critical Issues (sửa)
4. High Issues (sửa)
5. Medium Issues (sửa)

### Không được phép
- ❌ Thêm feature mới khi còn Critical
- ❌ Đổi giao diện khi còn Critical
- ❌ Chuyển v1.1 khi v1.0 chưa PASS

---

## Điều Kiện PASS

```
CRITICAL = 0 ✅
HIGH = 0 ✅
MEDIUM = 0 ✅
```

---

## 4 CRITICAL Issues Hiện Tại

| # | Vấn đề | Fix Status | Deploy Status |
|---|--------|-----------|---------------|
| C-001 | Executive Scorecard hiển thị UNKNOWN | ✅ Sửa | ❌ Chưa deploy |
| C-002 | MCP Widget hiển thị trạng thái không nhất quán | ✅ Sửa | ❌ Chưa deploy |
| C-003 | Incident Board không hiển thị nội dung | ✅ Sửa | ❌ Chưa deploy |
| C-004 | Timeline không hiển thị nội dung | ✅ Sửa | ❌ Chưa deploy |

---

## Tình Trạng Hiện Tại

### GitHub
✅ Có code mới (develop branch)

### Render
❌ Chưa xác nhận deploy commit mới nhất

### Production
❌ Chưa xác nhận chạy commit mới nhất

---

## Next Priority

1. ✓ Xác nhận commit production
2. ▶ Sửa Executive Scorecard (C-001)
3. ▶ Sửa MCP duplicate widget (C-002)
4. ▶ Sửa Incident Board (C-003)
5. ▶ Sửa Timeline (C-004)

---

## Quick Start

### Để fix một issue
```
1. Đọc M365_COPILOT_CONTEXT.md
2. Mở web/app.js
3. Tìm render function
4. Sửa code
5. git commit -m "Fix C-XXX"
6. git push origin develop
7. Kiểm tra production
```

### Để check tình trạng
```
1. Mở browser
2. Đi https://sentinelops-soc.onrender.com
3. Bấm F12 → Console
4. Tìm "[RENDER]" logs
5. Kiểm tra có sửa được không
```

### Nếu stuck
```
1. Đọc TROUBLESHOOTING.md
2. Kiểm tra GIT_STATE.md
3. Đọc SESSION_STATE.md
```

---

**Status**: 🔴 BLOCKED (Render not deploying, but code ready)

**Last Updated**: 2026-09-07

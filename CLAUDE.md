# CLAUDE.md - mcp-cyber-tools Context Guide

## 🔍 Vai trò và Phạm vi

**Project**: SentinelOps MCP Cyber Tools  
**Vai trò**: DFIR/SOC Engineer - Security Architect  
**Mục tiêu**: Xây dựng nền tảng MCP (Model Context Protocol) cho Security Operations Center, cung cấp công cụ DFIR tự động hóa điều tra sự cố.

---

## 🏗️ Kiến trúc Hiện tại

### Core Modules
- **Trust Engine**: Xác minh độ tin cậy của các nguồn dữ liệu an ninh
- **Shadow Asset Detection**: Phát hiện tài sản ẩn / thiết bị không được quản lý
- **Threat Intelligence Correlation**: Liên kết các chỉ báo đe dọa từ nhiều nguồn
- **Incident Triage & Analysis**: Phân loại và phân tích sự cố tự động

### Technology Stack
- **Language**: Python 3.10+
- **MCP Integration**: Anthropic MCP protocol for Claude integration
- **Testing**: Pester + GitHub Actions (automation validation)
- **Security**: Event-sourced Case Engine, structured audit trails

---

## 📋 Quy tắc Phát triển (Branch Strategy)

### Branch Naming
- `develop` - Main development branch
- `feature/` - New features (e.g., `feature/shadow-asset-detection`)
- `bugfix/` - Bug fixes (e.g., `bugfix/trust-engine-validation`)
- `hotfix/` - Critical fixes for production
- `claude/` - AI-generated features (e.g., `claude/dfir-triage-investigation-xhgwz7`)

### Commit Convention
```
[TYPE] Short description

Longer explanation if needed.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

**Types**: `[FEAT]`, `[FIX]`, `[DOCS]`, `[TEST]`, `[REFACTOR]`, `[CHORE]`

### PR Requirements
- ✅ All tests passing (GitHub Actions)
- ✅ Code review approval
- ✅ Audit trail updated
- ✅ CHANGELOG.md updated
- ✅ Related issues linked

---

## 💬 Quy tắc Giao tiếp (Communication Rules)

### Ngôn ngữ & Lối trình bày
- **Luôn trả lời bằng tiếng Việt**: Tất cả giải thích, tài liệu, và phản hồi phải bằng tiếng Việt
- **Trình bày ngắn gọn & súc tích**: 
  - Tránh dài dòng, đi thẳng vào vấn đề
  - Ưu tiên kết quả và giải pháp
  - Sử dụng bullet points hoặc structured format
- **Dễ hiểu**: Giải thích phức tạp bằng ví dụ cụ thể và từng bước rõ ràng

### Thuật ngữ Kỹ thuật
- **Giữ thuật ngữ tiếng Anh chuẩn**: DFIR, SOC, Commit, PR, SIEM, MCP, etc.
- **Giải thích bằng tiếng Việt**: 
  - Commit = Lần ghi nhân code (Lần commit)
  - PR = Yêu cầu hợp nhất code (Pull Request)
  - DFIR = Điều tra và phục hồi dữ liệu số hóa
  - SOC = Trung tâm vận hành bảo mật
  - SIEM = Hệ thống quản lý sự kiện bảo mật
  - MCP = Giao thức bối cảnh mô hình

### Ví dụ Giao tiếp Tốt
```
❌ KHÔNG TỐT:
"The trust engine's source credibility scoring mechanism exhibits suboptimal performance characteristics..."

✅ TỐT:
"Trust Engine (hệ thống xác minh độ tin cậy) hiện đang có vấn đề:
- Điểm số tin cậy tính toán chậm
- Độ chính xác chưa đạt 90%"
```

---

## 🛠️ Lệnh Chạy Công Cụ (Command Reference)

### Lệnh phát triển
```bash
# Install dependencies
pip install -r requirements.txt

# Run security audit
npm run security-audit

# Validate automation pipeline
npm run certify

# Run DFIR investigation
python -m sentinelops.cli investigate --case-id <CASE_ID>

# Verify trust engine
python -m sentinelops.cli verify-trust --source <SOURCE>
```

### Lệnh kiểm thử
```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Full validation suite
npm run test:all
```

### Lệnh triển khai
```bash
# Build package
python setup.py build

# Generate MCP server binary
npm run build:mcp

# Deploy to staging
npm run deploy:staging
```

---

## 💬 Quy tắc Giao tiếp (Communication Rules)

### Ngôn ngữ & Phong cách
- **Luôn trả lời và giải thích bằng tiếng Việt** - Tất cả nội dung hướng dẫn, giải thích, và kết quả phải bằng tiếng Việt
- **Ngắn gọn, súc tích, dễ hiểu** - Tránh văn vở, đi thẳng vào giải pháp và kết quả thay vì lý thuyết dài dòng
- **Thuật ngữ kỹ thuật chuẩn** - Giữ các thuật ngữ tiếng Anh phổ biến trong ngành (DFIR, SOC, Commit, PR, MCP, API, etc.) nhưng luôn giải thích bằng tiếng Việt khi cần thiết
- **Trực tiếp và hành động** - Tập trung vào "làm gì bây giờ" thay vì "tại sao" nếu ngữ cảnh đã rõ

### Ví dụ Giao tiếp Tốt
```
❌ Xấu: "Chúng tôi cần thực hiện một số tùy chỉnh liên quan đến việc xử lý các yếu tố nhất định trong quy trình."

✅ Tốt: "Cần cập nhật scheduler để chạy `collect_soc_intelligence.py` sau Nessus collector. Tôi sẽ sửa file scheduler.py ngay."

❌ Xấu: "PR là một khái niệm trong Git workflow..."

✅ Tốt: "Merge yêu cầu (PR - Pull Request) vào branch `develop` sau khi tests pass."
```

---

## 🔐 Security Policies

### Incident Handling
1. **Severity Levels**:
   - **Critical**: Immediate response, 24/7 on-call
   - **High**: Within 4 hours
   - **Medium**: Within 1 business day
   - **Low**: Scheduled review

2. **Audit Trail Requirements**:
   - All decisions logged with timestamp
   - User/agent attribution required
   - Reversible actions tracked
   - Evidence preservation mandatory

### Data Handling
- No hardcoded credentials
- All secrets in environment variables
- Sensitive logs redacted
- GDPR/compliance-aware data retention

---

---

## 🏪 PATH GOVERNANCE (SINGLE SOURCE OF TRUTH - 2026-09-11)

### ✅ CONSOLIDATED PATH
```
C:\GitHub\mcp-cyber-tools
```

**All 7 Repositories Now at `C:\GitHub`:**
- mcp-cyber-tools (PRIMARY - Telegram bot, SOC skills)
- home-soc-reports
- sentinelops-homepage
- KEVIN-NGUYENDAD
- cybersecurity-labs
- network-security-audit-frontend
- uber-order-filter

See `C:\GitHub\REPO_INVENTORY.md` for complete list.

### ❌ DEPRECATED PATHS (Archived)
- `C:\Projects\` → `C:\Projects_OLD` (7-day retention)
- `C:\Users\tamng\Projects\` → `C:\Users\tamng\Projects_OLD` (7-day retention)
- `C:\Users\tamng\AppData\Roaming\Claude\Projects\` - Duplicates removed

### Git Pre-Commit Checklist
Before ANY change:
```bash
pwd  # Must show: C:\GitHub\mcp-cyber-tools
git branch --show-current  # Must show: feature/* or hotfix/* or develop
git status  # Review uncommitted changes
```

---

## 🚀 OPERATION MODE (SPRINT B Complete)

**Current Phase**: Production Stability & Bug Fixes  
**Focus**: Runtime monitoring, telemetry, operational excellence

### What's Allowed ✅
- Bug fixes (breaking issues)
- Runtime stability improvements
- Error handling & graceful degradation
- Monitoring & logging enhancements
- Documentation updates

### What's BLOCKED ❌
- No new Sprints (Sprint C forbidden)
- No new Skills
- No new Tools
- No feature expansion
- No dashboard/UI work

### Telegram Bot Deployment
```bash
cd C:\GitHub\mcp-cyber-tools
node scripts/telegram/telegramBot.js
```
- Bot must load `.env` via `dotenv.config()`
- Bot must stay alive (never exit)
- All commands: `/hunt`, `/triage`, `/evidence`, `/ioc`
- Handlers return real security data from Python skills

---

## 📚 Thông tin Thêm

- **Docs**: `/docs` folder - architecture, API reference, playbooks
- **Tests**: `/tests` folder - unit, integration, E2E tests
- **Issue Tracking**: GitHub Issues with `priority:*` labels
- **Runbook**: `/docs/runbooks` - operational playbooks
- **Repository Inventory**: `C:\GitHub\REPO_INVENTORY.md`
- **Telegram Bot**: `scripts/telegram/telegramBot.js` - SOC operations center

---

**Last Updated**: 2026-09-11 (Repository Consolidation - moved to C:\GitHub)  
**Maintainer**: Kevin (Tam) Nguyen - Security Architect  
**Phase**: Sprint B Complete - Operation Mode Active

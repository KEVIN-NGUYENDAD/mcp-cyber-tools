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

## 📚 Thông tin Thêm

- **Docs**: `/docs` folder - architecture, API reference, playbooks
- **Tests**: `/tests` folder - unit, integration, E2E tests
- **Issue Tracking**: GitHub Issues with `priority:*` labels
- **Runbook**: `/docs/runbooks` - operational playbooks

---

**Last Updated**: 2026-09-10  
**Maintainer**: Kevin (Tam) Nguyen - Security Architect

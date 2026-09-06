# PHASE N.7 - INCIDENT & CHANGE TIMELINE

## Mục Tiêu

Xây dựng Timeline và History Layer để trả lời câu hỏi:
**"Điều gì đã thay đổi trong 24 giờ qua?"**

## Thành Phần

### 1. Timeline Events Collector (`collect_timeline_events.py`)

Phát hiện 5 loại thay đổi:

1. **Asset Changes**: Thiết bị mới / biến mất
2. **Service Changes**: Service mới / port mới
3. **WAAP Changes**: Điểm rủi ro tăng / giảm
4. **Risk Changes**: Thay đổi mức độ rủi ro (LOW→MEDIUM, MEDIUM→HIGH, etc.)
5. **MCP Changes**: Defender/Firewall enable/disable, CPU>90%, Disk>90%

### 2. State File: `state/timeline.json`

```json
{
  "timestamp": "2026-09-05T10:30:00Z",
  "period": "24 giờ gần nhất",
  "total_events": 5,
  "by_category": {
    "Asset": 1,
    "Security": 2,
    "Risk": 1,
    "System": 1
  },
  "by_severity": {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 2
  },
  "events": [
    {
      "timestamp": "2026-09-05T10:15:00Z",
      "category": "Security",
      "type": "Defender Disabled",
      "severity": "CRITICAL",
      "description": "Microsoft Defender đã bị tắt",
      "details": {}
    }
  ]
}
```

### 3. History Snapshots

Mỗi collection, script lưu snapshot trước đó trong `state/history/`:
- `state/history/assets.json.prev`
- `state/history/services.json.prev`
- `state/history/waap_score.json.prev`
- `state/history/risk_score.json.prev`
- `state/history/defender_status.json.prev`
- `state/history/firewall_status.json.prev`
- `state/history/system_health.json.prev`

Script so sánh:
- Current state vs Previous snapshot
- Phát hiện thay đổi
- Tạo timeline events
- Lưu current state thành .prev cho lần sau

### 4. Dashboard Integration

Timeline hiển thị trên dashboard:
- **Summary**: Số CRITICAL/HIGH/MEDIUM events
- **Timeline Events**: 10 sự kiện gần nhất (mới nhất trước)
- **Color Coding**: CRITICAL (đỏ), HIGH (cam), MEDIUM (vàng), LOW (xanh)

### 5. Daily Brief Integration

Daily Brief bao gồm `change_summary`:
```json
{
  "change_summary": {
    "total_changes": 5,
    "changes_by_category": {...},
    "changes_by_severity": {...},
    "critical_incidents": [...],
    "summary_text": "1 sự kiện CRITICAL, 2 sự kiện HIGH"
  }
}
```

## Execution Flow

Pipeline orchestrator chạy Timeline collection ở Phase 7:

```
PHASE 1: DATA COLLECTION
→ Nessus, Domain, WAAP, System Health, Defender, Firewall, Security Events

PHASE 2: INTELLIGENCE EXTRACTION
→ Assets, Services, Crypto

PHASE 3-6: SCORING & DECISIONS

PHASE 7: INCIDENT & CHANGE TIMELINE ← NEW
→ Compare current vs previous state
→ Detect changes
→ Generate timeline.json
→ Update daily brief

→ Dashboard displays timeline in real-time
```

## Key Features

✅ Automatic diff detection
✅ Historical snapshots
✅ Severity-based categorization
✅ Real-time dashboard updates
✅ Daily brief integration
✅ No manual configuration needed

## Ví Dụ Timeline Events

- 🟥 CRITICAL: "Defender Disabled"
- 🟠 HIGH: "Firewall Disabled", "Disk Usage 95%"
- 🟡 MEDIUM: "New Device Detected", "WAAP Score Dropped 20 points"
- 🟢 LOW: "Device Removed"

## Constraints

- Không refactor kiến trúc
- Chỉ thêm timeline vào existing pipeline
- Timeline chỉ tracking 5 loại thay đổi (không mở rộng)
- History snapshots lưu trong state/history/
- Dừng sau khi timeline hiển thị trên dashboard

## Next Phase

Sau khi timeline hoạt động ổn định:
- Có thể thêm alerting dựa trên timeline events
- Có thể thêm correlation analysis
- Có thể thêm trend prediction

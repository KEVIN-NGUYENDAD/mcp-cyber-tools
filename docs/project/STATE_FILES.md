# State Files Reference

## All state/*.json files

### assets.json
- **Size**: 14 KB
- **Contains**: 11 assets with vulnerabilities
- **Schema**: 
  ```json
  {
    "timestamp": "2026-09-07T11:10:00",
    "total_assets": 11,
    "assets": [
      {
        "ip": "192.168.0.X",
        "hostname": "hostname",
        "os": "Windows",
        "vulnerability_count": N,
        "critical": 0,
        "high": 0,
        "medium": X,
        "low": X,
        "info": X
      }
    ]
  }
  ```

### incidents.json  
- **Size**: 8 KB
- **Contains**: 18 open incidents
- **Usage**: renderIncidentBoard() reads this

### risk_score.json
- **Size**: 2 KB  
- **Contains**: Overall risk metrics (74/100)
- **Usage**: Dashboard risk display

### system_health.json
- **Size**: 1 KB
- **Contains**: System operational status

### defender_status.json
- **Size**: 2 KB
- **Contains**: Windows Defender stats

### firewall_status.json
- **Size**: 3 KB
- **Contains**: Firewall rules and status

### waap_status.json
- **Size**: 1 KB
- **Contains**: Web WAF (SSL valid, 87 days left)

### domain_status.json  
- **Size**: 1 KB
- **Contains**: Domain info (sentinelops.fyi)

### notification_history.json
- **Size**: 5 KB
- **Contains**: Alert history

---

**Total**: 9 files, ~38 KB, updated manually or by scripts

#!/bin/bash

# PHASE 1 HARDENED HOME SOC - DEPLOYMENT ACTIVATION
# Run this script to activate continuous monitoring

set -e

echo "🚀 PHASE 1 HARDENED HOME SOC - DEPLOYMENT ACTIVATION"
echo "======================================================"
echo ""

# Check Node.js
echo "✓ Checking Node.js..."
node --version
echo ""

# Create directories
echo "✓ Creating report directories..."
mkdir -p reports/home-soc-state
mkdir -p reports/home-soc-briefs
mkdir -p reports/home-soc-executive
mkdir -p reports/home-soc-ops
mkdir -p logs
echo ""

# Initialize collection (first run)
echo "✓ Initializing network collector..."
node network-collector.js
echo ""

# Verify history files
echo "✓ Verifying history files created..."
if [ -f "reports/home-soc-state/device-history.json" ]; then
  echo "  ✓ device-history.json ($(wc -c < reports/home-soc-state/device-history.json) bytes)"
else
  echo "  ✗ device-history.json MISSING"
  exit 1
fi

if [ -f "reports/home-soc-state/network-history.json" ]; then
  echo "  ✓ network-history.json ($(wc -c < reports/home-soc-state/network-history.json) bytes)"
else
  echo "  ✗ network-history.json MISSING"
  exit 1
fi

if [ -f "reports/home-soc-state/changes.json" ]; then
  echo "  ✓ changes.json ($(wc -c < reports/home-soc-state/changes.json) bytes)"
else
  echo "  (changes.json will be created when changes detected)"
fi
echo ""

# Test report generation
echo "✓ Testing report generation from history..."
node home-soc-brief.js > /dev/null 2>&1
if [ -f "home-soc-brief-*.html" ]; then
  echo "  ✓ Home SOC Brief generated"
else
  echo "  ✗ Brief generation failed"
  exit 1
fi
echo ""

# Display collected evidence
echo "✓ Collected Evidence:"
echo ""
echo "Device History:"
cat reports/home-soc-state/device-history.json | grep -E "devices|timestamp|lastCollected" | head -3
echo ""

echo "Network History (snapshots):"
cat reports/home-soc-state/network-history.json | grep "timestamp" | tail -1
echo ""

# Cron installation prompt
echo "======================================================"
echo "✅ PHASE 1 DEPLOYMENT READY"
echo "======================================================"
echo ""
echo "Next step: Schedule continuous collection"
echo ""
echo "Option A: Linux/macOS Cron"
echo "================================"
echo "crontab -e"
echo ""
echo "Add these lines (replace /path/to with actual path):"
echo "# Collection every 30 minutes"
echo "*/30 * * * * cd /path/to/mcp-cyber-tools && node network-collector.js >> logs/collector.log 2>&1"
echo ""
echo "# Reports at 8:00 PM"
echo "0 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-brief.js >> logs/brief.log 2>&1"
echo "5 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-executive-brief.js >> logs/executive.log 2>&1"
echo "10 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-ops-brief.js >> logs/ops.log 2>&1"
echo ""
echo "Option B: Windows Task Scheduler"
echo "================================"
echo "1. Create batch file: run-home-soc.bat"
echo "   @echo off"
echo "   cd C:\path\to\mcp-cyber-tools"
echo "   node network-collector.js"
echo ""
echo "2. Schedule in Task Scheduler:"
echo "   - Task: Run home-soc.bat every 30 minutes"
echo "   - Trigger: Every 30 minutes"
echo ""
echo "Monitoring"
echo "=========="
echo "Watch collection: tail -f logs/collector.log"
echo "Watch briefs:     tail -f logs/brief.log"
echo "Check history:    ls -lh reports/home-soc-state/*.json"
echo ""
echo "14-Day Evaluation"
echo "================="
echo "After 14 days, check for:"
echo "- New devices discovered"
echo "- Offline/online events"
echo "- Camera availability"
echo "- Network stability"
echo ""
echo "Then: Decide if Phase 2 (router integration) is needed"
echo ""

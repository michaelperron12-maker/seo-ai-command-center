#!/bin/bash
# SeoAI Security Agent — Lynis Weekly Audit
# Installed: 2026-02-11
# Part of seoparai.com agent system

REPORT_DIR=/opt/seo-agent/security/reports
mkdir -p $REPORT_DIR

DATE=$(date +%Y%m%d)
REPORT_FILE=$REPORT_DIR/lynis-$DATE.log

echo "[SeoAI Security] Running Lynis audit — $(date)" > $REPORT_FILE
lynis audit system --no-colors --quiet >> $REPORT_FILE 2>&1

# Copy score to a simple status file for dashboard
SCORE=$(grep 'Hardening index' /var/log/lynis.log 2>/dev/null | grep -oP 'd+' | tail -1)
echo "{\"date\": \"$(date -Iseconds)\", \"score\": \"$SCORE\", \"report\": \"$REPORT_FILE\"}" > /opt/seo-agent/security/last-audit.json

# Keep only last 12 reports
ls -t $REPORT_DIR/lynis-*.log | tail -n +13 | xargs rm -f 2>/dev/null

echo "[SeoAI Security] Audit complete — Score: $SCORE" >> $REPORT_FILE

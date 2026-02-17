#!/bin/bash
# SeoAI Security — Monthly SSL Audit
# Part of seoparai.com agent system

REPORT_DIR=/opt/seo-agent/security/reports
mkdir -p $REPORT_DIR
DATE=$(date +%Y%m%d)

DOMAINS="seoparai.com deneigement-excellence.ca paysagiste-excellence.ca jcpeintre.com facturation.deneigement-excellence.ca"

echo "[SeoAI SSL Audit] Started — $(date)" > $REPORT_DIR/ssl-audit-$DATE.log

for DOMAIN in $DOMAINS; do
    echo "=== $DOMAIN ===" >> $REPORT_DIR/ssl-audit-$DATE.log
    /opt/seo-agent/security/testssl.sh/testssl.sh --quiet --color 0 $DOMAIN >> $REPORT_DIR/ssl-audit-$DATE.log 2>&1
    echo "" >> $REPORT_DIR/ssl-audit-$DATE.log
done

echo "[SeoAI SSL Audit] Complete — $(date)" >> $REPORT_DIR/ssl-audit-$DATE.log

# Keep last 6 reports
ls -t $REPORT_DIR/ssl-audit-*.log | tail -n +7 | xargs rm -f 2>/dev/null

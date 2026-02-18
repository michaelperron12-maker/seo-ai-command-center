#!/bin/bash
# SeoAI — Daily Backup Agent
# Part of seoparai.com agent system — 2026-02-11

BACKUP_DIR=/opt/seo-agent/backups
DATE=$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

echo "[SeoAI Backup] Started — $(date)"

# Backup all sites
tar czf $BACKUP_DIR/sites-$DATE.tar.gz     /var/www/jcpeintre.com/     /var/www/jcpeintre-api/     /var/www/deneigement/     /var/www/paysagement/     /var/www/dashboard/     /var/www/facturation/     /var/www/ticket911/     --exclude='node_modules'     --exclude='__pycache__'     --exclude='.git'     --exclude='venv'     2>/dev/null

echo "Sites backup: $(du -sh $BACKUP_DIR/sites-$DATE.tar.gz | cut -f1)"

# Backup databases separately
mkdir -p /tmp/db-backup-$DATE
cp /var/www/ticket911/db/ticket911.db /tmp/db-backup-$DATE/ 2>/dev/null
cp /var/www/jcpeintre-api/data/jcpeintre.db /tmp/db-backup-$DATE/ 2>/dev/null
cp /opt/seo-agent/agents/seo_agents.db /tmp/db-backup-$DATE/ 2>/dev/null
cp /var/www/dashboard/sessions.db /tmp/db-backup-$DATE/ 2>/dev/null
cp /opt/seo-agent/db/seo_analytics.db /tmp/db-backup-$DATE/ 2>/dev/null
tar czf $BACKUP_DIR/databases-$DATE.tar.gz /tmp/db-backup-$DATE/ 2>/dev/null
rm -rf /tmp/db-backup-$DATE

echo "DB backup: $(du -sh $BACKUP_DIR/databases-$DATE.tar.gz | cut -f1)"

# Backup nginx configs
tar czf $BACKUP_DIR/nginx-$DATE.tar.gz /etc/nginx/ 2>/dev/null

# Backup systemd services
tar czf $BACKUP_DIR/systemd-$DATE.tar.gz /etc/systemd/system/*.service 2>/dev/null

# Backup cron jobs
tar czf $BACKUP_DIR/cron-$DATE.tar.gz /etc/cron.d/seoai-* 2>/dev/null

# Backup .env files
mkdir -p /tmp/env-backup-$DATE
cp /var/www/jcpeintre.com/.env /tmp/env-backup-$DATE/jcpeintre.env 2>/dev/null
cp /var/www/jcpeintre-api/.env /tmp/env-backup-$DATE/jcpeintre-api.env 2>/dev/null
cp /var/www/ticket911/.env /tmp/env-backup-$DATE/ticket911.env 2>/dev/null
tar czf $BACKUP_DIR/env-$DATE.tar.gz /tmp/env-backup-$DATE/ 2>/dev/null
rm -rf /tmp/env-backup-$DATE

# Rotation: keep last 30 days
find $BACKUP_DIR -name '*.tar.gz' -mtime +30 -delete

# Status file for dashboard
TOTAL=$(du -sh $BACKUP_DIR | cut -f1)
echo "{\"date\": \"$(date -Iseconds)\", \"size\": \"$TOTAL\", \"files\": $(ls $BACKUP_DIR/*-$DATE.tar.gz 2>/dev/null | wc -l)}" > /opt/seo-agent/security/last-backup.json

echo "[SeoAI Backup] Complete — Total: $TOTAL"

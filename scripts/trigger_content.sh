#!/bin/bash
# Trigger content generation
curl -s -X POST http://localhost:8002/api/content/trigger -H 'Content-Type: application/json' -d '{"site_id":"all"}' >> /opt/seo-agent/logs/cron.log 2>&1
echo " - Content generation triggered at $(date)" >> /opt/seo-agent/logs/cron.log

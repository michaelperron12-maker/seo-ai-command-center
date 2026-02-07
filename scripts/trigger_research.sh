#!/bin/bash
# Trigger weekly keyword research
curl -s -X POST http://localhost:8002/api/research/trigger -H 'Content-Type: application/json' -d '{"site_id":"all"}' >> /opt/seo-agent/logs/cron.log 2>&1
echo " - Research triggered at $(date)" >> /opt/seo-agent/logs/cron.log

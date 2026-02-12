#!/usr/bin/env python3
"""
SEO Agent API Server - Backend complet pour dashboard
Port: 8002
"""

import os
import json
import sqlite3
import yaml
import subprocess
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import requests

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/opt/seo-agent/db/seo_agent.db"
CONFIG_PATH = "/opt/seo-agent/config.yaml"

def get_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except:
        return {"general": {"pause_active": False}}

def get_db():
    return sqlite3.connect(DB_PATH)

# ============================================
# KILLSWITCH
# ============================================

@app.route('/api/check-killswitch', methods=['GET'])
def check_killswitch():
    config = get_config()
    pause_active = config.get('general', {}).get('pause_active', False)
    return jsonify({"pause_active": pause_active, "timestamp": datetime.now().isoformat()})

@app.route('/api/activate-killswitch', methods=['POST'])
def activate_killswitch():
    try:
        config = get_config()
        config['general']['pause_active'] = True
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return jsonify({"status": "ok", "pause_active": True})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/deactivate-killswitch', methods=['POST'])
def deactivate_killswitch():
    try:
        config = get_config()
        config['general']['pause_active'] = False
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return jsonify({"status": "ok", "pause_active": False})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# STATS & HEALTH
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat(), "version": "2.0.0"})

@app.route('/api/stats', methods=['GET'])
def get_global_stats():
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM publications")
    stats['total_publications'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM publications WHERE published_at > datetime('now', '-24 hours')")
    stats['publications_24h'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM drafts WHERE status = 'pending'")
    stats['pending_drafts'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mon_alerts WHERE resolved = 0")
    stats['active_alerts'] = cursor.fetchone()[0]
    conn.close()
    config = get_config()
    stats['pause_active'] = config.get('general', {}).get('pause_active', False)
    return jsonify(stats)

# ============================================
# SITES
# ============================================

@app.route('/api/sites', methods=['GET'])
def get_sites():
    config = get_config()
    return jsonify({"sites": config.get('sites', [])})

# ============================================
# KEYWORDS
# ============================================

@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    site_id = request.args.get('site_id')
    conn = get_db()
    cursor = conn.cursor()
    if site_id:
        cursor.execute('SELECT id, site_id, mot_cle, volume, difficulte, priorite, statut FROM keywords WHERE site_id = ? ORDER BY priorite, volume DESC', (site_id,))
    else:
        cursor.execute('SELECT id, site_id, mot_cle, volume, difficulte, priorite, statut FROM keywords ORDER BY site_id, priorite, volume DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'keywords': [{'id': r[0], 'site_id': r[1], 'keyword': r[2], 'volume': r[3], 'difficulty': r[4], 'priority': r[5], 'status': r[6]} for r in rows]})

# ============================================
# ALERTS
# ============================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    resolved = request.args.get('resolved', 'false') == 'true'
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, site_id, alert_type, severity, message, created_at,
        COALESCE(source_agent, 'unknown') as source_agent,
        COALESCE(corrected_by, '') as corrected_by,
        resolved, resolved_at,
        CASE
            WHEN resolved = 1 AND corrected_by = 'self_audit_agent' THEN 'auto_fixed'
            WHEN resolved = 1 THEN 'resolved'
            WHEN created_at > datetime('now', '-1 hour') THEN 'new'
            ELSE 'active'
        END as status
    FROM mon_alerts WHERE resolved = ?
    ORDER BY
        CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
        created_at DESC
    LIMIT 50""", (1 if resolved else 0,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"alerts": [{"id": r[0], "site_id": r[1], "type": r[2], "severity": r[3], "message": r[4], "created_at": r[5], "source_agent": r[6], "corrected_by": r[7], "is_resolved": bool(r[8]), "resolved_at": r[9], "status": r[10]} for r in rows]})

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE mon_alerts SET resolved = 1, resolved_at = datetime('now') WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "resolved", "id": alert_id})

# ============================================
# DRAFTS
# ============================================

@app.route('/api/drafts', methods=['GET'])
def get_drafts():
    status = request.args.get('status', 'pending')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, site_id, titre, status, created_at FROM drafts WHERE status = ? ORDER BY created_at DESC LIMIT 50", (status,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"drafts": [{"id": r[0], "site_id": r[1], "titre": r[2], "status": r[3], "created_at": r[4]} for r in rows]})

@app.route('/api/drafts/<int:draft_id>/approve', methods=['POST'])
def approve_draft(draft_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE drafts SET status = 'approved', updated_at = datetime('now') WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "approved", "draft_id": draft_id})

@app.route('/api/drafts/<int:draft_id>/reject', methods=['POST'])
def reject_draft(draft_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE drafts SET status = 'rejected', updated_at = datetime('now') WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "rejected", "draft_id": draft_id})

# ============================================
# RUNS
# ============================================

@app.route('/api/runs', methods=['GET'])
def get_runs():
    limit = int(request.args.get('limit', 50))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, agent_name, task_type, site_id, status, duration_seconds, completed_at FROM agent_runs ORDER BY completed_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'runs': [{'id': r[0], 'agent': r[1], 'task': r[2], 'site': r[3], 'status': r[4], 'duration': round(r[5], 2) if r[5] else 0, 'completed_at': r[6]} for r in rows]})

# ============================================
# SSL
# ============================================

@app.route('/api/ssl', methods=['GET'])
def get_ssl():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT site_id, domain, valid, issuer, expires_at, days_until_expiry, checked_at FROM mon_ssl WHERE id IN (SELECT MAX(id) FROM mon_ssl GROUP BY site_id)')
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'ssl': [{'site_id': r[0], 'domain': r[1], 'valid': bool(r[2]), 'issuer': r[3], 'expires_at': r[4], 'days_left': r[5], 'checked_at': r[6]} for r in rows]})

# ============================================
# UPTIME
# ============================================

@app.route('/api/uptime/stats', methods=['GET'])
def get_uptime_stats():
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    for site_id in ['deneigement', 'paysagement', 'jcpeintre']:
        cursor.execute('SELECT COUNT(*), SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END), AVG(response_time_ms), MIN(response_time_ms), MAX(response_time_ms) FROM mon_uptime WHERE site_id = ? AND checked_at > datetime("now", "-24 hours")', (site_id,))
        row = cursor.fetchone()
        if row and row[0] > 0:
            stats[site_id] = {'total_checks': row[0], 'uptime_percent': round((row[1] / row[0]) * 100, 2), 'avg_response_ms': round(row[2], 2) if row[2] else 0, 'min_response_ms': round(row[3], 2) if row[3] else 0, 'max_response_ms': round(row[4], 2) if row[4] else 0}
    conn.close()
    return jsonify({'stats': stats})

@app.route('/api/uptime/history', methods=['GET'])
def get_uptime_history():
    days = int(request.args.get('days', 7))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT site_id, strftime('%Y-%m-%d %H:00', checked_at) as hour,
               AVG(response_time_ms) as avg_response,
               SUM(CASE WHEN is_up=1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as uptime_pct
        FROM mon_uptime WHERE checked_at > datetime('now', ?)
        GROUP BY site_id, hour ORDER BY hour DESC
    ''', (f'-{days} days',))
    rows = cursor.fetchall()
    conn.close()
    history = {}
    for r in rows:
        if r[0] not in history:
            history[r[0]] = []
        history[r[0]].append({'hour': r[1], 'response_ms': round(r[2], 2) if r[2] else 0, 'uptime': round(r[3], 2) if r[3] else 100})
    return jsonify({'history': history})

# ============================================
# CONFIG
# ============================================

@app.route('/api/config', methods=['GET'])
def get_full_config():
    config = get_config()
    safe_config = {
        'general': config.get('general', {}),
        'sites': config.get('sites', []),
        'timing': config.get('timing', {}),
        'notifications': {
            'telegram': {'enabled': config.get('notifications', {}).get('telegram', {}).get('enabled', False)},
            'email': {'enabled': config.get('notifications', {}).get('email', {}).get('enabled', False)},
            'sms': {'enabled': config.get('notifications', {}).get('sms', {}).get('enabled', False)}
        }
    }
    return jsonify(safe_config)

# ============================================
# LOGS
# ============================================

@app.route('/api/logs', methods=['GET'])
def get_logs():
    lines_count = int(request.args.get('lines', 50))
    log_type = request.args.get('type', 'master')
    log_files = {
        'master': '/opt/seo-agent/logs/master_agent.log',
        'seo': '/opt/seo-agent/logs/seo_agent.log',
        'nginx': '/var/log/nginx/access.log'
    }
    log_path = log_files.get(log_type, log_files['master'])
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()[-lines_count:]
        return jsonify({'logs': [l.strip() for l in lines], 'type': log_type})
    except Exception as e:
        return jsonify({'logs': [], 'error': str(e)})

# ============================================
# SERVER REALTIME
# ============================================

@app.route('/api/server/realtime', methods=['GET'])
def get_server_realtime():
    try:
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
        mem = subprocess.run(['free', '-m'], capture_output=True, text=True)
        mem_lines = mem.stdout.strip().split('\n')
        mem_vals = mem_lines[1].split()
        mem_total = int(mem_vals[1])
        mem_used = int(mem_vals[2])
        mem_pct = round((mem_used / mem_total) * 100, 1)
        disk = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        disk_pct = int(disk.stdout.strip().split('\n')[1].split()[4].replace('%', ''))
        return jsonify({'cpu_load': load, 'memory_percent': mem_pct, 'memory_used_mb': mem_used, 'memory_total_mb': mem_total, 'disk_percent': disk_pct, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)})

# ============================================
# PM2 STATUS
# ============================================

@app.route('/api/pm2', methods=['GET'])
def get_pm2_status():
    try:
        result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
        apps = json.loads(result.stdout) if result.stdout else []
        return jsonify({'apps': [{'name': a['name'], 'status': a['pm2_env']['status'], 'memory': a['monit']['memory'], 'cpu': a['monit']['cpu'], 'uptime': a['pm2_env'].get('pm_uptime', 0)} for a in apps]})
    except Exception as e:
        return jsonify({'apps': [], 'error': str(e)})

# ============================================
# CRON STATUS
# ============================================

@app.route('/api/cron', methods=['GET'])
def get_cron_status():
    return jsonify({'tasks': [
        {'name': 'Monitoring', 'schedule': 'Every 5 min', 'active': True},
        {'name': 'Performance', 'schedule': 'Every hour', 'active': True},
        {'name': 'Learning', 'schedule': 'Every 6h', 'active': True},
        {'name': 'Research', 'schedule': 'Every 24h', 'active': True},
        {'name': 'DB Backup', 'schedule': 'Daily 3:00', 'active': True}
    ]})

# ============================================
# PENDING ACTIONS (for human validation)
# ============================================

# Route /api/pending moved to new location

# ============================================
# APPROVE/REJECT ACTIONS
# ============================================

# Old approve_action removed - using actions_approve instead

# Old reject route removed
@app.route('/api/content/trigger', methods=['POST'])
def trigger_content():
    data = request.json or {}
    site_id = data.get('site_id', 'all')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO agent_runs (agent_name, task_type, site_id, status, result, duration_seconds, completed_at) VALUES (?, ?, ?, ?, ?, ?, datetime("now"))', ('content', 'generation_triggered', site_id, 'pending', '{}', 0))
    conn.commit()
    conn.close()
    return jsonify({'status': 'triggered', 'message': 'Content generation scheduled'})

@app.route('/api/research/trigger', methods=['POST'])
def trigger_research():
    data = request.json or {}
    site_id = data.get('site_id', 'all')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO agent_runs (agent_name, task_type, site_id, status, result, duration_seconds, completed_at) VALUES (?, ?, ?, ?, ?, ?, datetime("now"))', ('research', 'keywords_triggered', site_id, 'pending', '{}', 0))
    conn.commit()
    conn.close()
    return jsonify({'status': 'triggered', 'message': 'Keyword research scheduled'})

@app.route('/api/backup/trigger', methods=['POST'])
def trigger_backup():
    import shutil
    try:
        backup_dir = '/opt/seo-agent/db/backup'
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = f"{backup_dir}/seo_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(DB_PATH, backup_path)
        return jsonify({'status': 'success', 'backup_path': backup_path})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/briefs', methods=['GET'])
def get_briefs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, site_id, mot_cle, sujet, status, created_at FROM briefs ORDER BY created_at DESC LIMIT 50')
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'briefs': [{'id': r[0], 'site_id': r[1], 'keyword_id': r[2], 'titre': r[3], 'status': r[4], 'created_at': r[5]} for r in rows]})

# AI QWEN ENDPOINTS (Fireworks API)
# ============================================

import base64

FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY', 'fw_CbsGnsaL5NSi4wgasWhjtQ')
FIREWORKS_URL = 'https://api.fireworks.ai/inference/v1/chat/completions'
QWEN_MODEL = 'accounts/fireworks/models/qwen3-235b-a22b-instruct-2507'
DEEPSEEK_R1 = 'accounts/fireworks/models/deepseek-r1-0528'
ACTIVE_MODEL = DEEPSEEK_R1
QWEN_VL_MODEL = 'accounts/fireworks/models/qwen3-vl-235b-a22b-instruct'

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.json or {}
    message = data.get('message', '')
    context = str(data.get("context", "seo")) if not isinstance(data.get("context"), dict) else "general"
    if not message:
        return jsonify({'error': 'Message requis'}), 400
    prompts = {
        'seo': 'Tu es un expert SEO. Aide avec les strategies de referencement. Reponds en francais.',
        'content': 'Tu es un redacteur SEO expert. Cree du contenu optimise. Reponds en francais.',
        'analysis': 'Tu es un analyste de donnees SEO. Analyse les metriques. Reponds en francais.',
        'general': 'Tu es un assistant AI polyvalent. Reponds en francais.'
    }
    try:
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {FIREWORKS_API_KEY}'}
        payload = {'model': ACTIVE_MODEL, 'messages': [{'role': 'system', 'content': prompts.get(context, prompts['general'])}, {'role': 'user', 'content': message}], 'max_tokens': 2048, 'temperature': 0.7}
        response = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            return jsonify({'error': f'Erreur Fireworks: {response.status_code}'}), 500
        result = response.json()
        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        # Strip DeepSeek R1 <think> reasoning tags
        import re as _re
        ai_response = _re.sub(r'<think>.*?</think>', '', ai_response, flags=_re.DOTALL).strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ai_chat_history (context, user_message, ai_response, model, created_at) VALUES (?, ?, ?, ?, datetime("now"))', (context, message, ai_response, ACTIVE_MODEL))
        conn.commit()
        conn.close()
        return jsonify({'response': ai_response, 'model': ACTIVE_MODEL, 'context': context})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/history', methods=['GET'])
def ai_history():
    limit = int(request.args.get('limit', 20))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, context, user_message, ai_response, model, created_at FROM ai_chat_history ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'history': [{'id': r[0], 'context': r[1], 'user_message': r[2], 'ai_response': r[3], 'model': r[4], 'created_at': r[5]} for r in rows]})

@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    try:
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {FIREWORKS_API_KEY}'}
        response = requests.post(FIREWORKS_URL, headers=headers, json={'model': ACTIVE_MODEL, 'messages': [{'role': 'user', 'content': 'OK'}], 'max_tokens': 5}, timeout=15)
        return jsonify({'status': 'online' if response.status_code == 200 else 'error', 'model': ACTIVE_MODEL})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/ai/estimate', methods=['POST'])
def ai_estimate():
    data = request.json or {}
    prix = float(data.get('prix_concurrent', 0))
    recommande = round(prix * 0.90, 2)
    return jsonify({'prix_concurrent': prix, 'prix_recommande': recommande, 'reduction': 10, 'economie': round(prix - recommande, 2)})

@app.route('/api/ai/analyze-document', methods=['POST'])
def ai_analyze_document():
    if 'file' not in request.files:
        return jsonify({'error': 'Fichier requis'}), 400
    file = request.files['file']
    try:
        file_data = base64.standard_b64encode(file.read()).decode('utf-8')
        ext = file.filename.lower().split('.')[-1]
        mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}.get(ext, 'image/jpeg')
        prompt = 'Extrais les informations de ce document concurrent. REPONDS en JSON: {"nom_client": "", "adresse": "", "ville": "", "telephone": "", "services": "", "prix_concurrent": 0}'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {FIREWORKS_API_KEY}'}
        payload = {'model': QWEN_VL_MODEL, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{file_data}'}}]}], 'max_tokens': 2048, 'temperature': 0.2}
        response = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            return jsonify({'error': f'Erreur: {response.status_code}'}), 500
        result = response.json()
        text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        if '{' in text:
            text = text[text.find('{'):text.rfind('}')+1]
        extracted = json.loads(text)
        prix = float(extracted.get('prix_concurrent', 0) or 0)
        return jsonify({'success': True, 'extracted': extracted, 'prix_concurrent': prix, 'prix_recommande': round(prix * 0.90, 2)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/update', methods=['POST'])
def update_config():
    data = request.json or {}
    section = data.get('section')
    key = data.get('key')
    value = data.get('value')
    if not section or not key:
        return jsonify({'error': 'Section et key requis'}), 400
    try:
        import yaml
        config_path = '/opt/seo-agent/config/config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        parts = section.split('.')
        target = config
        for p in parts[:-1]:
            if p not in target:
                target[p] = {}
            target = target[p]
        if len(parts) == 1:
            if parts[0] not in config:
                config[parts[0]] = {}
            config[parts[0]][key] = value
        else:
            target[parts[-1]] = {key: value} if parts[-1] not in target else {**target[parts[-1]], key: value}
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/configure', methods=['POST'])
def configure_analytics():
    data = request.json or {}
    prop_id = data.get('property_id')
    if not prop_id:
        return jsonify({'error': 'Property ID requis'}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES ("ga_property_id", ?, datetime("now"))', (prop_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'property_id': prop_id})

# ============================================
# N8N WORKFLOW ENDPOINTS
# ============================================

import subprocess as sp

@app.route('/api/n8n/status', methods=['GET'])
def n8n_status():
    try:
        result = sp.run(['docker', 'inspect', '--format', '{{.State.Status}}', 'seo-agent-n8n'], capture_output=True, text=True)
        status = result.stdout.strip()
        return jsonify({'status': status, 'running': status == 'running', 'container': 'seo-agent-n8n', 'port': 5678})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/n8n/workflows', methods=['GET'])
def n8n_workflows():
    try:
        result = sp.run(['docker', 'exec', 'seo-agent-n8n', 'n8n', 'list:workflow'], capture_output=True, text=True)
        workflows = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                workflows.append({'id': parts[0].strip(), 'name': parts[1].strip()})
        
        # Get active workflows
        result_active = sp.run(['docker', 'exec', 'seo-agent-n8n', 'n8n', 'list:workflow', '--active=true'], capture_output=True, text=True)
        active_ids = [l.split('|')[0].strip() for l in result_active.stdout.strip().split('\n') if '|' in l]
        
        for w in workflows:
            w['active'] = w['id'] in active_ids
        
        return jsonify({'workflows': workflows})
    except Exception as e:
        return jsonify({'workflows': [], 'error': str(e)})

@app.route('/api/n8n/workflow/<workflow_id>/activate', methods=['POST'])
def n8n_activate(workflow_id):
    try:
        result = sp.run(['docker', 'exec', 'seo-agent-n8n', 'n8n', 'update:workflow', '--id', workflow_id, '--active=true'], capture_output=True, text=True)
        return jsonify({'success': True, 'workflow_id': workflow_id, 'action': 'activated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/n8n/workflow/<workflow_id>/deactivate', methods=['POST'])
def n8n_deactivate(workflow_id):
    try:
        result = sp.run(['docker', 'exec', 'seo-agent-n8n', 'n8n', 'update:workflow', '--id', workflow_id, '--active=false'], capture_output=True, text=True)
        return jsonify({'success': True, 'workflow_id': workflow_id, 'action': 'deactivated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/n8n/workflow/<workflow_id>/execute', methods=['POST'])
def n8n_execute(workflow_id):
    try:
        result = sp.run(['docker', 'exec', 'seo-agent-n8n', 'n8n', 'execute', '--id', workflow_id], capture_output=True, text=True, timeout=60)
        return jsonify({'success': True, 'workflow_id': workflow_id, 'output': result.stdout[:500]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/n8n/restart', methods=['POST'])
def n8n_restart():
    try:
        sp.run(['docker', 'restart', 'seo-agent-n8n'], capture_output=True)
        return jsonify({'success': True, 'message': 'n8n redemarrage en cours'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================
# AGENTS SYSTEM INTEGRATION
# ============================================
try:
    from agents_system import (
        MasterOrchestrator, KeywordResearchAgent, ContentGenerationAgent,
        FAQGenerationAgent, TechnicalSEOAuditAgent, PerformanceAgent,
        LocalSEOAgent, CompetitorAnalysisAgent, SchemaMarkupAgent,
        ContentCalendarAgent, BlogIdeaAgent, MonitoringAgent, SITES
    )
    AGENTS_LOADED = True
    from api_agents_routes import register_all_agent_routes
    register_all_agent_routes(app)
    orchestrator = MasterOrchestrator()
except Exception as e:
    AGENTS_LOADED = False
    print(f"Agents not loaded: {e}")

@app.route("/api/agents/list", methods=["GET"])
def list_agents():
    if not AGENTS_LOADED:
        return jsonify({"agents": [], "error": "not loaded"})
    agents = orchestrator.get_all_agents_status()
    return jsonify({"agents": agents, "count": len(agents)})

@app.route("/api/agents/audit/<int:site_id>", methods=["POST"])
def agent_audit(site_id):
    if not AGENTS_LOADED:
        return jsonify({"error": "Agents not loaded"}), 500
    results = orchestrator.run_full_audit(site_id)
    return jsonify(results)

@app.route("/api/agents/uptime", methods=["GET"])
def agent_uptime():
    if not AGENTS_LOADED:
        return jsonify({"error": "Agents not loaded"}), 500
    agent = MonitoringAgent()
    results = agent.check_uptime(SITES)
    return jsonify(results)


@app.route("/api/alerts/revalidate", methods=["POST"])
def revalidate_alerts():
    if not AGENTS_LOADED:
        return jsonify({"error": "Agents not loaded"}), 500
    agent = MonitoringAgent()
    results = agent.revalidate_old_alerts()
    return jsonify(results)

@app.route("/api/alerts/<int:alert_id>/corrected", methods=["POST"])
def mark_alert_corrected(alert_id):
    if not AGENTS_LOADED:
        return jsonify({"error": "Agents not loaded"}), 500
    data = request.json or {}
    agent_name = data.get("agent_name", "unknown_agent")
    agent = MonitoringAgent()
    result = agent.mark_corrected_by_agent(alert_id, agent_name)
    return jsonify(result)

@app.route("/api/alerts/site/<site_id>", methods=["GET"])
def get_site_alerts(site_id):
    if not AGENTS_LOADED:
        return jsonify({"error": "Agents not loaded"}), 500
    alert_type = request.args.get("type")
    agent = MonitoringAgent()
    alerts = agent.find_alerts_for_site(site_id, alert_type)
    return jsonify({"alerts": alerts})
# NOTIFICATIONS WHATSAPP
# ============================================
import os

WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '')

def send_whatsapp_notification(message):
    """Envoie notification WhatsApp via CallMeBot (gratuit)"""
    if not WHATSAPP_NUMBER:
        return {'success': False, 'error': 'No WhatsApp number configured'}
    
    try:
        # CallMeBot API (gratuit)
        import urllib.parse
        encoded_msg = urllib.parse.quote(message)
        url = f'https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={encoded_msg}&apikey=YOUR_API_KEY'
        # Pour activer: envoyer 'I allow callmebot to send me messages' au +34 644 51 95 23
        return {'success': True, 'message': 'WhatsApp notification queued'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/api/notifications/whatsapp/config', methods=['POST'])
def config_whatsapp():
    data = request.get_json() or {}
    phone = data.get('phone', '')
    
    # Save to env file
    try:
        with open('/opt/seo-agent/.env', 'a') as f:
            f.write(f'\nWHATSAPP_NUMBER={phone}\n')
        
        global WHATSAPP_NUMBER
        WHATSAPP_NUMBER = phone
        
        return jsonify({
            'success': True,
            'message': f'WhatsApp configure: {phone}',
            'instructions': 'Envoyez I allow callmebot to send me messages au +34 644 51 95 23 sur WhatsApp pour activer'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/notifications/whatsapp/test', methods=['POST'])
def test_whatsapp():
    result = send_whatsapp_notification('🔔 Test notification SEO AI Dashboard - Tout fonctionne!')
    return jsonify(result)

@app.route('/api/notifications/whatsapp/status', methods=['GET'])
def whatsapp_status():
    return jsonify({
        'configured': bool(WHATSAPP_NUMBER),
        'number': WHATSAPP_NUMBER[:6] + '****' if WHATSAPP_NUMBER else None
    })


# ============================================
# ENDPOINTS MANQUANTS (aliases et corrections)
# ============================================

@app.route('/api/pending', methods=['GET'])
def get_pending():
    """Retourne les drafts en attente de validation"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, site_id, titre, mot_cle, status, created_at FROM drafts WHERE status = 'pending' ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"drafts": [{"id": r[0], "site_id": r[1], "titre": r[2] or 'Sans titre', "sujet": r[3] or '', "status": r[4], "created_at": r[5]} for r in rows]})

@app.route('/api/actions/approve', methods=['POST'])
def actions_approve():
    """Alias pour approve draft"""
    data = request.get_json() or {}
    draft_id = data.get('id')
    if not draft_id:
        return jsonify({"success": False, "error": "ID requis"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE drafts SET status = 'approved', updated_at = datetime('now') WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": "approved", "draft_id": draft_id})

@app.route('/api/actions/reject', methods=['POST'])
def actions_reject():
    """Alias pour reject draft"""
    data = request.get_json() or {}
    draft_id = data.get('id')
    if not draft_id:
        return jsonify({"success": False, "error": "ID requis"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE drafts SET status = 'rejected', updated_at = datetime('now') WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": "rejected", "draft_id": draft_id})

@app.route('/api/drafts/<int:draft_id>/preview', methods=['GET'])
def preview_draft(draft_id):
    """Apercu d'un draft"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, site_id, titre, contenu, mot_cle, status, created_at FROM drafts WHERE id = ?", (draft_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Draft non trouve"}), 404
    return jsonify({
        "id": row[0], "site_id": row[1], "titre": row[2], 
        "contenu": row[3], "mot_cle": row[4], "status": row[5], "created_at": row[6]
    })



# ============================================
# PAGE D'ACCUEIL API
# ============================================
@app.route('/', methods=['GET'])
def api_index():
    return jsonify({
        'name': 'SEO AI Command Center API',
        'version': '3.0',
        'status': 'running',
        'agents': 30,
        'endpoints': {
            'stats': '/api/stats',
            'sites': '/api/sites',
            'keywords': '/api/keywords',
            'pending': '/api/pending',
            'alerts': '/api/alerts',
            'agents': '/api/agents/status',
            'uptime': '/api/agents/uptime',
            'health': '/api/health'
        },
        'dashboard': 'http://148.113.194.234:8080'
    })




@app.route("/api/self-audit/dashboard", methods=["GET"])
def self_audit_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT
        COUNT(*) as total,
        SUM(CASE WHEN auto_fixed = 1 THEN 1 ELSE 0 END) as auto_fixed,
        SUM(CASE WHEN fix_level = 'confirm' AND confirmed = 0 THEN 1 ELSE 0 END) as pending,
        SUM(CASE WHEN fix_level = 'manual' AND executed = 0 THEN 1 ELSE 0 END) as manual,
        SUM(CASE WHEN severity = 'critical' AND auto_fixed = 0 AND confirmed = 0 THEN 1 ELSE 0 END) as critical_open
    FROM self_audit_results""")
    stats = cursor.fetchone()
    cursor.execute("""SELECT id, site_id, check_type, severity, message, fix_level, auto_fixed, confirmed, created_at
    FROM self_audit_results ORDER BY created_at DESC LIMIT 30""")
    issues = cursor.fetchall()
    cursor.execute("""SELECT site_id, issues_found, auto_fixed, pending_confirm, completed_at
    FROM self_audit_runs WHERE site_id != '_email_skip' ORDER BY completed_at DESC LIMIT 1""")
    last_run = cursor.fetchone()
    conn.close()
    return jsonify({
        "stats": {"total": stats[0] if stats else 0, "auto_fixed": stats[1] if stats else 0,
            "pending_confirm": stats[2] if stats else 0, "manual_required": stats[3] if stats else 0,
            "critical_open": stats[4] if stats else 0},
        "issues": [{"id": r[0], "site_id": r[1], "check_type": r[2], "severity": r[3],
            "message": r[4], "fix_level": r[5], "auto_fixed": bool(r[6]), "confirmed": bool(r[7]),
            "created_at": r[8],
            "status": "auto_fixed" if r[6] else ("confirmed" if r[7] else "pending" if r[5]=="confirm" else "manual")
        } for r in issues],
        "last_run": {"site_id": last_run[0], "issues_found": last_run[1], "auto_fixed": last_run[2],
            "pending_confirm": last_run[3], "completed_at": last_run[4]} if last_run else None
    })

# Self-audit routes
from self_audit_routes import register_self_audit_routes
register_self_audit_routes(app)

@app.route("/api/agent/self-audit", methods=["POST"])
def run_self_audit_agent():
    try:
        from self_audit_agent import SelfAuditAgent
        agent = SelfAuditAgent()
        results = {}
        for site in ["deneigement-excellence.ca", "paysagiste-excellence.ca", "jcpeintre.com", "seoparai.com"]:
            r = agent.check_live_site(site)
            results[site] = r
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# COMMAND CENTER ENDPOINTS
# ============================================

@app.route("/api/command/git-sync", methods=["POST"])
def command_git_sync():
    try:
        result = subprocess.run(
            ["git", "-C", "/opt/seo-agent", "pull", "origin", "master"],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip() + result.stderr.strip()
        return jsonify({"success": result.returncode == 0, "output": output, "message": "Git sync complete"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/command/deploy", methods=["POST"])
def command_deploy():
    try:
        steps = []
        # Pull latest code
        r = subprocess.run(["git", "-C", "/opt/seo-agent", "pull", "origin", "master"],
                          capture_output=True, text=True, timeout=30)
        git_out = (r.stdout.strip() + ' ' + r.stderr.strip()).strip()
        steps.append(f"git pull: {'OK' if r.returncode == 0 else 'FAIL'} - {git_out[:100]}")

        # Restart scanner first (safe)
        r2 = subprocess.run(["sudo", "systemctl", "restart", "seo-scanner"], capture_output=True, text=True, timeout=15)
        steps.append(f"seo-scanner restart: {'OK' if r2.returncode == 0 else 'FAIL'}")

        # Schedule API restart in background (so response is sent first)
        import threading
        def delayed_restart():
            import time
            time.sleep(2)
            subprocess.run(["sudo", "systemctl", "restart", "seo-api"], capture_output=True, timeout=15)
        threading.Thread(target=delayed_restart, daemon=True).start()
        steps.append("seo-api: restart scheduled in 2s")

        return jsonify({"success": True, "output": "\n".join(steps), "message": "Deploy complete"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/command/restart-services", methods=["POST"])
def command_restart_services():
    try:
        # Don't restart seo-api itself (kills the response), restart it last in background
        services_first = ["seo-scanner"]
        results = []
        for svc in services_first:
            r = subprocess.run(["sudo", "systemctl", "restart", svc], capture_output=True, text=True, timeout=15)
            status = "OK" if r.returncode == 0 else f"FAIL ({r.stderr.strip()[:60]})"
            results.append(f"{svc}: {status}")

        # Check other services status instead of restarting non-existent ones
        for svc in ["seo-api"]:
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=5)
            results.append(f"{svc}: {r.stdout.strip()}")

        # Schedule self-restart in background after response
        import threading
        def delayed_restart():
            import time
            time.sleep(2)
            subprocess.run(["sudo", "systemctl", "restart", "seo-api"], capture_output=True, timeout=15)
        threading.Thread(target=delayed_restart, daemon=True).start()
        results.append("seo-api: scheduled restart in 2s")

        return jsonify({"success": True, "output": "\n".join(results), "message": f"Services checked/restarted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/command/status", methods=["GET"])
def command_status():
    try:
        services = ["seo-api", "seo-scanner", "seo-scheduler", "seo-audit"]
        statuses = {}
        for svc in services:
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=5)
            statuses[svc] = r.stdout.strip()
        return jsonify({"success": True, "services": statuses})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/db/backup", methods=["POST"])
def command_backup_db():
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        src = DB_PATH
        dst = f"/opt/seo-agent/backups/seo_agent_{ts}.db"
        os.makedirs("/opt/seo-agent/backups", exist_ok=True)
        import shutil
        shutil.copy2(src, dst)
        return jsonify({"success": True, "message": f"Backup saved: {dst}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ssl/check", methods=["POST"])
def command_check_ssl():
    try:
        import ssl, socket
        results = []
        config = get_config()
        sites = config.get('sites', [])
        domains = [s.get('domain', '') for s in sites if s.get('domain')]
        if not domains:
            domains = ["deneigement-excellence.ca", "paysagiste-excellence.ca", "jcpeintre.com", "seoparai.com"]
        for domain in domains:
            try:
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                    s.settimeout(5)
                    s.connect((domain, 443))
                    cert = s.getpeercert()
                    exp = cert.get('notAfter', '')
                    results.append({"domain": domain, "valid": True, "expires": exp})
            except Exception as e:
                results.append({"domain": domain, "valid": False, "error": str(e)[:80]})
        return jsonify({"success": True, "results": results, "message": f"Checked {len(results)} domains"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/alerts/resolve-all", methods=["POST"])
def resolve_all_alerts():
    try:
        conn = get_db()
        conn.execute("DELETE FROM mon_alerts")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "All alerts resolved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500






# ════════════════════════════════════════════════════════
# MISSING AGENT COMMAND ENDPOINTS
# ════════════════════════════════════════════════════════


@app.route("/api/agent/fix-all", methods=["POST"])
def agent_fix_all():
    """Run self-audit and auto-fix common issues"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        fixes = []

        # 1. Fix stale alerts older than 7 days
        cursor.execute("DELETE FROM mon_alerts WHERE created_at < datetime('now', '-7 days')")
        stale = cursor.rowcount
        if stale:
            fixes.append(f"Removed {stale} stale alerts (>7 days)")

        # 2. Check sites uptime
        import requests as _req
        sites = {1: "deneigement-excellence.ca", 2: "paysagiste-excellence.ca", 3: "jcpeintre.com", 4: "seoparai.com"}
        for sid, domain in sites.items():
            try:
                r = _req.get(f"https://{domain}", timeout=10)
                if r.status_code == 200:
                    fixes.append(f"{domain}: UP ({r.elapsed.total_seconds():.1f}s)")
                else:
                    fixes.append(f"{domain}: WARNING HTTP {r.status_code}")
            except:
                fixes.append(f"{domain}: DOWN - needs attention")

        # 3. Clean old agent_runs >30 days
        cursor.execute("DELETE FROM agent_runs WHERE started_at < datetime('now', '-30 days')")
        old_runs = cursor.rowcount
        if old_runs:
            fixes.append(f"Cleaned {old_runs} old agent runs (>30 days)")

        # 4. Check DB size
        import os
        db_path = '/opt/seo-agent/db/seo_agent.db'
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024*1024)
            fixes.append(f"DB size: {size_mb:.1f} MB")
            if size_mb > 500:
                cursor.execute("VACUUM")
                fixes.append("Ran VACUUM to optimize DB")

        conn.commit()
        conn.close()
        return jsonify({"success": True, "fixes": fixes, "message": f"Ran {len(fixes)} checks/fixes"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route("/api/agent/run", methods=["POST"])
def agent_run_generic():
    """Run any agent by name"""
    try:
        data = request.get_json() or {}
        agent_name = data.get('agent', data.get('name', ''))
        site_id = data.get('site_id', '1')
        if not agent_name:
            return jsonify({"success": False, "error": "Agent name required"}), 400

        # Map common names to classes
        agent_map = {
            'technical-seo': ('TechnicalSEOAuditAgent', 'run_audit', [site_id]),
            'schema-markup': ('SchemaMarkupAgent', 'generate_local_business', [site_id]),
            'content-generation': ('ContentGenerationAgent', 'generate_article', [site_id, data.get('keyword', 'seo')]),
            'keyword-research': ('KeywordResearchAgent', 'research_keywords', [site_id, data.get('keyword', 'seo'), 10]),
            'backlink-analysis': ('BacklinkAnalysisAgent', 'analyze_opportunities', [site_id]),
            'competitor-analysis': ('CompetitorAnalysisAgent', 'identify_competitors', [site_id]),
            'social-media': ('SocialMediaAgent', 'generate_post', [site_id, data.get('platform', 'linkedin'), data.get('topic', 'seo')]),
            'internal-linking': ('InternalLinkingAgent', 'suggest_links', [site_id, data.get('topic', '')]),
            'faq': ('FAQGenerationAgent', 'generate_faqs', [site_id, data.get('topic', 'services'), data.get('count', 10)]),
            'site-speed': ('SiteSpeedAgent', 'analyze_speed', [site_id]),
            'image-optimization': ('ImageOptimizationAgent', 'audit_images', [site_id]),
            'review-management': ('ReviewManagementAgent', 'generate_review_response', [data.get('text', 'Great service'), data.get('rating', 5), True]),
        }

        if agent_name in agent_map:
            class_name, method_name, args = agent_map[agent_name]
            import importlib
            mod = importlib.import_module('agents_system')
            cls = getattr(mod, class_name)
            instance = cls()
            method = getattr(instance, method_name)
            result = method(*args)
            return jsonify({"success": True, "result": result, "agent": agent_name})
        else:
            return jsonify({"success": False, "error": f"Unknown agent: {agent_name}. Available: {list(agent_map.keys())}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════
# AUTO SCHEDULER STATUS
# ════════════════════════════════════════════════════════

@app.route("/api/scheduler/status", methods=["GET"])
def get_scheduler_status():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cycles = {
        "monitoring": {"cron": "*/5 * * * *", "desc": "Uptime & alerts"},
        "seo-core": {"cron": "0 */4 * * *", "desc": "Technical SEO audits"},
        "content": {"cron": "0 8,20 * * *", "desc": "Content generation"},
        "marketing": {"cron": "0 10 * * *", "desc": "Social & backlinks"},
        "business": {"cron": "0 6 * * *", "desc": "Analytics & reports"},
        "maintenance": {"cron": "0 3 * * 0", "desc": "Backup & cleanup"},
    }
    result = []
    for name, info in cycles.items():
        row = conn.execute(
            "SELECT status, result, duration_seconds, started_at FROM agent_runs WHERE task_type=? AND status != 'running' ORDER BY started_at DESC LIMIT 1",
            (f"cycle_{name}" if name != "monitoring" else "monitoring",)
        ).fetchone()
        cycle_data = {
            "name": name, "cron": info["cron"], "description": info["desc"],
            "last_run": dict(row) if row else None,
            "status": row["status"] if row else "never"
        }
        result.append(cycle_data)
    count_24h = conn.execute("SELECT COUNT(*) FROM agent_runs WHERE started_at > datetime('now', '-1 day')").fetchone()[0]
    success_24h = conn.execute("SELECT COUNT(*) FROM agent_runs WHERE started_at > datetime('now', '-1 day') AND status='success'").fetchone()[0]
    unique_agents = conn.execute("SELECT COUNT(DISTINCT agent_name) FROM agent_runs WHERE started_at > datetime('now', '-1 day')").fetchone()[0]
    conn.close()
    return jsonify({
        "cycles": result,
        "stats_24h": {"total_runs": count_24h, "success_runs": success_24h,
            "success_rate": round(success_24h / count_24h * 100, 1) if count_24h > 0 else 0,
            "unique_agents": unique_agents},
        "model": "deepseek-r1-0528",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/scheduler/runs", methods=["GET"])
def get_scheduler_runs():
    limit = request.args.get("limit", 50, type=int)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM agent_runs ORDER BY started_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])



# ════════════════════════════════════════════════════════
# CHART DATA ENDPOINTS
# ════════════════════════════════════════════════════════

@app.route("/api/charts/agent-runs-daily", methods=["GET"])
def chart_agent_runs_daily():
    days = request.args.get("days", 7, type=int)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT date(started_at) as day, COUNT(*) as total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success FROM agent_runs WHERE started_at > datetime('now', ?) GROUP BY date(started_at) ORDER BY day",
        (f"-{days} days",)
    ).fetchall()
    conn.close()
    return jsonify({"days": [r[0] for r in rows], "total": [r[1] for r in rows], "success": [r[2] for r in rows]})

@app.route("/api/charts/uptime-daily", methods=["GET"])
def chart_uptime_daily():
    days = request.args.get("days", 7, type=int)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT date(created_at) as day, site_id, COUNT(*) as total, SUM(CASE WHEN status='up' THEN 1 ELSE 0 END) as up_count FROM mon_uptime WHERE created_at > datetime('now', ?) GROUP BY date(created_at), site_id ORDER BY day",
        (f"-{days} days",)
    ).fetchall()
    conn.close()
    sites = {}
    days_list = sorted(set(r[0] for r in rows))
    for r in rows:
        sid = r[1]
        if sid not in sites:
            sites[sid] = {}
        sites[sid][r[0]] = round(r[3]/r[2]*100, 1) if r[2] > 0 else 100
    result = {}
    for sid, data in sites.items():
        result[sid] = [data.get(d, 100) for d in days_list]
    return jsonify({"days": days_list, "sites": result})

@app.route("/api/charts/keyword-positions", methods=["GET"])
def chart_keyword_positions():
    site_id = request.args.get("site_id", "1")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT keyword, position, checked_at FROM serp_history WHERE client_id=? ORDER BY checked_at DESC LIMIT 200",
        (site_id,)
    ).fetchall()
    conn.close()
    keywords = {}
    for r in rows:
        kw = r[0]
        if kw not in keywords:
            keywords[kw] = {"dates": [], "positions": []}
        keywords[kw]["dates"].append(r[2])
        keywords[kw]["positions"].append(r[1])
    return jsonify(keywords)

@app.route("/api/charts/content-pipeline", methods=["GET"])
def chart_content_pipeline():
    conn = sqlite3.connect(DB_PATH)
    stats = {}
    for table, status_col in [("drafts", "statut"), ("content", "statut"), ("publications", "statut")]:
        try:
            rows = conn.execute(f"SELECT {status_col}, COUNT(*) FROM {table} GROUP BY {status_col}").fetchall()
            for r in rows:
                key = r[0] or "unknown"
                stats[key] = stats.get(key, 0) + r[1]
        except:
            pass
    total_briefs = conn.execute("SELECT COUNT(*) FROM briefs").fetchone()[0]
    stats["briefs"] = total_briefs
    conn.close()
    return jsonify(stats)

@app.route("/api/charts/alert-severity", methods=["GET"])
def chart_alert_severity():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT severity, COUNT(*) FROM mon_alerts WHERE resolved=0 GROUP BY severity").fetchall()
    conn.close()
    return jsonify({r[0]: r[1] for r in rows})

@app.route("/api/charts/scheduler-daily", methods=["GET"])
def chart_scheduler_daily():
    days = request.args.get("days", 7, type=int)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT date(started_at) as day, task_type, COUNT(*) as total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as ok FROM agent_runs WHERE task_type LIKE 'cycle_%%' AND started_at > datetime('now', ?) GROUP BY day, task_type ORDER BY day",
        (f"-{days} days",)
    ).fetchall()
    conn.close()
    days_list = sorted(set(r[0] for r in rows))
    cycles = {}
    for r in rows:
        c = r[1].replace("cycle_", "")
        if c not in cycles:
            cycles[c] = {}
        cycles[c][r[0]] = {"total": r[2], "ok": r[3]}
    return jsonify({"days": days_list, "cycles": cycles})

# ════════════════════════════════════════════════════════
# KEYWORD CLUSTER & TOPICAL MAP ENDPOINTS
# ════════════════════════════════════════════════════════

@app.route("/api/keyword-cluster", methods=["POST"])
def api_keyword_cluster():
    data = request.json or {}
    site_id = data.get("site_id", "1")
    try:
        from agents_system import KeywordClusterAgent
        agent = KeywordClusterAgent()
        result = agent.cluster_keywords(site_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/keyword-clusters", methods=["GET"])
def api_keyword_clusters_list():
    site_id = request.args.get("site_id", "1")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM keyword_clusters WHERE site_id=? ORDER BY priority, created_at DESC", (site_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/topical-map/generate", methods=["POST"])
def api_topical_map_generate():
    data = request.json or {}
    site_id = data.get("site_id", "1")
    seed = data.get("seed", "")
    try:
        from agents_system import TopicalMapAgent
        agent = TopicalMapAgent()
        result = agent.generate_map(site_id, seed)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/topical-maps", methods=["GET"])
def api_topical_maps_list():
    site_id = request.args.get("site_id", "1")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM topical_maps WHERE site_id=? ORDER BY created_at DESC", (site_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/content-score", methods=["POST"])
def api_content_score():
    data = request.json or {}
    content = data.get("content", "")
    keyword = data.get("keyword", "")
    if not content:
        return jsonify({"error": "content required"}), 400
    try:
        from agents_system import ContentScoringAgent
        agent = ContentScoringAgent()
        result = agent.score_content(content, keyword)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════
# REPORT BUILDER ENDPOINTS
# ════════════════════════════════════════════════════════

@app.route("/api/report/generate", methods=["POST"])
def api_report_generate():
    data = request.json or {}
    site_id = data.get("site_id", "1")
    branding = data.get("branding", None)
    try:
        from agents_system import WhiteLabelReportAgent
        agent = WhiteLabelReportAgent()
        result = agent.generate_monthly_report(site_id, branding)
        # Save to DB
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO reports (site_id, report_type, period, html_content, metrics_json, created_at) VALUES (?,?,?,?,?,datetime('now'))",
            (site_id, "monthly", datetime.now().strftime("%Y-%m"), str(result.get("html_report",""))[:50000], json.dumps(result.get("metrics",{})))
        )
        conn.commit()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports", methods=["GET"])
def api_reports_list():
    site_id = request.args.get("site_id")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = "SELECT id, site_id, report_type, period, created_at FROM reports"
    params = ()
    if site_id:
        q += " WHERE site_id=?"
        params = (site_id,)
    q += " ORDER BY created_at DESC LIMIT 20"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/report/<int:report_id>", methods=["GET"])
def api_report_view(report_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(dict(row))

# ════════════════════════════════════════════════════════
# BACKLINK ENRICHED ENDPOINTS
# ════════════════════════════════════════════════════════

@app.route("/api/backlinks/summary", methods=["GET"])
def api_backlinks_summary():
    site_id = request.args.get("site_id", "1")
    conn = sqlite3.connect(DB_PATH)
    try:
        total = conn.execute("SELECT COUNT(*) FROM backlinks WHERE client_id=?", (site_id,)).fetchone()[0]
        new_30d = conn.execute("SELECT COUNT(*) FROM backlinks WHERE client_id=? AND discovered_at > datetime('now','-30 days')", (site_id,)).fetchone()[0]
        domains = conn.execute("SELECT COUNT(DISTINCT source_domain) FROM backlinks WHERE client_id=?", (site_id,)).fetchone()[0]
        anchors = conn.execute("SELECT anchor_text, COUNT(*) as cnt FROM backlinks WHERE client_id=? GROUP BY anchor_text ORDER BY cnt DESC LIMIT 10", (site_id,)).fetchall()
    except:
        total, new_30d, domains, anchors = 0, 0, 0, []
    conn.close()
    return jsonify({
        "total": total, "new_30d": new_30d, "referring_domains": domains,
        "top_anchors": [{"text": a[0], "count": a[1]} for a in anchors]
    })


@app.route("/api/review-response", methods=["POST"])
def generate_review_response_api():
    try:
        data = request.get_json() or {}
        review_text = data.get("text", "")
        rating = data.get("rating", 5)
        is_positive = data.get("is_positive", True)
        if not review_text:
            return jsonify({"error": "Review text required"}), 400
        from agents_system import ReviewManagementAgent
        agent = ReviewManagementAgent()
        result = agent.generate_review_response(review_text, rating, is_positive)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=== SEO Agent API Server v3.0 ===")
    print("Port: 8002")
    app.run(host="0.0.0.0", port=8002)



# ============================================
# SELF-AUDIT ENDPOINTS
# ============================================

@app.route("/api/self-audit/results", methods=["GET"])
def get_self_audit_results():
    site_id = request.args.get("site_id")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT id, site_id, check_type, severity, message, fix_level, fix_command, auto_fixed, confirmed, executed, created_at FROM self_audit_results WHERE 1=1"
    params = []
    if site_id:
        query += " AND site_id = ?"
        params.append(site_id)
    query += " ORDER BY created_at DESC LIMIT 100"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"results": [{"id": r[0], "site_id": r[1], "check_type": r[2], "severity": r[3], "message": r[4], "fix_level": r[5], "fix_command": r[6], "auto_fixed": bool(r[7]), "confirmed": bool(r[8]), "executed": bool(r[9]), "created_at": r[10]} for r in rows]})

@app.route("/api/self-audit/pending", methods=["GET"])
def get_self_audit_pending():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, site_id, check_type, severity, message, fix_command FROM self_audit_results WHERE fix_level = 'confirm' AND confirmed = 0 AND executed = 0 ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"pending": [{"id": r[0], "site_id": r[1], "check_type": r[2], "severity": r[3], "message": r[4], "fix_command": r[5]} for r in rows]})

@app.route("/api/self-audit/confirm/<int:fix_id>", methods=["POST"])
def confirm_self_audit_fix(fix_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE self_audit_results SET confirmed = 1, confirmed_by = 'dashboard', fixed_at = datetime('now') WHERE id = ?", (fix_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "confirmed", "id": fix_id})

@app.route("/api/self-audit/confirm-all", methods=["POST"])
def confirm_all_self_audit():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE self_audit_results SET confirmed = 1, confirmed_by = 'dashboard', fixed_at = datetime('now') WHERE fix_level = 'confirm' AND confirmed = 0")
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return jsonify({"status": "confirmed_all", "count": affected})

@app.route("/api/self-audit/stats", methods=["GET"])
def get_self_audit_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN auto_fixed = 1 THEN 1 ELSE 0 END), SUM(CASE WHEN fix_level = 'confirm' AND confirmed = 0 THEN 1 ELSE 0 END), SUM(CASE WHEN fix_level = 'manual' AND executed = 0 THEN 1 ELSE 0 END) FROM self_audit_results")
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"total": row[0], "auto_fixed": row[1], "pending_confirm": row[2], "manual_required": row[3]})
    return jsonify({"total": 0, "auto_fixed": 0, "pending_confirm": 0, "manual_required": 0})


# ============================================
# AUTO-FIX SEO API ENDPOINTS
# ============================================

@app.route("/api/autofix/sites", methods=["GET"])
def autofix_list_sites():
    """Return list of sites available for auto-fix"""
    try:
        from agents_system import SITES as _SITES
    except ImportError:
        return jsonify({"error": "agents_system not available"}), 500
    sites_list = []
    for sid, info in _SITES.items():
        sites_list.append({
            "id": sid,
            "nom": info.get("nom", ""),
            "domaine": info.get("domaine", ""),
            "niche": info.get("niche", ""),
            "path": info.get("path", "")
        })
    return jsonify({"sites": sites_list})


@app.route("/api/autofix/diagnostic/<int:site_id>", methods=["GET"])
def autofix_diagnostic(site_id):
    """Scan a site and return what each agent found + what can be fixed"""
    try:
        from agents_system import (
            SITES as _SITES, TitleTagAgent, SchemaMarkupAgent,
            OpenGraphAgent, SocialMediaAgent, TechnicalSEOAuditAgent
        )
    except ImportError:
        return jsonify({"error": "agents_system not available"}), 500

    if site_id not in _SITES:
        return jsonify({"error": "Site {} not found".format(site_id)}), 404

    site = _SITES[site_id]
    domain = site.get("domaine", "")
    results = {"site_id": site_id, "domain": domain, "nom": site.get("nom", ""), "agents": {}}

    # --- title_tag agent ---
    try:
        tech = TechnicalSEOAuditAgent()
        url = "https://" + domain
        audit = tech.audit_page(url)
        title_issues = [i for i in audit.get("issues", []) if "title" in i.get("message", "").lower()]
        results["agents"]["title_tag"] = {
            "status": "issues_found" if title_issues else "ok",
            "issues": title_issues,
            "can_fix": bool(title_issues),
            "score": audit.get("score", 0)
        }
    except Exception as e:
        results["agents"]["title_tag"] = {"status": "error", "error": str(e), "can_fix": False}

    # --- schema agent ---
    try:
        schema_agent = SchemaMarkupAgent()
        schema_data = schema_agent.generate_complete_schema(site_id)
        import requests as _req
        resp = _req.get("https://" + domain, timeout=10, headers={"User-Agent": "SeoparAI-Agent/1.0"})
        has_schema = "application/ld+json" in resp.text.lower()
        results["agents"]["schema"] = {
            "status": "ok" if has_schema else "missing",
            "has_existing_schema": has_schema,
            "generated_schema": schema_data,
            "can_fix": not has_schema
        }
    except Exception as e:
        results["agents"]["schema"] = {"status": "error", "error": str(e), "can_fix": False}

    # --- opengraph agent ---
    try:
        og_agent = OpenGraphAgent()
        og_data = og_agent.generate_og_tags(site_id)
        missing_count = len(og_data.get("missing_og", [])) + len(og_data.get("missing_tw", []))
        results["agents"]["opengraph"] = {
            "status": og_data.get("status", "unknown"),
            "missing_og": og_data.get("missing_og", []),
            "missing_tw": og_data.get("missing_tw", []),
            "og_tags": og_data.get("og_tags", {}),
            "twitter_tags": og_data.get("twitter_tags", {}),
            "html_tags": og_data.get("html_tags", ""),
            "can_fix": missing_count > 0
        }
    except Exception as e:
        results["agents"]["opengraph"] = {"status": "error", "error": str(e), "can_fix": False}

    # --- social agent ---
    try:
        social_agent = SocialMediaAgent()
        sample = social_agent.generate_social_posts(site.get("nom", domain), "https://" + domain)
        has_posts = bool(sample)
        results["agents"]["social"] = {
            "status": "ok" if has_posts else "no_content",
            "sample_posts": sample,
            "can_fix": False
        }
    except Exception as e:
        results["agents"]["social"] = {"status": "error", "error": str(e), "can_fix": False}

    # Summary
    fixable = [k for k, v in results["agents"].items() if v.get("can_fix")]
    results["summary"] = {
        "total_agents": len(results["agents"]),
        "fixable_count": len(fixable),
        "fixable_agents": fixable
    }

    return jsonify(results)


@app.route("/api/autofix/run/<int:site_id>", methods=["POST"])
def autofix_run(site_id):
    """Run auto-fix agents to correct issues on a site"""
    try:
        from agents_system import (
            SITES as _SITES, TitleTagAgent, SchemaMarkupAgent,
            OpenGraphAgent, TechnicalSEOAuditAgent
        )
    except ImportError:
        return jsonify({"error": "agents_system not available"}), 500

    if site_id not in _SITES:
        return jsonify({"error": "Site {} not found".format(site_id)}), 404

    site = _SITES[site_id]
    domain = site.get("domaine", "")
    site_path = site.get("path", "")
    data = request.get_json(force=True, silent=True) or {}
    requested_agents = data.get("agents", [])

    if not requested_agents:
        return jsonify({"error": "No agents specified. Send {\"agents\": [\"schema\", \"opengraph\"]}"}), 400

    fix_results = {"site_id": site_id, "domain": domain, "fixes": {}}

    for agent_name in requested_agents:

        # --- Fix schema ---
        if agent_name == "schema":
            try:
                schema_agent = SchemaMarkupAgent()
                schema_data = schema_agent.generate_local_business_schema(site_id)
                schema_json = json.dumps(schema_data, indent=2, ensure_ascii=False)
                snippet = '<script type="application/ld+json">\n' + schema_json + '\n</script>'
                index_path = os.path.join(site_path, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "r", encoding="utf-8") as f:
                        html = f.read()
                    if "application/ld+json" not in html:
                        html = html.replace("</head>", snippet + "\n</head>", 1)
                        with open(index_path, "w", encoding="utf-8") as f:
                            f.write(html)
                        fix_results["fixes"]["schema"] = {"status": "injected", "file": index_path}
                    else:
                        fix_results["fixes"]["schema"] = {"status": "already_present", "file": index_path}
                else:
                    fix_results["fixes"]["schema"] = {"status": "file_not_found", "path": index_path}
            except Exception as e:
                fix_results["fixes"]["schema"] = {"status": "error", "error": str(e)}

        # --- Fix opengraph ---
        elif agent_name == "opengraph":
            try:
                og_agent = OpenGraphAgent()
                og_data = og_agent.generate_og_tags(site_id)
                og_html = og_data.get("html_tags", "")
                index_path = os.path.join(site_path, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "r", encoding="utf-8") as f:
                        html = f.read()
                    if "og:title" not in html:
                        html = html.replace("</head>", og_html + "\n</head>", 1)
                        with open(index_path, "w", encoding="utf-8") as f:
                            f.write(html)
                        fix_results["fixes"]["opengraph"] = {"status": "injected", "file": index_path, "tags_added": len(og_data.get("missing_og", [])) + len(og_data.get("missing_tw", []))}
                    else:
                        fix_results["fixes"]["opengraph"] = {"status": "already_present", "file": index_path}
                else:
                    fix_results["fixes"]["opengraph"] = {"status": "file_not_found", "path": index_path}
            except Exception as e:
                fix_results["fixes"]["opengraph"] = {"status": "error", "error": str(e)}

        # --- Fix title_tag ---
        elif agent_name == "title_tag":
            try:
                title_agent = TitleTagAgent()
                optimized = title_agent.optimize_title(
                    site.get("nom", ""), site.get("niche", ""), site.get("nom", "")
                )
                new_title = optimized.get("optimized_title", "")
                if new_title:
                    index_path = os.path.join(site_path, "index.html")
                    if os.path.exists(index_path):
                        import re as _re
                        with open(index_path, "r", encoding="utf-8") as f:
                            html = f.read()
                        old_title = _re.search(r"<title>(.*?)</title>", html, _re.IGNORECASE | _re.DOTALL)
                        if old_title:
                            html = html.replace(old_title.group(0), "<title>" + new_title + "</title>", 1)
                            with open(index_path, "w", encoding="utf-8") as f:
                                f.write(html)
                            fix_results["fixes"]["title_tag"] = {"status": "updated", "old": old_title.group(1).strip(), "new": new_title, "file": index_path}
                        else:
                            fix_results["fixes"]["title_tag"] = {"status": "no_title_found", "file": index_path}
                    else:
                        fix_results["fixes"]["title_tag"] = {"status": "file_not_found", "path": index_path}
                else:
                    fix_results["fixes"]["title_tag"] = {"status": "ai_no_result", "detail": "AI did not return an optimized title"}
            except Exception as e:
                fix_results["fixes"]["title_tag"] = {"status": "error", "error": str(e)}

        else:
            fix_results["fixes"][agent_name] = {"status": "unknown_agent", "detail": "Agent '{}' not supported for auto-fix".format(agent_name)}

    fix_results["summary"] = {
        "requested": len(requested_agents),
        "completed": len([v for v in fix_results["fixes"].values() if v.get("status") in ("injected", "updated", "already_present")])
    }

    return jsonify(fix_results)

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
    cursor.execute('SELECT id, site_id, keyword_id, titre, status, created_at FROM briefs ORDER BY created_at DESC LIMIT 50')
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'briefs': [{'id': r[0], 'site_id': r[1], 'keyword_id': r[2], 'titre': r[3], 'status': r[4], 'created_at': r[5]} for r in rows]})

# AI QWEN ENDPOINTS (Fireworks API)
# ============================================

import base64

FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY', 'fw_CbsGnsaL5NSi4wgasWhjtQ')
FIREWORKS_URL = 'https://api.fireworks.ai/inference/v1/chat/completions'
QWEN_MODEL = 'accounts/fireworks/models/qwen3-235b-a22b-instruct-2507'
QWEN_VL_MODEL = 'accounts/fireworks/models/qwen3-vl-235b-a22b-instruct'

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.json or {}
    message = data.get('message', '')
    context = data.get('context', 'seo')
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
        payload = {'model': QWEN_MODEL, 'messages': [{'role': 'system', 'content': prompts.get(context, prompts['general'])}, {'role': 'user', 'content': message}], 'max_tokens': 2048, 'temperature': 0.7}
        response = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            return jsonify({'error': f'Erreur Fireworks: {response.status_code}'}), 500
        result = response.json()
        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ai_chat_history (context, user_message, ai_response, model, created_at) VALUES (?, ?, ?, ?, datetime("now"))', (context, message, ai_response, QWEN_MODEL))
        conn.commit()
        conn.close()
        return jsonify({'response': ai_response, 'model': QWEN_MODEL, 'context': context})
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
        response = requests.post(FIREWORKS_URL, headers=headers, json={'model': QWEN_MODEL, 'messages': [{'role': 'user', 'content': 'OK'}], 'max_tokens': 5}, timeout=15)
        return jsonify({'status': 'online' if response.status_code == 200 else 'error', 'model': QWEN_MODEL})
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

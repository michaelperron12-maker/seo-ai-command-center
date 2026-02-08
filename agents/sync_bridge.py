#!/usr/bin/env python3
"""
Sync Bridge - Pont de synchronisation entre tous les composants
- SQLite seo_agent.db (source de vérité)
- n8n (via API)
- Ollama AI (Qwen, DeepSeek)
- API pour Claude Code SSH
"""

import sqlite3
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import threading
import time

# Configuration
DB_PATH = '/opt/seo-agent/db/seo_agent.db'
OLLAMA_URL = 'http://localhost:11434'
N8N_URL = 'http://localhost:5678'

app = Flask(__name__)

class SyncBridge:
    def __init__(self):
        self.db_path = DB_PATH
        self.last_sync = None

    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==========================================
    # SYNC: Données pour AI (Qwen/DeepSeek)
    # ==========================================
    def get_context_for_ai(self, site_domain=None):
        """Prépare le contexte pour les modèles AI"""
        conn = self.get_db()
        cursor = conn.cursor()

        context = {
            'timestamp': datetime.now().isoformat(),
            'sites': [],
            'alerts': [],
            'tasks': [],
            'keywords': []
        }

        # Sites
        if site_domain:
            cursor.execute("SELECT * FROM sites WHERE domaine = ?", [site_domain])
        else:
            cursor.execute("SELECT * FROM sites WHERE actif = 1")
        context['sites'] = [dict(row) for row in cursor.fetchall()]

        # Alertes actives
        cursor.execute("""
            SELECT sa.*, s.domaine
            FROM site_alerts sa
            LEFT JOIN sites s ON sa.site_id = s.id
            WHERE sa.is_active = 1
            ORDER BY
                CASE sa.priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END
            LIMIT 50
        """)
        context['alerts'] = [dict(row) for row in cursor.fetchall()]

        # Tâches en attente
        cursor.execute("""
            SELECT t.id, t.site_id, t.task_type, t.task_name, t.priority, t.status, s.domaine
            FROM tasks t
            LEFT JOIN sites s ON t.site_id = s.id
            WHERE t.status = 'pending'
            ORDER BY t.priority ASC
            LIMIT 20
        """)
        context['tasks'] = [dict(row) for row in cursor.fetchall()]

        # Mots-clés suivis
        cursor.execute("""
            SELECT k.*, s.domaine
            FROM keywords k
            LEFT JOIN sites s ON k.site_id = s.id
            ORDER BY k.priorite DESC
            LIMIT 30
        """)
        context['keywords'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return context

    def query_ai(self, model, prompt, context=None):
        """Envoie une requête à Ollama avec contexte DB"""
        if context is None:
            context = self.get_context_for_ai()

        system_prompt = f"""Tu es un expert SEO. Voici le contexte actuel:

SITES GÉRÉS: {len(context['sites'])}
{json.dumps([{'domaine': s.get('domaine'), 'nom': s.get('nom')} for s in context['sites']], indent=2)}

ALERTES ACTIVES: {len(context['alerts'])} (top priorités)
{json.dumps([{'domaine': a.get('domaine'), 'type': a.get('alert_type'), 'priority': a.get('priority'), 'message': a.get('message')[:100]} for a in context['alerts'][:10]], indent=2)}

TÂCHES EN ATTENTE: {len(context['tasks'])}
{json.dumps([{'domaine': t.get('domaine'), 'type': t.get('task_type'), 'name': t.get('task_name', '')[:100]} for t in context['tasks'][:5]], indent=2)}

Réponds en français de manière concise et actionnable.
"""

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get('response', '')
            return f"Erreur Ollama: {response.status_code}"
        except Exception as e:
            return f"Erreur: {str(e)}"

    # ==========================================
    # SYNC: n8n Webhooks
    # ==========================================
    def notify_n8n(self, event_type, data):
        """Envoie une notification à n8n"""
        webhook_url = f"{N8N_URL}/webhook/seo-sync"
        try:
            response = requests.post(
                webhook_url,
                json={
                    'event': event_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    # ==========================================
    # SYNC: Écriture dans DB
    # ==========================================
    def sync_from_external(self, source, data):
        """Synchronise des données depuis une source externe"""
        conn = self.get_db()
        cursor = conn.cursor()

        log_entry = {
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'data_type': data.get('type'),
            'status': 'success'
        }

        try:
            if data.get('type') == 'new_site':
                cursor.execute("""
                    INSERT OR IGNORE INTO sites (domaine, nom, categorie, actif)
                    VALUES (?, ?, ?, 1)
                """, [data['domain'], data['name'], data.get('category')])

            elif data.get('type') == 'alert':
                cursor.execute("""
                    INSERT INTO site_alerts (site_id, alert_type, message, priority)
                    SELECT id, ?, ?, ? FROM sites WHERE domaine = ?
                """, [data['alert_type'], data['message'], data.get('priority', 'medium'), data['domain']])

            elif data.get('type') == 'task':
                cursor.execute("""
                    INSERT INTO tasks (site_id, task_type, task_name, priority, status)
                    SELECT id, ?, ?, ?, 'pending' FROM sites WHERE domaine = ?
                """, [data['task_type'], data.get('task_name', data.get('description', '')), data.get('priority', 5), data['domain']])

            elif data.get('type') == 'task_complete':
                cursor.execute("""
                    UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?
                """, [datetime.now().isoformat(), data['task_id']])

            elif data.get('type') == 'resolve_alert':
                cursor.execute("""
                    UPDATE site_alerts SET is_active = 0, resolved_at = ? WHERE id = ?
                """, [datetime.now().isoformat(), data['alert_id']])

            conn.commit()

        except Exception as e:
            log_entry['status'] = 'error'
            log_entry['error'] = str(e)

        # Log de synchronisation
        cursor.execute("""
            INSERT INTO agent_logs (agent_name, action, status, details, created_at)
            VALUES ('sync_bridge', 'external_sync', ?, ?, ?)
        """, [log_entry['status'], json.dumps(log_entry), datetime.now().isoformat()])
        conn.commit()
        conn.close()

        return log_entry

    # ==========================================
    # STATS & STATUS
    # ==========================================
    def get_sync_status(self):
        """Retourne le statut de synchronisation"""
        conn = self.get_db()
        cursor = conn.cursor()

        status = {
            'timestamp': datetime.now().isoformat(),
            'db_path': self.db_path,
            'components': {}
        }

        # DB Stats
        cursor.execute("SELECT COUNT(*) FROM sites WHERE actif = 1")
        status['components']['sqlite'] = {
            'status': 'ok',
            'sites': cursor.fetchone()[0]
        }
        cursor.execute("SELECT COUNT(*) FROM site_alerts WHERE is_active = 1")
        status['components']['sqlite']['alerts'] = cursor.fetchone()[0]

        conn.close()

        # Ollama
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                status['components']['ollama'] = {
                    'status': 'ok',
                    'models': [m['name'] for m in models]
                }
            else:
                status['components']['ollama'] = {'status': 'error'}
        except:
            status['components']['ollama'] = {'status': 'offline'}

        # n8n
        try:
            resp = requests.get(f"{N8N_URL}/healthz", timeout=5)
            status['components']['n8n'] = {
                'status': 'ok' if resp.status_code == 200 else 'error'
            }
        except:
            status['components']['n8n'] = {'status': 'offline'}

        return status


# ==========================================
# API FLASK
# ==========================================
bridge = SyncBridge()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'sync-bridge'})

@app.route('/status', methods=['GET'])
def status():
    return jsonify(bridge.get_sync_status())

@app.route('/context', methods=['GET'])
def get_context():
    """Contexte complet pour AI/Claude"""
    domain = request.args.get('domain')
    return jsonify(bridge.get_context_for_ai(domain))

@app.route('/query', methods=['POST'])
def query_ai():
    """Requête aux modèles AI avec contexte DB"""
    data = request.json
    model = data.get('model', 'qwen2.5:7b')
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'prompt requis'}), 400

    response = bridge.query_ai(model, prompt)
    return jsonify({
        'model': model,
        'prompt': prompt,
        'response': response
    })

@app.route('/sync', methods=['POST'])
def sync_data():
    """Reçoit des données à synchroniser"""
    data = request.json
    source = data.get('source', 'unknown')
    result = bridge.sync_from_external(source, data)
    return jsonify(result)

@app.route('/sites', methods=['GET'])
def get_sites():
    """Liste des sites pour intégration externe"""
    context = bridge.get_context_for_ai()
    return jsonify(context['sites'])

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Alertes actives"""
    context = bridge.get_context_for_ai()
    return jsonify(context['alerts'])

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Tâches en attente"""
    context = bridge.get_context_for_ai()
    return jsonify(context['tasks'])

# Webhook pour n8n
@app.route('/webhook/n8n', methods=['POST'])
def n8n_webhook():
    """Reçoit les événements de n8n"""
    data = request.json
    result = bridge.sync_from_external('n8n', data)
    return jsonify(result)


if __name__ == '__main__':
    print("="*60)
    print("🔄 SYNC BRIDGE - Pont de synchronisation SEO-AI")
    print("="*60)
    print(f"📁 Base de données: {DB_PATH}")
    print(f"🤖 Ollama: {OLLAMA_URL}")
    print(f"⚡ n8n: {N8N_URL}")
    print("="*60)

    # Afficher le statut initial
    status = bridge.get_sync_status()
    print("\n📊 STATUT INITIAL:")
    for comp, info in status['components'].items():
        print(f"   {comp}: {info.get('status', 'unknown')}")

    print("\n🚀 Démarrage du serveur sur port 8892...")
    app.run(host='0.0.0.0', port=8892)

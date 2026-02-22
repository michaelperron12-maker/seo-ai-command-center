# ============================================
# NOUVEAUX ENDPOINTS API - AI QWEN + CONFIG + ANALYTICS
# ============================================

import os
import json
import base64
import requests
from datetime import datetime

# Fireworks API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
GROQ_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"

# ============================================
# AI QWEN ENDPOINTS
# ============================================

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat avec Qwen 2.5 via Fireworks"""
    data = request.json or {}
    message = data.get('message', '')
    context = data.get('context', 'seo')  # seo, content, analysis

    if not message:
        return jsonify({'error': 'Message requis'}), 400

    system_prompts = {
        'seo': "Tu es un expert SEO. Aide avec les strategies de referencement, mots-cles, et optimisation de contenu. Reponds en francais.",
        'content': "Tu es un redacteur SEO expert. Cree du contenu optimise pour le referencement. Reponds en francais.",
        'analysis': "Tu es un analyste de donnees SEO. Analyse les metriques et donne des recommandations. Reponds en francais.",
        'general': "Tu es un assistant AI polyvalent. Reponds en francais de maniere concise et utile."
    }

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompts.get(context, system_prompts['general'])},
                {"role": "user", "content": message}
            ],
            "max_tokens": 2048,
            "temperature": 0.7
        }

        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            return jsonify({'error': f'Erreur Fireworks: {response.status_code}'}), 500

        result = response.json()
        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Sauvegarder dans l'historique
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_chat_history (context, user_message, ai_response, model, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (context, message, ai_response, QWEN_MODEL))
        conn.commit()
        conn.close()

        return jsonify({
            'response': ai_response,
            'model': QWEN_MODEL,
            'context': context
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/analyze-document', methods=['POST'])
def ai_analyze_document():
    """Analyse un document avec Qwen Vision - extraction infos concurrent -10%"""
    if 'file' not in request.files:
        return jsonify({'error': 'Fichier requis'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400

    try:
        # Lire et encoder le fichier
        file_data = base64.standard_b64encode(file.read()).decode('utf-8')

        # Determiner le type MIME
        ext = file.filename.lower().split('.')[-1]
        mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}
        mime_type = mime_types.get(ext, 'image/jpeg')

        prompt = """Tu es un expert en extraction de donnees depuis des documents.
Ce document est une soumission ou facture d'un CONCURRENT.

Extrais les informations suivantes:
- Nom du client ou entreprise
- Adresse complete
- Telephone
- Email
- Services demandes
- Prix du concurrent

REPONDS UNIQUEMENT en JSON valide:
{
    "nom_client": "...",
    "adresse": "...",
    "ville": "...",
    "code_postal": "...",
    "telephone": "...",
    "email": "...",
    "services": "...",
    "prix_concurrent": 0,
    "notes": "..."
}"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        payload = {
            "model": GROQ_VISION,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{file_data}"}}
                    ]
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.2
        }

        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            return jsonify({'error': f'Erreur Fireworks: {response.status_code}'}), 500

        result = response.json()
        text_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Parser le JSON
        try:
            # Nettoyer la reponse
            if '```json' in text_response:
                text_response = text_response.split('```json')[1].split('```')[0]
            elif '```' in text_response:
                text_response = text_response.split('```')[1].split('```')[0]

            text_response = text_response.strip()
            if not text_response.startswith('{'):
                start = text_response.find('{')
                end = text_response.rfind('}') + 1
                if start >= 0 and end > start:
                    text_response = text_response[start:end]

            extracted = json.loads(text_response)

            # Calculer prix recommande (-10%)
            prix_concurrent = float(extracted.get('prix_concurrent', 0) or 0)
            prix_recommande = round(prix_concurrent * 0.90, 2)

            return jsonify({
                'success': True,
                'extracted': extracted,
                'prix_concurrent': prix_concurrent,
                'prix_recommande': prix_recommande,
                'reduction': '10%',
                'model': QWEN_VL_MODEL
            })

        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'raw_response': text_response,
                'error': 'Impossible de parser le JSON'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/estimate', methods=['POST'])
def ai_estimate():
    """Estimation rapide -10% du prix concurrent"""
    data = request.json or {}
    prix_concurrent = float(data.get('prix_concurrent', 0))
    services = data.get('services', '')

    prix_recommande = round(prix_concurrent * 0.90, 2)
    economie = round(prix_concurrent - prix_recommande, 2)

    return jsonify({
        'prix_concurrent': prix_concurrent,
        'prix_recommande': prix_recommande,
        'reduction_percent': 10,
        'economie': economie,
        'services': services
    })


@app.route('/api/ai/history', methods=['GET'])
def ai_history():
    """Historique des conversations AI"""
    limit = int(request.args.get('limit', 20))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, context, user_message, ai_response, model, created_at
        FROM ai_chat_history
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({
        'history': [
            {
                'id': r[0],
                'context': r[1],
                'user_message': r[2],
                'ai_response': r[3],
                'model': r[4],
                'created_at': r[5]
            }
            for r in rows
        ]
    })


@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Status de l'API Fireworks/Qwen"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        response = requests.post(
            FIREWORKS_URL,
            headers=headers,
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": "OK"}],
                "max_tokens": 5
            },
            timeout=15
        )
        return jsonify({
            'status': 'online' if response.status_code == 200 else 'error',
            'model': QWEN_MODEL,
            'vision_model': QWEN_VL_MODEL,
            'api_key_configured': bool(FIREWORKS_API_KEY)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })


# ============================================
# CONFIG ENDPOINTS
# ============================================

@app.route('/api/config/full', methods=['GET'])
def get_full_config():
    """Configuration complete editable"""
    try:
        config_path = '/opt/seo-agent/config/config.yaml'
        with open(config_path, 'r') as f:
            import yaml
            config = yaml.safe_load(f)
        return jsonify({'config': config, 'path': config_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/update', methods=['POST'])
def update_config():
    """Mettre a jour la configuration"""
    data = request.json or {}
    section = data.get('section')
    key = data.get('key')
    value = data.get('value')

    if not section or not key:
        return jsonify({'error': 'Section et key requis'}), 400

    try:
        config_path = '/opt/seo-agent/config/config.yaml'
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if section not in config:
            config[section] = {}

        config[section][key] = value

        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        return jsonify({'success': True, 'section': section, 'key': key, 'value': value})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/sites', methods=['GET'])
def get_sites_config():
    """Configuration des sites"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sites')
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    conn.close()

    return jsonify({'sites': [dict(zip(cols, r)) for r in rows]})


@app.route('/api/config/sites/<int:site_id>', methods=['PUT'])
def update_site_config(site_id):
    """Mettre a jour un site"""
    data = request.json or {}

    conn = get_db()
    cursor = conn.cursor()

    updates = []
    values = []
    for key, value in data.items():
        if key not in ['id', 'created_at']:
            updates.append(f"{key} = ?")
            values.append(value)

    if updates:
        values.append(site_id)
        cursor.execute(f"UPDATE sites SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return jsonify({'success': True, 'site_id': site_id})


# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@app.route('/api/analytics/overview', methods=['GET'])
def analytics_overview():
    """Vue d'ensemble analytics (simulee - a connecter avec GA)"""
    # Placeholder - a connecter avec Google Analytics API
    return jsonify({
        'note': 'Connecter Google Analytics API pour donnees reelles',
        'placeholder_data': {
            'visitors_today': 0,
            'visitors_week': 0,
            'pageviews_today': 0,
            'bounce_rate': 0,
            'avg_session_duration': 0
        },
        'setup_required': True,
        'setup_url': 'https://console.cloud.google.com/apis/credentials'
    })


@app.route('/api/analytics/configure', methods=['POST'])
def configure_analytics():
    """Configurer Google Analytics"""
    data = request.json or {}
    ga_property_id = data.get('property_id')
    ga_credentials = data.get('credentials')

    if not ga_property_id:
        return jsonify({'error': 'Property ID requis'}), 400

    # Sauvegarder la config
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO system_state (key, value, updated_at)
        VALUES ('ga_property_id', ?, datetime('now'))
    ''', (ga_property_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'property_id': ga_property_id})


# ============================================
# TABLE CREATION - A EXECUTER UNE FOIS
# ============================================

def create_new_tables():
    """Creer les nouvelles tables"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context TEXT,
            user_message TEXT,
            ai_response TEXT,
            model TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# Appeler au demarrage
# create_new_tables()

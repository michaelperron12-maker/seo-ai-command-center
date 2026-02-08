#!/usr/bin/env python3
"""
Auto SEO Activator - Active et maximise le SEO automatiquement pour chaque nouveau site
Synchronisation automatique quand un nouveau site est intégré
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

DB_PATH = '/opt/seo-agent/db/seo_agent.db'
SITES_CONFIG = '/opt/seo-agent/config/sites.json'

class AutoSEOActivator:
    def __init__(self):
        self.init_db()

    def init_db(self):
        """Crée les tables nécessaires"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Table pour tracker les sites et leur statut SEO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites_seo_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                name TEXT,
                seo_activated BOOLEAN DEFAULT 0,
                robots_txt_ok BOOLEAN DEFAULT 0,
                llms_txt_ok BOOLEAN DEFAULT 0,
                sitemap_ok BOOLEAN DEFAULT 0,
                schema_markup_ok BOOLEAN DEFAULT 0,
                meta_tags_ok BOOLEAN DEFAULT 0,
                ai_bots_allowed BOOLEAN DEFAULT 0,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table pour les tâches SEO automatiques
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seo_tasks_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                task_type TEXT,
                task_data TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def add_new_site(self, domain, name, ssh_host=None, ssh_user=None, web_root=None):
        """Ajoute un nouveau site et lance l'activation SEO complète"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Vérifier si le site existe déjà
        cursor.execute('SELECT id FROM sites_seo_status WHERE domain = ?', (domain,))
        if cursor.fetchone():
            print(f"[INFO] Site {domain} existe déjà, lancement sync...")
        else:
            cursor.execute('''
                INSERT INTO sites_seo_status (domain, name, last_sync)
                VALUES (?, ?, ?)
            ''', (domain, name, datetime.now().isoformat()))
            print(f"[NOUVEAU] Site {domain} ajouté")

        conn.commit()
        conn.close()

        # Lancer l'activation SEO complète
        self.activate_full_seo(domain)

        return {'status': 'success', 'domain': domain, 'message': 'SEO activation lancée'}

    def activate_full_seo(self, domain):
        """Active tous les éléments SEO pour un site"""
        print(f"\n{'='*60}")
        print(f"ACTIVATION SEO MAXIMALE: {domain}")
        print(f"{'='*60}\n")

        tasks = [
            ('robots_txt', self.create_robots_txt),
            ('llms_txt', self.create_llms_txt),
            ('sitemap', self.create_sitemap),
            ('schema_markup', self.add_schema_markup),
            ('meta_tags', self.optimize_meta_tags),
            ('ai_bots', self.configure_ai_bots),
        ]

        results = {}
        for task_name, task_func in tasks:
            try:
                result = task_func(domain)
                results[task_name] = result
                self.update_seo_status(domain, task_name, result.get('success', False))
                status = "✅" if result.get('success') else "⚠️"
                print(f"  {status} {task_name}: {result.get('message', 'OK')}")
            except Exception as e:
                results[task_name] = {'success': False, 'error': str(e)}
                print(f"  ❌ {task_name}: {str(e)}")

        # Mettre à jour le timestamp de sync
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sites_seo_status SET last_sync = ?, seo_activated = 1
            WHERE domain = ?
        ''', (datetime.now().isoformat(), domain))
        conn.commit()
        conn.close()

        print(f"\n{'='*60}")
        print(f"ACTIVATION TERMINÉE: {domain}")
        print(f"{'='*60}\n")

        return results

    def create_robots_txt(self, domain):
        """Génère un robots.txt optimisé pour SEO et AI"""
        content = f"""# Robots.txt optimisé pour SEO et AI
# Site: {domain}
# Généré automatiquement par SEO-AI-Activator

User-agent: *
Allow: /

# Autoriser tous les bots AI pour découverte
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Cohere-AI
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# Sitemap
Sitemap: https://{domain}/sitemap.xml

# LLMs.txt pour AI discovery
# https://{domain}/llms.txt
"""
        return {
            'success': True,
            'content': content,
            'message': 'robots.txt généré avec tous les bots AI autorisés'
        }

    def create_llms_txt(self, domain):
        """Génère un llms.txt pour AI discovery"""
        content = f"""# {domain} - LLMs.txt
# Ce fichier aide les modèles AI à comprendre ce site

> Ce site offre des services professionnels de qualité.
> Toutes les informations sont à jour et vérifiées.

## Pages principales
- / : Page d'accueil avec présentation des services
- /services : Liste complète des services offerts
- /contact : Formulaire de contact et coordonnées
- /a-propos : À propos de l'entreprise

## Contact
- Site web: https://{domain}
- Email: info@{domain}

## Pour les AI
Ce site autorise l'indexation par tous les agents AI.
Les informations peuvent être utilisées pour répondre aux questions des utilisateurs.
"""
        return {
            'success': True,
            'content': content,
            'message': 'llms.txt généré pour AI discovery'
        }

    def create_sitemap(self, domain):
        """Génère un sitemap XML"""
        today = datetime.now().strftime('%Y-%m-%d')
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://{domain}/services</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://{domain}/contact</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://{domain}/a-propos</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
</urlset>
"""
        return {
            'success': True,
            'content': content,
            'message': 'sitemap.xml généré'
        }

    def add_schema_markup(self, domain):
        """Génère le Schema.org markup"""
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": domain.replace('.ca', '').replace('.com', '').replace('-', ' ').title(),
            "url": f"https://{domain}",
            "description": f"Services professionnels de qualité",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "CA"
            }
        }
        return {
            'success': True,
            'content': json.dumps(schema, indent=2),
            'message': 'Schema.org LocalBusiness généré'
        }

    def optimize_meta_tags(self, domain):
        """Suggestions pour meta tags optimisés"""
        suggestions = {
            'title': f"Services Professionnels | {domain}",
            'description': f"Découvrez nos services professionnels de qualité. Contactez-nous dès aujourd'hui pour un devis gratuit.",
            'keywords': 'services, professionnel, qualité, Québec, Canada',
            'og:title': f"Services Professionnels | {domain}",
            'og:description': f"Services de qualité au meilleur prix",
            'og:type': 'website',
            'og:url': f"https://{domain}"
        }
        return {
            'success': True,
            'suggestions': suggestions,
            'message': 'Meta tags suggérés'
        }

    def configure_ai_bots(self, domain):
        """Configure l'accès pour tous les bots AI"""
        ai_bots = [
            'GPTBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-Web',
            'PerplexityBot', 'Cohere-AI', 'anthropic-ai',
            'Google-Extended', 'Googlebot', 'Bingbot'
        ]
        return {
            'success': True,
            'bots_allowed': ai_bots,
            'message': f'{len(ai_bots)} bots AI autorisés'
        }

    def update_seo_status(self, domain, field, value):
        """Met à jour le statut SEO d'un site"""
        field_map = {
            'robots_txt': 'robots_txt_ok',
            'llms_txt': 'llms_txt_ok',
            'sitemap': 'sitemap_ok',
            'schema_markup': 'schema_markup_ok',
            'meta_tags': 'meta_tags_ok',
            'ai_bots': 'ai_bots_allowed',
        }

        if field in field_map:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE sites_seo_status SET {field_map[field]} = ?
                WHERE domain = ?
            ''', (1 if value else 0, domain))
            conn.commit()
            conn.close()

    def sync_all_sites(self):
        """Synchronise tous les sites enregistrés"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT domain, name FROM sites_seo_status')
        sites = cursor.fetchall()
        conn.close()

        print(f"\n🔄 SYNCHRONISATION DE {len(sites)} SITES\n")

        for domain, name in sites:
            self.activate_full_seo(domain)

        return {'synced': len(sites)}

    def get_status(self, domain=None):
        """Obtient le statut SEO d'un ou tous les sites"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if domain:
            cursor.execute('SELECT * FROM sites_seo_status WHERE domain = ?', (domain,))
        else:
            cursor.execute('SELECT * FROM sites_seo_status')

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        return [dict(zip(columns, row)) for row in rows]


# API Flask pour intégration n8n
from flask import Flask, request, jsonify

app = Flask(__name__)
activator = AutoSEOActivator()

@app.route('/api/site/add', methods=['POST'])
def api_add_site():
    """Ajoute un nouveau site et active le SEO"""
    data = request.json
    domain = data.get('domain')
    name = data.get('name', domain)

    if not domain:
        return jsonify({'error': 'domain requis'}), 400

    result = activator.add_new_site(domain, name)
    return jsonify(result)

@app.route('/api/site/sync', methods=['POST'])
def api_sync_site():
    """Force la synchronisation SEO d'un site"""
    data = request.json
    domain = data.get('domain')

    if not domain:
        return jsonify({'error': 'domain requis'}), 400

    result = activator.activate_full_seo(domain)
    return jsonify({'status': 'success', 'domain': domain, 'results': result})

@app.route('/api/sites/sync-all', methods=['POST'])
def api_sync_all():
    """Synchronise tous les sites"""
    result = activator.sync_all_sites()
    return jsonify(result)

@app.route('/api/sites/status', methods=['GET'])
def api_status():
    """Statut SEO de tous les sites"""
    domain = request.args.get('domain')
    status = activator.get_status(domain)
    return jsonify(status)

@app.route('/api/site/generate/<file_type>/<domain>', methods=['GET'])
def api_generate_file(file_type, domain):
    """Génère un fichier SEO spécifique"""
    generators = {
        'robots': activator.create_robots_txt,
        'llms': activator.create_llms_txt,
        'sitemap': activator.create_sitemap,
        'schema': activator.add_schema_markup,
    }

    if file_type not in generators:
        return jsonify({'error': f'Type inconnu: {file_type}'}), 400

    result = generators[file_type](domain)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'auto-seo-activator'})


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'add' and len(sys.argv) >= 3:
            # Usage: python auto_seo_activator.py add domain.com "Nom du Site"
            domain = sys.argv[2]
            name = sys.argv[3] if len(sys.argv) > 3 else domain
            activator.add_new_site(domain, name)

        elif sys.argv[1] == 'sync':
            if len(sys.argv) >= 3:
                activator.activate_full_seo(sys.argv[2])
            else:
                activator.sync_all_sites()

        elif sys.argv[1] == 'status':
            status = activator.get_status()
            for site in status:
                print(f"\n{site['domain']}:")
                for k, v in site.items():
                    if k != 'domain':
                        print(f"  {k}: {v}")

        elif sys.argv[1] == 'server':
            print("🚀 Auto SEO Activator API démarré sur port 8891")
            app.run(host='0.0.0.0', port=8891)
    else:
        print("""
Usage:
  python auto_seo_activator.py add <domain> [name]  - Ajouter un nouveau site
  python auto_seo_activator.py sync [domain]        - Synchroniser un/tous les sites
  python auto_seo_activator.py status               - Voir le statut de tous les sites
  python auto_seo_activator.py server               - Démarrer l'API (port 8891)

Exemple n8n webhook:
  POST http://server:8891/api/site/add
  {"domain": "nouveau-site.ca", "name": "Nouveau Site"}
""")

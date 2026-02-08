#!/usr/bin/env python3
"""
SITE AUDIT AGENT - Audit complet + Alertes permanentes
Surveille les 4 sites et alerte pour tout ce qui manque
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request

DB_PATH = '/opt/seo-agent/db/seo_agent.db'

app = Flask(__name__)

# ========================================
# CHECKLIST PAR SITE - Ce qui doit exister
# ========================================
CHECKLIST = {
    'reseaux_sociaux': [
        {'id': 'facebook_page', 'name': 'Page Facebook', 'priority': 'high'},
        {'id': 'facebook_linked', 'name': 'Facebook lie au site', 'priority': 'high'},
        {'id': 'instagram', 'name': 'Compte Instagram', 'priority': 'medium'},
        {'id': 'linkedin', 'name': 'Page LinkedIn', 'priority': 'medium'},
        {'id': 'twitter', 'name': 'Compte Twitter/X', 'priority': 'low'},
        {'id': 'youtube', 'name': 'Chaine YouTube', 'priority': 'low'},
        {'id': 'tiktok', 'name': 'Compte TikTok', 'priority': 'low'},
    ],
    'seo_local': [
        {'id': 'google_business', 'name': 'Google Business Profile', 'priority': 'critical'},
        {'id': 'google_business_verified', 'name': 'Google Business verifie', 'priority': 'critical'},
        {'id': 'google_business_photos', 'name': 'Photos Google Business (min 10)', 'priority': 'high'},
        {'id': 'google_business_posts', 'name': 'Posts Google Business reguliers', 'priority': 'medium'},
        {'id': 'bing_places', 'name': 'Bing Places', 'priority': 'medium'},
        {'id': 'apple_maps', 'name': 'Apple Maps Connect', 'priority': 'medium'},
        {'id': 'yelp', 'name': 'Page Yelp', 'priority': 'medium'},
        {'id': 'pages_jaunes', 'name': 'Pages Jaunes Canada', 'priority': 'high'},
    ],
    'forums_communautes': [
        {'id': 'reddit_account', 'name': 'Compte Reddit', 'priority': 'high'},
        {'id': 'reddit_karma', 'name': 'Reddit karma > 100', 'priority': 'medium'},
        {'id': 'reddit_posts', 'name': 'Posts Reddit pertinents', 'priority': 'medium'},
        {'id': 'quora', 'name': 'Compte Quora', 'priority': 'medium'},
        {'id': 'forums_locaux', 'name': 'Forums locaux Quebec', 'priority': 'medium'},
    ],
    'technique': [
        {'id': 'ssl_valid', 'name': 'SSL valide', 'priority': 'critical'},
        {'id': 'mobile_friendly', 'name': 'Mobile-friendly', 'priority': 'critical'},
        {'id': 'vitesse_ok', 'name': 'Vitesse < 3s', 'priority': 'high'},
        {'id': 'sitemap', 'name': 'Sitemap.xml', 'priority': 'high'},
        {'id': 'robots_txt', 'name': 'Robots.txt', 'priority': 'high'},
        {'id': 'schema_markup', 'name': 'Schema markup LocalBusiness', 'priority': 'high'},
        {'id': 'meta_tags', 'name': 'Meta title/description', 'priority': 'critical'},
        {'id': 'h1_tags', 'name': 'H1 sur chaque page', 'priority': 'high'},
        {'id': 'alt_images', 'name': 'Alt text sur images', 'priority': 'medium'},
        {'id': 'analytics', 'name': 'Google Analytics installe', 'priority': 'high'},
        {'id': 'search_console', 'name': 'Google Search Console', 'priority': 'critical'},
    ],
    'contenu': [
        {'id': 'page_accueil', 'name': 'Page accueil optimisee', 'priority': 'critical'},
        {'id': 'page_services', 'name': 'Page services', 'priority': 'critical'},
        {'id': 'page_contact', 'name': 'Page contact avec formulaire', 'priority': 'critical'},
        {'id': 'page_apropos', 'name': 'Page a propos', 'priority': 'high'},
        {'id': 'blog_actif', 'name': 'Blog avec articles', 'priority': 'high'},
        {'id': 'temoignages', 'name': 'Page temoignages/avis', 'priority': 'high'},
        {'id': 'faq', 'name': 'Page FAQ', 'priority': 'medium'},
        {'id': 'zones_service', 'name': 'Pages zones de service', 'priority': 'high'},
    ],
    'backlinks': [
        {'id': 'annuaires_locaux', 'name': 'Annuaires locaux (min 10)', 'priority': 'high'},
        {'id': 'guest_posts', 'name': 'Guest posts (min 3)', 'priority': 'medium'},
        {'id': 'partenaires', 'name': 'Liens partenaires', 'priority': 'medium'},
        {'id': 'citations_nap', 'name': 'Citations NAP coherentes', 'priority': 'critical'},
    ],
}

# ========================================
# TACHES HEBDOMADAIRES
# ========================================
WEEKLY_TASKS = [
    {'id': 'blog_post', 'name': 'Publier 1 article blog', 'frequency': 'weekly'},
    {'id': 'google_post', 'name': 'Post Google Business', 'frequency': 'weekly'},
    {'id': 'social_posts', 'name': 'Posts reseaux sociaux (3-5)', 'frequency': 'weekly'},
    {'id': 'check_reviews', 'name': 'Repondre aux avis', 'frequency': 'weekly'},
    {'id': 'check_rankings', 'name': 'Verifier positions keywords', 'frequency': 'weekly'},
    {'id': 'backlink_outreach', 'name': 'Outreach 2-3 backlinks', 'frequency': 'weekly'},
    {'id': 'competitor_check', 'name': 'Analyse concurrents', 'frequency': 'monthly'},
    {'id': 'technical_audit', 'name': 'Audit technique', 'frequency': 'monthly'},
    {'id': 'content_update', 'name': 'Mise a jour contenu ancien', 'frequency': 'monthly'},
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table audit par site
    cursor.execute('''CREATE TABLE IF NOT EXISTS site_audit_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        check_id TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT DEFAULT 'not_done',
        notes TEXT,
        completed_at TEXT,
        last_checked TEXT,
        UNIQUE(site_id, check_id)
    )''')
    
    # Table alertes actives
    cursor.execute('''CREATE TABLE IF NOT EXISTS site_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        alert_type TEXT NOT NULL,
        check_id TEXT,
        message TEXT NOT NULL,
        priority TEXT DEFAULT 'medium',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        resolved_at TEXT
    )''')
    
    # Table taches hebdomadaires
    cursor.execute('''CREATE TABLE IF NOT EXISTS weekly_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        task_id TEXT NOT NULL,
        week_number INTEGER NOT NULL,
        year INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        completed_at TEXT,
        notes TEXT,
        UNIQUE(site_id, task_id, week_number, year)
    )''')
    
    conn.commit()
    conn.close()

def get_sites():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, nom, domaine FROM sites WHERE actif = 1')
    sites = [{'id': r[0], 'name': r[1], 'domain': r[2]} for r in cursor.fetchall()]
    conn.close()
    return sites

def audit_site(site_id):
    """Audit complet d'un site - genere alertes pour tout ce qui manque"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    alerts = []
    status_report = {}
    
    for category, checks in CHECKLIST.items():
        status_report[category] = []
        for check in checks:
            # Verifier si fait
            cursor.execute('SELECT status, completed_at FROM site_audit_status WHERE site_id = ? AND check_id = ?', 
                          (site_id, check['id']))
            result = cursor.fetchone()
            
            if result and result[0] == 'done':
                status_report[category].append({
                    'id': check['id'],
                    'name': check['name'],
                    'status': 'done',
                    'completed_at': result[1]
                })
            else:
                # Pas fait = creer alerte
                status_report[category].append({
                    'id': check['id'],
                    'name': check['name'],
                    'status': 'not_done',
                    'priority': check['priority']
                })
                
                # Ajouter alerte si pas deja active
                cursor.execute('SELECT id FROM site_alerts WHERE site_id = ? AND check_id = ? AND is_active = 1',
                              (site_id, check['id']))
                if not cursor.fetchone():
                    cursor.execute('''INSERT INTO site_alerts (site_id, alert_type, check_id, message, priority)
                        VALUES (?, 'missing', ?, ?, ?)''',
                        (site_id, check['id'], f'MANQUANT: {check["name"]}', check['priority']))
                
                alerts.append({
                    'check': check['name'],
                    'priority': check['priority'],
                    'category': category
                })
            
            # Mettre a jour last_checked
            cursor.execute('''INSERT OR REPLACE INTO site_audit_status (site_id, check_id, category, status, last_checked)
                VALUES (?, ?, ?, COALESCE((SELECT status FROM site_audit_status WHERE site_id = ? AND check_id = ?), 'not_done'), ?)''',
                (site_id, check['id'], category, site_id, check['id'], datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {
        'site_id': site_id,
        'audit_date': datetime.now().isoformat(),
        'status': status_report,
        'alerts': alerts,
        'total_checks': sum(len(checks) for checks in CHECKLIST.values()),
        'done': sum(1 for cat in status_report.values() for item in cat if item['status'] == 'done'),
        'missing': len(alerts)
    }

def get_all_alerts(site_id=None):
    """Recupere toutes les alertes actives"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if site_id:
        cursor.execute('''SELECT a.id, a.site_id, s.nom, a.alert_type, a.check_id, a.message, a.priority, a.created_at
            FROM site_alerts a JOIN sites s ON a.site_id = s.id
            WHERE a.is_active = 1 AND a.site_id = ?
            ORDER BY CASE a.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END''',
            (site_id,))
    else:
        cursor.execute('''SELECT a.id, a.site_id, s.nom, a.alert_type, a.check_id, a.message, a.priority, a.created_at
            FROM site_alerts a JOIN sites s ON a.site_id = s.id
            WHERE a.is_active = 1
            ORDER BY CASE a.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END''')
    
    alerts = [{'id': r[0], 'site_id': r[1], 'site_name': r[2], 'type': r[3], 'check_id': r[4], 
               'message': r[5], 'priority': r[6], 'created_at': r[7]} for r in cursor.fetchall()]
    conn.close()
    return alerts

def mark_done(site_id, check_id, notes=None):
    """Marque un element comme fait"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Mettre a jour status
    cursor.execute('''INSERT OR REPLACE INTO site_audit_status (site_id, check_id, category, status, notes, completed_at, last_checked)
        VALUES (?, ?, 
            COALESCE((SELECT category FROM site_audit_status WHERE site_id = ? AND check_id = ?), 'other'),
            'done', ?, ?, ?)''',
        (site_id, check_id, site_id, check_id, notes, now, now))
    
    # Desactiver alerte
    cursor.execute('UPDATE site_alerts SET is_active = 0, resolved_at = ? WHERE site_id = ? AND check_id = ? AND is_active = 1',
                  (now, site_id, check_id))
    
    conn.commit()
    conn.close()
    return {'success': True, 'message': f'{check_id} marque comme fait'}

def get_weekly_tasks(site_id=None):
    """Recupere les taches de la semaine"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now()
    week = now.isocalendar()[1]
    year = now.year
    
    sites = get_sites()
    result = {}
    
    for site in sites:
        if site_id and site['id'] != site_id:
            continue
            
        result[site['name']] = []
        for task in WEEKLY_TASKS:
            if task['frequency'] == 'monthly' and week % 4 != 0:
                continue
                
            cursor.execute('SELECT status, completed_at FROM weekly_tasks WHERE site_id = ? AND task_id = ? AND week_number = ? AND year = ?',
                          (site['id'], task['id'], week, year))
            row = cursor.fetchone()
            
            if row:
                result[site['name']].append({
                    'task_id': task['id'],
                    'name': task['name'],
                    'status': row[0],
                    'completed_at': row[1]
                })
            else:
                # Creer la tache
                cursor.execute('''INSERT INTO weekly_tasks (site_id, task_id, week_number, year)
                    VALUES (?, ?, ?, ?)''', (site['id'], task['id'], week, year))
                result[site['name']].append({
                    'task_id': task['id'],
                    'name': task['name'],
                    'status': 'pending',
                    'completed_at': None
                })
    
    conn.commit()
    conn.close()
    return {'week': week, 'year': year, 'tasks': result}

def complete_weekly_task(site_id, task_id, notes=None):
    """Complete une tache hebdomadaire"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now()
    week = now.isocalendar()[1]
    year = now.year
    
    cursor.execute('''UPDATE weekly_tasks SET status = 'done', completed_at = ?, notes = ?
        WHERE site_id = ? AND task_id = ? AND week_number = ? AND year = ?''',
        (now.isoformat(), notes, site_id, task_id, week, year))
    
    conn.commit()
    conn.close()
    return {'success': True}

def get_dashboard():
    """Dashboard global - vue d'ensemble"""
    sites = get_sites()
    alerts = get_all_alerts()
    weekly = get_weekly_tasks()
    
    summary = {
        'sites': len(sites),
        'total_alerts': len(alerts),
        'critical_alerts': len([a for a in alerts if a['priority'] == 'critical']),
        'high_alerts': len([a for a in alerts if a['priority'] == 'high']),
        'weekly_tasks_pending': sum(1 for site_tasks in weekly['tasks'].values() for t in site_tasks if t['status'] == 'pending'),
        'sites_status': []
    }
    
    for site in sites:
        site_alerts = [a for a in alerts if a['site_id'] == site['id']]
        summary['sites_status'].append({
            'name': site['name'],
            'domain': site['domain'],
            'alerts': len(site_alerts),
            'critical': len([a for a in site_alerts if a['priority'] == 'critical'])
        })
    
    return summary

# ========================================
# ROUTES API
# ========================================

@app.route('/audit/dashboard', methods=['GET'])
def api_dashboard():
    return jsonify(get_dashboard())

@app.route('/audit/site/<int:site_id>', methods=['GET'])
def api_audit_site(site_id):
    return jsonify(audit_site(site_id))

@app.route('/audit/all', methods=['POST'])
def api_audit_all():
    sites = get_sites()
    results = []
    for site in sites:
        results.append(audit_site(site['id']))
    return jsonify({'audits': results, 'total_sites': len(sites)})

@app.route('/audit/alerts', methods=['GET'])
def api_get_alerts():
    site_id = request.args.get('site_id')
    alerts = get_all_alerts(int(site_id) if site_id else None)
    return jsonify({'alerts': alerts, 'count': len(alerts)})

@app.route('/audit/mark-done', methods=['POST'])
def api_mark_done():
    data = request.get_json() or {}
    result = mark_done(data.get('site_id'), data.get('check_id'), data.get('notes'))
    return jsonify(result)

@app.route('/audit/weekly-tasks', methods=['GET'])
def api_weekly_tasks():
    site_id = request.args.get('site_id')
    return jsonify(get_weekly_tasks(int(site_id) if site_id else None))

@app.route('/audit/complete-task', methods=['POST'])
def api_complete_task():
    data = request.get_json() or {}
    result = complete_weekly_task(data.get('site_id'), data.get('task_id'), data.get('notes'))
    return jsonify(result)

@app.route('/audit/checklist', methods=['GET'])
def api_checklist():
    return jsonify({'checklist': CHECKLIST, 'weekly_tasks': WEEKLY_TASKS})

@app.route('/audit/sites', methods=['GET'])
def api_sites():
    return jsonify({'sites': get_sites()})

if __name__ == '__main__':
    init_db()
    print('[SITE AUDIT] Demarrage agent audit...')
    print(f'[SITE AUDIT] {sum(len(c) for c in CHECKLIST.values())} checks par site')
    print(f'[SITE AUDIT] {len(WEEKLY_TASKS)} taches hebdomadaires')
    app.run(host='0.0.0.0', port=8889, debug=False)

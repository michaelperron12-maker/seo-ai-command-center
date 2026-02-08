#!/usr/bin/env python3
"""
Site Scanner - Vérifie ce qui existe déjà sur chaque site
Les agents consultent ce scan avant d'agir pour éviter les doublons
"""

import requests
import sqlite3
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

DB_PATH = '/opt/seo-agent/db/seo_agent.db'

SITES = [
    {'id': 1, 'name': 'Déneigement Excellence', 'domain': 'deneigement-excellence.ca'},
    {'id': 2, 'name': 'Paysagiste Excellence', 'domain': 'paysagiste-excellence.ca'},
    {'id': 3, 'name': 'JC Peintre', 'domain': 'jcpeintre.com'},
    {'id': 4, 'name': 'SEO par AI', 'domain': 'seoparai.com'},
]

def init_db():
    """Crée la table site_status si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            domain TEXT,
            check_type TEXT,
            check_name TEXT,
            is_present BOOLEAN,
            value TEXT,
            last_checked TIMESTAMP,
            UNIQUE(site_id, check_type, check_name)
        )
    ''')
    conn.commit()
    conn.close()

def get_page(url, timeout=10):
    """Récupère une page web"""
    try:
        headers = {'User-Agent': 'SEO-AI-Scanner/1.0'}
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        return resp
    except:
        return None

def scan_site(site):
    """Scan complet d'un site"""
    domain = site['domain']
    site_id = site['id']
    results = []

    # Essayer HTTPS puis HTTP
    base_url = f"https://{domain}"
    resp = get_page(base_url)
    if not resp or resp.status_code != 200:
        base_url = f"http://{domain}"
        resp = get_page(base_url)

    if not resp or resp.status_code != 200:
        print(f"[ERREUR] {domain} non accessible")
        return results

    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')

    # === META TAGS ===
    # Title
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else None
    results.append({
        'check_type': 'meta',
        'check_name': 'title',
        'is_present': bool(title),
        'value': title[:200] if title else None
    })

    # Description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    desc = meta_desc.get('content', '').strip() if meta_desc else None
    results.append({
        'check_type': 'meta',
        'check_name': 'description',
        'is_present': bool(desc),
        'value': desc[:500] if desc else None
    })

    # Keywords
    meta_kw = soup.find('meta', attrs={'name': 'keywords'})
    kw = meta_kw.get('content', '').strip() if meta_kw else None
    results.append({
        'check_type': 'meta',
        'check_name': 'keywords',
        'is_present': bool(kw),
        'value': kw[:500] if kw else None
    })

    # === PAGES ===
    pages_to_check = [
        ('contact', ['/contact', '/contact.html', '/contactez-nous', '/nous-joindre']),
        ('services', ['/services', '/services.html', '/nos-services']),
        ('about', ['/a-propos', '/about', '/a-propos.html', '/qui-sommes-nous']),
        ('faq', ['/faq', '/faq.html', '/questions']),
        ('blog', ['/blog', '/blogue', '/articles', '/actualites']),
    ]

    for page_name, urls in pages_to_check:
        found = False
        found_url = None
        for url in urls:
            resp = get_page(f"{base_url}{url}")
            if resp and resp.status_code == 200:
                found = True
                found_url = url
                break
        results.append({
            'check_type': 'page',
            'check_name': page_name,
            'is_present': found,
            'value': found_url
        })

    # === FICHIERS TECHNIQUES ===
    # Sitemap
    sitemap_resp = get_page(f"{base_url}/sitemap.xml")
    results.append({
        'check_type': 'technical',
        'check_name': 'sitemap',
        'is_present': sitemap_resp and sitemap_resp.status_code == 200,
        'value': '/sitemap.xml' if sitemap_resp and sitemap_resp.status_code == 200 else None
    })

    # Robots.txt
    robots_resp = get_page(f"{base_url}/robots.txt")
    results.append({
        'check_type': 'technical',
        'check_name': 'robots',
        'is_present': robots_resp and robots_resp.status_code == 200,
        'value': '/robots.txt' if robots_resp and robots_resp.status_code == 200 else None
    })

    # === SCHEMA MARKUP ===
    schema_scripts = soup.find_all('script', type='application/ld+json')
    schema_types = []
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                schema_types.append(data.get('@type', 'Unknown'))
            elif isinstance(data, list):
                for item in data:
                    schema_types.append(item.get('@type', 'Unknown'))
        except:
            pass
    results.append({
        'check_type': 'schema',
        'check_name': 'structured_data',
        'is_present': len(schema_types) > 0,
        'value': ', '.join(schema_types) if schema_types else None
    })

    # === H1 TAG ===
    h1_tags = soup.find_all('h1')
    results.append({
        'check_type': 'seo',
        'check_name': 'h1',
        'is_present': len(h1_tags) > 0,
        'value': h1_tags[0].text.strip()[:200] if h1_tags else None
    })

    # === IMAGES ALT ===
    images = soup.find_all('img')
    images_with_alt = [img for img in images if img.get('alt')]
    results.append({
        'check_type': 'seo',
        'check_name': 'images_alt',
        'is_present': len(images_with_alt) == len(images) and len(images) > 0,
        'value': f"{len(images_with_alt)}/{len(images)} images avec alt"
    })

    # === SSL ===
    ssl_ok = base_url.startswith('https')
    results.append({
        'check_type': 'technical',
        'check_name': 'ssl',
        'is_present': ssl_ok,
        'value': 'HTTPS actif' if ssl_ok else 'HTTP seulement'
    })

    return results

def save_results(site_id, domain, results):
    """Sauvegarde les résultats dans la DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for result in results:
        cursor.execute('''
            INSERT OR REPLACE INTO site_status
            (site_id, domain, check_type, check_name, is_present, value, last_checked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            site_id,
            domain,
            result['check_type'],
            result['check_name'],
            result['is_present'],
            result['value'],
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

def check_before_action(site_id, check_type, check_name):
    """
    Les agents appellent cette fonction AVANT de créer quelque chose
    Retourne True si l'élément existe déjà, False sinon
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT is_present, value FROM site_status
        WHERE site_id = ? AND check_type = ? AND check_name = ?
    ''', (site_id, check_type, check_name))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {'is_present': bool(row[0]), 'value': row[1]}
    return {'is_present': False, 'value': None}

def get_site_summary(site_id):
    """Résumé de ce qui existe sur un site"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT check_type, check_name, is_present, value
        FROM site_status WHERE site_id = ?
        ORDER BY check_type, check_name
    ''', (site_id,))
    rows = cursor.fetchall()
    conn.close()

    summary = {'is_present': [], 'missing': []}
    for row in rows:
        item = {'type': row[0], 'name': row[1], 'value': row[3]}
        if row[2]:
            summary['is_present'].append(item)
        else:
            summary['missing'].append(item)
    return summary

def scan_all_sites():
    """Scan tous les sites et sauvegarde les résultats"""
    print("=" * 60)
    print("SCAN COMPLET DE TOUS LES SITES")
    print("=" * 60)

    init_db()

    for site in SITES:
        print(f"\n[SCAN] {site['name']} ({site['domain']})")
        results = scan_site(site)

        if results:
            save_results(site['id'], site['domain'], results)

            exists_count = len([r for r in results if r['is_present']])
            missing_count = len([r for r in results if not r['is_present']])

            print(f"  ✅ {exists_count} éléments présents")
            print(f"  ❌ {missing_count} éléments manquants")

            # Afficher détails
            for r in results:
                status = "✅" if r['is_present'] else "❌"
                print(f"    {status} {r['check_type']}/{r['check_name']}: {r['value'] or 'MANQUANT'}")

    print("\n" + "=" * 60)
    print("SCAN TERMINÉ - Résultats sauvegardés dans la DB")
    print("Les agents vont maintenant vérifier avant d'agir")
    print("=" * 60)

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    scan_all_sites()

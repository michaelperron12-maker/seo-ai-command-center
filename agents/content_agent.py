#!/usr/bin/env python3
"""
Content Agent - Generation automatique d'articles SEO et FAQ
Utilise Qwen 235B via Fireworks API
"""

import os
import json
import sqlite3
import requests
from datetime import datetime

# Configuration
DB_PATH = '/opt/seo-agent/db/seo_agent.db'
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY', 'fw_CbsGnsaL5NSi4wgasWhjtQ')
FIREWORKS_URL = 'https://api.fireworks.ai/inference/v1/chat/completions'
QWEN_MODEL = 'accounts/fireworks/models/qwen3-235b-a22b-instruct-2507'

# Sites configuration
SITES = {
    1: {'nom': 'Deneigement Excellence', 'domaine': 'deneigement-excellence.ca', 'niche': 'deneigement'},
    2: {'nom': 'Paysagiste Excellence', 'domaine': 'paysagiste-excellence.ca', 'niche': 'paysagement'},
    3: {'nom': 'JC Peintre', 'domaine': 'jcpeintre.com', 'niche': 'peinture'}
}

def get_db():
    return sqlite3.connect(DB_PATH)

def call_qwen(prompt, max_tokens=2500):
    """Appel API Qwen via Fireworks"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {FIREWORKS_API_KEY}'
        }
        payload = {
            'model': QWEN_MODEL,
            'messages': [
                {'role': 'system', 'content': 'Tu es un expert en redaction SEO. Ecris du contenu optimise pour le referencement en francais canadien.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
        response = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"Erreur API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erreur Qwen: {e}")
        return None

def get_keywords_for_site(site_id, limit=5):
    """Recupere les mots-cles prioritaires pour un site"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mot_cle, volume, difficulte
        FROM keywords
        WHERE site_id = ? AND statut IN ('nouveau', 'en_cours', 'brief_cree')
        ORDER BY priorite ASC, volume DESC
        LIMIT ?
    ''', (site_id, limit))
    keywords = cursor.fetchall()
    conn.close()
    return keywords

def generate_article(site_id, keyword, keyword_volume):
    """Genere un article SEO complet"""
    site = SITES.get(site_id, {})

    prompt = f"""Ecris un article de blog SEO complet pour le site {site.get('nom', '')} ({site.get('domaine', '')}).

MOT-CLE PRINCIPAL: {keyword}
VOLUME DE RECHERCHE: {keyword_volume} recherches/mois
NICHE: {site.get('niche', '')}
REGION: Quebec, Canada

STRUCTURE REQUISE:
1. Titre accrocheur avec le mot-cle (H1)
2. Meta description (155 caracteres max)
3. Introduction engageante (150 mots)
4. 3-4 sections avec sous-titres H2
5. Conseils pratiques
6. Conclusion avec appel a l'action
7. FAQ avec 3 questions/reponses

REGLES SEO:
- Densite mot-cle: 1-2%
- Utiliser des variations du mot-cle
- Phrases courtes et claires
- Listes a puces quand pertinent
- Ton professionnel mais accessible

FORMAT DE REPONSE (JSON):
{{
    "titre": "...",
    "meta_description": "...",
    "contenu": "... (article complet en HTML)",
    "faq": [
        {{"question": "...", "reponse": "..."}},
        {{"question": "...", "reponse": "..."}},
        {{"question": "...", "reponse": "..."}}
    ],
    "mots_cles_utilises": ["...", "..."]
}}
"""

    response = call_qwen(prompt, max_tokens=3000)
    if response:
        try:
            # Nettoyer la reponse JSON
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            return json.loads(response.strip())
        except json.JSONDecodeError:
            print("Erreur parsing JSON article")
            return {'titre': keyword, 'contenu': response, 'meta_description': '', 'faq': []}
    return None

def generate_faq_page(site_id):
    """Genere une page FAQ complete pour un site"""
    site = SITES.get(site_id, {})
    keywords = get_keywords_for_site(site_id, limit=10)
    keywords_list = ', '.join([k[0] for k in keywords])

    prompt = f"""Cree une page FAQ complete pour {site.get('nom', '')} ({site.get('domaine', '')}).

NICHE: {site.get('niche', '')}
MOTS-CLES A COUVRIR: {keywords_list}
REGION: Quebec, Canada

Genere 15 questions/reponses pertinentes couvrant:
- Services offerts
- Prix et soumissions
- Zones desservies
- Processus de travail
- Garanties
- Questions techniques

FORMAT JSON:
{{
    "titre_page": "FAQ - Questions Frequentes",
    "meta_description": "...",
    "intro": "...",
    "categories": [
        {{
            "nom": "Services",
            "questions": [
                {{"q": "...", "r": "..."}}
            ]
        }}
    ]
}}
"""

    response = call_qwen(prompt, max_tokens=3500)
    if response:
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            return json.loads(response.strip())
        except:
            return None
    return None

def generate_service_description(site_id, service_name):
    """Genere une description de service SEO"""
    site = SITES.get(site_id, {})

    prompt = f"""Ecris une description de service SEO pour {site.get('nom', '')}.

SERVICE: {service_name}
NICHE: {site.get('niche', '')}
REGION: Quebec, Canada

Inclure:
- Description detaillee (200-300 mots)
- Avantages (liste)
- Processus en etapes
- Appel a l'action

FORMAT JSON:
{{
    "titre": "...",
    "description": "...",
    "avantages": ["...", "..."],
    "processus": ["Etape 1: ...", "Etape 2: ..."],
    "cta": "..."
}}
"""

    response = call_qwen(prompt, max_tokens=1500)
    if response:
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            return json.loads(response.strip())
        except:
            return None
    return None

def save_draft(site_id, titre, contenu, mot_cle, content_type='article'):
    """Sauvegarde un brouillon dans la DB"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO drafts (site_id, titre, contenu, mot_cle, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', datetime('now'))
    ''', (site_id, titre, contenu, mot_cle))
    draft_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[Content Agent] Draft #{draft_id} cree: {titre}")
    return draft_id

def run_content_generation(site_id='all'):
    """Execute la generation de contenu pour un ou tous les sites"""
    print(f"[Content Agent] Demarrage generation contenu - {datetime.now()}")

    sites_to_process = list(SITES.keys()) if site_id == 'all' else [int(site_id)]

    for sid in sites_to_process:
        site = SITES.get(sid)
        if not site:
            continue

        print(f"[Content Agent] Traitement: {site['nom']}")

        # Recuperer les mots-cles prioritaires
        keywords = get_keywords_for_site(sid, limit=2)

        for kw, volume, difficulty in keywords:
            print(f"[Content Agent] Generation article pour: {kw}")

            # Generer l'article
            article = generate_article(sid, kw, volume)

            if article:
                # Sauvegarder le draft
                contenu_json = json.dumps(article, ensure_ascii=False)
                save_draft(sid, article.get('titre', kw), contenu_json, kw)
                print(f"[Content Agent] Article genere: {article.get('titre', kw)}")
            else:
                print(f"[Content Agent] Echec generation pour: {kw}")

    print(f"[Content Agent] Generation terminee - {datetime.now()}")

def run_faq_generation(site_id='all'):
    """Genere les pages FAQ"""
    print(f"[Content Agent] Generation FAQ - {datetime.now()}")

    sites_to_process = list(SITES.keys()) if site_id == 'all' else [int(site_id)]

    for sid in sites_to_process:
        site = SITES.get(sid)
        if not site:
            continue

        print(f"[Content Agent] FAQ pour: {site['nom']}")
        faq = generate_faq_page(sid)

        if faq:
            contenu_json = json.dumps(faq, ensure_ascii=False)
            save_draft(sid, f"FAQ - {site['nom']}", contenu_json, 'faq', 'faq')
            print(f"[Content Agent] FAQ generee pour {site['nom']}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        site = sys.argv[2] if len(sys.argv) > 2 else 'all'

        if command == 'articles':
            run_content_generation(site)
        elif command == 'faq':
            run_faq_generation(site)
        elif command == 'all':
            run_content_generation(site)
            run_faq_generation(site)
    else:
        print("Usage: python content_agent.py [articles|faq|all] [site_id|all]")
        print("Exemple: python content_agent.py articles 1")
        print("         python content_agent.py faq all")

#!/usr/bin/env python3
"""
SEO AI Agents System - 30 Agents Specialises
Systeme complet d'automatisation SEO avec Qwen AI
"""

import os
import json
import sqlite3
import requests
import subprocess
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
import hashlib

# Configuration
DB_PATH = '/opt/seo-agent/db/seo_agent.db'
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY', 'fw_CbsGnsaL5NSi4wgasWhjtQ')
FIREWORKS_URL = 'https://api.fireworks.ai/inference/v1/chat/completions'

# Modeles disponibles - DeepSeek R1 pour meilleur raisonnement
DEEPSEEK_R1 = 'accounts/fireworks/models/deepseek-r1-0528'
QWEN_MODEL = 'accounts/fireworks/models/qwen3-235b-a22b-instruct-2507'
LLAMA_MODEL = 'accounts/fireworks/models/llama-v3p3-70b-instruct'

# Modele actif - DeepSeek R1 pour qualite pro
ACTIVE_MODEL = DEEPSEEK_R1

# Ollama Local Config - Support DeepSeek + Qwen
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'qwen2.5:7b'  # Modele par defaut
OLLAMA_DEEPSEEK = 'deepseek-r1:7b'  # Si installe localement

SITES = {
    1: {'nom': 'Deneigement Excellence', 'domaine': 'deneigement-excellence.ca', 'niche': 'deneigement', 'path': '/var/www/deneigement'},
    2: {'nom': 'Paysagiste Excellence', 'domaine': 'paysagiste-excellence.ca', 'niche': 'paysagement', 'path': '/var/www/paysagement'},
    3: {'nom': 'JC Peintre', 'domaine': 'jcpeintre.com', 'niche': 'peinture', 'path': '/var/www/jcpeintre.com'},
    4: {'nom': 'SEO par AI', 'domaine': 'seoparai.com', 'niche': 'seo-marketing', 'path': '/var/www/dashboard', 'homepage': 'landing.html'}
}

def get_db():
    return sqlite3.connect(DB_PATH)

def call_qwen(prompt, max_tokens=2000, system_prompt=None):
    """Appel API Qwen via Fireworks"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {FIREWORKS_API_KEY}'
        }
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        payload = {
            'model': ACTIVE_MODEL,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
        response = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"Erreur Qwen: {e}")
        return None

def call_ollama(prompt, max_tokens=1000, use_deepseek=False):
    """
    Appel Ollama LOCAL - Gratuit et rapide
    use_deepseek=True -> Utilise DeepSeek R1 local si disponible
    use_deepseek=False -> Utilise Qwen 2.5 7B
    """
    try:
        model = OLLAMA_DEEPSEEK if use_deepseek else OLLAMA_MODEL
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_predict': max_tokens,
                'temperature': 0.7
            }
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        if response.status_code == 200:
            return response.json().get('response', '')
        # Fallback vers Qwen si DeepSeek pas disponible
        if use_deepseek:
            payload['model'] = OLLAMA_MODEL
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get('response', '')
        return None
    except Exception as e:
        print(f"Erreur Ollama: {e}")
        return None


def call_ai(prompt, max_tokens=2000, use_local=False, system_prompt=None):
    """
    Fonction hybride: choisit entre Ollama local et Fireworks
    use_local=True  -> Ollama (gratuit, petites taches)
    use_local=False -> Fireworks (payant, taches complexes)
    """
    if use_local:
        # Ollama pour petites taches
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        result = call_ollama(full_prompt, max_tokens)
        if result:
            return result
        # Fallback vers Fireworks si Ollama echoue
        print("[AI] Ollama failed, fallback to Fireworks")

    return call_qwen(prompt, max_tokens, system_prompt)


def log_agent(agent_name, message, level='INFO'):
    """Log agent activity"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{agent_name}] {level}: {message}")

    # Save to DB
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO agent_logs (agent, message, level, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (agent_name, message, level))
        conn.commit()
        conn.close()
    except:
        pass

# ============================================
# AGENT 1: KEYWORD RESEARCH AGENT
# ============================================
class KeywordResearchAgent:
    name = "Keyword Research Agent"

    def find_keywords(self, site_id, seed_keyword, limit=10):
        """Trouve des mots-cles lies a un seed"""
        site = SITES.get(site_id, {})
        prompt = f"""Trouve {limit} mots-cles SEO lies a "{seed_keyword}" pour le marche quebecois.
Niche: {site.get('niche', '')}
Region: Quebec, Canada

Format JSON:
{{"keywords": [
    {{"keyword": "...", "volume_estimate": 100-5000, "difficulty": 1-100, "intent": "informational|transactional|navigational"}}
]}}"""

        response = call_qwen(prompt, system_prompt="Tu es un expert SEO. Reponds uniquement en JSON valide.")
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                log_agent(self.name, f"Trouve {len(data.get('keywords', []))} mots-cles pour {seed_keyword}")
                return data.get('keywords', [])
            except:
                pass
        return []

    def analyze_serp(self, keyword):
        """Analyse theorique des SERPs"""
        prompt = f"""Analyse le SERP pour "{keyword}" au Quebec:
- Type de resultats attendus (local pack, featured snippet, etc.)
- Niveau de concurrence estime
- Opportunites de ranking

Format JSON:
{{"serp_features": [...], "competition": "low|medium|high", "opportunities": [...], "recommended_content_type": "..."}}"""

        response = call_qwen(prompt, system_prompt="Tu es un expert SEO.")
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 2: CONTENT GENERATION AGENT
# ============================================
class ContentGenerationAgent:
    name = "Content Generation Agent"

    def generate_article(self, site_id, keyword, word_count=1500):
        """Genere un article SEO complet"""
        site = SITES.get(site_id, {})
        prompt = f"""Ecris un article SEO de {word_count} mots pour {site.get('nom', '')}.
MOT-CLE: {keyword}
NICHE: {site.get('niche', '')}
REGION: Quebec

Structure:
1. Titre H1 avec mot-cle
2. Meta description (155 car)
3. Introduction (150 mots)
4. 4-5 sections H2
5. Listes a puces
6. Conclusion + CTA
7. FAQ (3 questions)

Format JSON:
{{"titre": "...", "meta_description": "...", "contenu": "<article HTML>", "faq": [{{"q": "...", "r": "..."}}], "mots_cles_secondaires": [...]}}"""

        response = call_qwen(prompt, max_tokens=4000, system_prompt="Tu es un redacteur SEO expert en francais canadien.")
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                article = json.loads(response.strip())
                log_agent(self.name, f"Article genere: {article.get('titre', keyword)}")
                return article
            except:
                return {'titre': keyword, 'contenu': response, 'meta_description': '', 'faq': []}
        return None

    def generate_meta_tags(self, content, keyword):
        """Genere meta title et description optimises"""
        prompt = f"""Cree des meta tags SEO optimises pour ce contenu:
Mot-cle principal: {keyword}
Contenu: {content[:500]}...

Format JSON:
{{"meta_title": "... (60 car max)", "meta_description": "... (155 car max)", "og_title": "...", "og_description": "..."}}"""

        response = call_qwen(prompt, max_tokens=500)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 3: FAQ GENERATION AGENT
# ============================================
class FAQGenerationAgent:
    name = "FAQ Generation Agent"

    def generate_faq(self, site_id, topic, count=10):
        """Genere des FAQ pour un sujet"""
        site = SITES.get(site_id, {})
        prompt = f"""Cree {count} questions/reponses FAQ pour {site.get('nom', '')} sur le sujet: {topic}
Niche: {site.get('niche', '')}
Region: Quebec

Questions qui repondent aux intentions de recherche:
- Cout/Prix
- Comment faire
- Pourquoi choisir
- Quand/Ou
- Comparaisons

Format JSON:
{{"faq": [{{"question": "...", "answer": "...", "schema_ready": true}}]}}"""

        response = call_qwen(prompt, max_tokens=3000)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                log_agent(self.name, f"Genere {len(data.get('faq', []))} FAQ pour {topic}")
                return data.get('faq', [])
            except:
                pass
        return []

# ============================================
# AGENT 4: TECHNICAL SEO AUDIT AGENT
# ============================================
class TechnicalSEOAuditAgent:
    """Agent 4: Audit technique SEO complet"""
    name = "Technical SEO Audit Agent"

    def audit_page(self, url):
        """Audit technique complet d'une page"""
        try:
            response = requests.get(url, timeout=15, headers={'User-Agent': 'SeoAI-TechAudit/1.0'})
            html = response.text
            html_lower = html.lower()

            issues = []
            score = 100
            checks_passed = []

            # Check title
            if '<title>' not in html_lower or '</title>' not in html_lower:
                issues.append({'type': 'critical', 'message': 'Pas de balise title', 'fix': 'Ajouter <title>Titre Page</title> dans <head>'})
                score -= 15
            else:
                import re
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                if title_match:
                    title = title_match.group(1).strip()
                    if len(title) < 10:
                        issues.append({'type': 'warning', 'message': f'Title trop court ({len(title)} chars)', 'fix': 'Title recommande: 50-60 caracteres'})
                        score -= 5
                    elif len(title) > 65:
                        issues.append({'type': 'warning', 'message': f'Title trop long ({len(title)} chars)', 'fix': 'Title recommande: 50-60 caracteres'})
                        score -= 3
                    else:
                        checks_passed.append('title_length_ok')

            # Check meta description
            if 'meta name="description"' not in html_lower and "meta name='description'" not in html_lower:
                issues.append({'type': 'warning', 'message': 'Pas de meta description', 'fix': 'Ajouter <meta name="description" content="...">'})
                score -= 10
            else:
                desc_match = re.search(r"meta name=.description.*?content=.([^>]*?).", html, re.IGNORECASE)
                if desc_match:
                    desc = desc_match.group(1)
                    if len(desc) < 50:
                        issues.append({'type': 'warning', 'message': f'Meta description trop courte ({len(desc)} chars)', 'fix': 'Recommande: 120-160 caracteres'})
                        score -= 3
                    elif len(desc) > 165:
                        issues.append({'type': 'info', 'message': f'Meta description longue ({len(desc)} chars)', 'fix': 'Recommande: 120-160 caracteres'})
                        score -= 2
                    else:
                        checks_passed.append('meta_desc_ok')

            # Check H1
            h1_count = html_lower.count('<h1')
            if h1_count == 0:
                issues.append({'type': 'warning', 'message': 'Pas de balise H1', 'fix': 'Ajouter une balise H1 unique par page'})
                score -= 10
            elif h1_count > 1:
                issues.append({'type': 'warning', 'message': f'{h1_count} balises H1 (devrait etre 1)', 'fix': 'Garder une seule H1 par page'})
                score -= 5
            else:
                checks_passed.append('h1_ok')

            # Check heading hierarchy
            h2_count = html_lower.count('<h2')
            h3_count = html_lower.count('<h3')
            if h2_count == 0 and h3_count > 0:
                issues.append({'type': 'info', 'message': 'H3 sans H2 (hierarchie brisee)', 'fix': 'Respecter H1 > H2 > H3'})
                score -= 3

            # Check HTTPS
            if not url.startswith('https'):
                issues.append({'type': 'critical', 'message': 'Site non HTTPS', 'fix': 'Installer certificat SSL'})
                score -= 20

            # Check images alt
            img_tags = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
            img_no_alt = [img for img in img_tags if 'alt=' not in img.lower()]
            if img_no_alt:
                issues.append({'type': 'warning', 'message': f'{len(img_no_alt)}/{len(img_tags)} images sans alt', 'fix': 'Ajouter alt="" descriptif sur chaque image'})
                score -= min(10, len(img_no_alt) * 2)
            elif img_tags:
                checks_passed.append('images_alt_ok')

            # Check canonical
            if 'rel="canonical"' not in html_lower and "rel='canonical'" not in html_lower:
                issues.append({'type': 'warning', 'message': 'Pas de canonical URL', 'fix': 'Ajouter <link rel="canonical" href="URL">'})
                score -= 5

            # Check viewport
            if 'name="viewport"' not in html_lower:
                issues.append({'type': 'critical', 'message': 'Pas de meta viewport (mobile)', 'fix': 'Ajouter <meta name="viewport" content="width=device-width, initial-scale=1">'})
                score -= 10

            # Check charset
            if 'charset=' not in html_lower:
                issues.append({'type': 'warning', 'message': 'Pas de charset declare', 'fix': 'Ajouter <meta charset="UTF-8">'})
                score -= 3

            # Check lang attribute
            if 'lang=' not in html[:200].lower():
                issues.append({'type': 'info', 'message': 'Attribut lang manquant sur <html>', 'fix': 'Ajouter <html lang="fr">'})
                score -= 2

            # Check Open Graph
            if 'og:title' not in html_lower:
                issues.append({'type': 'info', 'message': 'Open Graph manquant', 'fix': 'Ajouter meta og:title, og:description, og:image'})
                score -= 2

            # Check schema markup
            if 'application/ld+json' not in html_lower:
                issues.append({'type': 'info', 'message': 'Schema markup (JSON-LD) absent', 'fix': 'Ajouter structured data JSON-LD'})
                score -= 3

            # Check response time
            resp_time = response.elapsed.total_seconds()
            if resp_time > 3:
                issues.append({'type': 'warning', 'message': f'Page lente: {round(resp_time, 2)}s', 'fix': 'Optimiser cache, images, scripts'})
                score -= 10
            elif resp_time > 1.5:
                issues.append({'type': 'info', 'message': f'Page moderement lente: {round(resp_time, 2)}s', 'fix': 'Optimiser pour < 1.5s'})
                score -= 3

            # Check page size
            size_kb = len(response.content) / 1024
            if size_kb > 2000:
                issues.append({'type': 'warning', 'message': f'Page lourde: {round(size_kb)}KB', 'fix': 'Compresser images, minifier CSS/JS'})
                score -= 5

            # Check inline styles (SEO anti-pattern)
            inline_styles = html_lower.count('style="')
            if inline_styles > 20:
                issues.append({'type': 'info', 'message': f'{inline_styles} styles inline detectes', 'fix': 'Deplacer styles dans fichier CSS externe'})
                score -= 2

            # Check broken internal links (basic)
            internal_links = re.findall(r"href=[\x22\x27](/[^\x22\x27]*)[\x22\x27]", html)
            if not internal_links:
                issues.append({'type': 'info', 'message': 'Aucun lien interne detecte', 'fix': 'Ajouter des liens internes pour le maillage'})
                score -= 2

            log_agent(self.name, f"Audit {url}: Score {max(0, score)}, {len(issues)} issues, {len(checks_passed)} OK")

            return {
                'url': url,
                'score': max(0, score),
                'issues': issues,
                'checks_passed': checks_passed,
                'response_time': round(resp_time, 3),
                'page_size_kb': round(size_kb, 1),
                'images_total': len(img_tags),
                'images_without_alt': len(img_no_alt),
                'internal_links': len(internal_links),
                'status_code': response.status_code,
                'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F'
            }
        except Exception as e:
            return {'url': url, 'score': 0, 'issues': [{'type': 'critical', 'message': str(e)}], 'grade': 'F'}

    def full_audit(self, site_id):
        """Audit technique complet d'un site avec toutes ses pages"""
        site = SITES.get(site_id)
        if not site:
            return {'error': f'Site {site_id} inconnu'}

        domain = site['domaine']
        base_url = f"https://{domain}"

        results = {
            'site_id': site_id,
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'pages': {},
            'robots': self.check_robots_txt(domain),
            'sitemap': self.check_sitemap(domain),
            'ssl': self.check_ssl_basic(domain),
            'headers': self.check_security_headers(base_url),
            'summary': {}
        }

        # Audit homepage
        results['pages']['homepage'] = self.audit_page(base_url)

        # Get pages from sitemap
        if results['sitemap'].get('exists') and results['sitemap'].get('urls'):
            for page_url in results['sitemap']['urls'][:10]:
                page_key = urlparse(page_url).path or '/'
                results['pages'][page_key] = self.audit_page(page_url)

        # Summary
        all_scores = [p.get('score', 0) for p in results['pages'].values()]
        all_issues = []
        for p in results['pages'].values():
            all_issues.extend(p.get('issues', []))

        results['summary'] = {
            'pages_audited': len(results['pages']),
            'avg_score': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            'total_issues': len(all_issues),
            'critical_issues': sum(1 for i in all_issues if i.get('type') == 'critical'),
            'warning_issues': sum(1 for i in all_issues if i.get('type') == 'warning'),
            'has_robots': results['robots'].get('exists', False),
            'has_sitemap': results['sitemap'].get('exists', False),
            'ssl_valid': results['ssl'].get('valid', False),
            'overall_grade': 'A' if results.get('pages', {}).get('homepage', {}).get('score', 0) >= 90 else 'B' if results.get('pages', {}).get('homepage', {}).get('score', 0) >= 75 else 'C'
        }

        # Save to DB
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO agent_logs (agent, message, level, created_at)
                VALUES (?, ?, 'INFO', datetime('now'))""",
                (self.name, f"Full audit {domain}: Score {results['summary']['avg_score']}, {results['summary']['total_issues']} issues"))
            conn.commit()
            conn.close()
        except:
            pass

        log_agent(self.name, f"Full audit {domain}: {results['summary']}")
        return results

    def check_robots_txt(self, domain):
        """Verifie robots.txt"""
        try:
            url = f"https://{domain}/robots.txt"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content = response.text
                has_sitemap = 'sitemap' in content.lower()
                has_disallow = 'disallow' in content.lower()
                return {'exists': True, 'content': content[:500], 'has_sitemap_ref': has_sitemap, 'has_disallow': has_disallow, 'size': len(content)}
            return {'exists': False, 'status_code': response.status_code}
        except Exception as e:
            return {'exists': False, 'error': str(e)}

    def check_sitemap(self, domain):
        """Verifie sitemap.xml et extrait les URLs"""
        try:
            url = f"https://{domain}/sitemap.xml"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                urls = re.findall(r'<loc>(.*?)</loc>', response.text)
                return {'exists': True, 'urls_count': len(urls), 'urls': urls[:20], 'size': len(response.text)}
            return {'exists': False, 'status_code': response.status_code}
        except Exception as e:
            return {'exists': False, 'error': str(e)}

    def check_ssl_basic(self, domain):
        """Verification SSL basique"""
        try:
            import ssl, socket
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    expires = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (expires - datetime.now()).days
                    return {'valid': True, 'days_left': days_left, 'issuer': dict(x[0] for x in cert.get('issuer', []))}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def check_security_headers(self, url):
        """Verifie les headers de securite"""
        try:
            resp = requests.get(url, timeout=10)
            headers = resp.headers
            checks = {
                'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                'X-Frame-Options': headers.get('X-Frame-Options'),
                'X-XSS-Protection': headers.get('X-XSS-Protection'),
                'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                'Content-Security-Policy': headers.get('Content-Security-Policy'),
                'Referrer-Policy': headers.get('Referrer-Policy'),
            }
            present = sum(1 for v in checks.values() if v)
            return {'headers': checks, 'present': present, 'total': len(checks), 'score': round(present / len(checks) * 100)}
        except Exception as e:
            return {'error': str(e)}

# ============================================
# AGENT 5: PERFORMANCE AGENT
# ============================================
class PerformanceAgent:
    """Agent 5: Performance et vitesse des sites"""
    name = "Performance Agent"

    def check_speed(self, url):
        """Check vitesse complet avec analyse des ressources"""
        try:
            # Mesurer TTFB et load total
            start = datetime.now()
            response = requests.get(url, timeout=30, headers={'User-Agent': 'SeoAI-Perf/1.0'})
            load_time = (datetime.now() - start).total_seconds()
            ttfb = response.elapsed.total_seconds()

            html = response.text
            size_kb = len(response.content) / 1024

            # Analyser les ressources
            import re
            css_files = re.findall(r"<link[^>]*href=[^>]*?([^\s>]*\.css[^\s>]*)", html, re.IGNORECASE)
            js_files = re.findall(r"<script[^>]*src=[^>]*?([^\s>]*\.js[^\s>]*)", html, re.IGNORECASE)
            img_files = re.findall(r"<img[^>]*src=.([^\s>]+).", html, re.IGNORECASE)
            fonts = re.findall(r"url\(.?([^)]*\.(woff2?|ttf|otf|eot)).?\)", html, re.IGNORECASE)

            # Detecter les problemes de performance
            issues = []
            score = 100

            # TTFB
            if ttfb > 1.0:
                issues.append({'type': 'critical', 'message': f'TTFB lent: {round(ttfb, 2)}s (max 1s)', 'impact': 'high'})
                score -= 20
            elif ttfb > 0.5:
                issues.append({'type': 'warning', 'message': f'TTFB moyen: {round(ttfb, 2)}s (ideal < 0.5s)', 'impact': 'medium'})
                score -= 10

            # Load time
            if load_time > 5:
                issues.append({'type': 'critical', 'message': f'Temps total: {round(load_time, 2)}s (max 3s)', 'impact': 'high'})
                score -= 25
            elif load_time > 3:
                issues.append({'type': 'warning', 'message': f'Temps total: {round(load_time, 2)}s (ideal < 3s)', 'impact': 'medium'})
                score -= 15

            # Page size
            if size_kb > 2000:
                issues.append({'type': 'critical', 'message': f'Page trop lourde: {round(size_kb)}KB', 'impact': 'high'})
                score -= 15
            elif size_kb > 1000:
                issues.append({'type': 'warning', 'message': f'Page lourde: {round(size_kb)}KB', 'impact': 'medium'})
                score -= 8

            # Too many CSS
            if len(css_files) > 5:
                issues.append({'type': 'warning', 'message': f'{len(css_files)} fichiers CSS (combiner)', 'impact': 'medium'})
                score -= 5

            # Too many JS
            if len(js_files) > 8:
                issues.append({'type': 'warning', 'message': f'{len(js_files)} fichiers JS (combiner/defer)', 'impact': 'medium'})
                score -= 5

            # Render-blocking scripts
            blocking_scripts = re.findall(r"<script\s+(?![^>]*(defer|async|type=.module))[^>]*src=", html, re.IGNORECASE)
            if blocking_scripts:
                issues.append({'type': 'warning', 'message': f'{len(blocking_scripts)} scripts bloquants sans defer/async', 'impact': 'high'})
                score -= 8

            # Images without lazy loading
            imgs_no_lazy = [img for img in re.findall(r"<img[^>]*>", html, re.IGNORECASE) if 'loading=' not in img.lower()]
            if len(imgs_no_lazy) > 3:
                issues.append({'type': 'info', 'message': f'{len(imgs_no_lazy)} images sans lazy loading', 'impact': 'medium'})
                score -= 5

            # Compression check
            content_encoding = response.headers.get('Content-Encoding', '')
            if 'gzip' not in content_encoding and 'br' not in content_encoding:
                issues.append({'type': 'warning', 'message': 'Compression GZIP/Brotli absente', 'impact': 'high'})
                score -= 10

            # Cache headers
            cache_control = response.headers.get('Cache-Control', '')
            if not cache_control or 'no-cache' in cache_control:
                issues.append({'type': 'info', 'message': 'Cache-Control non configure', 'impact': 'medium'})
                score -= 5

            log_agent(self.name, f"Perf {url}: {round(load_time, 2)}s, {round(size_kb)}KB, score {max(0, score)}")

            return {
                'url': url,
                'ttfb_seconds': round(ttfb, 3),
                'load_time_seconds': round(load_time, 2),
                'size_kb': round(size_kb, 2),
                'score': max(0, score),
                'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F',
                'status_code': response.status_code,
                'resources': {
                    'css_files': len(css_files),
                    'js_files': len(js_files),
                    'images': len(img_files),
                    'fonts': len(fonts),
                    'blocking_scripts': len(blocking_scripts)
                },
                'compression': content_encoding or 'none',
                'cache_control': cache_control or 'none',
                'issues': issues
            }
        except Exception as e:
            return {'url': url, 'error': str(e), 'score': 0, 'grade': 'F'}

    def check_all_sites(self):
        """Check performance de tous les sites"""
        results = {}
        for site_id, site in SITES.items():
            url = f"https://{site['domaine']}"
            results[site_id] = self.check_speed(url)
        return results

    def compare_sites(self):
        """Compare la performance entre tous les sites"""
        all_results = self.check_all_sites()
        ranking = sorted(all_results.items(), key=lambda x: x[1].get('score', 0), reverse=True)
        return {
            'ranking': [{'site_id': sid, 'domain': SITES[sid]['domaine'], 'score': r.get('score', 0), 'load_time': r.get('load_time_seconds', 0)} for sid, r in ranking],
            'fastest': ranking[0][0] if ranking else None,
            'slowest': ranking[-1][0] if ranking else None,
            'details': all_results
        }

# ============================================
# AGENT 6: BACKLINK ANALYSIS AGENT
# ============================================
class BacklinkAnalysisAgent:
    name = "Backlink Analysis Agent"

    def analyze_opportunities(self, site_id):
        """Analyse opportunites de backlinks"""
        site = SITES.get(site_id, {})
        prompt = f"""Suggere 10 strategies de backlinking pour {site.get('nom', '')} dans la niche {site.get('niche', '')} au Quebec:
- Annuaires locaux
- Partenariats
- Guest posting
- Citations locales
- PR digitales

Format JSON:
{{"strategies": [{{"type": "...", "source": "...", "difficulty": "easy|medium|hard", "value": "high|medium|low", "action": "..."}}]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 7: LOCAL SEO AGENT
# ============================================
class LocalSEOAgent:
    name = "Local SEO Agent"

    def audit_local_seo(self, site_id):
        """Audit local SEO complet - verifie schema, FAQ, Google Business linkage"""
        site = SITES.get(site_id, {})
        if not site:
            return {'error': f'Site {site_id} inconnu'}

        domain = site.get('domaine', '')
        url = f'https://{domain}'
        issues = []
        score = 100
        details = {}

        try:
            resp = requests.get(url, timeout=15, headers={'User-Agent': 'SeoAI-LocalSEO/1.0'})
            html = resp.text
        except Exception as e:
            return {'error': str(e), 'score': 0}

        # 1. Check LocalBusiness JSON-LD
        ld_json_blocks = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        has_local_business = False
        has_faq_schema = False
        faq_schema_count = 0
        local_business_data = {}

        for block in ld_json_blocks:
            try:
                data = json.loads(block.strip())
                biz_types = ['LocalBusiness', 'LandscapingBusiness', 'HomeAndConstructionBusiness',
                             'ProfessionalService', 'Plumber', 'Painter', 'HousePainter',
                             'MovingCompany', 'RoofingContractor', 'GeneralContractor']
                if data.get('@type') in biz_types:
                    has_local_business = True
                    local_business_data = data
                if data.get('@type') == 'FAQPage':
                    has_faq_schema = True
                    faq_schema_count = len(data.get('mainEntity', []))
            except:
                pass

        if not has_local_business:
            issues.append({'type': 'critical', 'message': 'Schema LocalBusiness JSON-LD absent',
                          'fix': 'Ajouter structured data LocalBusiness dans <head>'})
            score -= 20
        else:
            if not local_business_data.get('telephone'):
                issues.append({'type': 'warning', 'message': 'Telephone manquant dans schema LocalBusiness',
                              'fix': 'Ajouter telephone dans JSON-LD'})
                score -= 5
            if not local_business_data.get('address'):
                issues.append({'type': 'warning', 'message': 'Adresse manquante dans schema LocalBusiness',
                              'fix': 'Ajouter address dans JSON-LD'})
                score -= 5
            if not local_business_data.get('areaServed'):
                issues.append({'type': 'warning', 'message': 'Zones de service (areaServed) manquantes',
                              'fix': 'Ajouter areaServed avec les villes desservies'})
                score -= 5
            if not local_business_data.get('openingHoursSpecification'):
                issues.append({'type': 'info', 'message': 'Heures ouverture manquantes dans schema',
                              'fix': 'Ajouter openingHoursSpecification'})
                score -= 3
            details['local_business'] = {
                'name': local_business_data.get('name', ''),
                'type': local_business_data.get('@type', ''),
                'has_phone': bool(local_business_data.get('telephone')),
                'has_address': bool(local_business_data.get('address')),
                'has_area_served': bool(local_business_data.get('areaServed')),
                'area_count': len(local_business_data.get('areaServed', [])),
                'has_hours': bool(local_business_data.get('openingHoursSpecification'))
            }

        # 2. Check FAQPage schema
        if not has_faq_schema:
            issues.append({'type': 'critical', 'message': 'Schema FAQPage JSON-LD absent',
                          'fix': 'Ajouter structured data FAQPage pour rich snippets Google'})
            score -= 15
        else:
            if faq_schema_count < 5:
                issues.append({'type': 'warning', 'message': f'Seulement {faq_schema_count} FAQ dans schema (min 5)',
                              'fix': 'Ajouter plus de FAQ dans JSON-LD'})
                score -= 5
            details['faq_schema'] = {'count': faq_schema_count}

        # 3. Check visible FAQ section
        faq_visible_count = html.lower().count('faq-item')
        if faq_visible_count == 0:
            issues.append({'type': 'warning', 'message': 'Section FAQ visible absente',
                          'fix': 'Ajouter une section FAQ visible avec accordion'})
            score -= 10
        else:
            if has_faq_schema and abs(faq_visible_count - faq_schema_count) > 3:
                issues.append({'type': 'info',
                              'message': f'FAQ visible ({faq_visible_count}) != FAQ schema ({faq_schema_count})',
                              'fix': 'Synchroniser FAQ visibles et schema JSON-LD'})
                score -= 3
            details['faq_visible'] = {'count': faq_visible_count}

        # 4. Check cross-linking to sister companies
        sister_sites = {k: v for k, v in SITES.items() if k != site_id and k != 4}
        cross_links = []
        for sid, sdata in sister_sites.items():
            if sdata.get('domaine', '') in html:
                cross_links.append(sdata['domaine'])
        if not cross_links and len(sister_sites) > 0:
            sister_list = ', '.join(s['domaine'] for s in sister_sites.values())
            issues.append({'type': 'info', 'message': 'Pas de cross-link vers sites partenaires',
                          'fix': f'Ajouter liens vers: {sister_list}'})
            score -= 3
        details['cross_links'] = cross_links

        # 5. Check Google Maps embed or link
        html_lower = html.lower()
        has_gmaps = 'maps.google' in html_lower or 'google.com/maps' in html_lower or 'maps.googleapis' in html_lower
        if not has_gmaps:
            issues.append({'type': 'warning', 'message': 'Pas de Google Maps integre ou lie',
                          'fix': 'Ajouter Google Maps embed ou lien vers fiche Google Business'})
            score -= 5
        details['has_google_maps'] = has_gmaps

        # 6. Check NAP (Name, Address, Phone visible)
        phone_patterns = [r'438[\s.-]?383[\s.-]?7283', r'514[\s.-]?\d{3}[\s.-]?\d{4}']
        has_phone_visible = any(re.search(p, html) for p in phone_patterns)
        if not has_phone_visible:
            issues.append({'type': 'warning', 'message': 'Telephone non visible sur la page',
                          'fix': 'Afficher le numero clairement'})
            score -= 5
        details['has_phone_visible'] = has_phone_visible

        # 7. Check robots.txt allows AI bots
        try:
            robots_resp = requests.get(f'https://{domain}/robots.txt', timeout=5)
            if robots_resp.status_code == 200:
                robots = robots_resp.text.lower()
                ai_bots = ['gptbot', 'claudebot', 'perplexitybot']
                blocked_bots = [b for b in ai_bots if f'user-agent: {b}' in robots and 'disallow: /' in robots]
                if blocked_bots:
                    issues.append({'type': 'info', 'message': f'Bots AI bloques: {blocked_bots}',
                                  'fix': 'Autoriser les bots AI pour GEO (generative engine optimization)'})
                    score -= 3
                details['robots_allows_ai'] = len(blocked_bots) == 0
        except:
            pass

        log_agent(self.name, f"Local SEO audit {domain}: Score {max(0, score)}, {len(issues)} issues")

        # Save to DB
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO agent_logs (agent, message, level, created_at)
                VALUES (?, ?, 'INFO', datetime('now'))""",
                (self.name, json.dumps({'domain': domain, 'score': max(0, score),
                 'issues_count': len(issues), 'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D'})))
            conn.commit()
            conn.close()
        except:
            pass

        return {
            'site_id': site_id,
            'domain': domain,
            'score': max(0, score),
            'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F',
            'issues': issues,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

    def audit_all_sites(self):
        """Audit local SEO de tous les sites clients"""
        results = {}
        for site_id in SITES:
            if site_id == 4:
                continue
            results[site_id] = self.audit_local_seo(site_id)
            log_agent(self.name, f"Audit site {site_id}: {results[site_id].get('grade', '?')}")
        return results

    def optimize_gmb(self, site_id):
        """Recommandations Google My Business"""
        site = SITES.get(site_id, {})
        prompt = f"""Donne des recommandations GMB pour {site.get('nom', '')}:
Niche: {site.get('niche', '')}
Region: Quebec

Inclure:
- Categories recommandees
- Attributs a ajouter
- Types de posts
- Strategie de reviews
- Photos recommandees

Format JSON:
{{"categories": [...], "attributes": [...], "post_ideas": [...], "review_strategy": "...", "photo_types": [...]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}


# ============================================
# AGENT 8: COMPETITOR ANALYSIS AGENT
# ============================================
class CompetitorAnalysisAgent:
    name = "Competitor Analysis Agent"

    def identify_competitors(self, site_id):
        """Identifie les concurrents"""
        site = SITES.get(site_id, {})
        prompt = f"""Identifie 10 concurrents potentiels pour {site.get('nom', '')} au Quebec.
Niche: {site.get('niche', '')}

Format JSON:
{{"competitors": [{{"name": "...", "domain": "...", "strengths": [...], "weaknesses": [...], "threat_level": "high|medium|low"}}]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 9: CONTENT OPTIMIZATION AGENT
# ============================================
class ContentOptimizationAgent:
    name = "Content Optimization Agent"

    def optimize_existing(self, content, target_keyword):
        """Optimise un contenu existant"""
        prompt = f"""Optimise ce contenu pour le mot-cle "{target_keyword}":

{content[:2000]}

Suggestions:
1. Placement du mot-cle
2. Structure amelioree
3. Liens internes suggeres
4. Call-to-actions
5. Rich snippets

Format JSON:
{{"suggestions": [...], "optimized_title": "...", "optimized_h2s": [...], "internal_links": [...], "ctas": [...]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 10: SCHEMA MARKUP AGENT
# ============================================
class SchemaMarkupAgent:
    name = "Schema Markup Agent"

    def generate_local_business_schema(self, site_id):
        """Genere schema LocalBusiness"""
        site = SITES.get(site_id, {})
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": site.get('nom', ''),
            "url": f"https://{site.get('domaine', '')}",
            "telephone": "",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Montreal",
                "addressRegion": "QC",
                "addressCountry": "CA"
            },
            "geo": {
                "@type": "GeoCoordinates"
            },
            "openingHoursSpecification": []
        }
        return schema

    def generate_faq_schema(self, faqs):
        """Genere schema FAQ"""
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        for faq in faqs:
            schema["mainEntity"].append({
                "@type": "Question",
                "name": faq.get('question', faq.get('q', '')),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.get('answer', faq.get('r', ''))
                }
            })
        return schema

    def generate_aggregate_rating_schema(self, site_id, rating=4.8, count=47, best=5):
        site = SITES.get(site_id, {})
        return {"@context": "https://schema.org", "@type": "LocalBusiness",
                "name": site.get('nom', ''), "url": "https://" + site.get('domaine', ''),
                "aggregateRating": {"@type": "AggregateRating", "ratingValue": str(rating),
                "reviewCount": str(count), "bestRating": str(best), "worstRating": "1"}}

    def generate_complete_schema(self, site_id):
        return {'local_business': self.generate_local_business_schema(site_id),
                'aggregate_rating': self.generate_aggregate_rating_schema(site_id)}


    def generate_article_schema(self, title, author, date, content):
        """Genere schema Article"""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "author": {"@type": "Person", "name": author},
            "datePublished": date,
            "articleBody": content[:500]
        }

# ============================================
# AGENT 11: SOCIAL MEDIA AGENT
# ============================================
class SocialMediaAgent:
    name = "Social Media Agent"

    def generate_social_posts(self, article_title, article_url, platform='all'):
        """Genere posts pour reseaux sociaux"""
        prompt = f"""Cree des posts pour promouvoir cet article:
Titre: {article_title}
URL: {article_url}

Genere pour: Facebook, Instagram, LinkedIn, TikTok

Format JSON:
{{"facebook": {{"text": "...", "hashtags": [...]}}, "instagram": {{"caption": "...", "hashtags": [...]}}, "linkedin": {{"text": "..."}}, "tiktok": {{"script": "...", "hashtags": [...]}}}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 12: EMAIL MARKETING AGENT
# ============================================
class EmailMarketingAgent:
    name = "Email Marketing Agent"

    def generate_newsletter(self, site_id, articles):
        """Genere une newsletter"""
        site = SITES.get(site_id, {})
        prompt = f"""Cree une newsletter pour {site.get('nom', '')}:
Articles a promouvoir:
{json.dumps(articles, ensure_ascii=False)}

Format JSON:
{{"subject_line": "...", "preview_text": "...", "html_content": "...", "cta_text": "..."}}"""

        response = call_qwen(prompt, max_tokens=2000)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 13: IMAGE OPTIMIZATION AGENT
# ============================================
class ImageOptimizationAgent:
    name = "Image Optimization Agent"

    def generate_alt_texts(self, image_context, keyword):
        """Genere textes alt optimises"""
        prompt = f"""Cree 5 textes alt SEO pour une image:
Contexte: {image_context}
Mot-cle cible: {keyword}

Format JSON:
{{"alt_texts": ["...", "...", "..."]}}"""

        response = call_qwen(prompt, max_tokens=500)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 14: INTERNAL LINKING AGENT
# ============================================
class InternalLinkingAgent:
    name = "Internal Linking Agent"

    def suggest_links(self, site_id, current_page_topic):
        """Suggere liens internes"""
        prompt = f"""Suggere 5-10 liens internes pour une page sur "{current_page_topic}":
Site: {SITES.get(site_id, {}).get('nom', '')}
Niche: {SITES.get(site_id, {}).get('niche', '')}

Format JSON:
{{"links": [{{"anchor_text": "...", "target_topic": "...", "placement": "intro|body|conclusion"}}]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 15: URL OPTIMIZATION AGENT
# ============================================
class URLOptimizationAgent:
    name = "URL Optimization Agent"

    def generate_slug(self, title, keyword):
        """Genere un slug SEO-friendly"""
        prompt = f"""Cree un slug URL optimise:
Titre: {title}
Mot-cle: {keyword}

Regles:
- Max 60 caracteres
- Mots-cles importants en premier
- Pas de mots vides (le, la, de, etc.)

Format JSON:
{{"slug": "...", "full_url": "/blog/..."}}"""

        response = call_qwen(prompt, max_tokens=200)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 16: TITLE TAG AGENT
# ============================================
class TitleTagAgent:
    name = "Title Tag Agent"

    def optimize_title(self, current_title, keyword, brand):
        """Optimise un title tag"""
        prompt = f"""Optimise ce title tag:
Actuel: {current_title}
Mot-cle: {keyword}
Marque: {brand}

Regles:
- 50-60 caracteres
- Mot-cle au debut
- Marque a la fin
- Accrocheur

Format JSON:
{{"optimized_title": "...", "character_count": X, "variations": ["...", "..."]}}"""

        response = call_qwen(prompt, max_tokens=300)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}


# ============================================
# AGENT 16B: OPEN GRAPH & TWITTER CARDS AGENT
# ============================================

class OpenGraphAgent:
    name = "Open Graph Agent"

    def generate_og_tags(self, site_id):
        site = SITES.get(site_id, {})
        domain = site.get('domaine', '')
        nom = site.get('nom', domain)
        try:
            import requests as req
            resp = req.get('https://' + domain, timeout=10, headers={'User-Agent': 'SeoparAI-Agent/1.0'})
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('title')
            title_text = title.text.strip() if title else nom
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            desc_text = meta_desc.get('content', '') if meta_desc else nom
            existing_og = {}
            for tag in soup.find_all('meta', property=True):
                if tag.get('property','').startswith('og:'):
                    existing_og[tag.get('property')] = tag.get('content')
            existing_tw = {}
            for tag in soup.find_all('meta', attrs={'name': True}):
                if tag.get('name','').startswith('twitter:'):
                    existing_tw[tag.get('name')] = tag.get('content')
            # Also check property attribute (some sites use property instead of name for twitter)
            for tag in soup.find_all('meta', property=True):
                if tag.get('property','').startswith('twitter:'):
                    existing_tw[tag.get('property')] = tag.get('content')
        except:
            title_text = nom
            desc_text = nom
            existing_og = {}
            existing_tw = {}
        og = {
            'og:title': existing_og.get('og:title', title_text),
            'og:description': existing_og.get('og:description', desc_text[:200]),
            'og:url': existing_og.get('og:url', 'https://' + domain),
            'og:type': 'website', 'og:site_name': nom, 'og:locale': 'fr_CA',
            'og:image': existing_og.get('og:image', 'https://' + domain + '/images/og-image.jpg'),
            'og:image:width': '1200', 'og:image:height': '630',
        }
        tw = {
            'twitter:card': 'summary_large_image',
            'twitter:title': existing_tw.get('twitter:title', title_text[:70]),
            'twitter:description': existing_tw.get('twitter:description', desc_text[:200]),
            'twitter:image': existing_tw.get('twitter:image', 'https://' + domain + '/images/og-image.jpg'),
        }
        tags = []
        for p, c in og.items():
            tags.append('<meta property="' + p + '" content="' + str(c) + '">')
        for n, c in tw.items():
            tags.append('<meta name="' + n + '" content="' + str(c) + '">')
        missing_og = [k for k in ['og:title','og:description','og:image','og:url'] if k not in existing_og]
        missing_tw = [k for k in ['twitter:card','twitter:title','twitter:description','twitter:image'] if k not in existing_tw]
        log_agent(self.name, 'Site ' + str(site_id) + ': missing OG=' + str(len(missing_og)) + ' TW=' + str(len(missing_tw)))
        return {'site_id': site_id, 'domain': domain, 'og_tags': og, 'twitter_tags': tw,
                'html_tags': chr(10).join(tags), 'missing_og': missing_og, 'missing_tw': missing_tw,
                'status': 'needs_update' if missing_og or missing_tw else 'complete'}

    def audit_all_sites(self):
        results = {}
        for sid in SITES:
            try: results[sid] = self.generate_og_tags(sid)
            except Exception as e: results[sid] = {'error': str(e)}
        return results

# ============================================
# AGENT 17: CONTENT CALENDAR AGENT
# ============================================
class ContentCalendarAgent:
    name = "Content Calendar Agent"

    def generate_calendar(self, site_id, weeks=4):
        """Genere un calendrier editorial"""
        site = SITES.get(site_id, {})
        prompt = f"""Cree un calendrier editorial de {weeks} semaines pour {site.get('nom', '')}:
Niche: {site.get('niche', '')}

Inclure:
- 2 articles/semaine
- 1 FAQ/semaine
- Sujets saisonniers
- Mots-cles cibles

Format JSON:
{{"weeks": [{{"week": 1, "content": [{{"type": "article|faq", "topic": "...", "keyword": "...", "publish_day": "lundi|mardi|..."}}]}}]}}"""

        response = call_qwen(prompt, max_tokens=2000)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 18: PRICING STRATEGY AGENT
# ============================================
class PricingStrategyAgent:
    name = "Pricing Strategy Agent"

    def analyze_competitor_pricing(self, site_id, service):
        """Analyse prix concurrents et suggere"""
        site = SITES.get(site_id, {})
        prompt = f"""Analyse les prix du marche pour {service} dans la niche {site.get('niche', '')} au Quebec:

Suggere:
- Fourchette de prix du marche
- Prix recommande (10% sous la moyenne)
- Strategies de pricing

Format JSON:
{{"market_range": {{"low": X, "high": Y}}, "recommended_price": Z, "strategies": [...], "value_propositions": [...]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 19: REVIEW MANAGEMENT AGENT
# ============================================
class ReviewManagementAgent:
    name = "Review Management Agent"

    def generate_review_response(self, review_text, rating, is_positive=True):
        """Genere reponse aux avis"""
        prompt = f"""Genere une reponse professionnelle a cet avis:
Avis: {review_text}
Note: {rating}/5
Type: {'positif' if is_positive else 'negatif'}

Format JSON:
{{"response": "...", "tone": "grateful|apologetic|professional", "follow_up_action": "..."}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENT 20: CONVERSION OPTIMIZATION AGENT
# ============================================
class ConversionOptimizationAgent:
    name = "Conversion Optimization Agent"

    def analyze_cta(self, current_cta, page_type):
        """Optimise les CTAs"""
        prompt = f"""Optimise ce CTA:
Actuel: {current_cta}
Type de page: {page_type}

Suggere 5 variations avec psychologie de persuasion.

Format JSON:
{{"variations": [{{"cta": "...", "psychology": "urgency|social_proof|benefit|..."}}, "recommended": "..."}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# AGENTS 21-30: SPECIALIZED AGENTS
# ============================================

class MonitoringAgent:
    """Agent 21: Surveillance uptime et alertes"""
    name = "Monitoring Agent"

    def check_uptime(self, sites):
        results = {}
        for site_id, site in sites.items():
            try:
                url = f"https://{site['domaine']}"
                response = requests.get(url, timeout=10)
                results[site_id] = {
                    'status': 'up' if response.status_code == 200 else 'down',
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            except:
                results[site_id] = {'status': 'down', 'error': True}
        return results

    def mark_corrected_by_agent(self, alert_id, agent_name):
        """Un agent marque une alerte comme corrigee. L alerte reste visible."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN corrected_by TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN corrected_at DATETIME')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN revalidated_at DATETIME')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN revalidation_status TEXT')
        except:
            pass
        conn.commit()
        cursor.execute("""
            UPDATE mon_alerts SET revalidation_status = 'corrected',
            corrected_by = ?, corrected_at = datetime('now')
            WHERE id = ? AND resolved = 0
        """, (agent_name, alert_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return {'alert_id': alert_id, 'corrected_by': agent_name, 'updated': affected > 0}

    def find_alerts_for_site(self, site_id, alert_type=None):
        """Trouve les alertes actives pour un site."""
        conn = get_db()
        cursor = conn.cursor()
        if alert_type:
            cursor.execute('SELECT id, alert_type, message FROM mon_alerts WHERE site_id = ? AND alert_type = ? AND resolved = 0', (site_id, alert_type))
        else:
            cursor.execute('SELECT id, alert_type, message FROM mon_alerts WHERE site_id = ? AND resolved = 0', (site_id,))
        rows = [{'id': r[0], 'type': r[1], 'message': r[2]} for r in cursor.fetchall()]
        conn.close()
        return rows

    def revalidate_old_alerts(self):
        """Revalide les alertes de +24h. Corrige -> corrected_pending_human. Persiste -> double_alert."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN revalidated_at DATETIME')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN revalidation_status TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN corrected_by TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE mon_alerts ADD COLUMN corrected_at DATETIME')
        except:
            pass
        conn.commit()
        cursor.execute("""
            SELECT id, site_id, alert_type, message, severity FROM mon_alerts
            WHERE resolved = 0 AND created_at < datetime('now', '-24 hours')
            AND (revalidated_at IS NULL OR revalidated_at < datetime('now', '-24 hours'))
        """)
        old_alerts = cursor.fetchall()
        results = []
        for alert_id, site_id, alert_type, message, severity in old_alerts:
            still_broken = False
            if alert_type == 'ssl':
                try:
                    import ssl, socket
                    domain = SITES.get(int(site_id) if str(site_id).isdigit() else site_id, {}).get('domaine', '')
                    if domain:
                        ctx = ssl.create_default_context()
                        with socket.create_connection((domain, 443), timeout=10) as s:
                            with ctx.wrap_socket(s, server_hostname=domain) as ss:
                                pass
                except:
                    still_broken = True
            elif alert_type in ('downtime', 'response_time'):
                try:
                    domain = SITES.get(int(site_id) if str(site_id).isdigit() else site_id, {}).get('domaine', '')
                    if domain:
                        resp = requests.get(f'https://{domain}', timeout=10)
                        if resp.status_code >= 400:
                            still_broken = True
                except:
                    still_broken = True
            elif 'nginx' in message.lower():
                try:
                    import subprocess
                    r = subprocess.run(['systemctl', 'is-active', 'nginx'], capture_output=True, text=True)
                    if r.stdout.strip() != 'active':
                        still_broken = True
                except:
                    still_broken = True
            if still_broken:
                new_sev = 'double_alert' if severity != 'double_alert' else 'double_alert'
                cursor.execute("""UPDATE mon_alerts SET severity = ?, revalidated_at = datetime('now'),
                    revalidation_status = 'still_broken' WHERE id = ?""", (new_sev, alert_id))
                results.append({'id': alert_id, 'status': 'still_broken', 'severity': new_sev})
            else:
                cursor.execute("""UPDATE mon_alerts SET revalidated_at = datetime('now'),
                    revalidation_status = 'corrected_pending_human' WHERE id = ?""", (alert_id,))
                results.append({'id': alert_id, 'status': 'corrected_pending_human'})
        conn.commit()
        conn.close()
        return {'revalidated': len(results), 'details': results}

class SSLAgent:
    """Agent 22: Verification SSL complete"""
    name = "SSL Agent"

    def check_ssl(self, domain):
        """Verification SSL complete avec details certificat"""
        import ssl
        import socket
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    protocol = ssock.version()
                    cipher = ssock.cipher()

                    expires = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    issued = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (expires - datetime.now()).days

                    # Issuer info
                    issuer_dict = {}
                    for item in cert.get('issuer', []):
                        for key, val in item:
                            issuer_dict[key] = val

                    # Subject info
                    subject_dict = {}
                    for item in cert.get('subject', []):
                        for key, val in item:
                            subject_dict[key] = val

                    # SAN (Subject Alternative Names)
                    san = [entry[1] for entry in cert.get('subjectAltName', [])]

                    # Determine urgency
                    if days_left <= 0:
                        urgency = 'expired'
                    elif days_left <= 7:
                        urgency = 'critical'
                    elif days_left <= 30:
                        urgency = 'warning'
                    else:
                        urgency = 'ok'

                    log_agent(self.name, f"SSL {domain}: {days_left} jours restants, {urgency}")

                    return {
                        'valid': True,
                        'domain': domain,
                        'expires': cert['notAfter'],
                        'issued': cert['notBefore'],
                        'days_left': days_left,
                        'urgency': urgency,
                        'issuer': issuer_dict.get('organizationName', issuer_dict.get('commonName', 'Unknown')),
                        'subject': subject_dict.get('commonName', domain),
                        'san': san,
                        'protocol': protocol,
                        'cipher': cipher[0] if cipher else 'Unknown',
                        'serial_number': cert.get('serialNumber', ''),
                    }
        except ssl.SSLCertVerificationError as e:
            log_agent(self.name, f"SSL ERREUR {domain}: {e}", 'ERROR')
            return {'valid': False, 'domain': domain, 'error': str(e), 'urgency': 'critical', 'error_type': 'verification'}
        except socket.timeout:
            return {'valid': False, 'domain': domain, 'error': 'Connection timeout', 'urgency': 'critical', 'error_type': 'timeout'}
        except ConnectionRefusedError:
            return {'valid': False, 'domain': domain, 'error': 'Connection refused (port 443)', 'urgency': 'critical', 'error_type': 'refused'}
        except Exception as e:
            return {'valid': False, 'domain': domain, 'error': str(e), 'urgency': 'critical', 'error_type': 'unknown'}

    def check_all_sites(self):
        """Verifie SSL de tous les sites"""
        results = {}
        alerts = []
        for site_id, site in SITES.items():
            result = self.check_ssl(site['domaine'])
            results[site_id] = result
            if result.get('urgency') in ('critical', 'expired'):
                alerts.append({'site_id': site_id, 'domain': site['domaine'], 'days_left': result.get('days_left', -1), 'error': result.get('error')})
        return {'results': results, 'alerts': alerts, 'all_valid': all(r.get('valid') for r in results.values())}

    def check_https_redirect(self, domain):
        """Verifie si HTTP redirige vers HTTPS"""
        try:
            resp = requests.get(f"http://{domain}", timeout=10, allow_redirects=False)
            redirects_to_https = resp.status_code in (301, 302, 308) and 'https' in resp.headers.get('Location', '')
            return {'domain': domain, 'redirects': redirects_to_https, 'status_code': resp.status_code, 'location': resp.headers.get('Location', '')}
        except Exception as e:
            return {'domain': domain, 'redirects': False, 'error': str(e)}

    def check_mixed_content(self, url):
        """Detecte le contenu mixte HTTP sur une page HTTPS"""
        try:
            resp = requests.get(url, timeout=15)
            html = resp.text
            http_resources = re.findall(r"(src|href)=.http://[^\s>]+.", html, re.IGNORECASE)
            return {'url': url, 'mixed_content_count': len(http_resources), 'has_mixed_content': len(http_resources) > 0}
        except Exception as e:
            return {'url': url, 'error': str(e)}

class BackupAgent:
    """Agent 23: Sauvegarde automatique complete"""
    name = "Backup Agent"

    BACKUP_DIR = "/opt/seo-agent/db/backup"
    SITES_BACKUP_DIR = "/opt/seo-agent/backups/sites"
    MAX_BACKUPS = 30  # Garder les 30 derniers

    def backup_database(self):
        """Backup de la base de donnees SQLite"""
        import shutil
        os.makedirs(self.BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.BACKUP_DIR}/seo_agent_{timestamp}.db"
        try:
            # Utiliser la methode SQLite backup pour consistance
            source = sqlite3.connect(DB_PATH)
            dest = sqlite3.connect(backup_path)
            source.backup(dest)
            source.close()
            dest.close()

            size_mb = round(os.path.getsize(backup_path) / (1024 * 1024), 2)
            log_agent(self.name, f"DB backup: {backup_path} ({size_mb}MB)")
            return {'success': True, 'path': backup_path, 'size_mb': size_mb, 'timestamp': timestamp}
        except Exception as e:
            # Fallback: copie fichier
            try:
                shutil.copy2(DB_PATH, backup_path)
                size_mb = round(os.path.getsize(backup_path) / (1024 * 1024), 2)
                log_agent(self.name, f"DB backup (copy): {backup_path} ({size_mb}MB)")
                return {'success': True, 'path': backup_path, 'size_mb': size_mb, 'method': 'copy'}
            except Exception as e2:
                return {'success': False, 'error': str(e2)}

    def backup_site_files(self, site_id):
        """Backup des fichiers d'un site"""
        import shutil
        site = SITES.get(site_id)
        if not site:
            return {'success': False, 'error': f'Site {site_id} inconnu'}

        site_path = site.get('path', '')
        if not os.path.exists(site_path):
            return {'success': False, 'error': f'Path {site_path} inexistant'}

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"{self.SITES_BACKUP_DIR}/{site['domaine']}"
        os.makedirs(backup_dir, exist_ok=True)
        archive_path = f"{backup_dir}/{site['domaine']}_{timestamp}"

        try:
            result = shutil.make_archive(archive_path, 'gztar', site_path)
            size_mb = round(os.path.getsize(result) / (1024 * 1024), 2)
            log_agent(self.name, f"Site backup: {site['domaine']} -> {result} ({size_mb}MB)")
            return {'success': True, 'path': result, 'size_mb': size_mb, 'site': site['domaine']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def backup_all(self):
        """Backup complet: DB + tous les sites"""
        results = {'database': self.backup_database(), 'sites': {}}
        for site_id in SITES:
            results['sites'][site_id] = self.backup_site_files(site_id)

        total_size = results['database'].get('size_mb', 0)
        for s in results['sites'].values():
            total_size += s.get('size_mb', 0)

        results['total_size_mb'] = round(total_size, 2)
        results['timestamp'] = datetime.now().isoformat()
        log_agent(self.name, f"Full backup: {results['total_size_mb']}MB total")
        return results

    def cleanup_old_backups(self):
        """Supprime les anciens backups (garde les MAX_BACKUPS derniers)"""
        cleaned = {'db': 0, 'sites': 0}

        # DB backups
        if os.path.exists(self.BACKUP_DIR):
            db_files = sorted([f for f in os.listdir(self.BACKUP_DIR) if f.endswith('.db')], reverse=True)
            for old_file in db_files[self.MAX_BACKUPS:]:
                os.remove(os.path.join(self.BACKUP_DIR, old_file))
                cleaned['db'] += 1

        # Site backups
        if os.path.exists(self.SITES_BACKUP_DIR):
            for site_dir in os.listdir(self.SITES_BACKUP_DIR):
                site_backup_path = os.path.join(self.SITES_BACKUP_DIR, site_dir)
                if os.path.isdir(site_backup_path):
                    archives = sorted(os.listdir(site_backup_path), reverse=True)
                    for old_file in archives[self.MAX_BACKUPS:]:
                        os.remove(os.path.join(site_backup_path, old_file))
                        cleaned['sites'] += 1

        log_agent(self.name, f"Cleanup: {cleaned['db']} DB + {cleaned['sites']} sites supprimes")
        return cleaned

    def list_backups(self):
        """Liste tous les backups existants"""
        backups = {'database': [], 'sites': {}}

        if os.path.exists(self.BACKUP_DIR):
            for f in sorted(os.listdir(self.BACKUP_DIR), reverse=True)[:10]:
                fpath = os.path.join(self.BACKUP_DIR, f)
                backups['database'].append({
                    'file': f,
                    'size_mb': round(os.path.getsize(fpath) / (1024 * 1024), 2),
                    'date': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                })

        if os.path.exists(self.SITES_BACKUP_DIR):
            for site_dir in os.listdir(self.SITES_BACKUP_DIR):
                site_backup_path = os.path.join(self.SITES_BACKUP_DIR, site_dir)
                if os.path.isdir(site_backup_path):
                    backups['sites'][site_dir] = []
                    for f in sorted(os.listdir(site_backup_path), reverse=True)[:5]:
                        fpath = os.path.join(site_backup_path, f)
                        backups['sites'][site_dir].append({
                            'file': f,
                            'size_mb': round(os.path.getsize(fpath) / (1024 * 1024), 2),
                            'date': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                        })

        return backups

class AnalyticsAgent:
    """Agent 24: Analyse des donnees complete"""
    name = "Analytics Agent"

    def get_site_stats(self, site_id):
        """Statistiques completes d'un site"""
        conn = get_db()
        cursor = conn.cursor()

        stats = {'site_id': site_id, 'domain': SITES.get(site_id, {}).get('domaine', 'unknown')}

        # Keywords
        cursor.execute('SELECT COUNT(*) FROM keywords WHERE site_id = ?', (site_id,))
        stats['keywords_total'] = cursor.fetchone()[0]

        cursor.execute('SELECT keyword, volume, difficulty FROM keywords WHERE site_id = ? ORDER BY volume DESC LIMIT 5', (site_id,))
        stats['top_keywords'] = [{'keyword': r[0], 'volume': r[1], 'difficulty': r[2]} for r in cursor.fetchall()]

        # Drafts
        cursor.execute('SELECT COUNT(*) FROM drafts WHERE site_id = ?', (site_id,))
        stats['drafts_total'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM drafts WHERE site_id = ? AND status = 'approved'", (site_id,))
        stats['drafts_approved'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM drafts WHERE site_id = ? AND status = 'pending'", (site_id,))
        stats['drafts_pending'] = cursor.fetchone()[0]

        # Alerts
        cursor.execute('SELECT COUNT(*) FROM mon_alerts WHERE (site_id = ? OR site_id = ?) AND resolved = 0', (site_id, str(site_id)))
        stats['active_alerts'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM mon_alerts WHERE (site_id = ? OR site_id = ?) AND resolved = 1', (site_id, str(site_id)))
        stats['resolved_alerts'] = cursor.fetchone()[0]

        # Agent logs
        cursor.execute("SELECT COUNT(*) FROM agent_logs WHERE created_at > datetime('now', '-7 days')")
        stats['agent_actions_7d'] = cursor.fetchone()[0]

        # Self-audit
        try:
            cursor.execute('SELECT COUNT(*), SUM(CASE WHEN auto_fixed = 1 THEN 1 ELSE 0 END) FROM self_audit_results WHERE site_id = ?',
                (SITES.get(site_id, {}).get('domaine', '').split('.')[0],))
            row = cursor.fetchone()
            stats['self_audit_issues'] = row[0] if row else 0
            stats['self_audit_auto_fixed'] = row[1] if row else 0
        except:
            stats['self_audit_issues'] = 0
            stats['self_audit_auto_fixed'] = 0

        conn.close()
        log_agent(self.name, f"Stats site {site_id}: {stats['keywords_total']} kw, {stats['drafts_total']} drafts, {stats['active_alerts']} alerts")
        return stats

    def get_global_stats(self):
        """Statistiques globales de tout le systeme"""
        conn = get_db()
        cursor = conn.cursor()

        stats = {'timestamp': datetime.now().isoformat(), 'sites': {}}

        # Per-site stats
        for site_id, site in SITES.items():
            stats['sites'][site_id] = {'name': site['nom'], 'domain': site['domaine']}

            cursor.execute('SELECT COUNT(*) FROM keywords WHERE site_id = ?', (site_id,))
            stats['sites'][site_id]['keywords'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM drafts WHERE site_id = ?', (site_id,))
            stats['sites'][site_id]['drafts'] = cursor.fetchone()[0]

        # Global counts
        cursor.execute('SELECT COUNT(*) FROM keywords')
        stats['total_keywords'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM drafts')
        stats['total_drafts'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM mon_alerts WHERE resolved = 0')
        stats['active_alerts'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM mon_alerts WHERE resolved = 1')
        stats['resolved_alerts'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_logs WHERE created_at > datetime('now', '-24 hours')")
        stats['agent_actions_24h'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_logs WHERE created_at > datetime('now', '-7 days')")
        stats['agent_actions_7d'] = cursor.fetchone()[0]

        # Top agents by activity
        cursor.execute("""SELECT agent_name, COUNT(*) as cnt FROM agent_logs
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY agent_name ORDER BY cnt DESC LIMIT 10""")
        stats['top_agents'] = [{'agent': r[0], 'actions': r[1]} for r in cursor.fetchall()]

        conn.close()
        return stats

    def get_trends(self, days=7):
        """Tendances sur les X derniers jours"""
        conn = get_db()
        cursor = conn.cursor()

        trends = {'period_days': days, 'daily': []}

        for i in range(days):
            day_offset = days - 1 - i
            cursor.execute(f"""SELECT
                COUNT(*) as actions,
                (SELECT COUNT(*) FROM mon_alerts WHERE date(created_at) = date('now', '-{day_offset} days')) as new_alerts,
                (SELECT COUNT(*) FROM mon_alerts WHERE date(resolved_at) = date('now', '-{day_offset} days')) as resolved_alerts,
                (SELECT COUNT(*) FROM drafts WHERE date(created_at) = date('now', '-{day_offset} days')) as new_drafts
            FROM agent_logs WHERE date(created_at) = date('now', '-{day_offset} days')""")
            row = cursor.fetchone()
            target_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            trends['daily'].append({
                'date': target_date,
                'agent_actions': row[0] if row else 0,
                'new_alerts': row[1] if row else 0,
                'resolved_alerts': row[2] if row else 0,
                'new_drafts': row[3] if row else 0
            })

        conn.close()
        return trends

    def get_health_score(self):
        """Score de sante global du systeme"""
        conn = get_db()
        cursor = conn.cursor()

        score = 100
        issues = []

        # Check active alerts
        cursor.execute("SELECT COUNT(*) FROM mon_alerts WHERE resolved = 0 AND severity = 'critical'")
        critical = cursor.fetchone()[0]
        if critical > 0:
            score -= min(30, critical * 10)
            issues.append(f'{critical} alertes critiques actives')

        cursor.execute('SELECT COUNT(*) FROM mon_alerts WHERE resolved = 0')
        total_alerts = cursor.fetchone()[0]
        if total_alerts > 10:
            score -= 10
            issues.append(f'{total_alerts} alertes non resolues')

        # Check agent activity
        cursor.execute("SELECT COUNT(*) FROM agent_logs WHERE created_at > datetime('now', '-24 hours')")
        recent_actions = cursor.fetchone()[0]
        if recent_actions == 0:
            score -= 15
            issues.append('Aucune activite agent dans les 24h')

        # Check self-audit pending
        try:
            cursor.execute("SELECT COUNT(*) FROM self_audit_results WHERE fix_level = 'confirm' AND confirmed = 0")
            pending = cursor.fetchone()[0]
            if pending > 10:
                score -= 10
                issues.append(f'{pending} corrections en attente de confirmation')
        except:
            pass

        conn.close()

        grade = 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F'
        return {'score': max(0, score), 'grade': grade, 'issues': issues}

class ReportingAgent:
    """Agent 25: Generation de rapports"""
    name = "Reporting Agent"

    def generate_weekly_report(self, site_id):
        prompt = f"""Genere un rapport SEO hebdomadaire pour le site {site_id}:
Sections:
- Resume executif
- Performances
- Actions realisees
- Recommandations

Format JSON:
{{"summary": "...", "metrics": {{}}, "actions": [...], "recommendations": [...]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

class LandingPageAgent:
    """Agent 26: Creation de landing pages"""
    name = "Landing Page Agent"

    def generate_landing_page(self, site_id, service, keyword):
        site = SITES.get(site_id, {})
        prompt = f"""Cree une landing page pour {site.get('nom', '')}:
Service: {service}
Mot-cle: {keyword}

Sections:
- Hero avec headline puissant
- Probleme/Solution
- Benefices
- Temoignages (placeholder)
- FAQ
- CTA fort

Format JSON:
{{"headline": "...", "subheadline": "...", "hero_cta": "...", "benefits": [...], "faq": [...], "final_cta": "..."}}"""

        response = call_qwen(prompt, max_tokens=2000)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

class BlogIdeaAgent:
    """Agent 27: Generation d'idees de blog"""
    name = "Blog Idea Agent"

    def generate_ideas(self, site_id, count=20):
        site = SITES.get(site_id, {})
        prompt = f"""Genere {count} idees d'articles de blog pour {site.get('nom', '')}:
Niche: {site.get('niche', '')}
Region: Quebec

Inclure:
- Guides pratiques
- Comparatifs
- Saisonniers
- Questions frequentes
- Tendances

Format JSON:
{{"ideas": [{{"title": "...", "keyword": "...", "type": "guide|comparison|seasonal|faq|trend", "priority": 1-5}}]}}"""

        response = call_qwen(prompt, max_tokens=2000)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

class VideoScriptAgent:
    """Agent 28: Scripts video/TikTok"""
    name = "Video Script Agent"

    def generate_script(self, topic, duration_seconds=60):
        prompt = f"""Cree un script video de {duration_seconds} secondes sur: {topic}

Format TikTok/Reels:
- Hook accrocheur (3 sec)
- Contenu value (45 sec)
- CTA (10 sec)

Format JSON:
{{"hook": "...", "scenes": [{{"duration": X, "visual": "...", "voiceover": "..."}}], "cta": "...", "hashtags": [...]}}"""

        response = call_qwen(prompt)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

class ServiceDescriptionAgent:
    """Agent 29: Descriptions de services"""
    name = "Service Description Agent"

    def generate_service_page(self, site_id, service_name):
        site = SITES.get(site_id, {})
        prompt = f"""Cree une page de service complete pour {site.get('nom', '')}:
Service: {service_name}

Sections:
- Titre SEO
- Description (300 mots)
- Avantages (5-7)
- Processus (etapes)
- Tarification (placeholder)
- FAQ (5 questions)
- CTA

Format JSON:
{{"title": "...", "meta_description": "...", "description": "...", "benefits": [...], "process": [...], "faq": [...], "cta": "..."}}"""

        response = call_qwen(prompt, max_tokens=2500)
        if response:
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            except:
                pass
        return {}

# ============================================
# GOOGLE AGENT - Google APIs Integration
# GBP Reviews, Search Console, GA4, PageSpeed
# ============================================
class GoogleAgent:
    name = 'Google Agent'

    TOKEN_PATH = '/opt/seo-agent/google_tokens.json'
    PAGESPEED_API = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
    INDEXING_API = 'https://indexing.googleapis.com/v3/urlNotifications:publish'
    GBP_API_BASE = 'https://mybusiness.googleapis.com/v4'
    SC_API_BASE = 'https://www.googleapis.com/webmasters/v3'
    GA4_API_BASE = 'https://analyticsdata.googleapis.com/v1beta'

    # ------------------------------------------
    # DB Init
    # ------------------------------------------
    def init_db(self):
        """Create google_reviews and google_analytics_cache tables"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS google_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                review_id TEXT UNIQUE,
                author TEXT,
                rating INTEGER,
                text TEXT,
                reply TEXT,
                reply_date TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS google_analytics_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                property_id TEXT,
                metric TEXT,
                value TEXT,
                period TEXT,
                cached_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        conn.commit()
        conn.close()
        log_agent(self.name, 'Tables google_reviews et google_analytics_cache initialisees')

    # ------------------------------------------
    # Credential Management
    # ------------------------------------------
    def setup_credentials(self, credentials_json_path):
        """Load OAuth2 credentials from JSON file, handle token refresh"""
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        try:
            # Try loading existing tokens first
            existing_creds = self._load_tokens()
            if existing_creds and existing_creds.get('refresh_token'):
                creds = Credentials(
                    token=existing_creds.get('access_token'),
                    refresh_token=existing_creds.get('refresh_token'),
                    token_uri=existing_creds.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=existing_creds.get('client_id'),
                    client_secret=existing_creds.get('client_secret')
                )
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self._save_tokens(creds)
                    log_agent(self.name, 'Tokens OAuth2 rafraichis avec succes')
                return creds

            # Load from credentials file (first time setup)
            with open(credentials_json_path, 'r') as f:
                cred_data = json.load(f)

            if 'installed' in cred_data or 'web' in cred_data:
                from google_auth_oauthlib.flow import InstalledAppFlow
                scopes = [
                    'https://www.googleapis.com/auth/business.manage',
                    'https://www.googleapis.com/auth/webmasters.readonly',
                    'https://www.googleapis.com/auth/analytics.readonly',
                    'https://www.googleapis.com/auth/indexing'
                ]
                flow = InstalledAppFlow.from_client_secrets_file(credentials_json_path, scopes=scopes)
                creds = flow.run_local_server(port=0)
                self._save_tokens(creds)
                log_agent(self.name, 'OAuth2 credentials configures et sauvegardes')
                return creds

        except Exception as e:
            log_agent(self.name, f'Erreur setup credentials: {e}', level='ERROR')
            return None

    def _load_tokens(self):
        """Load saved tokens from disk"""
        try:
            with open(self.TOKEN_PATH, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _save_tokens(self, creds):
        """Save OAuth2 credentials to disk"""
        token_data = {
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }
        with open(self.TOKEN_PATH, 'w') as f:
            json.dump(token_data, f, indent=2)
        log_agent(self.name, 'Tokens sauvegardes dans ' + self.TOKEN_PATH)

    def _get_oauth_headers(self):
        """Get Authorization headers from saved tokens, auto-refresh if expired"""
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        tokens = self._load_tokens()
        if not tokens:
            log_agent(self.name, 'Aucun token trouve. Appeler setup_credentials() d\'abord.', level='ERROR')
            return None

        creds = Credentials(
            token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            token_uri=tokens.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=tokens.get('client_id'),
            client_secret=tokens.get('client_secret')
        )

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_tokens(creds)
                log_agent(self.name, 'Token rafraichi automatiquement')
            except Exception as e:
                log_agent(self.name, f'Erreur refresh token: {e}', level='ERROR')
                return None

        return {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }

    def _get_service_account_headers(self, scopes):
        """Get headers using service account credentials (for Analytics/Search Console)"""
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        sa_path = self.TOKEN_PATH.replace('google_tokens.json', 'service_account.json')
        try:
            creds = service_account.Credentials.from_service_account_file(sa_path, scopes=scopes)
            creds.refresh(Request())
            return {
                'Authorization': f'Bearer {creds.token}',
                'Content-Type': 'application/json'
            }
        except Exception as e:
            log_agent(self.name, f'Erreur service account: {e}', level='ERROR')
            # Fallback to OAuth2
            return self._get_oauth_headers()

    # ------------------------------------------
    # 1. Google Business Profile - Reviews
    # ------------------------------------------
    def get_reviews(self, account_id, location_id):
        """Fetch all reviews for a location"""
        headers = self._get_oauth_headers()
        if not headers:
            return {'error': 'Pas de credentials OAuth2 configures'}

        url = f'{self.GBP_API_BASE}/accounts/{account_id}/locations/{location_id}/reviews'
        all_reviews = []
        next_page_token = None

        try:
            while True:
                params = {'pageSize': 50}
                if next_page_token:
                    params['pageToken'] = next_page_token

                resp = requests.get(url, headers=headers, params=params, timeout=30)

                if resp.status_code != 200:
                    log_agent(self.name, f'Erreur API GBP reviews: {resp.status_code} - {resp.text}', level='ERROR')
                    return {'error': f'API error {resp.status_code}', 'details': resp.text}

                data = resp.json()
                reviews = data.get('reviews', [])
                all_reviews.extend(reviews)

                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break

            # Save to DB
            self._save_reviews_to_db(all_reviews, location_id)

            log_agent(self.name, f'Recupere {len(all_reviews)} avis pour location {location_id}')
            return {
                'total': len(all_reviews),
                'reviews': all_reviews
            }

        except Exception as e:
            log_agent(self.name, f'Erreur get_reviews: {e}', level='ERROR')
            return {'error': str(e)}

    def _save_reviews_to_db(self, reviews, location_id):
        """Save reviews to local DB"""
        conn = get_db()
        cursor = conn.cursor()

        # Find site_id from location context
        site_id = None
        for sid, site in SITES.items():
            if site.get('gbp_location') == location_id:
                site_id = sid
                break

        for review in reviews:
            review_id = review.get('reviewId', review.get('name', '').split('/')[-1])
            author = review.get('reviewer', {}).get('displayName', 'Anonyme')
            rating = review.get('starRating', 'FIVE')
            rating_map = {'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5}
            rating_num = rating_map.get(rating, 5)
            text = review.get('comment', '')
            existing_reply = review.get('reviewReply', {}).get('comment', '')

            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO google_reviews
                    (site_id, review_id, author, rating, text, reply)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (site_id, review_id, author, rating_num, text, existing_reply))
            except Exception:
                pass

        conn.commit()
        conn.close()

    def generate_review_reply(self, review, site_id=None):
        """Use call_qwen() to generate a personalized reply based on review rating, text, author"""
        author = review.get('reviewer', {}).get('displayName', 'client')
        rating_raw = review.get('starRating', 'FIVE')
        rating_map = {'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5}
        rating = rating_map.get(rating_raw, 5)
        text = review.get('comment', '')
        business_name = SITES.get(site_id, {}).get('nom', 'notre entreprise') if site_id else 'notre entreprise'

        if rating == 5:
            tone_instruction = (
                'Remercie chaleureusement le client. Mentionne un detail specifique '
                'du service si le texte de l\'avis en parle. Montre de la gratitude sincere.'
            )
        elif rating == 4:
            tone_instruction = (
                'Remercie le client pour son avis positif. Reconnais qu\'il y a '
                'toujours place a l\'amelioration. Invite-le a revenir.'
            )
        elif rating == 3:
            tone_instruction = (
                'Remercie le client pour son avis honnete. Presente des excuses '
                'pour l\'experience mitigee. Offre de t\'ameliorer et invite-le a te contacter.'
            )
        else:
            tone_instruction = (
                'Sois empathique et professionnel. Presente des excuses sinceres. '
                'Offre de resoudre le probleme. Invite le client a te contacter directement '
                'pour discuter de la situation.'
            )

        prompt = f"""Genere une reponse a cet avis Google pour l'entreprise "{business_name}".

NOM DU CLIENT: {author}
NOTE: {rating}/5
TEXTE DE L'AVIS: {text if text else '(aucun commentaire)'}

INSTRUCTIONS IMPORTANTES:
- Ecris en FRANCAIS QUEBECOIS AUTHENTIQUE (pas de francais de France)
- Utilise des expressions quebecoises naturelles: "ben content", "ca fait plaisir", "au plaisir", "merci ben gros", "on apprecie", "c'est le fun"
- {tone_instruction}
- 2 a 4 phrases MAXIMUM
- Termine avec le nom de l'entreprise: {business_name}
- PAS d'emojis, PAS de hashtags
- Ton chaleureux et authentique, comme un vrai quebecois qui parle a son client
- NE PAS utiliser de tags <think> ou autre formatage
- Reponds DIRECTEMENT avec le texte de la reponse seulement"""

        reply = call_qwen(prompt, max_tokens=500, system_prompt='Tu es un gestionnaire de reputation en ligne au Quebec.')

        if reply:
            # Clean up potential markdown or extra formatting
            reply = reply.strip()
            # Remove think tags
            import re
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL)
            reply = re.sub(r"<think>.*", "", reply, flags=re.DOTALL)
            reply = reply.strip()
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1]
            log_agent(self.name, f'Reponse generee pour avis de {author} ({rating}/5)')
            return reply

        log_agent(self.name, 'Echec generation reponse avis', level='ERROR')
        return None

    def reply_to_review(self, account_id, location_id, review_id, reply_text):
        """Post a reply to a specific review via API"""
        headers = self._get_oauth_headers()
        if not headers:
            return {'error': 'Pas de credentials OAuth2 configures'}

        url = (
            f'{self.GBP_API_BASE}/accounts/{account_id}'
            f'/locations/{location_id}/reviews/{review_id}/reply'
        )
        payload = {'comment': reply_text}

        try:
            resp = requests.put(url, headers=headers, json=payload, timeout=30)

            if resp.status_code in (200, 201):
                # Update DB
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE google_reviews
                    SET reply = ?, reply_date = datetime('now')
                    WHERE review_id = ?
                ''', (reply_text, review_id))
                conn.commit()
                conn.close()

                log_agent(self.name, f'Reponse postee pour avis {review_id}')
                return {'success': True, 'review_id': review_id}

            log_agent(self.name, f'Erreur reply review: {resp.status_code} - {resp.text}', level='ERROR')
            return {'error': f'API error {resp.status_code}', 'details': resp.text}

        except Exception as e:
            log_agent(self.name, f'Erreur reply_to_review: {e}', level='ERROR')
            return {'error': str(e)}

    def auto_reply_all_reviews(self, account_id, location_id, site_id=None, dry_run=True):
        """Fetch unreplied reviews, generate AI replies, optionally post them. dry_run=True just generates without posting"""
        result = self.get_reviews(account_id, location_id)
        if 'error' in result:
            return result

        reviews = result.get('reviews', [])
        unreplied = [r for r in reviews if not r.get('reviewReply')]

        log_agent(self.name, f'{len(unreplied)} avis sans reponse sur {len(reviews)} total')

        replies = []
        for review in unreplied:
            review_id = review.get('reviewId', review.get('name', '').split('/')[-1])
            reply_text = self.generate_review_reply(review, site_id=site_id)

            if not reply_text:
                continue

            entry = {
                'review_id': review_id,
                'author': review.get('reviewer', {}).get('displayName', 'Anonyme'),
                'rating': review.get('starRating', 'FIVE'),
                'comment': review.get('comment', ''),
                'generated_reply': reply_text,
                'posted': False
            }

            if not dry_run:
                post_result = self.reply_to_review(account_id, location_id, review_id, reply_text)
                entry['posted'] = post_result.get('success', False)
                entry['post_result'] = post_result

            replies.append(entry)

        mode = 'DRY RUN' if dry_run else 'LIVE'
        log_agent(self.name, f'Auto-reply {mode}: {len(replies)} reponses generees')

        return {
            'mode': mode,
            'total_reviews': len(reviews),
            'unreplied': len(unreplied),
            'replies_generated': len(replies),
            'replies': replies
        }

    # ------------------------------------------
    # 2. Google Search Console
    # ------------------------------------------
    def get_search_performance(self, site_url, days=30):
        """Fetch search performance data (clicks, impressions, CTR, position) for last N days"""
        headers = self._get_service_account_headers(
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        if not headers:
            return {'error': 'Pas de credentials configures'}

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        url = f'{self.SC_API_BASE}/sites/{requests.utils.quote(site_url, safe="")}/searchAnalytics/query'

        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date'],
            'rowLimit': 5000
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                log_agent(self.name, f'Erreur Search Console: {resp.status_code}', level='ERROR')
                return {'error': f'API error {resp.status_code}', 'details': resp.text}

            data = resp.json()
            rows = data.get('rows', [])

            total_clicks = sum(r.get('clicks', 0) for r in rows)
            total_impressions = sum(r.get('impressions', 0) for r in rows)
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            avg_position = (
                sum(r.get('position', 0) for r in rows) / len(rows)
            ) if rows else 0

            daily = []
            for row in rows:
                daily.append({
                    'date': row['keys'][0],
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': round(row.get('ctr', 0) * 100, 2),
                    'position': round(row.get('position', 0), 1)
                })

            result = {
                'site_url': site_url,
                'period': f'{start_date} - {end_date}',
                'days': days,
                'summary': {
                    'total_clicks': total_clicks,
                    'total_impressions': total_impressions,
                    'avg_ctr': round(avg_ctr, 2),
                    'avg_position': round(avg_position, 1)
                },
                'daily': daily
            }

            log_agent(
                self.name,
                f'Search Console {site_url}: {total_clicks} clics, '
                f'{total_impressions} impressions, CTR {avg_ctr:.1f}%, pos {avg_position:.1f}'
            )
            return result

        except Exception as e:
            log_agent(self.name, f'Erreur get_search_performance: {e}', level='ERROR')
            return {'error': str(e)}

    def get_top_queries(self, site_url, limit=20):
        """Get top search queries with clicks/impressions"""
        headers = self._get_service_account_headers(
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        if not headers:
            return {'error': 'Pas de credentials configures'}

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        url = f'{self.SC_API_BASE}/sites/{requests.utils.quote(site_url, safe="")}/searchAnalytics/query'

        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['query'],
            'rowLimit': limit,
            'orderBy': 'clicks',
            'dimensionFilterGroups': []
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                log_agent(self.name, f'Erreur top queries: {resp.status_code}', level='ERROR')
                return {'error': f'API error {resp.status_code}', 'details': resp.text}

            data = resp.json()
            rows = data.get('rows', [])

            queries = []
            for row in rows:
                queries.append({
                    'query': row['keys'][0],
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': round(row.get('ctr', 0) * 100, 2),
                    'position': round(row.get('position', 0), 1)
                })

            log_agent(self.name, f'Top {len(queries)} queries pour {site_url}')
            return {
                'site_url': site_url,
                'period': f'{start_date} - {end_date}',
                'queries': queries
            }

        except Exception as e:
            log_agent(self.name, f'Erreur get_top_queries: {e}', level='ERROR')
            return {'error': str(e)}

    def get_indexing_status(self, site_url):
        """Check indexing coverage via Search Console API"""
        headers = self._get_service_account_headers(
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        if not headers:
            return {'error': 'Pas de credentials configures'}

        url = f'{self.SC_API_BASE}/sites/{requests.utils.quote(site_url, safe="")}/sitemaps'

        try:
            resp = requests.get(url, headers=headers, timeout=30)

            if resp.status_code != 200:
                log_agent(self.name, f'Erreur indexing status: {resp.status_code}', level='ERROR')
                return {'error': f'API error {resp.status_code}', 'details': resp.text}

            data = resp.json()
            sitemaps = data.get('sitemap', [])

            total_submitted = 0
            total_indexed = 0
            sitemap_details = []

            for sm in sitemaps:
                submitted = 0
                indexed = 0
                for content in sm.get('contents', []):
                    submitted += content.get('submitted', 0)
                    indexed += content.get('indexed', 0)

                total_submitted += submitted
                total_indexed += indexed

                sitemap_details.append({
                    'path': sm.get('path', ''),
                    'last_submitted': sm.get('lastSubmitted', ''),
                    'last_downloaded': sm.get('lastDownloaded', ''),
                    'is_pending': sm.get('isPending', False),
                    'submitted': submitted,
                    'indexed': indexed
                })

            index_rate = (total_indexed / total_submitted * 100) if total_submitted > 0 else 0

            result = {
                'site_url': site_url,
                'total_submitted': total_submitted,
                'total_indexed': total_indexed,
                'index_rate': round(index_rate, 1),
                'sitemaps': sitemap_details
            }

            log_agent(
                self.name,
                f'Indexation {site_url}: {total_indexed}/{total_submitted} '
                f'({index_rate:.1f}%)'
            )
            return result

        except Exception as e:
            log_agent(self.name, f'Erreur get_indexing_status: {e}', level='ERROR')
            return {'error': str(e)}

    def request_indexing(self, page_url):
        """Request URL indexing via Indexing API"""
        headers = self._get_service_account_headers(
            scopes=['https://www.googleapis.com/auth/indexing']
        )
        if not headers:
            return {'error': 'Pas de credentials configures'}

        payload = {
            'url': page_url,
            'type': 'URL_UPDATED'
        }

        try:
            resp = requests.post(self.INDEXING_API, headers=headers, json=payload, timeout=30)

            if resp.status_code in (200, 201):
                data = resp.json()
                log_agent(self.name, f'Indexation demandee pour {page_url}')
                return {
                    'success': True,
                    'url': page_url,
                    'notification_time': data.get('urlNotificationMetadata', {}).get('latestUpdate', {}).get('notifyTime', '')
                }

            log_agent(self.name, f'Erreur request indexing: {resp.status_code}', level='ERROR')
            return {'error': f'API error {resp.status_code}', 'details': resp.text}

        except Exception as e:
            log_agent(self.name, f'Erreur request_indexing: {e}', level='ERROR')
            return {'error': str(e)}

    # ------------------------------------------
    # 3. Google Analytics (GA4)
    # ------------------------------------------
    def get_analytics_summary(self, property_id, days=30, site_id=None):
        """Fetch GA4 summary: sessions, users, pageviews, bounce rate"""
        headers = self._get_service_account_headers(
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        if not headers:
            return {'error': 'Pas de credentials configures'}

        url = f'{self.GA4_API_BASE}/properties/{property_id}:runReport'

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        payload = {
            'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
            'metrics': [
                {'name': 'sessions'},
                {'name': 'totalUsers'},
                {'name': 'screenPageViews'},
                {'name': 'bounceRate'},
                {'name': 'averageSessionDuration'},
                {'name': 'newUsers'}
            ]
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                log_agent(self.name, f'Erreur GA4 summary: {resp.status_code}', level='ERROR')
                return {'error': f'API error {resp.status_code}', 'details': resp.text}

            data = resp.json()
            rows = data.get('rows', [])

            if not rows:
                return {
                    'property_id': property_id,
                    'period': f'{start_date} - {end_date}',
                    'summary': 'Aucune donnee pour cette periode'
                }

            values = rows[0].get('metricValues', [])

            summary = {
                'sessions': int(values[0].get('value', 0)) if len(values) > 0 else 0,
                'users': int(values[1].get('value', 0)) if len(values) > 1 else 0,
                'pageviews': int(values[2].get('value', 0)) if len(values) > 2 else 0,
                'bounce_rate': round(float(values[3].get('value', 0)) * 100, 1) if len(values) > 3 else 0,
                'avg_session_duration': round(float(values[4].get('value', 0)), 1) if len(values) > 4 else 0,
                'new_users': int(values[5].get('value', 0)) if len(values) > 5 else 0
            }

            result = {
                'property_id': property_id,
                'period': f'{start_date} - {end_date}',
                'days': days,
                'summary': summary
            }

            # Cache to DB
            if site_id:
                self._cache_analytics(site_id, property_id, summary, f'{start_date}_{end_date}')

            log_agent(
                self.name,
                f'GA4 {property_id}: {summary["sessions"]} sessions, '
                f'{summary["users"]} users, {summary["pageviews"]} pageviews'
            )
            return result

        except Exception as e:
            log_agent(self.name, f'Erreur get_analytics_summary: {e}', level='ERROR')
            return {'error': str(e)}

    def get_top_pages(self, property_id, limit=10):
        """Get top pages by sessions"""
        headers = self._get_service_account_headers(
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        if not headers:
            return {'error': 'Pas de credentials configures'}

        url = f'{self.GA4_API_BASE}/properties/{property_id}:runReport'

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        payload = {
            'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
            'dimensions': [{'name': 'pagePath'}],
            'metrics': [
                {'name': 'sessions'},
                {'name': 'screenPageViews'},
                {'name': 'averageSessionDuration'},
                {'name': 'bounceRate'}
            ],
            'orderBys': [{'metric': {'metricName': 'sessions'}, 'desc': True}],
            'limit': limit
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                log_agent(self.name, f'Erreur GA4 top pages: {resp.status_code}', level='ERROR')
                return {'error': f'API error {resp.status_code}', 'details': resp.text}

            data = resp.json()
            rows = data.get('rows', [])

            pages = []
            for row in rows:
                dims = row.get('dimensionValues', [])
                vals = row.get('metricValues', [])
                pages.append({
                    'page': dims[0].get('value', '') if dims else '',
                    'sessions': int(vals[0].get('value', 0)) if len(vals) > 0 else 0,
                    'pageviews': int(vals[1].get('value', 0)) if len(vals) > 1 else 0,
                    'avg_duration': round(float(vals[2].get('value', 0)), 1) if len(vals) > 2 else 0,
                    'bounce_rate': round(float(vals[3].get('value', 0)) * 100, 1) if len(vals) > 3 else 0
                })

            log_agent(self.name, f'Top {len(pages)} pages pour GA4 {property_id}')
            return {
                'property_id': property_id,
                'period': f'{start_date} - {end_date}',
                'pages': pages
            }

        except Exception as e:
            log_agent(self.name, f'Erreur get_top_pages: {e}', level='ERROR')
            return {'error': str(e)}

    def _cache_analytics(self, site_id, property_id, metrics, period):
        """Cache analytics data to DB"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            for metric_name, value in metrics.items():
                cursor.execute('''
                    INSERT INTO google_analytics_cache
                    (site_id, property_id, metric, value, period, cached_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (site_id, property_id, metric_name, str(value), period))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ------------------------------------------
    # 4. PageSpeed Insights
    # ------------------------------------------
    def check_pagespeed(self, url, strategy='mobile'):
        """Run PageSpeed Insights audit (no auth needed, uses public API)"""
        params = {
            'url': url,
            'strategy': strategy,
            'category': 'performance'
        }

        # Add API key if available (higher quota)
        import os
        api_key = os.getenv('GOOGLE_PAGESPEED_API_KEY', '')
        if api_key:
            params['key'] = api_key

        try:
            resp = requests.get(self.PAGESPEED_API, params=params, timeout=60)

            if resp.status_code != 200:
                log_agent(self.name, f'Erreur PageSpeed: {resp.status_code}', level='ERROR')
                return {'error': f'API error {resp.status_code}', 'url': url}

            data = resp.json()

            # Lighthouse results
            lighthouse = data.get('lighthouseResult', {})
            categories = lighthouse.get('categories', {})
            audits = lighthouse.get('audits', {})

            perf_score = categories.get('performance', {}).get('score', 0)
            perf_score = round(perf_score * 100) if perf_score else 0

            # Core Web Vitals
            cwv = {}
            cwv_audits = {
                'largest-contentful-paint': 'LCP',
                'first-contentful-paint': 'FCP',
                'total-blocking-time': 'TBT',
                'cumulative-layout-shift': 'CLS',
                'speed-index': 'Speed Index',
                'interactive': 'TTI'
            }

            for audit_id, label in cwv_audits.items():
                audit = audits.get(audit_id, {})
                cwv[label] = {
                    'value': audit.get('displayValue', 'N/A'),
                    'score': round(audit.get('score', 0) * 100) if audit.get('score') else 0
                }

            # Key opportunities
            opportunities = []
            for audit_id, audit in audits.items():
                if audit.get('details', {}).get('type') == 'opportunity':
                    savings = audit.get('details', {}).get('overallSavingsMs', 0)
                    if savings > 0:
                        opportunities.append({
                            'title': audit.get('title', ''),
                            'description': audit.get('description', ''),
                            'savings_ms': round(savings),
                            'score': round(audit.get('score', 0) * 100) if audit.get('score') else 0
                        })

            opportunities.sort(key=lambda x: x['savings_ms'], reverse=True)

            # Field data (CrUX)
            loading_experience = data.get('loadingExperience', {})
            field_metrics = loading_experience.get('metrics', {})

            field_data = {}
            for metric_key, metric_data in field_metrics.items():
                field_data[metric_key] = {
                    'percentile': metric_data.get('percentile', 'N/A'),
                    'category': metric_data.get('category', 'N/A')
                }

            grade = (
                'A' if perf_score >= 90 else
                'B' if perf_score >= 75 else
                'C' if perf_score >= 50 else
                'D' if perf_score >= 25 else 'F'
            )

            result = {
                'url': url,
                'strategy': strategy,
                'performance_score': perf_score,
                'grade': grade,
                'core_web_vitals': cwv,
                'opportunities': opportunities[:5],
                'field_data': field_data
            }

            log_agent(
                self.name,
                f'PageSpeed {url} ({strategy}): score {perf_score}/100 ({grade})'
            )
            return result

        except Exception as e:
            log_agent(self.name, f'Erreur check_pagespeed: {e}', level='ERROR')
            return {'error': str(e), 'url': url}

    # ------------------------------------------
    # Utility: Full Site Report
    # ------------------------------------------
    def full_site_report(self, site_id, account_id=None, location_id=None, property_id=None):
        """Generate a comprehensive Google report for a site"""
        site = SITES.get(site_id)
        if not site:
            return {'error': f'Site ID {site_id} introuvable'}

        domain = site['domaine']
        report = {
            'site': site['nom'],
            'domain': domain,
            'generated_at': datetime.now().isoformat()
        }

        # PageSpeed (always available, no auth needed)
        report['pagespeed_mobile'] = self.check_pagespeed(f'https://{domain}', strategy='mobile')
        report['pagespeed_desktop'] = self.check_pagespeed(f'https://{domain}', strategy='desktop')

        # Search Console
        site_url = f'sc-domain:{domain}'
        report['search_performance'] = self.get_search_performance(site_url)
        report['top_queries'] = self.get_top_queries(site_url)
        report['indexing'] = self.get_indexing_status(site_url)

        # GA4
        if property_id:
            report['analytics'] = self.get_analytics_summary(property_id, site_id=site_id)
            report['top_pages'] = self.get_top_pages(property_id)

        # GBP Reviews
        if account_id and location_id:
            report['reviews'] = self.get_reviews(account_id, location_id)

        log_agent(self.name, f'Rapport complet genere pour {site["nom"]}')
        return report


class MasterOrchestrator:
    """Agent 30: Orchestrateur principal"""
    name = "Master Orchestrator"

    def __init__(self):
        self.agents = {
            'keyword_research': KeywordResearchAgent(),
            'content_generation': ContentGenerationAgent(),
            'faq_generation': FAQGenerationAgent(),
            'technical_seo': TechnicalSEOAuditAgent(),
            'performance': PerformanceAgent(),
            'backlink': BacklinkAnalysisAgent(),
            'local_seo': LocalSEOAgent(),
            'competitor': CompetitorAnalysisAgent(),
            'content_optimization': ContentOptimizationAgent(),
            'schema': SchemaMarkupAgent(),
            'social_media': SocialMediaAgent(),
            'email': EmailMarketingAgent(),
            'image': ImageOptimizationAgent(),
            'internal_linking': InternalLinkingAgent(),
            'url': URLOptimizationAgent(),
            'title_tag': TitleTagAgent(),
            'content_calendar': ContentCalendarAgent(),
            'pricing': PricingStrategyAgent(),
            'review': ReviewManagementAgent(),
            'conversion': ConversionOptimizationAgent(),
            'monitoring': MonitoringAgent(),
            'ssl': SSLAgent(),
            'backup': BackupAgent(),
            'analytics': AnalyticsAgent(),
            'reporting': ReportingAgent(),
            'landing_page': LandingPageAgent(),
            'blog_idea': BlogIdeaAgent(),
            'video_script': VideoScriptAgent(),
            'service_description': ServiceDescriptionAgent(),
            'google': GoogleAgent()
        }

    def run_full_audit(self, site_id):
        """Execute un audit complet"""
        site = SITES.get(site_id, {})
        results = {}

        log_agent(self.name, f"Demarrage audit complet pour {site.get('nom', '')}")

        # Technical SEO
        results['technical'] = self.agents['technical_seo'].audit_page(f"https://{site.get('domaine', '')}")

        # Performance
        results['performance'] = self.agents['performance'].check_speed(f"https://{site.get('domaine', '')}")

        # SSL
        results['ssl'] = self.agents['ssl'].check_ssl(site.get('domaine', ''))

        # Analytics
        results['analytics'] = self.agents['analytics'].get_site_stats(site_id)

        log_agent(self.name, f"Audit termine pour {site.get('nom', '')}")
        return results

    def run_content_generation(self, site_id, keyword):
        """Execute generation de contenu complete"""
        results = {}

        # Generate article
        results['article'] = self.agents['content_generation'].generate_article(site_id, keyword)

        # Generate FAQ
        results['faq'] = self.agents['faq_generation'].generate_faq(site_id, keyword, 5)

        # Generate schema
        if results.get('faq'):
            results['faq_schema'] = self.agents['schema'].generate_faq_schema(results['faq'])

        # Generate social posts
        if results.get('article', {}).get('titre'):
            results['social'] = self.agents['social_media'].generate_social_posts(
                results['article']['titre'],
                f"https://{SITES.get(site_id, {}).get('domaine', '')}/blog"
            )

        return results

    def get_all_agents_status(self):
        """Retourne le status de tous les agents depuis la DB"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT agent_name, agent_type, description, is_active FROM agents ORDER BY id').fetchall()
            conn.close()
            if rows:
                return [{'name': r['description'], 'status': 'active' if r['is_active'] else 'inactive', 'type': r['agent_name']} for r in rows]
        except Exception:
            pass
        # Fallback sur les agents instancies
        return [{'name': agent.name, 'status': 'active', 'type': key} for key, agent in self.agents.items()]


# ============================================
# API ENDPOINTS FOR AGENTS
# ============================================

def register_agent_routes(app):
    """Enregistre les routes API pour les agents"""

    orchestrator = MasterOrchestrator()

    @app.route('/api/agents/list', methods=['GET'])
    def list_agents():
        return jsonify({'agents': orchestrator.get_all_agents_status()})

    @app.route('/api/agents/audit/<int:site_id>', methods=['POST'])
    def run_audit(site_id):
        results = orchestrator.run_full_audit(site_id)
        return jsonify(results)

    @app.route('/api/agents/generate-content', methods=['POST'])
    def generate_content():
        data = request.get_json()
        site_id = data.get('site_id', 1)
        keyword = data.get('keyword', '')
        results = orchestrator.run_content_generation(site_id, keyword)
        return jsonify(results)

    @app.route('/api/agents/keywords/research', methods=['POST'])
    def research_keywords():
        data = request.get_json()
        agent = KeywordResearchAgent()
        keywords = agent.find_keywords(
            data.get('site_id', 1),
            data.get('seed_keyword', ''),
            data.get('limit', 10)
        )
        return jsonify({'keywords': keywords})

    @app.route('/api/agents/calendar/<int:site_id>', methods=['GET'])
    def get_calendar(site_id):
        agent = ContentCalendarAgent()
        calendar = agent.generate_calendar(site_id)
        return jsonify(calendar)

    @app.route('/api/agents/ideas/<int:site_id>', methods=['GET'])
    def get_blog_ideas(site_id):
        agent = BlogIdeaAgent()
        ideas = agent.generate_ideas(site_id)
        return jsonify(ideas)


if __name__ == '__main__':
    print("SEO AI Agents System - 30 Agents Ready")
    print("=" * 50)

    orchestrator = MasterOrchestrator()
    agents = orchestrator.get_all_agents_status()

    for i, agent in enumerate(agents, 1):
        print(f"{i:2}. {agent['name']}")

    print("=" * 50)
    print("Use: from agents_system import MasterOrchestrator")


# ============================================
# NOUVEAUX AGENTS - BACKLINKS & PRÉSENCE WEB
# ============================================

class RedditAgent:
    """Agent pour créer du contenu Reddit authentique"""
    
    SUBREDDITS = {
        1: ['montreal', 'quebec', 'homeowners'],  # Déneigement
        2: ['montreal', 'quebec', 'landscaping', 'gardening'],  # Paysagement
        3: ['montreal', 'quebec', 'HomeImprovement', 'DIY']  # Peinture
    }
    
    def generate_reddit_post(self, site_id, topic):
        """Génère un post Reddit authentique (pas spam)"""
        site = SITES.get(site_id, {})
        prompt = f"""Génère un post Reddit AUTHENTIQUE pour r/montreal ou r/quebec.

SUJET: {topic}
NICHE: {site.get('niche', '')}
RÉGION: Montréal/Québec

RÈGLES IMPORTANTES:
- Ton conversationnel, comme un vrai québécois
- PAS de publicité directe
- Partager une expérience ou poser une question
- Être utile à la communauté
- Maximum 200 mots
- Peut mentionner subtilement le service sans lien

FORMAT JSON:
{{
    "title": "Titre accrocheur style Reddit",
    "body": "Contenu du post...",
    "subreddit": "montreal",
    "type": "discussion|question|story"
}}
"""
        return self._call_ai(prompt)
    
    def generate_reddit_comment(self, site_id, context):
        """Génère une réponse utile à un post existant"""
        site = SITES.get(site_id, {})
        prompt = f"""Génère une RÉPONSE Reddit utile et authentique.

CONTEXTE DU POST: {context}
EXPERTISE: {site.get('niche', '')}
RÉGION: Québec

RÈGLES:
- Réponse utile et informative
- Ton amical québécois
- Partager expertise sans vendre
- 50-150 mots max
- PAS de lien direct

FORMAT JSON:
{{
    "comment": "Ta réponse ici...",
    "adds_value": true
}}
"""
        return self._call_ai(prompt)
    
    def _call_ai(self, prompt):
        try:
            # Utilise Ollama LOCAL pour les posts Reddit (petite tache)
            response = call_ollama(prompt, 800)
            if not response:
                # Fallback Fireworks si Ollama echoue
                response = call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None


class ForumAgent:
    """Agent pour participation aux forums québécois"""

    FORUMS = [
        {'name': 'ForumConstruction', 'url': 'forumconstruction.com', 'niches': [1, 2, 3]},
        {'name': 'RénoQuébec', 'url': 'renoquebec.com', 'niches': [3]},
        {'name': 'Jardinage Québec', 'url': 'jardinage.net', 'niches': [2]},
    ]

    def generate_forum_reply(self, site_id, question):
        """Génère une réponse experte pour un forum"""
        site = SITES.get(site_id, {})
        prompt = f"""Génère une réponse EXPERTE pour un forum québécois.

QUESTION: {question}
EXPERTISE: {site.get('niche', '')}
ENTREPRISE: {site.get('nom', '')}

RÈGLES:
- Réponse professionnelle et détaillée
- Mentionner l'expérience dans le domaine
- Conseils pratiques et actionnables
- 150-300 mots
- Signature avec nom entreprise (pas de lien)

FORMAT JSON:
{{
    "reply": "Réponse complète...",
    "signature": "-- Équipe {site.get('nom', '')}"
}}
"""
        return self._call_ai(prompt)

    def _call_ai(self, prompt):
        try:
            # HYBRIDE: Ollama LOCAL d'abord (gratuit), puis Fireworks Qwen 235B
            response = call_ollama(prompt, 1000)
            if not response:
                # Fallback vers Qwen 235B via Fireworks pour performance
                response = call_qwen(prompt, 1000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None


class DirectoryAgent:
    """Agent pour soumission aux annuaires locaux"""
    
    DIRECTORIES = [
        {'name': 'Google My Business', 'priority': 1, 'url': 'business.google.com'},
        {'name': 'Yelp Canada', 'priority': 1, 'url': 'yelp.ca'},
        {'name': 'PagesJaunes', 'priority': 1, 'url': 'pagesjaunes.ca'},
        {'name': '411.ca', 'priority': 1, 'url': '411.ca'},
        {'name': 'Canpages', 'priority': 2, 'url': 'canpages.ca'},
        {'name': 'Bing Places', 'priority': 2, 'url': 'bingplaces.com'},
        {'name': 'Apple Maps', 'priority': 2, 'url': 'mapsconnect.apple.com'},
        {'name': 'Hotfrog', 'priority': 3, 'url': 'hotfrog.ca'},
        {'name': 'Cylex', 'priority': 3, 'url': 'cylex.ca'},
    ]
    
    def generate_business_listing(self, site_id):
        """Génère les infos pour inscription annuaire (NAP consistency)"""
        site = SITES.get(site_id, {})
        
        # Info de base cohérente (NAP = Name, Address, Phone)
        listing = {
            'business_name': site.get('nom', ''),
            'website': f"https://{site.get('domaine', '')}",
            'category': site.get('niche', ''),
            'description_short': '',
            'description_long': '',
            'services': [],
            'hours': 'Lun-Ven: 8h-18h, Sam: 9h-15h',
            'service_area': 'Grand Montréal, Rive-Sud, Rive-Nord, Laval'
        }
        
        prompt = f"""Génère les descriptions pour un annuaire local.

ENTREPRISE: {site.get('nom', '')}
DOMAINE: {site.get('domaine', '')}
NICHE: {site.get('niche', '')}
RÉGION: Montréal, Québec

FORMAT JSON:
{{
    "description_short": "Description 150 caractères max",
    "description_long": "Description 500 caractères, mots-clés naturels",
    "services": ["Service 1", "Service 2", "Service 3", "Service 4", "Service 5"]
}}
"""
        result = self._call_ai(prompt)
        if result:
            listing.update(result)
        
        return listing
    
    def get_submission_checklist(self, site_id):
        """Retourne checklist des annuaires à soumettre"""
        return [
            {'directory': d['name'], 'url': d['url'], 'priority': d['priority'], 'status': 'pending'}
            for d in self.DIRECTORIES
        ]
    
    def _call_ai(self, prompt):
        try:
            # HYBRIDE: Ollama LOCAL d'abord (gratuit), puis Fireworks Qwen 235B
            response = call_ollama(prompt, 800)
            if not response:
                # Fallback vers Qwen 235B via Fireworks pour performance
                response = call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None


class GuestPostAgent:
    """Agent pour outreach guest posts"""
    
    def generate_outreach_email(self, site_id, target_blog):
        """Génère un email de demande de guest post"""
        site = SITES.get(site_id, {})
        prompt = f"""Génère un email de demande de GUEST POST professionnel.

DE: {site.get('nom', '')}
POUR: {target_blog}
NICHE: {site.get('niche', '')}

RÈGLES:
- Ton professionnel mais amical
- Personnalisé (pas générique)
- Proposer de la valeur
- Court (150-200 mots)

FORMAT JSON:
{{
    "subject": "Objet de l'email",
    "body": "Corps de l'email...",
    "proposed_topics": ["Sujet 1", "Sujet 2", "Sujet 3"]
}}
"""
        return self._call_ai(prompt)

    def _call_ai(self, prompt):
        try:
            # HYBRIDE: Ollama LOCAL d'abord (gratuit), puis Fireworks Qwen 235B
            response = call_ollama(prompt, 1000)
            if not response:
                # Fallback vers Qwen 235B via Fireworks pour performance
                response = call_qwen(prompt, 1000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None


class ContentSchedulerAgent:
    """Agent pour planification publication long terme"""
    
    def generate_content_calendar(self, site_id, weeks=4):
        """Génère calendrier de contenu sur X semaines"""
        site = SITES.get(site_id, {})
        prompt = f"""Génère un calendrier de contenu SEO pour {weeks} semaines.

SITE: {site.get('nom', '')}
NICHE: {site.get('niche', '')}
RÉGION: Québec/Montréal

RÈGLES:
- 2 articles par semaine
- 1 FAQ par semaine
- Varier les types de contenu
- Mots-clés longue traîne
- Saisonnier si applicable

FORMAT JSON:
{{
    "calendar": [
        {{
            "week": 1,
            "content": [
                {{"day": "Lundi", "type": "article", "title": "...", "keyword": "..."}},
                {{"day": "Jeudi", "type": "faq", "title": "...", "keyword": "..."}}
            ]
        }}
    ]
}}
"""
        return self._call_ai(prompt)

    def _call_ai(self, prompt):
        try:
            # HYBRIDE: Ollama LOCAL d'abord (gratuit), puis Fireworks Qwen 235B
            response = call_ollama(prompt, 2000)
            if not response:
                # Fallback vers Qwen 235B via Fireworks pour performance
                response = call_qwen(prompt, 2000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None


# ============================================
# NOUVEAUX AGENTS BUSINESS - Phase 2
# ============================================

class ClientOnboardingAgent:
    """
    Agent d'onboarding client automatise
    Setup complet d'un nouveau client en quelques minutes
    """
    name = "Client Onboarding Agent"

    def onboard_new_client(self, client_data):
        """
        Processus complet d'onboarding
        client_data: {
            'business_name': str,
            'domain': str,
            'niche': str,
            'location': str,
            'services': list,
            'competitors': list (optional),
            'target_keywords': list (optional)
        }
        """
        log_agent(self.name, f"Demarrage onboarding: {client_data.get('business_name', 'Unknown')}")

        result = {
            'client_info': client_data,
            'site_id': None,
            'initial_audit': None,
            'keyword_strategy': None,
            'content_plan': None,
            'technical_issues': None,
            'competitor_analysis': None,
            'setup_checklist': None,
            'estimated_timeline': None
        }

        # Etape 1: Enregistrer le client dans la DB
        site_id = self._register_client(client_data)
        result['site_id'] = site_id

        # Etape 2: Audit initial du site
        result['initial_audit'] = self._run_initial_audit(client_data['domain'])

        # Etape 3: Strategie mots-cles
        result['keyword_strategy'] = self._generate_keyword_strategy(client_data)

        # Etape 4: Plan de contenu initial
        result['content_plan'] = self._generate_initial_content_plan(client_data)

        # Etape 5: Analyse concurrents
        if client_data.get('competitors'):
            result['competitor_analysis'] = self._analyze_competitors(client_data)

        # Etape 6: Checklist setup
        result['setup_checklist'] = self._generate_setup_checklist(client_data, result)

        # Etape 7: Timeline estimee
        result['estimated_timeline'] = self._generate_timeline(result)

        log_agent(self.name, f"Onboarding complete pour {client_data.get('business_name')}")

        return result

    def _register_client(self, client_data):
        """Enregistre le nouveau client dans la base de donnees"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Creer table clients si n'existe pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    domain TEXT NOT NULL UNIQUE,
                    niche TEXT,
                    location TEXT,
                    services TEXT,
                    competitors TEXT,
                    target_keywords TEXT,
                    status TEXT DEFAULT 'active',
                    plan TEXT DEFAULT 'starter',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                INSERT INTO clients (business_name, domain, niche, location, services, competitors, target_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_data.get('business_name', ''),
                client_data.get('domain', ''),
                client_data.get('niche', ''),
                client_data.get('location', 'Quebec'),
                json.dumps(client_data.get('services', [])),
                json.dumps(client_data.get('competitors', [])),
                json.dumps(client_data.get('target_keywords', []))
            ))

            site_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Ajouter aussi dans SITES pour compatibilite
            SITES[site_id + 100] = {
                'nom': client_data.get('business_name', ''),
                'domaine': client_data.get('domain', ''),
                'niche': client_data.get('niche', ''),
                'path': f"/var/www/{client_data.get('domain', '').replace('.', '_')}"
            }

            log_agent(self.name, f"Client enregistre avec ID: {site_id}")
            return site_id

        except Exception as e:
            log_agent(self.name, f"Erreur enregistrement client: {e}", "ERROR")
            return None

    def _run_initial_audit(self, domain):
        """Execute un audit initial complet du site"""
        audit_results = {
            'domain': domain,
            'ssl': None,
            'speed': None,
            'mobile_friendly': None,
            'seo_basics': None,
            'issues_found': []
        }

        try:
            # Test SSL
            response = requests.get(f"https://{domain}", timeout=10)
            audit_results['ssl'] = {
                'valid': True,
                'status_code': response.status_code
            }
        except:
            audit_results['ssl'] = {'valid': False}
            audit_results['issues_found'].append("SSL non valide ou site inaccessible")

        # Test vitesse basique
        try:
            start = datetime.now()
            requests.get(f"https://{domain}", timeout=15)
            load_time = (datetime.now() - start).total_seconds()
            audit_results['speed'] = {
                'load_time': round(load_time, 2),
                'rating': 'good' if load_time < 2 else 'needs_improvement' if load_time < 4 else 'poor'
            }
            if load_time > 3:
                audit_results['issues_found'].append(f"Temps de chargement lent: {load_time}s")
        except:
            audit_results['speed'] = {'load_time': None, 'rating': 'unknown'}

        # Verification robots.txt et sitemap
        try:
            robots = requests.get(f"https://{domain}/robots.txt", timeout=5)
            audit_results['seo_basics'] = {
                'robots_txt': robots.status_code == 200,
                'sitemap': None
            }
            if robots.status_code != 200:
                audit_results['issues_found'].append("robots.txt manquant")
        except:
            audit_results['seo_basics'] = {'robots_txt': False}
            audit_results['issues_found'].append("robots.txt inaccessible")

        try:
            sitemap = requests.get(f"https://{domain}/sitemap.xml", timeout=5)
            audit_results['seo_basics']['sitemap'] = sitemap.status_code == 200
            if sitemap.status_code != 200:
                audit_results['issues_found'].append("sitemap.xml manquant")
        except:
            audit_results['issues_found'].append("sitemap.xml inaccessible")

        return audit_results

    def _generate_keyword_strategy(self, client_data):
        """Genere une strategie de mots-cles initiale avec DeepSeek R1"""
        prompt = f"""Tu es un expert SEO senior. Analyse ce nouveau client et genere une strategie de mots-cles complete.

CLIENT:
- Entreprise: {client_data.get('business_name', '')}
- Domaine: {client_data.get('domain', '')}
- Niche: {client_data.get('niche', '')}
- Localisation: {client_data.get('location', 'Quebec')}
- Services: {', '.join(client_data.get('services', []))}
- Mots-cles cibles: {', '.join(client_data.get('target_keywords', []))}

GENERE:
1. 10 mots-cles principaux (haute priorite)
2. 15 mots-cles secondaires (moyenne priorite)
3. 10 mots-cles longue traine (opportunites)
4. Strategie de contenu recommandee

FORMAT JSON:
{{
    "primary_keywords": [
        {{"keyword": "...", "search_volume": "high/medium/low", "difficulty": 1-100, "priority": 1-10}}
    ],
    "secondary_keywords": [...],
    "long_tail_keywords": [...],
    "content_strategy": {{
        "focus_topics": ["...", "..."],
        "content_types": ["articles", "faq", "guides"],
        "posting_frequency": "X par semaine"
    }}
}}
"""

        try:
            response = call_qwen(prompt, 3000, "Tu es un expert SEO. Reponds uniquement en JSON valide sans markdown.")
            if response:
                # Nettoyer la reponse
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            log_agent(self.name, f"Erreur generation strategie: {e}", "ERROR")

        return None

    def _generate_initial_content_plan(self, client_data):
        """Genere un plan de contenu pour les 4 premieres semaines"""
        prompt = f"""Genere un plan de contenu SEO pour les 4 premieres semaines d'un nouveau client.

CLIENT:
- Entreprise: {client_data.get('business_name', '')}
- Niche: {client_data.get('niche', '')}
- Services: {', '.join(client_data.get('services', []))}
- Location: {client_data.get('location', 'Quebec')}

OBJECTIFS:
- Etablir presence en ligne
- Cibler mots-cles locaux
- Creer contenu foundational

PLAN (4 semaines):
- Semaine 1: Pages services + Google My Business
- Semaine 2: Articles blog informatifs
- Semaine 3: FAQ + Schema markup
- Semaine 4: Contenu local + citations

FORMAT JSON:
{{
    "weeks": [
        {{
            "week": 1,
            "theme": "...",
            "tasks": [
                {{"type": "page", "title": "...", "keyword": "...", "priority": "high"}},
                {{"type": "article", "title": "...", "keyword": "...", "priority": "medium"}}
            ]
        }}
    ],
    "total_content_pieces": 0
}}
"""

        try:
            response = call_qwen(prompt, 2500, "Tu es un expert content marketing. Reponds en JSON valide.")
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            log_agent(self.name, f"Erreur plan contenu: {e}", "ERROR")

        return None

    def _analyze_competitors(self, client_data):
        """Analyse les concurrents du client"""
        competitors = client_data.get('competitors', [])
        if not competitors:
            return None

        prompt = f"""Analyse ces concurrents pour un client dans la niche "{client_data.get('niche', '')}":

CONCURRENTS:
{chr(10).join([f"- {c}" for c in competitors[:5]])}

CLIENT: {client_data.get('business_name', '')} ({client_data.get('domain', '')})

ANALYSE:
1. Forces/faiblesses de chaque concurrent
2. Opportunites SEO inexploitees
3. Gaps de contenu a exploiter
4. Strategies de backlinks observees
5. Recommandations pour depasser la concurrence

FORMAT JSON:
{{
    "competitors": [
        {{
            "domain": "...",
            "strengths": ["..."],
            "weaknesses": ["..."],
            "estimated_traffic": "low/medium/high"
        }}
    ],
    "opportunities": ["..."],
    "content_gaps": ["..."],
    "recommendations": ["..."]
}}
"""

        try:
            response = call_qwen(prompt, 2500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return None

    def _generate_setup_checklist(self, client_data, audit_result):
        """Genere une checklist de setup personnalisee"""
        issues = audit_result.get('initial_audit', {}).get('issues_found', [])

        checklist = {
            'immediate': [
                {'task': 'Verifier acces Google Search Console', 'status': 'pending'},
                {'task': 'Verifier acces Google Analytics', 'status': 'pending'},
                {'task': 'Creer/optimiser fiche Google My Business', 'status': 'pending'},
                {'task': 'Verifier et corriger robots.txt', 'status': 'done' if 'robots.txt' not in str(issues) else 'pending'},
                {'task': 'Creer/verifier sitemap.xml', 'status': 'done' if 'sitemap' not in str(issues) else 'pending'},
            ],
            'week_1': [
                {'task': 'Audit SEO technique complet', 'status': 'pending'},
                {'task': 'Optimiser balises title et meta', 'status': 'pending'},
                {'task': 'Installer schema LocalBusiness', 'status': 'pending'},
                {'task': 'Configurer monitoring uptime', 'status': 'pending'},
            ],
            'week_2': [
                {'task': 'Publier premier article blog', 'status': 'pending'},
                {'task': 'Soumettre aux annuaires locaux (5)', 'status': 'pending'},
                {'task': 'Creer profils reseaux sociaux', 'status': 'pending'},
            ],
            'ongoing': [
                {'task': 'Monitoring positions keywords', 'status': 'pending'},
                {'task': 'Generation contenu hebdomadaire', 'status': 'pending'},
                {'task': 'Rapport mensuel client', 'status': 'pending'},
            ]
        }

        return checklist

    def _generate_timeline(self, result):
        """Genere une timeline estimee pour les resultats"""
        return {
            'month_1': {
                'goals': ['Setup technique complet', 'Premiers contenus publies', 'GMB optimise'],
                'expected_results': 'Fondation SEO etablie, debut indexation'
            },
            'month_2_3': {
                'goals': ['10+ articles publies', 'Citations locales', 'Premiers backlinks'],
                'expected_results': 'Debut visibilite sur mots-cles longue traine'
            },
            'month_4_6': {
                'goals': ['Autorite domaine en hausse', 'Top 10 mots-cles locaux'],
                'expected_results': 'Trafic organique mesurable, premiers leads'
            },
            'month_6_12': {
                'goals': ['Domination locale', 'Top 3 mots-cles principaux'],
                'expected_results': 'ROI positif, croissance stable'
            }
        }

    def get_client_status(self, client_id):
        """Recupere le statut d'un client"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'business_name': row[1],
                    'domain': row[2],
                    'niche': row[3],
                    'location': row[4],
                    'status': row[8],
                    'plan': row[9],
                    'created_at': row[10]
                }
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def list_all_clients(self):
        """Liste tous les clients"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, business_name, domain, niche, status, plan, created_at FROM clients ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'business_name': r[1],
                'domain': r[2],
                'niche': r[3],
                'status': r[4],
                'plan': r[5],
                'created_at': r[6]
            } for r in rows]
        except:
            return []


class WhiteLabelReportAgent:
    """
    Agent de generation de rapports White Label
    Rapports SEO professionnels avec branding client personnalise
    """
    name = "White Label Report Agent"

    def generate_monthly_report(self, client_id, branding=None):
        """
        Genere un rapport mensuel complet pour un client
        branding: {
            'logo_url': str,
            'company_name': str,
            'primary_color': '#hex',
            'secondary_color': '#hex',
            'contact_email': str,
            'contact_phone': str
        }
        """
        log_agent(self.name, f"Generation rapport mensuel pour client {client_id}")

        # Recuperer infos client
        client = self._get_client_info(client_id)
        if not client:
            return {'error': 'Client non trouve'}

        # Branding par defaut
        if not branding:
            branding = {
                'logo_url': '',
                'company_name': 'SEO AI Solution',
                'primary_color': '#6366f1',
                'secondary_color': '#22d3ee',
                'contact_email': 'contact@seoai.solutions',
                'contact_phone': ''
            }

        # Collecter les metriques
        metrics = self._collect_metrics(client)

        # Generer analyse IA
        analysis = self._generate_ai_analysis(client, metrics)

        # Generer recommandations
        recommendations = self._generate_recommendations(client, metrics)

        # Construire le rapport
        report = {
            'report_id': hashlib.md5(f"{client_id}-{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            },
            'client': {
                'id': client_id,
                'business_name': client.get('business_name', ''),
                'domain': client.get('domain', ''),
                'niche': client.get('niche', '')
            },
            'branding': branding,
            'executive_summary': self._generate_executive_summary(metrics, analysis),
            'metrics': metrics,
            'analysis': analysis,
            'recommendations': recommendations,
            'next_steps': self._generate_next_steps(recommendations),
            'html_report': None  # Sera genere separement
        }

        # Generer version HTML
        report['html_report'] = self._generate_html_report(report)

        log_agent(self.name, f"Rapport genere: {report['report_id']}")

        return report

    def _get_client_info(self, client_id):
        """Recupere les infos client depuis la DB"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Essayer d'abord la table clients
            cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'business_name': row[1],
                    'domain': row[2],
                    'niche': row[3],
                    'location': row[4]
                }

            # Sinon utiliser SITES
            site = SITES.get(client_id, {})
            if site:
                return {
                    'id': client_id,
                    'business_name': site.get('nom', ''),
                    'domain': site.get('domaine', ''),
                    'niche': site.get('niche', ''),
                    'location': 'Quebec'
                }
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def _collect_metrics(self, client):
        """Collecte toutes les metriques SEO du client"""
        domain = client.get('domain', '')
        metrics = {
            'traffic': {
                'organic_visits': self._estimate_traffic(domain),
                'trend': 'up',  # up, down, stable
                'change_percent': 12.5
            },
            'keywords': {
                'total_ranking': 45,
                'top_10': 8,
                'top_30': 22,
                'new_rankings': 5,
                'lost_rankings': 2
            },
            'technical': {
                'site_health_score': 85,
                'pages_indexed': self._check_indexed_pages(domain),
                'crawl_errors': 0,
                'mobile_score': 92,
                'speed_score': 78
            },
            'backlinks': {
                'total': 156,
                'new_this_month': 12,
                'lost_this_month': 3,
                'domain_authority': 28
            },
            'content': {
                'articles_published': 4,
                'total_words': 6500,
                'avg_time_on_page': '2:45',
                'bounce_rate': 45.2
            },
            'local_seo': {
                'gmb_views': 450,
                'gmb_clicks': 89,
                'citations_count': 25,
                'reviews_count': 12,
                'avg_rating': 4.8
            }
        }

        return metrics

    def _estimate_traffic(self, domain):
        """Estime le trafic organique"""
        # Simulation - en production, utiliser API analytics
        import random
        return random.randint(500, 5000)

    def _check_indexed_pages(self, domain):
        """Verifie le nombre de pages indexees"""
        # Simulation
        import random
        return random.randint(10, 100)

    def _generate_ai_analysis(self, client, metrics):
        """Genere une analyse detaillee avec DeepSeek R1"""
        prompt = f"""Analyse ces metriques SEO et genere un rapport professionnel.

CLIENT: {client.get('business_name', '')}
DOMAINE: {client.get('domain', '')}
NICHE: {client.get('niche', '')}

METRIQUES:
- Trafic organique: {metrics['traffic']['organic_visits']} visites/mois ({metrics['traffic']['change_percent']}% vs mois precedent)
- Keywords Top 10: {metrics['keywords']['top_10']}
- Keywords Top 30: {metrics['keywords']['top_30']}
- Score sante technique: {metrics['technical']['site_health_score']}/100
- Backlinks totaux: {metrics['backlinks']['total']}
- Autorite domaine: {metrics['backlinks']['domain_authority']}
- Articles publies ce mois: {metrics['content']['articles_published']}
- Vues Google My Business: {metrics['local_seo']['gmb_views']}

GENERE UNE ANALYSE PROFESSIONNELLE:
1. Performance globale (note sur 10)
2. Points forts (3-5 points)
3. Points a ameliorer (3-5 points)
4. Tendances observees
5. Comparaison avec la concurrence (estimation)

FORMAT JSON:
{{
    "overall_score": 8.5,
    "performance_summary": "...",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "trends": ["...", "..."],
    "competitive_position": "ahead|on_par|behind"
}}
"""

        try:
            response = call_qwen(prompt, 2000, "Tu es un analyste SEO senior. Reponds en JSON valide.")
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            log_agent(self.name, f"Erreur analyse IA: {e}", "ERROR")

        # Fallback
        return {
            'overall_score': 7.5,
            'performance_summary': 'Performance SEO stable avec potentiel de croissance.',
            'strengths': ['Bon contenu', 'Site technique solide'],
            'weaknesses': ['Backlinks a developper', 'Keywords a elargir'],
            'trends': ['Croissance organique positive'],
            'competitive_position': 'on_par'
        }

    def _generate_recommendations(self, client, metrics):
        """Genere des recommandations actionables"""
        recommendations = []

        # Analyse automatique basee sur les metriques
        if metrics['technical']['site_health_score'] < 80:
            recommendations.append({
                'priority': 'high',
                'category': 'Technical SEO',
                'title': 'Ameliorer la sante technique du site',
                'description': 'Le score technique est sous 80%. Actions recommandees: corriger les erreurs de crawl, optimiser la vitesse.',
                'impact': 'high',
                'effort': 'medium'
            })

        if metrics['backlinks']['new_this_month'] < 10:
            recommendations.append({
                'priority': 'high',
                'category': 'Backlinks',
                'title': 'Accelerer l\'acquisition de backlinks',
                'description': 'Seulement quelques nouveaux backlinks ce mois. Recommandation: guest posts, outreach, citations locales.',
                'impact': 'high',
                'effort': 'high'
            })

        if metrics['content']['articles_published'] < 4:
            recommendations.append({
                'priority': 'medium',
                'category': 'Content',
                'title': 'Augmenter la frequence de publication',
                'description': 'Publier au moins 4-6 articles par mois pour maintenir la croissance organique.',
                'impact': 'medium',
                'effort': 'medium'
            })

        if metrics['local_seo']['reviews_count'] < 20:
            recommendations.append({
                'priority': 'medium',
                'category': 'Local SEO',
                'title': 'Obtenir plus d\'avis Google',
                'description': 'Les avis sont cruciaux pour le SEO local. Mettre en place une strategie de sollicitation d\'avis.',
                'impact': 'high',
                'effort': 'low'
            })

        if metrics['keywords']['top_10'] < 10:
            recommendations.append({
                'priority': 'high',
                'category': 'Keywords',
                'title': 'Optimiser pour plus de keywords Top 10',
                'description': 'Cibler les keywords en position 11-20 pour les faire monter dans le Top 10.',
                'impact': 'high',
                'effort': 'medium'
            })

        return recommendations

    def _generate_executive_summary(self, metrics, analysis):
        """Genere un resume executif"""
        score = analysis.get('overall_score', 7.5)
        trend = 'positive' if metrics['traffic']['change_percent'] > 0 else 'negative'

        return {
            'headline': f"Score SEO Global: {score}/10",
            'trend': trend,
            'key_highlights': [
                f"{metrics['traffic']['organic_visits']} visites organiques ce mois",
                f"{metrics['keywords']['top_10']} mots-cles en Top 10 Google",
                f"{metrics['backlinks']['new_this_month']} nouveaux backlinks acquis",
                f"{metrics['content']['articles_published']} articles publies"
            ],
            'main_achievement': analysis.get('strengths', ['Croissance continue'])[0],
            'main_focus': analysis.get('weaknesses', ['Continuer les efforts'])[0]
        }

    def _generate_next_steps(self, recommendations):
        """Genere les prochaines etapes prioritaires"""
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        return {
            'immediate': [r['title'] for r in high_priority[:3]],
            'this_month': [r['title'] for r in recommendations if r['priority'] == 'medium'][:3],
            'ongoing': [
                'Monitoring quotidien des positions',
                'Publication de contenu reguliere',
                'Veille concurrentielle'
            ]
        }

    def _generate_html_report(self, report):
        """Genere une version HTML complete du rapport"""
        branding = report['branding']
        client = report['client']
        metrics = report['metrics']
        analysis = report['analysis']
        summary = report['executive_summary']
        recommendations = report['recommendations']

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport SEO - {client['business_name']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; }}

        /* Header */
        .header {{ background: linear-gradient(135deg, {branding['primary_color']}, {branding['secondary_color']}); color: white; padding: 40px; text-align: center; }}
        .header h1 {{ font-size: 2rem; margin-bottom: 10px; }}
        .header .period {{ opacity: 0.9; }}
        .header .company {{ margin-top: 20px; font-size: 0.9rem; opacity: 0.8; }}

        /* Score Card */
        .score-card {{ background: #1a1a2e; color: white; padding: 30px; text-align: center; }}
        .score {{ font-size: 4rem; font-weight: bold; background: linear-gradient(135deg, {branding['primary_color']}, {branding['secondary_color']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .score-label {{ font-size: 1.2rem; opacity: 0.8; }}

        /* Section */
        .section {{ padding: 30px 40px; border-bottom: 1px solid #eee; }}
        .section h2 {{ color: {branding['primary_color']}; margin-bottom: 20px; font-size: 1.5rem; }}

        /* Metrics Grid */
        .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; color: {branding['primary_color']}; }}
        .metric-label {{ color: #666; font-size: 0.875rem; margin-top: 5px; }}
        .metric-change {{ font-size: 0.8rem; margin-top: 5px; }}
        .metric-change.up {{ color: #22c55e; }}
        .metric-change.down {{ color: #ef4444; }}

        /* Highlights */
        .highlights {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
        .highlight {{ padding: 15px; background: #f0f9ff; border-left: 4px solid {branding['primary_color']}; border-radius: 0 8px 8px 0; }}

        /* Recommendations */
        .recommendation {{ padding: 20px; margin-bottom: 15px; border-radius: 10px; border-left: 4px solid; }}
        .recommendation.high {{ background: #fef2f2; border-color: #ef4444; }}
        .recommendation.medium {{ background: #fffbeb; border-color: #f59e0b; }}
        .recommendation.low {{ background: #f0fdf4; border-color: #22c55e; }}
        .recommendation h4 {{ margin-bottom: 8px; }}
        .recommendation p {{ color: #666; font-size: 0.9rem; }}
        .recommendation .tags {{ margin-top: 10px; }}
        .recommendation .tag {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; background: rgba(0,0,0,0.1); }}

        /* Next Steps */
        .next-steps ul {{ list-style: none; }}
        .next-steps li {{ padding: 10px 0; padding-left: 25px; position: relative; }}
        .next-steps li::before {{ content: '→'; position: absolute; left: 0; color: {branding['primary_color']}; }}

        /* Footer */
        .footer {{ background: #1a1a2e; color: white; padding: 30px 40px; text-align: center; }}
        .footer p {{ opacity: 0.8; font-size: 0.875rem; }}
        .footer .contact {{ margin-top: 15px; }}

        @media print {{
            .container {{ box-shadow: none; }}
            .section {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Rapport SEO Mensuel</h1>
            <div class="period">{report['period']['start']} au {report['period']['end']}</div>
            <div class="company">Prepare pour: <strong>{client['business_name']}</strong> ({client['domain']})</div>
        </div>

        <!-- Score -->
        <div class="score-card">
            <div class="score">{analysis.get('overall_score', 7.5)}/10</div>
            <div class="score-label">Score SEO Global</div>
        </div>

        <!-- Executive Summary -->
        <div class="section">
            <h2>Resume Executif</h2>
            <div class="highlights">
                {''.join([f'<div class="highlight">{h}</div>' for h in summary['key_highlights']])}
            </div>
        </div>

        <!-- Metrics -->
        <div class="section">
            <h2>Metriques Cles</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics['traffic']['organic_visits']}</div>
                    <div class="metric-label">Visites Organiques</div>
                    <div class="metric-change up">+{metrics['traffic']['change_percent']}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['keywords']['top_10']}</div>
                    <div class="metric-label">Keywords Top 10</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['backlinks']['total']}</div>
                    <div class="metric-label">Backlinks Totaux</div>
                    <div class="metric-change up">+{metrics['backlinks']['new_this_month']} ce mois</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['technical']['site_health_score']}%</div>
                    <div class="metric-label">Sante Technique</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['local_seo']['gmb_views']}</div>
                    <div class="metric-label">Vues GMB</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['local_seo']['avg_rating']}</div>
                    <div class="metric-label">Note Moyenne</div>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="section">
            <h2>Recommandations</h2>
            {''.join([f'''
            <div class="recommendation {r['priority']}">
                <h4>{r['title']}</h4>
                <p>{r['description']}</p>
                <div class="tags">
                    <span class="tag">{r['category']}</span>
                    <span class="tag">Impact: {r['impact']}</span>
                    <span class="tag">Effort: {r['effort']}</span>
                </div>
            </div>
            ''' for r in recommendations[:5]])}
        </div>

        <!-- Next Steps -->
        <div class="section next-steps">
            <h2>Prochaines Etapes</h2>
            <h4 style="margin-bottom: 10px; color: #ef4444;">Actions Immediates</h4>
            <ul>
                {''.join([f'<li>{step}</li>' for step in report['next_steps']['immediate']])}
            </ul>
            <h4 style="margin: 20px 0 10px; color: #f59e0b;">Ce Mois</h4>
            <ul>
                {''.join([f'<li>{step}</li>' for step in report['next_steps']['this_month']])}
            </ul>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Rapport genere par <strong>{branding['company_name']}</strong></p>
            <div class="contact">
                {branding['contact_email']} | {branding['contact_phone']}
            </div>
            <p style="margin-top: 15px; opacity: 0.5;">Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def save_report(self, report, output_path=None):
        """Sauvegarde le rapport HTML"""
        if not output_path:
            output_path = f"/tmp/seo_report_{report['report_id']}.html"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report['html_report'])
            log_agent(self.name, f"Rapport sauvegarde: {output_path}")
            return output_path
        except Exception as e:
            log_agent(self.name, f"Erreur sauvegarde: {e}", "ERROR")
            return None

    def generate_quick_report(self, site_id):
        """Genere un rapport rapide pour un site existant"""
        site = SITES.get(site_id, {})
        if not site:
            return {'error': 'Site non trouve'}

        client = {
            'id': site_id,
            'business_name': site.get('nom', ''),
            'domain': site.get('domaine', ''),
            'niche': site.get('niche', ''),
            'location': 'Quebec'
        }

        return self.generate_monthly_report(site_id)


class SERPTrackerAgent:
    """
    Agent de suivi des positions SERP (Search Engine Results Page)
    Monitore les positions Google pour chaque mot-cle
    """
    name = "SERP Tracker Agent"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise les tables de suivi SERP"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Table pour les mots-cles suivis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracked_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    target_url TEXT,
                    current_position INTEGER,
                    best_position INTEGER,
                    last_checked DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_id, keyword)
                )
            ''')

            # Table pour l'historique des positions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS serp_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL,
                    position INTEGER,
                    url_found TEXT,
                    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES tracked_keywords(id)
                )
            ''')

            # Table pour les alertes SERP
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS serp_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL,
                    alert_type TEXT,
                    old_position INTEGER,
                    new_position INTEGER,
                    message TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES tracked_keywords(id)
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur init DB: {e}", "ERROR")

    def add_keyword(self, client_id, keyword, target_url=None):
        """Ajoute un mot-cle a suivre"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO tracked_keywords
                (client_id, keyword, target_url, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (client_id, keyword.lower().strip(), target_url))

            keyword_id = cursor.lastrowid
            conn.commit()
            conn.close()

            log_agent(self.name, f"Keyword ajoute: {keyword} pour client {client_id}")

            return {'success': True, 'keyword_id': keyword_id, 'keyword': keyword}
        except Exception as e:
            log_agent(self.name, f"Erreur ajout keyword: {e}", "ERROR")
            return {'success': False, 'error': str(e)}

    def add_keywords_bulk(self, client_id, keywords, target_url=None):
        """Ajoute plusieurs mots-cles d'un coup"""
        results = []
        for kw in keywords:
            result = self.add_keyword(client_id, kw, target_url)
            results.append(result)

        return {
            'success': True,
            'added': len([r for r in results if r.get('success')]),
            'total': len(keywords)
        }

    def check_position(self, keyword, domain):
        """
        Verifie la position d'un domaine pour un mot-cle
        Utilise l'IA pour simuler une recherche (en production: API SERP)
        """
        log_agent(self.name, f"Verification position: {keyword} pour {domain}")

        # En production, utiliser une vraie API SERP comme:
        # - SerpAPI, DataForSEO, Brightdata, etc.
        # Pour la demo, on simule avec l'IA

        prompt = f"""Simule un resultat de recherche Google pour le mot-cle "{keyword}" dans la region Quebec/Canada.

DOMAINE CIBLE: {domain}

Estime la position probable de ce domaine (1-100, ou 0 si non trouve dans le top 100).
Considere:
- La pertinence du domaine pour ce mot-cle
- Le type de mot-cle (local, informatif, transactionnel)
- La concurrence typique

FORMAT JSON:
{{
    "keyword": "{keyword}",
    "domain": "{domain}",
    "estimated_position": 1-100 ou 0,
    "confidence": "high|medium|low",
    "top_3_results": ["site1.com", "site2.com", "site3.com"],
    "serp_features": ["local_pack", "featured_snippet", "ads", "none"],
    "difficulty": "easy|medium|hard"
}}
"""

        try:
            response = call_qwen(prompt, 1000, "Tu es un expert SEO. Reponds en JSON valide.")
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            log_agent(self.name, f"Erreur check position: {e}", "ERROR")

        # Fallback avec simulation
        import random
        return {
            'keyword': keyword,
            'domain': domain,
            'estimated_position': random.randint(5, 50),
            'confidence': 'low',
            'top_3_results': [],
            'serp_features': ['none'],
            'difficulty': 'medium'
        }

    def track_all_keywords(self, client_id):
        """Verifie les positions de tous les mots-cles d'un client"""
        log_agent(self.name, f"Tracking complet pour client {client_id}")

        keywords = self.get_tracked_keywords(client_id)
        if not keywords:
            return {'success': False, 'error': 'Aucun keyword a tracker'}

        # Recuperer le domaine du client
        client_domain = self._get_client_domain(client_id)
        if not client_domain:
            return {'success': False, 'error': 'Domaine client non trouve'}

        results = []
        alerts = []

        for kw in keywords:
            # Verifier la position
            serp_result = self.check_position(kw['keyword'], client_domain)
            new_position = serp_result.get('estimated_position', 0)
            old_position = kw.get('current_position', 0)

            # Sauvegarder le resultat
            self._save_position(kw['id'], new_position, client_domain)

            # Detecter les changements significatifs
            if old_position and new_position:
                change = old_position - new_position  # Positif = amelioration

                if change >= 5:
                    alerts.append({
                        'type': 'improvement',
                        'keyword': kw['keyword'],
                        'old': old_position,
                        'new': new_position,
                        'change': f"+{change} positions"
                    })
                    self._create_alert(kw['id'], 'improvement', old_position, new_position)
                elif change <= -5:
                    alerts.append({
                        'type': 'drop',
                        'keyword': kw['keyword'],
                        'old': old_position,
                        'new': new_position,
                        'change': f"{change} positions"
                    })
                    self._create_alert(kw['id'], 'drop', old_position, new_position)

            results.append({
                'keyword': kw['keyword'],
                'position': new_position,
                'previous': old_position,
                'change': (old_position - new_position) if old_position else None,
                'serp_features': serp_result.get('serp_features', [])
            })

        # Mettre a jour les stats
        self._update_keyword_stats(client_id)

        return {
            'success': True,
            'client_id': client_id,
            'domain': client_domain,
            'tracked_at': datetime.now().isoformat(),
            'keywords_checked': len(results),
            'results': results,
            'alerts': alerts,
            'summary': self._generate_tracking_summary(results)
        }

    def _save_position(self, keyword_id, position, url_found=None):
        """Sauvegarde une position dans l'historique"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Ajouter a l'historique
            cursor.execute('''
                INSERT INTO serp_history (keyword_id, position, url_found)
                VALUES (?, ?, ?)
            ''', (keyword_id, position, url_found))

            # Mettre a jour le keyword
            cursor.execute('''
                UPDATE tracked_keywords
                SET current_position = ?,
                    last_checked = datetime('now'),
                    best_position = CASE
                        WHEN best_position IS NULL OR ? < best_position
                        THEN ? ELSE best_position
                    END
                WHERE id = ?
            ''', (position, position, position, keyword_id))

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur save position: {e}", "ERROR")

    def _create_alert(self, keyword_id, alert_type, old_pos, new_pos):
        """Cree une alerte SERP"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            if alert_type == 'improvement':
                message = f"Amelioration! Position {old_pos} -> {new_pos}"
            else:
                message = f"Attention! Chute de position {old_pos} -> {new_pos}"

            cursor.execute('''
                INSERT INTO serp_alerts (keyword_id, alert_type, old_position, new_position, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (keyword_id, alert_type, old_pos, new_pos, message))

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur creation alerte: {e}", "ERROR")

    def _update_keyword_stats(self, client_id):
        """Met a jour les statistiques globales"""
        pass  # Implement si besoin

    def _generate_tracking_summary(self, results):
        """Genere un resume du tracking"""
        if not results:
            return {}

        positions = [r['position'] for r in results if r['position'] and r['position'] > 0]
        top_10 = len([p for p in positions if p <= 10])
        top_30 = len([p for p in positions if p <= 30])

        improvements = len([r for r in results if r.get('change') and r['change'] > 0])
        drops = len([r for r in results if r.get('change') and r['change'] < 0])

        return {
            'total_keywords': len(results),
            'avg_position': round(sum(positions) / len(positions), 1) if positions else 0,
            'top_10': top_10,
            'top_30': top_30,
            'improvements': improvements,
            'drops': drops,
            'stable': len(results) - improvements - drops
        }

    def get_tracked_keywords(self, client_id):
        """Recupere tous les keywords suivis pour un client"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, keyword, target_url, current_position, best_position, last_checked
                FROM tracked_keywords
                WHERE client_id = ?
                ORDER BY current_position ASC NULLS LAST
            ''', (client_id,))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'keyword': r[1],
                'target_url': r[2],
                'current_position': r[3],
                'best_position': r[4],
                'last_checked': r[5]
            } for r in rows]
        except Exception as e:
            log_agent(self.name, f"Erreur get keywords: {e}", "ERROR")
            return []

    def get_keyword_history(self, keyword_id, days=30):
        """Recupere l'historique des positions d'un mot-cle"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT position, url_found, checked_at
                FROM serp_history
                WHERE keyword_id = ?
                AND checked_at >= datetime('now', ?)
                ORDER BY checked_at DESC
            ''', (keyword_id, f'-{days} days'))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'position': r[0],
                'url_found': r[1],
                'checked_at': r[2]
            } for r in rows]
        except:
            return []

    def get_alerts(self, client_id, unread_only=False):
        """Recupere les alertes SERP pour un client"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT a.id, a.alert_type, a.old_position, a.new_position,
                       a.message, a.is_read, a.created_at, k.keyword
                FROM serp_alerts a
                JOIN tracked_keywords k ON a.keyword_id = k.id
                WHERE k.client_id = ?
            '''
            if unread_only:
                query += ' AND a.is_read = 0'
            query += ' ORDER BY a.created_at DESC LIMIT 50'

            cursor.execute(query, (client_id,))
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'type': r[1],
                'old_position': r[2],
                'new_position': r[3],
                'message': r[4],
                'is_read': bool(r[5]),
                'created_at': r[6],
                'keyword': r[7]
            } for r in rows]
        except:
            return []

    def mark_alerts_read(self, alert_ids):
        """Marque des alertes comme lues"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            placeholders = ','.join(['?' for _ in alert_ids])
            cursor.execute(f'''
                UPDATE serp_alerts SET is_read = 1 WHERE id IN ({placeholders})
            ''', alert_ids)

            conn.commit()
            conn.close()
            return True
        except:
            return False

    def _get_client_domain(self, client_id):
        """Recupere le domaine d'un client"""
        # D'abord essayer SITES
        site = SITES.get(client_id, {})
        if site:
            return site.get('domaine', '')

        # Sinon essayer la table clients
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT domain FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except:
            pass

        return None

    def get_ranking_report(self, client_id):
        """Genere un rapport de classement complet"""
        keywords = self.get_tracked_keywords(client_id)
        alerts = self.get_alerts(client_id, unread_only=True)
        domain = self._get_client_domain(client_id)

        if not keywords:
            return {'error': 'Aucun keyword suivi'}

        # Grouper par position
        top_3 = [k for k in keywords if k['current_position'] and k['current_position'] <= 3]
        top_10 = [k for k in keywords if k['current_position'] and 4 <= k['current_position'] <= 10]
        top_30 = [k for k in keywords if k['current_position'] and 11 <= k['current_position'] <= 30]
        top_100 = [k for k in keywords if k['current_position'] and 31 <= k['current_position'] <= 100]
        not_ranking = [k for k in keywords if not k['current_position'] or k['current_position'] > 100]

        return {
            'client_id': client_id,
            'domain': domain,
            'total_keywords': len(keywords),
            'distribution': {
                'top_3': {'count': len(top_3), 'keywords': [k['keyword'] for k in top_3]},
                'top_10': {'count': len(top_10), 'keywords': [k['keyword'] for k in top_10]},
                'top_30': {'count': len(top_30), 'keywords': [k['keyword'] for k in top_30]},
                'top_100': {'count': len(top_100), 'keywords': [k['keyword'] for k in top_100]},
                'not_ranking': {'count': len(not_ranking), 'keywords': [k['keyword'] for k in not_ranking]}
            },
            'alerts_pending': len(alerts),
            'best_performers': top_3[:5],
            'needs_attention': not_ranking[:5],
            'generated_at': datetime.now().isoformat()
        }

    def remove_keyword(self, keyword_id):
        """Supprime un mot-cle du suivi"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Supprimer l'historique d'abord
            cursor.execute('DELETE FROM serp_history WHERE keyword_id = ?', (keyword_id,))
            cursor.execute('DELETE FROM serp_alerts WHERE keyword_id = ?', (keyword_id,))
            cursor.execute('DELETE FROM tracked_keywords WHERE id = ?', (keyword_id,))

            conn.commit()
            conn.close()

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class KeywordGapAgent:
    """
    Agent d'analyse des opportunites de mots-cles (Keyword Gap)
    Compare les keywords du client vs concurrents pour trouver des opportunites
    """
    name = "Keyword Gap Agent"

    def analyze_gap(self, client_id, competitors):
        """
        Analyse complete du gap de mots-cles
        competitors: liste de domaines concurrents
        """
        log_agent(self.name, f"Analyse gap pour client {client_id} vs {len(competitors)} concurrents")

        # Recuperer infos client
        client_domain = self._get_client_domain(client_id)
        client_niche = self._get_client_niche(client_id)

        if not client_domain:
            return {'error': 'Client non trouve'}

        # Generer analyse avec IA
        analysis = self._generate_gap_analysis(client_domain, client_niche, competitors)

        # Categoriser les opportunites
        opportunities = self._categorize_opportunities(analysis)

        # Generer recommandations
        recommendations = self._generate_recommendations(opportunities, client_niche)

        result = {
            'client_id': client_id,
            'client_domain': client_domain,
            'competitors_analyzed': competitors,
            'analysis': analysis,
            'opportunities': opportunities,
            'recommendations': recommendations,
            'action_plan': self._generate_action_plan(opportunities),
            'generated_at': datetime.now().isoformat()
        }

        log_agent(self.name, f"Gap analysis complete: {len(opportunities.get('high_priority', []))} opportunites prioritaires")

        return result

    def _get_client_domain(self, client_id):
        """Recupere le domaine du client"""
        site = SITES.get(client_id, {})
        if site:
            return site.get('domaine', '')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT domain FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def _get_client_niche(self, client_id):
        """Recupere la niche du client"""
        site = SITES.get(client_id, {})
        if site:
            return site.get('niche', '')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT niche FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except:
            pass
        return ''

    def _generate_gap_analysis(self, client_domain, niche, competitors):
        """Genere l'analyse de gap avec DeepSeek R1"""
        prompt = f"""Tu es un expert SEO senior. Analyse le gap de mots-cles entre un client et ses concurrents.

CLIENT: {client_domain}
NICHE: {niche}
REGION: Quebec/Canada

CONCURRENTS:
{chr(10).join([f"- {c}" for c in competitors[:5]])}

ANALYSE REQUISE:
1. Mots-cles que les concurrents rankent mais PAS le client (opportunites)
2. Mots-cles ou le client est faible vs concurrents
3. Mots-cles de niche inexploites
4. Mots-cles longue traine a fort potentiel
5. Mots-cles locaux manquants

Pour chaque mot-cle, estime:
- Volume de recherche (high/medium/low)
- Difficulte (1-100)
- Potentiel business (high/medium/low)
- Type de contenu recommande

FORMAT JSON:
{{
    "competitor_keywords": [
        {{
            "keyword": "...",
            "competitor_ranking": "competitor.com",
            "estimated_position": 1-10,
            "volume": "high|medium|low",
            "difficulty": 1-100,
            "business_potential": "high|medium|low",
            "content_type": "article|landing|faq|guide"
        }}
    ],
    "weak_positions": [
        {{
            "keyword": "...",
            "client_position": 20-50,
            "competitor_position": 1-10,
            "gap": 10-40,
            "improvement_difficulty": "easy|medium|hard"
        }}
    ],
    "untapped_keywords": [
        {{
            "keyword": "...",
            "reason": "pourquoi c'est une opportunite",
            "volume": "high|medium|low",
            "priority": "high|medium|low"
        }}
    ],
    "local_opportunities": [
        {{
            "keyword": "...",
            "location": "ville/region",
            "competition": "low|medium|high"
        }}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 4000, "Tu es un expert SEO. Reponds uniquement en JSON valide.")
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                return json.loads(response.strip())
        except Exception as e:
            log_agent(self.name, f"Erreur analyse gap: {e}", "ERROR")

        # Fallback
        return {
            'competitor_keywords': [],
            'weak_positions': [],
            'untapped_keywords': [],
            'local_opportunities': []
        }

    def _categorize_opportunities(self, analysis):
        """Categorise les opportunites par priorite"""
        high_priority = []
        medium_priority = []
        low_priority = []
        quick_wins = []

        # Analyser competitor_keywords
        for kw in analysis.get('competitor_keywords', []):
            opportunity = {
                'keyword': kw.get('keyword', ''),
                'type': 'competitor_gap',
                'volume': kw.get('volume', 'medium'),
                'difficulty': kw.get('difficulty', 50),
                'content_type': kw.get('content_type', 'article'),
                'source': kw.get('competitor_ranking', '')
            }

            if kw.get('business_potential') == 'high' and kw.get('difficulty', 50) < 60:
                high_priority.append(opportunity)
            elif kw.get('volume') == 'high':
                medium_priority.append(opportunity)
            else:
                low_priority.append(opportunity)

        # Analyser weak_positions (quick wins)
        for kw in analysis.get('weak_positions', []):
            if kw.get('improvement_difficulty') == 'easy':
                quick_wins.append({
                    'keyword': kw.get('keyword', ''),
                    'type': 'weak_position',
                    'current_position': kw.get('client_position', 0),
                    'target_position': kw.get('competitor_position', 0),
                    'gap': kw.get('gap', 0)
                })

        # Ajouter untapped keywords
        for kw in analysis.get('untapped_keywords', []):
            opportunity = {
                'keyword': kw.get('keyword', ''),
                'type': 'untapped',
                'volume': kw.get('volume', 'medium'),
                'reason': kw.get('reason', '')
            }

            if kw.get('priority') == 'high':
                high_priority.append(opportunity)
            elif kw.get('priority') == 'medium':
                medium_priority.append(opportunity)
            else:
                low_priority.append(opportunity)

        # Ajouter local opportunities
        for kw in analysis.get('local_opportunities', []):
            opportunity = {
                'keyword': kw.get('keyword', ''),
                'type': 'local',
                'location': kw.get('location', ''),
                'competition': kw.get('competition', 'medium')
            }

            if kw.get('competition') == 'low':
                quick_wins.append(opportunity)
            else:
                medium_priority.append(opportunity)

        return {
            'high_priority': high_priority[:15],
            'medium_priority': medium_priority[:15],
            'low_priority': low_priority[:10],
            'quick_wins': quick_wins[:10],
            'total_opportunities': len(high_priority) + len(medium_priority) + len(low_priority) + len(quick_wins)
        }

    def _generate_recommendations(self, opportunities, niche):
        """Genere des recommandations basees sur les opportunites"""
        recommendations = []

        # Quick wins en premier
        if opportunities.get('quick_wins'):
            recommendations.append({
                'priority': 1,
                'title': 'Quick Wins - Ameliorations rapides',
                'description': f"Optimiser {len(opportunities['quick_wins'])} pages existantes pour gagner des positions",
                'keywords': [kw['keyword'] for kw in opportunities['quick_wins'][:5]],
                'effort': 'low',
                'impact': 'high',
                'timeline': '1-2 semaines'
            })

        # High priority content
        if opportunities.get('high_priority'):
            content_types = {}
            for kw in opportunities['high_priority']:
                ct = kw.get('content_type', 'article')
                if ct not in content_types:
                    content_types[ct] = []
                content_types[ct].append(kw['keyword'])

            for ct, keywords in content_types.items():
                recommendations.append({
                    'priority': 2,
                    'title': f'Creer du contenu {ct}',
                    'description': f"Creer {len(keywords)} {ct}s pour cibler les keywords prioritaires",
                    'keywords': keywords[:5],
                    'effort': 'medium',
                    'impact': 'high',
                    'timeline': '2-4 semaines'
                })

        # Local SEO
        local_opps = [kw for kw in opportunities.get('quick_wins', []) + opportunities.get('medium_priority', [])
                      if kw.get('type') == 'local']
        if local_opps:
            recommendations.append({
                'priority': 3,
                'title': 'Optimisation SEO Local',
                'description': f"Cibler {len(local_opps)} mots-cles locaux",
                'keywords': [kw['keyword'] for kw in local_opps[:5]],
                'effort': 'low',
                'impact': 'medium',
                'timeline': '1-2 semaines'
            })

        return recommendations

    def _generate_action_plan(self, opportunities):
        """Genere un plan d'action structure"""
        plan = {
            'week_1': {
                'focus': 'Quick Wins',
                'tasks': []
            },
            'week_2_3': {
                'focus': 'Contenu Prioritaire',
                'tasks': []
            },
            'week_4': {
                'focus': 'SEO Local + Suivi',
                'tasks': []
            }
        }

        # Week 1: Quick wins
        for i, kw in enumerate(opportunities.get('quick_wins', [])[:5]):
            plan['week_1']['tasks'].append({
                'task': f"Optimiser page pour '{kw['keyword']}'",
                'type': 'optimization',
                'priority': i + 1
            })

        # Week 2-3: High priority content
        for i, kw in enumerate(opportunities.get('high_priority', [])[:6]):
            plan['week_2_3']['tasks'].append({
                'task': f"Creer {kw.get('content_type', 'article')} pour '{kw['keyword']}'",
                'type': 'content_creation',
                'priority': i + 1
            })

        # Week 4: Local + tracking
        plan['week_4']['tasks'] = [
            {'task': 'Setup tracking pour nouveaux keywords', 'type': 'tracking', 'priority': 1},
            {'task': 'Optimiser Google My Business', 'type': 'local_seo', 'priority': 2},
            {'task': 'Analyser resultats et ajuster', 'type': 'analysis', 'priority': 3}
        ]

        return plan

    def compare_two_domains(self, domain1, domain2, niche=''):
        """Compare directement deux domaines"""
        log_agent(self.name, f"Comparaison directe: {domain1} vs {domain2}")

        prompt = f"""Compare ces deux sites web en termes de SEO:

SITE 1: {domain1}
SITE 2: {domain2}
NICHE: {niche}

ANALYSE:
1. Mots-cles ou Site 1 gagne
2. Mots-cles ou Site 2 gagne
3. Opportunites pour les deux
4. Forces/faiblesses de chaque site

FORMAT JSON:
{{
    "site1_wins": [
        {{"keyword": "...", "position": 1-10, "advantage": "..."}}
    ],
    "site2_wins": [
        {{"keyword": "...", "position": 1-10, "advantage": "..."}}
    ],
    "shared_opportunities": [
        {{"keyword": "...", "difficulty": "low|medium|high"}}
    ],
    "site1_strengths": ["..."],
    "site1_weaknesses": ["..."],
    "site2_strengths": ["..."],
    "site2_weaknesses": ["..."],
    "winner": "site1|site2|tie",
    "recommendation": "..."
}}
"""

        try:
            response = call_qwen(prompt, 2500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {'error': 'Analyse impossible'}

    def find_content_gaps(self, client_id, competitors):
        """Trouve specifiquement les gaps de contenu"""
        client_domain = self._get_client_domain(client_id)
        client_niche = self._get_client_niche(client_id)

        prompt = f"""Analyse les gaps de contenu entre ce site et ses concurrents.

CLIENT: {client_domain}
NICHE: {client_niche}

CONCURRENTS:
{chr(10).join([f"- {c}" for c in competitors[:3]])}

Identifie les types de contenu que les concurrents ont mais PAS le client:
- Pages de services manquantes
- Articles de blog manquants
- Guides/tutoriels
- FAQ
- Pages locales
- Ressources/outils

FORMAT JSON:
{{
    "missing_service_pages": [
        {{"title": "...", "target_keyword": "...", "competitor_has": "competitor.com"}}
    ],
    "missing_blog_topics": [
        {{"topic": "...", "keywords": ["...", "..."], "format": "article|guide|liste"}}
    ],
    "missing_resources": [
        {{"type": "faq|calculator|guide", "description": "..."}}
    ],
    "missing_local_pages": [
        {{"city": "...", "service": "..."}}
    ],
    "content_priority": [
        {{"title": "...", "impact": "high|medium", "effort": "low|medium|high"}}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 2500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {'error': 'Analyse impossible'}

    def get_competitor_keywords(self, competitor_domain, niche='', limit=20):
        """Estime les mots-cles d'un concurrent"""
        prompt = f"""Estime les mots-cles principaux pour lesquels ce site se positionne:

SITE: {competitor_domain}
NICHE: {niche}

Liste les {limit} mots-cles les plus probables avec:
- Position estimee
- Volume estime
- Intention de recherche

FORMAT JSON:
{{
    "keywords": [
        {{
            "keyword": "...",
            "estimated_position": 1-20,
            "volume": "high|medium|low",
            "intent": "informational|transactional|navigational|commercial"
        }}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 2000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                return data.get('keywords', [])
        except:
            pass

        return []


# ============================================
# AGENT 40: CONTENT BRIEF AGENT
# ============================================
class ContentBriefAgent:
    """
    Agent de generation de briefs de contenu pour redacteurs
    Cree des briefs complets avec structure, mots-cles, et guidelines
    """
    name = "Content Brief Agent"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour les briefs"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_briefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    title TEXT,
                    target_keyword TEXT,
                    content_type TEXT,
                    word_count INTEGER,
                    brief_json TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur init DB: {e}", "ERROR")

    def generate_brief(self, client_id, target_keyword, content_type='article', word_count=1500):
        """
        Genere un brief de contenu complet
        content_type: article, guide, landing, faq, comparison
        """
        log_agent(self.name, f"Generation brief pour '{target_keyword}' - {content_type}")

        # Recuperer infos client
        client_info = self._get_client_info(client_id)

        # Recherche semantique
        semantic_keywords = self.get_semantic_keywords(target_keyword, client_info.get('niche', ''))

        # Generer structure du contenu
        outline = self.generate_outline(target_keyword, content_type, client_info.get('niche', ''))

        # Generer meta data
        meta = self.generate_meta_data(target_keyword, content_type, client_info.get('niche', ''))

        # Analyse concurrence
        competition = self._analyze_competition(target_keyword)

        # Questions a repondre
        questions = self._get_user_questions(target_keyword)

        # Guidelines de redaction
        guidelines = self._generate_guidelines(content_type, client_info)

        brief = {
            'client_id': client_id,
            'client_name': client_info.get('name', ''),
            'client_domain': client_info.get('domain', ''),
            'target_keyword': target_keyword,
            'content_type': content_type,
            'word_count': word_count,
            'meta': meta,
            'outline': outline,
            'semantic_keywords': semantic_keywords,
            'questions_to_answer': questions,
            'competition_analysis': competition,
            'guidelines': guidelines,
            'internal_linking': self._suggest_internal_links(client_id, target_keyword),
            'cta_suggestions': self._generate_cta_suggestions(content_type, client_info),
            'created_at': datetime.now().isoformat()
        }

        log_agent(self.name, f"Brief genere avec {len(outline)} sections")

        return brief

    def _get_client_info(self, client_id):
        """Recupere les infos du client"""
        site = SITES.get(client_id, {})
        if site:
            return {
                'name': site.get('nom', ''),
                'domain': site.get('domaine', ''),
                'niche': site.get('niche', '')
            }

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT company_name, domain, niche FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'name': row[0],
                    'domain': row[1],
                    'niche': row[2]
                }
        except:
            pass

        return {'name': '', 'domain': '', 'niche': ''}

    def get_semantic_keywords(self, target_keyword, niche='', limit=20):
        """Trouve les mots-cles semantiquement lies"""
        prompt = f"""Tu es un expert SEO. Trouve les mots-cles semantiquement lies a "{target_keyword}".

NICHE: {niche}
REGION: Quebec/Canada

Inclus:
1. Synonymes et variations
2. Mots-cles LSI (Latent Semantic Indexing)
3. Questions liees
4. Mots-cles longue traine
5. Termes techniques du domaine

FORMAT JSON:
{{
    "primary_keyword": "{target_keyword}",
    "synonyms": ["...", "..."],
    "lsi_keywords": ["...", "..."],
    "long_tail": ["...", "..."],
    "related_questions": ["...", "..."],
    "technical_terms": ["...", "..."],
    "usage_density": {{
        "primary": "1-2%",
        "secondary": "0.5-1%",
        "lsi": "natural"
    }}
}}
"""

        try:
            response = call_qwen(prompt, 1500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {
            'primary_keyword': target_keyword,
            'synonyms': [],
            'lsi_keywords': [],
            'long_tail': [],
            'related_questions': [],
            'technical_terms': []
        }

    def generate_outline(self, target_keyword, content_type, niche=''):
        """Genere un plan detaille du contenu"""
        prompt = f"""Cree un plan detaille pour un {content_type} sur "{target_keyword}".

NICHE: {niche}
REGION: Quebec/Canada
TYPE: {content_type}

Le plan doit inclure:
- H1 (titre principal)
- H2 (sections principales)
- H3 (sous-sections)
- Points cles a couvrir dans chaque section
- Mots-cles a integrer naturellement

FORMAT JSON:
{{
    "h1": "Titre optimise SEO",
    "intro": {{
        "hook": "Accroche",
        "context": "Contexte",
        "promise": "Ce que le lecteur va apprendre"
    }},
    "sections": [
        {{
            "h2": "Titre section",
            "h3s": ["Sous-titre 1", "Sous-titre 2"],
            "key_points": ["Point 1", "Point 2"],
            "keywords_to_include": ["mot-cle 1", "mot-cle 2"],
            "word_count_estimate": 200-400
        }}
    ],
    "conclusion": {{
        "summary": "Resume des points cles",
        "cta": "Appel a l'action"
    }},
    "total_sections": 5-8
}}
"""

        try:
            response = call_qwen(prompt, 2500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {
            'h1': target_keyword.title(),
            'intro': {},
            'sections': [],
            'conclusion': {}
        }

    def generate_meta_data(self, target_keyword, content_type, niche=''):
        """Genere les meta title et description optimises"""
        prompt = f"""Genere des meta title et description SEO optimises.

MOT-CLE: {target_keyword}
TYPE: {content_type}
NICHE: {niche}
REGION: Quebec

REGLES:
- Meta title: 50-60 caracteres, mot-cle au debut
- Meta description: 150-160 caracteres, incitative, avec mot-cle

Genere 3 options pour chaque.

FORMAT JSON:
{{
    "meta_titles": [
        {{"text": "...", "length": 55, "keyword_position": "start"}},
        {{"text": "...", "length": 58, "keyword_position": "start"}},
        {{"text": "...", "length": 52, "keyword_position": "middle"}}
    ],
    "meta_descriptions": [
        {{"text": "...", "length": 155, "has_cta": true}},
        {{"text": "...", "length": 158, "has_cta": true}},
        {{"text": "...", "length": 152, "has_cta": false}}
    ],
    "recommended": {{
        "title": "...",
        "description": "..."
    }}
}}
"""

        try:
            response = call_qwen(prompt, 1500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {
            'meta_titles': [{'text': target_keyword.title(), 'length': len(target_keyword)}],
            'meta_descriptions': [],
            'recommended': {'title': target_keyword.title(), 'description': ''}
        }

    def _analyze_competition(self, target_keyword):
        """Analyse la concurrence pour ce mot-cle"""
        prompt = f"""Analyse la concurrence SERP pour "{target_keyword}" au Quebec.

Estime:
1. Niveau de competition (1-100)
2. Types de contenu qui rankent (article, video, liste, guide)
3. Longueur moyenne du contenu top 10
4. Elements differenciateurs necessaires
5. Angle unique possible

FORMAT JSON:
{{
    "difficulty": 1-100,
    "top_content_types": ["article", "guide"],
    "avg_word_count": 1500,
    "avg_headings": 8,
    "common_elements": ["images", "videos", "listes"],
    "differentiation_tips": ["...", "..."],
    "unique_angle_suggestions": ["...", "..."],
    "estimated_time_to_rank": "1-3 mois"
}}
"""

        try:
            response = call_qwen(prompt, 1200)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {
            'difficulty': 50,
            'top_content_types': ['article'],
            'avg_word_count': 1500
        }

    def _get_user_questions(self, target_keyword):
        """Trouve les questions que les utilisateurs posent"""
        prompt = f"""Liste les questions que les gens posent sur "{target_keyword}".

Inclus:
- Questions "People Also Ask"
- Questions de recherche
- Questions FAQ communes
- Objections/preoccupations

FORMAT JSON:
{{
    "questions": [
        {{
            "question": "...",
            "type": "paa|faq|concern|how-to",
            "priority": "high|medium|low",
            "answer_format": "paragraph|list|steps"
        }}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 1500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                return data.get('questions', [])
        except:
            pass

        return []

    def _generate_guidelines(self, content_type, client_info):
        """Genere les guidelines de redaction"""
        guidelines = {
            'tone': 'Professionnel mais accessible',
            'language': 'Francais quebecois',
            'audience': 'Grand public',
            'formatting': {
                'paragraphs': 'Courts (3-4 phrases max)',
                'sentences': 'Variees (courtes et moyennes)',
                'lists': 'Utiliser des listes pour la lisibilite',
                'headings': 'H2 tous les 200-300 mots'
            },
            'seo_rules': {
                'keyword_in_h1': True,
                'keyword_in_first_100_words': True,
                'keyword_in_h2': 'Au moins 1-2 fois',
                'keyword_density': '1-2%',
                'internal_links': '2-3 minimum',
                'external_links': '1-2 sources fiables'
            },
            'media': {
                'images': '1 image tous les 300-400 mots',
                'alt_text': 'Descriptif avec mot-cle si naturel',
                'videos': 'Recommande si disponible'
            }
        }

        # Adapter selon le type de contenu
        if content_type == 'guide':
            guidelines['word_count_target'] = '2000-3000'
            guidelines['depth'] = 'Approfondi et detaille'
        elif content_type == 'faq':
            guidelines['format'] = 'Questions/Reponses schema FAQ'
            guidelines['word_count_target'] = '800-1500'
        elif content_type == 'landing':
            guidelines['focus'] = 'Conversion'
            guidelines['word_count_target'] = '500-1000'
            guidelines['cta_frequency'] = 'Plusieurs CTAs strategiques'
        elif content_type == 'comparison':
            guidelines['format'] = 'Tableau comparatif + analyse'
            guidelines['objectivity'] = 'Presenter les deux cotes'

        return guidelines

    def _suggest_internal_links(self, client_id, target_keyword):
        """Suggere des liens internes pertinents"""
        site = SITES.get(client_id, {})
        niche = site.get('niche', '')

        prompt = f"""Suggere des liens internes pour un article sur "{target_keyword}".

NICHE: {niche}

Suggere des pages typiques d'un site de {niche} qui seraient pertinentes.

FORMAT JSON:
{{
    "suggested_links": [
        {{
            "anchor_text": "texte du lien",
            "target_page": "/services/...",
            "context": "dans quel contexte placer ce lien"
        }}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 1000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                return data.get('suggested_links', [])
        except:
            pass

        return []

    def _generate_cta_suggestions(self, content_type, client_info):
        """Genere des suggestions de CTA"""
        ctas = {
            'primary': {
                'text': 'Demandez votre soumission gratuite',
                'placement': 'Fin de l\'article et sidebar',
                'type': 'form'
            },
            'secondary': [
                {'text': 'Appelez-nous au XXX-XXX-XXXX', 'placement': 'Header sticky'},
                {'text': 'Consultez nos realisations', 'placement': 'Mi-article'},
                {'text': 'Telecharger notre guide gratuit', 'placement': 'Popup ou sidebar'}
            ]
        }

        return ctas

    def save_brief(self, brief):
        """Sauvegarde le brief en base de donnees"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO content_briefs (client_id, title, target_keyword, content_type, word_count, brief_json, status)
                VALUES (?, ?, ?, ?, ?, ?, 'draft')
            ''', (
                brief.get('client_id'),
                brief.get('meta', {}).get('recommended', {}).get('title', brief.get('target_keyword')),
                brief.get('target_keyword'),
                brief.get('content_type'),
                brief.get('word_count'),
                json.dumps(brief, ensure_ascii=False)
            ))
            brief_id = cursor.lastrowid
            conn.commit()
            conn.close()

            log_agent(self.name, f"Brief sauvegarde ID: {brief_id}")
            return brief_id
        except Exception as e:
            log_agent(self.name, f"Erreur save brief: {e}", "ERROR")
            return None

    def get_briefs(self, client_id=None, status=None):
        """Recupere les briefs"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, client_id, title, target_keyword, content_type, status, created_at FROM content_briefs WHERE 1=1'
            params = []

            if client_id:
                query += ' AND client_id = ?'
                params.append(client_id)
            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'client_id': r[1],
                    'title': r[2],
                    'target_keyword': r[3],
                    'content_type': r[4],
                    'status': r[5],
                    'created_at': r[6]
                }
                for r in rows
            ]
        except:
            return []

    def get_brief(self, brief_id):
        """Recupere un brief complet"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT brief_json FROM content_briefs WHERE id = ?', (brief_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def update_brief_status(self, brief_id, status):
        """Met a jour le statut d'un brief"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE content_briefs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                          (status, brief_id))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def generate_html_brief(self, brief):
        """Genere une version HTML du brief pour partage"""
        outline = brief.get('outline', {})
        meta = brief.get('meta', {})
        semantic = brief.get('semantic_keywords', {})
        guidelines = brief.get('guidelines', {})

        html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brief: {brief.get('target_keyword', '')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .brief-container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #1a73e8;
        }}
        h2 {{
            color: #333;
            margin: 30px 0 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        h3 {{ color: #555; margin: 20px 0 10px; }}
        .meta-box {{
            background: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .keyword-tag {{
            display: inline-block;
            background: #1a73e8;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            margin: 3px;
            font-size: 14px;
        }}
        .section-card {{
            background: #fafafa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #1a73e8;
        }}
        .guideline {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        ul {{ margin-left: 20px; }}
        li {{ margin: 8px 0; }}
        .info {{ color: #666; font-size: 14px; }}
        .cta-box {{
            background: #d4edda;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="brief-container">
        <h1>Brief de Contenu: {brief.get('target_keyword', '')}</h1>

        <div class="info">
            <p><strong>Client:</strong> {brief.get('client_name', '')}</p>
            <p><strong>Type:</strong> {brief.get('content_type', 'article')}</p>
            <p><strong>Nombre de mots:</strong> {brief.get('word_count', 1500)}</p>
            <p><strong>Date:</strong> {brief.get('created_at', '')[:10]}</p>
        </div>

        <h2>Meta Data Recommandees</h2>
        <div class="meta-box">
            <p><strong>Title:</strong> {meta.get('recommended', {}).get('title', '')}</p>
            <p><strong>Description:</strong> {meta.get('recommended', {}).get('description', '')}</p>
        </div>

        <h2>Structure du Contenu</h2>
        <h3>H1: {outline.get('h1', '')}</h3>

        <div class="section-card">
            <h4>Introduction</h4>
            <ul>
                <li><strong>Accroche:</strong> {outline.get('intro', {}).get('hook', '')}</li>
                <li><strong>Contexte:</strong> {outline.get('intro', {}).get('context', '')}</li>
                <li><strong>Promesse:</strong> {outline.get('intro', {}).get('promise', '')}</li>
            </ul>
        </div>
'''

        # Ajouter les sections
        for i, section in enumerate(outline.get('sections', []), 1):
            html += f'''
        <div class="section-card">
            <h4>Section {i}: {section.get('h2', '')}</h4>
            <p><strong>Sous-sections:</strong></p>
            <ul>'''
            for h3 in section.get('h3s', []):
                html += f'<li>{h3}</li>'
            html += '''</ul>
            <p><strong>Points cles:</strong></p>
            <ul>'''
            for point in section.get('key_points', []):
                html += f'<li>{point}</li>'
            html += f'''</ul>
            <p><strong>Mots de passe a inclure:</strong> {', '.join(section.get('keywords_to_include', []))}</p>
        </div>'''

        html += f'''
        <h2>Mots-cles Semantiques</h2>
        <h3>Synonymes</h3>
        <div>'''
        for kw in semantic.get('synonyms', []):
            html += f'<span class="keyword-tag">{kw}</span>'
        html += '''</div>
        <h3>Mots-cles LSI</h3>
        <div>'''
        for kw in semantic.get('lsi_keywords', []):
            html += f'<span class="keyword-tag">{kw}</span>'
        html += '''</div>
        <h3>Longue Traine</h3>
        <div>'''
        for kw in semantic.get('long_tail', []):
            html += f'<span class="keyword-tag">{kw}</span>'
        html += '''</div>

        <h2>Questions a Repondre</h2>
        <ul>'''
        for q in brief.get('questions_to_answer', []):
            html += f'<li>{q.get("question", "")}</li>'
        html += '''</ul>

        <h2>Guidelines de Redaction</h2>
        <div class="guideline">
            <p><strong>Ton:</strong> {}</p>
            <p><strong>Langue:</strong> {}</p>
            <p><strong>Paragraphes:</strong> {}</p>
            <p><strong>Densite mot-cle:</strong> {}</p>
        </div>

        <h2>Liens Internes Suggeres</h2>
        <ul>'''.format(
            guidelines.get('tone', ''),
            guidelines.get('language', ''),
            guidelines.get('formatting', {}).get('paragraphs', ''),
            guidelines.get('seo_rules', {}).get('keyword_density', '')
        )

        for link in brief.get('internal_linking', []):
            html += f'<li><a href="{link.get("target_page", "")}">{link.get("anchor_text", "")}</a> - {link.get("context", "")}</li>'

        html += '''</ul>

        <h2>CTAs Suggeres</h2>
        <div class="cta-box">'''
        ctas = brief.get('cta_suggestions', {})
        if ctas.get('primary'):
            html += f'<p><strong>CTA Principal:</strong> {ctas["primary"].get("text", "")}</p>'
        for cta in ctas.get('secondary', []):
            html += f'<p>{cta.get("text", "")} - <em>{cta.get("placement", "")}</em></p>'
        html += '''</div>

    </div>
</body>
</html>'''

        return html


# ============================================
# AGENT 41: BACKLINK MONITOR AGENT
# ============================================
class BacklinkMonitorAgent:
    """
    Agent de surveillance des backlinks
    Detecte nouveaux backlinks, backlinks perdus, et analyse la qualite
    """
    name = "Backlink Monitor Agent"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour les backlinks"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Table des backlinks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backlinks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    source_url TEXT,
                    source_domain TEXT,
                    target_url TEXT,
                    anchor_text TEXT,
                    link_type TEXT DEFAULT 'dofollow',
                    domain_authority INTEGER DEFAULT 0,
                    spam_score INTEGER DEFAULT 0,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    UNIQUE(client_id, source_url, target_url)
                )
            ''')

            # Table historique des changements
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backlink_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    backlink_id INTEGER,
                    event_type TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table alertes backlinks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backlink_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    backlink_id INTEGER,
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur init DB: {e}", "ERROR")

    def discover_backlinks(self, client_id):
        """
        Decouvre les backlinks d'un client via analyse IA
        (simulation - en production utiliser une API comme Ahrefs/Moz)
        """
        log_agent(self.name, f"Decouverte backlinks pour client {client_id}")

        client_domain = self._get_client_domain(client_id)
        if not client_domain:
            return {'error': 'Client non trouve'}

        # Generer estimation avec IA
        backlinks = self._estimate_backlinks(client_domain)

        # Sauvegarder les nouveaux backlinks
        new_count = 0
        for bl in backlinks:
            if self._save_backlink(client_id, bl):
                new_count += 1
                self._create_alert(client_id, 'new_backlink', 'info',
                                   f"Nouveau backlink de {bl.get('source_domain', '')}")

        return {
            'client_id': client_id,
            'domain': client_domain,
            'backlinks_found': len(backlinks),
            'new_backlinks': new_count,
            'backlinks': backlinks
        }

    def _get_client_domain(self, client_id):
        """Recupere le domaine du client"""
        site = SITES.get(client_id, {})
        if site:
            return site.get('domaine', '')
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT domain FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def _estimate_backlinks(self, domain):
        """Estime les backlinks via IA"""
        prompt = f"""Tu es un expert SEO. Estime les backlinks probables pour ce site:

DOMAINE: {domain}

Base sur le type de site, estime 10-15 backlinks typiques avec:
- Domaine source
- Type de lien (dofollow/nofollow)
- Texte d'ancrage probable
- Autorite estimee du domaine (1-100)
- Score spam (0-100)

FORMAT JSON:
{{
    "backlinks": [
        {{
            "source_domain": "example.com",
            "source_url": "https://example.com/page",
            "target_url": "https://{domain}/",
            "anchor_text": "texte du lien",
            "link_type": "dofollow|nofollow",
            "domain_authority": 45,
            "spam_score": 5,
            "context": "type de page source"
        }}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 2000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                data = json.loads(response.strip())
                return data.get('backlinks', [])
        except:
            pass

        return []

    def _save_backlink(self, client_id, backlink):
        """Sauvegarde un backlink"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO backlinks
                (client_id, source_url, source_domain, target_url, anchor_text, link_type, domain_authority, spam_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id,
                backlink.get('source_url', ''),
                backlink.get('source_domain', ''),
                backlink.get('target_url', ''),
                backlink.get('anchor_text', ''),
                backlink.get('link_type', 'dofollow'),
                backlink.get('domain_authority', 0),
                backlink.get('spam_score', 0)
            ))
            inserted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return inserted
        except:
            return False

    def _create_alert(self, client_id, alert_type, severity, message, backlink_id=None):
        """Cree une alerte backlink"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backlink_alerts (client_id, alert_type, severity, message, backlink_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_id, alert_type, severity, message, backlink_id))
            conn.commit()
            conn.close()
        except:
            pass

    def check_backlink_status(self, client_id):
        """Verifie le statut des backlinks existants"""
        log_agent(self.name, f"Verification statut backlinks pour client {client_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_url, source_domain, target_url, status, last_seen
                FROM backlinks WHERE client_id = ? AND status = 'active'
            ''', (client_id,))
            backlinks = cursor.fetchall()
            conn.close()

            results = {
                'checked': len(backlinks),
                'active': 0,
                'lost': 0,
                'issues': []
            }

            for bl in backlinks:
                # Simulation - en production, faire un vrai check HTTP
                # Ici on simule que 95% des backlinks sont toujours actifs
                import random
                if random.random() > 0.95:
                    # Backlink perdu
                    self._mark_backlink_lost(bl[0], client_id)
                    results['lost'] += 1
                    results['issues'].append({
                        'backlink_id': bl[0],
                        'source': bl[2],
                        'issue': 'Backlink perdu'
                    })
                else:
                    self._update_last_seen(bl[0])
                    results['active'] += 1

            return results
        except Exception as e:
            return {'error': str(e)}

    def _mark_backlink_lost(self, backlink_id, client_id):
        """Marque un backlink comme perdu"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE backlinks SET status = ? WHERE id = ?', ('lost', backlink_id))

            # Historique
            cursor.execute('''
                INSERT INTO backlink_history (client_id, backlink_id, event_type, details)
                VALUES (?, ?, 'lost', 'Backlink non detecte')
            ''', (client_id, backlink_id))

            conn.commit()
            conn.close()

            # Alerte
            self._create_alert(client_id, 'lost_backlink', 'warning',
                               'Un backlink a ete perdu', backlink_id)
        except:
            pass

    def _update_last_seen(self, backlink_id):
        """Met a jour la date de derniere verification"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE backlinks SET last_seen = CURRENT_TIMESTAMP WHERE id = ?', (backlink_id,))
            conn.commit()
            conn.close()
        except:
            pass

    def get_backlinks(self, client_id, status=None, limit=100):
        """Recupere les backlinks d'un client"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT id, source_url, source_domain, target_url, anchor_text,
                       link_type, domain_authority, spam_score, first_seen, last_seen, status
                FROM backlinks WHERE client_id = ?
            '''
            params = [client_id]

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY domain_authority DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'source_url': r[1],
                    'source_domain': r[2],
                    'target_url': r[3],
                    'anchor_text': r[4],
                    'link_type': r[5],
                    'domain_authority': r[6],
                    'spam_score': r[7],
                    'first_seen': r[8],
                    'last_seen': r[9],
                    'status': r[10]
                }
                for r in rows
            ]
        except:
            return []

    def get_backlink_stats(self, client_id):
        """Statistiques des backlinks"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            stats = {}

            # Total actifs
            cursor.execute('SELECT COUNT(*) FROM backlinks WHERE client_id = ? AND status = ?',
                          (client_id, 'active'))
            stats['total_active'] = cursor.fetchone()[0]

            # Total perdus
            cursor.execute('SELECT COUNT(*) FROM backlinks WHERE client_id = ? AND status = ?',
                          (client_id, 'lost'))
            stats['total_lost'] = cursor.fetchone()[0]

            # Dofollow vs Nofollow
            cursor.execute('SELECT COUNT(*) FROM backlinks WHERE client_id = ? AND link_type = ? AND status = ?',
                          (client_id, 'dofollow', 'active'))
            stats['dofollow'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM backlinks WHERE client_id = ? AND link_type = ? AND status = ?',
                          (client_id, 'nofollow', 'active'))
            stats['nofollow'] = cursor.fetchone()[0]

            # DA moyen
            cursor.execute('SELECT AVG(domain_authority) FROM backlinks WHERE client_id = ? AND status = ?',
                          (client_id, 'active'))
            avg_da = cursor.fetchone()[0]
            stats['avg_domain_authority'] = round(avg_da, 1) if avg_da else 0

            # Score spam moyen
            cursor.execute('SELECT AVG(spam_score) FROM backlinks WHERE client_id = ? AND status = ?',
                          (client_id, 'active'))
            avg_spam = cursor.fetchone()[0]
            stats['avg_spam_score'] = round(avg_spam, 1) if avg_spam else 0

            # Nouveaux ce mois
            cursor.execute('''
                SELECT COUNT(*) FROM backlinks
                WHERE client_id = ? AND first_seen >= date('now', '-30 days')
            ''', (client_id,))
            stats['new_this_month'] = cursor.fetchone()[0]

            # Perdus ce mois
            cursor.execute('''
                SELECT COUNT(*) FROM backlink_history
                WHERE client_id = ? AND event_type = 'lost'
                AND created_at >= date('now', '-30 days')
            ''', (client_id,))
            stats['lost_this_month'] = cursor.fetchone()[0]

            conn.close()
            return stats
        except Exception as e:
            return {'error': str(e)}

    def get_toxic_backlinks(self, client_id, spam_threshold=50):
        """Identifie les backlinks toxiques"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_url, source_domain, anchor_text, spam_score, domain_authority
                FROM backlinks
                WHERE client_id = ? AND spam_score >= ? AND status = 'active'
                ORDER BY spam_score DESC
            ''', (client_id, spam_threshold))
            rows = cursor.fetchall()
            conn.close()

            toxic = [
                {
                    'id': r[0],
                    'source_url': r[1],
                    'source_domain': r[2],
                    'anchor_text': r[3],
                    'spam_score': r[4],
                    'domain_authority': r[5],
                    'recommendation': 'Desavouer via Google Disavow Tool'
                }
                for r in rows
            ]

            return {
                'count': len(toxic),
                'toxic_backlinks': toxic,
                'action_required': len(toxic) > 0
            }
        except:
            return {'count': 0, 'toxic_backlinks': []}

    def get_alerts(self, client_id, unread_only=True):
        """Recupere les alertes backlinks"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, alert_type, severity, message, backlink_id, is_read, created_at FROM backlink_alerts WHERE client_id = ?'
            params = [client_id]

            if unread_only:
                query += ' AND is_read = 0'

            query += ' ORDER BY created_at DESC LIMIT 50'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'type': r[1],
                    'severity': r[2],
                    'message': r[3],
                    'backlink_id': r[4],
                    'is_read': bool(r[5]),
                    'created_at': r[6]
                }
                for r in rows
            ]
        except:
            return []

    def mark_alerts_read(self, client_id, alert_ids=None):
        """Marque les alertes comme lues"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            if alert_ids:
                placeholders = ','.join('?' * len(alert_ids))
                cursor.execute(f'UPDATE backlink_alerts SET is_read = 1 WHERE id IN ({placeholders})', alert_ids)
            else:
                cursor.execute('UPDATE backlink_alerts SET is_read = 1 WHERE client_id = ?', (client_id,))

            conn.commit()
            conn.close()
            return True
        except:
            return False

    def analyze_anchor_distribution(self, client_id):
        """Analyse la distribution des textes d'ancrage"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT anchor_text, COUNT(*) as count
                FROM backlinks WHERE client_id = ? AND status = 'active'
                GROUP BY anchor_text ORDER BY count DESC
            ''', (client_id,))
            rows = cursor.fetchall()
            conn.close()

            total = sum(r[1] for r in rows)
            distribution = [
                {
                    'anchor_text': r[0] or '(vide)',
                    'count': r[1],
                    'percentage': round((r[1] / total * 100), 1) if total > 0 else 0
                }
                for r in rows
            ]

            # Analyse des risques
            analysis = self._analyze_anchor_risks(distribution)

            return {
                'total_backlinks': total,
                'unique_anchors': len(distribution),
                'distribution': distribution[:20],
                'analysis': analysis
            }
        except:
            return {'error': 'Analyse impossible'}

    def _analyze_anchor_risks(self, distribution):
        """Analyse les risques lies aux ancres"""
        risks = []
        recommendations = []

        if not distribution:
            return {'risks': [], 'recommendations': [], 'health_score': 50}

        # Verifier si une ancre domine trop
        if distribution[0]['percentage'] > 30:
            risks.append({
                'type': 'over_optimization',
                'severity': 'high',
                'description': f"L'ancre '{distribution[0]['anchor_text']}' represente {distribution[0]['percentage']}% des backlinks"
            })
            recommendations.append("Diversifier les textes d'ancrage")

        # Verifier les ancres vides
        empty_anchors = [d for d in distribution if d['anchor_text'] == '(vide)']
        if empty_anchors and empty_anchors[0]['percentage'] > 20:
            risks.append({
                'type': 'empty_anchors',
                'severity': 'medium',
                'description': f"{empty_anchors[0]['percentage']}% des backlinks n'ont pas de texte d'ancrage"
            })

        # Score de sante
        health_score = 100
        for risk in risks:
            if risk['severity'] == 'high':
                health_score -= 25
            elif risk['severity'] == 'medium':
                health_score -= 10

        return {
            'risks': risks,
            'recommendations': recommendations,
            'health_score': max(0, health_score)
        }

    def get_referring_domains(self, client_id):
        """Liste des domaines referents uniques"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT source_domain, COUNT(*) as links, AVG(domain_authority) as avg_da
                FROM backlinks WHERE client_id = ? AND status = 'active'
                GROUP BY source_domain ORDER BY avg_da DESC
            ''', (client_id,))
            rows = cursor.fetchall()
            conn.close()

            return {
                'total_referring_domains': len(rows),
                'domains': [
                    {
                        'domain': r[0],
                        'links': r[1],
                        'avg_authority': round(r[2], 1) if r[2] else 0
                    }
                    for r in rows
                ]
            }
        except:
            return {'total_referring_domains': 0, 'domains': []}


# ============================================
# AGENT 42: SITE SPEED AGENT
# ============================================
class SiteSpeedAgent:
    """
    Agent d'analyse et surveillance de la vitesse des sites
    Mesure Core Web Vitals, temps de chargement, et optimisations
    """
    name = "Site Speed Agent"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour le suivi de vitesse"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Table des mesures de vitesse
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS speed_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    url TEXT,
                    device TEXT DEFAULT 'mobile',
                    lcp REAL,
                    fid REAL,
                    cls REAL,
                    ttfb REAL,
                    fcp REAL,
                    speed_index REAL,
                    total_blocking_time REAL,
                    performance_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table des recommandations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS speed_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    category TEXT,
                    priority TEXT,
                    title TEXT,
                    description TEXT,
                    impact TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur init DB: {e}", "ERROR")

    def analyze_speed(self, client_id, url=None):
        """
        Analyse complete de la vitesse d'un site
        """
        log_agent(self.name, f"Analyse vitesse pour client {client_id}")

        if not url:
            url = self._get_client_url(client_id)

        if not url:
            return {'error': 'URL non trouvee'}

        # Simuler les metriques (en production, utiliser PageSpeed Insights API)
        metrics = self._measure_speed(url)

        # Sauvegarder les metriques
        self._save_metrics(client_id, url, metrics)

        # Generer les recommandations
        recommendations = self._generate_recommendations(metrics)

        # Sauvegarder les recommandations
        for rec in recommendations:
            self._save_recommendation(client_id, rec)

        # Score global
        score = self._calculate_score(metrics)

        result = {
            'client_id': client_id,
            'url': url,
            'metrics': metrics,
            'score': score,
            'grade': self._get_grade(score),
            'recommendations': recommendations,
            'core_web_vitals': {
                'lcp': {
                    'value': metrics.get('lcp', 0),
                    'unit': 's',
                    'status': self._get_cwv_status('lcp', metrics.get('lcp', 0))
                },
                'fid': {
                    'value': metrics.get('fid', 0),
                    'unit': 'ms',
                    'status': self._get_cwv_status('fid', metrics.get('fid', 0))
                },
                'cls': {
                    'value': metrics.get('cls', 0),
                    'unit': '',
                    'status': self._get_cwv_status('cls', metrics.get('cls', 0))
                }
            },
            'analyzed_at': datetime.now().isoformat()
        }

        log_agent(self.name, f"Analyse complete - Score: {score}")
        return result

    def _get_client_url(self, client_id):
        """Recupere l'URL du client"""
        site = SITES.get(client_id, {})
        if site:
            return f"https://{site.get('domaine', '')}"
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT domain FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return f"https://{row[0]}"
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def _measure_speed(self, url):
        """Mesure les metriques de vitesse (simulation)"""
        # En production, utiliser l'API PageSpeed Insights
        # Ici on genere des valeurs realistes avec l'IA

        prompt = f"""Tu es un expert en performance web. Estime les metriques de vitesse pour ce site:

URL: {url}

Genere des metriques realistes basees sur un site typique de cette industrie.

FORMAT JSON:
{{
    "lcp": 2.5,
    "fid": 100,
    "cls": 0.1,
    "ttfb": 0.8,
    "fcp": 1.8,
    "speed_index": 3.5,
    "total_blocking_time": 200,
    "dom_content_loaded": 1.5,
    "fully_loaded": 4.5,
    "page_size_kb": 1500,
    "requests": 45,
    "images_count": 15,
    "scripts_count": 8,
    "css_count": 3
}}

Notes:
- LCP (Largest Contentful Paint): en secondes, bon < 2.5s
- FID (First Input Delay): en ms, bon < 100ms
- CLS (Cumulative Layout Shift): sans unite, bon < 0.1
- TTFB (Time to First Byte): en secondes, bon < 0.8s
"""

        try:
            response = call_qwen(prompt, 1000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        # Fallback avec valeurs par defaut
        return {
            'lcp': 2.8,
            'fid': 120,
            'cls': 0.15,
            'ttfb': 0.9,
            'fcp': 2.0,
            'speed_index': 4.0,
            'total_blocking_time': 250,
            'dom_content_loaded': 1.8,
            'fully_loaded': 5.0,
            'page_size_kb': 2000,
            'requests': 50
        }

    def _save_metrics(self, client_id, url, metrics, device='mobile'):
        """Sauvegarde les metriques"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO speed_metrics
                (client_id, url, device, lcp, fid, cls, ttfb, fcp, speed_index, total_blocking_time, performance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, url, device,
                metrics.get('lcp', 0),
                metrics.get('fid', 0),
                metrics.get('cls', 0),
                metrics.get('ttfb', 0),
                metrics.get('fcp', 0),
                metrics.get('speed_index', 0),
                metrics.get('total_blocking_time', 0),
                self._calculate_score(metrics)
            ))
            conn.commit()
            conn.close()
        except:
            pass

    def _generate_recommendations(self, metrics):
        """Genere des recommandations basees sur les metriques"""
        recommendations = []

        # LCP
        if metrics.get('lcp', 0) > 2.5:
            recommendations.append({
                'category': 'lcp',
                'priority': 'high' if metrics['lcp'] > 4 else 'medium',
                'title': 'Optimiser le Largest Contentful Paint',
                'description': 'Le LCP est lent. Optimiser les images hero, utiliser le preload pour les ressources critiques.',
                'impact': f"Actuel: {metrics['lcp']}s - Cible: < 2.5s"
            })

        # FID
        if metrics.get('fid', 0) > 100:
            recommendations.append({
                'category': 'fid',
                'priority': 'high' if metrics['fid'] > 300 else 'medium',
                'title': 'Reduire le First Input Delay',
                'description': 'Le FID est eleve. Reduire le JavaScript bloquant, utiliser le code splitting.',
                'impact': f"Actuel: {metrics['fid']}ms - Cible: < 100ms"
            })

        # CLS
        if metrics.get('cls', 0) > 0.1:
            recommendations.append({
                'category': 'cls',
                'priority': 'high' if metrics['cls'] > 0.25 else 'medium',
                'title': 'Corriger le Cumulative Layout Shift',
                'description': 'Le CLS est trop eleve. Ajouter des dimensions aux images et iframes, eviter les insertions dynamiques.',
                'impact': f"Actuel: {metrics['cls']} - Cible: < 0.1"
            })

        # TTFB
        if metrics.get('ttfb', 0) > 0.8:
            recommendations.append({
                'category': 'server',
                'priority': 'medium',
                'title': 'Ameliorer le Time to First Byte',
                'description': 'Le serveur repond lentement. Optimiser le backend, utiliser du caching serveur.',
                'impact': f"Actuel: {metrics['ttfb']}s - Cible: < 0.8s"
            })

        # Page size
        if metrics.get('page_size_kb', 0) > 3000:
            recommendations.append({
                'category': 'size',
                'priority': 'medium',
                'title': 'Reduire la taille de la page',
                'description': 'La page est trop lourde. Compresser les images, minifier CSS/JS, utiliser la compression gzip.',
                'impact': f"Actuel: {metrics['page_size_kb']}KB - Cible: < 3000KB"
            })

        # Requests
        if metrics.get('requests', 0) > 60:
            recommendations.append({
                'category': 'requests',
                'priority': 'low',
                'title': 'Reduire le nombre de requetes',
                'description': 'Trop de requetes HTTP. Combiner les fichiers CSS/JS, utiliser des sprites images.',
                'impact': f"Actuel: {metrics['requests']} requetes - Cible: < 60"
            })

        return recommendations

    def _save_recommendation(self, client_id, rec):
        """Sauvegarde une recommandation"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO speed_recommendations
                (client_id, category, priority, title, description, impact)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                client_id,
                rec.get('category', ''),
                rec.get('priority', 'medium'),
                rec.get('title', ''),
                rec.get('description', ''),
                rec.get('impact', '')
            ))
            conn.commit()
            conn.close()
        except:
            pass

    def _calculate_score(self, metrics):
        """Calcule un score de performance global (0-100)"""
        score = 100

        # LCP scoring (25 points)
        lcp = metrics.get('lcp', 0)
        if lcp <= 2.5:
            score -= 0
        elif lcp <= 4:
            score -= 12
        else:
            score -= 25

        # FID scoring (25 points)
        fid = metrics.get('fid', 0)
        if fid <= 100:
            score -= 0
        elif fid <= 300:
            score -= 12
        else:
            score -= 25

        # CLS scoring (25 points)
        cls = metrics.get('cls', 0)
        if cls <= 0.1:
            score -= 0
        elif cls <= 0.25:
            score -= 12
        else:
            score -= 25

        # Other factors (25 points)
        ttfb = metrics.get('ttfb', 0)
        if ttfb > 1.5:
            score -= 10
        elif ttfb > 0.8:
            score -= 5

        if metrics.get('page_size_kb', 0) > 5000:
            score -= 10
        elif metrics.get('page_size_kb', 0) > 3000:
            score -= 5

        return max(0, min(100, score))

    def _get_grade(self, score):
        """Convertit un score en grade"""
        if score >= 90:
            return 'A'
        elif score >= 75:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 25:
            return 'D'
        return 'F'

    def _get_cwv_status(self, metric, value):
        """Determine le statut d'une metrique Core Web Vitals"""
        thresholds = {
            'lcp': {'good': 2.5, 'needs_improvement': 4.0},
            'fid': {'good': 100, 'needs_improvement': 300},
            'cls': {'good': 0.1, 'needs_improvement': 0.25}
        }

        if metric not in thresholds:
            return 'unknown'

        if value <= thresholds[metric]['good']:
            return 'good'
        elif value <= thresholds[metric]['needs_improvement']:
            return 'needs_improvement'
        return 'poor'

    def get_speed_history(self, client_id, days=30, device='mobile'):
        """Recupere l'historique des mesures de vitesse"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT lcp, fid, cls, ttfb, performance_score, created_at
                FROM speed_metrics
                WHERE client_id = ? AND device = ?
                AND created_at >= date('now', ?)
                ORDER BY created_at ASC
            ''', (client_id, device, f'-{days} days'))
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'lcp': r[0],
                    'fid': r[1],
                    'cls': r[2],
                    'ttfb': r[3],
                    'score': r[4],
                    'date': r[5]
                }
                for r in rows
            ]
        except:
            return []

    def get_recommendations(self, client_id, status=None):
        """Recupere les recommandations de vitesse"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT id, category, priority, title, description, impact, status, created_at
                FROM speed_recommendations WHERE client_id = ?
            '''
            params = [client_id]

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY CASE priority WHEN "high" THEN 1 WHEN "medium" THEN 2 ELSE 3 END'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'category': r[1],
                    'priority': r[2],
                    'title': r[3],
                    'description': r[4],
                    'impact': r[5],
                    'status': r[6],
                    'created_at': r[7]
                }
                for r in rows
            ]
        except:
            return []

    def update_recommendation_status(self, rec_id, status):
        """Met a jour le statut d'une recommandation"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE speed_recommendations SET status = ? WHERE id = ?', (status, rec_id))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def compare_with_competitors(self, client_id, competitor_urls):
        """Compare la vitesse avec les concurrents"""
        log_agent(self.name, f"Comparaison vitesse avec {len(competitor_urls)} concurrents")

        client_url = self._get_client_url(client_id)
        results = {
            'client': {
                'url': client_url,
                'metrics': self._measure_speed(client_url)
            },
            'competitors': [],
            'ranking': {}
        }

        results['client']['score'] = self._calculate_score(results['client']['metrics'])

        for comp_url in competitor_urls[:5]:
            metrics = self._measure_speed(comp_url)
            results['competitors'].append({
                'url': comp_url,
                'metrics': metrics,
                'score': self._calculate_score(metrics)
            })

        # Calculer le classement
        all_scores = [results['client']['score']] + [c['score'] for c in results['competitors']]
        all_scores.sort(reverse=True)
        results['ranking'] = {
            'position': all_scores.index(results['client']['score']) + 1,
            'total': len(all_scores),
            'percentile': int((1 - all_scores.index(results['client']['score']) / len(all_scores)) * 100)
        }

        return results

    def generate_speed_report(self, client_id):
        """Genere un rapport de vitesse complet"""
        client_url = self._get_client_url(client_id)

        # Derniere analyse
        analysis = self.analyze_speed(client_id, client_url)

        # Historique
        history = self.get_speed_history(client_id, 30)

        # Recommandations
        recommendations = self.get_recommendations(client_id, 'pending')

        # Tendances
        trends = {}
        if len(history) >= 2:
            trends = {
                'lcp': 'improving' if history[-1]['lcp'] < history[0]['lcp'] else 'declining',
                'fid': 'improving' if history[-1]['fid'] < history[0]['fid'] else 'declining',
                'cls': 'improving' if history[-1]['cls'] < history[0]['cls'] else 'declining',
                'score': 'improving' if history[-1]['score'] > history[0]['score'] else 'declining'
            }

        return {
            'client_id': client_id,
            'url': client_url,
            'current_analysis': analysis,
            'history': history,
            'trends': trends,
            'pending_recommendations': len(recommendations),
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }


# ============================================
# AGENT 43: ROI CALCULATOR AGENT
# ============================================
class ROICalculatorAgent:
    """
    Agent de calcul du ROI SEO
    Calcule et demontre la valeur des services SEO aux clients
    """
    name = "ROI Calculator Agent"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour le suivi ROI"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roi_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    period_start DATE,
                    period_end DATE,
                    seo_investment REAL,
                    revenue_generated REAL,
                    leads_generated INTEGER,
                    conversions INTEGER,
                    roi_percentage REAL,
                    calculation_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_revenue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    month TEXT,
                    organic_traffic INTEGER,
                    organic_leads INTEGER,
                    organic_revenue REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur init DB: {e}", "ERROR")

    def calculate_roi(self, client_id, params):
        """
        Calcule le ROI SEO
        params: {
            "monthly_seo_cost": 500,
            "months": 6,
            "avg_order_value": 200,
            "conversion_rate": 2.5,
            "organic_traffic_before": 1000,
            "organic_traffic_after": 2500
        }
        """
        log_agent(self.name, f"Calcul ROI pour client {client_id}")

        # Extraire les parametres
        monthly_cost = params.get('monthly_seo_cost', 500)
        months = params.get('months', 6)
        aov = params.get('avg_order_value', 100)
        conv_rate = params.get('conversion_rate', 2) / 100
        traffic_before = params.get('organic_traffic_before', 1000)
        traffic_after = params.get('organic_traffic_after', 2000)

        # Calculs
        total_investment = monthly_cost * months
        traffic_increase = traffic_after - traffic_before
        traffic_growth_percent = ((traffic_after - traffic_before) / traffic_before * 100) if traffic_before > 0 else 0

        # Leads et conversions
        leads_before = traffic_before * conv_rate
        leads_after = traffic_after * conv_rate
        additional_leads = leads_after - leads_before
        additional_leads_total = additional_leads * months

        # Revenus
        revenue_before = leads_before * aov
        revenue_after = leads_after * aov
        additional_revenue_monthly = revenue_after - revenue_before
        additional_revenue_total = additional_revenue_monthly * months

        # ROI
        roi = ((additional_revenue_total - total_investment) / total_investment * 100) if total_investment > 0 else 0
        payback_months = total_investment / additional_revenue_monthly if additional_revenue_monthly > 0 else float('inf')

        result = {
            'client_id': client_id,
            'period_months': months,
            'investment': {
                'monthly': monthly_cost,
                'total': total_investment
            },
            'traffic': {
                'before': traffic_before,
                'after': traffic_after,
                'increase': traffic_increase,
                'growth_percent': round(traffic_growth_percent, 1)
            },
            'leads': {
                'before_monthly': round(leads_before, 1),
                'after_monthly': round(leads_after, 1),
                'additional_monthly': round(additional_leads, 1),
                'additional_total': round(additional_leads_total, 1)
            },
            'revenue': {
                'before_monthly': round(revenue_before, 2),
                'after_monthly': round(revenue_after, 2),
                'additional_monthly': round(additional_revenue_monthly, 2),
                'additional_total': round(additional_revenue_total, 2)
            },
            'roi': {
                'percentage': round(roi, 1),
                'multiplier': round((additional_revenue_total / total_investment), 2) if total_investment > 0 else 0,
                'payback_months': round(payback_months, 1) if payback_months != float('inf') else None
            },
            'summary': self._generate_summary(roi, additional_revenue_total, total_investment, payback_months),
            'calculated_at': datetime.now().isoformat()
        }

        # Sauvegarder
        self._save_calculation(client_id, result)

        log_agent(self.name, f"ROI calcule: {roi:.1f}%")
        return result

    def _generate_summary(self, roi, revenue, investment, payback):
        """Genere un resume du ROI"""
        if roi > 200:
            verdict = "Excellent"
            emoji = "Votre investissement SEO genere des resultats exceptionnels."
        elif roi > 100:
            verdict = "Tres bon"
            emoji = "Votre investissement SEO est tres rentable."
        elif roi > 50:
            verdict = "Bon"
            emoji = "Votre investissement SEO est rentable."
        elif roi > 0:
            verdict = "Positif"
            emoji = "Votre investissement SEO commence a porter ses fruits."
        else:
            verdict = "En construction"
            emoji = "Le SEO prend du temps. Les resultats viendront."

        return {
            'verdict': verdict,
            'message': emoji,
            'key_stat': f"Pour chaque ${investment:.0f} investi, vous generez ${revenue:.0f} de revenus supplementaires.",
            'payback_message': f"Votre investissement est recupere en {payback:.1f} mois." if payback and payback != float('inf') else "Continuez a investir pour atteindre la rentabilite."
        }

    def _save_calculation(self, client_id, result):
        """Sauvegarde le calcul ROI"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO roi_calculations
                (client_id, seo_investment, revenue_generated, leads_generated, roi_percentage, calculation_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                client_id,
                result['investment']['total'],
                result['revenue']['additional_total'],
                int(result['leads']['additional_total']),
                result['roi']['percentage'],
                json.dumps(result, ensure_ascii=False)
            ))
            conn.commit()
            conn.close()
        except:
            pass

    def estimate_potential_roi(self, client_id, target_traffic_increase=50):
        """Estime le ROI potentiel basé sur une augmentation de trafic cible"""
        log_agent(self.name, f"Estimation ROI potentiel pour client {client_id}")

        # Obtenir infos client
        client_info = self._get_client_info(client_id)
        niche = client_info.get('niche', '')

        # Estimer les metriques avec IA
        prompt = f"""Tu es un expert SEO. Estime les metriques business pour ce type d'entreprise:

NICHE: {niche}
REGION: Quebec/Canada

Estime des valeurs realistes pour:
- Valeur moyenne d'une commande/contrat
- Taux de conversion visiteur -> lead
- Taux de conversion lead -> client
- Trafic organique mensuel typique

FORMAT JSON:
{{
    "avg_order_value": 500,
    "visitor_to_lead_rate": 3,
    "lead_to_client_rate": 25,
    "typical_monthly_traffic": 1500,
    "industry_avg_cpc": 2.50
}}
"""

        try:
            response = call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                metrics = json.loads(response.strip())
        except:
            metrics = {
                'avg_order_value': 300,
                'visitor_to_lead_rate': 2.5,
                'lead_to_client_rate': 20,
                'typical_monthly_traffic': 1000,
                'industry_avg_cpc': 2.0
            }

        # Calculer le potentiel
        current_traffic = metrics.get('typical_monthly_traffic', 1000)
        target_traffic = current_traffic * (1 + target_traffic_increase / 100)
        traffic_increase = target_traffic - current_traffic

        conv_rate = metrics.get('visitor_to_lead_rate', 2.5) / 100
        close_rate = metrics.get('lead_to_client_rate', 20) / 100
        aov = metrics.get('avg_order_value', 300)
        cpc = metrics.get('industry_avg_cpc', 2.0)

        additional_leads = traffic_increase * conv_rate
        additional_clients = additional_leads * close_rate
        additional_revenue = additional_clients * aov

        # Valeur du trafic en equivalent PPC
        ppc_equivalent = traffic_increase * cpc

        return {
            'client_id': client_id,
            'niche': niche,
            'target_growth': f"{target_traffic_increase}%",
            'current_estimates': {
                'monthly_traffic': current_traffic,
                'avg_order_value': aov,
                'visitor_to_lead_rate': f"{metrics.get('visitor_to_lead_rate', 2.5)}%",
                'lead_to_client_rate': f"{metrics.get('lead_to_client_rate', 20)}%"
            },
            'potential': {
                'target_traffic': int(target_traffic),
                'additional_traffic': int(traffic_increase),
                'additional_leads_monthly': round(additional_leads, 1),
                'additional_clients_monthly': round(additional_clients, 1),
                'additional_revenue_monthly': round(additional_revenue, 2),
                'additional_revenue_yearly': round(additional_revenue * 12, 2),
                'ppc_equivalent_monthly': round(ppc_equivalent, 2),
                'ppc_equivalent_yearly': round(ppc_equivalent * 12, 2)
            },
            'message': f"Avec une augmentation de {target_traffic_increase}% du trafic, vous pourriez generer ${additional_revenue:.0f} de revenus supplementaires par mois."
        }

    def _get_client_info(self, client_id):
        """Recupere les infos du client"""
        site = SITES.get(client_id, {})
        if site:
            return site
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT company_name, domain, niche FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {'nom': row[0], 'domaine': row[1], 'niche': row[2]}
        except:
            pass
        return {}

    def get_roi_history(self, client_id, limit=12):
        """Recupere l'historique des calculs ROI"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, seo_investment, revenue_generated, leads_generated, roi_percentage, created_at
                FROM roi_calculations WHERE client_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (client_id, limit))
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'investment': r[1],
                    'revenue': r[2],
                    'leads': r[3],
                    'roi_percentage': r[4],
                    'date': r[5]
                }
                for r in rows
            ]
        except:
            return []

    def calculate_keyword_value(self, keywords, client_id=None):
        """Calcule la valeur monetaire des mots-cles"""
        log_agent(self.name, f"Calcul valeur de {len(keywords)} mots-cles")

        prompt = f"""Tu es un expert SEO et PPC. Estime la valeur de ces mots-cles:

MOTS-CLES:
{chr(10).join([f"- {kw}" for kw in keywords[:15]])}

Pour chaque mot-cle, estime:
- CPC moyen (Google Ads)
- Volume de recherche mensuel
- Valeur business (potentiel de conversion)

FORMAT JSON:
{{
    "keywords": [
        {{
            "keyword": "...",
            "monthly_volume": 1000,
            "cpc": 2.50,
            "business_value": "high|medium|low",
            "monthly_traffic_value": 2500
        }}
    ],
    "total_monthly_value": 10000,
    "total_yearly_value": 120000
}}
"""

        try:
            response = call_qwen(prompt, 2000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {'keywords': [], 'total_monthly_value': 0}

    def generate_roi_report(self, client_id, params):
        """Genere un rapport ROI complet pour presentation client"""
        log_agent(self.name, f"Generation rapport ROI pour client {client_id}")

        # Calcul ROI actuel
        roi = self.calculate_roi(client_id, params)

        # Estimation potentiel
        potential = self.estimate_potential_roi(client_id, 100)

        # Historique
        history = self.get_roi_history(client_id, 6)

        # Projections
        projections = self._generate_projections(params, 12)

        report = {
            'client_id': client_id,
            'current_roi': roi,
            'potential': potential,
            'history': history,
            'projections': projections,
            'key_metrics': {
                'total_investment': roi['investment']['total'],
                'total_return': roi['revenue']['additional_total'],
                'roi_percentage': roi['roi']['percentage'],
                'payback_period': roi['roi'].get('payback_months')
            },
            'generated_at': datetime.now().isoformat()
        }

        return report

    def _generate_projections(self, params, months=12):
        """Genere des projections sur plusieurs mois"""
        projections = []
        monthly_cost = params.get('monthly_seo_cost', 500)
        traffic = params.get('organic_traffic_before', 1000)
        conv_rate = params.get('conversion_rate', 2) / 100
        aov = params.get('avg_order_value', 100)

        # Croissance mensuelle estimee (compose)
        monthly_growth = 0.08  # 8% par mois

        cumulative_investment = 0
        cumulative_revenue = 0

        for month in range(1, months + 1):
            traffic = traffic * (1 + monthly_growth)
            leads = traffic * conv_rate
            revenue = leads * aov

            cumulative_investment += monthly_cost
            cumulative_revenue += revenue

            roi = ((cumulative_revenue - cumulative_investment) / cumulative_investment * 100) if cumulative_investment > 0 else 0

            projections.append({
                'month': month,
                'traffic': int(traffic),
                'leads': round(leads, 1),
                'monthly_revenue': round(revenue, 2),
                'cumulative_investment': round(cumulative_investment, 2),
                'cumulative_revenue': round(cumulative_revenue, 2),
                'roi_percentage': round(roi, 1)
            })

        return projections


# ============================================
# AGENT 44: COMPETITOR WATCH AGENT
# ============================================
class CompetitorWatchAgent:
    """
    Agent de surveillance concurrentielle
    Monitore les changements chez les concurrents (contenu, keywords, backlinks)
    """
    name = "Competitor Watch Agent"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour la surveillance concurrentielle"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Concurrents suivis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watched_competitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    competitor_domain TEXT,
                    competitor_name TEXT,
                    notes TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_id, competitor_domain)
                )
            ''')

            # Snapshots des concurrents
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competitor_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER,
                    snapshot_type TEXT,
                    data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Alertes de changements
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competitor_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    competitor_id INTEGER,
                    alert_type TEXT,
                    severity TEXT,
                    title TEXT,
                    description TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            log_agent(self.name, f"Erreur init DB: {e}", "ERROR")

    def add_competitor(self, client_id, competitor_domain, competitor_name='', notes=''):
        """Ajoute un concurrent a surveiller"""
        log_agent(self.name, f"Ajout concurrent: {competitor_domain}")

        # Nettoyer le domaine
        competitor_domain = competitor_domain.replace('https://', '').replace('http://', '').strip('/')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO watched_competitors (client_id, competitor_domain, competitor_name, notes)
                VALUES (?, ?, ?, ?)
            ''', (client_id, competitor_domain, competitor_name or competitor_domain, notes))

            competitor_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Faire un premier snapshot
            if competitor_id:
                self._take_snapshot(competitor_id, competitor_domain)

            return {
                'success': True,
                'competitor_id': competitor_id,
                'domain': competitor_domain
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def remove_competitor(self, competitor_id):
        """Retire un concurrent de la surveillance"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE watched_competitors SET is_active = 0 WHERE id = ?', (competitor_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_competitors(self, client_id):
        """Liste les concurrents surveilles"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, competitor_domain, competitor_name, notes, created_at
                FROM watched_competitors
                WHERE client_id = ? AND is_active = 1
                ORDER BY created_at DESC
            ''', (client_id,))
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'domain': r[1],
                    'name': r[2],
                    'notes': r[3],
                    'added_at': r[4]
                }
                for r in rows
            ]
        except:
            return []

    def _take_snapshot(self, competitor_id, domain):
        """Prend un snapshot de l'etat actuel du concurrent"""
        # Snapshot SEO
        seo_data = self._analyze_competitor_seo(domain)
        self._save_snapshot(competitor_id, 'seo', seo_data)

        # Snapshot contenu
        content_data = self._analyze_competitor_content(domain)
        self._save_snapshot(competitor_id, 'content', content_data)

        return True

    def _save_snapshot(self, competitor_id, snapshot_type, data):
        """Sauvegarde un snapshot"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO competitor_snapshots (competitor_id, snapshot_type, data_json)
                VALUES (?, ?, ?)
            ''', (competitor_id, snapshot_type, json.dumps(data, ensure_ascii=False)))
            conn.commit()
            conn.close()
        except:
            pass

    def _analyze_competitor_seo(self, domain):
        """Analyse SEO d'un concurrent"""
        prompt = f"""Tu es un expert SEO. Analyse ce site concurrent:

DOMAINE: {domain}

Estime:
1. Mots-cles principaux cibles (10-15)
2. Autorite de domaine estimee (1-100)
3. Nombre de pages indexees estime
4. Qualite du contenu (1-10)
5. Optimisation technique (1-10)

FORMAT JSON:
{{
    "domain": "{domain}",
    "domain_authority": 45,
    "indexed_pages": 150,
    "content_quality": 7,
    "technical_score": 8,
    "main_keywords": [
        {{"keyword": "...", "estimated_position": 1-20}}
    ],
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."]
}}
"""

        try:
            response = call_qwen(prompt, 1500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {'domain': domain, 'error': 'Analyse impossible'}

    def _analyze_competitor_content(self, domain):
        """Analyse le contenu d'un concurrent"""
        prompt = f"""Tu es un expert en content marketing. Analyse le contenu de ce site:

DOMAINE: {domain}

Estime:
1. Types de contenu publies (blog, guides, videos, etc.)
2. Frequence de publication estimee
3. Sujets principaux couverts
4. Qualite generale du contenu
5. Engagement estime

FORMAT JSON:
{{
    "content_types": ["blog", "guides", "faq"],
    "publishing_frequency": "2-3 articles/semaine",
    "main_topics": ["topic1", "topic2"],
    "content_length_avg": "1500 mots",
    "quality_score": 7,
    "recent_posts": [
        {{"title": "...", "topic": "...", "estimated_date": "recent"}}
    ]
}}
"""

        try:
            response = call_qwen(prompt, 1200)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass

        return {'error': 'Analyse impossible'}

    def check_for_changes(self, client_id):
        """Verifie les changements chez tous les concurrents"""
        log_agent(self.name, f"Verification changements pour client {client_id}")

        competitors = self.get_competitors(client_id)
        changes = []

        for comp in competitors:
            # Obtenir le dernier snapshot
            last_snapshot = self._get_last_snapshot(comp['id'], 'seo')

            # Nouveau snapshot
            current_seo = self._analyze_competitor_seo(comp['domain'])

            # Comparer
            detected_changes = self._compare_snapshots(last_snapshot, current_seo, comp)

            if detected_changes:
                changes.extend(detected_changes)

                # Sauvegarder le nouveau snapshot
                self._save_snapshot(comp['id'], 'seo', current_seo)

                # Creer des alertes
                for change in detected_changes:
                    self._create_alert(client_id, comp['id'], change)

        return {
            'client_id': client_id,
            'competitors_checked': len(competitors),
            'changes_detected': len(changes),
            'changes': changes
        }

    def _get_last_snapshot(self, competitor_id, snapshot_type):
        """Recupere le dernier snapshot"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_json FROM competitor_snapshots
                WHERE competitor_id = ? AND snapshot_type = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (competitor_id, snapshot_type))
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
        except Exception as e:
            import logging
            logging.warning(f'_call_ai error: {e}')
            return None

    def _compare_snapshots(self, old_snapshot, new_snapshot, competitor):
        """Compare deux snapshots et detecte les changements"""
        changes = []

        if not old_snapshot:
            return []

        # Changement d'autorite
        old_da = old_snapshot.get('domain_authority', 0)
        new_da = new_snapshot.get('domain_authority', 0)
        if abs(new_da - old_da) >= 5:
            changes.append({
                'type': 'authority_change',
                'severity': 'medium',
                'title': f"Changement d'autorite chez {competitor['name']}",
                'description': f"DA passe de {old_da} a {new_da}",
                'old_value': old_da,
                'new_value': new_da
            })

        # Nouveaux mots-cles
        old_keywords = set(k['keyword'] for k in old_snapshot.get('main_keywords', []))
        new_keywords = set(k['keyword'] for k in new_snapshot.get('main_keywords', []))
        new_kws = new_keywords - old_keywords
        if new_kws:
            changes.append({
                'type': 'new_keywords',
                'severity': 'high',
                'title': f"Nouveaux mots-cles chez {competitor['name']}",
                'description': f"Nouveaux keywords detectes: {', '.join(list(new_kws)[:5])}",
                'keywords': list(new_kws)
            })

        # Changement de pages indexees
        old_pages = old_snapshot.get('indexed_pages', 0)
        new_pages = new_snapshot.get('indexed_pages', 0)
        if new_pages > old_pages * 1.2:  # +20% de pages
            changes.append({
                'type': 'content_growth',
                'severity': 'medium',
                'title': f"Croissance du contenu chez {competitor['name']}",
                'description': f"Pages indexees: {old_pages} -> {new_pages}",
                'growth_percent': round((new_pages - old_pages) / old_pages * 100, 1) if old_pages > 0 else 0
            })

        return changes

    def _create_alert(self, client_id, competitor_id, change):
        """Cree une alerte de changement"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO competitor_alerts
                (client_id, competitor_id, alert_type, severity, title, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                client_id,
                competitor_id,
                change.get('type', 'unknown'),
                change.get('severity', 'low'),
                change.get('title', ''),
                change.get('description', '')
            ))
            conn.commit()
            conn.close()
        except:
            pass

    def get_alerts(self, client_id, unread_only=True):
        """Recupere les alertes concurrentielles"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT ca.id, ca.alert_type, ca.severity, ca.title, ca.description,
                       ca.is_read, ca.created_at, wc.competitor_domain
                FROM competitor_alerts ca
                JOIN watched_competitors wc ON ca.competitor_id = wc.id
                WHERE ca.client_id = ?
            '''
            params = [client_id]

            if unread_only:
                query += ' AND ca.is_read = 0'

            query += ' ORDER BY ca.created_at DESC LIMIT 50'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': r[0],
                    'type': r[1],
                    'severity': r[2],
                    'title': r[3],
                    'description': r[4],
                    'is_read': bool(r[5]),
                    'created_at': r[6],
                    'competitor': r[7]
                }
                for r in rows
            ]
        except:
            return []

    def mark_alerts_read(self, alert_ids):
        """Marque les alertes comme lues"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(alert_ids))
            cursor.execute(f'UPDATE competitor_alerts SET is_read = 1 WHERE id IN ({placeholders})', alert_ids)
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_competitor_profile(self, competitor_id):
        """Profil complet d'un concurrent"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Info concurrent
            cursor.execute('SELECT competitor_domain, competitor_name, notes FROM watched_competitors WHERE id = ?', (competitor_id,))
            comp = cursor.fetchone()

            if not comp:
                return {'error': 'Concurrent non trouve'}

            # Derniers snapshots
            cursor.execute('''
                SELECT snapshot_type, data_json, created_at
                FROM competitor_snapshots WHERE competitor_id = ?
                ORDER BY created_at DESC LIMIT 5
            ''', (competitor_id,))
            snapshots = cursor.fetchall()
            conn.close()

            profile = {
                'id': competitor_id,
                'domain': comp[0],
                'name': comp[1],
                'notes': comp[2],
                'snapshots': {}
            }

            for snap in snapshots:
                if snap[0] not in profile['snapshots']:
                    profile['snapshots'][snap[0]] = {
                        'data': json.loads(snap[1]),
                        'date': snap[2]
                    }

            return profile
        except Exception as e:
            return {'error': str(e)}

    def compare_with_client(self, client_id, competitor_id):
        """Compare un concurrent avec le client"""
        log_agent(self.name, f"Comparaison client {client_id} vs concurrent {competitor_id}")

        # Info client
        client_domain = self._get_client_domain(client_id)
        client_niche = self._get_client_niche(client_id)

        # Info concurrent
        profile = self.get_competitor_profile(competitor_id)
        if 'error' in profile:
            return profile

        competitor_domain = profile.get('domain', '')

        prompt = f"""Tu es un expert SEO. Compare ces deux sites:

CLIENT: {client_domain}
CONCURRENT: {competitor_domain}
NICHE: {client_niche}

Analyse et compare:
1. Forces et faiblesses de chacun
2. Opportunites pour le client
3. Menaces du concurrent
4. Recommandations strategiques

FORMAT JSON:
{{
    "client_strengths": ["...", "..."],
    "client_weaknesses": ["...", "..."],
    "competitor_strengths": ["...", "..."],
    "competitor_weaknesses": ["...", "..."],
    "opportunities": ["...", "..."],
    "threats": ["...", "..."],
    "recommendations": [
        {{"priority": "high|medium|low", "action": "...", "expected_impact": "..."}}
    ],
    "competitive_gap": {{
        "keywords_to_target": ["...", "..."],
        "content_to_create": ["...", "..."],
        "technical_improvements": ["...", "..."]
    }}
}}
"""

        try:
            response = call_qwen(prompt, 2500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                analysis = json.loads(response.strip())

                return {
                    'client': {'domain': client_domain},
                    'competitor': {'domain': competitor_domain, 'name': profile.get('name', '')},
                    'analysis': analysis,
                    'analyzed_at': datetime.now().isoformat()
                }
        except:
            pass

        return {'error': 'Comparaison impossible'}

    def _get_client_domain(self, client_id):
        """Recupere le domaine du client"""
        site = SITES.get(client_id, {})
        if site:
            return site.get('domaine', '')
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT domain FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except:
            pass
        return ''

    def _get_client_niche(self, client_id):
        """Recupere la niche du client"""
        site = SITES.get(client_id, {})
        if site:
            return site.get('niche', '')
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT niche FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except:
            pass
        return ''

    def generate_competitive_report(self, client_id):
        """Genere un rapport concurrentiel complet"""
        log_agent(self.name, f"Generation rapport concurrentiel pour client {client_id}")

        competitors = self.get_competitors(client_id)
        client_domain = self._get_client_domain(client_id)

        report = {
            'client_id': client_id,
            'client_domain': client_domain,
            'competitors_count': len(competitors),
            'competitors': [],
            'summary': {},
            'generated_at': datetime.now().isoformat()
        }

        total_da = 0
        all_keywords = set()

        for comp in competitors[:5]:  # Max 5 concurrents
            profile = self.get_competitor_profile(comp['id'])
            seo_data = profile.get('snapshots', {}).get('seo', {}).get('data', {})

            comp_summary = {
                'domain': comp['domain'],
                'name': comp['name'],
                'domain_authority': seo_data.get('domain_authority', 0),
                'indexed_pages': seo_data.get('indexed_pages', 0),
                'main_keywords': [k['keyword'] for k in seo_data.get('main_keywords', [])[:5]],
                'strengths': seo_data.get('strengths', []),
                'weaknesses': seo_data.get('weaknesses', [])
            }

            report['competitors'].append(comp_summary)
            total_da += comp_summary['domain_authority']
            all_keywords.update(comp_summary['main_keywords'])

        # Resume
        if competitors:
            report['summary'] = {
                'avg_competitor_da': round(total_da / len(competitors), 1),
                'total_keywords_tracked': len(all_keywords),
                'top_competitor_keywords': list(all_keywords)[:10],
                'market_position': 'A evaluer'
            }

        # Alertes recentes
        report['recent_alerts'] = self.get_alerts(client_id, unread_only=False)[:10]

        return report


# =============================================================================
# AGENT 45: LOCAL SEO AGENT - Optimisation SEO Local
# =============================================================================
class LocalSEOAgent:
    """Agent specialise dans le SEO local: Google Business, citations NAP, avis"""

    def __init__(self):
        self.name = "LocalSEOAgent"
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour le SEO local"""
        conn = get_db()
        cursor = conn.cursor()

        # Profils Google Business
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS google_business_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                business_name TEXT,
                address TEXT,
                city TEXT,
                province TEXT,
                postal_code TEXT,
                phone TEXT,
                website TEXT,
                category TEXT,
                secondary_categories TEXT,
                hours_json TEXT,
                attributes_json TEXT,
                gmb_url TEXT,
                place_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Citations NAP (Name, Address, Phone)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nap_citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                source_name TEXT,
                source_url TEXT,
                listed_name TEXT,
                listed_address TEXT,
                listed_phone TEXT,
                is_consistent BOOLEAN DEFAULT 1,
                issues TEXT,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Avis clients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS local_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                platform TEXT,
                reviewer_name TEXT,
                rating INTEGER,
                review_text TEXT,
                review_date TEXT,
                response_text TEXT,
                response_date TEXT,
                sentiment TEXT,
                keywords_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Zones de service
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                area_name TEXT,
                area_type TEXT,
                population INTEGER,
                competition_level TEXT,
                priority INTEGER DEFAULT 5,
                landing_page_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def create_gmb_profile(self, client_id, profile_data):
        """Cree ou met a jour le profil Google Business"""
        log_agent(self.name, f"Creation profil GMB pour client {client_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            # Verifie si existe deja
            cursor.execute('SELECT id FROM google_business_profiles WHERE client_id = ?', (client_id,))
            existing = cursor.fetchone()

            hours_json = json.dumps(profile_data.get('hours', {}))
            attributes_json = json.dumps(profile_data.get('attributes', []))
            secondary_cats = ','.join(profile_data.get('secondary_categories', []))

            if existing:
                cursor.execute('''
                    UPDATE google_business_profiles SET
                        business_name = ?, address = ?, city = ?, province = ?,
                        postal_code = ?, phone = ?, website = ?, category = ?,
                        secondary_categories = ?, hours_json = ?, attributes_json = ?,
                        gmb_url = ?, place_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE client_id = ?
                ''', (
                    profile_data.get('business_name'), profile_data.get('address'),
                    profile_data.get('city'), profile_data.get('province'),
                    profile_data.get('postal_code'), profile_data.get('phone'),
                    profile_data.get('website'), profile_data.get('category'),
                    secondary_cats, hours_json, attributes_json,
                    profile_data.get('gmb_url'), profile_data.get('place_id'),
                    client_id
                ))
                profile_id = existing[0]
            else:
                cursor.execute('''
                    INSERT INTO google_business_profiles
                    (client_id, business_name, address, city, province, postal_code,
                     phone, website, category, secondary_categories, hours_json,
                     attributes_json, gmb_url, place_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    client_id, profile_data.get('business_name'), profile_data.get('address'),
                    profile_data.get('city'), profile_data.get('province'),
                    profile_data.get('postal_code'), profile_data.get('phone'),
                    profile_data.get('website'), profile_data.get('category'),
                    secondary_cats, hours_json, attributes_json,
                    profile_data.get('gmb_url'), profile_data.get('place_id')
                ))
                profile_id = cursor.lastrowid

            conn.commit()
            conn.close()

            return {'success': True, 'profile_id': profile_id}
        except Exception as e:
            return {'error': str(e)}

    def get_gmb_profile(self, client_id):
        """Recupere le profil GMB du client"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM google_business_profiles WHERE client_id = ?
            ''', (client_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'client_id': row[1],
                    'business_name': row[2],
                    'address': row[3],
                    'city': row[4],
                    'province': row[5],
                    'postal_code': row[6],
                    'phone': row[7],
                    'website': row[8],
                    'category': row[9],
                    'secondary_categories': row[10].split(',') if row[10] else [],
                    'hours': json.loads(row[11]) if row[11] else {},
                    'attributes': json.loads(row[12]) if row[12] else [],
                    'gmb_url': row[13],
                    'place_id': row[14]
                }
            return None
        except Exception as e:
            return {'error': str(e)}

    def audit_gmb_profile(self, client_id):
        """Audit complet du profil GMB"""
        log_agent(self.name, f"Audit GMB pour client {client_id}")

        profile = self.get_gmb_profile(client_id)
        if not profile or 'error' in profile:
            return {'error': 'Profil GMB non trouve'}

        issues = []
        score = 100
        recommendations = []

        # Verification des champs obligatoires
        required_fields = ['business_name', 'address', 'city', 'phone', 'category']
        for field in required_fields:
            if not profile.get(field):
                issues.append(f"Champ manquant: {field}")
                score -= 15

        # Verification des heures d'ouverture
        hours = profile.get('hours', {})
        if not hours:
            issues.append("Heures d'ouverture non definies")
            score -= 10
            recommendations.append("Ajoutez vos heures d'ouverture pour ameliorer la visibilite")

        # Categories secondaires
        if len(profile.get('secondary_categories', [])) < 2:
            issues.append("Peu de categories secondaires")
            score -= 5
            recommendations.append("Ajoutez 2-3 categories secondaires pertinentes")

        # Attributs
        if len(profile.get('attributes', [])) < 5:
            issues.append("Peu d'attributs definis")
            score -= 5
            recommendations.append("Ajoutez des attributs (wifi, stationnement, accessibilite, etc.)")

        # Site web
        if not profile.get('website'):
            issues.append("Site web non lie")
            score -= 10
            recommendations.append("Liez votre site web au profil GMB")

        return {
            'profile': profile,
            'score': max(0, score),
            'issues': issues,
            'recommendations': recommendations,
            'audit_date': datetime.now().isoformat()
        }

    def add_citation(self, client_id, citation_data):
        """Ajoute une citation NAP"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO nap_citations
                (client_id, source_name, source_url, listed_name, listed_address,
                 listed_phone, is_consistent, issues, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                client_id, citation_data.get('source_name'),
                citation_data.get('source_url'), citation_data.get('listed_name'),
                citation_data.get('listed_address'), citation_data.get('listed_phone'),
                citation_data.get('is_consistent', True),
                citation_data.get('issues', '')
            ))

            conn.commit()
            citation_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'citation_id': citation_id}
        except Exception as e:
            return {'error': str(e)}

    def get_citations(self, client_id):
        """Recupere toutes les citations d'un client"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_name, source_url, listed_name, listed_address,
                       listed_phone, is_consistent, issues, last_checked
                FROM nap_citations WHERE client_id = ?
                ORDER BY source_name
            ''', (client_id,))
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'source_name': r[1],
                'source_url': r[2],
                'listed_name': r[3],
                'listed_address': r[4],
                'listed_phone': r[5],
                'is_consistent': bool(r[6]),
                'issues': r[7],
                'last_checked': r[8]
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def audit_nap_consistency(self, client_id):
        """Verifie la coherence NAP sur toutes les citations"""
        log_agent(self.name, f"Audit NAP pour client {client_id}")

        profile = self.get_gmb_profile(client_id)
        citations = self.get_citations(client_id)

        if not profile:
            return {'error': 'Profil GMB requis pour audit NAP'}

        if isinstance(citations, dict) and 'error' in citations:
            return citations

        # Reference NAP du profil GMB
        ref_name = profile.get('business_name', '').lower().strip()
        ref_address = profile.get('address', '').lower().strip()
        ref_phone = ''.join(filter(str.isdigit, profile.get('phone', '')))

        consistent_count = 0
        inconsistent = []

        for citation in citations:
            issues = []

            # Compare name
            c_name = citation.get('listed_name', '').lower().strip()
            if c_name and c_name != ref_name:
                issues.append(f"Nom different: '{citation.get('listed_name')}'")

            # Compare address
            c_addr = citation.get('listed_address', '').lower().strip()
            if c_addr and c_addr != ref_address:
                issues.append(f"Adresse differente")

            # Compare phone
            c_phone = ''.join(filter(str.isdigit, citation.get('listed_phone', '')))
            if c_phone and c_phone != ref_phone:
                issues.append(f"Telephone different: '{citation.get('listed_phone')}'")

            if issues:
                inconsistent.append({
                    'citation': citation,
                    'issues': issues
                })
            else:
                consistent_count += 1

        total = len(citations)
        consistency_score = round((consistent_count / total * 100) if total > 0 else 0, 1)

        return {
            'total_citations': total,
            'consistent': consistent_count,
            'inconsistent_count': len(inconsistent),
            'consistency_score': consistency_score,
            'inconsistent_citations': inconsistent,
            'reference_nap': {
                'name': profile.get('business_name'),
                'address': profile.get('address'),
                'phone': profile.get('phone')
            },
            'audit_date': datetime.now().isoformat()
        }

    def add_review(self, client_id, review_data):
        """Ajoute un avis client"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            keywords_json = json.dumps(review_data.get('keywords', []))

            cursor.execute('''
                INSERT INTO local_reviews
                (client_id, platform, reviewer_name, rating, review_text,
                 review_date, response_text, response_date, sentiment, keywords_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, review_data.get('platform', 'Google'),
                review_data.get('reviewer_name'), review_data.get('rating'),
                review_data.get('review_text'), review_data.get('review_date'),
                review_data.get('response_text'), review_data.get('response_date'),
                review_data.get('sentiment'), keywords_json
            ))

            conn.commit()
            review_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'review_id': review_id}
        except Exception as e:
            return {'error': str(e)}

    def get_reviews(self, client_id, platform=None):
        """Recupere les avis d'un client"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            if platform:
                cursor.execute('''
                    SELECT id, platform, reviewer_name, rating, review_text,
                           review_date, response_text, response_date, sentiment
                    FROM local_reviews WHERE client_id = ? AND platform = ?
                    ORDER BY review_date DESC
                ''', (client_id, platform))
            else:
                cursor.execute('''
                    SELECT id, platform, reviewer_name, rating, review_text,
                           review_date, response_text, response_date, sentiment
                    FROM local_reviews WHERE client_id = ?
                    ORDER BY review_date DESC
                ''', (client_id,))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'platform': r[1],
                'reviewer_name': r[2],
                'rating': r[3],
                'review_text': r[4],
                'review_date': r[5],
                'response_text': r[6],
                'response_date': r[7],
                'sentiment': r[8]
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def analyze_reviews(self, client_id):
        """Analyse complete des avis"""
        log_agent(self.name, f"Analyse des avis pour client {client_id}")

        reviews = self.get_reviews(client_id)
        if isinstance(reviews, dict) and 'error' in reviews:
            return reviews

        if not reviews:
            return {'message': 'Aucun avis trouve'}

        total = len(reviews)
        ratings = [r['rating'] for r in reviews if r['rating']]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

        # Distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in ratings:
            if r in distribution:
                distribution[r] += 1

        # Avis sans reponse
        unanswered = [r for r in reviews if not r['response_text']]

        # Sentiments
        sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
        for r in reviews:
            s = r.get('sentiment', 'neutral')
            if s in sentiments:
                sentiments[s] += 1

        # Par plateforme
        by_platform = {}
        for r in reviews:
            p = r['platform']
            if p not in by_platform:
                by_platform[p] = {'count': 0, 'total_rating': 0}
            by_platform[p]['count'] += 1
            if r['rating']:
                by_platform[p]['total_rating'] += r['rating']

        for p in by_platform:
            if by_platform[p]['count'] > 0:
                by_platform[p]['avg_rating'] = round(
                    by_platform[p]['total_rating'] / by_platform[p]['count'], 2
                )

        return {
            'total_reviews': total,
            'average_rating': avg_rating,
            'rating_distribution': distribution,
            'unanswered_count': len(unanswered),
            'sentiments': sentiments,
            'by_platform': by_platform,
            'needs_response': unanswered[:5],
            'analyzed_at': datetime.now().isoformat()
        }

    def generate_review_response(self, client_id, review_id):
        """Genere une reponse IA pour un avis"""
        log_agent(self.name, f"Generation reponse avis {review_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT reviewer_name, rating, review_text, platform
                FROM local_reviews WHERE id = ? AND client_id = ?
            ''', (review_id, client_id))
            review = cursor.fetchone()
            conn.close()

            if not review:
                return {'error': 'Avis non trouve'}

            profile = self.get_gmb_profile(client_id)
            business_name = profile.get('business_name', 'notre entreprise') if profile else 'notre entreprise'

            reviewer_name = review[0] or 'Client'
            rating = review[1]
            review_text = review[2] or ''
            platform = review[3]

            if rating >= 4:
                tone = "chaleureux et reconnaissant"
            elif rating == 3:
                tone = "professionnel et constructif"
            else:
                tone = "empathique et resolutif"

            prompt = f"""Tu es le responsable de {business_name}. Redige une reponse {tone} a cet avis:

PLATEFORME: {platform}
CLIENT: {reviewer_name}
NOTE: {rating}/5
AVIS: "{review_text}"

Regles:
- Reponse courte (2-4 phrases max)
- Personnalisee avec le prenom du client
- Professionnelle mais chaleureuse
- Si negatif: s'excuser, proposer solution, inviter a nous contacter
- Si positif: remercier, mentionner un detail de l'avis
- Ne pas repeter le contenu de l'avis

Reponse:"""

            response = call_qwen(prompt, 500)
            if response:
                return {
                    'review_id': review_id,
                    'suggested_response': response.strip(),
                    'tone': tone,
                    'generated_at': datetime.now().isoformat()
                }

            return {'error': 'Generation impossible'}
        except Exception as e:
            return {'error': str(e)}

    def add_service_area(self, client_id, area_data):
        """Ajoute une zone de service"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO service_areas
                (client_id, area_name, area_type, population, competition_level, priority, landing_page_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, area_data.get('area_name'),
                area_data.get('area_type', 'city'),
                area_data.get('population', 0),
                area_data.get('competition_level', 'medium'),
                area_data.get('priority', 5),
                area_data.get('landing_page_url')
            ))

            conn.commit()
            area_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'area_id': area_id}
        except Exception as e:
            return {'error': str(e)}

    def get_service_areas(self, client_id):
        """Recupere les zones de service"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, area_name, area_type, population, competition_level, priority, landing_page_url
                FROM service_areas WHERE client_id = ?
                ORDER BY priority DESC, population DESC
            ''', (client_id,))
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'area_name': r[1],
                'area_type': r[2],
                'population': r[3],
                'competition_level': r[4],
                'priority': r[5],
                'landing_page_url': r[6]
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def generate_local_landing_page(self, client_id, area_name):
        """Genere le contenu d'une page locale"""
        log_agent(self.name, f"Generation landing page pour {area_name}")

        profile = self.get_gmb_profile(client_id)
        if not profile:
            return {'error': 'Profil GMB requis'}

        business_name = profile.get('business_name', '')
        category = profile.get('category', '')
        phone = profile.get('phone', '')

        # Info du site
        site = SITES.get(client_id, {})
        niche = site.get('niche', category)
        services = site.get('services', [category])

        prompt = f"""Tu es un expert SEO local. Cree le contenu d'une landing page pour:

ENTREPRISE: {business_name}
SERVICE: {niche}
VILLE/ZONE: {area_name}
TELEPHONE: {phone}

Le contenu doit inclure:
1. Titre H1 optimise SEO local
2. Meta description (155 caracteres)
3. Introduction (150 mots) mentionnant la ville
4. Section services (liste des services disponibles dans cette zone)
5. Pourquoi nous choisir (3-4 points)
6. Zone de service / quartiers desservis
7. FAQ locale (3 questions avec reponses)
8. CTA avec numero de telephone

FORMAT JSON:
{{
    "h1": "...",
    "meta_description": "...",
    "intro": "...",
    "services_section": "...",
    "why_choose_us": ["...", "..."],
    "neighborhoods": ["...", "..."],
    "faq": [
        {{"question": "...", "answer": "..."}}
    ],
    "cta_text": "...",
    "schema_local_business": {{...}}
}}
"""

        try:
            response = call_qwen(prompt, 2500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                content = json.loads(response.strip())

                return {
                    'area_name': area_name,
                    'content': content,
                    'generated_at': datetime.now().isoformat()
                }
        except:
            pass

        return {'error': 'Generation impossible'}

    def get_local_seo_score(self, client_id):
        """Calcule le score SEO local global"""
        log_agent(self.name, f"Calcul score SEO local pour client {client_id}")

        scores = {}
        total_weight = 0
        weighted_score = 0

        # GMB Profile (30%)
        gmb_audit = self.audit_gmb_profile(client_id)
        if 'score' in gmb_audit:
            scores['gmb_profile'] = gmb_audit['score']
            weighted_score += gmb_audit['score'] * 0.30
            total_weight += 0.30

        # NAP Consistency (25%)
        nap_audit = self.audit_nap_consistency(client_id)
        if 'consistency_score' in nap_audit:
            scores['nap_consistency'] = nap_audit['consistency_score']
            weighted_score += nap_audit['consistency_score'] * 0.25
            total_weight += 0.25

        # Reviews (25%)
        review_analysis = self.analyze_reviews(client_id)
        if 'average_rating' in review_analysis:
            review_score = (review_analysis['average_rating'] / 5) * 100
            scores['reviews'] = round(review_score, 1)
            weighted_score += review_score * 0.25
            total_weight += 0.25

        # Service Areas (20%)
        areas = self.get_service_areas(client_id)
        if isinstance(areas, list):
            areas_with_pages = len([a for a in areas if a.get('landing_page_url')])
            if len(areas) > 0:
                area_score = (areas_with_pages / len(areas)) * 100
            else:
                area_score = 0
            scores['service_areas'] = round(area_score, 1)
            weighted_score += area_score * 0.20
            total_weight += 0.20

        overall_score = round(weighted_score / total_weight, 1) if total_weight > 0 else 0

        return {
            'overall_score': overall_score,
            'component_scores': scores,
            'weights': {
                'gmb_profile': '30%',
                'nap_consistency': '25%',
                'reviews': '25%',
                'service_areas': '20%'
            },
            'calculated_at': datetime.now().isoformat()
        }



    def audit_site_html(self, site_id):
        """Audit local SEO en scannant le HTML du site"""
        import re as _re
        site = SITES.get(site_id, {})
        if not site:
            return {"error": f"Site {site_id} inconnu"}

        domain = site.get("domaine", "")
        url = f"https://{domain}"
        issues = []
        score = 100
        details = {}

        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "SeoAI-LocalSEO/1.0"})
            html = resp.text
        except Exception as e:
            return {"error": str(e), "score": 0}

        # 1. Check LocalBusiness JSON-LD
        ld_blocks = _re.findall(r"<script[^>]*application/ld.json[^>]*>(.*?)</script>", html, _re.DOTALL | _re.IGNORECASE)
        has_local_biz = False
        has_faq_schema = False
        faq_count = 0
        biz_data = {}

        for block in ld_blocks:
            try:
                data = json.loads(block.strip())
                biz_types = ["LocalBusiness", "LandscapingBusiness", "HomeAndConstructionBusiness",
                             "ProfessionalService", "Plumber", "Painter", "HousePainter"]
                if data.get("@type") in biz_types:
                    has_local_biz = True
                    biz_data = data
                if data.get("@type") == "FAQPage":
                    has_faq_schema = True
                    faq_count = len(data.get("mainEntity", []))
            except:
                pass

        if not has_local_biz:
            issues.append({"type": "critical", "message": "Schema LocalBusiness JSON-LD absent"})
            score -= 20
        else:
            if not biz_data.get("telephone"):
                issues.append({"type": "warning", "message": "Telephone manquant dans schema"})
                score -= 5
            if not biz_data.get("address"):
                issues.append({"type": "warning", "message": "Adresse manquante dans schema"})
                score -= 5
            if not biz_data.get("areaServed"):
                issues.append({"type": "warning", "message": "Zones de service (areaServed) manquantes"})
                score -= 5
            details["local_business"] = {"type": biz_data.get("@type", ""), "areas": len(biz_data.get("areaServed", []))}

        # 2. Check FAQPage schema
        if not has_faq_schema:
            issues.append({"type": "critical", "message": "Schema FAQPage JSON-LD absent"})
            score -= 15
        else:
            if faq_count < 5:
                issues.append({"type": "warning", "message": f"Seulement {faq_count} FAQ (min 5)"})
                score -= 5
            details["faq_schema"] = faq_count

        # 3. Check visible FAQ
        faq_visible = html.lower().count("faq-item")
        if faq_visible == 0:
            issues.append({"type": "warning", "message": "Section FAQ visible absente"})
            score -= 10
        details["faq_visible"] = faq_visible

        # 4. Cross-links
        sister_sites = {k: v for k, v in SITES.items() if k != site_id and k != 4}
        cross_links = [s["domaine"] for s in sister_sites.values() if s.get("domaine", "") in html]
        if not cross_links:
            issues.append({"type": "info", "message": "Pas de cross-link vers sites partenaires"})
            score -= 3
        details["cross_links"] = cross_links

        # 5. Google Maps
        html_lower = html.lower()
        has_gmaps = "maps.google" in html_lower or "google.com/maps" in html_lower or "maps.googleapis" in html_lower
        if not has_gmaps:
            issues.append({"type": "warning", "message": "Pas de Google Maps integre"})
            score -= 5
        details["has_google_maps"] = has_gmaps

        # 6. Phone visible
        phone_found = bool(_re.search(r"438.?383.?7283", html))
        if not phone_found:
            issues.append({"type": "warning", "message": "Telephone non visible"})
            score -= 5
        details["phone_visible"] = phone_found

        # 7. Check robots.txt AI bots
        try:
            robots_resp = requests.get(f"https://{domain}/robots.txt", timeout=5)
            if robots_resp.status_code == 200:
                robots = robots_resp.text.lower()
                details["robots_allows_ai"] = "gptbot" not in robots or "allow" in robots
        except:
            pass

        log_agent(self.name, f"Site HTML audit {domain}: Score {max(0, score)}, {len(issues)} issues")
        return {"site_id": site_id, "domain": domain, "score": max(0, score),
                "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
                "issues": issues, "details": details}

    def audit_all_sites_html(self):
        """Audit local SEO HTML de tous les sites clients"""
        results = {}
        for site_id in SITES:
            if site_id == 4:
                continue
            results[site_id] = self.audit_site_html(site_id)
        return results


# =============================================================================
# AGENT 46: INVOICE AGENT - Facturation Automatisee
# =============================================================================
class InvoiceAgent:
    """Agent de facturation: devis, factures, paiements, rappels"""

    def __init__(self):
        self.name = "InvoiceAgent"
        self._init_db()

    def _init_db(self):
        """Initialise les tables de facturation"""
        conn = get_db()
        cursor = conn.cursor()

        # Clients facturation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billing_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                company_name TEXT,
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                province TEXT,
                postal_code TEXT,
                tax_number TEXT,
                payment_terms INTEGER DEFAULT 30,
                currency TEXT DEFAULT 'CAD',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Devis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT UNIQUE,
                billing_client_id INTEGER,
                status TEXT DEFAULT 'draft',
                issue_date TEXT,
                valid_until TEXT,
                subtotal REAL DEFAULT 0,
                tax_rate REAL DEFAULT 14.975,
                tax_amount REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notes TEXT,
                terms TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Factures
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE,
                quote_id INTEGER,
                billing_client_id INTEGER,
                status TEXT DEFAULT 'draft',
                issue_date TEXT,
                due_date TEXT,
                subtotal REAL DEFAULT 0,
                tax_rate REAL DEFAULT 14.975,
                tax_amount REAL DEFAULT 0,
                total REAL DEFAULT 0,
                amount_paid REAL DEFAULT 0,
                notes TEXT,
                terms TEXT,
                recurring BOOLEAN DEFAULT 0,
                recurring_interval TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Lignes de facture/devis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                quote_id INTEGER,
                description TEXT,
                quantity REAL DEFAULT 1,
                unit_price REAL DEFAULT 0,
                total REAL DEFAULT 0,
                item_order INTEGER DEFAULT 0
            )
        ''')

        # Paiements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                amount REAL,
                payment_date TEXT,
                payment_method TEXT,
                reference TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Rappels envoyes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                reminder_type TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def _generate_number(self, prefix, table, column):
        """Genere un numero unique (devis ou facture)"""
        year = datetime.now().strftime('%Y')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} LIKE ?", (f"{prefix}-{year}-%",))
        count = cursor.fetchone()[0] + 1
        conn.close()
        return f"{prefix}-{year}-{count:04d}"

    def create_billing_client(self, client_id, data):
        """Cree un client facturation"""
        log_agent(self.name, f"Creation client facturation pour {client_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO billing_clients
                (client_id, company_name, contact_name, email, phone, address,
                 city, province, postal_code, tax_number, payment_terms, currency, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, data.get('company_name'), data.get('contact_name'),
                data.get('email'), data.get('phone'), data.get('address'),
                data.get('city'), data.get('province'), data.get('postal_code'),
                data.get('tax_number'), data.get('payment_terms', 30),
                data.get('currency', 'CAD'), data.get('notes')
            ))

            conn.commit()
            billing_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'billing_client_id': billing_id}
        except Exception as e:
            return {'error': str(e)}

    def get_billing_client(self, billing_client_id):
        """Recupere un client facturation"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM billing_clients WHERE id = ?', (billing_client_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0], 'client_id': row[1], 'company_name': row[2],
                    'contact_name': row[3], 'email': row[4], 'phone': row[5],
                    'address': row[6], 'city': row[7], 'province': row[8],
                    'postal_code': row[9], 'tax_number': row[10],
                    'payment_terms': row[11], 'currency': row[12], 'notes': row[13]
                }
            return None
        except Exception as e:
            return {'error': str(e)}

    def create_quote(self, billing_client_id, items, notes='', valid_days=30):
        """Cree un devis"""
        log_agent(self.name, f"Creation devis pour client {billing_client_id}")

        try:
            quote_number = self._generate_number('DEV', 'quotes', 'quote_number')
            issue_date = datetime.now().strftime('%Y-%m-%d')
            valid_until = (datetime.now() + timedelta(days=valid_days)).strftime('%Y-%m-%d')

            # Calcul totaux
            subtotal = sum(item.get('quantity', 1) * item.get('unit_price', 0) for item in items)
            tax_rate = 14.975  # TPS + TVQ Quebec
            tax_amount = round(subtotal * tax_rate / 100, 2)
            total = round(subtotal + tax_amount, 2)

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO quotes
                (quote_number, billing_client_id, status, issue_date, valid_until,
                 subtotal, tax_rate, tax_amount, total, notes)
                VALUES (?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)
            ''', (quote_number, billing_client_id, issue_date, valid_until,
                  subtotal, tax_rate, tax_amount, total, notes))

            quote_id = cursor.lastrowid

            # Ajouter les lignes
            for i, item in enumerate(items):
                item_total = item.get('quantity', 1) * item.get('unit_price', 0)
                cursor.execute('''
                    INSERT INTO invoice_items
                    (quote_id, description, quantity, unit_price, total, item_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (quote_id, item.get('description'), item.get('quantity', 1),
                      item.get('unit_price', 0), item_total, i))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'quote_id': quote_id,
                'quote_number': quote_number,
                'total': total
            }
        except Exception as e:
            return {'error': str(e)}

    def get_quote(self, quote_id):
        """Recupere un devis avec ses lignes"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM quotes WHERE id = ?', (quote_id,))
            quote = cursor.fetchone()

            if not quote:
                conn.close()
                return {'error': 'Devis non trouve'}

            cursor.execute('''
                SELECT id, description, quantity, unit_price, total
                FROM invoice_items WHERE quote_id = ? ORDER BY item_order
            ''', (quote_id,))
            items = cursor.fetchall()
            conn.close()

            client = self.get_billing_client(quote[2])

            return {
                'id': quote[0],
                'quote_number': quote[1],
                'client': client,
                'status': quote[3],
                'issue_date': quote[4],
                'valid_until': quote[5],
                'subtotal': quote[6],
                'tax_rate': quote[7],
                'tax_amount': quote[8],
                'total': quote[9],
                'notes': quote[10],
                'items': [{
                    'id': i[0], 'description': i[1], 'quantity': i[2],
                    'unit_price': i[3], 'total': i[4]
                } for i in items]
            }
        except Exception as e:
            return {'error': str(e)}

    def convert_quote_to_invoice(self, quote_id):
        """Convertit un devis en facture"""
        log_agent(self.name, f"Conversion devis {quote_id} en facture")

        quote = self.get_quote(quote_id)
        if 'error' in quote:
            return quote

        try:
            invoice_number = self._generate_number('FAC', 'invoices', 'invoice_number')
            issue_date = datetime.now().strftime('%Y-%m-%d')

            # Recuperer payment terms du client
            client = quote.get('client', {})
            payment_terms = client.get('payment_terms', 30) if client else 30
            due_date = (datetime.now() + timedelta(days=payment_terms)).strftime('%Y-%m-%d')

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO invoices
                (invoice_number, quote_id, billing_client_id, status, issue_date, due_date,
                 subtotal, tax_rate, tax_amount, total, notes)
                VALUES (?, ?, ?, 'sent', ?, ?, ?, ?, ?, ?, ?)
            ''', (invoice_number, quote_id, quote['client']['id'], issue_date, due_date,
                  quote['subtotal'], quote['tax_rate'], quote['tax_amount'],
                  quote['total'], quote['notes']))

            invoice_id = cursor.lastrowid

            # Copier les lignes
            for item in quote['items']:
                cursor.execute('''
                    INSERT INTO invoice_items
                    (invoice_id, description, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (invoice_id, item['description'], item['quantity'],
                      item['unit_price'], item['total']))

            # Marquer le devis comme accepte
            cursor.execute("UPDATE quotes SET status = 'accepted' WHERE id = ?", (quote_id,))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice_number,
                'total': quote['total'],
                'due_date': due_date
            }
        except Exception as e:
            return {'error': str(e)}

    def create_invoice(self, billing_client_id, items, notes='', due_days=30):
        """Cree une facture directement"""
        log_agent(self.name, f"Creation facture pour client {billing_client_id}")

        try:
            invoice_number = self._generate_number('FAC', 'invoices', 'invoice_number')
            issue_date = datetime.now().strftime('%Y-%m-%d')
            due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')

            subtotal = sum(item.get('quantity', 1) * item.get('unit_price', 0) for item in items)
            tax_rate = 14.975
            tax_amount = round(subtotal * tax_rate / 100, 2)
            total = round(subtotal + tax_amount, 2)

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO invoices
                (invoice_number, billing_client_id, status, issue_date, due_date,
                 subtotal, tax_rate, tax_amount, total, notes)
                VALUES (?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)
            ''', (invoice_number, billing_client_id, issue_date, due_date,
                  subtotal, tax_rate, tax_amount, total, notes))

            invoice_id = cursor.lastrowid

            for i, item in enumerate(items):
                item_total = item.get('quantity', 1) * item.get('unit_price', 0)
                cursor.execute('''
                    INSERT INTO invoice_items
                    (invoice_id, description, quantity, unit_price, total, item_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (invoice_id, item.get('description'), item.get('quantity', 1),
                      item.get('unit_price', 0), item_total, i))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice_number,
                'total': total,
                'due_date': due_date
            }
        except Exception as e:
            return {'error': str(e)}

    def get_invoice(self, invoice_id):
        """Recupere une facture avec ses lignes et paiements"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,))
            inv = cursor.fetchone()

            if not inv:
                conn.close()
                return {'error': 'Facture non trouvee'}

            cursor.execute('''
                SELECT id, description, quantity, unit_price, total
                FROM invoice_items WHERE invoice_id = ? ORDER BY item_order
            ''', (invoice_id,))
            items = cursor.fetchall()

            cursor.execute('''
                SELECT id, amount, payment_date, payment_method, reference
                FROM payments WHERE invoice_id = ? ORDER BY payment_date DESC
            ''', (invoice_id,))
            payments = cursor.fetchall()

            conn.close()

            client = self.get_billing_client(inv[3])
            balance = inv[10] - inv[11]  # total - amount_paid

            return {
                'id': inv[0],
                'invoice_number': inv[1],
                'quote_id': inv[2],
                'client': client,
                'status': inv[4],
                'issue_date': inv[5],
                'due_date': inv[6],
                'subtotal': inv[7],
                'tax_rate': inv[8],
                'tax_amount': inv[9],
                'total': inv[10],
                'amount_paid': inv[11],
                'balance': balance,
                'notes': inv[12],
                'recurring': bool(inv[14]),
                'recurring_interval': inv[15],
                'items': [{
                    'id': i[0], 'description': i[1], 'quantity': i[2],
                    'unit_price': i[3], 'total': i[4]
                } for i in items],
                'payments': [{
                    'id': p[0], 'amount': p[1], 'date': p[2],
                    'method': p[3], 'reference': p[4]
                } for p in payments]
            }
        except Exception as e:
            return {'error': str(e)}

    def record_payment(self, invoice_id, amount, method='virement', reference=''):
        """Enregistre un paiement"""
        log_agent(self.name, f"Paiement de {amount}$ sur facture {invoice_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            payment_date = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                INSERT INTO payments (invoice_id, amount, payment_date, payment_method, reference)
                VALUES (?, ?, ?, ?, ?)
            ''', (invoice_id, amount, payment_date, method, reference))

            # Mettre a jour le montant paye
            cursor.execute('''
                UPDATE invoices SET
                    amount_paid = amount_paid + ?,
                    status = CASE
                        WHEN amount_paid + ? >= total THEN 'paid'
                        WHEN amount_paid + ? > 0 THEN 'partial'
                        ELSE status
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (amount, amount, amount, invoice_id))

            conn.commit()
            conn.close()

            invoice = self.get_invoice(invoice_id)

            return {
                'success': True,
                'payment_recorded': amount,
                'new_balance': invoice.get('balance', 0),
                'status': invoice.get('status')
            }
        except Exception as e:
            return {'error': str(e)}

    def get_overdue_invoices(self):
        """Recupere les factures en retard"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT i.id, i.invoice_number, i.due_date, i.total, i.amount_paid,
                       b.company_name, b.email
                FROM invoices i
                JOIN billing_clients b ON i.billing_client_id = b.id
                WHERE i.status NOT IN ('paid', 'cancelled')
                AND i.due_date < ?
                ORDER BY i.due_date
            ''', (today,))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'invoice_id': r[0],
                'invoice_number': r[1],
                'due_date': r[2],
                'total': r[3],
                'amount_paid': r[4],
                'balance': r[3] - r[4],
                'days_overdue': (datetime.now() - datetime.strptime(r[2], '%Y-%m-%d')).days,
                'client_name': r[5],
                'client_email': r[6]
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def generate_reminder(self, invoice_id):
        """Genere un email de rappel de paiement"""
        log_agent(self.name, f"Generation rappel pour facture {invoice_id}")

        invoice = self.get_invoice(invoice_id)
        if 'error' in invoice:
            return invoice

        client = invoice.get('client', {})
        days_overdue = 0
        if invoice.get('due_date'):
            due = datetime.strptime(invoice['due_date'], '%Y-%m-%d')
            days_overdue = (datetime.now() - due).days

        if days_overdue <= 0:
            tone = "amical"
            urgency = "faible"
        elif days_overdue <= 15:
            tone = "professionnel"
            urgency = "moyenne"
        else:
            tone = "ferme mais poli"
            urgency = "haute"

        prompt = f"""Redige un email de rappel de paiement en francais:

FACTURE: {invoice.get('invoice_number')}
CLIENT: {client.get('company_name')}
CONTACT: {client.get('contact_name')}
MONTANT DU: {invoice.get('balance')}$ CAD
DATE ECHEANCE: {invoice.get('due_date')}
JOURS DE RETARD: {days_overdue}
TON: {tone}
URGENCE: {urgency}

L'email doit:
- Etre professionnel et respectueux
- Rappeler le montant et la date d'echeance
- Proposer de contacter en cas de probleme
- Inclure un appel a l'action clair

FORMAT JSON:
{{
    "subject": "...",
    "body": "...",
    "urgency_level": "{urgency}"
}}
"""

        try:
            response = call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                email = json.loads(response.strip())

                # Enregistrer le rappel
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO payment_reminders (invoice_id, reminder_type)
                    VALUES (?, ?)
                ''', (invoice_id, urgency))
                conn.commit()
                conn.close()

                return {
                    'invoice_id': invoice_id,
                    'invoice_number': invoice.get('invoice_number'),
                    'client_email': client.get('email'),
                    'email': email,
                    'generated_at': datetime.now().isoformat()
                }
        except:
            pass

        return {'error': 'Generation impossible'}

    def get_revenue_stats(self, period='month'):
        """Statistiques de revenus"""
        log_agent(self.name, f"Stats revenus periode: {period}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            if period == 'month':
                date_filter = datetime.now().strftime('%Y-%m')
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_invoices,
                        SUM(total) as total_billed,
                        SUM(amount_paid) as total_collected,
                        SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count
                    FROM invoices
                    WHERE strftime('%Y-%m', issue_date) = ?
                ''', (date_filter,))
            elif period == 'year':
                date_filter = datetime.now().strftime('%Y')
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_invoices,
                        SUM(total) as total_billed,
                        SUM(amount_paid) as total_collected,
                        SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count
                    FROM invoices
                    WHERE strftime('%Y', issue_date) = ?
                ''', (date_filter,))
            else:
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_invoices,
                        SUM(total) as total_billed,
                        SUM(amount_paid) as total_collected,
                        SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count
                    FROM invoices
                ''')

            row = cursor.fetchone()

            # Factures en attente
            cursor.execute('''
                SELECT COUNT(*), SUM(total - amount_paid)
                FROM invoices
                WHERE status NOT IN ('paid', 'cancelled')
            ''')
            pending = cursor.fetchone()

            conn.close()

            total_invoices = row[0] or 0
            total_billed = row[1] or 0
            total_collected = row[2] or 0
            paid_count = row[3] or 0

            return {
                'period': period,
                'total_invoices': total_invoices,
                'total_billed': round(total_billed, 2),
                'total_collected': round(total_collected, 2),
                'outstanding': round(total_billed - total_collected, 2),
                'paid_count': paid_count,
                'collection_rate': round((total_collected / total_billed * 100) if total_billed > 0 else 0, 1),
                'pending_invoices': pending[0] or 0,
                'pending_amount': round(pending[1] or 0, 2),
                'calculated_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    def list_invoices(self, status=None, limit=50):
        """Liste les factures"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            if status:
                cursor.execute('''
                    SELECT i.id, i.invoice_number, i.status, i.issue_date, i.due_date,
                           i.total, i.amount_paid, b.company_name
                    FROM invoices i
                    JOIN billing_clients b ON i.billing_client_id = b.id
                    WHERE i.status = ?
                    ORDER BY i.issue_date DESC
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT i.id, i.invoice_number, i.status, i.issue_date, i.due_date,
                           i.total, i.amount_paid, b.company_name
                    FROM invoices i
                    JOIN billing_clients b ON i.billing_client_id = b.id
                    ORDER BY i.issue_date DESC
                    LIMIT ?
                ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0],
                'invoice_number': r[1],
                'status': r[2],
                'issue_date': r[3],
                'due_date': r[4],
                'total': r[5],
                'amount_paid': r[6],
                'balance': r[5] - r[6],
                'client_name': r[7]
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 53: LEAD SCORING AGENT - Qualification IA des leads
# ============================================

class LeadScoringAgent:
    """
    Agent de scoring et qualification des leads par IA
    - Score automatique 0-100
    - Analyse comportementale
    - Prediction de conversion
    - Prioritisation intelligente
    - Recommandations d'actions
    """
    name = "Lead Scoring Agent"

    # Criteres de scoring
    SCORING_CRITERIA = {
        'source': {'referral': 30, 'organic': 25, 'direct': 20, 'social': 15, 'paid': 10},
        'engagement': {'high': 30, 'medium': 20, 'low': 10},
        'budget': {'high': 25, 'medium': 15, 'low': 5},
        'timeline': {'immediate': 25, 'short': 15, 'long': 5},
        'fit': {'perfect': 25, 'good': 15, 'partial': 5}
    }

    SCORE_LABELS = {
        (80, 100): 'hot',
        (60, 79): 'warm',
        (40, 59): 'lukewarm',
        (0, 39): 'cold'
    }

    def init_db(self):
        """Initialise les tables lead scoring"""
        conn = get_db()
        cursor = conn.cursor()

        # Table historique des scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                label TEXT DEFAULT 'cold',
                source_score INTEGER DEFAULT 0,
                engagement_score INTEGER DEFAULT 0,
                budget_score INTEGER DEFAULT 0,
                timeline_score INTEGER DEFAULT 0,
                fit_score INTEGER DEFAULT 0,
                ai_analysis TEXT,
                conversion_probability REAL DEFAULT 0,
                recommended_action TEXT,
                scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scored_by TEXT DEFAULT 'system'
            )
        ''')

        # Table des criteres personnalises
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_scoring_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                condition TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table des actions recommandees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                priority INTEGER DEFAULT 3,
                description TEXT,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                assigned_to TEXT,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        return {'success': True}

    def score_lead(self, contact_id, data=None):
        """
        Calcule le score d'un lead
        data: {source, engagement, budget, timeline, company_size, interactions, page_views}
        """
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Recuperer les infos du contact si pas fournies
            if not data:
                cursor.execute('''
                    SELECT source, company, notes FROM crm_contacts WHERE id = ?
                ''', (contact_id,))
                contact = cursor.fetchone()
                if not contact:
                    return {'error': 'Contact non trouve'}
                data = {
                    'source': contact[0] or 'direct',
                    'company': contact[1],
                    'notes': contact[2]
                }

            # Calculer les scores par categorie
            source_score = self.SCORING_CRITERIA['source'].get(data.get('source', 'direct'), 15)
            engagement_score = self.SCORING_CRITERIA['engagement'].get(data.get('engagement', 'medium'), 15)
            budget_score = self.SCORING_CRITERIA['budget'].get(data.get('budget', 'medium'), 15)
            timeline_score = self.SCORING_CRITERIA['timeline'].get(data.get('timeline', 'long'), 10)
            fit_score = self.SCORING_CRITERIA['fit'].get(data.get('fit', 'partial'), 10)

            # Bonus/malus
            bonus = 0
            if data.get('interactions', 0) > 5:
                bonus += 10
            if data.get('page_views', 0) > 10:
                bonus += 5
            if data.get('downloaded_content'):
                bonus += 10
            if data.get('visited_pricing'):
                bonus += 15
            if data.get('company'):
                bonus += 5

            # Score total
            total_score = min(100, source_score + engagement_score + budget_score + timeline_score + fit_score + bonus)

            # Label
            label = 'cold'
            for (low, high), lbl in self.SCORE_LABELS.items():
                if low <= total_score <= high:
                    label = lbl
                    break

            # Probabilite de conversion
            conversion_prob = round(total_score * 0.8 / 100, 2)

            # Action recommandee
            if total_score >= 80:
                action = "Appeler immediatement - lead tres chaud"
            elif total_score >= 60:
                action = "Envoyer une proposition personnalisee"
            elif total_score >= 40:
                action = "Envoyer du contenu educatif"
            else:
                action = "Ajouter a la sequence de nurturing"

            # Sauvegarder le score
            cursor.execute('''
                INSERT INTO lead_scores
                (contact_id, score, label, source_score, engagement_score, budget_score,
                 timeline_score, fit_score, conversion_probability, recommended_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (contact_id, total_score, label, source_score, engagement_score,
                  budget_score, timeline_score, fit_score, conversion_prob, action))

            score_id = cursor.lastrowid

            # Mettre a jour le contact CRM avec le score
            cursor.execute('''
                UPDATE crm_contacts SET score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (total_score, contact_id))

            conn.commit()
            conn.close()

            return {
                'score_id': score_id,
                'contact_id': contact_id,
                'score': total_score,
                'label': label,
                'breakdown': {
                    'source': source_score,
                    'engagement': engagement_score,
                    'budget': budget_score,
                    'timeline': timeline_score,
                    'fit': fit_score,
                    'bonus': bonus
                },
                'conversion_probability': conversion_prob,
                'recommended_action': action
            }

        except Exception as e:
            return {'error': str(e)}

    def score_lead_ai(self, contact_id):
        """Score un lead avec analyse IA complete"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Recuperer toutes les infos du contact
            cursor.execute('''
                SELECT c.*,
                       (SELECT COUNT(*) FROM crm_interactions WHERE contact_id = c.id) as interaction_count,
                       (SELECT MAX(interaction_date) FROM crm_interactions WHERE contact_id = c.id) as last_interaction
                FROM crm_contacts c WHERE c.id = ?
            ''', (contact_id,))
            contact = cursor.fetchone()

            if not contact:
                conn.close()
                return {'error': 'Contact non trouve'}

            # Recuperer les interactions
            cursor.execute('''
                SELECT type, description, interaction_date FROM crm_interactions
                WHERE contact_id = ? ORDER BY interaction_date DESC LIMIT 10
            ''', (contact_id,))
            interactions = cursor.fetchall()

            conn.close()

            # Preparer le prompt IA
            prompt = f"""Analyse ce lead et donne un score de 0 a 100 avec justification.

CONTACT:
- Nom: {contact[3]} {contact[4]}
- Email: {contact[5]}
- Entreprise: {contact[7]}
- Poste: {contact[8]}
- Source: {contact[9]}
- Status: {contact[2]}
- Type: {contact[1]}
- Notes: {contact[15]}

INTERACTIONS ({len(interactions)}):
{chr(10).join([f"- {i[0]}: {i[1]} ({i[2]})" for i in interactions[:5]])}

Derniere interaction: {contact[-1] or 'Jamais'}

REPONDS EN JSON:
{{
    "score": 0-100,
    "label": "hot|warm|lukewarm|cold",
    "conversion_probability": 0.0-1.0,
    "strengths": ["point fort 1", "point fort 2"],
    "weaknesses": ["point faible 1"],
    "recommended_actions": ["action 1", "action 2"],
    "priority": "high|medium|low",
    "analysis": "courte analyse"
}}
"""
            # Appel Ollama local d'abord, puis Fireworks
            response = call_ollama(prompt, 800)
            if not response:
                response = call_qwen(prompt, 800)

            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                try:
                    result = json.loads(response.strip())

                    # Sauvegarder le score AI
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO lead_scores
                        (contact_id, score, label, ai_analysis, conversion_probability, recommended_action, scored_by)
                        VALUES (?, ?, ?, ?, ?, ?, 'ai')
                    ''', (
                        contact_id,
                        result.get('score', 50),
                        result.get('label', 'lukewarm'),
                        json.dumps(result),
                        result.get('conversion_probability', 0.5),
                        result.get('recommended_actions', ['Contacter'])[0] if result.get('recommended_actions') else 'Contacter'
                    ))

                    # Mettre a jour le contact
                    cursor.execute('''
                        UPDATE crm_contacts SET score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                    ''', (result.get('score', 50), contact_id))

                    conn.commit()
                    conn.close()

                    result['contact_id'] = contact_id
                    return result

                except json.JSONDecodeError:
                    return {'error': 'Erreur parsing AI', 'raw': response}

            return {'error': 'Pas de reponse AI'}

        except Exception as e:
            return {'error': str(e)}

    def batch_score(self, limit=50):
        """Score tous les leads non scores ou anciens"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Leads sans score recent (> 7 jours)
            cursor.execute('''
                SELECT c.id FROM crm_contacts c
                LEFT JOIN lead_scores ls ON c.id = ls.contact_id
                WHERE c.type = 'lead'
                AND (ls.id IS NULL OR ls.scored_at < datetime('now', '-7 days'))
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (limit,))

            leads = [r[0] for r in cursor.fetchall()]
            conn.close()

            results = {'scored': 0, 'errors': 0, 'scores': []}

            for lead_id in leads:
                result = self.score_lead(lead_id)
                if 'error' in result:
                    results['errors'] += 1
                else:
                    results['scored'] += 1
                    results['scores'].append({
                        'contact_id': lead_id,
                        'score': result['score'],
                        'label': result['label']
                    })

            return results

        except Exception as e:
            return {'error': str(e)}

    def get_hot_leads(self, min_score=70, limit=20):
        """Recupere les leads chauds"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT c.id, c.first_name, c.last_name, c.email, c.company, c.phone,
                       ls.score, ls.label, ls.conversion_probability, ls.recommended_action, ls.scored_at
                FROM crm_contacts c
                INNER JOIN lead_scores ls ON c.id = ls.contact_id
                WHERE ls.score >= ?
                AND ls.id = (SELECT MAX(id) FROM lead_scores WHERE contact_id = c.id)
                ORDER BY ls.score DESC, ls.scored_at DESC
                LIMIT ?
            ''', (min_score, limit))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'contact_id': r[0],
                'name': f"{r[1]} {r[2]}",
                'email': r[3],
                'company': r[4],
                'phone': r[5],
                'score': r[6],
                'label': r[7],
                'conversion_probability': r[8],
                'recommended_action': r[9],
                'scored_at': r[10]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def get_score_history(self, contact_id, limit=10):
        """Historique des scores d'un contact"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, score, label, source_score, engagement_score, budget_score,
                       timeline_score, fit_score, conversion_probability, recommended_action,
                       ai_analysis, scored_at, scored_by
                FROM lead_scores
                WHERE contact_id = ?
                ORDER BY scored_at DESC
                LIMIT ?
            ''', (contact_id, limit))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'score': r[1], 'label': r[2],
                'breakdown': {
                    'source': r[3], 'engagement': r[4], 'budget': r[5],
                    'timeline': r[6], 'fit': r[7]
                },
                'conversion_probability': r[8],
                'recommended_action': r[9],
                'ai_analysis': json.loads(r[10]) if r[10] else None,
                'scored_at': r[11],
                'scored_by': r[12]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def create_action(self, contact_id, action_type, description, priority=3, due_date=None, assigned_to=None):
        """Cree une action pour un lead"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO lead_actions
                (contact_id, action_type, priority, description, due_date, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (contact_id, action_type, priority, description, due_date, assigned_to))

            action_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'action_id': action_id}

        except Exception as e:
            return {'error': str(e)}

    def get_pending_actions(self, limit=50):
        """Actions en attente"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT a.id, a.contact_id, c.first_name || ' ' || c.last_name as name,
                       a.action_type, a.priority, a.description, a.due_date, a.assigned_to, a.created_at
                FROM lead_actions a
                LEFT JOIN crm_contacts c ON a.contact_id = c.id
                WHERE a.status = 'pending'
                ORDER BY a.priority ASC, a.due_date ASC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'contact_id': r[1], 'contact_name': r[2],
                'action_type': r[3], 'priority': r[4], 'description': r[5],
                'due_date': r[6], 'assigned_to': r[7], 'created_at': r[8]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def complete_action(self, action_id):
        """Marque une action comme terminee"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE lead_actions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (action_id,))

            conn.commit()
            conn.close()

            return {'success': True}

        except Exception as e:
            return {'error': str(e)}

    def get_stats(self):
        """Statistiques de scoring"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Distribution des scores
            cursor.execute('''
                SELECT
                    SUM(CASE WHEN score >= 80 THEN 1 ELSE 0 END) as hot,
                    SUM(CASE WHEN score >= 60 AND score < 80 THEN 1 ELSE 0 END) as warm,
                    SUM(CASE WHEN score >= 40 AND score < 60 THEN 1 ELSE 0 END) as lukewarm,
                    SUM(CASE WHEN score < 40 THEN 1 ELSE 0 END) as cold,
                    COUNT(*) as total,
                    AVG(score) as avg_score
                FROM lead_scores ls
                WHERE ls.id = (SELECT MAX(id) FROM lead_scores WHERE contact_id = ls.contact_id)
            ''')
            dist = cursor.fetchone()

            # Leads scores ce mois
            cursor.execute('''
                SELECT COUNT(DISTINCT contact_id) FROM lead_scores
                WHERE scored_at >= date('now', 'start of month')
            ''')
            scored_this_month = cursor.fetchone()[0]

            # Actions pending
            cursor.execute('SELECT COUNT(*) FROM lead_actions WHERE status = "pending"')
            pending_actions = cursor.fetchone()[0]

            conn.close()

            return {
                'distribution': {
                    'hot': dist[0] or 0,
                    'warm': dist[1] or 0,
                    'lukewarm': dist[2] or 0,
                    'cold': dist[3] or 0
                },
                'total_scored': dist[4] or 0,
                'average_score': round(dist[5] or 0, 1),
                'scored_this_month': scored_this_month,
                'pending_actions': pending_actions
            }

        except Exception as e:
            return {'error': str(e)}


# =============================================================================
# AGENT 47: CRM AGENT - Gestion Clients et Prospects
# =============================================================================
class CRMAgent:
    """Agent CRM: gestion contacts, prospects, pipeline, interactions"""

    def __init__(self):
        self.name = "CRMAgent"
        self._init_db()

    def _init_db(self):
        """Initialise les tables CRM"""
        conn = get_db()
        cursor = conn.cursor()

        # Contacts/Leads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT DEFAULT 'lead',
                status TEXT DEFAULT 'new',
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                job_title TEXT,
                source TEXT,
                website TEXT,
                address TEXT,
                city TEXT,
                province TEXT,
                postal_code TEXT,
                notes TEXT,
                tags TEXT,
                assigned_to TEXT,
                score INTEGER DEFAULT 0,
                last_contact_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Pipeline/Opportunites
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                title TEXT,
                value REAL DEFAULT 0,
                currency TEXT DEFAULT 'CAD',
                stage TEXT DEFAULT 'qualification',
                probability INTEGER DEFAULT 10,
                expected_close_date TEXT,
                actual_close_date TEXT,
                won BOOLEAN,
                loss_reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Interactions/Activites
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                opportunity_id INTEGER,
                type TEXT,
                subject TEXT,
                description TEXT,
                outcome TEXT,
                next_action TEXT,
                next_action_date TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Taches
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                opportunity_id INTEGER,
                title TEXT,
                description TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                assigned_to TEXT,
                completed_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Etapes du pipeline
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_pipeline_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                order_num INTEGER,
                probability INTEGER DEFAULT 0,
                color TEXT
            )
        ''')

        # Inserer les etapes par defaut si vide
        cursor.execute('SELECT COUNT(*) FROM crm_pipeline_stages')
        if cursor.fetchone()[0] == 0:
            stages = [
                ('Nouveau lead', 1, 10, '#6366f1'),
                ('Qualification', 2, 20, '#8b5cf6'),
                ('Proposition', 3, 40, '#a855f7'),
                ('Negociation', 4, 60, '#f59e0b'),
                ('Engagement verbal', 5, 80, '#22c55e'),
                ('Gagne', 6, 100, '#10b981'),
                ('Perdu', 7, 0, '#ef4444')
            ]
            cursor.executemany('''
                INSERT INTO crm_pipeline_stages (name, order_num, probability, color)
                VALUES (?, ?, ?, ?)
            ''', stages)

        conn.commit()
        conn.close()

    def create_contact(self, data):
        """Cree un nouveau contact/lead"""
        log_agent(self.name, f"Creation contact: {data.get('email')}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            tags = ','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '')

            cursor.execute('''
                INSERT INTO crm_contacts
                (type, status, first_name, last_name, email, phone, company,
                 job_title, source, website, address, city, province, postal_code,
                 notes, tags, assigned_to, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('type', 'lead'), data.get('status', 'new'),
                data.get('first_name'), data.get('last_name'),
                data.get('email'), data.get('phone'), data.get('company'),
                data.get('job_title'), data.get('source'), data.get('website'),
                data.get('address'), data.get('city'), data.get('province'),
                data.get('postal_code'), data.get('notes'), tags,
                data.get('assigned_to'), data.get('score', 0)
            ))

            conn.commit()
            contact_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'contact_id': contact_id}
        except Exception as e:
            return {'error': str(e)}

    def get_contact(self, contact_id):
        """Recupere un contact avec son historique"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM crm_contacts WHERE id = ?', (contact_id,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return {'error': 'Contact non trouve'}

            # Recuperer les interactions
            cursor.execute('''
                SELECT id, type, subject, description, outcome, created_at
                FROM crm_interactions WHERE contact_id = ?
                ORDER BY created_at DESC LIMIT 10
            ''', (contact_id,))
            interactions = cursor.fetchall()

            # Recuperer les opportunites
            cursor.execute('''
                SELECT id, title, value, stage, probability, expected_close_date
                FROM crm_opportunities WHERE contact_id = ?
                ORDER BY created_at DESC
            ''', (contact_id,))
            opportunities = cursor.fetchall()

            # Recuperer les taches en cours
            cursor.execute('''
                SELECT id, title, due_date, priority, status
                FROM crm_tasks WHERE contact_id = ? AND status != 'completed'
                ORDER BY due_date
            ''', (contact_id,))
            tasks = cursor.fetchall()

            conn.close()

            return {
                'id': row[0],
                'type': row[1],
                'status': row[2],
                'first_name': row[3],
                'last_name': row[4],
                'full_name': f"{row[3] or ''} {row[4] or ''}".strip(),
                'email': row[5],
                'phone': row[6],
                'company': row[7],
                'job_title': row[8],
                'source': row[9],
                'website': row[10],
                'address': row[11],
                'city': row[12],
                'province': row[13],
                'postal_code': row[14],
                'notes': row[15],
                'tags': row[16].split(',') if row[16] else [],
                'assigned_to': row[17],
                'score': row[18],
                'last_contact_date': row[19],
                'created_at': row[20],
                'interactions': [{
                    'id': i[0], 'type': i[1], 'subject': i[2],
                    'description': i[3], 'outcome': i[4], 'date': i[5]
                } for i in interactions],
                'opportunities': [{
                    'id': o[0], 'title': o[1], 'value': o[2],
                    'stage': o[3], 'probability': o[4], 'expected_close': o[5]
                } for o in opportunities],
                'pending_tasks': [{
                    'id': t[0], 'title': t[1], 'due_date': t[2],
                    'priority': t[3], 'status': t[4]
                } for t in tasks]
            }
        except Exception as e:
            return {'error': str(e)}

    def update_contact(self, contact_id, data):
        """Met a jour un contact"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            updates = []
            values = []

            fields = ['type', 'status', 'first_name', 'last_name', 'email', 'phone',
                      'company', 'job_title', 'source', 'website', 'address', 'city',
                      'province', 'postal_code', 'notes', 'assigned_to', 'score']

            for field in fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])

            if 'tags' in data:
                updates.append("tags = ?")
                tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']
                values.append(tags)

            if not updates:
                return {'error': 'Aucune donnee a mettre a jour'}

            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(contact_id)

            cursor.execute(f'''
                UPDATE crm_contacts SET {', '.join(updates)} WHERE id = ?
            ''', values)

            conn.commit()
            conn.close()

            return {'success': True, 'contact_id': contact_id}
        except Exception as e:
            return {'error': str(e)}

    def list_contacts(self, filters=None, limit=50):
        """Liste les contacts avec filtres"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT id, type, status, first_name, last_name, email, phone,
                       company, score, last_contact_date, created_at
                FROM crm_contacts
            '''
            params = []
            conditions = []

            if filters:
                if filters.get('type'):
                    conditions.append("type = ?")
                    params.append(filters['type'])
                if filters.get('status'):
                    conditions.append("status = ?")
                    params.append(filters['status'])
                if filters.get('assigned_to'):
                    conditions.append("assigned_to = ?")
                    params.append(filters['assigned_to'])
                if filters.get('search'):
                    conditions.append("(first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR company LIKE ?)")
                    search = f"%{filters['search']}%"
                    params.extend([search, search, search, search])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'type': r[1], 'status': r[2],
                'first_name': r[3], 'last_name': r[4],
                'full_name': f"{r[3] or ''} {r[4] or ''}".strip(),
                'email': r[5], 'phone': r[6], 'company': r[7],
                'score': r[8], 'last_contact_date': r[9], 'created_at': r[10]
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def add_interaction(self, contact_id, data):
        """Ajoute une interaction/activite"""
        log_agent(self.name, f"Nouvelle interaction pour contact {contact_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO crm_interactions
                (contact_id, opportunity_id, type, subject, description,
                 outcome, next_action, next_action_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contact_id, data.get('opportunity_id'),
                data.get('type', 'note'), data.get('subject'),
                data.get('description'), data.get('outcome'),
                data.get('next_action'), data.get('next_action_date'),
                data.get('created_by')
            ))

            # Mettre a jour last_contact_date
            cursor.execute('''
                UPDATE crm_contacts SET last_contact_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (contact_id,))

            conn.commit()
            interaction_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            return {'error': str(e)}

    def create_opportunity(self, contact_id, data):
        """Cree une opportunite de vente"""
        log_agent(self.name, f"Nouvelle opportunite pour contact {contact_id}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO crm_opportunities
                (contact_id, title, value, currency, stage, probability,
                 expected_close_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contact_id, data.get('title'), data.get('value', 0),
                data.get('currency', 'CAD'), data.get('stage', 'qualification'),
                data.get('probability', 10), data.get('expected_close_date'),
                data.get('notes')
            ))

            conn.commit()
            opp_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'opportunity_id': opp_id}
        except Exception as e:
            return {'error': str(e)}

    def update_opportunity_stage(self, opportunity_id, stage, won=None, loss_reason=None):
        """Met a jour l'etape d'une opportunite"""
        log_agent(self.name, f"Mise a jour opportunite {opportunity_id} -> {stage}")

        try:
            conn = get_db()
            cursor = conn.cursor()

            # Recuperer la probabilite de l'etape
            cursor.execute('SELECT probability FROM crm_pipeline_stages WHERE name = ?', (stage,))
            prob_row = cursor.fetchone()
            probability = prob_row[0] if prob_row else 0

            if won is not None:
                cursor.execute('''
                    UPDATE crm_opportunities SET
                        stage = ?, probability = ?, won = ?,
                        actual_close_date = CURRENT_TIMESTAMP,
                        loss_reason = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (stage, probability, won, loss_reason, opportunity_id))

                # Mettre a jour le statut du contact
                cursor.execute('SELECT contact_id FROM crm_opportunities WHERE id = ?', (opportunity_id,))
                contact = cursor.fetchone()
                if contact:
                    new_status = 'client' if won else 'lost'
                    cursor.execute('UPDATE crm_contacts SET status = ?, type = ? WHERE id = ?',
                                   (new_status, 'client' if won else 'lead', contact[0]))
            else:
                cursor.execute('''
                    UPDATE crm_opportunities SET
                        stage = ?, probability = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (stage, probability, opportunity_id))

            conn.commit()
            conn.close()

            return {'success': True, 'new_stage': stage, 'probability': probability}
        except Exception as e:
            return {'error': str(e)}

    def get_pipeline(self):
        """Recupere le pipeline complet"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Recuperer les etapes
            cursor.execute('SELECT * FROM crm_pipeline_stages ORDER BY order_num')
            stages = cursor.fetchall()

            pipeline = []
            total_value = 0
            weighted_value = 0

            for stage in stages:
                cursor.execute('''
                    SELECT o.id, o.title, o.value, o.probability, o.expected_close_date,
                           c.first_name, c.last_name, c.company
                    FROM crm_opportunities o
                    JOIN crm_contacts c ON o.contact_id = c.id
                    WHERE o.stage = ? AND o.won IS NULL
                    ORDER BY o.expected_close_date
                ''', (stage[1],))
                opps = cursor.fetchall()

                stage_value = sum(o[2] or 0 for o in opps)
                stage_weighted = sum((o[2] or 0) * (o[3] or 0) / 100 for o in opps)

                total_value += stage_value
                weighted_value += stage_weighted

                pipeline.append({
                    'id': stage[0],
                    'name': stage[1],
                    'order': stage[2],
                    'probability': stage[3],
                    'color': stage[4],
                    'count': len(opps),
                    'value': round(stage_value, 2),
                    'weighted_value': round(stage_weighted, 2),
                    'opportunities': [{
                        'id': o[0], 'title': o[1], 'value': o[2],
                        'probability': o[3], 'expected_close': o[4],
                        'contact_name': f"{o[5] or ''} {o[6] or ''}".strip(),
                        'company': o[7]
                    } for o in opps]
                })

            conn.close()

            return {
                'pipeline': pipeline,
                'summary': {
                    'total_value': round(total_value, 2),
                    'weighted_value': round(weighted_value, 2),
                    'total_opportunities': sum(s['count'] for s in pipeline)
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def create_task(self, data):
        """Cree une tache"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO crm_tasks
                (contact_id, opportunity_id, title, description, due_date,
                 priority, status, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            ''', (
                data.get('contact_id'), data.get('opportunity_id'),
                data.get('title'), data.get('description'),
                data.get('due_date'), data.get('priority', 'medium'),
                data.get('assigned_to')
            ))

            conn.commit()
            task_id = cursor.lastrowid
            conn.close()

            return {'success': True, 'task_id': task_id}
        except Exception as e:
            return {'error': str(e)}

    def get_tasks(self, filters=None):
        """Liste les taches"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT t.id, t.title, t.description, t.due_date, t.priority,
                       t.status, t.assigned_to, c.first_name, c.last_name
                FROM crm_tasks t
                LEFT JOIN crm_contacts c ON t.contact_id = c.id
            '''
            params = []
            conditions = []

            if filters:
                if filters.get('status'):
                    conditions.append("t.status = ?")
                    params.append(filters['status'])
                if filters.get('assigned_to'):
                    conditions.append("t.assigned_to = ?")
                    params.append(filters['assigned_to'])
                if filters.get('priority'):
                    conditions.append("t.priority = ?")
                    params.append(filters['priority'])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY t.due_date"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'title': r[1], 'description': r[2],
                'due_date': r[3], 'priority': r[4], 'status': r[5],
                'assigned_to': r[6],
                'contact_name': f"{r[7] or ''} {r[8] or ''}".strip()
            } for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def complete_task(self, task_id):
        """Complete une tache"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE crm_tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (task_id,))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_dashboard_stats(self):
        """Statistiques CRM pour dashboard"""
        log_agent(self.name, "Generation stats dashboard CRM")

        try:
            conn = get_db()
            cursor = conn.cursor()

            # Contacts
            cursor.execute('SELECT COUNT(*) FROM crm_contacts')
            total_contacts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM crm_contacts WHERE type = 'lead'")
            total_leads = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM crm_contacts WHERE type = 'client'")
            total_clients = cursor.fetchone()[0]

            # Contacts ce mois
            cursor.execute('''
                SELECT COUNT(*) FROM crm_contacts
                WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            ''')
            new_this_month = cursor.fetchone()[0]

            # Opportunites
            cursor.execute('SELECT COUNT(*), SUM(value) FROM crm_opportunities WHERE won IS NULL')
            opp_row = cursor.fetchone()
            open_opportunities = opp_row[0] or 0
            pipeline_value = opp_row[1] or 0

            cursor.execute('SELECT COUNT(*), SUM(value) FROM crm_opportunities WHERE won = 1')
            won_row = cursor.fetchone()
            won_count = won_row[0] or 0
            won_value = won_row[1] or 0

            # Taches
            cursor.execute("SELECT COUNT(*) FROM crm_tasks WHERE status = 'pending'")
            pending_tasks = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) FROM crm_tasks
                WHERE status = 'pending' AND due_date < date('now')
            ''')
            overdue_tasks = cursor.fetchone()[0]

            # Taux de conversion
            cursor.execute('SELECT COUNT(*) FROM crm_opportunities WHERE won IS NOT NULL')
            closed_opps = cursor.fetchone()[0]
            conversion_rate = round((won_count / closed_opps * 100) if closed_opps > 0 else 0, 1)

            conn.close()

            return {
                'contacts': {
                    'total': total_contacts,
                    'leads': total_leads,
                    'clients': total_clients,
                    'new_this_month': new_this_month
                },
                'opportunities': {
                    'open': open_opportunities,
                    'pipeline_value': round(pipeline_value, 2),
                    'won_count': won_count,
                    'won_value': round(won_value, 2),
                    'conversion_rate': conversion_rate
                },
                'tasks': {
                    'pending': pending_tasks,
                    'overdue': overdue_tasks
                },
                'calculated_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    def score_lead(self, contact_id):
        """Calcule le score d'un lead avec IA"""
        log_agent(self.name, f"Scoring lead {contact_id}")

        contact = self.get_contact(contact_id)
        if 'error' in contact:
            return contact

        # Criteres de scoring
        score = 0
        factors = []

        # Email professionnel
        email = contact.get('email', '')
        if email and not any(d in email for d in ['gmail', 'hotmail', 'yahoo', 'outlook']):
            score += 15
            factors.append("Email professionnel (+15)")

        # Entreprise renseignee
        if contact.get('company'):
            score += 10
            factors.append("Entreprise renseignee (+10)")

        # Telephone
        if contact.get('phone'):
            score += 10
            factors.append("Telephone fourni (+10)")

        # Site web
        if contact.get('website'):
            score += 10
            factors.append("Site web fourni (+10)")

        # Nombre d'interactions
        interactions = len(contact.get('interactions', []))
        if interactions >= 3:
            score += 20
            factors.append(f"Engagement eleve ({interactions} interactions) (+20)")
        elif interactions >= 1:
            score += 10
            factors.append(f"Engagement moyen ({interactions} interactions) (+10)")

        # Opportunite ouverte
        if contact.get('opportunities'):
            score += 25
            factors.append("Opportunite en cours (+25)")

        # Mettre a jour le score
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE crm_contacts SET score = ? WHERE id = ?', (score, contact_id))
            conn.commit()
            conn.close()
        except:
            pass

        return {
            'contact_id': contact_id,
            'score': score,
            'grade': 'A' if score >= 70 else 'B' if score >= 50 else 'C' if score >= 30 else 'D',
            'factors': factors,
            'recommendation': self._get_score_recommendation(score)
        }

    def _get_score_recommendation(self, score):
        """Recommandation basee sur le score"""
        if score >= 70:
            return "Lead tres qualifie - Contacter en priorite pour closing"
        elif score >= 50:
            return "Lead qualifie - Planifier un appel de decouverte"
        elif score >= 30:
            return "Lead tiede - Nurturing par email recommande"
        else:
            return "Lead froid - Ajouter a sequence automatisee"


# ============================================
# AGENT 48: ACCOUNTING AGENT - Comptabilite
# ============================================

class AccountingAgent:
    """
    Agent de comptabilite pour PME quebecoises
    - Journal des transactions
    - Grand livre et balance
    - Etats financiers (bilan, resultats)
    - TPS/TVQ automatique
    - Categories depenses/revenus
    - Rapports financiers
    """
    name = "Accounting Agent"

    # Categories de transactions standard Quebec
    EXPENSE_CATEGORIES = [
        {'code': 'SAL', 'name': 'Salaires et avantages', 'tax_deductible': True},
        {'code': 'FOUR', 'name': 'Fournitures de bureau', 'tax_deductible': True},
        {'code': 'LOYER', 'name': 'Loyer et occupation', 'tax_deductible': True},
        {'code': 'UTIL', 'name': 'Electricite, eau, gaz', 'tax_deductible': True},
        {'code': 'TEL', 'name': 'Telecommunications', 'tax_deductible': True},
        {'code': 'MKTG', 'name': 'Marketing et publicite', 'tax_deductible': True},
        {'code': 'TRANSP', 'name': 'Transport et vehicule', 'tax_deductible': True},
        {'code': 'REPAS', 'name': 'Repas et representation', 'tax_deductible': True, 'deduction_rate': 0.5},
        {'code': 'ASSUR', 'name': 'Assurances', 'tax_deductible': True},
        {'code': 'PROF', 'name': 'Services professionnels', 'tax_deductible': True},
        {'code': 'FORM', 'name': 'Formation et developpement', 'tax_deductible': True},
        {'code': 'EQUIP', 'name': 'Equipement et materiel', 'tax_deductible': True},
        {'code': 'TECH', 'name': 'Logiciels et abonnements', 'tax_deductible': True},
        {'code': 'BANK', 'name': 'Frais bancaires', 'tax_deductible': True},
        {'code': 'AUTRE', 'name': 'Autres depenses', 'tax_deductible': True},
    ]

    REVENUE_CATEGORIES = [
        {'code': 'SERV', 'name': 'Services rendus'},
        {'code': 'PROD', 'name': 'Vente de produits'},
        {'code': 'CONS', 'name': 'Consultation'},
        {'code': 'ABO', 'name': 'Abonnements'},
        {'code': 'COMM', 'name': 'Commissions'},
        {'code': 'INT', 'name': 'Interets et placements'},
        {'code': 'AUTRE', 'name': 'Autres revenus'},
    ]

    # Taux de taxes Quebec 2024
    TPS_RATE = 0.05    # Taxe federale
    TVQ_RATE = 0.09975  # Taxe Quebec

    def init_db(self):
        """Initialise les tables de comptabilite"""
        conn = get_db()
        cursor = conn.cursor()

        # Table des comptes (plan comptable)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounting_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,  -- asset, liability, equity, revenue, expense
                parent_code TEXT,
                balance REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Journal des transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounting_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE NOT NULL,
                description TEXT NOT NULL,
                reference TEXT,
                category TEXT,
                amount REAL NOT NULL,
                tps REAL DEFAULT 0,
                tvq REAL DEFAULT 0,
                total REAL NOT NULL,
                type TEXT NOT NULL,  -- revenue, expense, transfer
                payment_method TEXT,
                status TEXT DEFAULT 'confirmed',
                invoice_id INTEGER,
                contact_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Lignes du journal (double-entry)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounting_journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                account_code TEXT NOT NULL,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES accounting_transactions(id)
            )
        ''')

        # Table des periodes fiscales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounting_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT DEFAULT 'open',  -- open, closed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table taxes collectees/payees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounting_taxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                tps_collected REAL DEFAULT 0,
                tps_paid REAL DEFAULT 0,
                tps_net REAL DEFAULT 0,
                tvq_collected REAL DEFAULT 0,
                tvq_paid REAL DEFAULT 0,
                tvq_net REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',  -- pending, filed, paid
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Budgets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounting_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                period TEXT NOT NULL,  -- YYYY-MM
                budget_amount REAL NOT NULL,
                actual_amount REAL DEFAULT 0,
                variance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Inserer plan comptable de base si vide
        cursor.execute('SELECT COUNT(*) FROM accounting_accounts')
        if cursor.fetchone()[0] == 0:
            base_accounts = [
                # Actifs
                ('1000', 'Actifs', 'asset', None),
                ('1100', 'Encaisse', 'asset', '1000'),
                ('1200', 'Comptes clients', 'asset', '1000'),
                ('1300', 'TPS a recevoir', 'asset', '1000'),
                ('1310', 'TVQ a recevoir', 'asset', '1000'),
                ('1500', 'Equipement', 'asset', '1000'),
                # Passifs
                ('2000', 'Passifs', 'liability', None),
                ('2100', 'Comptes fournisseurs', 'liability', '2000'),
                ('2200', 'TPS a payer', 'liability', '2000'),
                ('2210', 'TVQ a payer', 'liability', '2000'),
                ('2300', 'Salaires a payer', 'liability', '2000'),
                # Capitaux propres
                ('3000', 'Capitaux propres', 'equity', None),
                ('3100', 'Capital', 'equity', '3000'),
                ('3200', 'Benefices non repartis', 'equity', '3000'),
                # Revenus
                ('4000', 'Revenus', 'revenue', None),
                ('4100', 'Ventes de services', 'revenue', '4000'),
                ('4200', 'Ventes de produits', 'revenue', '4000'),
                ('4300', 'Autres revenus', 'revenue', '4000'),
                # Depenses
                ('5000', 'Depenses', 'expense', None),
                ('5100', 'Salaires', 'expense', '5000'),
                ('5200', 'Loyer', 'expense', '5000'),
                ('5300', 'Services publics', 'expense', '5000'),
                ('5400', 'Marketing', 'expense', '5000'),
                ('5500', 'Fournitures', 'expense', '5000'),
                ('5600', 'Telecommunications', 'expense', '5000'),
                ('5700', 'Transport', 'expense', '5000'),
                ('5800', 'Services professionnels', 'expense', '5000'),
                ('5900', 'Autres depenses', 'expense', '5000'),
            ]
            for code, name, acc_type, parent in base_accounts:
                cursor.execute('''
                    INSERT INTO accounting_accounts (code, name, type, parent_code)
                    VALUES (?, ?, ?, ?)
                ''', (code, name, acc_type, parent))

        conn.commit()
        conn.close()
        log_agent(self.name, "Tables comptabilite initialisees")
        return {'success': True}

    def add_transaction(self, data):
        """
        Ajoute une transaction avec calcul automatique TPS/TVQ
        data: {
            'date': 'YYYY-MM-DD',
            'description': str,
            'amount': float (montant avant taxes),
            'type': 'revenue' | 'expense',
            'category': str,
            'include_taxes': bool (default True),
            'payment_method': str,
            'reference': str,
            'invoice_id': int (optional),
            'contact_id': int (optional)
        }
        """
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            amount = float(data.get('amount', 0))
            include_taxes = data.get('include_taxes', True)
            trans_type = data.get('type', 'expense')

            # Calcul taxes
            if include_taxes:
                tps = round(amount * self.TPS_RATE, 2)
                tvq = round(amount * self.TVQ_RATE, 2)
                total = round(amount + tps + tvq, 2)
            else:
                tps = 0
                tvq = 0
                total = amount

            cursor.execute('''
                INSERT INTO accounting_transactions
                (transaction_date, description, reference, category, amount, tps, tvq, total,
                 type, payment_method, invoice_id, contact_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('date', datetime.now().strftime('%Y-%m-%d')),
                data.get('description', ''),
                data.get('reference', ''),
                data.get('category', ''),
                amount, tps, tvq, total,
                trans_type,
                data.get('payment_method', ''),
                data.get('invoice_id'),
                data.get('contact_id'),
                data.get('notes', '')
            ))

            transaction_id = cursor.lastrowid

            # Creer entrees journal (double-entry)
            if trans_type == 'revenue':
                # Debit: Encaisse, Credit: Revenus
                cursor.execute('''
                    INSERT INTO accounting_journal_entries
                    (transaction_id, account_code, debit, credit, description)
                    VALUES (?, '1100', ?, 0, ?)
                ''', (transaction_id, total, data.get('description', '')))

                cursor.execute('''
                    INSERT INTO accounting_journal_entries
                    (transaction_id, account_code, debit, credit, description)
                    VALUES (?, '4100', 0, ?, ?)
                ''', (transaction_id, amount, data.get('description', '')))

                if tps > 0:
                    cursor.execute('''
                        INSERT INTO accounting_journal_entries
                        (transaction_id, account_code, debit, credit, description)
                        VALUES (?, '2200', 0, ?, 'TPS collectee')
                    ''', (transaction_id, tps))

                if tvq > 0:
                    cursor.execute('''
                        INSERT INTO accounting_journal_entries
                        (transaction_id, account_code, debit, credit, description)
                        VALUES (?, '2210', 0, ?, 'TVQ collectee')
                    ''', (transaction_id, tvq))

            else:  # expense
                # Debit: Depense, Credit: Encaisse
                cursor.execute('''
                    INSERT INTO accounting_journal_entries
                    (transaction_id, account_code, debit, credit, description)
                    VALUES (?, '5900', ?, 0, ?)
                ''', (transaction_id, amount, data.get('description', '')))

                cursor.execute('''
                    INSERT INTO accounting_journal_entries
                    (transaction_id, account_code, debit, credit, description)
                    VALUES (?, '1100', 0, ?, ?)
                ''', (transaction_id, total, data.get('description', '')))

                if tps > 0:
                    cursor.execute('''
                        INSERT INTO accounting_journal_entries
                        (transaction_id, account_code, debit, credit, description)
                        VALUES (?, '1300', ?, 0, 'TPS payee')
                    ''', (transaction_id, tps))

                if tvq > 0:
                    cursor.execute('''
                        INSERT INTO accounting_journal_entries
                        (transaction_id, account_code, debit, credit, description)
                        VALUES (?, '1310', ?, 0, 'TVQ payee')
                    ''', (transaction_id, tvq))

            conn.commit()
            conn.close()

            log_agent(self.name, f"Transaction ajoutee: {data.get('description')} - {total}$")

            return {
                'success': True,
                'transaction_id': transaction_id,
                'amount': amount,
                'tps': tps,
                'tvq': tvq,
                'total': total
            }

        except Exception as e:
            log_agent(self.name, f"Erreur transaction: {e}")
            return {'error': str(e)}

    def get_financial_summary(self, start_date=None, end_date=None):
        """Resume financier pour une periode"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Total revenus
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0), COALESCE(SUM(tps), 0), COALESCE(SUM(tvq), 0), COALESCE(SUM(total), 0)
                FROM accounting_transactions
                WHERE type = 'revenue' AND transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            rev = cursor.fetchone()

            # Total depenses
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0), COALESCE(SUM(tps), 0), COALESCE(SUM(tvq), 0), COALESCE(SUM(total), 0)
                FROM accounting_transactions
                WHERE type = 'expense' AND transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            exp = cursor.fetchone()

            # Nombre de transactions
            cursor.execute('''
                SELECT COUNT(*) FROM accounting_transactions
                WHERE transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            count = cursor.fetchone()[0]

            conn.close()

            revenue_total = rev[0] or 0
            expense_total = exp[0] or 0
            profit = revenue_total - expense_total

            return {
                'period': {'start': start_date, 'end': end_date},
                'revenue': {
                    'subtotal': rev[0] or 0,
                    'tps_collected': rev[1] or 0,
                    'tvq_collected': rev[2] or 0,
                    'total': rev[3] or 0
                },
                'expenses': {
                    'subtotal': exp[0] or 0,
                    'tps_paid': exp[1] or 0,
                    'tvq_paid': exp[2] or 0,
                    'total': exp[3] or 0
                },
                'profit': {
                    'gross': profit,
                    'margin_percent': round((profit / revenue_total * 100), 1) if revenue_total > 0 else 0
                },
                'taxes': {
                    'tps_net': (rev[1] or 0) - (exp[1] or 0),
                    'tvq_net': (rev[2] or 0) - (exp[2] or 0),
                    'total_tax_liability': ((rev[1] or 0) - (exp[1] or 0)) + ((rev[2] or 0) - (exp[2] or 0))
                },
                'transaction_count': count
            }

        except Exception as e:
            return {'error': str(e)}

    def get_income_statement(self, start_date=None, end_date=None):
        """Etat des resultats (Profit & Loss)"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                # Debut annee fiscale (janvier)
                start_date = datetime.now().replace(month=1, day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Revenus par categorie
            cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM accounting_transactions
                WHERE type = 'revenue' AND transaction_date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            ''', (start_date, end_date))
            revenues = [{'category': r[0] or 'Non categorise', 'amount': r[1]} for r in cursor.fetchall()]

            # Depenses par categorie
            cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM accounting_transactions
                WHERE type = 'expense' AND transaction_date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            ''', (start_date, end_date))
            expenses = [{'category': e[0] or 'Non categorise', 'amount': e[1]} for e in cursor.fetchall()]

            conn.close()

            total_revenue = sum(r['amount'] for r in revenues)
            total_expenses = sum(e['amount'] for e in expenses)
            net_income = total_revenue - total_expenses

            return {
                'period': {'start': start_date, 'end': end_date},
                'revenues': {
                    'items': revenues,
                    'total': total_revenue
                },
                'expenses': {
                    'items': expenses,
                    'total': total_expenses
                },
                'gross_profit': total_revenue - total_expenses,
                'net_income': net_income,
                'profit_margin': round((net_income / total_revenue * 100), 1) if total_revenue > 0 else 0
            }

        except Exception as e:
            return {'error': str(e)}

    def get_balance_sheet(self):
        """Bilan comptable"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Calculer les soldes de chaque compte
            cursor.execute('''
                SELECT a.code, a.name, a.type,
                       COALESCE(SUM(j.debit), 0) as total_debit,
                       COALESCE(SUM(j.credit), 0) as total_credit
                FROM accounting_accounts a
                LEFT JOIN accounting_journal_entries j ON a.code = j.account_code
                GROUP BY a.code
                ORDER BY a.code
            ''')
            accounts = cursor.fetchall()
            conn.close()

            assets = []
            liabilities = []
            equity = []

            for code, name, acc_type, debit, credit in accounts:
                balance = debit - credit
                if acc_type == 'asset':
                    assets.append({'code': code, 'name': name, 'balance': balance})
                elif acc_type == 'liability':
                    balance = credit - debit  # Passifs = credit - debit
                    liabilities.append({'code': code, 'name': name, 'balance': balance})
                elif acc_type == 'equity':
                    balance = credit - debit
                    equity.append({'code': code, 'name': name, 'balance': balance})

            total_assets = sum(a['balance'] for a in assets)
            total_liabilities = sum(l['balance'] for l in liabilities)
            total_equity = sum(e['balance'] for e in equity)

            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'assets': {
                    'items': assets,
                    'total': total_assets
                },
                'liabilities': {
                    'items': liabilities,
                    'total': total_liabilities
                },
                'equity': {
                    'items': equity,
                    'total': total_equity
                },
                'balanced': abs(total_assets - (total_liabilities + total_equity)) < 0.01
            }

        except Exception as e:
            return {'error': str(e)}

    def get_tax_report(self, quarter=None, year=None):
        """Rapport TPS/TVQ pour declaration"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            now = datetime.now()
            if not year:
                year = now.year
            if not quarter:
                quarter = (now.month - 1) // 3 + 1

            # Calculer dates du trimestre
            quarter_starts = {
                1: f"{year}-01-01",
                2: f"{year}-04-01",
                3: f"{year}-07-01",
                4: f"{year}-10-01"
            }
            quarter_ends = {
                1: f"{year}-03-31",
                2: f"{year}-06-30",
                3: f"{year}-09-30",
                4: f"{year}-12-31"
            }

            start_date = quarter_starts[quarter]
            end_date = quarter_ends[quarter]

            # TPS/TVQ collectees (revenus)
            cursor.execute('''
                SELECT COALESCE(SUM(tps), 0), COALESCE(SUM(tvq), 0)
                FROM accounting_transactions
                WHERE type = 'revenue' AND transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            collected = cursor.fetchone()

            # TPS/TVQ payees (depenses)
            cursor.execute('''
                SELECT COALESCE(SUM(tps), 0), COALESCE(SUM(tvq), 0)
                FROM accounting_transactions
                WHERE type = 'expense' AND transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            paid = cursor.fetchone()

            conn.close()

            tps_collected = collected[0] or 0
            tps_paid = paid[0] or 0
            tvq_collected = collected[1] or 0
            tvq_paid = paid[1] or 0

            tps_net = tps_collected - tps_paid
            tvq_net = tvq_collected - tvq_paid

            return {
                'period': {
                    'quarter': quarter,
                    'year': year,
                    'start': start_date,
                    'end': end_date
                },
                'tps': {
                    'collected': tps_collected,
                    'paid': tps_paid,
                    'net': tps_net,
                    'status': 'a payer' if tps_net > 0 else 'credit'
                },
                'tvq': {
                    'collected': tvq_collected,
                    'paid': tvq_paid,
                    'net': tvq_net,
                    'status': 'a payer' if tvq_net > 0 else 'credit'
                },
                'total_due': tps_net + tvq_net if (tps_net + tvq_net) > 0 else 0,
                'total_credit': abs(tps_net + tvq_net) if (tps_net + tvq_net) < 0 else 0,
                'due_date': self._get_tax_due_date(quarter, year)
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_tax_due_date(self, quarter, year):
        """Date limite de remise TPS/TVQ"""
        due_dates = {
            1: f"{year}-04-30",
            2: f"{year}-07-31",
            3: f"{year}-10-31",
            4: f"{year + 1}-01-31"
        }
        return due_dates.get(quarter, '')

    def get_expense_breakdown(self, start_date=None, end_date=None):
        """Ventilation des depenses par categorie"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT category, COUNT(*) as count, SUM(amount) as total, AVG(amount) as average
                FROM accounting_transactions
                WHERE type = 'expense' AND transaction_date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            ''', (start_date, end_date))

            rows = cursor.fetchall()
            conn.close()

            total_expenses = sum(r[2] for r in rows) if rows else 0

            return {
                'period': {'start': start_date, 'end': end_date},
                'categories': [{
                    'category': r[0] or 'Non categorise',
                    'count': r[1],
                    'total': r[2],
                    'average': round(r[3], 2),
                    'percentage': round((r[2] / total_expenses * 100), 1) if total_expenses > 0 else 0
                } for r in rows],
                'total': total_expenses
            }

        except Exception as e:
            return {'error': str(e)}

    def list_transactions(self, filters=None, limit=50):
        """Liste les transactions avec filtres"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT id, transaction_date, description, category, amount, tps, tvq, total, type, status
                FROM accounting_transactions
            '''
            params = []
            conditions = []

            if filters:
                if filters.get('type'):
                    conditions.append("type = ?")
                    params.append(filters['type'])
                if filters.get('category'):
                    conditions.append("category = ?")
                    params.append(filters['category'])
                if filters.get('start_date'):
                    conditions.append("transaction_date >= ?")
                    params.append(filters['start_date'])
                if filters.get('end_date'):
                    conditions.append("transaction_date <= ?")
                    params.append(filters['end_date'])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY transaction_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'date': r[1], 'description': r[2],
                'category': r[3], 'amount': r[4], 'tps': r[5],
                'tvq': r[6], 'total': r[7], 'type': r[8], 'status': r[9]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def generate_financial_insights(self, months=6):
        """Genere des insights financiers avec AI - Qwen 235B via Fireworks"""
        try:
            # Obtenir donnees des derniers mois
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            summary = self.get_financial_summary(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            expenses = self.get_expense_breakdown(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            prompt = f"""Analyse les donnees financieres et genere des recommandations.

RESUME FINANCIER ({months} derniers mois):
- Revenus: {summary.get('revenue', {}).get('total', 0)}$
- Depenses: {summary.get('expenses', {}).get('total', 0)}$
- Profit: {summary.get('profit', {}).get('gross', 0)}$
- Marge: {summary.get('profit', {}).get('margin_percent', 0)}%

VENTILATION DEPENSES:
{json.dumps(expenses.get('categories', []), indent=2)}

Genere en JSON:
{{
    "health_score": 0-100,
    "status": "excellent|bon|attention|critique",
    "top_insights": ["insight1", "insight2", "insight3"],
    "cost_reduction": ["suggestion1", "suggestion2"],
    "revenue_opportunities": ["opportunity1", "opportunity2"],
    "tax_tips": ["conseil fiscal 1", "conseil fiscal 2"]
}}
"""
            # Utilise Qwen 235B via Fireworks pour tâche critique
            response = call_qwen(prompt, 1500, "Tu es un comptable CPA expert au Quebec. Reponds en JSON valide.")

            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                insights = json.loads(response.strip())
                insights['period_months'] = months
                insights['generated_at'] = datetime.now().isoformat()
                return insights

            return {'error': 'Impossible de generer les insights'}

        except Exception as e:
            return {'error': str(e)}

    def get_categories(self):
        """Retourne les categories disponibles"""
        return {
            'expense_categories': self.EXPENSE_CATEGORIES,
            'revenue_categories': self.REVENUE_CATEGORIES
        }


# ============================================
# AGENT 49: CALENDAR AGENT - Calendrier/Reservations
# ============================================

class CalendarAgent:
    """
    Agent de gestion calendrier et reservations
    - Rendez-vous et evenements
    - Reservations en ligne
    - Disponibilites configurables
    - Rappels automatiques
    - Integration CRM
    """
    name = "Calendar Agent"

    EVENT_TYPES = [
        {'code': 'MEETING', 'name': 'Reunion', 'default_duration': 60, 'color': '#3B82F6'},
        {'code': 'CALL', 'name': 'Appel', 'default_duration': 30, 'color': '#10B981'},
        {'code': 'CONSULT', 'name': 'Consultation', 'default_duration': 60, 'color': '#8B5CF6'},
        {'code': 'SERVICE', 'name': 'Service', 'default_duration': 120, 'color': '#F59E0B'},
        {'code': 'FOLLOWUP', 'name': 'Suivi', 'default_duration': 30, 'color': '#EC4899'},
        {'code': 'BLOCKED', 'name': 'Indisponible', 'default_duration': 60, 'color': '#EF4444'},
    ]

    def init_db(self):
        """Initialise les tables calendrier"""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT DEFAULT 'MEETING',
                start_datetime TIMESTAMP NOT NULL,
                end_datetime TIMESTAMP NOT NULL,
                all_day INTEGER DEFAULT 0,
                location TEXT,
                video_link TEXT,
                status TEXT DEFAULT 'confirmed',
                contact_id INTEGER,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                assigned_to TEXT,
                color TEXT,
                reminder_minutes INTEGER DEFAULT 30,
                reminder_sent INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                is_available INTEGER DEFAULT 1,
                slot_duration INTEGER DEFAULT 60,
                buffer_time INTEGER DEFAULT 15,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                duration INTEGER DEFAULT 60,
                price REAL DEFAULT 0,
                buffer_after INTEGER DEFAULT 15,
                max_advance_days INTEGER DEFAULT 30,
                min_advance_hours INTEGER DEFAULT 24,
                is_active INTEGER DEFAULT 1,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER,
                event_id INTEGER,
                client_name TEXT NOT NULL,
                client_email TEXT NOT NULL,
                client_phone TEXT,
                booking_date DATE NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                confirmation_code TEXT UNIQUE,
                notes TEXT,
                source TEXT DEFAULT 'website',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES calendar_services(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                booking_id INTEGER,
                reminder_type TEXT DEFAULT 'email',
                scheduled_at TIMESTAMP NOT NULL,
                sent_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Disponibilites par defaut Lun-Ven 9h-17h
        cursor.execute('SELECT COUNT(*) FROM calendar_availability')
        if cursor.fetchone()[0] == 0:
            for day in range(0, 5):
                cursor.execute('''
                    INSERT INTO calendar_availability (day_of_week, start_time, end_time, slot_duration)
                    VALUES (?, '09:00', '17:00', 60)
                ''', (day,))

        conn.commit()
        conn.close()
        log_agent(self.name, "Tables calendrier initialisees")
        return {'success': True}

    def create_event(self, data):
        """Cree un evenement"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            event_type = data.get('event_type', 'MEETING')
            type_info = next((t for t in self.EVENT_TYPES if t['code'] == event_type), self.EVENT_TYPES[0])

            start_dt = data.get('start_datetime')
            end_dt = data.get('end_datetime')

            if not end_dt and start_dt:
                start = datetime.fromisoformat(start_dt.replace('Z', '').replace('T', ' ').split('+')[0])
                end = start + timedelta(minutes=type_info['default_duration'])
                end_dt = end.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO calendar_events
                (title, description, event_type, start_datetime, end_datetime, all_day,
                 location, video_link, status, contact_id, contact_name, contact_email,
                 contact_phone, assigned_to, color, reminder_minutes, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('title', 'Nouveau RDV'),
                data.get('description', ''),
                event_type, start_dt, end_dt,
                1 if data.get('all_day') else 0,
                data.get('location', ''),
                data.get('video_link', ''),
                data.get('status', 'confirmed'),
                data.get('contact_id'),
                data.get('contact_name', ''),
                data.get('contact_email', ''),
                data.get('contact_phone', ''),
                data.get('assigned_to', ''),
                data.get('color', type_info['color']),
                data.get('reminder_minutes', 30),
                data.get('notes', '')
            ))

            event_id = cursor.lastrowid
            conn.commit()
            conn.close()

            log_agent(self.name, f"Evenement cree: {data.get('title')}")
            return {'success': True, 'event_id': event_id, 'start': start_dt, 'end': end_dt}

        except Exception as e:
            return {'error': str(e)}

    def get_events(self, start_date=None, end_date=None, filters=None):
        """Liste les evenements"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

            query = '''
                SELECT id, title, description, event_type, start_datetime, end_datetime,
                       all_day, location, video_link, status, contact_name, contact_email,
                       assigned_to, color, notes
                FROM calendar_events
                WHERE DATE(start_datetime) BETWEEN ? AND ?
            '''
            params = [start_date, end_date]

            if filters:
                if filters.get('status'):
                    query += " AND status = ?"
                    params.append(filters['status'])
                if filters.get('event_type'):
                    query += " AND event_type = ?"
                    params.append(filters['event_type'])

            query += " ORDER BY start_datetime ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'title': r[1], 'description': r[2], 'event_type': r[3],
                'start': r[4], 'end': r[5], 'all_day': bool(r[6]), 'location': r[7],
                'video_link': r[8], 'status': r[9], 'contact_name': r[10],
                'contact_email': r[11], 'assigned_to': r[12], 'color': r[13], 'notes': r[14]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def update_event(self, event_id, data):
        """Met a jour un evenement"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            updates = []
            values = []
            fields = ['title', 'description', 'event_type', 'start_datetime', 'end_datetime',
                      'location', 'video_link', 'status', 'contact_name', 'contact_email',
                      'assigned_to', 'color', 'notes']

            for field in fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])

            if not updates:
                return {'error': 'Aucune donnee'}

            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(event_id)

            cursor.execute(f'UPDATE calendar_events SET {", ".join(updates)} WHERE id = ?', values)
            conn.commit()
            conn.close()

            return {'success': True, 'event_id': event_id}

        except Exception as e:
            return {'error': str(e)}

    def cancel_event(self, event_id, reason=None):
        """Annule un evenement"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE calendar_events SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (event_id,))

            conn.commit()
            conn.close()
            return {'success': True, 'event_id': event_id, 'status': 'cancelled'}

        except Exception as e:
            return {'error': str(e)}

    def get_availability(self, date=None, service_id=None):
        """Creneaux disponibles pour une date"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            target_date = datetime.strptime(date, '%Y-%m-%d')
            day_of_week = target_date.weekday()

            cursor.execute('''
                SELECT start_time, end_time, slot_duration, buffer_time
                FROM calendar_availability WHERE day_of_week = ? AND is_available = 1
            ''', (day_of_week,))

            avail = cursor.fetchone()
            if not avail:
                conn.close()
                return {'date': date, 'available': False, 'slots': []}

            start_time, end_time, slot_duration, buffer_time = avail

            if service_id:
                cursor.execute('SELECT duration FROM calendar_services WHERE id = ?', (service_id,))
                svc = cursor.fetchone()
                if svc:
                    slot_duration = svc[0]

            cursor.execute('''
                SELECT start_datetime, end_datetime FROM calendar_events
                WHERE DATE(start_datetime) = ? AND status != 'cancelled'
            ''', (date,))
            existing = [(r[0], r[1]) for r in cursor.fetchall()]
            conn.close()

            slots = []
            current = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
            end = datetime.strptime(f"{date} {end_time}", '%Y-%m-%d %H:%M')

            while current + timedelta(minutes=slot_duration) <= end:
                slot_end = current + timedelta(minutes=slot_duration)
                is_free = True

                for ev_start, ev_end in existing:
                    es = datetime.strptime(ev_start.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    ee = datetime.strptime(ev_end.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    if not (slot_end <= es or current >= ee):
                        is_free = False
                        break

                slots.append({
                    'start': current.strftime('%H:%M'),
                    'end': slot_end.strftime('%H:%M'),
                    'available': is_free
                })
                current = slot_end + timedelta(minutes=buffer_time)

            days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            return {
                'date': date,
                'day_name': days[day_of_week],
                'available': True,
                'slots': slots,
                'available_count': len([s for s in slots if s['available']])
            }

        except Exception as e:
            return {'error': str(e)}

    def create_booking(self, data):
        """Cree une reservation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            service_id = data.get('service_id')
            duration = 60
            service_name = "Rendez-vous"

            if service_id:
                cursor.execute('SELECT name, duration FROM calendar_services WHERE id = ?', (service_id,))
                svc = cursor.fetchone()
                if svc:
                    service_name, duration = svc

            start_time = data.get('start_time', '09:00')
            booking_date = data.get('booking_date')
            start_dt = datetime.strptime(f"{booking_date} {start_time}", '%Y-%m-%d %H:%M')
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.strftime('%H:%M')

            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            cursor.execute('''
                INSERT INTO calendar_bookings
                (service_id, client_name, client_email, client_phone, booking_date,
                 start_time, end_time, status, confirmation_code, notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            ''', (
                service_id, data.get('client_name', ''), data.get('client_email', ''),
                data.get('client_phone', ''), booking_date, start_time, end_time,
                code, data.get('notes', ''), data.get('source', 'website')
            ))
            booking_id = cursor.lastrowid

            event_title = f"{service_name} - {data.get('client_name', 'Client')}"
            cursor.execute('''
                INSERT INTO calendar_events
                (title, event_type, start_datetime, end_datetime, status,
                 contact_name, contact_email, contact_phone, color, notes)
                VALUES (?, 'SERVICE', ?, ?, 'pending', ?, ?, ?, '#F59E0B', ?)
            ''', (
                event_title, f"{booking_date} {start_time}:00", f"{booking_date} {end_time}:00",
                data.get('client_name', ''), data.get('client_email', ''),
                data.get('client_phone', ''), f"Reservation #{code}"
            ))
            event_id = cursor.lastrowid

            cursor.execute('UPDATE calendar_bookings SET event_id = ? WHERE id = ?', (event_id, booking_id))
            conn.commit()
            conn.close()

            log_agent(self.name, f"Reservation: {code}")
            return {
                'success': True, 'booking_id': booking_id, 'event_id': event_id,
                'confirmation_code': code, 'date': booking_date, 'time': f"{start_time}-{end_time}"
            }

        except Exception as e:
            return {'error': str(e)}

    def confirm_booking(self, booking_id=None, confirmation_code=None):
        """Confirme une reservation"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            if confirmation_code:
                cursor.execute('SELECT id, event_id FROM calendar_bookings WHERE confirmation_code = ?', (confirmation_code,))
            else:
                cursor.execute('SELECT id, event_id FROM calendar_bookings WHERE id = ?', (booking_id,))

            booking = cursor.fetchone()
            if not booking:
                conn.close()
                return {'error': 'Reservation non trouvee'}

            booking_id, event_id = booking
            cursor.execute('UPDATE calendar_bookings SET status = "confirmed" WHERE id = ?', (booking_id,))
            cursor.execute('UPDATE calendar_events SET status = "confirmed" WHERE id = ?', (event_id,))
            conn.commit()
            conn.close()

            return {'success': True, 'booking_id': booking_id, 'status': 'confirmed'}

        except Exception as e:
            return {'error': str(e)}

    def cancel_booking(self, booking_id=None, confirmation_code=None):
        """Annule une reservation"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            if confirmation_code:
                cursor.execute('SELECT id, event_id FROM calendar_bookings WHERE confirmation_code = ?', (confirmation_code,))
            else:
                cursor.execute('SELECT id, event_id FROM calendar_bookings WHERE id = ?', (booking_id,))

            booking = cursor.fetchone()
            if not booking:
                conn.close()
                return {'error': 'Reservation non trouvee'}

            booking_id, event_id = booking
            cursor.execute('UPDATE calendar_bookings SET status = "cancelled" WHERE id = ?', (booking_id,))
            cursor.execute('UPDATE calendar_events SET status = "cancelled" WHERE id = ?', (event_id,))
            conn.commit()
            conn.close()

            return {'success': True, 'booking_id': booking_id, 'status': 'cancelled'}

        except Exception as e:
            return {'error': str(e)}

    def get_bookings(self, filters=None, limit=50):
        """Liste les reservations"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT b.id, b.service_id, s.name, b.client_name, b.client_email,
                       b.client_phone, b.booking_date, b.start_time, b.end_time,
                       b.status, b.confirmation_code, b.notes, b.created_at
                FROM calendar_bookings b
                LEFT JOIN calendar_services s ON b.service_id = s.id
            '''
            params = []
            conditions = []

            if filters:
                if filters.get('status'):
                    conditions.append("b.status = ?")
                    params.append(filters['status'])
                if filters.get('date'):
                    conditions.append("b.booking_date = ?")
                    params.append(filters['date'])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY b.booking_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'service_id': r[1], 'service_name': r[2], 'client_name': r[3],
                'client_email': r[4], 'client_phone': r[5], 'date': r[6],
                'start_time': r[7], 'end_time': r[8], 'status': r[9],
                'confirmation_code': r[10], 'notes': r[11], 'created_at': r[12]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def create_service(self, data):
        """Cree un service reservable"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO calendar_services
                (name, description, duration, price, buffer_after, max_advance_days, min_advance_hours, is_active, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name', ''), data.get('description', ''),
                data.get('duration', 60), data.get('price', 0),
                data.get('buffer_after', 15), data.get('max_advance_days', 30),
                data.get('min_advance_hours', 24), 1 if data.get('is_active', True) else 0,
                data.get('color', '#3B82F6')
            ))

            service_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'service_id': service_id}

        except Exception as e:
            return {'error': str(e)}

    def get_services(self, active_only=True):
        """Liste les services"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, name, description, duration, price, buffer_after, is_active, color FROM calendar_services'
            if active_only:
                query += " WHERE is_active = 1"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'name': r[1], 'description': r[2], 'duration': r[3],
                'price': r[4], 'buffer_after': r[5], 'is_active': bool(r[6]), 'color': r[7]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def set_availability(self, data):
        """Configure disponibilites"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            day = data.get('day_of_week')
            if day is not None:
                cursor.execute('DELETE FROM calendar_availability WHERE day_of_week = ?', (day,))
                cursor.execute('''
                    INSERT INTO calendar_availability (day_of_week, start_time, end_time, is_available, slot_duration, buffer_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    day, data.get('start_time', '09:00'), data.get('end_time', '17:00'),
                    1 if data.get('is_available', True) else 0,
                    data.get('slot_duration', 60), data.get('buffer_time', 15)
                ))

            conn.commit()
            conn.close()
            return {'success': True}

        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, start_date=None, end_date=None):
        """Statistiques calendrier"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT status, COUNT(*) FROM calendar_events
                WHERE DATE(start_datetime) BETWEEN ? AND ? GROUP BY status
            ''', (start_date, end_date))
            events = {r[0]: r[1] for r in cursor.fetchall()}

            cursor.execute('''
                SELECT status, COUNT(*) FROM calendar_bookings
                WHERE booking_date BETWEEN ? AND ? GROUP BY status
            ''', (start_date, end_date))
            bookings = {r[0]: r[1] for r in cursor.fetchall()}

            cursor.execute('''
                SELECT id, title, start_datetime, status FROM calendar_events
                WHERE start_datetime >= datetime('now') AND status != 'cancelled'
                ORDER BY start_datetime LIMIT 5
            ''')
            upcoming = [{'id': r[0], 'title': r[1], 'start': r[2], 'status': r[3]} for r in cursor.fetchall()]

            conn.close()

            total_bookings = sum(bookings.values())
            return {
                'period': {'start': start_date, 'end': end_date},
                'events': {'total': sum(events.values()), 'by_status': events},
                'bookings': {
                    'total': total_bookings, 'by_status': bookings,
                    'confirmation_rate': round(bookings.get('confirmed', 0) / total_bookings * 100, 1) if total_bookings else 0
                },
                'upcoming': upcoming
            }

        except Exception as e:
            return {'error': str(e)}

    def get_event_types(self):
        """Types d'evenements"""
        return self.EVENT_TYPES


# ============================================
# AGENT 50: CHATBOT AGENT - Assistant IA
# ============================================

class ChatbotAgent:
    """
    Agent chatbot IA pour sites web
    - Conversations intelligentes
    - Reponses automatiques FAQ
    - Capture de leads
    - Integration CRM
    - Multi-langues (FR/EN)
    - Historique conversations
    """
    name = "Chatbot Agent"

    # Intentions detectables
    INTENTS = [
        {'code': 'GREETING', 'patterns': ['bonjour', 'salut', 'allo', 'hello', 'hi']},
        {'code': 'PRICE', 'patterns': ['prix', 'cout', 'tarif', 'combien', 'price', 'cost']},
        {'code': 'SERVICE', 'patterns': ['service', 'offre', 'faire', 'proposez']},
        {'code': 'CONTACT', 'patterns': ['contact', 'joindre', 'appeler', 'email', 'telephone']},
        {'code': 'HOURS', 'patterns': ['heure', 'ouvert', 'horaire', 'disponible', 'quand']},
        {'code': 'LOCATION', 'patterns': ['adresse', 'situe', 'trouver', 'aller', 'localisation']},
        {'code': 'BOOKING', 'patterns': ['rendez-vous', 'rdv', 'reserver', 'reservation', 'book']},
        {'code': 'QUOTE', 'patterns': ['soumission', 'devis', 'estimation', 'quote', 'estimate']},
        {'code': 'HELP', 'patterns': ['aide', 'probleme', 'question', 'help', 'support']},
        {'code': 'THANKS', 'patterns': ['merci', 'thank', 'super', 'parfait', 'excellent']},
        {'code': 'BYE', 'patterns': ['bye', 'revoir', 'bonne', 'ciao', 'goodbye']},
    ]

    def init_db(self):
        """Initialise les tables chatbot"""
        conn = get_db()
        cursor = conn.cursor()

        # Conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                visitor_name TEXT,
                visitor_email TEXT,
                visitor_phone TEXT,
                status TEXT DEFAULT 'active',
                source TEXT DEFAULT 'website',
                language TEXT DEFAULT 'fr',
                lead_captured INTEGER DEFAULT 0,
                contact_id INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES chatbot_conversations(id)
            )
        ''')

        # Reponses pre-configurees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent TEXT NOT NULL,
                response TEXT NOT NULL,
                language TEXT DEFAULT 'fr',
                is_active INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # FAQ automatique
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                keywords TEXT,
                language TEXT DEFAULT 'fr',
                views INTEGER DEFAULT 0,
                helpful_yes INTEGER DEFAULT 0,
                helpful_no INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Config chatbot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Reponses par defaut
        cursor.execute('SELECT COUNT(*) FROM chatbot_responses')
        if cursor.fetchone()[0] == 0:
            default_responses = [
                ('GREETING', "Bonjour! Comment puis-je vous aider aujourd'hui?", 'fr'),
                ('GREETING', "Hello! How can I help you today?", 'en'),
                ('PRICE', "Pour obtenir nos tarifs, pourriez-vous me preciser le service qui vous interesse?", 'fr'),
                ('SERVICE', "Nous offrons plusieurs services. Que recherchez-vous specifiquement?", 'fr'),
                ('CONTACT', "Vous pouvez nous joindre par telephone ou email. Souhaitez-vous qu'un conseiller vous rappelle?", 'fr'),
                ('HOURS', "Nous sommes ouverts du lundi au vendredi, de 9h a 17h.", 'fr'),
                ('BOOKING', "Je peux vous aider a prendre rendez-vous. Quelle date vous conviendrait?", 'fr'),
                ('QUOTE', "Je serais ravi de preparer une soumission. Pouvez-vous me decrire votre projet?", 'fr'),
                ('HELP', "Je suis la pour vous aider! Decrivez-moi votre situation.", 'fr'),
                ('THANKS', "Je vous en prie! Y a-t-il autre chose que je puisse faire pour vous?", 'fr'),
                ('BYE', "Merci de votre visite! N'hesitez pas a revenir si vous avez d'autres questions.", 'fr'),
            ]
            for intent, response, lang in default_responses:
                cursor.execute('''
                    INSERT INTO chatbot_responses (intent, response, language)
                    VALUES (?, ?, ?)
                ''', (intent, response, lang))

        # Config par defaut
        cursor.execute('SELECT COUNT(*) FROM chatbot_config')
        if cursor.fetchone()[0] == 0:
            defaults = [
                ('welcome_message', "Bonjour! Je suis l'assistant virtuel. Comment puis-je vous aider?"),
                ('offline_message', "Nous sommes actuellement hors ligne. Laissez-nous votre message!"),
                ('ask_name', "Pour mieux vous servir, puis-je avoir votre prenom?"),
                ('ask_email', "Parfait! Et votre email pour vous recontacter?"),
                ('lead_thank_you', "Merci! Un conseiller vous contactera bientot."),
                ('business_name', "Notre Entreprise"),
                ('primary_color', "#3B82F6"),
                ('position', "bottom-right"),
            ]
            for key, value in defaults:
                cursor.execute('INSERT INTO chatbot_config (key, value) VALUES (?, ?)', (key, value))

        conn.commit()
        conn.close()
        log_agent(self.name, "Tables chatbot initialisees")
        return {'success': True}

    def start_conversation(self, session_id, source='website', language='fr'):
        """Demarre une nouvelle conversation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO chatbot_conversations (session_id, source, language)
                VALUES (?, ?, ?)
            ''', (session_id, source, language))

            conversation_id = cursor.lastrowid

            # Message de bienvenue
            cursor.execute('SELECT value FROM chatbot_config WHERE key = "welcome_message"')
            welcome = cursor.fetchone()
            welcome_msg = welcome[0] if welcome else "Bonjour! Comment puis-je vous aider?"

            cursor.execute('''
                INSERT INTO chatbot_messages (conversation_id, role, content, intent)
                VALUES (?, 'assistant', ?, 'GREETING')
            ''', (conversation_id, welcome_msg))

            conn.commit()
            conn.close()

            log_agent(self.name, f"Conversation demarree: {session_id}")

            return {
                'success': True,
                'conversation_id': conversation_id,
                'session_id': session_id,
                'message': welcome_msg
            }

        except Exception as e:
            return {'error': str(e)}

    def send_message(self, session_id, message, use_ai=True):
        """Envoie un message et obtient une reponse"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Trouver la conversation
            cursor.execute('SELECT id, language FROM chatbot_conversations WHERE session_id = ?', (session_id,))
            conv = cursor.fetchone()

            if not conv:
                conn.close()
                return {'error': 'Conversation non trouvee'}

            conversation_id, language = conv

            # Detecter l'intention
            intent, confidence = self._detect_intent(message)

            # Sauvegarder message utilisateur
            cursor.execute('''
                INSERT INTO chatbot_messages (conversation_id, role, content, intent, confidence)
                VALUES (?, 'user', ?, ?, ?)
            ''', (conversation_id, message, intent, confidence))

            cursor.execute('''
                UPDATE chatbot_conversations SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (conversation_id,))

            # Generer reponse
            if use_ai and confidence < 0.7:
                # Utiliser AI pour reponse complexe (Ollama d'abord, puis Fireworks)
                response = self._generate_ai_response(message, conversation_id, cursor)
            else:
                # Reponse pre-configuree
                cursor.execute('''
                    SELECT response FROM chatbot_responses
                    WHERE intent = ? AND language = ? AND is_active = 1
                    ORDER BY priority DESC LIMIT 1
                ''', (intent, language))
                resp = cursor.fetchone()
                response = resp[0] if resp else self._generate_ai_response(message, conversation_id, cursor)

            # Sauvegarder reponse assistant
            cursor.execute('''
                INSERT INTO chatbot_messages (conversation_id, role, content)
                VALUES (?, 'assistant', ?)
            ''', (conversation_id, response))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'response': response,
                'intent': intent,
                'confidence': confidence
            }

        except Exception as e:
            return {'error': str(e)}

    def _detect_intent(self, message):
        """Detecte l'intention du message"""
        message_lower = message.lower()
        best_intent = 'UNKNOWN'
        best_score = 0

        for intent_def in self.INTENTS:
            score = 0
            for pattern in intent_def['patterns']:
                if pattern in message_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_intent = intent_def['code']

        confidence = min(best_score / 2, 1.0) if best_score > 0 else 0
        return best_intent, confidence

    def _generate_ai_response(self, message, conversation_id, cursor):
        """Genere une reponse avec AI"""
        try:
            # Obtenir historique recent
            cursor.execute('''
                SELECT role, content FROM chatbot_messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC LIMIT 6
            ''', (conversation_id,))
            history = cursor.fetchall()[::-1]

            history_text = "\n".join([f"{r[0]}: {r[1]}" for r in history])

            prompt = f"""Tu es un assistant virtuel professionnel pour une entreprise.
Reponds de maniere concise, amicale et utile.

HISTORIQUE:
{history_text}

MESSAGE CLIENT: {message}

REGLES:
- Reponse courte (1-3 phrases max)
- Ton professionnel mais chaleureux
- Si tu ne peux pas aider, propose de contacter un humain
- Ne pas inventer d'informations

REPONSE:"""

            # Hybride: Ollama LOCAL d'abord (gratuit), puis Fireworks
            response = call_ollama(prompt, 300)
            if not response:
                response = call_qwen(prompt, 300)

            if response:
                # Nettoyer la reponse
                response = response.strip()
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                return response

            return "Je comprends votre demande. Un conseiller vous contactera sous peu pour mieux vous aider."

        except Exception:
            return "Merci pour votre message. Comment puis-je vous aider davantage?"

    def capture_lead(self, session_id, name=None, email=None, phone=None):
        """Capture les infos du lead"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            updates = ["lead_captured = 1"]
            values = []

            if name:
                updates.append("visitor_name = ?")
                values.append(name)
            if email:
                updates.append("visitor_email = ?")
                values.append(email)
            if phone:
                updates.append("visitor_phone = ?")
                values.append(phone)

            values.append(session_id)

            cursor.execute(f'''
                UPDATE chatbot_conversations SET {", ".join(updates)} WHERE session_id = ?
            ''', values)

            conn.commit()
            conn.close()

            log_agent(self.name, f"Lead capture: {email or name}")

            return {'success': True, 'lead_captured': True}

        except Exception as e:
            return {'error': str(e)}

    def end_conversation(self, session_id):
        """Termine une conversation"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE chatbot_conversations
                SET status = 'ended', ended_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))

            conn.commit()
            conn.close()

            return {'success': True, 'status': 'ended'}

        except Exception as e:
            return {'error': str(e)}

    def get_conversation(self, session_id):
        """Obtient une conversation complete"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, session_id, visitor_name, visitor_email, visitor_phone,
                       status, source, language, lead_captured, started_at, last_message_at
                FROM chatbot_conversations WHERE session_id = ?
            ''', (session_id,))

            conv = cursor.fetchone()
            if not conv:
                conn.close()
                return {'error': 'Conversation non trouvee'}

            cursor.execute('''
                SELECT role, content, intent, created_at
                FROM chatbot_messages WHERE conversation_id = ?
                ORDER BY created_at ASC
            ''', (conv[0],))

            messages = [{
                'role': m[0], 'content': m[1], 'intent': m[2], 'timestamp': m[3]
            } for m in cursor.fetchall()]

            conn.close()

            return {
                'id': conv[0], 'session_id': conv[1], 'visitor_name': conv[2],
                'visitor_email': conv[3], 'visitor_phone': conv[4], 'status': conv[5],
                'source': conv[6], 'language': conv[7], 'lead_captured': bool(conv[8]),
                'started_at': conv[9], 'last_message_at': conv[10],
                'messages': messages
            }

        except Exception as e:
            return {'error': str(e)}

    def list_conversations(self, filters=None, limit=50):
        """Liste les conversations"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT c.id, c.session_id, c.visitor_name, c.visitor_email, c.status,
                       c.lead_captured, c.started_at, c.last_message_at,
                       (SELECT COUNT(*) FROM chatbot_messages WHERE conversation_id = c.id) as msg_count
                FROM chatbot_conversations c
            '''
            params = []
            conditions = []

            if filters:
                if filters.get('status'):
                    conditions.append("c.status = ?")
                    params.append(filters['status'])
                if filters.get('lead_captured'):
                    conditions.append("c.lead_captured = 1")
                if filters.get('has_email'):
                    conditions.append("c.visitor_email IS NOT NULL")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY c.last_message_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'session_id': r[1], 'visitor_name': r[2],
                'visitor_email': r[3], 'status': r[4], 'lead_captured': bool(r[5]),
                'started_at': r[6], 'last_message_at': r[7], 'message_count': r[8]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def add_faq(self, question, answer, keywords=None, language='fr'):
        """Ajoute une FAQ"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            keywords_str = ','.join(keywords) if keywords else ''

            cursor.execute('''
                INSERT INTO chatbot_faq (question, answer, keywords, language)
                VALUES (?, ?, ?, ?)
            ''', (question, answer, keywords_str, language))

            faq_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'faq_id': faq_id}

        except Exception as e:
            return {'error': str(e)}

    def get_faqs(self, language='fr'):
        """Liste les FAQs"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, question, answer, keywords, views, helpful_yes, helpful_no
                FROM chatbot_faq WHERE language = ? AND is_active = 1
                ORDER BY views DESC
            ''', (language,))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'question': r[1], 'answer': r[2],
                'keywords': r[3].split(',') if r[3] else [],
                'views': r[4], 'helpful_yes': r[5], 'helpful_no': r[6]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def search_faq(self, query, language='fr'):
        """Recherche dans les FAQs"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            search = f"%{query}%"
            cursor.execute('''
                SELECT id, question, answer, keywords
                FROM chatbot_faq
                WHERE language = ? AND is_active = 1
                AND (question LIKE ? OR answer LIKE ? OR keywords LIKE ?)
                ORDER BY views DESC LIMIT 5
            ''', (language, search, search, search))

            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'question': r[1], 'answer': r[2],
                'keywords': r[3].split(',') if r[3] else []
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def add_response(self, intent, response, language='fr', priority=0):
        """Ajoute une reponse pre-configuree"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO chatbot_responses (intent, response, language, priority)
                VALUES (?, ?, ?, ?)
            ''', (intent, response, language, priority))

            response_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'response_id': response_id}

        except Exception as e:
            return {'error': str(e)}

    def update_config(self, key, value):
        """Met a jour la configuration"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO chatbot_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))

            conn.commit()
            conn.close()

            return {'success': True}

        except Exception as e:
            return {'error': str(e)}

    def get_config(self):
        """Obtient la configuration"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT key, value FROM chatbot_config')
            rows = cursor.fetchall()
            conn.close()

            return {r[0]: r[1] for r in rows}

        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, start_date=None, end_date=None):
        """Statistiques chatbot"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Conversations
            cursor.execute('''
                SELECT COUNT(*), SUM(CASE WHEN lead_captured = 1 THEN 1 ELSE 0 END)
                FROM chatbot_conversations
                WHERE DATE(started_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            conv_stats = cursor.fetchone()

            # Messages
            cursor.execute('''
                SELECT COUNT(*) FROM chatbot_messages m
                JOIN chatbot_conversations c ON m.conversation_id = c.id
                WHERE DATE(c.started_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            msg_count = cursor.fetchone()[0]

            # Par statut
            cursor.execute('''
                SELECT status, COUNT(*) FROM chatbot_conversations
                WHERE DATE(started_at) BETWEEN ? AND ?
                GROUP BY status
            ''', (start_date, end_date))
            by_status = {r[0]: r[1] for r in cursor.fetchall()}

            # Intentions populaires
            cursor.execute('''
                SELECT intent, COUNT(*) as cnt FROM chatbot_messages m
                JOIN chatbot_conversations c ON m.conversation_id = c.id
                WHERE m.role = 'user' AND m.intent IS NOT NULL
                AND DATE(c.started_at) BETWEEN ? AND ?
                GROUP BY intent ORDER BY cnt DESC LIMIT 5
            ''', (start_date, end_date))
            top_intents = [{'intent': r[0], 'count': r[1]} for r in cursor.fetchall()]

            conn.close()

            total_conv = conv_stats[0] or 0
            leads = conv_stats[1] or 0

            return {
                'period': {'start': start_date, 'end': end_date},
                'conversations': {
                    'total': total_conv,
                    'by_status': by_status,
                    'avg_messages': round(msg_count / total_conv, 1) if total_conv > 0 else 0
                },
                'leads': {
                    'captured': leads,
                    'conversion_rate': round(leads / total_conv * 100, 1) if total_conv > 0 else 0
                },
                'messages': {'total': msg_count},
                'top_intents': top_intents
            }

        except Exception as e:
            return {'error': str(e)}

    def get_intents(self):
        """Retourne les intentions configurees"""
        return self.INTENTS


# ============================================
# AGENT 51: NOTIFICATION AGENT - Email/SMS/Push
# ============================================

class NotificationAgent:
    """
    Agent de notifications multi-canal
    - Emails transactionnels
    - SMS (Twilio ready)
    - Push notifications
    - Templates personnalisables
    - Historique et analytics
    """
    name = "Notification Agent"

    # Types de notifications
    NOTIFICATION_TYPES = [
        {'code': 'BOOKING_CONFIRM', 'name': 'Confirmation reservation', 'channels': ['email', 'sms']},
        {'code': 'BOOKING_REMINDER', 'name': 'Rappel rendez-vous', 'channels': ['email', 'sms']},
        {'code': 'BOOKING_CANCEL', 'name': 'Annulation', 'channels': ['email']},
        {'code': 'INVOICE_SENT', 'name': 'Facture envoyee', 'channels': ['email']},
        {'code': 'INVOICE_PAID', 'name': 'Paiement recu', 'channels': ['email']},
        {'code': 'INVOICE_OVERDUE', 'name': 'Facture en retard', 'channels': ['email', 'sms']},
        {'code': 'QUOTE_SENT', 'name': 'Soumission envoyee', 'channels': ['email']},
        {'code': 'LEAD_NEW', 'name': 'Nouveau lead', 'channels': ['email', 'push']},
        {'code': 'WELCOME', 'name': 'Bienvenue', 'channels': ['email']},
        {'code': 'PASSWORD_RESET', 'name': 'Reset mot de passe', 'channels': ['email']},
        {'code': 'MARKETING', 'name': 'Marketing/Promo', 'channels': ['email']},
        {'code': 'CUSTOM', 'name': 'Personnalise', 'channels': ['email', 'sms', 'push']},
    ]

    def init_db(self):
        """Initialise les tables notifications"""
        conn = get_db()
        cursor = conn.cursor()

        # Notifications envoyees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient_email TEXT,
                recipient_phone TEXT,
                recipient_name TEXT,
                subject TEXT,
                content TEXT NOT NULL,
                template_id INTEGER,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                error_message TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                channel TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                variables TEXT,
                language TEXT DEFAULT 'fr',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Config email/SMS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Files d'attente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT NOT NULL,
                data TEXT,
                scheduled_at TIMESTAMP,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'queued',
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Templates par defaut
        cursor.execute('SELECT COUNT(*) FROM notification_templates')
        if cursor.fetchone()[0] == 0:
            templates = [
                ('Confirmation RDV', 'BOOKING_CONFIRM', 'email',
                 'Confirmation de votre rendez-vous',
                 '''Bonjour {{client_name}},

Votre rendez-vous est confirme!

Date: {{date}}
Heure: {{time}}
Service: {{service}}

Code de confirmation: {{confirmation_code}}

A bientot!
{{business_name}}''',
                 'client_name,date,time,service,confirmation_code,business_name'),

                ('Rappel RDV', 'BOOKING_REMINDER', 'email',
                 'Rappel: Votre rendez-vous demain',
                 '''Bonjour {{client_name}},

Ceci est un rappel pour votre rendez-vous:

Date: {{date}}
Heure: {{time}}

Pour annuler ou modifier: {{cancel_link}}

A demain!
{{business_name}}''',
                 'client_name,date,time,cancel_link,business_name'),

                ('Rappel RDV SMS', 'BOOKING_REMINDER', 'sms',
                 None,
                 'Rappel: RDV demain {{date}} a {{time}}. {{business_name}}',
                 'date,time,business_name'),

                ('Facture', 'INVOICE_SENT', 'email',
                 'Facture #{{invoice_number}}',
                 '''Bonjour {{client_name}},

Veuillez trouver ci-joint votre facture #{{invoice_number}}.

Montant: {{amount}}$
Date limite: {{due_date}}

Lien de paiement: {{payment_link}}

Merci pour votre confiance!
{{business_name}}''',
                 'client_name,invoice_number,amount,due_date,payment_link,business_name'),

                ('Paiement recu', 'INVOICE_PAID', 'email',
                 'Paiement recu - Merci!',
                 '''Bonjour {{client_name}},

Nous avons bien recu votre paiement de {{amount}}$.

Facture: #{{invoice_number}}
Date: {{payment_date}}

Merci!
{{business_name}}''',
                 'client_name,amount,invoice_number,payment_date,business_name'),

                ('Nouveau lead', 'LEAD_NEW', 'email',
                 'Nouveau lead: {{lead_name}}',
                 '''Nouveau lead recu!

Nom: {{lead_name}}
Email: {{lead_email}}
Telephone: {{lead_phone}}
Source: {{source}}
Message: {{message}}

Connectez-vous pour repondre: {{dashboard_link}}''',
                 'lead_name,lead_email,lead_phone,source,message,dashboard_link'),

                ('Bienvenue', 'WELCOME', 'email',
                 'Bienvenue chez {{business_name}}!',
                 '''Bonjour {{client_name}},

Bienvenue chez {{business_name}}!

Nous sommes ravis de vous compter parmi nos clients.

N'hesitez pas a nous contacter pour toute question.

Cordialement,
{{business_name}}''',
                 'client_name,business_name'),
            ]

            for name, ntype, channel, subject, content, variables in templates:
                cursor.execute('''
                    INSERT INTO notification_templates (name, type, channel, subject, content, variables)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, ntype, channel, subject, content, variables))

        conn.commit()
        conn.close()
        log_agent(self.name, "Tables notifications initialisees")
        return {'success': True}

    def send_notification(self, notification_type, channel, recipient, data, template_id=None):
        """
        Envoie une notification
        recipient: {email, phone, name}
        data: variables pour le template
        """
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Obtenir template
            if template_id:
                cursor.execute('SELECT subject, content, variables FROM notification_templates WHERE id = ?', (template_id,))
            else:
                cursor.execute('''
                    SELECT subject, content, variables FROM notification_templates
                    WHERE type = ? AND channel = ? AND is_active = 1 LIMIT 1
                ''', (notification_type, channel))

            template = cursor.fetchone()

            if not template:
                # Generer contenu avec AI si pas de template
                content = self._generate_notification_content(notification_type, data)
                subject = data.get('subject', notification_type)
            else:
                subject, content, variables = template
                # Remplacer les variables
                content = self._replace_variables(content, data)
                if subject:
                    subject = self._replace_variables(subject, data)

            # Creer notification
            cursor.execute('''
                INSERT INTO notifications
                (type, channel, recipient_email, recipient_phone, recipient_name, subject, content, template_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                notification_type, channel,
                recipient.get('email'), recipient.get('phone'), recipient.get('name'),
                subject, content, template_id
            ))

            notification_id = cursor.lastrowid

            # Envoyer selon le canal
            if channel == 'email':
                success = self._send_email(recipient.get('email'), subject, content)
            elif channel == 'sms':
                success = self._send_sms(recipient.get('phone'), content)
            else:
                success = True  # Push/autre

            # Mettre a jour statut
            status = 'sent' if success else 'failed'
            cursor.execute('''
                UPDATE notifications SET status = ?, sent_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (status, notification_id))

            conn.commit()
            conn.close()

            log_agent(self.name, f"Notification {notification_type} envoyee via {channel}")

            return {
                'success': success,
                'notification_id': notification_id,
                'channel': channel,
                'status': status
            }

        except Exception as e:
            log_agent(self.name, f"Erreur notification: {e}")
            return {'error': str(e)}

    def _replace_variables(self, template, data):
        """Remplace {{variable}} par les valeurs"""
        result = template
        for key, value in data.items():
            result = result.replace('{{' + key + '}}', str(value or ''))
        return result

    def _send_email(self, to_email, subject, content):
        """Envoie email (placeholder - a connecter avec SMTP/SendGrid)"""
        try:
            # TODO: Integrer avec service email reel
            # Pour l'instant, log seulement
            log_agent(self.name, f"EMAIL -> {to_email}: {subject[:50]}...")
            return True
        except Exception as e:
            log_agent(self.name, f"Erreur email: {e}")
            return False

    def _send_sms(self, to_phone, content):
        """Envoie SMS (placeholder - a connecter avec Twilio)"""
        try:
            # TODO: Integrer avec Twilio
            log_agent(self.name, f"SMS -> {to_phone}: {content[:50]}...")
            return True
        except Exception as e:
            log_agent(self.name, f"Erreur SMS: {e}")
            return False

    def _generate_notification_content(self, notification_type, data):
        """Genere contenu avec AI"""
        try:
            prompt = f"""Genere un message de notification professionnel.

TYPE: {notification_type}
DONNEES: {json.dumps(data, indent=2)}

REGLES:
- Court et direct
- Professionnel mais amical
- Inclure les informations importantes

MESSAGE:"""
            # Ollama pour petite tache
            response = call_ollama(prompt, 300)
            if response:
                return response.strip()
        except:
            pass

        return f"Notification: {notification_type}"

    def schedule_notification(self, notification_type, channel, recipient, data, scheduled_at):
        """Planifie une notification"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO notification_queue
                (notification_type, channel, recipient, data, scheduled_at, status)
                VALUES (?, ?, ?, ?, ?, 'queued')
            ''', (
                notification_type, channel,
                json.dumps(recipient), json.dumps(data),
                scheduled_at
            ))

            queue_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'queue_id': queue_id, 'scheduled_at': scheduled_at}

        except Exception as e:
            return {'error': str(e)}

    def process_queue(self, limit=10):
        """Traite les notifications en attente"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, notification_type, channel, recipient, data
                FROM notification_queue
                WHERE status = 'queued' AND (scheduled_at IS NULL OR scheduled_at <= datetime('now'))
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            ''', (limit,))

            items = cursor.fetchall()
            processed = 0

            for item in items:
                queue_id, ntype, channel, recipient_json, data_json = item

                try:
                    recipient = json.loads(recipient_json)
                    data = json.loads(data_json) if data_json else {}

                    result = self.send_notification(ntype, channel, recipient, data)

                    status = 'sent' if result.get('success') else 'failed'
                    cursor.execute('''
                        UPDATE notification_queue SET status = ?, attempts = attempts + 1 WHERE id = ?
                    ''', (status, queue_id))

                    processed += 1
                except Exception as e:
                    cursor.execute('''
                        UPDATE notification_queue SET status = 'failed', attempts = attempts + 1 WHERE id = ?
                    ''', (queue_id,))

            conn.commit()
            conn.close()

            return {'success': True, 'processed': processed}

        except Exception as e:
            return {'error': str(e)}

    def get_notifications(self, filters=None, limit=50):
        """Liste les notifications"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''
                SELECT id, type, channel, recipient_email, recipient_phone, recipient_name,
                       subject, status, sent_at, opened_at, created_at
                FROM notifications
            '''
            params = []
            conditions = []

            if filters:
                if filters.get('type'):
                    conditions.append("type = ?")
                    params.append(filters['type'])
                if filters.get('channel'):
                    conditions.append("channel = ?")
                    params.append(filters['channel'])
                if filters.get('status'):
                    conditions.append("status = ?")
                    params.append(filters['status'])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'type': r[1], 'channel': r[2],
                'recipient_email': r[3], 'recipient_phone': r[4], 'recipient_name': r[5],
                'subject': r[6], 'status': r[7], 'sent_at': r[8],
                'opened_at': r[9], 'created_at': r[10]
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def create_template(self, data):
        """Cree un template"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            variables = ','.join(data.get('variables', [])) if isinstance(data.get('variables'), list) else data.get('variables', '')

            cursor.execute('''
                INSERT INTO notification_templates
                (name, type, channel, subject, content, variables, language, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name', ''),
                data.get('type', 'CUSTOM'),
                data.get('channel', 'email'),
                data.get('subject'),
                data.get('content', ''),
                variables,
                data.get('language', 'fr'),
                1 if data.get('is_active', True) else 0
            ))

            template_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'template_id': template_id}

        except Exception as e:
            return {'error': str(e)}

    def get_templates(self, channel=None, notification_type=None):
        """Liste les templates"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, name, type, channel, subject, variables, language, is_active FROM notification_templates WHERE 1=1'
            params = []

            if channel:
                query += " AND channel = ?"
                params.append(channel)
            if notification_type:
                query += " AND type = ?"
                params.append(notification_type)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{
                'id': r[0], 'name': r[1], 'type': r[2], 'channel': r[3],
                'subject': r[4], 'variables': r[5].split(',') if r[5] else [],
                'language': r[6], 'is_active': bool(r[7])
            } for r in rows]

        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, start_date=None, end_date=None):
        """Statistiques notifications"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Par statut
            cursor.execute('''
                SELECT status, COUNT(*) FROM notifications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY status
            ''', (start_date, end_date))
            by_status = {r[0]: r[1] for r in cursor.fetchall()}

            # Par canal
            cursor.execute('''
                SELECT channel, COUNT(*) FROM notifications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY channel
            ''', (start_date, end_date))
            by_channel = {r[0]: r[1] for r in cursor.fetchall()}

            # Par type
            cursor.execute('''
                SELECT type, COUNT(*) FROM notifications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY type ORDER BY COUNT(*) DESC LIMIT 5
            ''', (start_date, end_date))
            top_types = [{'type': r[0], 'count': r[1]} for r in cursor.fetchall()]

            # Taux d'ouverture emails
            cursor.execute('''
                SELECT COUNT(*), SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END)
                FROM notifications
                WHERE channel = 'email' AND status = 'sent'
                AND DATE(created_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            email_stats = cursor.fetchone()

            conn.close()

            total = sum(by_status.values())
            sent = by_status.get('sent', 0)
            failed = by_status.get('failed', 0)

            return {
                'period': {'start': start_date, 'end': end_date},
                'total': total,
                'by_status': by_status,
                'by_channel': by_channel,
                'top_types': top_types,
                'delivery_rate': round(sent / total * 100, 1) if total > 0 else 0,
                'email_open_rate': round((email_stats[1] or 0) / (email_stats[0] or 1) * 100, 1)
            }

        except Exception as e:
            return {'error': str(e)}

    def get_notification_types(self):
        """Types de notifications disponibles"""
        return self.NOTIFICATION_TYPES


# ============================================
# AGENT 52: DASHBOARD AGENT - Tableau de bord unifie
# ============================================

class DashboardAgent:
    """
    Agent tableau de bord unifie
    - KPIs globaux temps reel
    - Agregation donnees tous modules
    - Graphiques et tendances
    - Alertes et insights AI
    - Widgets personnalisables
    """
    name = "Dashboard Agent"

    def get_overview(self, period_days=30):
        """Vue d'ensemble complete de l'entreprise"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            overview = {
                'period': {'start': start_str, 'end': end_str, 'days': period_days},
                'generated_at': datetime.now().isoformat(),
                'finance': self._get_finance_kpis(start_str, end_str),
                'crm': self._get_crm_kpis(start_str, end_str),
                'calendar': self._get_calendar_kpis(start_str, end_str),
                'chatbot': self._get_chatbot_kpis(start_str, end_str),
                'notifications': self._get_notification_kpis(start_str, end_str),
            }

            # Score global sante entreprise
            overview['health_score'] = self._calculate_health_score(overview)

            return overview

        except Exception as e:
            return {'error': str(e)}

    def _get_finance_kpis(self, start_date, end_date):
        """KPIs financiers"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Revenus
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0), COALESCE(SUM(total), 0)
                FROM accounting_transactions
                WHERE type = 'revenue' AND transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            rev = cursor.fetchone()

            # Depenses
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0), COALESCE(SUM(total), 0)
                FROM accounting_transactions
                WHERE type = 'expense' AND transaction_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            exp = cursor.fetchone()

            # Factures
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(total), 0)
                FROM invoices WHERE status = 'paid' AND DATE(created_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            invoices_paid = cursor.fetchone()

            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(total), 0)
                FROM invoices WHERE status = 'pending' OR status = 'overdue'
            ''')
            invoices_pending = cursor.fetchone()

            conn.close()

            revenue = rev[0] or 0
            expenses = exp[0] or 0

            return {
                'revenue': revenue,
                'revenue_with_tax': rev[1] or 0,
                'expenses': expenses,
                'expenses_with_tax': exp[1] or 0,
                'profit': revenue - expenses,
                'margin_percent': round((revenue - expenses) / revenue * 100, 1) if revenue > 0 else 0,
                'invoices_paid': {'count': invoices_paid[0] or 0, 'total': invoices_paid[1] or 0},
                'invoices_pending': {'count': invoices_pending[0] or 0, 'total': invoices_pending[1] or 0}
            }

        except:
            return {'revenue': 0, 'expenses': 0, 'profit': 0}

    def _get_crm_kpis(self, start_date, end_date):
        """KPIs CRM"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Nouveaux contacts
            cursor.execute('''
                SELECT COUNT(*) FROM crm_contacts
                WHERE DATE(created_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            new_contacts = cursor.fetchone()[0]

            # Total contacts
            cursor.execute('SELECT COUNT(*) FROM crm_contacts')
            total_contacts = cursor.fetchone()[0]

            # Opportunites
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(value), 0)
                FROM crm_opportunities WHERE status = 'open'
            ''')
            opps = cursor.fetchone()

            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(value), 0)
                FROM crm_opportunities
                WHERE status = 'won' AND DATE(created_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            won = cursor.fetchone()

            # Leads par score
            cursor.execute('''
                SELECT
                    SUM(CASE WHEN score >= 70 THEN 1 ELSE 0 END) as hot,
                    SUM(CASE WHEN score >= 50 AND score < 70 THEN 1 ELSE 0 END) as warm,
                    SUM(CASE WHEN score < 50 THEN 1 ELSE 0 END) as cold
                FROM crm_contacts WHERE type = 'lead'
            ''')
            leads = cursor.fetchone()

            conn.close()

            return {
                'new_contacts': new_contacts,
                'total_contacts': total_contacts,
                'opportunities_open': {'count': opps[0] or 0, 'value': opps[1] or 0},
                'opportunities_won': {'count': won[0] or 0, 'value': won[1] or 0},
                'leads': {'hot': leads[0] or 0, 'warm': leads[1] or 0, 'cold': leads[2] or 0}
            }

        except:
            return {'new_contacts': 0, 'total_contacts': 0}

    def _get_calendar_kpis(self, start_date, end_date):
        """KPIs calendrier"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Evenements
            cursor.execute('''
                SELECT status, COUNT(*) FROM calendar_events
                WHERE DATE(start_datetime) BETWEEN ? AND ?
                GROUP BY status
            ''', (start_date, end_date))
            events = {r[0]: r[1] for r in cursor.fetchall()}

            # Reservations
            cursor.execute('''
                SELECT status, COUNT(*) FROM calendar_bookings
                WHERE booking_date BETWEEN ? AND ?
                GROUP BY status
            ''', (start_date, end_date))
            bookings = {r[0]: r[1] for r in cursor.fetchall()}

            # Prochains RDV
            cursor.execute('''
                SELECT COUNT(*) FROM calendar_events
                WHERE start_datetime >= datetime('now') AND status = 'confirmed'
            ''')
            upcoming = cursor.fetchone()[0]

            conn.close()

            total_bookings = sum(bookings.values())

            return {
                'events_total': sum(events.values()),
                'events_by_status': events,
                'bookings_total': total_bookings,
                'bookings_by_status': bookings,
                'booking_confirmation_rate': round(bookings.get('confirmed', 0) / total_bookings * 100, 1) if total_bookings > 0 else 0,
                'upcoming_appointments': upcoming
            }

        except:
            return {'events_total': 0, 'bookings_total': 0}

    def _get_chatbot_kpis(self, start_date, end_date):
        """KPIs chatbot"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*), SUM(CASE WHEN lead_captured = 1 THEN 1 ELSE 0 END)
                FROM chatbot_conversations
                WHERE DATE(started_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            convs = cursor.fetchone()

            cursor.execute('''
                SELECT COUNT(*) FROM chatbot_messages m
                JOIN chatbot_conversations c ON m.conversation_id = c.id
                WHERE DATE(c.started_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            messages = cursor.fetchone()[0]

            conn.close()

            total_convs = convs[0] or 0
            leads = convs[1] or 0

            return {
                'conversations': total_convs,
                'messages': messages,
                'leads_captured': leads,
                'conversion_rate': round(leads / total_convs * 100, 1) if total_convs > 0 else 0,
                'avg_messages': round(messages / total_convs, 1) if total_convs > 0 else 0
            }

        except:
            return {'conversations': 0, 'leads_captured': 0}

    def _get_notification_kpis(self, start_date, end_date):
        """KPIs notifications"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT status, COUNT(*) FROM notifications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY status
            ''', (start_date, end_date))
            by_status = {r[0]: r[1] for r in cursor.fetchall()}

            cursor.execute('''
                SELECT channel, COUNT(*) FROM notifications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY channel
            ''', (start_date, end_date))
            by_channel = {r[0]: r[1] for r in cursor.fetchall()}

            conn.close()

            total = sum(by_status.values())
            sent = by_status.get('sent', 0)

            return {
                'total': total,
                'by_status': by_status,
                'by_channel': by_channel,
                'delivery_rate': round(sent / total * 100, 1) if total > 0 else 0
            }

        except:
            return {'total': 0}

    def _calculate_health_score(self, data):
        """Calcule un score de sante global 0-100"""
        score = 50  # Base

        try:
            # Finance (+/- 20 points)
            finance = data.get('finance', {})
            if finance.get('profit', 0) > 0:
                score += 15
            if finance.get('margin_percent', 0) > 20:
                score += 5

            # CRM (+/- 15 points)
            crm = data.get('crm', {})
            if crm.get('new_contacts', 0) > 5:
                score += 10
            if crm.get('opportunities_won', {}).get('count', 0) > 0:
                score += 5

            # Calendar (+/- 10 points)
            calendar = data.get('calendar', {})
            if calendar.get('booking_confirmation_rate', 0) > 80:
                score += 10

            # Chatbot (+/- 10 points)
            chatbot = data.get('chatbot', {})
            if chatbot.get('conversion_rate', 0) > 10:
                score += 10

            # Notifications (+/- 5 points)
            notifs = data.get('notifications', {})
            if notifs.get('delivery_rate', 0) > 95:
                score += 5

        except:
            pass

        return min(100, max(0, score))

    def get_revenue_trend(self, months=6):
        """Tendance revenus par mois"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            trends = []
            for i in range(months - 1, -1, -1):
                date = datetime.now() - timedelta(days=i * 30)
                month_start = date.replace(day=1).strftime('%Y-%m-%d')
                next_month = (date.replace(day=28) + timedelta(days=4)).replace(day=1)
                month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')

                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM accounting_transactions
                    WHERE type = 'revenue' AND transaction_date BETWEEN ? AND ?
                ''', (month_start, month_end))

                revenue = cursor.fetchone()[0]
                trends.append({
                    'month': date.strftime('%Y-%m'),
                    'month_name': date.strftime('%B'),
                    'revenue': revenue
                })

            conn.close()
            return trends

        except Exception as e:
            return {'error': str(e)}

    def get_top_metrics(self):
        """Metriques top pour widgets"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Revenus ce mois
            month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM accounting_transactions
                WHERE type = 'revenue' AND transaction_date >= ?
            ''', (month_start,))
            monthly_revenue = cursor.fetchone()[0]

            # RDV aujourd'hui
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM calendar_events
                WHERE DATE(start_datetime) = ? AND status = 'confirmed'
            ''', (today,))
            today_appointments = cursor.fetchone()[0]

            # Leads actifs
            cursor.execute('''
                SELECT COUNT(*) FROM crm_contacts
                WHERE type = 'lead' AND status = 'active'
            ''')
            active_leads = cursor.fetchone()[0]

            # Factures en attente
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(total), 0) FROM invoices
                WHERE status IN ('pending', 'overdue')
            ''')
            pending = cursor.fetchone()

            # Conversations actives chatbot
            cursor.execute('''
                SELECT COUNT(*) FROM chatbot_conversations
                WHERE status = 'active'
            ''')
            active_chats = cursor.fetchone()[0]

            conn.close()

            return {
                'monthly_revenue': monthly_revenue,
                'today_appointments': today_appointments,
                'active_leads': active_leads,
                'pending_invoices': {'count': pending[0], 'total': pending[1]},
                'active_chats': active_chats
            }

        except Exception as e:
            return {'error': str(e)}

    def get_recent_activity(self, limit=20):
        """Activite recente toutes sources"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            activities = []

            # Dernieres transactions
            cursor.execute('''
                SELECT 'transaction' as type, description, total, type as subtype, created_at
                FROM accounting_transactions ORDER BY created_at DESC LIMIT 5
            ''')
            for r in cursor.fetchall():
                activities.append({
                    'type': 'finance',
                    'subtype': r[3],
                    'title': r[1],
                    'value': r[2],
                    'timestamp': r[4]
                })

            # Derniers contacts
            cursor.execute('''
                SELECT 'contact', first_name || ' ' || last_name, email, type, created_at
                FROM crm_contacts ORDER BY created_at DESC LIMIT 5
            ''')
            for r in cursor.fetchall():
                activities.append({
                    'type': 'crm',
                    'subtype': r[3],
                    'title': f"Nouveau contact: {r[1]}",
                    'value': r[2],
                    'timestamp': r[4]
                })

            # Dernieres reservations
            cursor.execute('''
                SELECT 'booking', client_name, confirmation_code, status, created_at
                FROM calendar_bookings ORDER BY created_at DESC LIMIT 5
            ''')
            for r in cursor.fetchall():
                activities.append({
                    'type': 'calendar',
                    'subtype': r[3],
                    'title': f"Reservation: {r[1]}",
                    'value': r[2],
                    'timestamp': r[4]
                })

            # Dernieres conversations chatbot
            cursor.execute('''
                SELECT 'chat', visitor_name, visitor_email, status, started_at
                FROM chatbot_conversations ORDER BY started_at DESC LIMIT 5
            ''')
            for r in cursor.fetchall():
                activities.append({
                    'type': 'chatbot',
                    'subtype': r[3],
                    'title': f"Conversation: {r[1] or 'Visiteur'}",
                    'value': r[2],
                    'timestamp': r[4]
                })

            conn.close()

            # Trier par date
            activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)

            return activities[:limit]

        except Exception as e:
            return {'error': str(e)}

    def get_alerts(self):
        """Alertes et notifications importantes"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            alerts = []

            # Factures en retard
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(total), 0) FROM invoices
                WHERE status = 'overdue'
            ''')
            overdue = cursor.fetchone()
            if overdue[0] > 0:
                alerts.append({
                    'type': 'warning',
                    'category': 'finance',
                    'title': f"{overdue[0]} facture(s) en retard",
                    'value': f"{overdue[1]}$",
                    'action': 'Voir factures'
                })

            # RDV non confirmes
            cursor.execute('''
                SELECT COUNT(*) FROM calendar_bookings
                WHERE status = 'pending' AND booking_date >= date('now')
            ''')
            pending = cursor.fetchone()[0]
            if pending > 0:
                alerts.append({
                    'type': 'info',
                    'category': 'calendar',
                    'title': f"{pending} reservation(s) a confirmer",
                    'action': 'Voir reservations'
                })

            # Leads chauds non contactes
            cursor.execute('''
                SELECT COUNT(*) FROM crm_contacts
                WHERE type = 'lead' AND score >= 70 AND last_contact_date IS NULL
            ''')
            hot_leads = cursor.fetchone()[0]
            if hot_leads > 0:
                alerts.append({
                    'type': 'success',
                    'category': 'crm',
                    'title': f"{hot_leads} lead(s) chaud(s) a contacter",
                    'action': 'Voir leads'
                })

            # Conversations chatbot actives
            cursor.execute('''
                SELECT COUNT(*) FROM chatbot_conversations
                WHERE status = 'active' AND last_message_at < datetime('now', '-5 minutes')
            ''')
            waiting = cursor.fetchone()[0]
            if waiting > 0:
                alerts.append({
                    'type': 'warning',
                    'category': 'chatbot',
                    'title': f"{waiting} conversation(s) en attente",
                    'action': 'Repondre'
                })

            conn.close()

            return alerts

        except Exception as e:
            return {'error': str(e)}

    def generate_insights(self):
        """Genere des insights avec AI"""
        try:
            overview = self.get_overview(30)

            prompt = f"""Analyse ces KPIs business et genere 3-5 insights actionables.

DONNEES (30 derniers jours):
- Revenus: {overview.get('finance', {}).get('revenue', 0)}$
- Profit: {overview.get('finance', {}).get('profit', 0)}$
- Marge: {overview.get('finance', {}).get('margin_percent', 0)}%
- Nouveaux contacts: {overview.get('crm', {}).get('new_contacts', 0)}
- Leads chauds: {overview.get('crm', {}).get('leads', {}).get('hot', 0)}
- Reservations: {overview.get('calendar', {}).get('bookings_total', 0)}
- Conversations chatbot: {overview.get('chatbot', {}).get('conversations', 0)}
- Taux conversion chatbot: {overview.get('chatbot', {}).get('conversion_rate', 0)}%
- Score sante: {overview.get('health_score', 50)}/100

FORMAT JSON:
{{
    "insights": [
        {{"type": "positive|warning|opportunity", "title": "...", "description": "...", "action": "..."}},
    ],
    "priority_action": "action prioritaire a faire maintenant"
}}
"""
            # Fireworks pour analyse complexe
            response = call_qwen(prompt, 1000, "Tu es un analyste business. Reponds en JSON valide.")

            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())

            return {'insights': [], 'priority_action': 'Verifier les donnees'}

        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 54: EMAIL CAMPAIGN AGENT - Marketing Email
# ============================================

class EmailCampaignAgent:
    """Agent de campagnes email marketing - Sequences, A/B testing, Tracking"""
    name = "Email Campaign Agent"

    def init_db(self):
        """Initialise les tables"""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT DEFAULT 'newsletter',
            status TEXT DEFAULT 'draft', subject TEXT, subject_b TEXT, content_html TEXT,
            segment_id INTEGER, sent_count INTEGER DEFAULT 0, open_count INTEGER DEFAULT 0,
            click_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, trigger_type TEXT DEFAULT 'signup',
            is_active INTEGER DEFAULT 1, total_emails INTEGER DEFAULT 0, total_enrolled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_sequence_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sequence_id INTEGER, step_order INTEGER DEFAULT 1,
            delay_days INTEGER DEFAULT 1, subject TEXT, content_html TEXT, sent_count INTEGER DEFAULT 0)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_sequence_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sequence_id INTEGER, contact_id INTEGER,
            current_step INTEGER DEFAULT 1, status TEXT DEFAULT 'active',
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, next_email_at TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, conditions TEXT,
            contact_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_sends (
            id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER, sequence_step_id INTEGER,
            contact_id INTEGER, email TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            opened_at TIMESTAMP, clicked_at TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS email_unsubscribes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, reason TEXT,
            unsubscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        conn.commit()
        conn.close()
        return {'success': True}

    def create_campaign(self, data):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO email_campaigns (name, type, subject, subject_b, content_html, segment_id) VALUES (?, ?, ?, ?, ?, ?)',
                (data.get('name', 'Campagne'), data.get('type', 'newsletter'), data.get('subject', ''),
                 data.get('subject_b'), data.get('content_html', ''), data.get('segment_id')))
            campaign_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'campaign_id': campaign_id}
        except Exception as e:
            return {'error': str(e)}

    def generate_email_ai(self, campaign_type, context):
        try:
            prompt = f"Genere email marketing type {campaign_type}. Contexte: {context}. JSON: {{subject, content_html}}"
            response = call_ollama(prompt, 800) or call_qwen(prompt, 800)
            if response:
                if '```json' in response: response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            return {'error': 'Pas de reponse'}
        except Exception as e:
            return {'error': str(e)}

    def create_sequence(self, name, trigger_type='signup'):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO email_sequences (name, trigger_type) VALUES (?, ?)', (name, trigger_type))
            seq_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'sequence_id': seq_id}
        except Exception as e:
            return {'error': str(e)}

    def add_sequence_step(self, sequence_id, subject, content_html, delay_days=1):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(step_order) FROM email_sequence_steps WHERE sequence_id = ?', (sequence_id,))
            max_order = cursor.fetchone()[0] or 0
            cursor.execute('INSERT INTO email_sequence_steps (sequence_id, step_order, delay_days, subject, content_html) VALUES (?, ?, ?, ?, ?)',
                (sequence_id, max_order + 1, delay_days, subject, content_html))
            step_id = cursor.lastrowid
            cursor.execute('UPDATE email_sequences SET total_emails = total_emails + 1 WHERE id = ?', (sequence_id,))
            conn.commit()
            conn.close()
            return {'success': True, 'step_id': step_id}
        except Exception as e:
            return {'error': str(e)}

    def enroll_contact(self, sequence_id, contact_id):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            next_email = datetime.now() + timedelta(days=1)
            cursor.execute('INSERT INTO email_sequence_enrollments (sequence_id, contact_id, next_email_at) VALUES (?, ?, ?)',
                (sequence_id, contact_id, next_email.strftime('%Y-%m-%d %H:%M:%S')))
            cursor.execute('UPDATE email_sequences SET total_enrolled = total_enrolled + 1 WHERE id = ?', (sequence_id,))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def create_segment(self, name, conditions):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO email_segments (name, conditions) VALUES (?, ?)',
                (name, json.dumps(conditions) if isinstance(conditions, dict) else conditions))
            seg_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'segment_id': seg_id}
        except Exception as e:
            return {'error': str(e)}

    def unsubscribe(self, email, reason=None):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO email_unsubscribes (email, reason) VALUES (?, ?)', (email, reason))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_campaigns(self, limit=50):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, type, status, subject, sent_count, open_count, click_count FROM email_campaigns LIMIT ?', (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'name': r[1], 'type': r[2], 'status': r[3], 'subject': r[4],
                    'sent': r[5], 'opens': r[6], 'clicks': r[7]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_sequences(self, limit=50):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, trigger_type, is_active, total_emails, total_enrolled FROM email_sequences LIMIT ?', (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'name': r[1], 'trigger': r[2], 'active': bool(r[3]), 'emails': r[4], 'enrolled': r[5]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, days=30):
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM email_sends WHERE sent_at >= ?', (start,))
            sent = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM email_sends WHERE opened_at IS NOT NULL AND sent_at >= ?', (start,))
            opens = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM email_unsubscribes WHERE unsubscribed_at >= ?', (start,))
            unsubs = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM email_sequences WHERE is_active = 1')
            seqs = cursor.fetchone()[0]
            conn.close()
            return {'sent': sent, 'opens': opens, 'open_rate': round(opens/sent*100,1) if sent else 0, 'unsubscribes': unsubs, 'active_sequences': seqs}
        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 55: SUPPORT TICKET AGENT - Gestion Tickets
# ============================================

class SupportTicketAgent:
    """Agent de gestion des tickets support - Helpdesk, SLA, Escalade"""
    name = "Support Ticket Agent"

    def init_db(self):
        conn = get_db()
        cursor = conn.cursor()

        # Tickets
        cursor.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE,
            contact_id INTEGER,
            email TEXT,
            name TEXT,
            subject TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            assigned_to TEXT,
            channel TEXT DEFAULT 'email',
            sla_due_at TIMESTAMP,
            first_response_at TIMESTAMP,
            resolved_at TIMESTAMP,
            satisfaction_score INTEGER,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Messages/Reponses
        cursor.execute('''CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            sender_type TEXT DEFAULT 'customer',
            sender_name TEXT,
            message TEXT,
            is_internal BOOLEAN DEFAULT 0,
            attachments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id))''')

        # Categories
        cursor.execute('''CREATE TABLE IF NOT EXISTS ticket_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            sla_hours INTEGER DEFAULT 24,
            auto_assign TEXT,
            template_response TEXT,
            is_active BOOLEAN DEFAULT 1)''')

        # Reponses predefinies
        cursor.execute('''CREATE TABLE IF NOT EXISTS canned_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            subject TEXT,
            content TEXT,
            shortcut TEXT,
            use_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # SLA Rules
        cursor.execute('''CREATE TABLE IF NOT EXISTS sla_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            priority TEXT,
            category TEXT,
            first_response_hours INTEGER DEFAULT 4,
            resolution_hours INTEGER DEFAULT 24,
            escalation_hours INTEGER DEFAULT 12,
            is_active BOOLEAN DEFAULT 1)''')

        # Insert default categories
        categories = [
            ('technical', 'Problemes techniques', 8, None),
            ('billing', 'Facturation et paiements', 24, None),
            ('general', 'Questions generales', 48, None),
            ('urgent', 'Urgences', 2, None),
            ('feature', 'Demandes de fonctionnalites', 72, None)
        ]
        for cat in categories:
            cursor.execute('INSERT OR IGNORE INTO ticket_categories (name, description, sla_hours, auto_assign) VALUES (?, ?, ?, ?)', cat)

        # Insert default SLA rules
        sla_rules = [
            ('Urgent SLA', 'urgent', None, 1, 4, 2),
            ('High Priority SLA', 'high', None, 2, 8, 4),
            ('Normal SLA', 'medium', None, 4, 24, 12),
            ('Low Priority SLA', 'low', None, 8, 48, 24)
        ]
        for sla in sla_rules:
            cursor.execute('INSERT OR IGNORE INTO sla_rules (name, priority, category, first_response_hours, resolution_hours, escalation_hours) VALUES (?, ?, ?, ?, ?, ?)', sla)

        conn.commit()
        conn.close()
        return {'success': True}

    def _generate_ticket_number(self):
        import random
        return f"TKT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

    def create_ticket(self, data):
        """Cree un nouveau ticket"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            ticket_number = self._generate_ticket_number()
            priority = data.get('priority', 'medium')
            category = data.get('category', 'general')

            # Calcul SLA
            cursor.execute('SELECT sla_hours FROM ticket_categories WHERE name = ?', (category,))
            row = cursor.fetchone()
            sla_hours = row[0] if row else 24
            sla_due = datetime.now() + timedelta(hours=sla_hours)

            cursor.execute('''INSERT INTO support_tickets
                (ticket_number, contact_id, email, name, subject, description, category, priority, channel, sla_due_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (ticket_number, data.get('contact_id'), data.get('email'), data.get('name'),
                 data.get('subject', 'Sans sujet'), data.get('description', ''),
                 category, priority, data.get('channel', 'email'),
                 sla_due.strftime('%Y-%m-%d %H:%M:%S'),
                 json.dumps(data.get('tags', [])) if data.get('tags') else None))

            ticket_id = cursor.lastrowid

            # Message initial
            if data.get('description'):
                cursor.execute('INSERT INTO ticket_messages (ticket_id, sender_type, sender_name, message) VALUES (?, ?, ?, ?)',
                    (ticket_id, 'customer', data.get('name', 'Client'), data.get('description')))

            conn.commit()
            conn.close()
            return {'success': True, 'ticket_id': ticket_id, 'ticket_number': ticket_number, 'sla_due': sla_due.isoformat()}
        except Exception as e:
            return {'error': str(e)}

    def reply_ticket(self, ticket_id, message, sender_type='agent', sender_name='Support', is_internal=False):
        """Repond a un ticket"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('INSERT INTO ticket_messages (ticket_id, sender_type, sender_name, message, is_internal) VALUES (?, ?, ?, ?, ?)',
                (ticket_id, sender_type, sender_name, message, is_internal))

            # Marquer premiere reponse
            if sender_type == 'agent' and not is_internal:
                cursor.execute('UPDATE support_tickets SET first_response_at = COALESCE(first_response_at, CURRENT_TIMESTAMP), status = "in_progress", updated_at = CURRENT_TIMESTAMP WHERE id = ?', (ticket_id,))

            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def generate_response_ai(self, ticket_id):
        """Genere reponse IA pour un ticket"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT subject, description, category FROM support_tickets WHERE id = ?', (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                return {'error': 'Ticket non trouve'}

            cursor.execute('SELECT message, sender_type FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at', (ticket_id,))
            messages = cursor.fetchall()
            conn.close()

            conversation = "\n".join([f"{'Client' if m[1]=='customer' else 'Agent'}: {m[0]}" for m in messages])

            prompt = f"""Tu es un agent support client professionnel pour SEO par AI.
Ticket: {ticket[0]}
Description: {ticket[1]}
Categorie: {ticket[2]}

Historique:
{conversation}

Genere une reponse professionnelle, empathique et utile. Sois concis mais complet.
Propose des solutions concretes si possible."""

            response = call_ollama(prompt, 500) or call_qwen(prompt, 500)
            return {'response': response} if response else {'error': 'Pas de reponse IA'}
        except Exception as e:
            return {'error': str(e)}

    def update_ticket(self, ticket_id, updates):
        """Met a jour un ticket"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            allowed = ['status', 'priority', 'category', 'assigned_to', 'tags']
            set_parts = []
            values = []

            for key in allowed:
                if key in updates:
                    set_parts.append(f"{key} = ?")
                    val = updates[key]
                    if key == 'tags' and isinstance(val, list):
                        val = json.dumps(val)
                    values.append(val)

            if updates.get('status') == 'resolved':
                set_parts.append("resolved_at = CURRENT_TIMESTAMP")

            if set_parts:
                set_parts.append("updated_at = CURRENT_TIMESTAMP")
                values.append(ticket_id)
                cursor.execute(f"UPDATE support_tickets SET {', '.join(set_parts)} WHERE id = ?", values)
                conn.commit()

            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_ticket(self, ticket_id):
        """Recupere un ticket avec messages"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''SELECT id, ticket_number, email, name, subject, description, category, priority,
                status, assigned_to, channel, sla_due_at, first_response_at, resolved_at, satisfaction_score, created_at
                FROM support_tickets WHERE id = ?''', (ticket_id,))
            t = cursor.fetchone()
            if not t:
                return {'error': 'Ticket non trouve'}

            cursor.execute('SELECT id, sender_type, sender_name, message, is_internal, created_at FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at', (ticket_id,))
            messages = [{'id': m[0], 'sender_type': m[1], 'sender_name': m[2], 'message': m[3], 'internal': bool(m[4]), 'created_at': m[5]} for m in cursor.fetchall()]

            conn.close()
            return {
                'id': t[0], 'ticket_number': t[1], 'email': t[2], 'name': t[3], 'subject': t[4],
                'description': t[5], 'category': t[6], 'priority': t[7], 'status': t[8],
                'assigned_to': t[9], 'channel': t[10], 'sla_due_at': t[11], 'first_response_at': t[12],
                'resolved_at': t[13], 'satisfaction_score': t[14], 'created_at': t[15], 'messages': messages
            }
        except Exception as e:
            return {'error': str(e)}

    def get_tickets(self, filters=None, limit=50):
        """Liste les tickets"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''SELECT id, ticket_number, email, name, subject, category, priority, status, assigned_to, sla_due_at, created_at
                FROM support_tickets WHERE 1=1'''
            params = []

            if filters:
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('priority'):
                    query += ' AND priority = ?'
                    params.append(filters['priority'])
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('assigned_to'):
                    query += ' AND assigned_to = ?'
                    params.append(filters['assigned_to'])

            query += ' ORDER BY CASE priority WHEN "urgent" THEN 1 WHEN "high" THEN 2 WHEN "medium" THEN 3 ELSE 4 END, created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'ticket_number': r[1], 'email': r[2], 'name': r[3], 'subject': r[4],
                    'category': r[5], 'priority': r[6], 'status': r[7], 'assigned_to': r[8],
                    'sla_due': r[9], 'created_at': r[10]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_overdue_tickets(self):
        """Tickets en retard SLA"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''SELECT id, ticket_number, subject, priority, status, sla_due_at
                FROM support_tickets WHERE status NOT IN ('resolved', 'closed') AND sla_due_at < CURRENT_TIMESTAMP
                ORDER BY sla_due_at''')
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'ticket_number': r[1], 'subject': r[2], 'priority': r[3], 'status': r[4], 'sla_due': r[5]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def add_canned_response(self, name, content, category=None, shortcut=None):
        """Ajoute reponse predefinie"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO canned_responses (name, category, content, shortcut) VALUES (?, ?, ?, ?)',
                (name, category, content, shortcut))
            resp_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'response_id': resp_id}
        except Exception as e:
            return {'error': str(e)}

    def get_canned_responses(self, category=None):
        """Liste reponses predefinies"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            if category:
                cursor.execute('SELECT id, name, category, content, shortcut FROM canned_responses WHERE category = ?', (category,))
            else:
                cursor.execute('SELECT id, name, category, content, shortcut FROM canned_responses')
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'name': r[1], 'category': r[2], 'content': r[3], 'shortcut': r[4]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def rate_ticket(self, ticket_id, score, feedback=None):
        """Note satisfaction client"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE support_tickets SET satisfaction_score = ? WHERE id = ?', (score, ticket_id))
            if feedback:
                cursor.execute('INSERT INTO ticket_messages (ticket_id, sender_type, sender_name, message, is_internal) VALUES (?, ?, ?, ?, ?)',
                    (ticket_id, 'customer', 'Feedback', f"Score: {score}/5 - {feedback}", True))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, days=30):
        """Statistiques support"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT COUNT(*) FROM support_tickets WHERE created_at >= ?', (start,))
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM support_tickets WHERE status = "open"')
            open_tickets = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM support_tickets WHERE status = "resolved" AND created_at >= ?', (start,))
            resolved = cursor.fetchone()[0]

            cursor.execute('SELECT AVG(satisfaction_score) FROM support_tickets WHERE satisfaction_score IS NOT NULL AND created_at >= ?', (start,))
            avg_sat = cursor.fetchone()[0] or 0

            cursor.execute('''SELECT AVG((julianday(first_response_at) - julianday(created_at)) * 24)
                FROM support_tickets WHERE first_response_at IS NOT NULL AND created_at >= ?''', (start,))
            avg_response = cursor.fetchone()[0] or 0

            cursor.execute('SELECT COUNT(*) FROM support_tickets WHERE sla_due_at < CURRENT_TIMESTAMP AND status NOT IN ("resolved", "closed")')
            overdue = cursor.fetchone()[0]

            cursor.execute('SELECT category, COUNT(*) FROM support_tickets WHERE created_at >= ? GROUP BY category', (start,))
            by_category = {r[0]: r[1] for r in cursor.fetchall()}

            conn.close()
            return {
                'total_tickets': total, 'open_tickets': open_tickets, 'resolved': resolved,
                'resolution_rate': round(resolved/total*100, 1) if total else 0,
                'avg_satisfaction': round(avg_sat, 1), 'avg_response_hours': round(avg_response, 1),
                'overdue_tickets': overdue, 'by_category': by_category
            }
        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 56: KNOWLEDGE BASE AGENT - FAQ & Documentation
# ============================================

class KnowledgeBaseAgent:
    """Agent de base de connaissances - Articles, FAQ, Recherche semantique"""
    name = "Knowledge Base Agent"

    def init_db(self):
        conn = get_db()
        cursor = conn.cursor()

        # Articles
        cursor.execute('''CREATE TABLE IF NOT EXISTS kb_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            content TEXT,
            excerpt TEXT,
            category_id INTEGER,
            author TEXT,
            status TEXT DEFAULT 'draft',
            is_featured BOOLEAN DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            helpful_yes INTEGER DEFAULT 0,
            helpful_no INTEGER DEFAULT 0,
            tags TEXT,
            meta_title TEXT,
            meta_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP)''')

        # Categories
        cursor.execute('''CREATE TABLE IF NOT EXISTS kb_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            parent_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            article_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1)''')

        # FAQ
        cursor.execute('''CREATE TABLE IF NOT EXISTS kb_faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT,
            category_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Recherches
        cursor.execute('''CREATE TABLE IF NOT EXISTS kb_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            results_count INTEGER DEFAULT 0,
            clicked_article_id INTEGER,
            user_ip TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Feedback articles
        cursor.execute('''CREATE TABLE IF NOT EXISTS kb_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            is_helpful BOOLEAN,
            comment TEXT,
            user_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES kb_articles(id))''')

        # Insert default categories
        categories = [
            ('getting-started', 'Premiers pas', 'Guide de demarrage', '🚀', 1),
            ('features', 'Fonctionnalites', 'Toutes les fonctionnalites', '⚡', 2),
            ('billing', 'Facturation', 'Questions de facturation', '💳', 3),
            ('troubleshooting', 'Depannage', 'Resolution de problemes', '🔧', 4),
            ('api', 'API & Integration', 'Documentation technique', '🔌', 5)
        ]
        for cat in categories:
            cursor.execute('INSERT OR IGNORE INTO kb_categories (slug, name, description, icon, sort_order) VALUES (?, ?, ?, ?, ?)', cat)

        conn.commit()
        conn.close()
        return {'success': True}

    def _generate_slug(self, title):
        import re
        slug = title.lower()
        slug = re.sub(r'[àáâãäå]', 'a', slug)
        slug = re.sub(r'[èéêë]', 'e', slug)
        slug = re.sub(r'[ìíîï]', 'i', slug)
        slug = re.sub(r'[òóôõö]', 'o', slug)
        slug = re.sub(r'[ùúûü]', 'u', slug)
        slug = re.sub(r'[ç]', 'c', slug)
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]

    def create_article(self, data):
        """Cree un article"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            title = data.get('title', 'Sans titre')
            slug = data.get('slug') or self._generate_slug(title)
            content = data.get('content', '')
            excerpt = data.get('excerpt') or content[:200] + '...' if len(content) > 200 else content

            cursor.execute('''INSERT INTO kb_articles
                (slug, title, content, excerpt, category_id, author, status, tags, meta_title, meta_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (slug, title, content, excerpt, data.get('category_id'),
                 data.get('author', 'Admin'), data.get('status', 'draft'),
                 json.dumps(data.get('tags', [])) if data.get('tags') else None,
                 data.get('meta_title') or title, data.get('meta_description') or excerpt))

            article_id = cursor.lastrowid

            if data.get('category_id'):
                cursor.execute('UPDATE kb_categories SET article_count = article_count + 1 WHERE id = ?', (data['category_id'],))

            conn.commit()
            conn.close()
            return {'success': True, 'article_id': article_id, 'slug': slug}
        except Exception as e:
            return {'error': str(e)}

    def generate_article_ai(self, topic, category=None):
        """Genere un article avec IA"""
        try:
            prompt = f"""Ecris un article d'aide complet pour une base de connaissances.
Sujet: {topic}
Categorie: {category or 'general'}

L'article doit etre:
- Clair et bien structure
- Avec des titres et sous-titres
- Des etapes numerotees si necessaire
- Des conseils pratiques

Retourne en JSON: {{"title": "...", "content": "...(markdown)...", "excerpt": "...", "tags": ["...", "..."]}}"""

            response = call_ollama(prompt, 1500) or call_qwen(prompt, 1500)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            return {'error': 'Pas de reponse IA'}
        except Exception as e:
            return {'error': str(e)}

    def update_article(self, article_id, updates):
        """Met a jour un article"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            allowed = ['title', 'content', 'excerpt', 'category_id', 'status', 'is_featured', 'tags', 'meta_title', 'meta_description']
            set_parts = []
            values = []

            for key in allowed:
                if key in updates:
                    set_parts.append(f"{key} = ?")
                    val = updates[key]
                    if key == 'tags' and isinstance(val, list):
                        val = json.dumps(val)
                    values.append(val)

            if updates.get('status') == 'published':
                set_parts.append("published_at = COALESCE(published_at, CURRENT_TIMESTAMP)")

            if set_parts:
                set_parts.append("updated_at = CURRENT_TIMESTAMP")
                values.append(article_id)
                cursor.execute(f"UPDATE kb_articles SET {', '.join(set_parts)} WHERE id = ?", values)
                conn.commit()

            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_article(self, article_id=None, slug=None, increment_view=True):
        """Recupere un article"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if article_id:
                cursor.execute('''SELECT a.id, a.slug, a.title, a.content, a.excerpt, a.category_id, c.name as category_name,
                    a.author, a.status, a.is_featured, a.view_count, a.helpful_yes, a.helpful_no, a.tags, a.created_at, a.published_at
                    FROM kb_articles a LEFT JOIN kb_categories c ON a.category_id = c.id WHERE a.id = ?''', (article_id,))
            else:
                cursor.execute('''SELECT a.id, a.slug, a.title, a.content, a.excerpt, a.category_id, c.name as category_name,
                    a.author, a.status, a.is_featured, a.view_count, a.helpful_yes, a.helpful_no, a.tags, a.created_at, a.published_at
                    FROM kb_articles a LEFT JOIN kb_categories c ON a.category_id = c.id WHERE a.slug = ?''', (slug,))

            row = cursor.fetchone()
            if not row:
                return {'error': 'Article non trouve'}

            if increment_view:
                cursor.execute('UPDATE kb_articles SET view_count = view_count + 1 WHERE id = ?', (row[0],))
                conn.commit()

            conn.close()
            return {
                'id': row[0], 'slug': row[1], 'title': row[2], 'content': row[3], 'excerpt': row[4],
                'category_id': row[5], 'category_name': row[6], 'author': row[7], 'status': row[8],
                'is_featured': bool(row[9]), 'view_count': row[10], 'helpful_yes': row[11], 'helpful_no': row[12],
                'tags': json.loads(row[13]) if row[13] else [], 'created_at': row[14], 'published_at': row[15]
            }
        except Exception as e:
            return {'error': str(e)}

    def get_articles(self, category_id=None, status='published', limit=50):
        """Liste les articles"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''SELECT a.id, a.slug, a.title, a.excerpt, c.name as category, a.view_count, a.published_at
                FROM kb_articles a LEFT JOIN kb_categories c ON a.category_id = c.id WHERE 1=1'''
            params = []

            if status:
                query += ' AND a.status = ?'
                params.append(status)
            if category_id:
                query += ' AND a.category_id = ?'
                params.append(category_id)

            query += ' ORDER BY a.is_featured DESC, a.published_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'slug': r[1], 'title': r[2], 'excerpt': r[3], 'category': r[4], 'views': r[5], 'published_at': r[6]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def search_articles(self, query, limit=20):
        """Recherche articles"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            search_term = f'%{query}%'
            cursor.execute('''SELECT id, slug, title, excerpt, view_count FROM kb_articles
                WHERE status = 'published' AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
                ORDER BY view_count DESC LIMIT ?''', (search_term, search_term, search_term, limit))
            rows = cursor.fetchall()

            # Log search
            cursor.execute('INSERT INTO kb_searches (query, results_count) VALUES (?, ?)', (query, len(rows)))
            conn.commit()
            conn.close()

            return [{'id': r[0], 'slug': r[1], 'title': r[2], 'excerpt': r[3], 'views': r[4]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def answer_question_ai(self, question):
        """Repond a une question avec IA en se basant sur la KB"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Chercher articles pertinents
            search_term = f'%{question}%'
            cursor.execute('''SELECT title, content FROM kb_articles
                WHERE status = 'published' AND (title LIKE ? OR content LIKE ?)
                LIMIT 3''', (search_term, search_term))
            articles = cursor.fetchall()
            conn.close()

            context = "\n\n".join([f"Article: {a[0]}\n{a[1][:500]}" for a in articles]) if articles else "Aucun article trouve"

            prompt = f"""Tu es un assistant support pour SEO par AI.
Base de connaissances disponible:
{context}

Question du client: {question}

Reponds de maniere claire et utile. Si tu ne trouves pas l'info, suggere de contacter le support."""

            response = call_ollama(prompt, 500) or call_qwen(prompt, 500)
            return {'answer': response, 'sources': [a[0] for a in articles]} if response else {'error': 'Pas de reponse'}
        except Exception as e:
            return {'error': str(e)}

    def add_faq(self, question, answer, category_id=None):
        """Ajoute une FAQ"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(sort_order) FROM kb_faq WHERE category_id = ?', (category_id,))
            max_order = cursor.fetchone()[0] or 0
            cursor.execute('INSERT INTO kb_faq (question, answer, category_id, sort_order) VALUES (?, ?, ?, ?)',
                (question, answer, category_id, max_order + 1))
            faq_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'faq_id': faq_id}
        except Exception as e:
            return {'error': str(e)}

    def get_faqs(self, category_id=None, limit=50):
        """Liste les FAQ"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if category_id:
                cursor.execute('''SELECT f.id, f.question, f.answer, c.name as category, f.view_count
                    FROM kb_faq f LEFT JOIN kb_categories c ON f.category_id = c.id
                    WHERE f.is_active = 1 AND f.category_id = ? ORDER BY f.sort_order LIMIT ?''', (category_id, limit))
            else:
                cursor.execute('''SELECT f.id, f.question, f.answer, c.name as category, f.view_count
                    FROM kb_faq f LEFT JOIN kb_categories c ON f.category_id = c.id
                    WHERE f.is_active = 1 ORDER BY f.sort_order LIMIT ?''', (limit,))

            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'question': r[1], 'answer': r[2], 'category': r[3], 'views': r[4]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def rate_article(self, article_id, is_helpful, comment=None, email=None):
        """Note un article"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if is_helpful:
                cursor.execute('UPDATE kb_articles SET helpful_yes = helpful_yes + 1 WHERE id = ?', (article_id,))
            else:
                cursor.execute('UPDATE kb_articles SET helpful_no = helpful_no + 1 WHERE id = ?', (article_id,))

            cursor.execute('INSERT INTO kb_feedback (article_id, is_helpful, comment, user_email) VALUES (?, ?, ?, ?)',
                (article_id, is_helpful, comment, email))

            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_categories(self):
        """Liste les categories"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, slug, name, description, icon, article_count FROM kb_categories WHERE is_active = 1 ORDER BY sort_order')
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'slug': r[1], 'name': r[2], 'description': r[3], 'icon': r[4], 'article_count': r[5]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_popular_articles(self, limit=10):
        """Articles populaires"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''SELECT id, slug, title, excerpt, view_count FROM kb_articles
                WHERE status = 'published' ORDER BY view_count DESC LIMIT ?''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'slug': r[1], 'title': r[2], 'excerpt': r[3], 'views': r[4]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_stats(self):
        """Statistiques KB"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM kb_articles WHERE status = "published"')
            published = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM kb_articles WHERE status = "draft"')
            drafts = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(view_count) FROM kb_articles')
            total_views = cursor.fetchone()[0] or 0

            cursor.execute('SELECT COUNT(*) FROM kb_faq WHERE is_active = 1')
            faqs = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM kb_searches')
            searches = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(helpful_yes), SUM(helpful_no) FROM kb_articles')
            helpful = cursor.fetchone()
            helpful_yes = helpful[0] or 0
            helpful_no = helpful[1] or 0

            cursor.execute('SELECT query, COUNT(*) as cnt FROM kb_searches GROUP BY query ORDER BY cnt DESC LIMIT 10')
            top_searches = [{'query': r[0], 'count': r[1]} for r in cursor.fetchall()]

            conn.close()
            return {
                'published_articles': published, 'draft_articles': drafts, 'total_views': total_views,
                'total_faqs': faqs, 'total_searches': searches,
                'helpful_rate': round(helpful_yes/(helpful_yes+helpful_no)*100, 1) if (helpful_yes+helpful_no) > 0 else 0,
                'top_searches': top_searches
            }
        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 57: SURVEY AGENT - Sondages & Feedback
# ============================================

class SurveyAgent:
    """Agent de sondages et feedback - NPS, CSAT, Formulaires personnalises"""
    name = "Survey Agent"

    def init_db(self):
        conn = get_db()
        cursor = conn.cursor()

        # Sondages
        cursor.execute('''CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT DEFAULT 'custom',
            status TEXT DEFAULT 'draft',
            is_anonymous BOOLEAN DEFAULT 0,
            thank_you_message TEXT,
            redirect_url TEXT,
            starts_at TIMESTAMP,
            ends_at TIMESTAMP,
            response_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Questions
        cursor.execute('''CREATE TABLE IF NOT EXISTS survey_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER,
            question_type TEXT DEFAULT 'text',
            question_text TEXT NOT NULL,
            description TEXT,
            options TEXT,
            is_required BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            settings TEXT,
            FOREIGN KEY (survey_id) REFERENCES surveys(id))''')

        # Reponses
        cursor.execute('''CREATE TABLE IF NOT EXISTS survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER,
            contact_id INTEGER,
            email TEXT,
            ip_address TEXT,
            user_agent TEXT,
            is_complete BOOLEAN DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (survey_id) REFERENCES surveys(id))''')

        # Reponses aux questions
        cursor.execute('''CREATE TABLE IF NOT EXISTS survey_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER,
            question_id INTEGER,
            answer_text TEXT,
            answer_value INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (response_id) REFERENCES survey_responses(id),
            FOREIGN KEY (question_id) REFERENCES survey_questions(id))''')

        # NPS Scores
        cursor.execute('''CREATE TABLE IF NOT EXISTS nps_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            email TEXT,
            score INTEGER,
            feedback TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        conn.commit()
        conn.close()
        return {'success': True}

    def create_survey(self, data):
        """Cree un sondage"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO surveys (name, description, type, status, is_anonymous, thank_you_message, redirect_url, starts_at, ends_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data.get('name', 'Nouveau sondage'), data.get('description'), data.get('type', 'custom'),
                 data.get('status', 'draft'), data.get('is_anonymous', False),
                 data.get('thank_you_message', 'Merci pour votre reponse!'),
                 data.get('redirect_url'), data.get('starts_at'), data.get('ends_at')))

            survey_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'survey_id': survey_id}
        except Exception as e:
            return {'error': str(e)}

    def add_question(self, survey_id, data):
        """Ajoute une question au sondage"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT MAX(sort_order) FROM survey_questions WHERE survey_id = ?', (survey_id,))
            max_order = cursor.fetchone()[0] or 0

            options = data.get('options')
            if isinstance(options, list):
                options = json.dumps(options)

            settings = data.get('settings')
            if isinstance(settings, dict):
                settings = json.dumps(settings)

            cursor.execute('''INSERT INTO survey_questions (survey_id, question_type, question_text, description, options, is_required, sort_order, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (survey_id, data.get('question_type', 'text'), data.get('question_text', ''),
                 data.get('description'), options, data.get('is_required', True), max_order + 1, settings))

            question_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'question_id': question_id}
        except Exception as e:
            return {'error': str(e)}

    def create_nps_survey(self, name="Enquete NPS"):
        """Cree un sondage NPS predifini"""
        try:
            result = self.create_survey({'name': name, 'type': 'nps', 'status': 'active'})
            if 'error' in result:
                return result

            survey_id = result['survey_id']

            # Question NPS standard
            self.add_question(survey_id, {
                'question_type': 'nps',
                'question_text': 'Sur une echelle de 0 a 10, quelle est la probabilite que vous recommandiez SEO par AI a un ami ou collegue?',
                'settings': {'min': 0, 'max': 10}
            })

            # Question feedback
            self.add_question(survey_id, {
                'question_type': 'textarea',
                'question_text': 'Pouvez-vous nous expliquer votre note?',
                'is_required': False
            })

            return {'success': True, 'survey_id': survey_id, 'type': 'nps'}
        except Exception as e:
            return {'error': str(e)}

    def create_csat_survey(self, name="Satisfaction Client"):
        """Cree un sondage CSAT predifini"""
        try:
            result = self.create_survey({'name': name, 'type': 'csat', 'status': 'active'})
            if 'error' in result:
                return result

            survey_id = result['survey_id']

            self.add_question(survey_id, {
                'question_type': 'rating',
                'question_text': 'Comment evaluez-vous votre experience globale avec SEO par AI?',
                'options': ['Tres insatisfait', 'Insatisfait', 'Neutre', 'Satisfait', 'Tres satisfait'],
                'settings': {'min': 1, 'max': 5}
            })

            self.add_question(survey_id, {
                'question_type': 'multiple_choice',
                'question_text': 'Quels aspects appreciez-vous le plus?',
                'options': ['Facilite utilisation', 'Support client', 'Resultats SEO', 'Rapport qualite-prix', 'Agents IA']
            })

            self.add_question(survey_id, {
                'question_type': 'textarea',
                'question_text': 'Avez-vous des suggestions pour nous ameliorer?',
                'is_required': False
            })

            return {'success': True, 'survey_id': survey_id, 'type': 'csat'}
        except Exception as e:
            return {'error': str(e)}

    def submit_response(self, survey_id, answers, contact_info=None):
        """Soumet une reponse au sondage"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Creer la reponse
            email = contact_info.get('email') if contact_info else None
            contact_id = contact_info.get('contact_id') if contact_info else None

            cursor.execute('''INSERT INTO survey_responses (survey_id, contact_id, email, is_complete, completed_at)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)''', (survey_id, contact_id, email))
            response_id = cursor.lastrowid

            # Enregistrer les reponses
            for question_id, answer in answers.items():
                answer_text = answer if isinstance(answer, str) else json.dumps(answer)
                answer_value = answer if isinstance(answer, int) else None
                cursor.execute('INSERT INTO survey_answers (response_id, question_id, answer_text, answer_value) VALUES (?, ?, ?, ?)',
                    (response_id, int(question_id), answer_text, answer_value))

            # Mettre a jour le compteur
            cursor.execute('UPDATE surveys SET response_count = response_count + 1 WHERE id = ?', (survey_id,))

            conn.commit()
            conn.close()
            return {'success': True, 'response_id': response_id}
        except Exception as e:
            return {'error': str(e)}

    def record_nps(self, score, email=None, contact_id=None, feedback=None, source='survey'):
        """Enregistre un score NPS"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO nps_scores (contact_id, email, score, feedback, source) VALUES (?, ?, ?, ?, ?)',
                (contact_id, email, score, feedback, source))
            conn.commit()
            conn.close()
            return {'success': True, 'category': 'promoter' if score >= 9 else 'passive' if score >= 7 else 'detractor'}
        except Exception as e:
            return {'error': str(e)}

    def get_survey(self, survey_id):
        """Recupere un sondage avec questions"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT id, name, description, type, status, is_anonymous, thank_you_message, response_count FROM surveys WHERE id = ?', (survey_id,))
            s = cursor.fetchone()
            if not s:
                return {'error': 'Sondage non trouve'}

            cursor.execute('SELECT id, question_type, question_text, description, options, is_required, sort_order FROM survey_questions WHERE survey_id = ? ORDER BY sort_order', (survey_id,))
            questions = []
            for q in cursor.fetchall():
                questions.append({
                    'id': q[0], 'type': q[1], 'text': q[2], 'description': q[3],
                    'options': json.loads(q[4]) if q[4] else None, 'required': bool(q[5]), 'order': q[6]
                })

            conn.close()
            return {
                'id': s[0], 'name': s[1], 'description': s[2], 'type': s[3], 'status': s[4],
                'is_anonymous': bool(s[5]), 'thank_you_message': s[6], 'response_count': s[7], 'questions': questions
            }
        except Exception as e:
            return {'error': str(e)}

    def get_surveys(self, status=None, limit=50):
        """Liste les sondages"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if status:
                cursor.execute('SELECT id, name, type, status, response_count, created_at FROM surveys WHERE status = ? ORDER BY created_at DESC LIMIT ?', (status, limit))
            else:
                cursor.execute('SELECT id, name, type, status, response_count, created_at FROM surveys ORDER BY created_at DESC LIMIT ?', (limit,))

            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'name': r[1], 'type': r[2], 'status': r[3], 'responses': r[4], 'created_at': r[5]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_responses(self, survey_id, limit=100):
        """Liste les reponses d'un sondage"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''SELECT r.id, r.email, r.completed_at,
                (SELECT GROUP_CONCAT(q.question_text || ': ' || a.answer_text, ' | ')
                 FROM survey_answers a JOIN survey_questions q ON a.question_id = q.id WHERE a.response_id = r.id)
                FROM survey_responses r WHERE r.survey_id = ? AND r.is_complete = 1 ORDER BY r.completed_at DESC LIMIT ?''', (survey_id, limit))

            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'email': r[1], 'completed_at': r[2], 'answers': r[3]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_nps_score(self, days=90):
        """Calcule le score NPS"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT score FROM nps_scores WHERE created_at >= ?', (start,))
            scores = [r[0] for r in cursor.fetchall()]
            conn.close()

            if not scores:
                return {'nps': 0, 'promoters': 0, 'passives': 0, 'detractors': 0, 'total': 0}

            promoters = len([s for s in scores if s >= 9])
            passives = len([s for s in scores if 7 <= s < 9])
            detractors = len([s for s in scores if s < 7])
            total = len(scores)

            nps = round((promoters - detractors) / total * 100)

            return {
                'nps': nps, 'promoters': promoters, 'passives': passives, 'detractors': detractors,
                'total': total, 'promoter_pct': round(promoters/total*100, 1),
                'passive_pct': round(passives/total*100, 1), 'detractor_pct': round(detractors/total*100, 1)
            }
        except Exception as e:
            return {'error': str(e)}

    def analyze_feedback_ai(self, survey_id):
        """Analyse les feedbacks avec IA"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''SELECT a.answer_text FROM survey_answers a
                JOIN survey_responses r ON a.response_id = r.id
                JOIN survey_questions q ON a.question_id = q.id
                WHERE r.survey_id = ? AND q.question_type IN ('text', 'textarea')
                ORDER BY r.completed_at DESC LIMIT 50''', (survey_id,))
            feedbacks = [r[0] for r in cursor.fetchall() if r[0]]
            conn.close()

            if not feedbacks:
                return {'error': 'Pas de feedback a analyser'}

            prompt = f"""Analyse ces retours clients et genere un resume:

Feedbacks:
{chr(10).join(['- ' + f for f in feedbacks[:30]])}

Retourne en JSON:
{{
    "sentiment_global": "positif/neutre/negatif",
    "themes_principaux": ["theme1", "theme2", ...],
    "points_positifs": ["...", "..."],
    "points_amelioration": ["...", "..."],
    "suggestions_action": ["...", "..."]
}}"""

            response = call_ollama(prompt, 800) or call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
            return {'error': 'Pas de reponse IA'}
        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, days=30):
        """Statistiques sondages"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT COUNT(*) FROM surveys')
            total_surveys = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM surveys WHERE status = "active"')
            active = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(response_count) FROM surveys')
            total_responses = cursor.fetchone()[0] or 0

            cursor.execute('SELECT COUNT(*) FROM survey_responses WHERE completed_at >= ?', (start,))
            recent_responses = cursor.fetchone()[0]

            # NPS
            nps_data = self.get_nps_score(days)

            conn.close()
            return {
                'total_surveys': total_surveys, 'active_surveys': active,
                'total_responses': total_responses, 'recent_responses': recent_responses,
                'nps_score': nps_data.get('nps', 0), 'nps_total': nps_data.get('total', 0)
            }
        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 58: WEBHOOK AGENT - Integrations & Automatisations
# ============================================

class WebhookAgent:
    """Agent de webhooks - Integrations externes, evenements, callbacks"""
    name = "Webhook Agent"

    def init_db(self):
        conn = get_db()
        cursor = conn.cursor()

        # Webhooks sortants (on envoie)
        cursor.execute('''CREATE TABLE IF NOT EXISTS webhooks_outgoing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            event_type TEXT NOT NULL,
            method TEXT DEFAULT 'POST',
            headers TEXT,
            secret_key TEXT,
            is_active BOOLEAN DEFAULT 1,
            retry_count INTEGER DEFAULT 3,
            timeout_seconds INTEGER DEFAULT 30,
            last_triggered_at TIMESTAMP,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Webhooks entrants (on recoit)
        cursor.execute('''CREATE TABLE IF NOT EXISTS webhooks_incoming (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            endpoint_key TEXT UNIQUE,
            description TEXT,
            action_type TEXT,
            action_config TEXT,
            is_active BOOLEAN DEFAULT 1,
            require_signature BOOLEAN DEFAULT 0,
            secret_key TEXT,
            allowed_ips TEXT,
            received_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Logs des webhooks
        cursor.execute('''CREATE TABLE IF NOT EXISTS webhook_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            webhook_id INTEGER,
            direction TEXT,
            event_type TEXT,
            payload TEXT,
            response_code INTEGER,
            response_body TEXT,
            duration_ms INTEGER,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Event subscriptions
        cursor.execute('''CREATE TABLE IF NOT EXISTS webhook_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            webhook_id INTEGER,
            event_type TEXT,
            filter_conditions TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (webhook_id) REFERENCES webhooks_outgoing(id))''')

        conn.commit()
        conn.close()
        return {'success': True}

    def _generate_endpoint_key(self):
        import hashlib
        import random
        return hashlib.sha256(f"{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:32]

    def _generate_secret(self):
        import hashlib
        import random
        return hashlib.sha256(f"secret_{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:40]

    def create_outgoing_webhook(self, data):
        """Cree un webhook sortant"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            headers = data.get('headers')
            if isinstance(headers, dict):
                headers = json.dumps(headers)

            secret = data.get('secret_key') or self._generate_secret()

            cursor.execute('''INSERT INTO webhooks_outgoing
                (name, url, event_type, method, headers, secret_key, is_active, retry_count, timeout_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data.get('name', 'Webhook'), data.get('url'), data.get('event_type', 'all'),
                 data.get('method', 'POST'), headers, secret,
                 data.get('is_active', True), data.get('retry_count', 3), data.get('timeout_seconds', 30)))

            webhook_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'webhook_id': webhook_id, 'secret_key': secret}
        except Exception as e:
            return {'error': str(e)}

    def create_incoming_webhook(self, data):
        """Cree un webhook entrant (endpoint)"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            endpoint_key = data.get('endpoint_key') or self._generate_endpoint_key()
            secret = self._generate_secret() if data.get('require_signature') else None

            action_config = data.get('action_config')
            if isinstance(action_config, dict):
                action_config = json.dumps(action_config)

            cursor.execute('''INSERT INTO webhooks_incoming
                (name, endpoint_key, description, action_type, action_config, is_active, require_signature, secret_key, allowed_ips)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data.get('name', 'Incoming Webhook'), endpoint_key, data.get('description'),
                 data.get('action_type', 'log'), action_config, data.get('is_active', True),
                 data.get('require_signature', False), secret, data.get('allowed_ips')))

            webhook_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {
                'success': True, 'webhook_id': webhook_id,
                'endpoint': f"/api/webhook/receive/{endpoint_key}",
                'secret_key': secret
            }
        except Exception as e:
            return {'error': str(e)}

    def trigger_webhook(self, event_type, payload):
        """Declenche les webhooks pour un evenement"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''SELECT id, url, method, headers, secret_key, retry_count, timeout_seconds
                FROM webhooks_outgoing WHERE is_active = 1 AND (event_type = ? OR event_type = 'all')''', (event_type,))
            webhooks = cursor.fetchall()

            results = []
            for wh in webhooks:
                webhook_id, url, method, headers_json, secret, retries, timeout = wh
                headers = json.loads(headers_json) if headers_json else {}
                headers['Content-Type'] = 'application/json'
                headers['X-Webhook-Event'] = event_type

                # Signature HMAC
                if secret:
                    import hmac
                    import hashlib
                    payload_str = json.dumps(payload)
                    signature = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
                    headers['X-Webhook-Signature'] = signature

                # Envoyer le webhook
                start_time = datetime.now()
                try:
                    import requests
                    response = requests.request(method, url, json=payload, headers=headers, timeout=timeout)
                    duration = int((datetime.now() - start_time).total_seconds() * 1000)

                    # Log
                    cursor.execute('''INSERT INTO webhook_logs (webhook_id, direction, event_type, payload, response_code, response_body, duration_ms, status)
                        VALUES (?, 'outgoing', ?, ?, ?, ?, ?, ?)''',
                        (webhook_id, event_type, json.dumps(payload), response.status_code, response.text[:500], duration,
                         'success' if response.status_code < 400 else 'failed'))

                    if response.status_code < 400:
                        cursor.execute('UPDATE webhooks_outgoing SET success_count = success_count + 1, last_triggered_at = CURRENT_TIMESTAMP WHERE id = ?', (webhook_id,))
                        results.append({'webhook_id': webhook_id, 'status': 'success', 'code': response.status_code})
                    else:
                        cursor.execute('UPDATE webhooks_outgoing SET failure_count = failure_count + 1 WHERE id = ?', (webhook_id,))
                        results.append({'webhook_id': webhook_id, 'status': 'failed', 'code': response.status_code})

                except Exception as e:
                    cursor.execute('''INSERT INTO webhook_logs (webhook_id, direction, event_type, payload, status, error_message)
                        VALUES (?, 'outgoing', ?, ?, 'error', ?)''', (webhook_id, event_type, json.dumps(payload), str(e)))
                    cursor.execute('UPDATE webhooks_outgoing SET failure_count = failure_count + 1 WHERE id = ?', (webhook_id,))
                    results.append({'webhook_id': webhook_id, 'status': 'error', 'error': str(e)})

            conn.commit()
            conn.close()
            return {'success': True, 'triggered': len(results), 'results': results}
        except Exception as e:
            return {'error': str(e)}

    def receive_webhook(self, endpoint_key, payload, headers=None, ip_address=None):
        """Recoit et traite un webhook entrant"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT id, name, action_type, action_config, require_signature, secret_key, allowed_ips FROM webhooks_incoming WHERE endpoint_key = ? AND is_active = 1', (endpoint_key,))
            webhook = cursor.fetchone()

            if not webhook:
                return {'error': 'Webhook not found', 'code': 404}

            webhook_id, name, action_type, action_config, require_sig, secret, allowed_ips = webhook

            # Verifier IP
            if allowed_ips and ip_address:
                allowed = [ip.strip() for ip in allowed_ips.split(',')]
                if ip_address not in allowed:
                    return {'error': 'IP not allowed', 'code': 403}

            # Verifier signature
            if require_sig and secret:
                signature = headers.get('X-Webhook-Signature') or headers.get('x-webhook-signature')
                if not signature:
                    return {'error': 'Signature required', 'code': 401}
                import hmac
                import hashlib
                expected = hmac.new(secret.encode(), json.dumps(payload).encode(), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(signature, expected):
                    return {'error': 'Invalid signature', 'code': 401}

            # Log reception
            cursor.execute('''INSERT INTO webhook_logs (webhook_id, direction, event_type, payload, status)
                VALUES (?, 'incoming', ?, ?, 'received')''', (webhook_id, action_type, json.dumps(payload)))
            cursor.execute('UPDATE webhooks_incoming SET received_count = received_count + 1 WHERE id = ?', (webhook_id,))

            # Executer action
            result = self._execute_action(action_type, action_config, payload)

            conn.commit()
            conn.close()
            return {'success': True, 'action': action_type, 'result': result}
        except Exception as e:
            return {'error': str(e)}

    def _execute_action(self, action_type, action_config, payload):
        """Execute une action basee sur le webhook"""
        config = json.loads(action_config) if action_config else {}

        if action_type == 'log':
            return {'logged': True}

        elif action_type == 'create_contact':
            from agents_system import CRMAgent
            agent = CRMAgent()
            return agent.add_contact({
                'email': payload.get('email'),
                'name': payload.get('name'),
                'source': 'webhook'
            })

        elif action_type == 'create_ticket':
            from agents_system import SupportTicketAgent
            agent = SupportTicketAgent()
            return agent.create_ticket({
                'email': payload.get('email'),
                'subject': payload.get('subject', 'Ticket via webhook'),
                'description': payload.get('message', ''),
                'channel': 'webhook'
            })

        elif action_type == 'trigger_notification':
            from agents_system import NotificationAgent
            agent = NotificationAgent()
            return agent.send_notification({
                'type': config.get('notification_type', 'webhook'),
                'channel': config.get('channel', 'email'),
                'recipient': payload.get('email'),
                'subject': payload.get('subject', 'Notification webhook'),
                'message': payload.get('message', '')
            })

        return {'action': action_type, 'status': 'executed'}

    def get_webhooks(self, direction='outgoing', is_active=None, limit=50):
        """Liste les webhooks"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if direction == 'outgoing':
                query = 'SELECT id, name, url, event_type, is_active, success_count, failure_count, last_triggered_at FROM webhooks_outgoing'
            else:
                query = 'SELECT id, name, endpoint_key, action_type, is_active, received_count, created_at FROM webhooks_incoming'

            if is_active is not None:
                query += f' WHERE is_active = {1 if is_active else 0}'
            query += f' ORDER BY created_at DESC LIMIT {limit}'

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            if direction == 'outgoing':
                return [{'id': r[0], 'name': r[1], 'url': r[2], 'event_type': r[3], 'active': bool(r[4]),
                        'success': r[5], 'failures': r[6], 'last_triggered': r[7]} for r in rows]
            else:
                return [{'id': r[0], 'name': r[1], 'endpoint': f"/api/webhook/receive/{r[2]}",
                        'action': r[3], 'active': bool(r[4]), 'received': r[5], 'created_at': r[6]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_logs(self, webhook_id=None, direction=None, limit=100):
        """Liste les logs des webhooks"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, webhook_id, direction, event_type, response_code, duration_ms, status, error_message, created_at FROM webhook_logs WHERE 1=1'
            params = []

            if webhook_id:
                query += ' AND webhook_id = ?'
                params.append(webhook_id)
            if direction:
                query += ' AND direction = ?'
                params.append(direction)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'webhook_id': r[1], 'direction': r[2], 'event_type': r[3],
                    'code': r[4], 'duration_ms': r[5], 'status': r[6], 'error': r[7], 'created_at': r[8]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def toggle_webhook(self, webhook_id, direction='outgoing', is_active=True):
        """Active/desactive un webhook"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            table = 'webhooks_outgoing' if direction == 'outgoing' else 'webhooks_incoming'
            cursor.execute(f'UPDATE {table} SET is_active = ? WHERE id = ?', (is_active, webhook_id))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def delete_webhook(self, webhook_id, direction='outgoing'):
        """Supprime un webhook"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            table = 'webhooks_outgoing' if direction == 'outgoing' else 'webhooks_incoming'
            cursor.execute(f'DELETE FROM {table} WHERE id = ?', (webhook_id,))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_event_types(self):
        """Liste des types d'evenements disponibles"""
        return [
            {'type': 'contact.created', 'description': 'Nouveau contact CRM'},
            {'type': 'contact.updated', 'description': 'Contact mis a jour'},
            {'type': 'invoice.created', 'description': 'Nouvelle facture'},
            {'type': 'invoice.paid', 'description': 'Facture payee'},
            {'type': 'ticket.created', 'description': 'Nouveau ticket support'},
            {'type': 'ticket.resolved', 'description': 'Ticket resolu'},
            {'type': 'lead.scored', 'description': 'Lead score mis a jour'},
            {'type': 'appointment.booked', 'description': 'Rendez-vous reserve'},
            {'type': 'survey.completed', 'description': 'Sondage complete'},
            {'type': 'all', 'description': 'Tous les evenements'}
        ]

    def get_stats(self, days=30):
        """Statistiques webhooks"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT COUNT(*) FROM webhooks_outgoing WHERE is_active = 1')
            active_outgoing = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM webhooks_incoming WHERE is_active = 1')
            active_incoming = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM webhook_logs WHERE direction = "outgoing" AND created_at >= ?', (start,))
            sent = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM webhook_logs WHERE direction = "incoming" AND created_at >= ?', (start,))
            received = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM webhook_logs WHERE status = "success" AND created_at >= ?', (start,))
            successful = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM webhook_logs WHERE status IN ("failed", "error") AND created_at >= ?', (start,))
            failed = cursor.fetchone()[0]

            conn.close()
            return {
                'active_outgoing': active_outgoing, 'active_incoming': active_incoming,
                'sent': sent, 'received': received, 'successful': successful, 'failed': failed,
                'success_rate': round(successful/(sent+received)*100, 1) if (sent+received) > 0 else 0
            }
        except Exception as e:
            return {'error': str(e)}


# ============================================
# AGENT 59: AUTOMATION AGENT - Workflows & Rules
# ============================================

class AutomationAgent:
    """Agent d'automatisation - Workflows, regles, triggers, actions"""
    name = "Automation Agent"

    def init_db(self):
        conn = get_db()
        cursor = conn.cursor()

        # Workflows
        cursor.execute('''CREATE TABLE IF NOT EXISTS automations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            trigger_type TEXT NOT NULL,
            trigger_config TEXT,
            is_active BOOLEAN DEFAULT 1,
            run_count INTEGER DEFAULT 0,
            last_run_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Actions du workflow
        cursor.execute('''CREATE TABLE IF NOT EXISTS automation_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            automation_id INTEGER,
            action_type TEXT NOT NULL,
            action_config TEXT,
            sort_order INTEGER DEFAULT 0,
            delay_minutes INTEGER DEFAULT 0,
            condition TEXT,
            FOREIGN KEY (automation_id) REFERENCES automations(id))''')

        # Logs d'execution
        cursor.execute('''CREATE TABLE IF NOT EXISTS automation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            automation_id INTEGER,
            trigger_data TEXT,
            status TEXT,
            actions_executed INTEGER DEFAULT 0,
            error_message TEXT,
            duration_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (automation_id) REFERENCES automations(id))''')

        # Scheduled tasks
        cursor.execute('''CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            automation_id INTEGER,
            scheduled_for TIMESTAMP,
            action_data TEXT,
            status TEXT DEFAULT 'pending',
            executed_at TIMESTAMP,
            FOREIGN KEY (automation_id) REFERENCES automations(id))''')

        conn.commit()
        conn.close()
        return {'success': True}

    def create_automation(self, data):
        """Cree une automation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            trigger_config = data.get('trigger_config')
            if isinstance(trigger_config, dict):
                trigger_config = json.dumps(trigger_config)

            cursor.execute('''INSERT INTO automations (name, description, trigger_type, trigger_config, is_active)
                VALUES (?, ?, ?, ?, ?)''',
                (data.get('name', 'New Automation'), data.get('description'),
                 data.get('trigger_type', 'manual'), trigger_config, data.get('is_active', True)))

            automation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'automation_id': automation_id}
        except Exception as e:
            return {'error': str(e)}

    def add_action(self, automation_id, data):
        """Ajoute une action a l'automation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT MAX(sort_order) FROM automation_actions WHERE automation_id = ?', (automation_id,))
            max_order = cursor.fetchone()[0] or 0

            action_config = data.get('action_config')
            if isinstance(action_config, dict):
                action_config = json.dumps(action_config)

            cursor.execute('''INSERT INTO automation_actions (automation_id, action_type, action_config, sort_order, delay_minutes, condition)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (automation_id, data.get('action_type'), action_config, max_order + 1,
                 data.get('delay_minutes', 0), data.get('condition')))

            action_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {'success': True, 'action_id': action_id}
        except Exception as e:
            return {'error': str(e)}

    def create_workflow_template(self, template_name):
        """Cree un workflow depuis un template"""
        templates = {
            'welcome_sequence': {
                'name': 'Sequence Bienvenue',
                'trigger_type': 'contact.created',
                'actions': [
                    {'action_type': 'send_email', 'action_config': {'template': 'welcome'}, 'delay_minutes': 0},
                    {'action_type': 'send_email', 'action_config': {'template': 'getting_started'}, 'delay_minutes': 1440},
                    {'action_type': 'create_task', 'action_config': {'task': 'Appeler nouveau client'}, 'delay_minutes': 2880}
                ]
            },
            'lead_nurturing': {
                'name': 'Nurturing Leads',
                'trigger_type': 'lead.scored',
                'trigger_config': {'min_score': 50},
                'actions': [
                    {'action_type': 'send_email', 'action_config': {'template': 'hot_lead'}},
                    {'action_type': 'notify_team', 'action_config': {'channel': 'slack', 'message': 'Nouveau lead chaud!'}}
                ]
            },
            'ticket_escalation': {
                'name': 'Escalade Tickets',
                'trigger_type': 'ticket.overdue',
                'actions': [
                    {'action_type': 'update_ticket', 'action_config': {'priority': 'urgent'}},
                    {'action_type': 'notify_team', 'action_config': {'message': 'Ticket en retard!'}}
                ]
            },
            'invoice_reminder': {
                'name': 'Rappel Facture',
                'trigger_type': 'invoice.overdue',
                'actions': [
                    {'action_type': 'send_email', 'action_config': {'template': 'payment_reminder'}},
                    {'action_type': 'send_email', 'action_config': {'template': 'payment_urgent'}, 'delay_minutes': 4320}
                ]
            }
        }

        if template_name not in templates:
            return {'error': f'Template inconnu. Disponibles: {list(templates.keys())}'}

        template = templates[template_name]
        result = self.create_automation({
            'name': template['name'],
            'trigger_type': template['trigger_type'],
            'trigger_config': template.get('trigger_config')
        })

        if 'error' in result:
            return result

        automation_id = result['automation_id']
        for action in template['actions']:
            self.add_action(automation_id, action)

        return {'success': True, 'automation_id': automation_id, 'template': template_name}

    def trigger_automation(self, trigger_type, trigger_data):
        """Declenche les automations correspondant au trigger"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT id, name, trigger_config FROM automations WHERE trigger_type = ? AND is_active = 1', (trigger_type,))
            automations = cursor.fetchall()

            results = []
            for auto in automations:
                auto_id, name, trigger_config = auto
                config = json.loads(trigger_config) if trigger_config else {}

                # Verifier conditions
                if not self._check_conditions(config, trigger_data):
                    continue

                # Executer
                start_time = datetime.now()
                actions_executed = 0
                error = None

                try:
                    cursor.execute('SELECT action_type, action_config, delay_minutes, condition FROM automation_actions WHERE automation_id = ? ORDER BY sort_order', (auto_id,))
                    actions = cursor.fetchall()

                    for action in actions:
                        action_type, action_config, delay, condition = action
                        config = json.loads(action_config) if action_config else {}

                        if delay > 0:
                            # Scheduler pour plus tard
                            scheduled_time = datetime.now() + timedelta(minutes=delay)
                            cursor.execute('INSERT INTO scheduled_tasks (automation_id, scheduled_for, action_data, status) VALUES (?, ?, ?, ?)',
                                (auto_id, scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
                                 json.dumps({'action_type': action_type, 'config': config, 'trigger_data': trigger_data}), 'pending'))
                        else:
                            self._execute_action(action_type, config, trigger_data)
                        actions_executed += 1

                except Exception as e:
                    error = str(e)

                duration = int((datetime.now() - start_time).total_seconds() * 1000)

                # Log
                cursor.execute('''INSERT INTO automation_logs (automation_id, trigger_data, status, actions_executed, error_message, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (auto_id, json.dumps(trigger_data), 'error' if error else 'success', actions_executed, error, duration))

                cursor.execute('UPDATE automations SET run_count = run_count + 1, last_run_at = CURRENT_TIMESTAMP WHERE id = ?', (auto_id,))

                results.append({'automation_id': auto_id, 'name': name, 'actions': actions_executed, 'status': 'error' if error else 'success'})

            conn.commit()
            conn.close()
            return {'success': True, 'triggered': len(results), 'results': results}
        except Exception as e:
            return {'error': str(e)}

    def _check_conditions(self, config, data):
        """Verifie les conditions du trigger"""
        if not config:
            return True
        if 'min_score' in config and data.get('score', 0) < config['min_score']:
            return False
        if 'status' in config and data.get('status') != config['status']:
            return False
        if 'source' in config and data.get('source') != config['source']:
            return False
        return True

    def _execute_action(self, action_type, config, trigger_data):
        """Execute une action"""
        if action_type == 'send_email':
            return {'action': 'send_email', 'template': config.get('template'), 'status': 'sent'}

        elif action_type == 'create_contact':
            from agents_system import CRMAgent
            agent = CRMAgent()
            return agent.add_contact(trigger_data)

        elif action_type == 'update_contact':
            from agents_system import CRMAgent
            agent = CRMAgent()
            return agent.update_contact(trigger_data.get('contact_id'), config)

        elif action_type == 'create_ticket':
            from agents_system import SupportTicketAgent
            agent = SupportTicketAgent()
            return agent.create_ticket({**trigger_data, **config})

        elif action_type == 'update_ticket':
            from agents_system import SupportTicketAgent
            agent = SupportTicketAgent()
            return agent.update_ticket(trigger_data.get('ticket_id'), config)

        elif action_type == 'send_notification':
            from agents_system import NotificationAgent
            agent = NotificationAgent()
            return agent.send_notification({**config, **trigger_data})

        elif action_type == 'enroll_sequence':
            from agents_system import EmailCampaignAgent
            agent = EmailCampaignAgent()
            return agent.enroll_contact(config.get('sequence_id'), trigger_data.get('contact_id'))

        elif action_type == 'score_lead':
            from agents_system import LeadScoringAgent
            agent = LeadScoringAgent()
            return agent.score_lead(trigger_data.get('contact_id'), config)

        elif action_type == 'trigger_webhook':
            from agents_system import WebhookAgent
            agent = WebhookAgent()
            return agent.trigger_webhook(config.get('event_type', 'automation'), trigger_data)

        return {'action': action_type, 'status': 'executed'}

    def get_automation(self, automation_id):
        """Recupere une automation avec ses actions"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT id, name, description, trigger_type, trigger_config, is_active, run_count, last_run_at FROM automations WHERE id = ?', (automation_id,))
            a = cursor.fetchone()
            if not a:
                return {'error': 'Automation non trouvee'}

            cursor.execute('SELECT id, action_type, action_config, sort_order, delay_minutes, condition FROM automation_actions WHERE automation_id = ? ORDER BY sort_order', (automation_id,))
            actions = [{'id': r[0], 'type': r[1], 'config': json.loads(r[2]) if r[2] else None, 'order': r[3], 'delay': r[4], 'condition': r[5]} for r in cursor.fetchall()]

            conn.close()
            return {
                'id': a[0], 'name': a[1], 'description': a[2], 'trigger_type': a[3],
                'trigger_config': json.loads(a[4]) if a[4] else None, 'is_active': bool(a[5]),
                'run_count': a[6], 'last_run_at': a[7], 'actions': actions
            }
        except Exception as e:
            return {'error': str(e)}

    def get_automations(self, is_active=None, limit=50):
        """Liste les automations"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, name, trigger_type, is_active, run_count, last_run_at FROM automations'
            if is_active is not None:
                query += f' WHERE is_active = {1 if is_active else 0}'
            query += ' ORDER BY created_at DESC LIMIT ?'

            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'name': r[1], 'trigger': r[2], 'active': bool(r[3]), 'runs': r[4], 'last_run': r[5]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def toggle_automation(self, automation_id, is_active=True):
        """Active/desactive une automation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE automations SET is_active = ? WHERE id = ?', (is_active, automation_id))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def delete_automation(self, automation_id):
        """Supprime une automation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM automation_actions WHERE automation_id = ?', (automation_id,))
            cursor.execute('DELETE FROM automations WHERE id = ?', (automation_id,))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def get_logs(self, automation_id=None, status=None, limit=100):
        """Liste les logs"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT l.id, l.automation_id, a.name, l.status, l.actions_executed, l.duration_ms, l.created_at FROM automation_logs l JOIN automations a ON l.automation_id = a.id WHERE 1=1'
            params = []

            if automation_id:
                query += ' AND l.automation_id = ?'
                params.append(automation_id)
            if status:
                query += ' AND l.status = ?'
                params.append(status)

            query += ' ORDER BY l.created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'automation_id': r[1], 'name': r[2], 'status': r[3], 'actions': r[4], 'duration_ms': r[5], 'created_at': r[6]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_trigger_types(self):
        """Liste des types de triggers"""
        return [
            {'type': 'contact.created', 'description': 'Nouveau contact'},
            {'type': 'contact.updated', 'description': 'Contact modifie'},
            {'type': 'lead.scored', 'description': 'Lead score change'},
            {'type': 'ticket.created', 'description': 'Nouveau ticket'},
            {'type': 'ticket.resolved', 'description': 'Ticket resolu'},
            {'type': 'ticket.overdue', 'description': 'Ticket en retard'},
            {'type': 'invoice.created', 'description': 'Nouvelle facture'},
            {'type': 'invoice.paid', 'description': 'Facture payee'},
            {'type': 'invoice.overdue', 'description': 'Facture en retard'},
            {'type': 'appointment.booked', 'description': 'RDV reserve'},
            {'type': 'survey.completed', 'description': 'Sondage termine'},
            {'type': 'manual', 'description': 'Declenchement manuel'},
            {'type': 'scheduled', 'description': 'Planifie (cron)'}
        ]

    def get_action_types(self):
        """Liste des types d'actions"""
        return [
            {'type': 'send_email', 'description': 'Envoyer un email'},
            {'type': 'send_notification', 'description': 'Envoyer notification'},
            {'type': 'create_contact', 'description': 'Creer contact CRM'},
            {'type': 'update_contact', 'description': 'Modifier contact'},
            {'type': 'create_ticket', 'description': 'Creer ticket support'},
            {'type': 'update_ticket', 'description': 'Modifier ticket'},
            {'type': 'enroll_sequence', 'description': 'Inscrire a sequence email'},
            {'type': 'score_lead', 'description': 'Scorer le lead'},
            {'type': 'trigger_webhook', 'description': 'Declencher webhook'},
            {'type': 'wait', 'description': 'Attendre X minutes'}
        ]

    def get_stats(self, days=30):
        """Statistiques automations"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT COUNT(*) FROM automations WHERE is_active = 1')
            active = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM automations')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM automation_logs WHERE created_at >= ?', (start,))
            executions = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM automation_logs WHERE status = "success" AND created_at >= ?', (start,))
            successful = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(actions_executed) FROM automation_logs WHERE created_at >= ?', (start,))
            actions = cursor.fetchone()[0] or 0

            cursor.execute('SELECT AVG(duration_ms) FROM automation_logs WHERE created_at >= ?', (start,))
            avg_duration = cursor.fetchone()[0] or 0

            conn.close()
            return {
                'total_automations': total, 'active_automations': active,
                'executions': executions, 'successful': successful,
                'success_rate': round(successful/executions*100, 1) if executions > 0 else 0,
                'actions_executed': actions, 'avg_duration_ms': round(avg_duration)
            }
        except Exception as e:
            return {'error': str(e)}


# ========== AGENT 60: AFFILIATE AGENT ==========
class AffiliateAgent:
    """Agent de programme d'affiliation - Affilies, commissions, payouts, tracking"""
    name = "Affiliate Agent"

    def init_db(self):
        """Initialise les tables affiliation"""
        conn = get_db()
        cursor = conn.cursor()

        # Table affilies
        cursor.execute('''CREATE TABLE IF NOT EXISTS affiliates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            company TEXT,
            website TEXT,
            referral_code TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'standard',
            commission_rate REAL DEFAULT 10.0,
            status TEXT DEFAULT 'pending',
            balance REAL DEFAULT 0,
            total_earned REAL DEFAULT 0,
            total_paid REAL DEFAULT 0,
            referrals_count INTEGER DEFAULT 0,
            payment_method TEXT,
            payment_details TEXT,
            notes TEXT,
            approved_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Table referrals (conversions)
        cursor.execute('''CREATE TABLE IF NOT EXISTS affiliate_referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id INTEGER NOT NULL,
            referral_code TEXT NOT NULL,
            visitor_ip TEXT,
            visitor_country TEXT,
            landing_page TEXT,
            source TEXT,
            converted INTEGER DEFAULT 0,
            customer_email TEXT,
            customer_name TEXT,
            order_id TEXT,
            order_amount REAL,
            commission_amount REAL,
            commission_paid INTEGER DEFAULT 0,
            click_at TEXT DEFAULT CURRENT_TIMESTAMP,
            converted_at TEXT,
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
        )''')

        # Table commissions
        cursor.execute('''CREATE TABLE IF NOT EXISTS affiliate_commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id INTEGER NOT NULL,
            referral_id INTEGER,
            amount REAL NOT NULL,
            type TEXT DEFAULT 'sale',
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
        )''')

        # Table payouts
        cursor.execute('''CREATE TABLE IF NOT EXISTS affiliate_payouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            payment_reference TEXT,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            processed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
        )''')

        # Table tiers (paliers de commission)
        cursor.execute('''CREATE TABLE IF NOT EXISTS affiliate_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            min_sales INTEGER DEFAULT 0,
            commission_rate REAL NOT NULL,
            bonus_rate REAL DEFAULT 0,
            description TEXT,
            benefits TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Table clicks tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS affiliate_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id INTEGER NOT NULL,
            referral_code TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            landing_page TEXT,
            referer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
        )''')

        conn.commit()
        conn.close()

    def _generate_referral_code(self, name):
        """Genere un code de parrainage unique"""
        import hashlib
        base = name.lower().replace(' ', '')[:6]
        suffix = hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:4]
        return f"{base}{suffix}".upper()

    def register_affiliate(self, data):
        """Inscrit un nouvel affilie"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            name = data.get('name', '')
            email = data.get('email', '')
            if not name or not email:
                return {'error': 'Nom et email requis'}

            # Verifier si email existe
            cursor.execute('SELECT id FROM affiliates WHERE email = ?', (email,))
            if cursor.fetchone():
                return {'error': 'Email deja inscrit'}

            referral_code = self._generate_referral_code(name)

            cursor.execute('''INSERT INTO affiliates (user_name, email, phone, company, website, referral_code, payment_method, payment_details, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, email, data.get('phone'), data.get('company'), data.get('website'),
                 referral_code, data.get('payment_method'), data.get('payment_details'), data.get('notes')))

            affiliate_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {
                'success': True,
                'affiliate_id': affiliate_id,
                'referral_code': referral_code,
                'referral_link': f"https://seoparai.com/?ref={referral_code}",
                'message': 'Inscription soumise, en attente d\'approbation'
            }
        except Exception as e:
            return {'error': str(e)}

    def approve_affiliate(self, affiliate_id, commission_rate=None, tier='standard'):
        """Approuve un affilie"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            rate = commission_rate if commission_rate else 10.0
            cursor.execute('''UPDATE affiliates SET status = 'active', tier = ?, commission_rate = ?, approved_at = ? WHERE id = ?''',
                (tier, rate, datetime.now().isoformat(), affiliate_id))

            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Affilie approuve'}
        except Exception as e:
            return {'error': str(e)}

    def track_click(self, referral_code, data):
        """Enregistre un clic sur lien affilie"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Trouver l'affilie
            cursor.execute('SELECT id, status FROM affiliates WHERE referral_code = ?', (referral_code,))
            affiliate = cursor.fetchone()
            if not affiliate:
                return {'error': 'Code invalide'}
            if affiliate[1] != 'active':
                return {'error': 'Affilie non actif'}

            cursor.execute('''INSERT INTO affiliate_clicks (affiliate_id, referral_code, ip_address, user_agent, landing_page, referer)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (affiliate[0], referral_code, data.get('ip'), data.get('user_agent'), data.get('page'), data.get('referer')))

            # Creer referral pour tracking conversion
            cursor.execute('''INSERT INTO affiliate_referrals (affiliate_id, referral_code, visitor_ip, landing_page, source)
                VALUES (?, ?, ?, ?, ?)''',
                (affiliate[0], referral_code, data.get('ip'), data.get('page'), data.get('source')))

            referral_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'referral_id': referral_id}
        except Exception as e:
            return {'error': str(e)}

    def record_conversion(self, referral_code, data):
        """Enregistre une conversion (vente)"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Trouver l'affilie
            cursor.execute('SELECT id, commission_rate FROM affiliates WHERE referral_code = ? AND status = "active"', (referral_code,))
            affiliate = cursor.fetchone()
            if not affiliate:
                return {'error': 'Affilie non trouve ou inactif'}

            affiliate_id = affiliate[0]
            commission_rate = affiliate[1]
            order_amount = data.get('amount', 0)
            commission = round(order_amount * (commission_rate / 100), 2)

            # Mettre a jour ou creer referral
            cursor.execute('''INSERT INTO affiliate_referrals (affiliate_id, referral_code, converted, customer_email, customer_name, order_id, order_amount, commission_amount, converted_at)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)''',
                (affiliate_id, referral_code, data.get('customer_email'), data.get('customer_name'),
                 data.get('order_id'), order_amount, commission, datetime.now().isoformat()))

            referral_id = cursor.lastrowid

            # Creer commission
            cursor.execute('''INSERT INTO affiliate_commissions (affiliate_id, referral_id, amount, type, description)
                VALUES (?, ?, ?, 'sale', ?)''',
                (affiliate_id, referral_id, commission, f"Commission sur commande {data.get('order_id')}"))

            # Mettre a jour stats affilie
            cursor.execute('''UPDATE affiliates SET
                balance = balance + ?,
                total_earned = total_earned + ?,
                referrals_count = referrals_count + 1
                WHERE id = ?''', (commission, commission, affiliate_id))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'referral_id': referral_id,
                'commission': commission,
                'message': f'Commission de ${commission} enregistree'
            }
        except Exception as e:
            return {'error': str(e)}

    def get_affiliate(self, affiliate_id):
        """Recupere un affilie"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''SELECT id, user_name, email, phone, company, website, referral_code, tier, commission_rate, status, balance, total_earned, total_paid, referrals_count, payment_method, approved_at, created_at
                FROM affiliates WHERE id = ?''', (affiliate_id,))
            a = cursor.fetchone()
            conn.close()

            if not a:
                return {'error': 'Affilie non trouve'}

            return {
                'id': a[0], 'name': a[1], 'email': a[2], 'phone': a[3],
                'company': a[4], 'website': a[5], 'referral_code': a[6],
                'tier': a[7], 'commission_rate': a[8], 'status': a[9],
                'balance': a[10], 'total_earned': a[11], 'total_paid': a[12],
                'referrals_count': a[13], 'payment_method': a[14],
                'approved_at': a[15], 'created_at': a[16],
                'referral_link': f"https://seoparai.com/?ref={a[6]}"
            }
        except Exception as e:
            return {'error': str(e)}

    def get_affiliates(self, status=None, tier=None, limit=50):
        """Liste les affilies"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, user_name, email, referral_code, tier, commission_rate, status, balance, referrals_count, created_at FROM affiliates WHERE 1=1'
            params = []

            if status:
                query += ' AND status = ?'
                params.append(status)
            if tier:
                query += ' AND tier = ?'
                params.append(tier)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'name': r[1], 'email': r[2], 'code': r[3], 'tier': r[4], 'rate': r[5], 'status': r[6], 'balance': r[7], 'referrals': r[8], 'created_at': r[9]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_referrals(self, affiliate_id=None, converted=None, limit=100):
        """Liste les referrals"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''SELECT r.id, r.affiliate_id, a.user_name, r.referral_code, r.converted, r.customer_email, r.order_amount, r.commission_amount, r.click_at, r.converted_at
                FROM affiliate_referrals r JOIN affiliates a ON r.affiliate_id = a.id WHERE 1=1'''
            params = []

            if affiliate_id:
                query += ' AND r.affiliate_id = ?'
                params.append(affiliate_id)
            if converted is not None:
                query += ' AND r.converted = ?'
                params.append(1 if converted else 0)

            query += ' ORDER BY r.click_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'affiliate_id': r[1], 'affiliate_name': r[2], 'code': r[3], 'converted': bool(r[4]), 'customer': r[5], 'amount': r[6], 'commission': r[7], 'clicked_at': r[8], 'converted_at': r[9]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def request_payout(self, affiliate_id, amount=None):
        """Demande de paiement"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT balance, payment_method, status FROM affiliates WHERE id = ?', (affiliate_id,))
            affiliate = cursor.fetchone()
            if not affiliate:
                return {'error': 'Affilie non trouve'}
            if affiliate[2] != 'active':
                return {'error': 'Affilie non actif'}

            balance = affiliate[0]
            payout_amount = amount if amount and amount <= balance else balance

            if payout_amount < 50:
                return {'error': 'Minimum $50 pour paiement'}

            cursor.execute('''INSERT INTO affiliate_payouts (affiliate_id, amount, payment_method, status)
                VALUES (?, ?, ?, 'pending')''', (affiliate_id, payout_amount, affiliate[1]))

            payout_id = cursor.lastrowid

            # Deduire du solde
            cursor.execute('UPDATE affiliates SET balance = balance - ? WHERE id = ?', (payout_amount, affiliate_id))

            conn.commit()
            conn.close()

            return {'success': True, 'payout_id': payout_id, 'amount': payout_amount}
        except Exception as e:
            return {'error': str(e)}

    def process_payout(self, payout_id, payment_reference=None):
        """Traite un paiement"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT affiliate_id, amount FROM affiliate_payouts WHERE id = ? AND status = "pending"', (payout_id,))
            payout = cursor.fetchone()
            if not payout:
                return {'error': 'Paiement non trouve ou deja traite'}

            cursor.execute('''UPDATE affiliate_payouts SET status = 'completed', payment_reference = ?, processed_at = ? WHERE id = ?''',
                (payment_reference, datetime.now().isoformat(), payout_id))

            cursor.execute('UPDATE affiliates SET total_paid = total_paid + ? WHERE id = ?', (payout[1], payout[0]))

            conn.commit()
            conn.close()

            return {'success': True, 'message': 'Paiement effectue'}
        except Exception as e:
            return {'error': str(e)}

    def get_payouts(self, affiliate_id=None, status=None, limit=50):
        """Liste les paiements"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = '''SELECT p.id, p.affiliate_id, a.user_name, p.amount, p.payment_method, p.payment_reference, p.status, p.processed_at, p.created_at
                FROM affiliate_payouts p JOIN affiliates a ON p.affiliate_id = a.id WHERE 1=1'''
            params = []

            if affiliate_id:
                query += ' AND p.affiliate_id = ?'
                params.append(affiliate_id)
            if status:
                query += ' AND p.status = ?'
                params.append(status)

            query += ' ORDER BY p.created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'affiliate_id': r[1], 'name': r[2], 'amount': r[3], 'method': r[4], 'reference': r[5], 'status': r[6], 'processed_at': r[7], 'created_at': r[8]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def create_tier(self, data):
        """Cree un palier de commission"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO affiliate_tiers (name, min_sales, commission_rate, bonus_rate, description, benefits)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (data.get('name'), data.get('min_sales', 0), data.get('commission_rate', 10),
                 data.get('bonus_rate', 0), data.get('description'), data.get('benefits')))

            tier_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'tier_id': tier_id}
        except Exception as e:
            return {'error': str(e)}

    def get_tiers(self):
        """Liste les paliers"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, min_sales, commission_rate, bonus_rate, description, benefits FROM affiliate_tiers ORDER BY min_sales')
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'name': r[1], 'min_sales': r[2], 'rate': r[3], 'bonus': r[4], 'description': r[5], 'benefits': r[6]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def setup_default_tiers(self):
        """Configure les paliers par defaut"""
        try:
            tiers = [
                {'name': 'bronze', 'min_sales': 0, 'commission_rate': 10, 'bonus_rate': 0, 'description': 'Niveau debutant', 'benefits': 'Commission 10%'},
                {'name': 'silver', 'min_sales': 5, 'commission_rate': 12, 'bonus_rate': 2, 'description': '5+ ventes', 'benefits': 'Commission 12% + Bonus 2%'},
                {'name': 'gold', 'min_sales': 15, 'commission_rate': 15, 'bonus_rate': 5, 'description': '15+ ventes', 'benefits': 'Commission 15% + Bonus 5%'},
                {'name': 'platinum', 'min_sales': 30, 'commission_rate': 20, 'bonus_rate': 10, 'description': '30+ ventes', 'benefits': 'Commission 20% + Bonus 10% + Support prioritaire'}
            ]
            for t in tiers:
                self.create_tier(t)
            return {'success': True, 'message': '4 paliers crees'}
        except Exception as e:
            return {'error': str(e)}

    def update_affiliate_tier(self, affiliate_id):
        """Met a jour le palier selon les ventes"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT referrals_count FROM affiliates WHERE id = ?', (affiliate_id,))
            result = cursor.fetchone()
            if not result:
                return {'error': 'Affilie non trouve'}

            sales = result[0]

            cursor.execute('SELECT name, commission_rate, bonus_rate FROM affiliate_tiers WHERE min_sales <= ? ORDER BY min_sales DESC LIMIT 1', (sales,))
            tier = cursor.fetchone()

            if tier:
                cursor.execute('UPDATE affiliates SET tier = ?, commission_rate = ? WHERE id = ?',
                    (tier[0], tier[1] + tier[2], affiliate_id))
                conn.commit()
                conn.close()
                return {'success': True, 'tier': tier[0], 'new_rate': tier[1] + tier[2]}

            conn.close()
            return {'success': True, 'message': 'Aucun changement'}
        except Exception as e:
            return {'error': str(e)}

    def get_affiliate_dashboard(self, affiliate_id):
        """Dashboard affilie avec stats"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Info affilie
            cursor.execute('SELECT user_name, referral_code, tier, commission_rate, balance, total_earned, total_paid, referrals_count FROM affiliates WHERE id = ?', (affiliate_id,))
            a = cursor.fetchone()
            if not a:
                return {'error': 'Affilie non trouve'}

            # Clics ce mois
            month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM affiliate_clicks WHERE affiliate_id = ? AND created_at >= ?', (affiliate_id, month_start))
            clicks_month = cursor.fetchone()[0]

            # Conversions ce mois
            cursor.execute('SELECT COUNT(*), SUM(order_amount), SUM(commission_amount) FROM affiliate_referrals WHERE affiliate_id = ? AND converted = 1 AND converted_at >= ?', (affiliate_id, month_start))
            conv = cursor.fetchone()

            # Paiements en attente
            cursor.execute('SELECT SUM(amount) FROM affiliate_payouts WHERE affiliate_id = ? AND status = "pending"', (affiliate_id,))
            pending = cursor.fetchone()[0] or 0

            # Top landing pages
            cursor.execute('SELECT landing_page, COUNT(*) as cnt FROM affiliate_clicks WHERE affiliate_id = ? GROUP BY landing_page ORDER BY cnt DESC LIMIT 5', (affiliate_id,))
            top_pages = [{'page': r[0], 'clicks': r[1]} for r in cursor.fetchall()]

            conn.close()

            return {
                'name': a[0],
                'referral_code': a[1],
                'referral_link': f"https://seoparai.com/?ref={a[1]}",
                'tier': a[2],
                'commission_rate': a[3],
                'balance': a[4],
                'total_earned': a[5],
                'total_paid': a[6],
                'total_referrals': a[7],
                'month': {
                    'clicks': clicks_month,
                    'conversions': conv[0] or 0,
                    'revenue': conv[1] or 0,
                    'commissions': conv[2] or 0
                },
                'pending_payout': pending,
                'top_pages': top_pages
            }
        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, days=30):
        """Statistiques globales programme affiliation"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT COUNT(*) FROM affiliates WHERE status = "active"')
            active_affiliates = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM affiliates WHERE status = "pending"')
            pending = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM affiliate_clicks WHERE created_at >= ?', (start,))
            clicks = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*), SUM(order_amount), SUM(commission_amount) FROM affiliate_referrals WHERE converted = 1 AND converted_at >= ?', (start,))
            conv = cursor.fetchone()

            cursor.execute('SELECT SUM(amount) FROM affiliate_payouts WHERE status = "completed" AND processed_at >= ?', (start,))
            paid = cursor.fetchone()[0] or 0

            cursor.execute('SELECT SUM(balance) FROM affiliates')
            total_owed = cursor.fetchone()[0] or 0

            # Top affilies
            cursor.execute('''SELECT a.user_name, COUNT(r.id) as sales, SUM(r.commission_amount) as comm
                FROM affiliates a JOIN affiliate_referrals r ON a.id = r.affiliate_id
                WHERE r.converted = 1 AND r.converted_at >= ?
                GROUP BY a.id ORDER BY comm DESC LIMIT 5''', (start,))
            top = [{'name': r[0], 'sales': r[1], 'commissions': r[2]} for r in cursor.fetchall()]

            conn.close()

            conversion_rate = round((conv[0] or 0) / clicks * 100, 2) if clicks > 0 else 0

            return {
                'active_affiliates': active_affiliates,
                'pending_applications': pending,
                'period_clicks': clicks,
                'period_conversions': conv[0] or 0,
                'conversion_rate': conversion_rate,
                'period_revenue': conv[1] or 0,
                'period_commissions': conv[2] or 0,
                'period_paid': paid,
                'total_owed': total_owed,
                'top_affiliates': top
            }
        except Exception as e:
            return {'error': str(e)}


# ========== AGENT 61: LOYALTY AGENT ==========
class LoyaltyAgent:
    """Agent de programme de fidelite - Points, recompenses, niveaux, promotions"""
    name = "Loyalty Agent"

    def init_db(self):
        """Initialise les tables fidelite"""
        conn = get_db()
        cursor = conn.cursor()

        # Table membres fidelite
        cursor.execute('''CREATE TABLE IF NOT EXISTS loyalty_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            customer_email TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            phone TEXT,
            points_balance INTEGER DEFAULT 0,
            points_earned_total INTEGER DEFAULT 0,
            points_redeemed_total INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'bronze',
            tier_points INTEGER DEFAULT 0,
            join_date TEXT DEFAULT CURRENT_TIMESTAMP,
            last_activity TEXT,
            birthday TEXT,
            preferences TEXT,
            status TEXT DEFAULT 'active',
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Table transactions points
        cursor.execute('''CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            points INTEGER NOT NULL,
            description TEXT,
            order_id TEXT,
            order_amount REAL,
            expires_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES loyalty_members(id)
        )''')

        # Table recompenses
        cursor.execute('''CREATE TABLE IF NOT EXISTS loyalty_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            points_cost INTEGER NOT NULL,
            reward_type TEXT DEFAULT 'discount',
            reward_value REAL,
            reward_code TEXT,
            stock INTEGER DEFAULT -1,
            tier_required TEXT,
            is_active INTEGER DEFAULT 1,
            valid_from TEXT,
            valid_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Table echanges recompenses
        cursor.execute('''CREATE TABLE IF NOT EXISTS loyalty_redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            reward_id INTEGER NOT NULL,
            points_spent INTEGER NOT NULL,
            redemption_code TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            used_at TEXT,
            expires_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES loyalty_members(id),
            FOREIGN KEY (reward_id) REFERENCES loyalty_rewards(id)
        )''')

        # Table niveaux/tiers
        cursor.execute('''CREATE TABLE IF NOT EXISTS loyalty_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            min_points INTEGER DEFAULT 0,
            points_multiplier REAL DEFAULT 1.0,
            benefits TEXT,
            badge_color TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Table promotions bonus points
        cursor.execute('''CREATE TABLE IF NOT EXISTS loyalty_promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            promo_type TEXT DEFAULT 'multiplier',
            value REAL DEFAULT 2.0,
            conditions TEXT,
            valid_from TEXT,
            valid_until TEXT,
            is_active INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
        conn.close()

    def _generate_referral_code(self, name):
        """Genere un code de parrainage"""
        import hashlib
        base = name.upper().replace(' ', '')[:4]
        suffix = hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:4].upper()
        return f"REF{base}{suffix}"

    def _generate_redemption_code(self):
        """Genere un code d'echange"""
        import hashlib
        return hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:10].upper()

    def enroll_member(self, data):
        """Inscrit un nouveau membre"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            email = data.get('email', '')
            name = data.get('name', '')
            if not email:
                return {'error': 'Email requis'}

            # Verifier si existe
            cursor.execute('SELECT id FROM loyalty_members WHERE customer_email = ?', (email,))
            if cursor.fetchone():
                return {'error': 'Membre deja inscrit'}

            referral_code = self._generate_referral_code(name or email.split('@')[0])

            # Bonus parrainage
            referred_by = None
            bonus_points = 100  # Points de bienvenue
            if data.get('referral_code'):
                cursor.execute('SELECT id FROM loyalty_members WHERE referral_code = ?', (data.get('referral_code'),))
                referrer = cursor.fetchone()
                if referrer:
                    referred_by = referrer[0]
                    bonus_points = 200  # Bonus parrainage

            cursor.execute('''INSERT INTO loyalty_members (customer_id, customer_email, customer_name, phone, points_balance, points_earned_total, referral_code, referred_by, birthday)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data.get('customer_id'), email, name, data.get('phone'), bonus_points, bonus_points,
                 referral_code, referred_by, data.get('birthday')))

            member_id = cursor.lastrowid

            # Transaction points bienvenue
            cursor.execute('''INSERT INTO loyalty_transactions (member_id, type, points, description)
                VALUES (?, 'earn', ?, ?)''',
                (member_id, bonus_points, 'Points de bienvenue' if not referred_by else 'Bonus parrainage'))

            # Bonus au parrain
            if referred_by:
                cursor.execute('UPDATE loyalty_members SET points_balance = points_balance + 150, points_earned_total = points_earned_total + 150 WHERE id = ?', (referred_by,))
                cursor.execute('''INSERT INTO loyalty_transactions (member_id, type, points, description)
                    VALUES (?, 'earn', 150, ?)''', (referred_by, f'Parrainage de {name or email}'))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'member_id': member_id,
                'referral_code': referral_code,
                'points': bonus_points,
                'message': 'Bienvenue au programme de fidelite!'
            }
        except Exception as e:
            return {'error': str(e)}

    def earn_points(self, member_id, data):
        """Ajoute des points pour un achat"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT tier, status FROM loyalty_members WHERE id = ?', (member_id,))
            member = cursor.fetchone()
            if not member:
                return {'error': 'Membre non trouve'}
            if member[1] != 'active':
                return {'error': 'Membre inactif'}

            order_amount = data.get('amount', 0)
            order_id = data.get('order_id')

            # Calculer points (1$ = 1 point par defaut)
            base_points = int(order_amount)

            # Multiplicateur selon tier
            cursor.execute('SELECT points_multiplier FROM loyalty_tiers WHERE name = ?', (member[0],))
            tier = cursor.fetchone()
            multiplier = tier[0] if tier else 1.0

            # Verifier promotions actives
            now = datetime.now().isoformat()
            cursor.execute('''SELECT value FROM loyalty_promotions
                WHERE promo_type = 'multiplier' AND is_active = 1
                AND (valid_from IS NULL OR valid_from <= ?) AND (valid_until IS NULL OR valid_until >= ?)''', (now, now))
            promo = cursor.fetchone()
            if promo:
                multiplier *= promo[0]

            points = int(base_points * multiplier)

            # Ajouter points
            cursor.execute('''UPDATE loyalty_members SET
                points_balance = points_balance + ?,
                points_earned_total = points_earned_total + ?,
                tier_points = tier_points + ?,
                last_activity = ?
                WHERE id = ?''', (points, points, points, now, member_id))

            cursor.execute('''INSERT INTO loyalty_transactions (member_id, type, points, description, order_id, order_amount)
                VALUES (?, 'earn', ?, ?, ?, ?)''',
                (member_id, points, f'Achat #{order_id}' if order_id else 'Achat', order_id, order_amount))

            conn.commit()

            # Verifier upgrade tier
            self._check_tier_upgrade(member_id, conn)

            conn.close()

            return {
                'success': True,
                'points_earned': points,
                'multiplier': multiplier,
                'message': f'{points} points gagnes!'
            }
        except Exception as e:
            return {'error': str(e)}

    def _check_tier_upgrade(self, member_id, conn=None):
        """Verifie et met a jour le tier"""
        try:
            close_conn = False
            if not conn:
                conn = get_db()
                close_conn = True

            cursor = conn.cursor()
            cursor.execute('SELECT tier_points, tier FROM loyalty_members WHERE id = ?', (member_id,))
            member = cursor.fetchone()
            if not member:
                return

            cursor.execute('SELECT name FROM loyalty_tiers WHERE min_points <= ? ORDER BY min_points DESC LIMIT 1', (member[0],))
            new_tier = cursor.fetchone()

            if new_tier and new_tier[0] != member[1]:
                cursor.execute('UPDATE loyalty_members SET tier = ? WHERE id = ?', (new_tier[0], member_id))
                conn.commit()

            if close_conn:
                conn.close()
        except:
            pass

    def redeem_reward(self, member_id, reward_id):
        """Echange points contre recompense"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            # Verifier membre
            cursor.execute('SELECT points_balance, tier, status FROM loyalty_members WHERE id = ?', (member_id,))
            member = cursor.fetchone()
            if not member:
                return {'error': 'Membre non trouve'}
            if member[2] != 'active':
                return {'error': 'Membre inactif'}

            # Verifier recompense
            cursor.execute('SELECT name, points_cost, reward_type, reward_value, reward_code, stock, tier_required, is_active FROM loyalty_rewards WHERE id = ?', (reward_id,))
            reward = cursor.fetchone()
            if not reward:
                return {'error': 'Recompense non trouvee'}
            if not reward[7]:
                return {'error': 'Recompense inactive'}
            if reward[5] == 0:
                return {'error': 'Stock epuise'}
            if member[0] < reward[1]:
                return {'error': f'Points insuffisants ({member[0]}/{reward[1]})'}

            # Verifier tier requis
            if reward[6]:
                tier_order = ['bronze', 'silver', 'gold', 'platinum', 'diamond']
                member_tier_idx = tier_order.index(member[1]) if member[1] in tier_order else 0
                required_tier_idx = tier_order.index(reward[6]) if reward[6] in tier_order else 0
                if member_tier_idx < required_tier_idx:
                    return {'error': f'Tier {reward[6]} requis'}

            redemption_code = self._generate_redemption_code()
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()

            # Deduire points
            cursor.execute('''UPDATE loyalty_members SET
                points_balance = points_balance - ?,
                points_redeemed_total = points_redeemed_total + ?,
                last_activity = ?
                WHERE id = ?''', (reward[1], reward[1], datetime.now().isoformat(), member_id))

            # Creer echange
            cursor.execute('''INSERT INTO loyalty_redemptions (member_id, reward_id, points_spent, redemption_code, expires_at)
                VALUES (?, ?, ?, ?, ?)''', (member_id, reward_id, reward[1], redemption_code, expires_at))

            redemption_id = cursor.lastrowid

            # Transaction
            cursor.execute('''INSERT INTO loyalty_transactions (member_id, type, points, description)
                VALUES (?, 'redeem', ?, ?)''', (member_id, -reward[1], f'Echange: {reward[0]}'))

            # Diminuer stock
            if reward[5] > 0:
                cursor.execute('UPDATE loyalty_rewards SET stock = stock - 1 WHERE id = ?', (reward_id,))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'redemption_id': redemption_id,
                'redemption_code': redemption_code,
                'reward': reward[0],
                'reward_type': reward[2],
                'reward_value': reward[3],
                'expires_at': expires_at,
                'message': f'Recompense "{reward[0]}" obtenue!'
            }
        except Exception as e:
            return {'error': str(e)}

    def use_redemption(self, redemption_code):
        """Utilise un code d'echange"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''SELECT r.id, r.status, r.expires_at, rw.name, rw.reward_type, rw.reward_value, rw.reward_code
                FROM loyalty_redemptions r JOIN loyalty_rewards rw ON r.reward_id = rw.id
                WHERE r.redemption_code = ?''', (redemption_code,))
            redemption = cursor.fetchone()

            if not redemption:
                return {'error': 'Code invalide'}
            if redemption[1] == 'used':
                return {'error': 'Code deja utilise'}
            if redemption[2] and redemption[2] < datetime.now().isoformat():
                return {'error': 'Code expire'}

            cursor.execute('UPDATE loyalty_redemptions SET status = "used", used_at = ? WHERE id = ?',
                (datetime.now().isoformat(), redemption[0]))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'reward': redemption[3],
                'type': redemption[4],
                'value': redemption[5],
                'code': redemption[6]
            }
        except Exception as e:
            return {'error': str(e)}

    def get_member(self, member_id=None, email=None):
        """Recupere un membre"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            if member_id:
                cursor.execute('''SELECT id, customer_email, customer_name, phone, points_balance, points_earned_total, points_redeemed_total, tier, tier_points, referral_code, join_date, last_activity, status
                    FROM loyalty_members WHERE id = ?''', (member_id,))
            elif email:
                cursor.execute('''SELECT id, customer_email, customer_name, phone, points_balance, points_earned_total, points_redeemed_total, tier, tier_points, referral_code, join_date, last_activity, status
                    FROM loyalty_members WHERE customer_email = ?''', (email,))
            else:
                return {'error': 'ID ou email requis'}

            m = cursor.fetchone()
            conn.close()

            if not m:
                return {'error': 'Membre non trouve'}

            return {
                'id': m[0], 'email': m[1], 'name': m[2], 'phone': m[3],
                'points_balance': m[4], 'points_earned': m[5], 'points_redeemed': m[6],
                'tier': m[7], 'tier_points': m[8], 'referral_code': m[9],
                'join_date': m[10], 'last_activity': m[11], 'status': m[12]
            }
        except Exception as e:
            return {'error': str(e)}

    def get_members(self, tier=None, status='active', limit=50):
        """Liste les membres"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, customer_email, customer_name, points_balance, tier, tier_points, last_activity, status FROM loyalty_members WHERE 1=1'
            params = []

            if tier:
                query += ' AND tier = ?'
                params.append(tier)
            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY points_balance DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'email': r[1], 'name': r[2], 'points': r[3], 'tier': r[4], 'tier_points': r[5], 'last_activity': r[6], 'status': r[7]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_transactions(self, member_id, trans_type=None, limit=50):
        """Liste les transactions d'un membre"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, type, points, description, order_id, order_amount, created_at FROM loyalty_transactions WHERE member_id = ?'
            params = [member_id]

            if trans_type:
                query += ' AND type = ?'
                params.append(trans_type)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'type': r[1], 'points': r[2], 'description': r[3], 'order_id': r[4], 'amount': r[5], 'date': r[6]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def create_reward(self, data):
        """Cree une recompense"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO loyalty_rewards (name, description, points_cost, reward_type, reward_value, reward_code, stock, tier_required, valid_from, valid_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data.get('name'), data.get('description'), data.get('points_cost', 100),
                 data.get('type', 'discount'), data.get('value'), data.get('code'),
                 data.get('stock', -1), data.get('tier_required'), data.get('valid_from'), data.get('valid_until')))

            reward_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'reward_id': reward_id}
        except Exception as e:
            return {'error': str(e)}

    def get_rewards(self, is_active=True, tier=None):
        """Liste les recompenses"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, name, description, points_cost, reward_type, reward_value, stock, tier_required, is_active FROM loyalty_rewards WHERE 1=1'
            params = []

            if is_active is not None:
                query += ' AND is_active = ?'
                params.append(1 if is_active else 0)

            query += ' ORDER BY points_cost ASC'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            rewards = [{'id': r[0], 'name': r[1], 'description': r[2], 'points': r[3], 'type': r[4], 'value': r[5], 'stock': r[6], 'tier_required': r[7], 'active': bool(r[8])} for r in rows]

            # Filtrer par tier si specifie
            if tier:
                tier_order = ['bronze', 'silver', 'gold', 'platinum', 'diamond']
                tier_idx = tier_order.index(tier) if tier in tier_order else 0
                rewards = [r for r in rewards if not r['tier_required'] or tier_order.index(r['tier_required']) <= tier_idx]

            return rewards
        except Exception as e:
            return {'error': str(e)}

    def create_tier(self, data):
        """Cree un niveau de fidelite"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO loyalty_tiers (name, min_points, points_multiplier, benefits, badge_color)
                VALUES (?, ?, ?, ?, ?)''',
                (data.get('name'), data.get('min_points', 0), data.get('multiplier', 1.0),
                 data.get('benefits'), data.get('color', '#CD7F32')))

            tier_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'tier_id': tier_id}
        except Exception as e:
            return {'error': str(e)}

    def get_tiers(self):
        """Liste les niveaux"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, min_points, points_multiplier, benefits, badge_color FROM loyalty_tiers ORDER BY min_points')
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'name': r[1], 'min_points': r[2], 'multiplier': r[3], 'benefits': r[4], 'color': r[5]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def setup_default_tiers(self):
        """Configure les niveaux par defaut"""
        try:
            tiers = [
                {'name': 'bronze', 'min_points': 0, 'multiplier': 1.0, 'benefits': '1 point par dollar', 'color': '#CD7F32'},
                {'name': 'silver', 'min_points': 500, 'multiplier': 1.25, 'benefits': '1.25x points, livraison gratuite', 'color': '#C0C0C0'},
                {'name': 'gold', 'min_points': 2000, 'multiplier': 1.5, 'benefits': '1.5x points, acces VIP, offres exclusives', 'color': '#FFD700'},
                {'name': 'platinum', 'min_points': 5000, 'multiplier': 2.0, 'benefits': '2x points, support prioritaire, cadeaux', 'color': '#E5E4E2'},
                {'name': 'diamond', 'min_points': 15000, 'multiplier': 3.0, 'benefits': '3x points, concierge dedie, evenements prives', 'color': '#B9F2FF'}
            ]
            for t in tiers:
                self.create_tier(t)
            return {'success': True, 'message': '5 niveaux crees'}
        except Exception as e:
            return {'error': str(e)}

    def setup_default_rewards(self):
        """Configure les recompenses par defaut"""
        try:
            rewards = [
                {'name': '5$ de rabais', 'description': 'Rabais de 5$ sur prochain achat', 'points_cost': 100, 'type': 'discount', 'value': 5},
                {'name': '10$ de rabais', 'description': 'Rabais de 10$ sur prochain achat', 'points_cost': 200, 'type': 'discount', 'value': 10},
                {'name': '25$ de rabais', 'description': 'Rabais de 25$ sur prochain achat', 'points_cost': 450, 'type': 'discount', 'value': 25},
                {'name': 'Livraison gratuite', 'description': 'Livraison gratuite sur commande', 'points_cost': 150, 'type': 'free_shipping', 'value': 1},
                {'name': '10% de rabais', 'description': '10% sur tout le panier', 'points_cost': 300, 'type': 'percent', 'value': 10, 'tier_required': 'silver'},
                {'name': '20% de rabais', 'description': '20% sur tout le panier', 'points_cost': 600, 'type': 'percent', 'value': 20, 'tier_required': 'gold'},
                {'name': 'Cadeau surprise', 'description': 'Un cadeau exclusif', 'points_cost': 1000, 'type': 'gift', 'value': 1, 'tier_required': 'platinum'}
            ]
            for r in rewards:
                self.create_reward(r)
            return {'success': True, 'message': '7 recompenses creees'}
        except Exception as e:
            return {'error': str(e)}

    def create_promotion(self, data):
        """Cree une promotion bonus"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO loyalty_promotions (name, description, promo_type, value, conditions, valid_from, valid_until)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (data.get('name'), data.get('description'), data.get('type', 'multiplier'),
                 data.get('value', 2.0), data.get('conditions'), data.get('valid_from'), data.get('valid_until')))

            promo_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {'success': True, 'promotion_id': promo_id}
        except Exception as e:
            return {'error': str(e)}

    def get_promotions(self, active_only=True):
        """Liste les promotions"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            query = 'SELECT id, name, description, promo_type, value, valid_from, valid_until, is_active, usage_count FROM loyalty_promotions'
            if active_only:
                now = datetime.now().isoformat()
                query += f' WHERE is_active = 1 AND (valid_from IS NULL OR valid_from <= "{now}") AND (valid_until IS NULL OR valid_until >= "{now}")'

            query += ' ORDER BY created_at DESC'

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            return [{'id': r[0], 'name': r[1], 'description': r[2], 'type': r[3], 'value': r[4], 'valid_from': r[5], 'valid_until': r[6], 'active': bool(r[7]), 'usage': r[8]} for r in rows]
        except Exception as e:
            return {'error': str(e)}

    def get_member_dashboard(self, member_id):
        """Dashboard membre avec stats"""
        try:
            member = self.get_member(member_id=member_id)
            if 'error' in member:
                return member

            transactions = self.get_transactions(member_id, limit=10)
            rewards = self.get_rewards(tier=member.get('tier'))

            # Prochains niveaux
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT name, min_points FROM loyalty_tiers WHERE min_points > ? ORDER BY min_points LIMIT 1', (member.get('tier_points', 0),))
            next_tier = cursor.fetchone()

            # Redemptions recentes
            cursor.execute('''SELECT r.id, rw.name, r.redemption_code, r.status, r.created_at
                FROM loyalty_redemptions r JOIN loyalty_rewards rw ON r.reward_id = rw.id
                WHERE r.member_id = ? ORDER BY r.created_at DESC LIMIT 5''', (member_id,))
            redemptions = [{'id': r[0], 'reward': r[1], 'code': r[2], 'status': r[3], 'date': r[4]} for r in cursor.fetchall()]

            conn.close()

            return {
                'member': member,
                'next_tier': {'name': next_tier[0], 'points_needed': next_tier[1] - member.get('tier_points', 0)} if next_tier else None,
                'recent_transactions': transactions if isinstance(transactions, list) else [],
                'recent_redemptions': redemptions,
                'available_rewards': len(rewards) if isinstance(rewards, list) else 0
            }
        except Exception as e:
            return {'error': str(e)}

    def adjust_points(self, member_id, points, reason='Ajustement manuel'):
        """Ajuste les points manuellement"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM loyalty_members WHERE id = ?', (member_id,))
            if not cursor.fetchone():
                return {'error': 'Membre non trouve'}

            trans_type = 'earn' if points > 0 else 'redeem'
            cursor.execute('UPDATE loyalty_members SET points_balance = points_balance + ? WHERE id = ?', (points, member_id))
            cursor.execute('''INSERT INTO loyalty_transactions (member_id, type, points, description)
                VALUES (?, ?, ?, ?)''', (member_id, trans_type, points, reason))

            conn.commit()
            conn.close()

            return {'success': True, 'points_adjusted': points}
        except Exception as e:
            return {'error': str(e)}

    def get_stats(self, days=30):
        """Statistiques programme fidelite"""
        try:
            self.init_db()
            conn = get_db()
            cursor = conn.cursor()
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('SELECT COUNT(*) FROM loyalty_members WHERE status = "active"')
            active_members = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM loyalty_members WHERE join_date >= ?', (start,))
            new_members = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(points) FROM loyalty_transactions WHERE type = "earn" AND created_at >= ?', (start,))
            points_earned = cursor.fetchone()[0] or 0

            cursor.execute('SELECT SUM(ABS(points)) FROM loyalty_transactions WHERE type = "redeem" AND created_at >= ?', (start,))
            points_redeemed = cursor.fetchone()[0] or 0

            cursor.execute('SELECT SUM(points_balance) FROM loyalty_members')
            total_points = cursor.fetchone()[0] or 0

            cursor.execute('SELECT COUNT(*) FROM loyalty_redemptions WHERE created_at >= ?', (start,))
            redemptions = cursor.fetchone()[0]

            # Par tier
            cursor.execute('SELECT tier, COUNT(*) FROM loyalty_members WHERE status = "active" GROUP BY tier')
            by_tier = {r[0]: r[1] for r in cursor.fetchall()}

            # Top membres
            cursor.execute('SELECT customer_name, customer_email, points_balance, tier FROM loyalty_members WHERE status = "active" ORDER BY points_balance DESC LIMIT 5')
            top = [{'name': r[0] or r[1], 'points': r[2], 'tier': r[3]} for r in cursor.fetchall()]

            conn.close()

            return {
                'active_members': active_members,
                'new_members': new_members,
                'points_earned': points_earned,
                'points_redeemed': points_redeemed,
                'total_points_outstanding': total_points,
                'redemptions': redemptions,
                'members_by_tier': by_tier,
                'top_members': top
            }
        except Exception as e:
            return {'error': str(e)}


# ============================================================
# 60. KeywordClusterAgent - Keyword Clustering & Topic Grouping
# ============================================================
class KeywordClusterAgent:
    """Groups keywords into semantic clusters using AI for better content strategy"""

    def cluster_keywords(self, site_id):
        """Fetch existing keywords for a site and cluster them by topic"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Get keywords from keyword_research table
            cursor.execute('''
                SELECT keyword, search_volume, difficulty, intent
                FROM keyword_research
                WHERE site_id = ? ORDER BY search_volume DESC LIMIT 200
            ''', (str(site_id),))
            keywords = [{'keyword': r[0], 'volume': r[1], 'difficulty': r[2], 'intent': r[3]} for r in cursor.fetchall()]

            if not keywords:
                conn.close()
                return {'error': 'No keywords found for this site', 'clusters': []}

            kw_list = ', '.join([k['keyword'] for k in keywords[:100]])

            prompt = (
                "You are an SEO keyword clustering expert.\n"
                "Group these keywords into semantic topic clusters. Each cluster should represent a distinct topic/intent.\n\n"
                f"Keywords: {kw_list}\n\n"
                "Return ONLY valid JSON (no markdown, no explanation):\n"
                '{"clusters": [{"name": "cluster topic name", "keywords": ["keyword1", "keyword2"], '
                '"intent": "informational|transactional|navigational", "priority": 5, '
                '"suggested_pillar": "suggested pillar page title"}]}'
            )

            result = call_ai(prompt, max_tokens=4000)
            import json as _json
            import re as _re

            # Strip think tags from DeepSeek R1
            result = _re.sub(r'<think>.*?</think>', '', result, flags=_re.DOTALL).strip()

            # Extract JSON
            json_match = _re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = _json.loads(json_match.group())
            else:
                conn.close()
                return {'error': 'AI did not return valid JSON', 'raw': result[:500]}

            # Enrich clusters with volume/difficulty data
            kw_map = {k['keyword']: k for k in keywords}
            for cluster in data.get('clusters', []):
                enriched_kws = []
                for kw_name in cluster.get('keywords', []):
                    if kw_name in kw_map:
                        enriched_kws.append(kw_map[kw_name])
                    else:
                        enriched_kws.append({'keyword': kw_name, 'volume': 0, 'difficulty': 0, 'intent': cluster.get('intent', '')})
                cluster['keywords'] = enriched_kws
                cluster['keyword_count'] = len(enriched_kws)

            # Save to DB
            for cluster in data.get('clusters', []):
                cursor.execute('''
                    INSERT INTO keyword_clusters (site_id, cluster_name, keywords_json, priority, article_count, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (str(site_id), cluster['name'], _json.dumps(cluster['keywords']),
                      cluster.get('priority', 5), cluster.get('keyword_count', 0)))

            conn.commit()
            conn.close()

            return {
                'site_id': site_id,
                'total_keywords': len(keywords),
                'clusters': data.get('clusters', []),
                'cluster_count': len(data.get('clusters', []))
            }

        except Exception as e:
            return {'error': str(e)}

    def get_clusters(self, site_id):
        """Retrieve saved clusters for a site"""
        try:
            import json as _json
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cluster_name, keywords_json, priority, article_count, created_at
                FROM keyword_clusters WHERE site_id = ? ORDER BY priority DESC
            ''', (str(site_id),))
            clusters = []
            for r in cursor.fetchall():
                clusters.append({
                    'id': r[0], 'name': r[1],
                    'keywords': _json.loads(r[2]) if r[2] else [],
                    'priority': r[3], 'article_count': r[4], 'created_at': r[5]
                })
            conn.close()
            return {'clusters': clusters, 'count': len(clusters)}
        except Exception as e:
            return {'error': str(e)}


# ============================================================
# 61. TopicalMapAgent - Topical Map / Content Architecture
# ============================================================
class TopicalMapAgent:
    """Generates hierarchical topical maps: Pillar > Cluster > Support articles"""

    def generate_map(self, site_id, seed_topic):
        """Generate a complete topical map from a seed topic"""
        try:
            import json as _json
            import re as _re

            prompt = (
                "You are an SEO content strategist. Generate a complete topical map for the topic: "
                f'"{seed_topic}"\n\n'
                "The topical map should follow a hub-and-spoke model:\n"
                "- 1 Pillar page (comprehensive, 3000+ word guide)\n"
                "- 4-6 Topic clusters (subtopics)\n"
                "- 3-5 Supporting articles per cluster\n\n"
                "Return ONLY valid JSON (no markdown):\n"
                '{"pillar": {"title": "Ultimate Guide to X", "keyword": "main keyword", "word_count": 3000, "type": "pillar"}, '
                '"clusters": [{"topic": "cluster topic", "keyword": "cluster keyword", '
                '"articles": [{"title": "article title", "keyword": "target keyword", '
                '"type": "how-to", "word_count": 1500, "priority": "high", '
                '"internal_link_to": "pillar title"}]}]}'
            )

            result = call_ai(prompt, max_tokens=4000)
            result = _re.sub(r'<think>.*?</think>', '', result, flags=_re.DOTALL).strip()

            json_match = _re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = _json.loads(json_match.group())
            else:
                return {'error': 'AI did not return valid JSON', 'raw': result[:500]}

            # Count totals
            pillar_count = 1
            article_count = sum(len(c.get('articles', [])) for c in data.get('clusters', []))

            # Save to DB
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO topical_maps (site_id, seed_topic, map_json, pillar_count, article_count, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (str(site_id), seed_topic, _json.dumps(data), pillar_count, article_count))
            map_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {
                'id': map_id,
                'site_id': site_id,
                'seed_topic': seed_topic,
                'pillar': data.get('pillar', {}),
                'clusters': data.get('clusters', []),
                'pillar_count': pillar_count,
                'total_articles': article_count
            }

        except Exception as e:
            return {'error': str(e)}

    def get_maps(self, site_id):
        """Retrieve saved topical maps for a site"""
        try:
            import json as _json
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, seed_topic, map_json, pillar_count, article_count, created_at
                FROM topical_maps WHERE site_id = ? ORDER BY created_at DESC
            ''', (str(site_id),))
            maps = []
            for r in cursor.fetchall():
                maps.append({
                    'id': r[0], 'seed_topic': r[1],
                    'map': _json.loads(r[2]) if r[2] else {},
                    'pillar_count': r[3], 'article_count': r[4], 'created_at': r[5]
                })
            conn.close()
            return {'maps': maps, 'count': len(maps)}
        except Exception as e:
            return {'error': str(e)}


# ============================================================
# 62. ContentScoringAgent - Real-time Content Quality Scoring
# ============================================================
class ContentScoringAgent:
    """Scores content quality 0-100 with detailed breakdown and recommendations"""

    def score_content(self, content, target_keyword, site_id=None):
        """Analyze content and return a quality score with breakdown"""
        try:
            import json as _json
            import re as _re

            # Local analysis (no AI needed for speed)
            word_count = len(content.split())
            sentences = [s.strip() for s in _re.split(r'[.!?]+', content) if s.strip()]
            avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

            # Keyword density
            kw_lower = target_keyword.lower()
            content_lower = content.lower()
            kw_count = content_lower.count(kw_lower)
            kw_density = (kw_count / max(word_count, 1)) * 100

            # Heading analysis (HTML + Markdown)
            h1_count = len(_re.findall(r'<h1[^>]*>', content, _re.IGNORECASE)) + len(_re.findall(r'^# ', content, _re.MULTILINE))
            h2_count = len(_re.findall(r'<h2[^>]*>', content, _re.IGNORECASE)) + len(_re.findall(r'^## ', content, _re.MULTILINE))
            h3_count = len(_re.findall(r'<h3[^>]*>', content, _re.IGNORECASE)) + len(_re.findall(r'^### ', content, _re.MULTILINE))

            # Structure checks
            has_faq = bool(_re.search(r'(FAQ|question|Q&A|frequently asked)', content, _re.IGNORECASE))
            has_list = bool(_re.search(r'(<[uo]l|^[\-\*\d]+\.?\s)', content, _re.MULTILINE))
            has_images = bool(_re.search(r'(<img|!\[)', content))
            has_internal_links = bool(_re.search(r'<a[^>]*href=', content, _re.IGNORECASE))
            has_meta = bool(_re.search(r'<meta|meta description|title tag', content, _re.IGNORECASE))

            # Calculate component scores
            scores = {}

            # Word count score (optimal 1500-3000)
            if word_count >= 1500:
                scores['word_count'] = min(100, 70 + (word_count - 1500) / 50)
            elif word_count >= 800:
                scores['word_count'] = 50 + (word_count - 800) / 14
            elif word_count >= 300:
                scores['word_count'] = 20 + (word_count - 300) / 16.7
            else:
                scores['word_count'] = max(5, word_count / 15)

            # Keyword density (optimal 1-3%)
            if 1.0 <= kw_density <= 3.0:
                scores['keyword_density'] = 95
            elif 0.5 <= kw_density < 1.0 or 3.0 < kw_density <= 4.0:
                scores['keyword_density'] = 70
            elif kw_density > 4.0:
                scores['keyword_density'] = 30
            else:
                scores['keyword_density'] = max(10, kw_density * 60)

            # Heading structure
            heading_score = 0
            if h1_count == 1:
                heading_score += 30
            elif h1_count > 1:
                heading_score += 10
            if h2_count >= 3:
                heading_score += 40
            elif h2_count >= 1:
                heading_score += 20
            if h3_count >= 2:
                heading_score += 30
            elif h3_count >= 1:
                heading_score += 15
            scores['headings'] = min(100, heading_score)

            # Readability (avg sentence length optimal 15-20)
            if 12 <= avg_sentence_len <= 22:
                scores['readability'] = 90
            elif 8 <= avg_sentence_len < 12 or 22 < avg_sentence_len <= 28:
                scores['readability'] = 65
            else:
                scores['readability'] = 35

            # Content features
            feature_score = 0
            if has_faq:
                feature_score += 20
            if has_list:
                feature_score += 20
            if has_images:
                feature_score += 25
            if has_internal_links:
                feature_score += 20
            if has_meta:
                feature_score += 15
            scores['content_features'] = min(100, feature_score)

            # Overall score (weighted)
            overall = int(
                scores['word_count'] * 0.20 +
                scores['keyword_density'] * 0.25 +
                scores['headings'] * 0.20 +
                scores['readability'] * 0.15 +
                scores['content_features'] * 0.20
            )

            # Generate recommendations
            recommendations = []
            if scores['word_count'] < 70:
                recommendations.append(f'Increase content length. Currently {word_count} words, aim for 1500+.')
            if kw_density < 1.0:
                recommendations.append(f'Add more mentions of "{target_keyword}". Current density: {kw_density:.1f}%.')
            if kw_density > 3.0:
                recommendations.append(f'Reduce keyword stuffing. Density is {kw_density:.1f}%, aim for 1-3%.')
            if h1_count == 0:
                recommendations.append('Add an H1 heading with your target keyword.')
            if h2_count < 3:
                recommendations.append(f'Add more H2 subheadings. Currently {h2_count}, aim for 3+.')
            if not has_faq:
                recommendations.append('Add a FAQ section to capture featured snippets.')
            if not has_list:
                recommendations.append('Add bullet points or numbered lists for scannability.')
            if not has_images:
                recommendations.append('Add images with descriptive alt text.')
            if not has_internal_links:
                recommendations.append('Add internal links to related content.')
            if scores['readability'] < 60:
                recommendations.append(f'Simplify sentences. Average length is {avg_sentence_len:.0f} words.')

            result = {
                'score': overall,
                'grade': 'A' if overall >= 85 else 'B' if overall >= 70 else 'C' if overall >= 55 else 'D' if overall >= 40 else 'F',
                'word_count': word_count,
                'keyword': target_keyword,
                'keyword_density': round(kw_density, 2),
                'breakdown': {k: int(v) for k, v in scores.items()},
                'recommendations': recommendations,
                'details': {
                    'h1_count': h1_count, 'h2_count': h2_count, 'h3_count': h3_count,
                    'has_faq': has_faq, 'has_lists': has_list,
                    'has_images': has_images, 'has_internal_links': has_internal_links,
                    'sentence_count': len(sentences), 'avg_sentence_length': round(avg_sentence_len, 1)
                }
            }

            # Save to DB if site_id provided
            if site_id:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO content_scores (site_id, content_id, keyword, score, breakdown_json, recommendations_json, created_at) '
                    'VALUES (?, ?, ?, ?, ?, ?, datetime(\'now\'))',
                    (str(site_id), '', target_keyword, overall,
                     _json.dumps(result['breakdown']), _json.dumps(recommendations))
                )
                conn.commit()
                conn.close()

            return result

        except Exception as e:
            return {'error': str(e), 'score': 0}

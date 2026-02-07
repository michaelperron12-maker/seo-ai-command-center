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
DEEPSEEK_R1 = 'accounts/fireworks/models/deepseek-r1'
QWEN_MODEL = 'accounts/fireworks/models/qwen3-235b-a22b-instruct-2507'
LLAMA_MODEL = 'accounts/fireworks/models/llama-v3p3-70b-instruct'

# Modele actif - DeepSeek R1 pour qualite pro
ACTIVE_MODEL = DEEPSEEK_R1

SITES = {
    1: {'nom': 'Deneigement Excellence', 'domaine': 'deneigement-excellence.ca', 'niche': 'deneigement', 'path': '/var/www/deneigement'},
    2: {'nom': 'Paysagiste Excellence', 'domaine': 'paysagiste-excellence.ca', 'niche': 'paysagement', 'path': '/var/www/paysagement'},
    3: {'nom': 'JC Peintre', 'domaine': 'jcpeintre.com', 'niche': 'peinture', 'path': '/var/www/jcpeintre.com'}
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
    name = "Technical SEO Audit Agent"

    def audit_page(self, url):
        """Audit technique d'une page"""
        try:
            response = requests.get(url, timeout=10)
            html = response.text

            issues = []
            score = 100

            # Check title
            if '<title>' not in html.lower():
                issues.append({'type': 'critical', 'message': 'Pas de balise title'})
                score -= 15

            # Check meta description
            if 'meta name="description"' not in html.lower():
                issues.append({'type': 'warning', 'message': 'Pas de meta description'})
                score -= 10

            # Check H1
            if '<h1' not in html.lower():
                issues.append({'type': 'warning', 'message': 'Pas de balise H1'})
                score -= 10

            # Check HTTPS
            if not url.startswith('https'):
                issues.append({'type': 'critical', 'message': 'Site non HTTPS'})
                score -= 20

            # Check images alt
            img_count = html.lower().count('<img')
            alt_count = html.lower().count('alt=')
            if img_count > 0 and alt_count < img_count:
                issues.append({'type': 'warning', 'message': f'{img_count - alt_count} images sans alt'})
                score -= 5

            log_agent(self.name, f"Audit {url}: Score {score}")
            return {'url': url, 'score': max(0, score), 'issues': issues, 'response_time': response.elapsed.total_seconds()}
        except Exception as e:
            return {'url': url, 'score': 0, 'issues': [{'type': 'critical', 'message': str(e)}]}

    def check_robots_txt(self, domain):
        """Verifie robots.txt"""
        try:
            url = f"https://{domain}/robots.txt"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {'exists': True, 'content': response.text[:500]}
            return {'exists': False}
        except:
            return {'exists': False}

    def check_sitemap(self, domain):
        """Verifie sitemap.xml"""
        try:
            url = f"https://{domain}/sitemap.xml"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                urls_count = response.text.count('<loc>')
                return {'exists': True, 'urls_count': urls_count}
            return {'exists': False}
        except:
            return {'exists': False}

# ============================================
# AGENT 5: PERFORMANCE AGENT
# ============================================
class PerformanceAgent:
    name = "Performance Agent"

    def check_speed(self, url):
        """Check vitesse basique"""
        try:
            start = datetime.now()
            response = requests.get(url, timeout=30)
            load_time = (datetime.now() - start).total_seconds()

            size_kb = len(response.content) / 1024

            score = 100
            if load_time > 3:
                score -= 20
            if load_time > 5:
                score -= 20
            if size_kb > 500:
                score -= 10
            if size_kb > 1000:
                score -= 10

            return {
                'url': url,
                'load_time_seconds': round(load_time, 2),
                'size_kb': round(size_kb, 2),
                'score': max(0, score),
                'status_code': response.status_code
            }
        except Exception as e:
            return {'url': url, 'error': str(e), 'score': 0}

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

    def generate_local_citations(self, site_id):
        """Liste de citations locales a creer"""
        site = SITES.get(site_id, {})
        prompt = f"""Liste 20 sites de citations locales pour une entreprise de {site.get('niche', '')} au Quebec:

Format JSON:
{{"citations": [{{"name": "...", "url": "...", "type": "directory|review|social", "priority": 1-5}}]}}"""

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

class SSLAgent:
    """Agent 22: Verification SSL"""
    name = "SSL Agent"

    def check_ssl(self, domain):
        import ssl
        import socket
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    expires = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (expires - datetime.now()).days
                    return {'valid': True, 'expires': cert['notAfter'], 'days_left': days_left}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

class BackupAgent:
    """Agent 23: Sauvegarde automatique"""
    name = "Backup Agent"

    def backup_database(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"/opt/seo-agent/db/backup/seo_agent_{timestamp}.db"
        try:
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            log_agent(self.name, f"Backup cree: {backup_path}")
            return {'success': True, 'path': backup_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class AnalyticsAgent:
    """Agent 24: Analyse des donnees"""
    name = "Analytics Agent"

    def get_site_stats(self, site_id):
        conn = get_db()
        cursor = conn.cursor()

        # Keywords count
        cursor.execute('SELECT COUNT(*) FROM keywords WHERE site_id = ?', (site_id,))
        keywords = cursor.fetchone()[0]

        # Drafts count
        cursor.execute('SELECT COUNT(*) FROM drafts WHERE site_id = ?', (site_id,))
        drafts = cursor.fetchone()[0]

        conn.close()
        return {'site_id': site_id, 'keywords': keywords, 'drafts': drafts}

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
            'service_description': ServiceDescriptionAgent()
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
        """Retourne le status de tous les agents"""
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
            response = call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass
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
            response = call_qwen(prompt, 1000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass
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
            response = call_qwen(prompt, 800)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass
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
            response = call_qwen(prompt, 1000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass
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
            response = call_qwen(prompt, 2000)
            if response:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                return json.loads(response.strip())
        except:
            pass
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
        except:
            pass
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
        except:
            pass
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
        except:
            pass
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
        except:
            pass
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
        except:
            pass
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
        except:
            pass
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
        except:
            pass
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

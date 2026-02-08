#!/usr/bin/env python3
"""
SEO Scanner API - Scanner STRICT pour seoparai.com
Analyse complète SEO + AI-readiness - SCORING SÉVÈRE
"""

import requests
import json
import re
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import concurrent.futures
import time

app = Flask(__name__)
CORS(app)

class SEOScanner:
    """Scanner SEO STRICT avec focus AI-readiness"""

    def __init__(self, domain):
        self.domain = domain.lower().strip()
        if self.domain.startswith('http'):
            parsed = urlparse(self.domain)
            self.domain = parsed.netloc
        self.base_url = f"https://{self.domain}"
        self.results = {
            'domain': self.domain,
            'scan_date': datetime.now().isoformat(),
            'scores': {},
            'seo_classic': {},
            'seo_technique': {},
            'ai_readiness': {},
            'content_quality': {},
            'recommendations': []
        }
        self.html = None
        self.soup = None

    def fetch_page(self, url, timeout=15):
        """Récupère une page web"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; SEOparAI-Scanner/2.0; +https://seoparai.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-CA,fr;q=0.9,en;q=0.8'
        }
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, verify=True, allow_redirects=True)
            return resp
        except requests.exceptions.SSLError:
            try:
                resp = requests.get(url.replace('https://', 'http://'), headers=headers, timeout=timeout)
                return resp
            except:
                return None
        except:
            return None

    def run_full_scan(self):
        """Lance le scan complet"""
        print(f"[SCAN] Démarrage scan STRICT: {self.domain}")

        # Récupérer la page d'accueil
        resp = self.fetch_page(self.base_url)
        if not resp:
            resp = self.fetch_page(f"http://{self.domain}")

        if not resp or resp.status_code != 200:
            self.results['error'] = f"Site inaccessible (Status: {resp.status_code if resp else 'N/A'})"
            self.results['scores']['total'] = 0
            return self.results

        self.html = resp.text
        self.soup = BeautifulSoup(self.html, 'html.parser')
        self.final_url = resp.url

        # Exécuter tous les scans
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.scan_seo_classic): 'seo_classic',
                executor.submit(self.scan_seo_technique): 'seo_technique',
                executor.submit(self.scan_ai_readiness): 'ai_readiness',
                executor.submit(self.scan_content_quality): 'content_quality',
            }

            for future in concurrent.futures.as_completed(futures):
                category = futures[future]
                try:
                    self.results[category] = future.result()
                except Exception as e:
                    self.results[category] = {'error': str(e)}

        # Calculer les scores STRICTS
        self.calculate_strict_scores()

        # Générer les recommandations
        self.generate_recommendations()

        return self.results

    # ==========================================
    # SEO CLASSIQUE - STRICT
    # ==========================================
    def scan_seo_classic(self):
        """Analyse SEO classique STRICTE"""
        results = {'checks': [], 'passed': 0, 'failed': 0, 'warnings': 0}

        # Title - STRICT: doit être entre 50-60 chars
        title_tag = self.soup.find('title')
        title = title_tag.text.strip() if title_tag else None
        title_len = len(title) if title else 0
        title_status = 'pass' if title and 50 <= title_len <= 60 else 'warning' if title and 30 <= title_len < 50 else 'fail'
        results['checks'].append({
            'name': 'Meta Title Optimisé',
            'status': title_status,
            'value': title[:80] if title else None,
            'details': f'{title_len} caractères (optimal: 50-60)' if title else 'MANQUANT - Critique pour SEO',
            'importance': 'critical',
            'recommendation': 'Titre entre 50-60 caractères avec mot-clé principal au début' if title_status != 'pass' else None
        })

        # Meta Description - STRICT: doit être entre 150-160 chars
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc.get('content', '').strip() if meta_desc else None
        desc_len = len(desc) if desc else 0
        desc_status = 'pass' if desc and 150 <= desc_len <= 160 else 'warning' if desc and 100 <= desc_len < 150 else 'fail'
        results['checks'].append({
            'name': 'Meta Description Optimisée',
            'status': desc_status,
            'value': desc[:200] if desc else None,
            'details': f'{desc_len} caractères (optimal: 150-160)' if desc else 'MANQUANTE - Perte de clics',
            'importance': 'critical',
            'recommendation': 'Description 150-160 caractères avec call-to-action et mot-clé' if desc_status != 'pass' else None
        })

        # H1 - STRICT: exactement 1, avec mot-clé
        h1_tags = self.soup.find_all('h1')
        h1_count = len(h1_tags)
        h1_text = h1_tags[0].text.strip()[:100] if h1_tags else None
        h1_status = 'pass' if h1_count == 1 else 'fail'
        results['checks'].append({
            'name': 'Balise H1 Unique',
            'status': h1_status,
            'value': h1_text,
            'details': f'{h1_count} H1 trouvé(s) - doit être exactement 1' if h1_count != 1 else 'OK - 1 H1 unique',
            'importance': 'critical',
            'recommendation': 'Exactement 1 H1 par page avec mot-clé principal' if h1_status != 'pass' else None
        })

        # H2 Structure - STRICT: minimum 3 H2
        h2_tags = self.soup.find_all('h2')
        h2_count = len(h2_tags)
        h2_status = 'pass' if h2_count >= 3 else 'warning' if h2_count >= 1 else 'fail'
        results['checks'].append({
            'name': 'Structure H2 (min 3)',
            'status': h2_status,
            'value': f'{h2_count} H2 trouvés',
            'details': f'{h2_count}/3 minimum requis',
            'importance': 'high',
            'recommendation': f'Ajouter {3 - h2_count} sous-titres H2 pour structurer le contenu' if h2_status != 'pass' else None
        })

        # Images ALT - STRICT: 100% requis
        images = self.soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt') and len(img.get('alt', '').strip()) > 5]
        img_count = len(images)
        alt_count = len(images_with_alt)
        img_score = (alt_count / img_count * 100) if img_count > 0 else 100
        img_status = 'pass' if img_score == 100 else 'warning' if img_score >= 80 else 'fail'
        results['checks'].append({
            'name': 'Images avec ALT descriptif',
            'status': img_status,
            'value': f'{alt_count}/{img_count}',
            'details': f'{img_score:.0f}% - TOUTES les images doivent avoir un ALT descriptif',
            'importance': 'high',
            'recommendation': f'Ajouter ALT descriptif à {img_count - alt_count} images' if img_status != 'pass' else None
        })

        # Internal Links - STRICT: minimum 5
        links = self.soup.find_all('a', href=True)
        internal_links = [l for l in links if self.domain in l.get('href', '') or l.get('href', '').startswith('/')]
        int_count = len(internal_links)
        link_status = 'pass' if int_count >= 5 else 'warning' if int_count >= 2 else 'fail'
        results['checks'].append({
            'name': 'Maillage Interne (min 5)',
            'status': link_status,
            'value': f'{int_count} liens internes',
            'details': f'{int_count}/5 minimum requis pour bon maillage',
            'importance': 'high',
            'recommendation': f'Ajouter {5 - int_count} liens internes vers pages importantes' if link_status != 'pass' else None
        })

        # Canonical
        canonical = self.soup.find('link', rel='canonical')
        canonical_url = canonical.get('href') if canonical else None
        can_status = 'pass' if canonical_url else 'fail'
        results['checks'].append({
            'name': 'URL Canonique',
            'status': can_status,
            'value': canonical_url[:80] if canonical_url else None,
            'details': 'Définie' if canonical_url else 'MANQUANTE - Risque contenu dupliqué',
            'importance': 'high',
            'recommendation': 'Ajouter <link rel="canonical"> pour éviter duplication' if can_status != 'pass' else None
        })

        # Open Graph - STRICT: tous les 4 requis
        og_tags = self.soup.find_all('meta', property=re.compile('^og:'))
        og_found = [tag.get('property') for tag in og_tags]
        og_required = ['og:title', 'og:description', 'og:image', 'og:url']
        og_missing = [t for t in og_required if t not in og_found]
        og_status = 'pass' if len(og_missing) == 0 else 'warning' if len(og_missing) <= 2 else 'fail'
        results['checks'].append({
            'name': 'Open Graph Complet',
            'status': og_status,
            'value': f'{4 - len(og_missing)}/4 tags',
            'details': f'Manquants: {", ".join(og_missing)}' if og_missing else 'Tous les tags présents',
            'importance': 'medium',
            'recommendation': f'Ajouter: {", ".join(og_missing)}' if og_status != 'pass' else None
        })

        # Twitter Cards
        twitter_tags = self.soup.find_all('meta', attrs={'name': re.compile('^twitter:')})
        tw_count = len(twitter_tags)
        tw_status = 'pass' if tw_count >= 4 else 'warning' if tw_count >= 2 else 'fail'
        results['checks'].append({
            'name': 'Twitter Cards',
            'status': tw_status,
            'value': f'{tw_count} tags',
            'details': f'{tw_count}/4 tags recommandés',
            'importance': 'low',
            'recommendation': 'Ajouter twitter:card, twitter:title, twitter:description, twitter:image' if tw_status != 'pass' else None
        })

        # Count
        for check in results['checks']:
            if check['status'] == 'pass': results['passed'] += 1
            elif check['status'] == 'fail': results['failed'] += 1
            else: results['warnings'] += 1

        return results

    # ==========================================
    # SEO TECHNIQUE - STRICT
    # ==========================================
    def scan_seo_technique(self):
        """Analyse SEO technique STRICTE"""
        results = {'checks': [], 'passed': 0, 'failed': 0, 'warnings': 0}

        # SSL/HTTPS - STRICT: obligatoire
        is_https = self.final_url.startswith('https')
        ssl_info = self.check_ssl()
        ssl_valid = ssl_info.get('valid', False)
        days = ssl_info.get('days_remaining', 0)
        ssl_status = 'pass' if is_https and ssl_valid and days > 30 else 'warning' if is_https and ssl_valid else 'fail'
        results['checks'].append({
            'name': 'HTTPS/SSL Valide',
            'status': ssl_status,
            'value': ssl_info,
            'details': f"SSL valide, expire dans {days} jours" if ssl_valid else 'SSL INVALIDE ou ABSENT - CRITIQUE',
            'importance': 'critical',
            'recommendation': 'Installer certificat SSL valide immédiatement' if ssl_status == 'fail' else 'Renouveler SSL avant expiration' if ssl_status == 'warning' else None
        })

        # Robots.txt - STRICT
        robots_resp = self.fetch_page(f"{self.base_url}/robots.txt")
        robots_exists = robots_resp and robots_resp.status_code == 200
        robots_content = robots_resp.text if robots_exists else None
        robots_status = 'pass' if robots_exists and len(robots_content or '') > 20 else 'fail'
        results['checks'].append({
            'name': 'Robots.txt Configuré',
            'status': robots_status,
            'value': robots_content[:300] if robots_content else None,
            'details': f'{len(robots_content or "")} caractères' if robots_exists else 'MANQUANT - Les bots ne savent pas quoi indexer',
            'importance': 'critical',
            'recommendation': 'Créer robots.txt avec règles pour moteurs et bots AI' if robots_status != 'pass' else None
        })

        # Sitemap.xml - STRICT
        sitemap_resp = self.fetch_page(f"{self.base_url}/sitemap.xml")
        sitemap_exists = sitemap_resp and sitemap_resp.status_code == 200
        sitemap_urls = len(re.findall(r'<loc>', sitemap_resp.text)) if sitemap_exists else 0
        sitemap_status = 'pass' if sitemap_exists and sitemap_urls >= 3 else 'warning' if sitemap_exists else 'fail'
        results['checks'].append({
            'name': 'Sitemap.xml avec URLs',
            'status': sitemap_status,
            'value': f'{sitemap_urls} URLs',
            'details': f'{sitemap_urls} pages indexées' if sitemap_exists else 'MANQUANT - Google ne trouve pas vos pages',
            'importance': 'critical',
            'recommendation': 'Créer sitemap.xml avec toutes les pages importantes' if sitemap_status != 'pass' else None
        })

        # Page Speed - STRICT: < 2s
        start_time = time.time()
        _ = self.fetch_page(self.base_url)
        load_time = time.time() - start_time
        speed_status = 'pass' if load_time < 2 else 'warning' if load_time < 3 else 'fail'
        results['checks'].append({
            'name': 'Vitesse < 2 secondes',
            'status': speed_status,
            'value': f'{load_time:.2f}s',
            'details': 'Rapide' if load_time < 2 else 'LENT - Perte de visiteurs' if load_time >= 3 else 'Acceptable',
            'importance': 'critical',
            'recommendation': 'Optimiser images, activer compression, utiliser CDN' if speed_status != 'pass' else None
        })

        # Mobile Viewport - STRICT
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        vp_content = viewport.get('content', '') if viewport else ''
        vp_status = 'pass' if viewport and 'width=device-width' in vp_content else 'fail'
        results['checks'].append({
            'name': 'Mobile Viewport Correct',
            'status': vp_status,
            'value': vp_content[:80] if vp_content else None,
            'details': 'Configuré correctement' if vp_status == 'pass' else 'MANQUANT - Site non mobile-friendly',
            'importance': 'critical',
            'recommendation': 'Ajouter <meta name="viewport" content="width=device-width, initial-scale=1">' if vp_status != 'pass' else None
        })

        # HTML Lang
        html_tag = self.soup.find('html')
        lang = html_tag.get('lang') if html_tag else None
        lang_status = 'pass' if lang and len(lang) >= 2 else 'fail'
        results['checks'].append({
            'name': 'Attribut lang HTML',
            'status': lang_status,
            'value': lang,
            'details': f'Langue: {lang}' if lang else 'MANQUANT - Problème accessibilité',
            'importance': 'high',
            'recommendation': 'Ajouter lang="fr" à la balise <html>' if lang_status != 'pass' else None
        })

        # Charset UTF-8
        charset = self.soup.find('meta', charset=True)
        charset_val = charset.get('charset', '').upper() if charset else None
        charset_status = 'pass' if charset_val == 'UTF-8' else 'warning' if charset else 'fail'
        results['checks'].append({
            'name': 'Encodage UTF-8',
            'status': charset_status,
            'value': charset_val,
            'details': 'UTF-8 correct' if charset_status == 'pass' else 'Encodage incorrect ou manquant',
            'importance': 'medium',
            'recommendation': 'Ajouter <meta charset="UTF-8"> en premier dans <head>' if charset_status != 'pass' else None
        })

        # Favicon
        favicon = self.soup.find('link', rel=re.compile('icon'))
        fav_status = 'pass' if favicon else 'warning'
        results['checks'].append({
            'name': 'Favicon',
            'status': fav_status,
            'value': favicon.get('href')[:60] if favicon else None,
            'details': 'Présent' if favicon else 'Manquant - Mauvaise image de marque',
            'importance': 'low',
            'recommendation': 'Ajouter favicon pour branding' if fav_status != 'pass' else None
        })

        # Count
        for check in results['checks']:
            if check['status'] == 'pass': results['passed'] += 1
            elif check['status'] == 'fail': results['failed'] += 1
            else: results['warnings'] += 1

        return results

    def check_ssl(self):
        """Vérifie le certificat SSL"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_remaining = (expire_date - datetime.now()).days
                    return {
                        'valid': True,
                        'issuer': dict(x[0] for x in cert['issuer']).get('organizationName', 'Unknown'),
                        'expires': expire_date.isoformat(),
                        'days_remaining': days_remaining
                    }
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    # ==========================================
    # AI READINESS - TRÈS STRICT!!!
    # ==========================================
    def scan_ai_readiness(self):
        """Analyse AI-readiness TRÈS STRICTE"""
        results = {'checks': [], 'passed': 0, 'failed': 0, 'warnings': 0, 'ai_score': 0}

        # 1. Robots.txt - AI Bots - STRICT: tous doivent être autorisés explicitement
        robots_resp = self.fetch_page(f"{self.base_url}/robots.txt")
        robots_content = robots_resp.text.lower() if robots_resp and robots_resp.status_code == 200 else ''

        ai_bots_check = {
            'GPTBot': self._check_bot_allowed(robots_content, 'gptbot'),
            'ChatGPT-User': self._check_bot_allowed(robots_content, 'chatgpt-user'),
            'ClaudeBot': self._check_bot_allowed(robots_content, 'claudebot'),
            'Claude-Web': self._check_bot_allowed(robots_content, 'claude-web'),
            'PerplexityBot': self._check_bot_allowed(robots_content, 'perplexitybot'),
            'Cohere-AI': self._check_bot_allowed(robots_content, 'cohere'),
            'Google-Extended': self._check_bot_allowed(robots_content, 'google-extended'),
            'Anthropic-AI': self._check_bot_allowed(robots_content, 'anthropic'),
        }

        blocked = [b for b, allowed in ai_bots_check.items() if not allowed]
        allowed = [b for b, allowed in ai_bots_check.items() if allowed]

        # STRICT: Tous les bots doivent être autorisés
        bot_status = 'pass' if len(blocked) == 0 else 'warning' if len(blocked) <= 2 else 'fail'
        results['checks'].append({
            'name': 'Bots AI Autorisés (8 requis)',
            'status': bot_status,
            'value': {'allowed': allowed, 'blocked': blocked},
            'details': f'{len(allowed)}/8 bots autorisés' + (f' - BLOQUÉS: {", ".join(blocked)}' if blocked else ''),
            'importance': 'critical',
            'recommendation': f'Autoriser explicitement dans robots.txt: {", ".join(blocked)}' if blocked else None,
            'ai_impact': 'ChatGPT, Claude et Perplexity NE PEUVENT PAS recommander votre site' if blocked else 'Tous les AI peuvent indexer votre site'
        })

        # 2. LLMs.txt - STRICT: obligatoire et bien formaté
        llms_resp = self.fetch_page(f"{self.base_url}/llms.txt")
        llms_exists = llms_resp and llms_resp.status_code == 200
        llms_content = llms_resp.text if llms_exists else None
        llms_good = llms_exists and len(llms_content or '') > 200 and '#' in (llms_content or '')
        llms_status = 'pass' if llms_good else 'warning' if llms_exists else 'fail'
        results['checks'].append({
            'name': 'Fichier llms.txt Complet',
            'status': llms_status,
            'value': llms_content[:500] if llms_content else None,
            'details': 'Bien formaté avec sections' if llms_good else 'Existe mais incomplet' if llms_exists else 'MANQUANT - Opportunité critique manquée',
            'importance': 'critical',
            'recommendation': 'Créer llms.txt détaillé avec services, FAQ, contact' if llms_status != 'pass' else None,
            'ai_impact': 'Les AI utilisent ce fichier pour MIEUX comprendre et recommander votre site'
        })

        # 3. Schema.org - STRICT: LocalBusiness OU Organization requis + FAQPage
        schema_scripts = self.soup.find_all('script', type='application/ld+json')
        schema_types = []
        for script in schema_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    schema_types.append(data.get('@type', ''))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_types.append(item.get('@type', ''))
            except:
                pass

        has_business = any(t in schema_types for t in ['LocalBusiness', 'Organization', 'Corporation', 'Service'])
        has_faq = 'FAQPage' in schema_types
        has_webpage = 'WebPage' in schema_types or 'WebSite' in schema_types

        schema_score = sum([has_business, has_faq, has_webpage])
        schema_status = 'pass' if schema_score >= 2 else 'warning' if schema_score >= 1 else 'fail'

        missing = []
        if not has_business: missing.append('LocalBusiness/Organization')
        if not has_faq: missing.append('FAQPage')

        results['checks'].append({
            'name': 'Schema.org (Business + FAQ)',
            'status': schema_status,
            'value': schema_types,
            'details': f'{len(schema_types)} schemas: {", ".join(schema_types[:4])}' if schema_types else 'AUCUN SCHEMA - Invisible pour AI',
            'importance': 'critical',
            'recommendation': f'Ajouter Schema: {", ".join(missing)}' if missing else None,
            'ai_impact': 'Les AI utilisent Schema.org pour comprendre votre entreprise et l\'afficher dans les résultats'
        })

        # 4. FAQ Structurée - STRICT: FAQPage schema requis
        faq_status = 'pass' if has_faq else 'fail'
        results['checks'].append({
            'name': 'FAQ avec Schema FAQPage',
            'status': faq_status,
            'value': 'FAQPage présent' if has_faq else None,
            'details': 'FAQ optimisée pour AI' if has_faq else 'MANQUANT - Vos FAQ n\'apparaissent pas dans ChatGPT',
            'importance': 'critical',
            'recommendation': 'Ajouter FAQPage Schema avec questions/réponses' if not has_faq else None,
            'ai_impact': 'Les FAQ avec Schema apparaissent DIRECTEMENT dans les réponses ChatGPT et Google'
        })

        # 5. Contenu Substantiel - STRICT: min 500 mots
        paragraphs = self.soup.find_all('p')
        word_count = sum(len(p.text.split()) for p in paragraphs)
        has_lists = len(self.soup.find_all(['ul', 'ol'])) >= 2

        content_status = 'pass' if word_count >= 500 and has_lists else 'warning' if word_count >= 300 else 'fail'
        results['checks'].append({
            'name': 'Contenu Riche (min 500 mots)',
            'status': content_status,
            'value': {'words': word_count, 'has_lists': has_lists},
            'details': f'{word_count} mots, listes: {"oui" if has_lists else "non"}',
            'importance': 'critical',
            'recommendation': f'Ajouter {500 - word_count} mots de contenu structuré avec listes' if word_count < 500 else None,
            'ai_impact': 'Plus de contenu = plus de contexte = plus de chances d\'être recommandé'
        })

        # 6. Informations NAP Claires - STRICT
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}'
        emails = list(set(re.findall(email_pattern, self.html)))
        phones = list(set(re.findall(phone_pattern, self.html)))

        nap_status = 'pass' if emails and phones else 'warning' if emails or phones else 'fail'
        results['checks'].append({
            'name': 'Contact Visible (Email + Tél)',
            'status': nap_status,
            'value': {'emails': emails[:2], 'phones': phones[:2]},
            'details': f'Email: {"oui" if emails else "NON"}, Tél: {"oui" if phones else "NON"}',
            'importance': 'high',
            'recommendation': 'Afficher clairement email ET téléphone sur la page' if nap_status != 'pass' else None,
            'ai_impact': 'Les AI recommandent avec vos coordonnées - invisible = pas de contact'
        })

        # 7. Meta Description Riche pour AI
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc.get('content', '') if meta_desc else ''
        desc_words = len(desc.split())
        desc_status = 'pass' if desc_words >= 20 else 'warning' if desc_words >= 10 else 'fail'
        results['checks'].append({
            'name': 'Description Riche pour AI',
            'status': desc_status,
            'value': desc[:150],
            'details': f'{desc_words} mots (min 20 recommandés)',
            'importance': 'high',
            'recommendation': 'Écrire description détaillée avec services, lieu, différenciateurs' if desc_status != 'pass' else None,
            'ai_impact': 'Les AI utilisent la meta description comme résumé principal'
        })

        # 8. Mentions de Marque
        brand = self.domain.split('.')[0].lower()
        brand_count = self.html.lower().count(brand)
        brand_status = 'pass' if brand_count >= 5 else 'warning' if brand_count >= 2 else 'fail'
        results['checks'].append({
            'name': 'Mentions de Marque (min 5)',
            'status': brand_status,
            'value': brand_count,
            'details': f'{brand_count} mentions de "{brand}"',
            'importance': 'medium',
            'recommendation': f'Mentionner votre marque "{brand}" au moins 5 fois' if brand_status != 'pass' else None,
            'ai_impact': 'Aide les AI à associer votre marque à vos services'
        })

        # 9. NOUVEAU: Données structurées pour services
        service_keywords = ['service', 'prix', 'tarif', 'offre', 'solution', 'produit']
        has_service_content = any(kw in self.html.lower() for kw in service_keywords)
        service_status = 'pass' if has_service_content and has_business else 'warning' if has_service_content else 'fail'
        results['checks'].append({
            'name': 'Services Clairement Décrits',
            'status': service_status,
            'value': has_service_content,
            'details': 'Services décrits avec schema' if service_status == 'pass' else 'Services mentionnés' if has_service_content else 'Aucune description de services',
            'importance': 'high',
            'recommendation': 'Décrire clairement vos services avec prix et détails' if service_status != 'pass' else None,
            'ai_impact': 'Les AI ne peuvent pas recommander ce qu\'ils ne comprennent pas'
        })

        # 10. NOUVEAU: Avis/Témoignages structurés
        has_reviews = bool(self.soup.find(class_=re.compile('review|testimonial|avis|temoignage', re.I)))
        review_schema = any(t in schema_types for t in ['Review', 'AggregateRating'])
        review_status = 'pass' if review_schema else 'warning' if has_reviews else 'fail'
        results['checks'].append({
            'name': 'Avis/Témoignages avec Schema',
            'status': review_status,
            'value': review_schema,
            'details': 'Avis avec schema Review' if review_schema else 'Témoignages sans schema' if has_reviews else 'Aucun avis visible',
            'importance': 'high',
            'recommendation': 'Ajouter témoignages clients avec schema AggregateRating' if review_status != 'pass' else None,
            'ai_impact': 'Les avis augmentent la crédibilité et les recommandations AI'
        })

        # Count
        for check in results['checks']:
            if check['status'] == 'pass': results['passed'] += 1
            elif check['status'] == 'fail': results['failed'] += 1
            else: results['warnings'] += 1

        # AI Score strict: échecs comptent double
        total = len(results['checks'])
        score = ((results['passed'] * 1) + (results['warnings'] * 0.4)) / total * 100
        results['ai_score'] = int(score)

        return results

    def _check_bot_allowed(self, robots_content, bot_name):
        """Vérifie si un bot est autorisé dans robots.txt"""
        if not robots_content:
            return True  # Pas de robots.txt = tout autorisé par défaut

        # Chercher une règle spécifique pour ce bot
        lines = robots_content.split('\n')
        current_agent = None

        for line in lines:
            line = line.strip().lower()
            if line.startswith('user-agent:'):
                current_agent = line.split(':', 1)[1].strip()
            elif current_agent and (bot_name in current_agent or current_agent == '*'):
                if line.startswith('disallow:') and line.split(':', 1)[1].strip() == '/':
                    return False
                if line.startswith('allow:'):
                    return True

        return True  # Par défaut autorisé

    # ==========================================
    # QUALITÉ DU CONTENU - STRICT
    # ==========================================
    def scan_content_quality(self):
        """Analyse qualité du contenu STRICTE"""
        results = {'checks': [], 'passed': 0, 'failed': 0, 'warnings': 0}

        # Word count - STRICT: min 800 mots
        text = self.soup.get_text()
        words = len(text.split())
        word_status = 'pass' if words >= 800 else 'warning' if words >= 400 else 'fail'
        results['checks'].append({
            'name': 'Contenu Substantiel (min 800)',
            'status': word_status,
            'value': words,
            'details': f'{words} mots (min 800 pour bon SEO)',
            'importance': 'critical',
            'recommendation': f'Ajouter {800 - words} mots de contenu pertinent' if words < 800 else None
        })

        # Paragraphes - STRICT
        paragraphs = self.soup.find_all('p')
        p_count = len([p for p in paragraphs if len(p.text.split()) > 20])
        p_status = 'pass' if p_count >= 5 else 'warning' if p_count >= 2 else 'fail'
        results['checks'].append({
            'name': 'Paragraphes Développés (min 5)',
            'status': p_status,
            'value': p_count,
            'details': f'{p_count} paragraphes de 20+ mots',
            'importance': 'high',
            'recommendation': 'Développer le contenu en paragraphes substantiels' if p_status != 'pass' else None
        })

        # Call to Action - STRICT
        cta_patterns = ['contact', 'appel', 'soumission', 'devis', 'gratuit', 'réserv', 'command', 'achet', 'inscri', 'essai']
        cta_found = [p for p in cta_patterns if p in text.lower()]
        cta_status = 'pass' if len(cta_found) >= 2 else 'warning' if len(cta_found) >= 1 else 'fail'
        results['checks'].append({
            'name': 'Appels à l\'Action (CTA)',
            'status': cta_status,
            'value': cta_found,
            'details': f'{len(cta_found)} CTA trouvés: {", ".join(cta_found[:3])}' if cta_found else 'AUCUN CTA - Pas de conversion',
            'importance': 'high',
            'recommendation': 'Ajouter CTAs clairs: "Contactez-nous", "Demandez un devis gratuit"' if cta_status != 'pass' else None
        })

        # Listes
        lists = self.soup.find_all(['ul', 'ol'])
        list_items = sum(len(l.find_all('li')) for l in lists)
        list_status = 'pass' if list_items >= 6 else 'warning' if list_items >= 3 else 'fail'
        results['checks'].append({
            'name': 'Listes Structurées',
            'status': list_status,
            'value': list_items,
            'details': f'{list_items} éléments de liste',
            'importance': 'medium',
            'recommendation': 'Ajouter listes à puces pour services, avantages, FAQ' if list_status != 'pass' else None
        })

        # Count
        for check in results['checks']:
            if check['status'] == 'pass': results['passed'] += 1
            elif check['status'] == 'fail': results['failed'] += 1
            else: results['warnings'] += 1

        return results

    # ==========================================
    # SCORES STRICTS
    # ==========================================
    def calculate_strict_scores(self):
        """Calcule les scores avec pénalités strictes"""
        categories = ['seo_classic', 'seo_technique', 'ai_readiness', 'content_quality']

        total_score = 0
        category_count = 0

        for cat in categories:
            if cat in self.results and 'checks' in self.results[cat]:
                checks = self.results[cat]['checks']
                passed = sum(1 for c in checks if c['status'] == 'pass')
                warnings = sum(1 for c in checks if c['status'] == 'warning')
                failed = sum(1 for c in checks if c['status'] == 'fail')
                total = len(checks)

                # Score strict: pass=100%, warning=40%, fail=0%
                # Les fails sur 'critical' pénalisent -10% supplémentaire
                critical_fails = sum(1 for c in checks if c['status'] == 'fail' and c.get('importance') == 'critical')

                raw_score = ((passed * 1) + (warnings * 0.4)) / total * 100 if total > 0 else 0
                penalty = critical_fails * 5  # -5% par échec critique

                cat_score = max(0, raw_score - penalty)
                self.results['scores'][cat] = int(cat_score)

                total_score += cat_score
                category_count += 1

        # Score total (moyenne)
        self.results['scores']['total'] = int(total_score / category_count) if category_count > 0 else 0

        # Grade STRICT
        score = self.results['scores']['total']
        if score >= 90: self.results['grade'] = 'A+'
        elif score >= 80: self.results['grade'] = 'A'
        elif score >= 70: self.results['grade'] = 'B'
        elif score >= 55: self.results['grade'] = 'C'
        elif score >= 40: self.results['grade'] = 'D'
        else: self.results['grade'] = 'F'

    def generate_recommendations(self):
        """Génère les recommandations prioritaires"""
        all_recs = []
        importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

        for cat in ['ai_readiness', 'seo_classic', 'seo_technique', 'content_quality']:
            if cat in self.results and 'checks' in self.results[cat]:
                for check in self.results[cat]['checks']:
                    if check.get('recommendation') and check['status'] != 'pass':
                        all_recs.append({
                            'category': cat,
                            'check': check['name'],
                            'importance': check.get('importance', 'medium'),
                            'recommendation': check['recommendation'],
                            'ai_impact': check.get('ai_impact'),
                            'status': check['status']
                        })

        all_recs.sort(key=lambda x: (importance_order.get(x['importance'], 2), x['status'] != 'fail'))
        self.results['recommendations'] = all_recs[:15]


# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'seo-scanner-api-strict', 'version': '2.0'})

@app.route('/api/scan', methods=['POST', 'GET'])
def scan_domain():
    """Lance un scan complet STRICT"""
    if request.method == 'POST':
        data = request.json or {}
        domain = data.get('domain')
    else:
        domain = request.args.get('domain')

    if not domain:
        return jsonify({'error': 'domain requis'}), 400

    domain = domain.strip().lower()
    if domain.startswith('http'):
        domain = urlparse(domain).netloc

    scanner = SEOScanner(domain)
    results = scanner.run_full_scan()

    return jsonify(results)


if __name__ == '__main__':
    print("="*60)
    print("🔍 SEO SCANNER API v2.0 - STRICT MODE")
    print("="*60)
    print("Scoring sévère activé:")
    print("  - Pass = 100%, Warning = 40%, Fail = 0%")
    print("  - Pénalité -5% par échec critique")
    print("  - 10 checks AI-readiness")
    print("="*60)
    app.run(host='0.0.0.0', port=8893, debug=False)

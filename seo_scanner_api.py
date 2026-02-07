#!/usr/bin/env python3
"""
SEO Scanner API - Scanner killer pour seoparai.ca
Analyse complète SEO + AI-readiness pour tout site web
"""

import requests
import json
import re
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import concurrent.futures
import time

app = Flask(__name__)
CORS(app)

class SEOScanner:
    """Scanner SEO complet avec focus AI-readiness"""

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
            'User-Agent': 'Mozilla/5.0 (compatible; SEOparAI-Scanner/1.0; +https://seoparai.ca)',
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
        print(f"[SCAN] Démarrage scan complet: {self.domain}")

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

        # Exécuter tous les scans en parallèle
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

        # Calculer les scores
        self.calculate_scores()

        # Générer les recommandations
        self.generate_recommendations()

        return self.results

    # ==========================================
    # SEO CLASSIQUE
    # ==========================================
    def scan_seo_classic(self):
        """Analyse SEO classique"""
        results = {'checks': [], 'passed': 0, 'failed': 0}

        # Title
        title_tag = self.soup.find('title')
        title = title_tag.text.strip() if title_tag else None
        title_len = len(title) if title else 0
        results['checks'].append({
            'name': 'Meta Title',
            'status': 'pass' if title and 30 <= title_len <= 60 else 'warning' if title else 'fail',
            'value': title[:80] if title else None,
            'details': f'{title_len} caractères' if title else 'Manquant',
            'importance': 'critical',
            'recommendation': 'Titre entre 30-60 caractères avec mot-clé principal' if not title or title_len < 30 or title_len > 60 else None
        })

        # Meta Description
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc.get('content', '').strip() if meta_desc else None
        desc_len = len(desc) if desc else 0
        results['checks'].append({
            'name': 'Meta Description',
            'status': 'pass' if desc and 120 <= desc_len <= 160 else 'warning' if desc else 'fail',
            'value': desc[:200] if desc else None,
            'details': f'{desc_len} caractères' if desc else 'Manquante',
            'importance': 'critical',
            'recommendation': 'Description entre 120-160 caractères avec call-to-action' if not desc or desc_len < 120 or desc_len > 160 else None
        })

        # H1
        h1_tags = self.soup.find_all('h1')
        h1_count = len(h1_tags)
        h1_text = h1_tags[0].text.strip()[:100] if h1_tags else None
        results['checks'].append({
            'name': 'Balise H1',
            'status': 'pass' if h1_count == 1 else 'warning' if h1_count > 1 else 'fail',
            'value': h1_text,
            'details': f'{h1_count} H1 trouvé(s)' if h1_count else 'Aucun H1',
            'importance': 'critical',
            'recommendation': 'Un seul H1 par page avec mot-clé principal' if h1_count != 1 else None
        })

        # H2-H6 Structure
        headings = {f'h{i}': len(self.soup.find_all(f'h{i}')) for i in range(2, 7)}
        has_structure = headings['h2'] > 0
        results['checks'].append({
            'name': 'Structure des titres',
            'status': 'pass' if has_structure else 'fail',
            'value': headings,
            'details': f"H2: {headings['h2']}, H3: {headings['h3']}, H4: {headings['h4']}",
            'importance': 'high',
            'recommendation': 'Ajouter des sous-titres H2, H3 pour structurer le contenu' if not has_structure else None
        })

        # Images ALT
        images = self.soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt') and img.get('alt').strip()]
        img_score = (len(images_with_alt) / len(images) * 100) if images else 100
        results['checks'].append({
            'name': 'Images avec ALT',
            'status': 'pass' if img_score >= 90 else 'warning' if img_score >= 50 else 'fail',
            'value': f'{len(images_with_alt)}/{len(images)}',
            'details': f'{img_score:.0f}% des images ont un attribut alt',
            'importance': 'high',
            'recommendation': f'Ajouter alt à {len(images) - len(images_with_alt)} images' if img_score < 100 else None
        })

        # Internal Links
        links = self.soup.find_all('a', href=True)
        internal_links = [l for l in links if self.domain in l.get('href', '') or l.get('href', '').startswith('/')]
        external_links = [l for l in links if l.get('href', '').startswith('http') and self.domain not in l.get('href', '')]
        results['checks'].append({
            'name': 'Maillage interne',
            'status': 'pass' if len(internal_links) >= 3 else 'warning' if len(internal_links) >= 1 else 'fail',
            'value': f'{len(internal_links)} internes, {len(external_links)} externes',
            'details': f'{len(links)} liens au total',
            'importance': 'high',
            'recommendation': 'Ajouter plus de liens internes vers vos pages importantes' if len(internal_links) < 3 else None
        })

        # Canonical
        canonical = self.soup.find('link', rel='canonical')
        canonical_url = canonical.get('href') if canonical else None
        results['checks'].append({
            'name': 'URL Canonique',
            'status': 'pass' if canonical_url else 'warning',
            'value': canonical_url[:80] if canonical_url else None,
            'details': 'Définie' if canonical_url else 'Non définie',
            'importance': 'medium',
            'recommendation': 'Ajouter une balise canonical pour éviter le contenu dupliqué' if not canonical_url else None
        })

        # Open Graph
        og_tags = self.soup.find_all('meta', property=re.compile('^og:'))
        og_present = ['og:title', 'og:description', 'og:image', 'og:url']
        og_found = [tag.get('property') for tag in og_tags]
        og_missing = [tag for tag in og_present if tag not in og_found]
        results['checks'].append({
            'name': 'Open Graph (Facebook)',
            'status': 'pass' if len(og_missing) == 0 else 'warning' if len(og_found) > 0 else 'fail',
            'value': og_found,
            'details': f'{len(og_found)}/4 tags présents',
            'importance': 'medium',
            'recommendation': f'Ajouter: {", ".join(og_missing)}' if og_missing else None
        })

        # Twitter Cards
        twitter_tags = self.soup.find_all('meta', attrs={'name': re.compile('^twitter:')})
        results['checks'].append({
            'name': 'Twitter Cards',
            'status': 'pass' if len(twitter_tags) >= 3 else 'warning' if len(twitter_tags) > 0 else 'fail',
            'value': [tag.get('name') for tag in twitter_tags],
            'details': f'{len(twitter_tags)} tags trouvés',
            'importance': 'low',
            'recommendation': 'Ajouter twitter:card, twitter:title, twitter:description' if len(twitter_tags) < 3 else None
        })

        # Count passed/failed
        for check in results['checks']:
            if check['status'] == 'pass':
                results['passed'] += 1
            elif check['status'] == 'fail':
                results['failed'] += 1

        return results

    # ==========================================
    # SEO TECHNIQUE
    # ==========================================
    def scan_seo_technique(self):
        """Analyse SEO technique"""
        results = {'checks': [], 'passed': 0, 'failed': 0}

        # SSL/HTTPS
        is_https = self.final_url.startswith('https')
        ssl_info = self.check_ssl()
        results['checks'].append({
            'name': 'HTTPS/SSL',
            'status': 'pass' if is_https and ssl_info.get('valid') else 'fail',
            'value': ssl_info,
            'details': f"SSL valide, expire dans {ssl_info.get('days_remaining', 'N/A')} jours" if ssl_info.get('valid') else 'SSL invalide ou absent',
            'importance': 'critical',
            'recommendation': 'Installer un certificat SSL valide' if not is_https else None
        })

        # Robots.txt
        robots_resp = self.fetch_page(f"{self.base_url}/robots.txt")
        robots_exists = robots_resp and robots_resp.status_code == 200
        robots_content = robots_resp.text if robots_exists else None
        results['checks'].append({
            'name': 'Robots.txt',
            'status': 'pass' if robots_exists else 'fail',
            'value': robots_content[:500] if robots_content else None,
            'details': f'{len(robots_content)} caractères' if robots_content else 'Fichier manquant',
            'importance': 'high',
            'recommendation': 'Créer un fichier robots.txt pour guider les moteurs de recherche' if not robots_exists else None
        })

        # Sitemap.xml
        sitemap_resp = self.fetch_page(f"{self.base_url}/sitemap.xml")
        sitemap_exists = sitemap_resp and sitemap_resp.status_code == 200
        sitemap_urls = 0
        if sitemap_exists:
            sitemap_urls = len(re.findall(r'<loc>', sitemap_resp.text))
        results['checks'].append({
            'name': 'Sitemap.xml',
            'status': 'pass' if sitemap_exists and sitemap_urls > 0 else 'warning' if sitemap_exists else 'fail',
            'value': f'{sitemap_urls} URLs',
            'details': f'{sitemap_urls} pages indexées' if sitemap_exists else 'Sitemap manquant',
            'importance': 'high',
            'recommendation': 'Créer un sitemap.xml avec toutes vos pages' if not sitemap_exists else None
        })

        # Page Speed (basique)
        start_time = time.time()
        _ = self.fetch_page(self.base_url)
        load_time = time.time() - start_time
        results['checks'].append({
            'name': 'Temps de chargement',
            'status': 'pass' if load_time < 2 else 'warning' if load_time < 4 else 'fail',
            'value': f'{load_time:.2f}s',
            'details': 'Rapide' if load_time < 2 else 'Moyen' if load_time < 4 else 'Lent',
            'importance': 'critical',
            'recommendation': 'Optimiser les images et activer la compression' if load_time >= 2 else None
        })

        # Mobile Viewport
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        results['checks'].append({
            'name': 'Mobile Viewport',
            'status': 'pass' if viewport else 'fail',
            'value': viewport.get('content')[:100] if viewport else None,
            'details': 'Configuré' if viewport else 'Manquant',
            'importance': 'critical',
            'recommendation': 'Ajouter <meta name="viewport" content="width=device-width, initial-scale=1">' if not viewport else None
        })

        # HTML Lang
        html_tag = self.soup.find('html')
        lang = html_tag.get('lang') if html_tag else None
        results['checks'].append({
            'name': 'Attribut lang HTML',
            'status': 'pass' if lang else 'warning',
            'value': lang,
            'details': f'Langue: {lang}' if lang else 'Non défini',
            'importance': 'medium',
            'recommendation': 'Ajouter lang="fr" à la balise <html>' if not lang else None
        })

        # Charset
        charset = self.soup.find('meta', charset=True) or self.soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        results['checks'].append({
            'name': 'Encodage charset',
            'status': 'pass' if charset else 'warning',
            'value': charset.get('charset') or 'UTF-8' if charset else None,
            'details': 'UTF-8 recommandé',
            'importance': 'medium',
            'recommendation': 'Ajouter <meta charset="UTF-8">' if not charset else None
        })

        # Favicon
        favicon = self.soup.find('link', rel=re.compile('icon'))
        results['checks'].append({
            'name': 'Favicon',
            'status': 'pass' if favicon else 'warning',
            'value': favicon.get('href')[:80] if favicon else None,
            'details': 'Présent' if favicon else 'Manquant',
            'importance': 'low',
            'recommendation': 'Ajouter un favicon pour le branding' if not favicon else None
        })

        # Count passed/failed
        for check in results['checks']:
            if check['status'] == 'pass':
                results['passed'] += 1
            elif check['status'] == 'fail':
                results['failed'] += 1

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
    # AI READINESS - Le plus important!
    # ==========================================
    def scan_ai_readiness(self):
        """Analyse la préparation pour les AI (ChatGPT, Claude, Perplexity, etc.)"""
        results = {'checks': [], 'passed': 0, 'failed': 0, 'ai_score': 0}

        # 1. Robots.txt - AI Bots
        robots_resp = self.fetch_page(f"{self.base_url}/robots.txt")
        robots_content = robots_resp.text.lower() if robots_resp and robots_resp.status_code == 200 else ''

        ai_bots = {
            'GPTBot': 'gptbot' in robots_content and 'disallow' not in robots_content.split('gptbot')[1][:50] if 'gptbot' in robots_content else True,
            'ChatGPT-User': 'chatgpt-user' not in robots_content or 'allow' in robots_content,
            'ClaudeBot': 'claudebot' not in robots_content or 'allow' in robots_content,
            'Claude-Web': 'claude-web' not in robots_content or 'allow' in robots_content,
            'PerplexityBot': 'perplexitybot' not in robots_content or 'allow' in robots_content,
            'Cohere-AI': 'cohere' not in robots_content or 'allow' in robots_content,
            'Google-Extended': 'google-extended' not in robots_content or 'allow' in robots_content,
        }

        blocked_bots = [bot for bot, allowed in ai_bots.items() if not allowed]
        allowed_bots = [bot for bot, allowed in ai_bots.items() if allowed]

        results['checks'].append({
            'name': 'Accès aux bots AI',
            'status': 'pass' if len(blocked_bots) == 0 else 'warning' if len(blocked_bots) < 3 else 'fail',
            'value': {'allowed': allowed_bots, 'blocked': blocked_bots},
            'details': f'{len(allowed_bots)}/7 bots AI autorisés',
            'importance': 'critical',
            'recommendation': f'Autoriser dans robots.txt: {", ".join(blocked_bots)}' if blocked_bots else None,
            'ai_impact': 'ChatGPT, Claude et Perplexity ne pourront pas indexer votre site' if blocked_bots else 'Tous les AI peuvent lire votre site'
        })

        # 2. LLMs.txt
        llms_resp = self.fetch_page(f"{self.base_url}/llms.txt")
        llms_exists = llms_resp and llms_resp.status_code == 200
        llms_content = llms_resp.text[:1000] if llms_exists else None
        results['checks'].append({
            'name': 'Fichier llms.txt',
            'status': 'pass' if llms_exists else 'fail',
            'value': llms_content,
            'details': 'Présent - Guide pour les AI' if llms_exists else 'Manquant - Opportunité manquée',
            'importance': 'critical',
            'recommendation': 'Créer llms.txt pour guider les AI sur votre contenu' if not llms_exists else None,
            'ai_impact': 'Les AI utilisent ce fichier pour mieux comprendre et recommander votre site'
        })

        # 3. Schema.org Markup
        schema_scripts = self.soup.find_all('script', type='application/ld+json')
        schema_types = []
        for script in schema_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    schema_types.append(data.get('@type', 'Unknown'))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_types.append(item.get('@type', 'Unknown'))
            except:
                pass

        important_schemas = ['LocalBusiness', 'Organization', 'WebSite', 'FAQPage', 'Article', 'Product', 'Service']
        has_important = any(s in schema_types for s in important_schemas)

        results['checks'].append({
            'name': 'Schema.org Markup',
            'status': 'pass' if has_important else 'warning' if schema_types else 'fail',
            'value': schema_types,
            'details': f'{len(schema_types)} schemas: {", ".join(schema_types[:5])}' if schema_types else 'Aucun schema trouvé',
            'importance': 'critical',
            'recommendation': 'Ajouter Schema LocalBusiness, FAQPage, Organization' if not has_important else None,
            'ai_impact': 'Les AI utilisent Schema.org pour comprendre votre entreprise et services'
        })

        # 4. FAQ structurée
        faq_schema = 'FAQPage' in schema_types
        faq_section = self.soup.find(id=re.compile('faq', re.I)) or self.soup.find(class_=re.compile('faq', re.I))
        results['checks'].append({
            'name': 'FAQ pour AI',
            'status': 'pass' if faq_schema else 'warning' if faq_section else 'fail',
            'value': 'FAQPage Schema présent' if faq_schema else 'Section FAQ trouvée' if faq_section else None,
            'details': 'Optimisé pour AI' if faq_schema else 'Partiellement optimisé' if faq_section else 'Manquant',
            'importance': 'high',
            'recommendation': 'Ajouter FAQPage Schema pour apparaître dans les réponses AI' if not faq_schema else None,
            'ai_impact': 'Les FAQ avec Schema apparaissent directement dans les réponses ChatGPT'
        })

        # 5. Contenu structuré et clair
        paragraphs = self.soup.find_all('p')
        word_count = sum(len(p.text.split()) for p in paragraphs)
        has_lists = len(self.soup.find_all(['ul', 'ol'])) > 0
        has_tables = len(self.soup.find_all('table')) > 0

        results['checks'].append({
            'name': 'Contenu structuré',
            'status': 'pass' if word_count > 300 and has_lists else 'warning' if word_count > 150 else 'fail',
            'value': {'words': word_count, 'lists': has_lists, 'tables': has_tables},
            'details': f'{word_count} mots, listes: {"oui" if has_lists else "non"}',
            'importance': 'high',
            'recommendation': 'Ajouter plus de contenu texte avec listes et structure claire' if word_count < 300 else None,
            'ai_impact': 'Plus de contenu = plus de chances d\'être cité par les AI'
        })

        # 6. Informations de contact claires
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}'
        emails = re.findall(email_pattern, self.html)
        phones = re.findall(phone_pattern, self.html)

        results['checks'].append({
            'name': 'Informations NAP',
            'status': 'pass' if emails and phones else 'warning' if emails or phones else 'fail',
            'value': {'emails': emails[:3], 'phones': phones[:3]},
            'details': f'Email: {"oui" if emails else "non"}, Téléphone: {"oui" if phones else "non"}',
            'importance': 'high',
            'recommendation': 'Afficher clairement email et téléphone' if not (emails and phones) else None,
            'ai_impact': 'Les AI peuvent recommander votre entreprise avec vos coordonnées'
        })

        # 7. Mentions de marque / Autorité
        brand_mentions = self.soup.find_all(string=re.compile(self.domain.split('.')[0], re.I))
        results['checks'].append({
            'name': 'Mentions de marque',
            'status': 'pass' if len(brand_mentions) >= 3 else 'warning' if len(brand_mentions) >= 1 else 'fail',
            'value': len(brand_mentions),
            'details': f'{len(brand_mentions)} mentions de votre marque',
            'importance': 'medium',
            'recommendation': 'Mentionner votre nom de marque régulièrement' if len(brand_mentions) < 3 else None,
            'ai_impact': 'Aide les AI à associer votre marque à vos services'
        })

        # 8. Meta descriptions riches
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        desc_content = meta_desc.get('content', '') if meta_desc else ''
        has_keywords = len(desc_content.split()) >= 15

        results['checks'].append({
            'name': 'Description riche',
            'status': 'pass' if has_keywords else 'warning' if desc_content else 'fail',
            'value': desc_content[:200],
            'details': 'Description détaillée' if has_keywords else 'Trop courte' if desc_content else 'Manquante',
            'importance': 'high',
            'recommendation': 'Écrire une description de 150+ caractères avec services et localisation' if not has_keywords else None,
            'ai_impact': 'Les AI utilisent la meta description pour résumer votre site'
        })

        # Count passed/failed
        for check in results['checks']:
            if check['status'] == 'pass':
                results['passed'] += 1
            elif check['status'] == 'fail':
                results['failed'] += 1

        # AI Score spécifique
        results['ai_score'] = int((results['passed'] / len(results['checks'])) * 100) if results['checks'] else 0

        return results

    # ==========================================
    # QUALITÉ DU CONTENU
    # ==========================================
    def scan_content_quality(self):
        """Analyse la qualité du contenu"""
        results = {'checks': [], 'passed': 0, 'failed': 0}

        # Word count
        text = self.soup.get_text()
        words = len(text.split())
        results['checks'].append({
            'name': 'Quantité de contenu',
            'status': 'pass' if words >= 500 else 'warning' if words >= 200 else 'fail',
            'value': words,
            'details': f'{words} mots sur la page',
            'importance': 'high',
            'recommendation': 'Ajouter plus de contenu (minimum 500 mots)' if words < 500 else None
        })

        # Keyword density (basic)
        title = self.soup.find('title')
        if title:
            title_words = title.text.lower().split()
            main_keyword = max(title_words, key=len) if title_words else ''
            keyword_count = text.lower().count(main_keyword)
            density = (keyword_count / words * 100) if words > 0 else 0
            results['checks'].append({
                'name': 'Densité mot-clé',
                'status': 'pass' if 1 <= density <= 3 else 'warning' if density < 1 else 'fail',
                'value': f'{density:.1f}%',
                'details': f'"{main_keyword}" apparaît {keyword_count} fois',
                'importance': 'medium',
                'recommendation': f'Ajuster la densité du mot-clé principal' if density < 1 or density > 3 else None
            })

        # Readability (basic - sentence length)
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        results['checks'].append({
            'name': 'Lisibilité',
            'status': 'pass' if 10 <= avg_sentence_length <= 20 else 'warning',
            'value': f'{avg_sentence_length:.1f} mots/phrase',
            'details': 'Bonne lisibilité' if 10 <= avg_sentence_length <= 20 else 'Phrases trop longues' if avg_sentence_length > 20 else 'Phrases trop courtes',
            'importance': 'medium',
            'recommendation': 'Varier la longueur des phrases' if avg_sentence_length > 20 or avg_sentence_length < 10 else None
        })

        # Call to Action
        cta_patterns = ['contact', 'appel', 'soumission', 'devis', 'gratuit', 'réserver', 'commander', 'acheter', 'inscri']
        cta_found = any(pattern in text.lower() for pattern in cta_patterns)
        results['checks'].append({
            'name': 'Appel à l\'action',
            'status': 'pass' if cta_found else 'warning',
            'value': 'Présent' if cta_found else 'Manquant',
            'details': 'CTA trouvé sur la page' if cta_found else 'Aucun CTA clair',
            'importance': 'high',
            'recommendation': 'Ajouter des appels à l\'action clairs (Contactez-nous, Demandez un devis)' if not cta_found else None
        })

        # Count passed/failed
        for check in results['checks']:
            if check['status'] == 'pass':
                results['passed'] += 1
            elif check['status'] == 'fail':
                results['failed'] += 1

        return results

    # ==========================================
    # SCORES & RECOMMENDATIONS
    # ==========================================
    def calculate_scores(self):
        """Calcule les scores globaux"""
        categories = ['seo_classic', 'seo_technique', 'ai_readiness', 'content_quality']

        total_passed = 0
        total_checks = 0

        for cat in categories:
            if cat in self.results and 'checks' in self.results[cat]:
                checks = self.results[cat]['checks']
                passed = sum(1 for c in checks if c['status'] == 'pass')
                total = len(checks)

                self.results['scores'][cat] = int((passed / total) * 100) if total > 0 else 0
                total_passed += passed
                total_checks += total

        # Score total
        self.results['scores']['total'] = int((total_passed / total_checks) * 100) if total_checks > 0 else 0

        # Grade
        score = self.results['scores']['total']
        if score >= 90:
            self.results['grade'] = 'A+'
        elif score >= 80:
            self.results['grade'] = 'A'
        elif score >= 70:
            self.results['grade'] = 'B'
        elif score >= 60:
            self.results['grade'] = 'C'
        elif score >= 50:
            self.results['grade'] = 'D'
        else:
            self.results['grade'] = 'F'

    def generate_recommendations(self):
        """Génère les recommandations prioritaires"""
        all_recommendations = []

        categories = ['ai_readiness', 'seo_classic', 'seo_technique', 'content_quality']
        importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

        for cat in categories:
            if cat in self.results and 'checks' in self.results[cat]:
                for check in self.results[cat]['checks']:
                    if check.get('recommendation') and check['status'] != 'pass':
                        all_recommendations.append({
                            'category': cat,
                            'check': check['name'],
                            'importance': check.get('importance', 'medium'),
                            'recommendation': check['recommendation'],
                            'ai_impact': check.get('ai_impact'),
                            'status': check['status']
                        })

        # Sort by importance
        all_recommendations.sort(key=lambda x: importance_order.get(x['importance'], 2))

        self.results['recommendations'] = all_recommendations[:15]  # Top 15


# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'seo-scanner-api'})

@app.route('/api/scan', methods=['POST', 'GET'])
def scan_domain():
    """Lance un scan complet"""
    if request.method == 'POST':
        data = request.json or {}
        domain = data.get('domain')
    else:
        domain = request.args.get('domain')

    if not domain:
        return jsonify({'error': 'domain requis'}), 400

    # Nettoyer le domaine
    domain = domain.strip().lower()
    if domain.startswith('http'):
        domain = urlparse(domain).netloc

    scanner = SEOScanner(domain)
    results = scanner.run_full_scan()

    return jsonify(results)

@app.route('/api/scan/quick', methods=['GET'])
def quick_scan():
    """Scan rapide - juste les scores"""
    domain = request.args.get('domain')
    if not domain:
        return jsonify({'error': 'domain requis'}), 400

    scanner = SEOScanner(domain)
    results = scanner.run_full_scan()

    return jsonify({
        'domain': results['domain'],
        'scores': results['scores'],
        'grade': results.get('grade'),
        'top_recommendations': results['recommendations'][:5]
    })


if __name__ == '__main__':
    print("="*60)
    print("🔍 SEO SCANNER API - seoparai.ca")
    print("="*60)
    print("Endpoints:")
    print("  POST /api/scan - Scan complet")
    print("  GET  /api/scan?domain=example.com - Scan complet")
    print("  GET  /api/scan/quick?domain=example.com - Scan rapide")
    print("="*60)
    app.run(host='0.0.0.0', port=8893, debug=False)

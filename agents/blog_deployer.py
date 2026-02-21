#!/usr/bin/env python3
"""
blog_deployer.py — Deploy approved articles from DB to live HTML files.

This agent bridges the gap between content generation (DB) and live blog posts.
It converts approved drafts to HTML, deploys them to /var/www/{site}/blog/,
updates blog index pages, sitemaps, and optionally submits to Google Indexing API.

Usage:
    python3 blog_deployer.py                    # Deploy all pending articles
    python3 blog_deployer.py --site 1           # Deploy for site_id=1 only
    python3 blog_deployer.py --dry-run          # Preview without writing files
"""

import os
import sys
import re
import sqlite3
import yaml
import json
import html as html_lib
import subprocess
from datetime import datetime
from urllib.parse import quote

# Path setup
BASE_DIR = '/opt/seo-agent'
DB_PATH = os.path.join(BASE_DIR, 'db', 'seo_agent.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'blog_deployer.log')

# ─── Logging ───
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [DEPLOYER] [{level}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ─── DB ───
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─── Config ───
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def get_site_config(site_id):
    config = load_config()
    sites = config.get('sites', [])
    idx = int(site_id) - 1
    if 0 <= idx < len(sites):
        return sites[idx]
    return None

# ─── Slug generation ───
def generate_slug(title, max_len=80):
    """Generate a URL-friendly slug from a title."""
    slug = title.lower().strip()
    # French accents
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ç': 'c', 'ñ': 'n',
        "'": '-', "'": '-', "–": '-', "—": '-',
    }
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    # Keep only alphanumeric and hyphens
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    # Truncate to max_len at word boundary
    if len(slug) > max_len:
        slug = slug[:max_len].rsplit('-', 1)[0]
    return slug

# ─── HTML Template ───
BLOG_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {site_name}</title>
    <meta name="description" content="{meta_description}">
    <link rel="canonical" href="https://{domain}/blog/{slug}.html">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="https://{domain}/blog/{slug}.html">
    <meta property="og:site_name" content="{site_name}">
    <meta property="og:locale" content="fr_CA">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{meta_description}">
    <script type="application/ld+json">
    {{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title_json}",
  "description": "{meta_description_json}",
  "url": "https://{domain}/blog/{slug}.html",
  "datePublished": "{date_published}",
  "dateModified": "{date_modified}",
  "publisher": {{
    "@type": "Organization",
    "name": "{site_name}",
    "url": "https://{domain}/"
  }},
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "https://{domain}/blog/{slug}.html"
  }}
}}
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        :root {{
            --primary: #0f172a;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --bg-light: #f0f4ff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --white: #ffffff;
            --shadow: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 20px rgba(0,0,0,0.08);
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: var(--text);
            line-height: 1.7;
            background: var(--white);
            -webkit-font-smoothing: antialiased;
        }}
        .nav {{
            background: var(--primary);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-lg);
        }}
        .nav-inner {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
        }}
        .nav-logo {{
            color: var(--white);
            font-weight: 700;
            font-size: 1.2rem;
            text-decoration: none;
            letter-spacing: -0.02em;
        }}
        .nav-links {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .nav-links a {{
            color: rgba(255,255,255,0.85);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        .nav-links a:hover {{
            color: var(--white);
            background: rgba(255,255,255,0.1);
        }}
        .nav-links .btn-accent {{
            background: var(--accent);
            color: var(--white) !important;
            padding: 8px 20px;
        }}
        .nav-links .btn-accent:hover {{
            background: var(--accent-hover);
        }}
        .breadcrumb {{
            max-width: 800px;
            margin: 0 auto;
            padding: 16px 24px;
            font-size: 0.85rem;
            color: var(--text-light);
        }}
        .breadcrumb a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        .breadcrumb span {{ margin: 0 8px; opacity: 0.5; }}
        .article {{
            max-width: 800px;
            margin: 0 auto;
            padding: 0 24px 60px;
        }}
        .article h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.25;
            color: var(--primary);
            margin-bottom: 24px;
            letter-spacing: -0.03em;
        }}
        .article h2 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            margin-top: 48px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--accent);
            letter-spacing: -0.02em;
        }}
        .article h3 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary);
            margin-top: 32px;
            margin-bottom: 12px;
        }}
        .article p {{
            margin-bottom: 16px;
            font-size: 1.05rem;
            color: #374151;
        }}
        .article ul, .article ol {{
            margin-bottom: 16px;
            padding-left: 24px;
        }}
        .article li {{
            margin-bottom: 8px;
            font-size: 1.05rem;
            color: #374151;
        }}
        .article strong {{
            color: var(--primary);
            font-weight: 600;
        }}
        .article a {{
            color: var(--accent);
            text-decoration: underline;
            text-decoration-thickness: 1px;
            text-underline-offset: 3px;
        }}
        .article a:hover {{ color: var(--accent-hover); }}
        .article blockquote {{
            border-left: 4px solid var(--accent);
            margin: 24px 0;
            padding: 16px 24px;
            background: var(--bg-light);
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: var(--text-light);
        }}
        .article img {{
            max-width: 100%;
            height: auto;
            border-radius: 12px;
            margin: 24px 0;
        }}
        .faq-category {{ margin: 32px 0; }}
        .faq-category h2 {{ font-size: 1.4rem; margin-bottom: 16px; }}
        .faq-item {{
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-bottom: 12px;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }}
        .faq-item:hover {{ box-shadow: var(--shadow); }}
        .faq-question {{
            padding: 18px 20px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-light);
            font-size: 1rem;
            color: var(--primary);
            user-select: none;
        }}
        .faq-question::after {{
            content: '+';
            font-size: 1.3rem;
            font-weight: 300;
            color: var(--accent);
            transition: transform 0.3s;
            flex-shrink: 0;
            margin-left: 16px;
        }}
        .faq-item.open .faq-question::after {{ content: '\\2212'; }}
        .faq-answer {{
            padding: 0 20px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
            font-size: 1rem;
            color: #374151;
            line-height: 1.7;
        }}
        .faq-item.open .faq-answer {{
            padding: 16px 20px;
            max-height: 500px;
        }}
        .articles-connexes {{
            margin-top: 48px;
            padding: 32px;
            background: #f0f4ff;
            border-radius: 16px;
        }}
        .articles-connexes h3 {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 16px;
        }}
        .articles-connexes ul {{
            list-style: none;
            padding: 0;
        }}
        .articles-connexes li {{
            margin-bottom: 12px;
        }}
        .articles-connexes a {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
        }}
        .cta-box {{
            background: linear-gradient(135deg, var(--primary), #0f172add);
            color: var(--white);
            padding: 40px;
            border-radius: 16px;
            text-align: center;
            margin: 48px 0 0;
        }}
        .cta-box h3 {{
            color: var(--white);
            font-size: 1.4rem;
            margin-bottom: 12px;
        }}
        .cta-box p {{
            color: rgba(255,255,255,0.85);
            margin-bottom: 20px;
            font-size: 1rem;
        }}
        .cta-box a {{
            display: inline-block;
            background: var(--accent);
            color: var(--white) !important;
            padding: 14px 32px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.2s;
        }}
        .cta-box a:hover {{
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        .footer {{
            background: var(--primary);
            color: rgba(255,255,255,0.7);
            text-align: center;
            padding: 32px 24px;
            font-size: 0.85rem;
            margin-top: 60px;
        }}
        .footer a {{
            color: rgba(255,255,255,0.9);
            text-decoration: none;
        }}
        .footer a:hover {{ text-decoration: underline; }}
        @media (max-width: 768px) {{
            .article h1 {{ font-size: 1.7rem; }}
            .article h2 {{ font-size: 1.3rem; }}
            .article {{ padding: 0 16px 40px; }}
            .nav-inner {{ padding: 0 16px; }}
            .nav-links {{ gap: 4px; }}
            .nav-links a {{ padding: 6px 10px; font-size: 0.82rem; }}
            .cta-box {{ padding: 28px 20px; }}
            .breadcrumb {{ padding: 12px 16px; }}
        }}
        @media (max-width: 480px) {{
            .article h1 {{ font-size: 1.4rem; }}
            .nav-logo {{ font-size: 1rem; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="https://{domain}/" class="nav-logo">{site_name}</a>
            <div class="nav-links">
                <a href="https://{domain}/">Accueil</a>
                <a href="https://{domain}/blog/">Blog</a>
                <a href="{cta_url}" class="btn-accent">{cta_text}</a>
            </div>
        </div>
    </nav>
    <div class="breadcrumb">
        <a href="https://{domain}/">Accueil</a>
        <span>&rsaquo;</span>
        <a href="https://{domain}/blog/">Blog</a>
        <span>&rsaquo;</span>
        {title}
    </div>
    <article class="article">
        <article>
{article_content}
</article>
{articles_connexes}
        <div class="cta-box">
            <h3>Besoin d&rsquo;un service professionnel?</h3>
            <p>Contactez {site_name} pour une soumission gratuite et sans engagement.</p>
            <a href="{cta_url}">{cta_text}</a>
        </div>
    </article>
    <footer class="footer">
        <p>&copy; {year} {site_name}. Tous droits r&eacute;serv&eacute;s.</p>
        <p style="margin-top: 8px;">
            <a href="https://{domain}/">Accueil</a> &middot;
            <a href="https://{domain}/blog/">Blog</a>
        </p>
    </footer>
    <script>
        document.querySelectorAll('.faq-question').forEach(q => {{
            q.addEventListener('click', () => {{
                const item = q.parentElement;
                const wasOpen = item.classList.contains('open');
                document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
                if (!wasOpen) item.classList.add('open');
            }});
        }});
    </script>
</body>
</html>"""

# CTA config per site category
CTA_CONFIG = {
    'deneigement': {
        'cta_url': 'https://deneigement-excellence.ca/#soumission',
        'cta_text': 'Soumission gratuite',
    },
    'paysagement': {
        'cta_url': 'https://paysagiste-excellence.ca/#soumission',
        'cta_text': 'Soumission gratuite',
    },
    'peinture': {
        'cta_url': 'https://jcpeintre.com/#soumission',
        'cta_text': 'Soumission gratuite',
    },
    'seo-marketing': {
        'cta_url': 'https://seoparai.com/formulaire.html',
        'cta_text': 'Soumission gratuite',
    },
}

# ─── Blog Index Card Template ───
INDEX_CARD_TEMPLATE = """        <a href="/blog/{slug}.html" class="blog-card">
            <h3>{title}</h3>
            <p>{excerpt}</p>
            <span class="date">{date}</span>
        </a>"""


# ═══════════════════════════════════════════════════════
#  CORE FUNCTIONS
# ═══════════════════════════════════════════════════════

def get_pending_articles(site_id=None):
    """Fetch articles that are approved but not yet deployed as HTML files.

    DB schema (French):
      content: id, brief_id, site_id, titre, slug, contenu_html, contenu_md,
               meta_description, statut (brouillon/revue/approuve/publie/archive)
      drafts:  id, site_id, titre, contenu, mot_cle, status (pending/approved/published)
      publications: id, content_id, site_id, url_publiee, statut (en_attente/publie/echec/retire)
    """
    conn = get_db()

    # Strategy: check both 'content' and 'drafts' tables
    # 1) From content table: articles with statut='approuve' not yet in publications as 'publie'
    rows = []
    try:
        if site_id:
            rows = conn.execute(
                """SELECT c.id, c.site_id, c.titre AS title,
                          COALESCE(c.contenu_html, c.contenu_md, '') AS content,
                          c.slug AS keyword, c.meta_description,
                          c.created_at, c.statut AS status
                   FROM content c
                   WHERE c.site_id = ? AND c.statut IN ('approuve', 'revue')
                   AND c.id NOT IN (SELECT content_id FROM publications WHERE statut='publie')
                   ORDER BY c.id""",
                (int(site_id),)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT c.id, c.site_id, c.titre AS title,
                          COALESCE(c.contenu_html, c.contenu_md, '') AS content,
                          c.slug AS keyword, c.meta_description,
                          c.created_at, c.statut AS status
                   FROM content c
                   WHERE c.statut IN ('approuve', 'revue')
                   AND c.id NOT IN (SELECT content_id FROM publications WHERE statut='publie')
                   ORDER BY c.id"""
            ).fetchall()
    except Exception as e:
        log(f"Error querying content table: {e}", "WARNING")

    # 2) Also check drafts table for approved but not published
    try:
        if site_id:
            draft_rows = conn.execute(
                """SELECT d.id AS id, d.site_id, d.titre AS title,
                          d.contenu AS content, d.mot_cle AS keyword,
                          '' AS meta_description,
                          d.created_at, d.status
                   FROM drafts d
                   WHERE d.site_id = ? AND d.status IN ('approved', 'approuve')
                   AND d.published_at IS NULL
                   ORDER BY d.id""",
                (str(site_id),)
            ).fetchall()
        else:
            draft_rows = conn.execute(
                """SELECT d.id AS id, d.site_id, d.titre AS title,
                          d.contenu AS content, d.mot_cle AS keyword,
                          '' AS meta_description,
                          d.created_at, d.status
                   FROM drafts d
                   WHERE d.status IN ('approved', 'approuve')
                   AND d.published_at IS NULL
                   ORDER BY d.id"""
            ).fetchall()
        rows = list(rows) + list(draft_rows)
    except Exception as e:
        log(f"Error querying drafts table: {e}", "WARNING")

    conn.close()
    return rows


def format_article_content(raw_content, title):
    """Convert raw content (text/markdown/JSON) to clean HTML."""
    content = raw_content.strip()

    # If content is JSON, extract the body
    if content.startswith('{'):
        try:
            data = json.loads(content)
            content = data.get('content', data.get('body', data.get('article', content)))
            if isinstance(content, dict):
                content = content.get('body', str(content))
        except (json.JSONDecodeError, TypeError):
            pass

    # If content already has HTML tags, return as-is
    if '<h1' in content or '<h2' in content or '<p>' in content:
        # Just ensure it has an h1
        if '<h1' not in content:
            content = f'<h1>{html_lib.escape(title)}</h1>\n\n{content}'
        return content

    # Convert markdown-like text to HTML
    lines = content.split('\n')
    html_parts = [f'<h1>{html_lib.escape(title)}</h1>\n']
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue

        # Headers
        if line.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h3>{html_lib.escape(line[4:])}</h3>')
        elif line.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{html_lib.escape(line[3:])}</h2>')
        elif line.startswith('# '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{html_lib.escape(line[2:])}</h2>')
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{html_lib.escape(line[2:])}</li>')
        elif line.startswith('**') and line.endswith('**'):
            html_parts.append(f'<p><strong>{html_lib.escape(line[2:-2])}</strong></p>')
        else:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            # Bold markers
            formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_lib.escape(line))
            html_parts.append(f'<p>{formatted}</p>')

    if in_list:
        html_parts.append('</ul>')

    return '\n'.join(html_parts)


def get_related_articles(site_id, current_slug, max_count=3):
    """Get other published articles on the same site for internal linking."""
    site_config = get_site_config(site_id)
    if not site_config:
        return []

    blog_path = site_config.get('blog_path', '')
    if not os.path.isdir(blog_path):
        return []

    articles = []
    for fname in os.listdir(blog_path):
        if not fname.endswith('.html') or fname == 'index.html' or fname == f'{current_slug}.html':
            continue
        fpath = os.path.join(blog_path, fname)
        # Extract title from file
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                head = f.read(2000)
            match = re.search(r'<title>(.+?)(?:\s*\|[^<]*)?</title>', head)
            if match:
                title = match.group(1).strip()
                articles.append((fname, title))
        except Exception:
            pass

    return articles[:max_count]


def build_connexes_html(related_articles, domain):
    """Build the 'Articles connexes' HTML block."""
    if not related_articles:
        return ''

    li_items = ''
    for slug, title in related_articles:
        li_items += f'        <li><a href="/blog/{slug}">{html_lib.escape(title)}</a></li>\n'

    return f"""
        <div class="articles-connexes">
            <h3>Articles connexes</h3>
            <ul>
{li_items}            </ul>
            <p style="margin-top: 16px;"><a href="https://{domain}/">&larr; Retour &agrave; l'accueil</a></p>
        </div>"""


def deploy_article(content_row, dry_run=False):
    """Deploy a single approved article as HTML to the site's blog directory."""
    content_id = content_row['id']
    site_id = content_row['site_id']
    title = content_row['title'] or 'Article sans titre'
    raw_content = content_row['content'] or ''
    keyword = content_row['keyword'] or ''
    meta_desc = content_row['meta_description'] or ''
    created = content_row['created_at'] or datetime.now().strftime('%Y-%m-%d')

    site_config = get_site_config(site_id)
    if not site_config:
        log(f"No site config for site_id={site_id}", "ERROR")
        return False

    domain = site_config['domaine']
    site_name = site_config['nom']
    blog_path = site_config.get('blog_path', os.path.join(site_config['chemin'], 'blog'))
    categorie = site_config.get('categorie', 'seo-marketing')

    # Generate slug
    slug = generate_slug(title)
    html_path = os.path.join(blog_path, f'{slug}.html')

    # Skip if already deployed
    if os.path.isfile(html_path):
        log(f"Already deployed: {slug}.html (content #{content_id})")
        return False

    # Format content
    article_html = format_article_content(raw_content, title)

    # Auto-generate meta description if missing
    if not meta_desc:
        # Strip HTML tags and take first 160 chars
        text_only = re.sub(r'<[^>]+>', '', article_html)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        meta_desc = text_only[:157] + '...' if len(text_only) > 160 else text_only

    # Get related articles for internal linking
    related = get_related_articles(site_id, slug)
    articles_connexes = build_connexes_html(related, domain)

    # CTA config
    cta = CTA_CONFIG.get(categorie, CTA_CONFIG['seo-marketing'])

    # Parse date
    date_str = created[:10] if len(created) >= 10 else datetime.now().strftime('%Y-%m-%d')

    # Render template
    final_html = BLOG_TEMPLATE.format(
        title=html_lib.escape(title),
        title_json=title.replace('"', '\\"'),
        meta_description=html_lib.escape(meta_desc),
        meta_description_json=meta_desc.replace('"', '\\"'),
        domain=domain,
        site_name=html_lib.escape(site_name),
        slug=slug,
        date_published=date_str,
        date_modified=datetime.now().strftime('%Y-%m-%d'),
        year=datetime.now().year,
        article_content=article_html,
        articles_connexes=articles_connexes,
        cta_url=cta['cta_url'],
        cta_text=cta['cta_text'],
    )

    if dry_run:
        log(f"[DRY-RUN] Would deploy: {html_path} ({len(final_html)} bytes)")
        return True

    # Ensure blog directory exists
    os.makedirs(blog_path, exist_ok=True)

    # Write HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    os.chmod(html_path, 0o644)

    log(f"Deployed: {html_path} ({len(final_html)} bytes)")

    # Mark as published in DB
    try:
        conn = get_db()
        # Update content table (French schema: statut)
        conn.execute(
            "UPDATE content SET statut='publie' WHERE id=?",
            (content_id,)
        )
        # Insert into publications (French schema: url_publiee, statut)
        conn.execute(
            """INSERT OR IGNORE INTO publications
               (content_id, site_id, url_publiee, statut, published_at)
               VALUES (?, ?, ?, 'publie', datetime('now'))""",
            (content_id, int(site_id),
             f"https://{domain}/blog/{slug}.html")
        )
        # Also update drafts table if the article came from there
        conn.execute(
            "UPDATE drafts SET status='published', published_at=datetime('now') WHERE titre=? AND site_id=?",
            (title, str(site_id))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"DB update error for content #{content_id}: {e}", "WARNING")

    return True


def update_blog_index(site_id):
    """Regenerate the blog/index.html with all published articles."""
    site_config = get_site_config(site_id)
    if not site_config:
        return False

    domain = site_config['domaine']
    site_name = site_config['nom']
    blog_path = site_config.get('blog_path', os.path.join(site_config['chemin'], 'blog'))
    categorie = site_config.get('categorie', 'seo-marketing')
    cta = CTA_CONFIG.get(categorie, CTA_CONFIG['seo-marketing'])
    index_path = os.path.join(blog_path, 'index.html')

    # Collect all articles
    articles = []
    if os.path.isdir(blog_path):
        for fname in sorted(os.listdir(blog_path), reverse=True):
            if not fname.endswith('.html') or fname == 'index.html':
                continue
            fpath = os.path.join(blog_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    head = f.read(3000)
                title_match = re.search(r'<title>(.+?)(?:\s*\|[^<]*)?</title>', head)
                desc_match = re.search(r'<meta name="description" content="(.+?)"', head)
                date_match = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', head)

                title = title_match.group(1).strip() if title_match else fname.replace('.html', '').replace('-', ' ').title()
                desc = desc_match.group(1).strip() if desc_match else ''
                date = date_match.group(1) if date_match else ''
                excerpt = desc[:120] + '...' if len(desc) > 120 else desc

                articles.append({
                    'slug': fname.replace('.html', ''),
                    'title': title,
                    'excerpt': excerpt,
                    'date': date,
                    'fname': fname,
                })
            except Exception:
                pass

    # Sort by date descending
    articles.sort(key=lambda a: a.get('date', ''), reverse=True)

    # Build cards
    cards_html = '\n'.join(
        INDEX_CARD_TEMPLATE.format(
            slug=a['slug'],
            title=html_lib.escape(a['title']),
            excerpt=html_lib.escape(a['excerpt']),
            date=a['date'],
        )
        for a in articles
    )

    index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog | {html_lib.escape(site_name)}</title>
    <meta name="description" content="Articles et conseils de {html_lib.escape(site_name)}. Restez inform&eacute; sur nos services et actualit&eacute;s.">
    <link rel="canonical" href="https://{domain}/blog/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        :root {{
            --primary: #0f172a;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --bg-light: #f0f4ff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --white: #ffffff;
            --shadow: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 20px rgba(0,0,0,0.08);
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: var(--text);
            line-height: 1.7;
            background: var(--white);
        }}
        .nav {{
            background: var(--primary);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-lg);
        }}
        .nav-inner {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
        }}
        .nav-logo {{
            color: var(--white);
            font-weight: 700;
            font-size: 1.2rem;
            text-decoration: none;
        }}
        .nav-links {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .nav-links a {{
            color: rgba(255,255,255,0.85);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        .nav-links a:hover {{
            color: var(--white);
            background: rgba(255,255,255,0.1);
        }}
        .nav-links .btn-accent {{
            background: var(--accent);
            color: var(--white) !important;
            padding: 8px 20px;
        }}
        .blog-header {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 48px 24px 32px;
        }}
        .blog-header h1 {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}
        .blog-header p {{
            color: var(--text-light);
            margin-top: 8px;
        }}
        .blog-grid {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px 60px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 24px;
        }}
        .blog-card {{
            display: block;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 28px;
            text-decoration: none;
            color: var(--text);
            transition: all 0.2s;
        }}
        .blog-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
            border-color: var(--accent);
        }}
        .blog-card h3 {{
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 8px;
        }}
        .blog-card p {{
            font-size: 0.95rem;
            color: var(--text-light);
            margin-bottom: 12px;
        }}
        .blog-card .date {{
            font-size: 0.82rem;
            color: var(--text-light);
        }}
        .footer {{
            background: var(--primary);
            color: rgba(255,255,255,0.7);
            text-align: center;
            padding: 32px 24px;
            font-size: 0.85rem;
            margin-top: 60px;
        }}
        .footer a {{
            color: rgba(255,255,255,0.9);
            text-decoration: none;
        }}
        @media (max-width: 768px) {{
            .blog-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="https://{domain}/" class="nav-logo">{html_lib.escape(site_name)}</a>
            <div class="nav-links">
                <a href="https://{domain}/">Accueil</a>
                <a href="https://{domain}/blog/">Blog</a>
                <a href="{cta['cta_url']}" class="btn-accent">{cta['cta_text']}</a>
            </div>
        </div>
    </nav>
    <div class="blog-header">
        <h1>Blog</h1>
        <p>{len(articles)} articles publi&eacute;s</p>
    </div>
    <div class="blog-grid">
{cards_html}
    </div>
    <footer class="footer">
        <p>&copy; {datetime.now().year} {html_lib.escape(site_name)}. Tous droits r&eacute;serv&eacute;s.</p>
        <p style="margin-top: 8px;">
            <a href="https://{domain}/">Accueil</a> &middot;
            <a href="https://{domain}/blog/">Blog</a>
        </p>
    </footer>
</body>
</html>"""

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)

    log(f"Updated blog index: {index_path} ({len(articles)} articles)")
    return True


def update_sitemap(site_id):
    """Add new blog URLs to the site's sitemap.xml."""
    site_config = get_site_config(site_id)
    if not site_config:
        return False

    domain = site_config['domaine']
    site_path = site_config['chemin']
    blog_path = site_config.get('blog_path', os.path.join(site_path, 'blog'))
    sitemap_path = os.path.join(site_path, 'sitemap.xml')

    # Read existing sitemap
    existing_urls = set()
    if os.path.isfile(sitemap_path):
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for match in re.finditer(r'<loc>(.+?)</loc>', content):
            existing_urls.add(match.group(1))
    else:
        content = ''

    # Find new blog URLs
    new_urls = []
    if os.path.isdir(blog_path):
        for fname in os.listdir(blog_path):
            if not fname.endswith('.html'):
                continue
            url = f"https://{domain}/blog/{fname}"
            if url not in existing_urls:
                new_urls.append(url)

    if not new_urls:
        return True

    today = datetime.now().strftime('%Y-%m-%d')

    # Build new entries
    new_entries = ''
    for url in new_urls:
        new_entries += f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
"""

    if '</urlset>' in content:
        content = content.replace('</urlset>', f'{new_entries}</urlset>')
    else:
        # Create new sitemap
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://{domain}/blog/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
{new_entries}</urlset>"""

    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(content)

    log(f"Updated sitemap: {sitemap_path} (+{len(new_urls)} URLs)")
    return True


def submit_to_google(url):
    """Submit a URL to Google for indexing.

    Note: Google deprecated the sitemap ping endpoint in June 2023.
    This now uses the Search Console Indexing API if credentials are available,
    otherwise it logs a reminder to submit manually via Search Console.
    """
    try:
        # Try Google Indexing API (requires service account JSON)
        creds_path = os.path.join(BASE_DIR, 'google-indexing-credentials.json')
        if os.path.isfile(creds_path):
            import urllib.request
            # Use Indexing API v3
            api_url = "https://indexing.googleapis.com/v3/urlNotifications:publish"
            payload = json.dumps({
                "url": url,
                "type": "URL_UPDATED"
            }).encode('utf-8')
            req = urllib.request.Request(api_url, data=payload, method='POST')
            req.add_header('Content-Type', 'application/json')
            # Note: needs OAuth2 token from service account — placeholder for now
            log(f"Google Indexing API: credentials found but OAuth not configured yet for {url}", "INFO")
            return False

        # No credentials: log reminder
        log(f"Google Indexing: submit manually via Search Console: {url}", "INFO")
        return True
    except Exception as e:
        log(f"Google indexing error: {e}", "WARNING")
        return False


def add_internal_links(site_id):
    """Add internal links to existing articles on a site."""
    site_config = get_site_config(site_id)
    if not site_config:
        return 0

    blog_path = site_config.get('blog_path', '')
    domain = site_config['domaine']
    if not os.path.isdir(blog_path):
        return 0

    # Collect all articles
    all_articles = []
    for fname in os.listdir(blog_path):
        if not fname.endswith('.html') or fname == 'index.html':
            continue
        fpath = os.path.join(blog_path, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                head = f.read(2000)
            match = re.search(r'<title>(.+?)(?:\s*\|[^<]*)?</title>', head)
            if match:
                all_articles.append((fname, match.group(1).strip()))
        except Exception:
            pass

    fixed = 0
    for fname, title in all_articles:
        fpath = os.path.join(blog_path, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if 'class="articles-connexes"' in content:
            continue

        # Pick related articles
        related = [(s, t) for s, t in all_articles if s != fname][:3]
        if not related:
            continue

        connexes_html = build_connexes_html(related, domain)

        # Insert before cta-box
        if '<div class="cta-box"' in content:
            content = content.replace('<div class="cta-box"', connexes_html + '\n        <div class="cta-box"', 1)
        elif '</article>' in content:
            content = content.replace('</article>', connexes_html + '\n</article>', 1)
        else:
            continue

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed += 1
        log(f"Added internal links to: {fname}")

    return fixed


def deploy_pending_articles(site_id=None, dry_run=False):
    """Main entry point: deploy all pending approved articles."""
    log("=" * 60)
    log("BLOG DEPLOYER: Starting deployment run")
    log("=" * 60)

    articles = get_pending_articles(site_id)
    log(f"Found {len(articles)} pending articles")

    deployed = 0
    failed = 0
    sites_updated = set()

    for article in articles:
        try:
            result = deploy_article(article, dry_run=dry_run)
            if result:
                deployed += 1
                sites_updated.add(article['site_id'])
        except Exception as e:
            log(f"Failed to deploy content #{article['id']}: {e}", "ERROR")
            failed += 1

    # Update blog indexes and sitemaps for affected sites
    if not dry_run:
        for sid in sites_updated:
            update_blog_index(sid)
            update_sitemap(sid)

        # Ping Google for each site
        config = load_config()
        for site in config.get('sites', []):
            domain = site['domaine']
            submit_to_google(f"https://{domain}/sitemap.xml")

    log("=" * 60)
    log(f"BLOG DEPLOYER DONE: {deployed} deployed, {failed} failed, {len(articles) - deployed - failed} skipped")
    log("=" * 60)

    return {"deployed": deployed, "failed": failed, "total": len(articles)}


# ═══════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Deploy approved blog articles')
    parser.add_argument('--site', type=int, help='Deploy for specific site_id only')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing files')
    parser.add_argument('--update-indexes', action='store_true', help='Only update blog index pages')
    parser.add_argument('--update-sitemaps', action='store_true', help='Only update sitemaps')
    parser.add_argument('--add-links', action='store_true', help='Add internal links to existing articles')
    args = parser.parse_args()

    if args.update_indexes:
        config = load_config()
        for i, site in enumerate(config.get('sites', []), 1):
            update_blog_index(i)
        sys.exit(0)

    if args.update_sitemaps:
        config = load_config()
        for i, site in enumerate(config.get('sites', []), 1):
            update_sitemap(i)
        sys.exit(0)

    if args.add_links:
        config = load_config()
        total = 0
        for i, site in enumerate(config.get('sites', []), 1):
            if args.site and args.site != i:
                continue
            total += add_internal_links(i)
        log(f"Internal links added to {total} articles")
        sys.exit(0)

    deploy_pending_articles(site_id=args.site, dry_run=args.dry_run)

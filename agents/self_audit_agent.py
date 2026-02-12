#!/usr/bin/env python3
"""
Self-Audit Agent - Auto-diagnostic et correction du systeme SEO
3 niveaux:
  1. AUTO-FIX: Corrections simples et sans danger (meta tags, lazy loading, defer)
  2. ALERTE SQLite: Corrections complexes en attente de confirmation humaine
  3. SYNC SSH: Rapport complet quand l'admin se connecte

Fonctionne sur TOUS les sites configures, incluant seoparai.com lui-meme.
"""

import os
import json
import sqlite3
import requests
import re
import hashlib
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from html.parser import HTMLParser
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/seo-agent/logs/self_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SelfAuditAgent')

SITES = {
    "deneigement": {
        "domain": "deneigement-excellence.ca",
        "url": "https://deneigement-excellence.ca",
        "path": "/var/www/deneigement"
    },
    "paysagement": {
        "domain": "paysagiste-excellence.ca",
        "url": "https://paysagiste-excellence.ca",
        "path": "/var/www/paysagement"
    },
    "jcpeintre": {
        "domain": "jcpeintre.com",
        "url": "https://jcpeintre.com",
        "path": "/var/www/jcpeintre.com"
    },
    "seoparai": {
        "domain": "seoparai.com",
        "url": "https://seoparai.com",
        "path": "/var/www/seoparai"
    }
}

# Classification des corrections
FIX_LEVELS = {
    "auto": "Correction automatique (safe, reversible)",
    "confirm": "Necessite confirmation humaine (complexe)",
    "manual": "Intervention manuelle requise (structurel)"
}

# Donnees business par site pour Schema LocalBusiness auto-generation
SITE_BUSINESS_DATA = {
    "jcpeintre": {
        "name": "Groupe Peinture JM Inc.",
        "alternateName": "JC Peintre",
        "types": ["LocalBusiness", "HousePainter", "HomeAndConstructionBusiness"],
        "description": "Peinture residentielle et commerciale, calfeutrage et plancher epoxy sur la Rive-Sud de Montreal depuis 15 ans.",
        "telephone": "+1-514-240-2986",
        "email": "entrepreneurpeintre@outlook.com",
        "address": {"addressLocality": "Longueuil", "addressRegion": "QC", "addressCountry": "CA"},
        "priceRange": "$$",
        "openingHours": [("Mo-Fr", "07:00", "18:00"), ("Sa", "08:00", "16:00")],
        "areaServed": ["Longueuil", "Brossard", "Boucherville", "Saint-Hubert", "Saint-Lambert", "La Prairie", "Candiac", "Chambly", "Montreal", "Laval"],
        "services": ["Peinture residentielle", "Peinture commerciale", "Calfeutrage", "Plancher epoxy"],
        "credential": "Licence RBQ 5829-2673-01",
        "rating": {"ratingValue": "5.0", "reviewCount": "3", "bestRating": "5"},
        "sameAs": ["https://www.facebook.com/PeintureJacobCouture"]
    },
    "paysagement": {
        "name": "Paysagiste Excellence",
        "types": ["LocalBusiness", "LandscapingBusiness"],
        "description": "Amenagement paysager, entretien de pelouse et travaux exterieurs sur la Rive-Sud de Montreal.",
        "telephone": "+1-438-383-7283",
        "email": "info@paysagiste-excellence.ca",
        "address": {"addressLocality": "Brossard", "addressRegion": "QC", "addressCountry": "CA"},
        "priceRange": "$$",
        "openingHours": [("Mo-Fr", "07:00", "18:00"), ("Sa", "08:00", "16:00")],
        "areaServed": ["Brossard", "Saint-Hubert", "Longueuil", "Boucherville", "La Prairie"],
        "services": ["Amenagement paysager", "Entretien pelouse", "Pave uni", "Terrassement"],
        "rating": {"ratingValue": "4.9", "reviewCount": "5", "bestRating": "5"},
        "sameAs": []
    },
    "deneigement": {
        "name": "Deneigement Excellence",
        "types": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "description": "Deneigement residentiel et commercial sur la Rive-Sud de Montreal.",
        "telephone": "+1-438-383-7283",
        "email": "info@deneigement-excellence.ca",
        "address": {"addressLocality": "Brossard", "addressRegion": "QC", "addressCountry": "CA"},
        "priceRange": "$$",
        "openingHours": [("Mo-Su", "00:00", "23:59")],
        "areaServed": ["Brossard", "Saint-Hubert", "Longueuil", "Boucherville", "La Prairie", "Candiac"],
        "services": ["Deneigement residentiel", "Deneigement commercial", "Epandage abrasifs", "Deglacage"],
        "rating": {"ratingValue": "4.8", "reviewCount": "10", "bestRating": "5"},
        "sameAs": []
    },
    "seoparai": {
        "name": "SeoAI - SEO par Intelligence Artificielle",
        "types": ["LocalBusiness", "ProfessionalService"],
        "description": "Plateforme de referencement SEO automatise par intelligence artificielle au Quebec.",
        "telephone": "+1-514-609-2882",
        "email": "michaelperron12@gmail.com",
        "address": {"addressLocality": "Montreal", "addressRegion": "QC", "addressCountry": "CA"},
        "priceRange": "$$$",
        "openingHours": [("Mo-Fr", "09:00", "17:00")],
        "areaServed": ["Montreal", "Quebec", "Canada"],
        "services": ["SEO automatise", "Optimisation par IA", "Gestion de sites web"],
        "rating": None,
        "sameAs": []
    }
}


class SelfAuditAgent:
    # IPs admin connues — pas d'alerte email si connecte depuis ces IPs
    ADMIN_USERS = ["ubuntu", "root", "michael"]

    def __init__(self, db_path: str = "/opt/seo-agent/db/seo_agent.db"):
        self.db_path = db_path
        self._init_db()

    def is_admin_connected(self) -> bool:
        """Verifie si un admin est connecte en SSH (via w command)"""
        try:
            import subprocess
            result = subprocess.run(["w", "-h"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                user = line.split()[0]
                if user in self.ADMIN_USERS:
                    return True
            return False
        except Exception:
            return False

    def get_admin_session_info(self) -> Optional[str]:
        """Retourne info sur la session admin active"""
        try:
            import subprocess
            result = subprocess.run(["w", "-h"], capture_output=True, text=True, timeout=5)
            sessions = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split()
                user = parts[0]
                if user in self.ADMIN_USERS:
                    # user + IP source
                    ip = parts[2] if len(parts) > 2 else "local"
                    sessions.append(f"{user} from {ip}")
            return "; ".join(sessions) if sessions else None
        except Exception:
            return None

    def _init_db(self):
        """Cree les tables pour le self-audit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS self_audit_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                check_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                fix_level TEXT NOT NULL,
                fix_command TEXT,
                fix_sql TEXT,
                auto_fixed BOOLEAN DEFAULT 0,
                confirmed BOOLEAN DEFAULT 0,
                executed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                fixed_at DATETIME,
                confirmed_by TEXT
            );

            CREATE TABLE IF NOT EXISTS self_audit_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                checks_total INTEGER DEFAULT 0,
                issues_found INTEGER DEFAULT 0,
                auto_fixed INTEGER DEFAULT 0,
                pending_confirm INTEGER DEFAULT 0,
                manual_required INTEGER DEFAULT 0,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS self_audit_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_audit_site ON self_audit_results(site_id);
            CREATE INDEX IF NOT EXISTS idx_audit_level ON self_audit_results(fix_level);
            CREATE INDEX IF NOT EXISTS idx_audit_executed ON self_audit_results(executed);
        """)
        conn.commit()
        conn.close()

    # =========================================
    # BACKUP avant toute modification
    # =========================================

    def _backup_file(self, site_id: str, file_path: str) -> Optional[str]:
        """Cree un backup avant modification"""
        if not os.path.exists(file_path):
            return None
        backup_dir = f"/opt/seo-agent/backups/{site_id}/{datetime.now().strftime('%Y%m%d')}"
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, os.path.basename(file_path) + f".{datetime.now().strftime('%H%M%S')}.bak")
        shutil.copy2(file_path, backup_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO self_audit_backups (site_id, file_path, backup_path) VALUES (?, ?, ?)",
            (site_id, file_path, backup_path)
        )
        conn.commit()
        conn.close()
        return backup_path

    # =========================================
    # ENREGISTREMENT DES RESULTATS
    # =========================================

    def _record_issue(self, site_id: str, check_type: str, severity: str,
                      message: str, fix_level: str, details: str = None,
                      fix_command: str = None, fix_sql: str = None,
                      auto_fixed: bool = False) -> int:
        """Enregistre un probleme trouve"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO self_audit_results
            (site_id, check_type, severity, message, details, fix_level, fix_command, fix_sql, auto_fixed, fixed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, check_type, severity, message, details, fix_level,
              fix_command, fix_sql, auto_fixed,
              datetime.now().isoformat() if auto_fixed else None))
        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Aussi creer une alerte dans mon_alerts pour le dashboard
        self._create_dashboard_alert(site_id, check_type, severity, message, auto_fixed=auto_fixed)

        return issue_id

    def _create_dashboard_alert(self, site_id: str, alert_type: str,
                                severity: str, message: str,
                                auto_fixed: bool = False):
        """Cree une alerte visible dans le dashboard existant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Eviter les doublons
        cursor.execute("""
            SELECT id FROM mon_alerts
            WHERE site_id = ? AND alert_type = ? AND message = ? AND resolved = 0
            AND created_at > datetime('now', '-6 hours')
        """, (site_id, f"self_audit_{alert_type}", message))
        existing = cursor.fetchone()
        if not existing:
            status = "auto_fixed" if auto_fixed else "new"
            cursor.execute("""
                INSERT INTO mon_alerts (site_id, alert_type, severity, message, details, source_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (site_id, f"self_audit_{alert_type}", severity, message,
                  f"Detecte par Self-Audit Agent le {datetime.now().strftime('%Y-%m-%d %H:%M')} | Status: {status}",
                  "self_audit_agent"))
            # Si auto-fixed, marquer comme resolu immediatement
            if auto_fixed:
                cursor.execute("""
                    UPDATE mon_alerts SET resolved = 1, resolved_at = datetime('now'),
                    corrected_by = 'self_audit_agent', corrected_at = datetime('now')
                    WHERE id = last_insert_rowid()
                """)
            conn.commit()
        conn.close()

    # =========================================
    # CHECKS HTML (fichiers locaux)
    # =========================================

    def check_html_files(self, site_id: str) -> Dict:
        """Analyse tous les fichiers HTML d'un site"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        path = SITES[site_id]["path"]
        if not os.path.exists(path):
            return {"error": f"Path inexistant: {path}"}

        results = {"checked": 0, "auto_fixed": 0, "pending": 0, "issues": []}

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'vendor', 'venv']]
            for fname in files:
                if not fname.endswith(('.html', '.htm', '.php')):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    if len(content) < 50:
                        continue
                    results["checked"] += 1
                    file_issues = self._audit_html(site_id, fpath, content)
                    results["issues"].extend(file_issues)
                    for issue in file_issues:
                        if issue["auto_fixed"]:
                            results["auto_fixed"] += 1
                        else:
                            results["pending"] += 1
                except Exception as e:
                    logger.error(f"Erreur lecture {fpath}: {e}")

        return results

    def _audit_html(self, site_id: str, file_path: str, content: str) -> List[Dict]:
        """Audit complet d'un fichier HTML — auto-fix ou alerte"""
        issues = []
        modified = False
        new_content = content

        # ---- AUTO-FIX: Meta description manquante ----
        if '<meta name="description"' not in content and '<head' in content:
            domain = SITES[site_id]["domain"]
            page_name = os.path.basename(file_path).replace('.html', '').replace('.htm', '').replace('.php', '')
            default_desc = f"{domain} - {page_name.replace('-', ' ').replace('_', ' ').title()}"
            meta_tag = f'<meta name="description" content="{default_desc}">'

            # AUTO-FIX: Inserer apres <head> ou apres le dernier <meta
            if '</head>' in new_content:
                new_content = new_content.replace('</head>', f'    {meta_tag}\n</head>')
                modified = True
                issues.append(self._record_and_return(
                    site_id, "meta_description", "high",
                    f"Meta description manquante: {file_path}",
                    "auto", file_path, meta_tag, auto_fixed=True
                ))

        # ---- AUTO-FIX: Lazy loading sur images ----
        img_pattern = re.compile(r'<img\s+(?![^>]*loading=)[^>]*src=', re.IGNORECASE)
        if img_pattern.search(new_content):
            new_content = re.sub(
                r'<img\s+(?![^>]*loading=)([^>]*)(src=)',
                r'<img loading="lazy" \1\2',
                new_content,
                flags=re.IGNORECASE
            )
            if new_content != content:
                modified = True
                count = len(img_pattern.findall(content))
                issues.append(self._record_and_return(
                    site_id, "lazy_loading", "medium",
                    f"{count} images sans lazy loading: {file_path}",
                    "auto", file_path,
                    f"Ajout loading='lazy' sur {count} images",
                    auto_fixed=True
                ))

        # ---- AUTO-FIX: defer sur scripts ----
        script_pattern = re.compile(
            r'<script\s+(?![^>]*(defer|async|type=["\']module))[^>]*src=',
            re.IGNORECASE
        )
        if script_pattern.search(new_content):
            new_content = re.sub(
                r'<script\s+(?![^>]*(defer|async|type=["\']module))([^>]*)(src=)',
                r'<script defer \2\3',
                new_content,
                flags=re.IGNORECASE
            )
            if new_content != (content if not modified else new_content):
                modified = True
                issues.append(self._record_and_return(
                    site_id, "script_defer", "medium",
                    f"Scripts bloquants sans defer: {file_path}",
                    "auto", file_path,
                    "Ajout defer sur scripts bloquants",
                    auto_fixed=True
                ))

        # ---- AUTO-FIX: DOCTYPE manquant ----
        if not content.strip().lower().startswith('<!doctype'):
            if '<html' in content.lower():
                new_content = '<!DOCTYPE html>\n' + new_content
                modified = True
                issues.append(self._record_and_return(
                    site_id, "doctype", "medium",
                    f"DOCTYPE manquant: {file_path}",
                    "auto", file_path,
                    "Ajout <!DOCTYPE html>",
                    auto_fixed=True
                ))

        # ---- AUTO-FIX: charset manquant ----
        if '<meta charset=' not in content.lower() and '<meta http-equiv="content-type"' not in content.lower():
            if '</head>' in new_content:
                new_content = new_content.replace('</head>', '    <meta charset="UTF-8">\n</head>')
                modified = True
                issues.append(self._record_and_return(
                    site_id, "charset", "medium",
                    f"Charset manquant: {file_path}",
                    "auto", file_path,
                    'Ajout <meta charset="UTF-8">',
                    auto_fixed=True
                ))

        # ---- AUTO-FIX: viewport manquant ----
        if '<meta name="viewport"' not in content.lower():
            if '</head>' in new_content:
                viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
                new_content = new_content.replace('</head>', f'    {viewport}\n</head>')
                modified = True
                issues.append(self._record_and_return(
                    site_id, "viewport", "high",
                    f"Viewport manquant: {file_path}",
                    "auto", file_path,
                    "Ajout meta viewport",
                    auto_fixed=True
                ))

        # ---- AUTO-FIX: Schema LocalBusiness (page principale seulement) ----
        is_main_page = os.path.basename(file_path) in ('index.html', 'landing.html')

        if is_main_page and site_id in SITE_BUSINESS_DATA:
            biz = SITE_BUSINESS_DATA[site_id]

            # Verifier si LocalBusiness existe deja dans le JSON-LD
            has_local_business = False
            existing_schemas = re.finditer(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                new_content, re.DOTALL
            )
            for match in existing_schemas:
                try:
                    schema_data = json.loads(match.group(1).strip())
                    schema_type = schema_data.get('@type', '')
                    if isinstance(schema_type, list):
                        if 'LocalBusiness' in schema_type:
                            has_local_business = True
                    elif schema_type == 'LocalBusiness':
                        has_local_business = True
                except (json.JSONDecodeError, AttributeError):
                    pass

            if not has_local_business and '</head>' in new_content:
                # Generer schema LocalBusiness complet
                local_schema = {
                    "@context": "https://schema.org",
                    "@type": biz["types"],
                    "@id": f"{SITES[site_id]['url']}/#localbusiness",
                    "name": biz["name"],
                    "url": SITES[site_id]["url"],
                    "description": biz["description"],
                    "telephone": biz["telephone"],
                    "email": biz.get("email", ""),
                    "address": {
                        "@type": "PostalAddress",
                        **biz["address"]
                    },
                    "priceRange": biz.get("priceRange", "$$"),
                    "areaServed": [
                        {"@type": "City", "name": city}
                        for city in biz.get("areaServed", [])
                    ],
                    "hasOfferCatalog": {
                        "@type": "OfferCatalog",
                        "name": "Services",
                        "itemListElement": [
                            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": svc}}
                            for svc in biz.get("services", [])
                        ]
                    }
                }
                # Horaires d'ouverture
                if biz.get("openingHours"):
                    local_schema["openingHoursSpecification"] = []
                    for days, opens, closes in biz["openingHours"]:
                        local_schema["openingHoursSpecification"].append({
                            "@type": "OpeningHoursSpecification",
                            "dayOfWeek": days,
                            "opens": opens,
                            "closes": closes
                        })
                # Licence/credential
                if biz.get("credential"):
                    local_schema["hasCredential"] = {
                        "@type": "EducationalOccupationalCredential",
                        "credentialCategory": "license",
                        "name": biz["credential"]
                    }
                # AggregateRating
                if biz.get("rating"):
                    local_schema["aggregateRating"] = {
                        "@type": "AggregateRating",
                        **biz["rating"]
                    }
                # Reseaux sociaux
                if biz.get("sameAs"):
                    local_schema["sameAs"] = biz["sameAs"]
                if biz.get("alternateName"):
                    local_schema["alternateName"] = biz["alternateName"]

                schema_json = json.dumps(local_schema, indent=2, ensure_ascii=False)
                schema_tag = f'\n    <script type="application/ld+json">\n{schema_json}\n    </script>'
                new_content = new_content.replace('</head>', f'{schema_tag}\n</head>')
                modified = True
                issues.append(self._record_and_return(
                    site_id, "schema_local_business", "critical",
                    f"Schema LocalBusiness+AggregateRating AUTO-INJECTE: {file_path}",
                    "auto", file_path,
                    f"JSON-LD LocalBusiness avec {len(biz.get('services',[]))} services, rating, horaires",
                    auto_fixed=True
                ))
                logger.info(f"AUTO-FIX Schema LocalBusiness injecte dans {file_path}")

        elif 'application/ld+json' not in content:
            # Pas de JSON-LD du tout sur page non-principale — CONFIRM
            schema_example = json.dumps({
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": SITES[site_id]["domain"],
                "url": SITES[site_id].get("url", f"https://{SITES[site_id]['domain']}")
            }, indent=2)
            fix_cmd = f'# Ajouter avant </head> dans {file_path}:\n<script type="application/ld+json">\n{schema_example}\n</script>'
            issues.append(self._record_and_return(
                site_id, "schema_markup", "high",
                f"Schema markup (JSON-LD) manquant: {file_path}",
                "confirm", file_path, fix_cmd,
                auto_fixed=False
            ))

        # ---- DETECT: Liens internes insuffisants (page principale) ----
        if is_main_page:
            internal_links = re.findall(
                r'<a[^>]+href=["\'](?!#|tel:|mailto:|https?://|javascript:)([^"\'>\s]+)["\']',
                content, re.IGNORECASE
            )
            unique_links = set(internal_links)
            if len(unique_links) < 5:
                issues.append(self._record_and_return(
                    site_id, "internal_links_low", "high",
                    f"Seulement {len(unique_links)} liens internes uniques (min 5): {file_path}",
                    "confirm", file_path,
                    f"Liens trouves: {', '.join(list(unique_links)[:10])}. Ajouter liens vers pages cles.",
                    auto_fixed=False
                ))

        # ---- DETECT: Listes structurees <ul>/<li> absentes (page principale) ----
        if is_main_page:
            has_lists = '<ul' in content.lower() or '<ol' in content.lower()
            if not has_lists:
                issues.append(self._record_and_return(
                    site_id, "no_structured_lists", "high",
                    f"Aucune liste structuree <ul>/<li> trouvee: {file_path}",
                    "confirm", file_path,
                    "Convertir les grilles de services/features en <ul><li> pour SEO semantique",
                    auto_fixed=False
                ))

        # ---- CONFIRM: Open Graph manquant ----
        if 'og:title' not in content and 'og:description' not in content:
            fix_cmd = f"""# Ajouter dans <head> de {file_path}:
<meta property="og:title" content="TITRE_PAGE">
<meta property="og:description" content="DESCRIPTION_PAGE">
<meta property="og:type" content="website">
<meta property="og:url" content="URL_PAGE">
<meta property="og:image" content="URL_IMAGE">"""
            issues.append(self._record_and_return(
                site_id, "open_graph", "medium",
                f"Open Graph meta tags manquants: {file_path}",
                "confirm", file_path, fix_cmd,
                auto_fixed=False
            ))

        # ---- CONFIRM: Alt text manquant sur images ----
        img_no_alt = re.findall(r'<img\s+(?![^>]*alt=)[^>]*>', content, re.IGNORECASE)
        if img_no_alt:
            fix_cmd = f"# {len(img_no_alt)} images sans alt dans {file_path}\n# Ajouter alt='description' sur chaque image"
            issues.append(self._record_and_return(
                site_id, "img_alt", "high",
                f"{len(img_no_alt)} images sans attribut alt: {file_path}",
                "confirm", file_path, fix_cmd,
                auto_fixed=False
            ))

        # ---- CONFIRM: Canonical URL manquant ----
        if '<link rel="canonical"' not in content:
            fix_cmd = f'# Ajouter dans <head> de {file_path}:\n<link rel="canonical" href="URL_DE_LA_PAGE">'
            issues.append(self._record_and_return(
                site_id, "canonical", "medium",
                f"Canonical URL manquant: {file_path}",
                "confirm", file_path, fix_cmd,
                auto_fixed=False
            ))

        # Sauvegarder les auto-fix
        if modified:
            self._backup_file(site_id, file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"AUTO-FIX applique: {file_path}")

        return issues

    def _record_and_return(self, site_id: str, check_type: str, severity: str,
                           message: str, fix_level: str, file_path: str,
                           fix_detail: str, auto_fixed: bool = False) -> Dict:
        """Enregistre et retourne un issue"""
        issue_id = self._record_issue(
            site_id, check_type, severity, message, fix_level,
            details=file_path, fix_command=fix_detail,
            auto_fixed=auto_fixed
        )
        return {
            "id": issue_id,
            "check_type": check_type,
            "severity": severity,
            "message": message,
            "fix_level": fix_level,
            "auto_fixed": auto_fixed
        }

    # =========================================
    # CHECK LIVE SITE (HTTP)
    # =========================================

    def check_live_site(self, site_id: str) -> Dict:
        """Verifie le site en live via HTTP"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        url = SITES[site_id].get("url", f"https://{SITES[site_id]['domain']}")
        results = {"site_id": site_id, "url": url, "issues": []}

        try:
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "SeoAI-SelfAudit/1.0"
            })
            html = resp.text

            # Verifier sitemap
            sitemap_url = f"{url}/sitemap.xml"
            try:
                sitemap_resp = requests.get(sitemap_url, timeout=10)
                if sitemap_resp.status_code != 200:
                    results["issues"].append(self._record_and_return(
                        site_id, "sitemap_missing", "high",
                        f"Sitemap.xml introuvable: {sitemap_url}",
                        "confirm", sitemap_url,
                        f"Creer sitemap.xml a la racine de {SITES[site_id]['path']}",
                        auto_fixed=False
                    ))
                else:
                    # Verifier que le sitemap pointe vers le bon domaine
                    domain = SITES[site_id]["domain"]
                    if domain not in sitemap_resp.text:
                        results["issues"].append(self._record_and_return(
                            site_id, "sitemap_domain_mismatch", "critical",
                            f"Sitemap pointe vers mauvais domaine (pas {domain})",
                            "confirm", sitemap_url,
                            f"Corriger les URLs dans sitemap.xml pour pointer vers {domain}",
                            auto_fixed=False
                        ))
            except Exception:
                pass

            # Verifier robots.txt
            robots_url = f"{url}/robots.txt"
            try:
                robots_resp = requests.get(robots_url, timeout=10)
                if robots_resp.status_code != 200:
                    results["issues"].append(self._record_and_return(
                        site_id, "robots_missing", "high",
                        f"robots.txt introuvable: {robots_url}",
                        "confirm", robots_url,
                        f"Creer robots.txt a la racine de {SITES[site_id]['path']}",
                        auto_fixed=False
                    ))
            except Exception:
                pass

            # Verifier HTTPS redirect
            try:
                http_resp = requests.get(
                    url.replace("https://", "http://"),
                    timeout=10, allow_redirects=False
                )
                if http_resp.status_code not in (301, 302, 308):
                    results["issues"].append(self._record_and_return(
                        site_id, "https_redirect", "critical",
                        f"Pas de redirect HTTP -> HTTPS",
                        "confirm", url,
                        "Configurer redirect 301 HTTP vers HTTPS dans nginx",
                        auto_fixed=False
                    ))
            except Exception:
                pass

            # Verifier headers de securite
            headers = resp.headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000"
            }
            for header, recommended in security_headers.items():
                if header not in headers:
                    results["issues"].append(self._record_and_return(
                        site_id, "security_header", "medium",
                        f"Header de securite manquant: {header}",
                        "confirm", url,
                        f"Ajouter dans nginx: add_header {header} \"{recommended}\";",
                        auto_fixed=False
                    ))

            # ---- SECURITY CHECKS ----

            # Verifier fichiers sensibles exposes
            sensitive_paths = [
                "/.env", "/.git/config", "/wp-config.php", "/config.yaml",
                "/db/seo_agent.db", "/.htpasswd", "/backup.sql", "/dump.sql",
                "/phpinfo.php", "/server-status", "/adminer.php"
            ]
            for spath in sensitive_paths:
                try:
                    check_url = f"{url}{spath}"
                    check_resp = requests.get(check_url, timeout=5, allow_redirects=False)
                    if check_resp.status_code == 200:
                        results["issues"].append(self._record_and_return(
                            site_id, "exposed_file", "critical",
                            f"SECURITE: Fichier sensible accessible: {check_url}",
                            "confirm", check_url,
                            f"Bloquer dans nginx: location {spath} {{ return 404; }}",
                            auto_fixed=False
                        ))
                except Exception:
                    pass

            # Verifier directory listing
            test_dirs = ["/images/", "/css/", "/js/", "/uploads/", "/backup/"]
            for tdir in test_dirs:
                try:
                    dir_url = f"{url}{tdir}"
                    dir_resp = requests.get(dir_url, timeout=5)
                    if dir_resp.status_code == 200 and ("Index of" in dir_resp.text or "<title>Index" in dir_resp.text):
                        results["issues"].append(self._record_and_return(
                            site_id, "directory_listing", "high",
                            f"SECURITE: Directory listing actif: {dir_url}",
                            "confirm", dir_url,
                            "Ajouter dans nginx: autoindex off;",
                            auto_fixed=False
                        ))
                except Exception:
                    pass

            # Verifier ports ouverts dangereux
            domain = SITES[site_id]["domain"]
            dangerous_ports = {8080: "Dashboard", 8002: "API", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB"}
            import socket
            for port, service in dangerous_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result_port = sock.connect_ex((domain, port))
                    sock.close()
                    if result_port == 0 and port not in (80, 443):
                        results["issues"].append(self._record_and_return(
                            site_id, "open_port", "critical",
                            f"SECURITE: Port {port} ({service}) ouvert sur {domain}",
                            "confirm", f"{domain}:{port}",
                            f"Fermer port {port} avec UFW: sudo ufw deny {port}",
                            auto_fixed=False
                        ))
                except Exception:
                    pass

            # Verifier si le serveur expose sa version
            server_header = headers.get("Server", "")
            if server_header and any(v in server_header.lower() for v in ["nginx/", "apache/", "php/"]):
                results["issues"].append(self._record_and_return(
                    site_id, "server_version_exposed", "medium",
                    f"SECURITE: Version serveur exposee: {server_header}",
                    "auto", url,
                    "Ajouter dans nginx: server_tokens off;",
                    auto_fixed=False
                ))

            # Response time
            response_ms = resp.elapsed.total_seconds() * 1000
            if response_ms > 3000:
                results["issues"].append(self._record_and_return(
                    site_id, "slow_response", "high",
                    f"Site lent: {round(response_ms)}ms (seuil: 3000ms)",
                    "manual", url,
                    "Optimiser: cache nginx, compression, images, CDN",
                    auto_fixed=False
                ))

        except Exception as e:
            results["issues"].append(self._record_and_return(
                site_id, "site_down", "critical",
                f"Site inaccessible: {url} - {str(e)}",
                "manual", url,
                f"Verifier serveur et nginx pour {url}",
                auto_fixed=False
            ))

        return results

    # =========================================
    # AUDIT COMPLET D'UN SITE
    # =========================================

    def full_audit(self, site_id: str) -> Dict:
        """Audit complet: fichiers locaux + site live"""
        logger.info(f"=== AUDIT COMPLET: {site_id} ===")
        start = datetime.now()

        results = {
            "site_id": site_id,
            "domain": SITES.get(site_id, {}).get("domain", "inconnu"),
            "started_at": start.isoformat(),
            "html_audit": {},
            "live_audit": {},
            "summary": {}
        }

        # Audit fichiers HTML locaux
        results["html_audit"] = self.check_html_files(site_id)

        # Audit site live
        results["live_audit"] = self.check_live_site(site_id)

        # Resume
        all_issues = results["html_audit"].get("issues", []) + results["live_audit"].get("issues", [])
        results["summary"] = {
            "total_issues": len(all_issues),
            "auto_fixed": sum(1 for i in all_issues if i.get("auto_fixed")),
            "pending_confirm": sum(1 for i in all_issues if i.get("fix_level") == "confirm"),
            "manual_required": sum(1 for i in all_issues if i.get("fix_level") == "manual"),
            "critical": sum(1 for i in all_issues if i.get("severity") == "critical"),
            "high": sum(1 for i in all_issues if i.get("severity") == "high"),
            "medium": sum(1 for i in all_issues if i.get("severity") == "medium"),
            "duration_seconds": (datetime.now() - start).total_seconds()
        }

        # Log du run
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO self_audit_runs
            (site_id, checks_total, issues_found, auto_fixed, pending_confirm, manual_required, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            site_id,
            results["html_audit"].get("checked", 0),
            results["summary"]["total_issues"],
            results["summary"]["auto_fixed"],
            results["summary"]["pending_confirm"],
            results["summary"]["manual_required"]
        ))
        conn.commit()
        conn.close()

        logger.info(f"Audit {site_id}: {results['summary']['total_issues']} issues, "
                     f"{results['summary']['auto_fixed']} auto-fixes, "
                     f"{results['summary']['pending_confirm']} en attente")

        return results

    def full_audit_all(self) -> Dict:
        """Audit complet de TOUS les sites"""
        results = {}
        for site_id in SITES:
            results[site_id] = self.full_audit(site_id)
        return results

    # =========================================
    # RAPPORT SSH - Ce que l'admin voit en se connectant
    # =========================================

    def get_ssh_report(self) -> str:
        """Genere le rapport pour la connexion SSH"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        report = []
        report.append("=" * 70)
        report.append("  SEOAI SELF-AUDIT — RAPPORT DE SYNC")
        report.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)

        # Corrections auto appliquees recemment
        cursor.execute("""
            SELECT site_id, check_type, message, fixed_at
            FROM self_audit_results
            WHERE auto_fixed = 1 AND fixed_at > datetime('now', '-24 hours')
            ORDER BY fixed_at DESC
        """)
        auto_fixes = cursor.fetchall()
        if auto_fixes:
            report.append(f"\n  AUTO-CORRIGES (derniers 24h): {len(auto_fixes)}")
            report.append("  " + "-" * 50)
            for fix in auto_fixes:
                report.append(f"  [OK] {fix[0]} | {fix[1]} | {fix[2][:60]}")

        # En attente de confirmation
        cursor.execute("""
            SELECT id, site_id, check_type, severity, message, fix_command
            FROM self_audit_results
            WHERE fix_level = 'confirm' AND confirmed = 0 AND executed = 0
            ORDER BY
                CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
        """)
        pending = cursor.fetchall()
        if pending:
            report.append(f"\n  EN ATTENTE DE CONFIRMATION: {len(pending)}")
            report.append("  " + "-" * 50)
            for p in pending:
                report.append(f"\n  [{p[3].upper()}] #{p[0]} — {p[1]} | {p[2]}")
                report.append(f"  Message: {p[4][:80]}")
                if p[5]:
                    report.append(f"  Fix: {p[5][:100]}")
                report.append(f"  -> Pour approuver: SELECT confirm_fix({p[0]});")

        # Interventions manuelles
        cursor.execute("""
            SELECT id, site_id, check_type, severity, message, fix_command
            FROM self_audit_results
            WHERE fix_level = 'manual' AND executed = 0
            ORDER BY created_at DESC
        """)
        manual = cursor.fetchall()
        if manual:
            report.append(f"\n  INTERVENTION MANUELLE REQUISE: {len(manual)}")
            report.append("  " + "-" * 50)
            for m in manual:
                report.append(f"\n  [{m[3].upper()}] #{m[0]} — {m[1]} | {m[2]}")
                if m[5]:
                    report.append(f"  Action: {m[5][:100]}")

        # Stats globales
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN auto_fixed = 1 THEN 1 ELSE 0 END) as fixed,
                SUM(CASE WHEN fix_level = 'confirm' AND confirmed = 0 THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN fix_level = 'manual' AND executed = 0 THEN 1 ELSE 0 END) as manual
            FROM self_audit_results
        """)
        stats = cursor.fetchone()
        conn.close()

        report.append(f"\n  STATS GLOBALES")
        report.append("  " + "-" * 50)
        if stats:
            report.append(f"  Total issues detectees: {stats[0]}")
            report.append(f"  Auto-corriges:          {stats[1]}")
            report.append(f"  En attente confirm:     {stats[2]}")
            report.append(f"  Manuels:                {stats[3]}")

        report.append("\n" + "=" * 70)
        report.append("  COMMANDES RAPIDES:")
        report.append("  python3 self_audit_agent.py audit          # Audit complet")
        report.append("  python3 self_audit_agent.py report         # Ce rapport")
        report.append("  python3 self_audit_agent.py confirm <id>   # Confirmer un fix")
        report.append("  python3 self_audit_agent.py confirm-all    # Confirmer tous")
        report.append("  python3 self_audit_agent.py pending-sql    # SQL des fixes en attente")
        report.append("=" * 70)

        return "\n".join(report)

    # =========================================
    # CONFIRMER ET EXECUTER LES FIXES
    # =========================================

    def confirm_fix(self, fix_id: int, confirmed_by: str = "ssh_admin") -> Dict:
        """Confirme un fix en attente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE self_audit_results
            SET confirmed = 1, confirmed_by = ?, fixed_at = datetime('now')
            WHERE id = ? AND fix_level = 'confirm'
        """, (confirmed_by, fix_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return {"status": "confirmed" if affected > 0 else "not_found", "id": fix_id}

    def confirm_all(self, confirmed_by: str = "ssh_admin") -> Dict:
        """Confirme tous les fixes en attente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE self_audit_results
            SET confirmed = 1, confirmed_by = ?, fixed_at = datetime('now')
            WHERE fix_level = 'confirm' AND confirmed = 0
        """, (confirmed_by,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return {"status": "confirmed_all", "count": affected}

    def get_pending_sql(self) -> str:
        """Genere les SQL des fixes en attente — pret a copier-coller"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, site_id, check_type, message, fix_command
            FROM self_audit_results
            WHERE fix_level = 'confirm' AND confirmed = 0 AND executed = 0
            ORDER BY
                CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END
        """)
        rows = cursor.fetchall()
        conn.close()

        sql_lines = []
        sql_lines.append("-- ==========================================")
        sql_lines.append("-- FIXES EN ATTENTE DE CONFIRMATION")
        sql_lines.append(f"-- Genere le {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        sql_lines.append("-- ==========================================\n")

        for r in rows:
            sql_lines.append(f"-- #{r[0]} | {r[1]} | {r[2]} | {r[3][:60]}")
            if r[4]:
                sql_lines.append(f"-- FIX: {r[4][:200]}")
            sql_lines.append(f"UPDATE self_audit_results SET confirmed = 1, confirmed_by = 'ssh_sync', fixed_at = datetime('now') WHERE id = {r[0]};")
            sql_lines.append("")

        sql_lines.append("-- Pour tout confirmer d'un coup:")
        sql_lines.append("-- UPDATE self_audit_results SET confirmed = 1, confirmed_by = 'ssh_sync', fixed_at = datetime('now') WHERE fix_level = 'confirm' AND confirmed = 0;")

        return "\n".join(sql_lines)


    # =========================================
    # EMAIL NOTIFICATIONS (Gmail SMTP)
    # =========================================

    def send_email(self, subject: str, body_html: str) -> bool:
        """Envoie un email via postfix local (alerts@seoparai.com)"""
        from_addr = os.getenv("SEOAI_EMAIL_FROM", "alerts@seoparai.com")
        to_addr = os.getenv("SEOAI_EMAIL_TO", "michaelperron12@gmail.com")

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"SeoAI Alerts <{from_addr}>"
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg["Reply-To"] = "alerts@seoparai.com"

            text_body = re.sub(r'<[^>]+>', '', body_html)
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            # Postfix local (localhost:25) — pas besoin de login
            with smtplib.SMTP("localhost", 25) as server:
                server.send_message(msg)

            logger.info(f"Email envoye: {subject} -> {to_addr}")
            return True
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False

    def _build_audit_email(self, results: Dict) -> Tuple[str, str]:
        """Construit le sujet et body HTML du email d'audit"""
        total_issues = 0
        total_auto = 0
        total_pending = 0
        total_critical = 0

        for site_id, data in results.items():
            if isinstance(data, dict) and "summary" in data:
                s = data["summary"]
                total_issues += s.get("total_issues", 0)
                total_auto += s.get("auto_fixed", 0)
                total_pending += s.get("pending_confirm", 0)
                total_critical += s.get("critical", 0)

        # Sujet
        if total_critical > 0:
            subject = f"🔴 CRITICAL: {total_critical} alertes critiques — SeoAI Self-Audit"
        elif total_pending > 0:
            subject = f"🟡 {total_pending} fixes en attente de confirmation — SeoAI"
        elif total_auto > 0:
            subject = f"🟢 {total_auto} corrections auto appliquees — SeoAI"
        else:
            subject = "✅ Aucun probleme detecte — SeoAI Self-Audit"

        # Body HTML
        html = f"""
        <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
        <div style="background: #1e3a5f; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin:0; font-size: 22px;">SeoAI — Self-Audit Report</h1>
            <p style="margin:5px 0 0; opacity:0.8;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6;">
            <h2 style="margin-top:0;">Resume</h2>
            <table style="width:100%; border-collapse:collapse;">
                <tr><td style="padding:8px; border-bottom:1px solid #ddd;">Total issues</td>
                    <td style="padding:8px; border-bottom:1px solid #ddd; font-weight:bold; text-align:right;">{total_issues}</td></tr>
                <tr><td style="padding:8px; border-bottom:1px solid #ddd;">Auto-corriges</td>
                    <td style="padding:8px; border-bottom:1px solid #ddd; color:green; font-weight:bold; text-align:right;">{total_auto}</td></tr>
                <tr><td style="padding:8px; border-bottom:1px solid #ddd;">En attente confirmation</td>
                    <td style="padding:8px; border-bottom:1px solid #ddd; color:orange; font-weight:bold; text-align:right;">{total_pending}</td></tr>
                <tr><td style="padding:8px;">Critiques</td>
                    <td style="padding:8px; color:red; font-weight:bold; text-align:right;">{total_critical}</td></tr>
            </table>
        </div>
        """

        # Detail par site
        for site_id, data in results.items():
            if not isinstance(data, dict) or "summary" not in data:
                continue
            s = data["summary"]
            domain = SITES.get(site_id, {}).get("domain", site_id)

            color = "#dc3545" if s.get("critical", 0) > 0 else "#ffc107" if s.get("pending_confirm", 0) > 0 else "#28a745"

            html += f"""
            <div style="border: 1px solid #dee2e6; margin-top: 15px; border-radius: 8px; overflow:hidden;">
                <div style="background: {color}; color: white; padding: 12px;">
                    <strong>{domain}</strong> — {s['total_issues']} issues
                </div>
                <div style="padding: 12px;">
            """

            # Lister les issues
            all_issues = data.get("html_audit", {}).get("issues", []) + data.get("live_audit", {}).get("issues", [])
            for issue in all_issues[:10]:
                icon = "✅" if issue.get("auto_fixed") else "⏳" if issue.get("fix_level") == "confirm" else "🔧"
                sev_color = {"critical": "#dc3545", "high": "#fd7e14", "medium": "#ffc107"}.get(issue.get("severity", ""), "#6c757d")
                html += f"""
                    <div style="padding:6px 0; border-bottom:1px solid #eee;">
                        {icon} <span style="color:{sev_color}; font-weight:bold;">[{issue.get('severity','').upper()}]</span>
                        {issue.get('check_type','')} — {issue.get('message','')[:80]}
                    </div>
                """

            if len(all_issues) > 10:
                html += f"<p style='color:#6c757d;'>... et {len(all_issues) - 10} autres</p>"

            html += "</div></div>"

        # Footer avec actions
        html += f"""
        <div style="background: #e9ecef; padding: 20px; margin-top: 15px; border-radius: 0 0 8px 8px;">
            <h3 style="margin-top:0;">Actions rapides (SSH)</h3>
            <code style="display:block; background:#343a40; color:#f8f9fa; padding:12px; border-radius:4px; font-size:13px;">
python3 self_audit_agent.py report       # Rapport complet<br>
python3 self_audit_agent.py pending-sql  # SQL des fixes<br>
python3 self_audit_agent.py confirm-all  # Approuver tout
            </code>
            <p style="margin-top:15px; font-size:12px; color:#6c757d;">
                Dashboard: <a href="http://148.113.194.234:8080/">http://148.113.194.234:8080/</a>
            </p>
        </div>
        </body></html>
        """

        return subject, html

    def send_audit_report(self, results: Dict) -> bool:
        """Envoie le rapport d'audit par email"""
        subject, html = self._build_audit_email(results)
        return self.send_email(subject, html)

    def send_critical_alert(self, site_id: str, message: str) -> bool:
        """Envoie une alerte critique instantanee"""
        subject = f"🔴 ALERTE CRITIQUE: {SITES.get(site_id, {}).get('domain', site_id)}"
        html = f"""
        <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #dc3545; color: white; padding: 20px; border-radius: 8px;">
            <h2 style="margin:0;">ALERTE CRITIQUE</h2>
            <p style="margin:10px 0 0;"><strong>Site:</strong> {SITES.get(site_id, {}).get('domain', site_id)}</p>
            <p style="margin:5px 0;"><strong>Message:</strong> {message}</p>
            <p style="margin:5px 0;"><strong>Heure:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <p style="margin-top:15px;">Connecte-toi en SSH pour investiguer:</p>
        <code style="display:block; background:#343a40; color:#f8f9fa; padding:12px; border-radius:4px;">
ssh root@148.113.194.234<br>
python3 /opt/seo-agent/self_audit_agent.py report
        </code>
        </body></html>
        """
        return self.send_email(subject, html)

    def full_audit_with_email(self, site_id: str = None) -> Dict:
        """Audit complet + envoi email automatique (sauf si admin connecte SSH)"""
        if site_id:
            results = {site_id: self.full_audit(site_id)}
        else:
            results = self.full_audit_all()

        # Checker si admin est connecte en SSH
        admin_connected = self.is_admin_connected()
        admin_info = self.get_admin_session_info()

        if admin_connected:
            logger.info(f"Admin connecte SSH ({admin_info}) — emails supprimes, issues en SQLite seulement")
            # Sauvegarder dans SQLite qu'on a skip les emails
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO self_audit_runs (site_id, checks_total, issues_found, auto_fixed, pending_confirm, manual_required, completed_at)
                VALUES ('_email_skip', 0, 0, 0, 0, 0, datetime('now'))
            """)
            conn.commit()
            conn.close()
            results["_email_skipped"] = True
            results["_admin_session"] = admin_info
            return results

        # Personne connecte — envoyer le rapport par email
        self.send_audit_report(results)

        # Envoyer alertes critiques instantanees
        for sid, data in results.items():
            if isinstance(data, dict) and "summary" in data:
                if data["summary"].get("critical", 0) > 0:
                    criticals = [i for i in
                                 data.get("html_audit", {}).get("issues", []) +
                                 data.get("live_audit", {}).get("issues", [])
                                 if i.get("severity") == "critical"]
                    for c in criticals:
                        self.send_critical_alert(sid, c.get("message", ""))

        return results


# =========================================
# CLI
# =========================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-Audit Agent - SeoAI")
    parser.add_argument("command", choices=[
        "audit", "audit-site", "report", "confirm", "confirm-all", "pending-sql",
        "audit-email", "test-email"
    ], help="Commande")
    parser.add_argument("--site", help="Site specifique (ex: seoparai)")
    parser.add_argument("--id", type=int, help="ID du fix a confirmer")

    args = parser.parse_args()
    agent = SelfAuditAgent()

    if args.command == "audit":
        if args.site:
            result = agent.full_audit(args.site)
        else:
            result = agent.full_audit_all()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "audit-site":
        site = args.site or "seoparai"
        result = agent.full_audit(site)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "report":
        print(agent.get_ssh_report())

    elif args.command == "confirm":
        if args.id:
            result = agent.confirm_fix(args.id)
            print(json.dumps(result))
        else:
            print("Erreur: --id requis")

    elif args.command == "confirm-all":
        result = agent.confirm_all()
        print(json.dumps(result))

    elif args.command == "pending-sql":
        print(agent.get_pending_sql())

    elif args.command == "audit-email":
        if args.site:
            result = agent.full_audit_with_email(args.site)
        else:
            result = agent.full_audit_with_email()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "test-email":
        ok = agent.send_email(
            "🧪 Test SeoAI Self-Audit Email",
            "<html><body><h2>Test reussi!</h2><p>Le systeme d'email fonctionne.</p></body></html>"
        )
        print("Email envoye!" if ok else "ERREUR: verifier SEOAI_SMTP_PASS")


if __name__ == "__main__":
    main()

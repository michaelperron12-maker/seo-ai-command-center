#!/usr/bin/env python3
"""
Favicon Agent - Detection, generation et deploiement automatique de favicons
Couvre les 4 sites: deneigement, paysagement, jcpeintre, seoparai
"""

import os
import json
import sqlite3
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional

SITES = {
    "deneigement": {
        "domain": "deneigement-excellence.ca",
        "url": "https://deneigement-excellence.ca",
        "path": "/var/www/deneigement",
        "brand_color": "#1a5276",
        "icon_letter": "D",
        "label": "Deneigement Excellence"
    },
    "paysagement": {
        "domain": "paysagiste-excellence.ca",
        "url": "https://paysagiste-excellence.ca",
        "path": "/var/www/paysagement",
        "brand_color": "#27ae60",
        "icon_letter": "P",
        "label": "Paysagiste Excellence"
    },
    "jcpeintre": {
        "domain": "jcpeintre.com",
        "url": "https://jcpeintre.com",
        "path": "/var/www/jcpeintre.com",
        "brand_color": "#c0392b",
        "icon_letter": "JC",
        "label": "JC Peintre"
    },
    "seoparai": {
        "domain": "seoparai.ca",
        "url": "https://seoparai.ca",
        "path": "/var/www/seoparai",
        "brand_color": "#0f3460",
        "icon_letter": "AI",
        "label": "SEO par AI"
    }
}

NGINX_ERROR_LOG = "/var/log/nginx/error.log"
DB_PATH = "/opt/seo-agent/db/seo_agent.db"
LOG_PATH = "/opt/seo-agent/logs/favicon_agent.log"

FAVICON_FILES = ["favicon.ico", "favicon.png", "favicon.svg"]


class FaviconAgent:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS favicon_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                domain TEXT,
                has_ico BOOLEAN DEFAULT 0,
                has_png BOOLEAN DEFAULT 0,
                has_svg BOOLEAN DEFAULT 0,
                html_link_tag BOOLEAN DEFAULT 0,
                nginx_404_count INTEGER DEFAULT 0,
                last_fix TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS favicon_fixes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                action TEXT NOT NULL,
                file_path TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a") as f:
                f.write(line + "\n")
        except Exception:
            pass

    # ========================================
    # SCAN - Detecter favicons manquants
    # ========================================
    def scan_all(self) -> Dict:
        self.log("=== SCAN FAVICONS ===")
        results = {}
        for site_id, site in SITES.items():
            results[site_id] = self.scan_site(site_id, site)
        return results

    def scan_site(self, site_id: str, site: Dict) -> Dict:
        path = site["path"]
        result = {
            "site_id": site_id,
            "domain": site["domain"],
            "has_ico": os.path.isfile(os.path.join(path, "favicon.ico")),
            "has_png": os.path.isfile(os.path.join(path, "favicon.png")),
            "has_svg": os.path.isfile(os.path.join(path, "favicon.svg")),
            "html_link_tag": False,
            "nginx_404_count": 0,
            "missing": []
        }

        # Verifier si index.html a un <link rel="icon">
        index_path = os.path.join(path, "index.html")
        if os.path.isfile(index_path):
            try:
                with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
                    html = f.read()
                result["html_link_tag"] = bool(re.search(
                    r'<link[^>]*rel=["\'](?:icon|shortcut icon)["\']', html, re.I
                ))
            except Exception:
                pass

        # Compter les 404 favicon dans les logs nginx
        result["nginx_404_count"] = self._count_nginx_favicon_404(site["domain"])

        # Determiner ce qui manque
        if not result["has_ico"] and not result["has_png"] and not result["has_svg"]:
            result["missing"].append("all")
        else:
            if not result["has_ico"]:
                result["missing"].append("ico")
            if not result["has_svg"]:
                result["missing"].append("svg")
        if not result["html_link_tag"]:
            result["missing"].append("html_tag")

        status = "OK" if not result["missing"] else f"MANQUE: {', '.join(result['missing'])}"
        self.log(f"  {site_id}: {status} (404 nginx: {result['nginx_404_count']})")

        # Sauvegarder dans la DB
        self._save_scan(result)
        return result

    def _count_nginx_favicon_404(self, domain: str) -> int:
        count = 0
        try:
            if os.path.isfile(NGINX_ERROR_LOG):
                with open(NGINX_ERROR_LOG, "r", errors="ignore") as f:
                    for line in f:
                        if "favicon" in line.lower() and domain in line:
                            count += 1
        except PermissionError:
            # Essayer avec sudo
            try:
                out = subprocess.run(
                    ["sudo", "grep", "-ci", "favicon.*" + domain, NGINX_ERROR_LOG],
                    capture_output=True, text=True, timeout=10
                )
                count = int(out.stdout.strip()) if out.stdout.strip() else 0
            except Exception:
                pass
        return count

    def _save_scan(self, result: Dict):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO favicon_status
                (site_id, domain, has_ico, has_png, has_svg, html_link_tag, nginx_404_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result["site_id"], result["domain"],
                result["has_ico"], result["has_png"], result["has_svg"],
                result["html_link_tag"], result["nginx_404_count"]
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"  DB erreur: {e}")

    # ========================================
    # GENERATE - Creer les favicons manquants
    # ========================================
    def generate_favicon_svg(self, site_id: str) -> Optional[str]:
        site = SITES.get(site_id)
        if not site:
            return None

        color = site["brand_color"]
        letter = site["icon_letter"]
        font_size = "14" if len(letter) > 1 else "18"

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="{color}"/>
  <text x="16" y="22" font-family="Arial,Helvetica,sans-serif" font-size="{font_size}" font-weight="bold" fill="white" text-anchor="middle">{letter}</text>
</svg>'''
        return svg

    def deploy_favicon(self, site_id: str, dry_run: bool = False) -> Dict:
        site = SITES.get(site_id)
        if not site:
            return {"error": "Site inconnu"}

        path = site["path"]
        result = {"site_id": site_id, "actions": []}

        if not os.path.isdir(path):
            result["error"] = f"Dossier {path} n'existe pas"
            return result

        # Generer et deployer le SVG
        svg_path = os.path.join(path, "favicon.svg")
        if not os.path.isfile(svg_path):
            svg_content = self.generate_favicon_svg(site_id)
            if svg_content:
                if not dry_run:
                    with open(svg_path, "w") as f:
                        f.write(svg_content)
                    subprocess.run(
                        ["sudo", "chown", "www-data:www-data", svg_path],
                        capture_output=True
                    )
                result["actions"].append(f"SVG cree: {svg_path}")
                self.log(f"  SVG deploye: {svg_path}")

        # Generer ICO a partir du SVG (si convert/rsvg disponible)
        ico_path = os.path.join(path, "favicon.ico")
        if not os.path.isfile(ico_path):
            if self._create_ico_from_svg(svg_path, ico_path, dry_run):
                result["actions"].append(f"ICO cree: {ico_path}")
            else:
                # Fallback: copier le SVG comme favicon.ico simple
                if not dry_run and os.path.isfile(svg_path):
                    png_path = os.path.join(path, "favicon.png")
                    self._create_simple_png(site_id, png_path)
                    result["actions"].append(f"PNG fallback cree: {png_path}")

        # Ajouter le link tag dans index.html si absent
        index_path = os.path.join(path, "index.html")
        if os.path.isfile(index_path):
            if not dry_run:
                self._inject_favicon_link(index_path, site_id)
            result["actions"].append("Link tag ajoute dans index.html")

        # Enregistrer le fix
        self._save_fix(site_id, result["actions"])
        return result

    def _create_ico_from_svg(self, svg_path: str, ico_path: str, dry_run: bool) -> bool:
        if dry_run:
            return True
        try:
            # Essayer avec convert (ImageMagick)
            r = subprocess.run(
                ["convert", svg_path, "-resize", "32x32", ico_path],
                capture_output=True, timeout=10
            )
            if r.returncode == 0:
                subprocess.run(["sudo", "chown", "www-data:www-data", ico_path], capture_output=True)
                return True
        except FileNotFoundError:
            pass
        try:
            # Essayer avec rsvg-convert + convert
            r = subprocess.run(
                ["rsvg-convert", svg_path, "-w", "32", "-h", "32", "-o", ico_path.replace(".ico", ".png")],
                capture_output=True, timeout=10
            )
            if r.returncode == 0:
                png_tmp = ico_path.replace(".ico", ".png")
                subprocess.run(["convert", png_tmp, ico_path], capture_output=True, timeout=10)
                subprocess.run(["sudo", "chown", "www-data:www-data", ico_path], capture_output=True)
                return True
        except FileNotFoundError:
            pass
        return False

    def _create_simple_png(self, site_id: str, png_path: str):
        """Creer un PNG minimal via Python si ImageMagick non disponible"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            site = SITES[site_id]
            img = Image.new("RGB", (32, 32), site["brand_color"])
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            except Exception:
                font = ImageFont.load_default()
            letter = site["icon_letter"]
            bbox = draw.textbbox((0, 0), letter, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            draw.text(((32 - w) / 2, (32 - h) / 2 - 2), letter, fill="white", font=font)
            img.save(png_path)
            subprocess.run(["sudo", "chown", "www-data:www-data", png_path], capture_output=True)
        except ImportError:
            self.log("  PIL non disponible, SVG seulement")

    def _inject_favicon_link(self, index_path: str, site_id: str):
        """Ajouter <link rel='icon'> dans le <head> si absent"""
        try:
            with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()

            if re.search(r'<link[^>]*rel=["\'](?:icon|shortcut icon)["\']', html, re.I):
                return  # Deja present

            favicon_tag = '    <link rel="icon" type="image/svg+xml" href="/favicon.svg">\n    <link rel="icon" type="image/x-icon" href="/favicon.ico">\n'

            # Inserer apres <head> ou apres <meta charset>
            if "<head>" in html:
                html = html.replace("<head>", "<head>\n" + favicon_tag, 1)
            elif "<HEAD>" in html:
                html = html.replace("<HEAD>", "<HEAD>\n" + favicon_tag, 1)
            else:
                return

            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)

            subprocess.run(["sudo", "chown", "www-data:www-data", index_path], capture_output=True)
            self.log(f"  Favicon link injecte dans {index_path}")
        except Exception as e:
            self.log(f"  Erreur injection HTML: {e}")

    def _save_fix(self, site_id: str, actions: List[str]):
        try:
            conn = sqlite3.connect(self.db_path)
            for action in actions:
                conn.execute("""
                    INSERT INTO favicon_fixes (site_id, action, status)
                    VALUES (?, ?, 'done')
                """, (site_id, action))
            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"  DB erreur fix: {e}")

    # ========================================
    # FIX ALL - Scanner et corriger tout
    # ========================================
    def fix_all(self, dry_run: bool = False) -> Dict:
        self.log("=== FAVICON AGENT - FIX ALL ===")
        scan = self.scan_all()
        fixes = {}
        for site_id, result in scan.items():
            if result.get("missing"):
                self.log(f"  Correction {site_id}...")
                fixes[site_id] = self.deploy_favicon(site_id, dry_run=dry_run)
            else:
                self.log(f"  {site_id}: OK, rien a faire")
                fixes[site_id] = {"actions": [], "status": "ok"}

        # Creer alerte si des corrections ont ete faites
        total_fixes = sum(len(f.get("actions", [])) for f in fixes.values())
        if total_fixes > 0:
            self._create_alert(f"Favicon Agent: {total_fixes} corrections appliquees sur {len(fixes)} sites")

        self.log(f"=== FIN - {total_fixes} corrections ===")
        return fixes

    def _create_alert(self, message: str):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO alerts (type, message, severite)
                VALUES ('info', ?, 2)
            """, (message,))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ========================================
    # STATUS - Rapport pour le dashboard
    # ========================================
    def status(self) -> Dict:
        result = {"sites": {}, "total_missing": 0, "last_check": None}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM favicon_status
                WHERE id IN (SELECT MAX(id) FROM favicon_status GROUP BY site_id)
                ORDER BY site_id
            """).fetchall()
            for row in rows:
                site = dict(row)
                missing = []
                if not site["has_ico"]:
                    missing.append("ico")
                if not site["has_svg"]:
                    missing.append("svg")
                if not site["html_link_tag"]:
                    missing.append("html_tag")
                site["missing"] = missing
                result["sites"][site["site_id"]] = site
                result["total_missing"] += len(missing)
                result["last_check"] = site["checked_at"]
            conn.close()
        except Exception:
            pass
        return result


# ========================================
# CLI
# ========================================
if __name__ == "__main__":
    import sys
    agent = FaviconAgent()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"

    if cmd == "scan":
        results = agent.scan_all()
        for site_id, r in results.items():
            status = "OK" if not r["missing"] else f"MANQUE: {', '.join(r['missing'])}"
            print(f"  {site_id}: {status}")

    elif cmd == "fix":
        results = agent.fix_all(dry_run=False)
        for site_id, r in results.items():
            if r.get("actions"):
                for a in r["actions"]:
                    print(f"  {site_id}: {a}")
            else:
                print(f"  {site_id}: OK")

    elif cmd == "dry-run":
        results = agent.fix_all(dry_run=True)
        print(json.dumps(results, indent=2, default=str))

    elif cmd == "status":
        print(json.dumps(agent.status(), indent=2, default=str))

    else:
        print("Usage: favicon_agent.py [scan|fix|dry-run|status]")

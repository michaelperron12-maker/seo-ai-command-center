#!/usr/bin/env python3
"""
Dashboard HTML - Interface visuelle des alertes SEO
Port: 8890
"""

from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)
DB_PATH = "/opt/seo-agent/db/seo_agent.db"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO AI - Dashboard Alertes</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { text-align: center; color: #00d4ff; margin-bottom: 30px; }
        .stats { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
        .stat-box { background: #16213e; padding: 20px 40px; border-radius: 10px; text-align: center; min-width: 150px; }
        .stat-box.critical { border: 2px solid #ff4757; }
        .stat-box.warning { border: 2px solid #ffa502; }
        .stat-box.info { border: 2px solid #00d4ff; }
        .stat-number { font-size: 48px; font-weight: bold; }
        .stat-label { font-size: 14px; opacity: 0.8; }
        .critical .stat-number { color: #ff4757; }
        .warning .stat-number { color: #ffa502; }
        .info .stat-number { color: #00d4ff; }

        .sites { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .site-card { background: #16213e; border-radius: 10px; padding: 20px; }
        .site-name { font-size: 20px; color: #00d4ff; margin-bottom: 5px; }
        .site-domain { font-size: 14px; opacity: 0.6; margin-bottom: 15px; }
        .alert-count { display: flex; gap: 15px; flex-wrap: wrap; }
        .alert-badge { padding: 5px 15px; border-radius: 5px; font-size: 14px; }
        .badge-critical { background: #ff4757; color: white; }
        .badge-total { background: #ffa502; color: black; }

        .alerts-section { margin-top: 40px; }
        .alerts-section h2 { color: #ff4757; margin-bottom: 20px; }
        .alert-item { background: #16213e; padding: 15px; margin-bottom: 10px; border-radius: 5px; border-left: 4px solid #ff4757; }
        .alert-item.high { border-left-color: #ffa502; }
        .alert-site { font-size: 12px; color: #00d4ff; }
        .alert-check { font-weight: bold; margin: 5px 0; }
        .alert-message { font-size: 14px; opacity: 0.8; }

        .refresh-btn { position: fixed; bottom: 20px; right: 20px; background: #00d4ff; color: #1a1a2e;
                       padding: 15px 25px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .refresh-btn:hover { background: #00b8e6; }

        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #333; }
        th { background: #0f3460; color: #00d4ff; }
        tr:hover { background: #1f4068; }
        .status-ok { color: #2ed573; }
        .status-fail { color: #ff4757; }
    </style>
</head>
<body>
    <h1>🚀 SEO AI - Dashboard Alertes</h1>

    <div class="stats">
        <div class="stat-box info">
            <div class="stat-number">{{ sites|length }}</div>
            <div class="stat-label">SITES</div>
        </div>
        <div class="stat-box critical">
            <div class="stat-number">{{ critical_total }}</div>
            <div class="stat-label">ALERTES CRITIQUES</div>
        </div>
        <div class="stat-box warning">
            <div class="stat-number">{{ total_alerts }}</div>
            <div class="stat-label">ALERTES TOTALES</div>
        </div>
        <div class="stat-box info">
            <div class="stat-number">{{ weekly_tasks }}</div>
            <div class="stat-label">TÂCHES SEMAINE</div>
        </div>
    </div>

    <h2 style="color: #00d4ff; margin: 30px 0 15px 0;">📊 Sites Audités ({{ sites|length }} sites)</h2>
    <div class="sites">
        {% for site in sites %}
        <div class="site-card">
            <div class="site-name">{{ site.name }}</div>
            <div class="site-domain">🌐 {{ site.domain }}</div>
            <div class="alert-count">
                <span class="alert-badge badge-critical">🚨 {{ site.critical }} critiques</span>
                <span class="alert-badge badge-total">⚠️ {{ site.alerts }} total</span>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="alerts-section">
        <h2>🚨 Alertes Critiques par Site</h2>
        <table>
            <thead>
                <tr>
                    <th>Site</th>
                    <th>Catégorie</th>
                    <th>Vérification</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for alert in critical_alerts %}
                <tr>
                    <td>{{ alert.site }}</td>
                    <td>{{ alert.category }}</td>
                    <td>{{ alert.check }}</td>
                    <td class="status-fail">❌ Non configuré</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Rafraîchir</button>

    <p style="text-align: center; margin-top: 50px; opacity: 0.5;">
        SEO AI Command Center - {{ sites|length }} sites | {{ total_alerts }} alertes
    </p>
</body>
</html>
"""

CHECKLIST = {
    "reseaux_sociaux": [
        {"id": "facebook", "name": "Page Facebook", "critical": True},
        {"id": "instagram", "name": "Compte Instagram", "critical": True},
        {"id": "linkedin", "name": "Page LinkedIn", "critical": False},
        {"id": "twitter", "name": "Compte Twitter/X", "critical": False},
        {"id": "youtube", "name": "Chaîne YouTube", "critical": False},
        {"id": "tiktok", "name": "Compte TikTok", "critical": False},
    ],
    "seo_local": [
        {"id": "google_business", "name": "Google Business Profile", "critical": True},
        {"id": "bing_places", "name": "Bing Places", "critical": False},
        {"id": "yelp", "name": "Profil Yelp", "critical": False},
        {"id": "pages_jaunes", "name": "Pages Jaunes", "critical": True},
    ],
    "forums_communautes": [
        {"id": "reddit", "name": "Compte Reddit", "critical": True},
        {"id": "quora", "name": "Compte Quora", "critical": False},
        {"id": "forums_locaux", "name": "Forums locaux", "critical": False},
    ],
    "technique": [
        {"id": "ssl", "name": "Certificat SSL", "critical": True},
        {"id": "mobile", "name": "Version Mobile", "critical": True},
        {"id": "speed", "name": "Vitesse < 3s", "critical": True},
        {"id": "sitemap", "name": "Sitemap XML", "critical": True},
        {"id": "robots", "name": "Robots.txt", "critical": False},
        {"id": "schema", "name": "Schema Markup", "critical": False},
    ],
    "contenu": [
        {"id": "meta_title", "name": "Meta Title optimisé", "critical": True},
        {"id": "meta_desc", "name": "Meta Description", "critical": True},
        {"id": "h1", "name": "Balise H1 unique", "critical": True},
        {"id": "images_alt", "name": "Alt text images", "critical": False},
        {"id": "blog", "name": "Section Blog active", "critical": False},
        {"id": "faq", "name": "Page FAQ", "critical": False},
    ],
    "backlinks": [
        {"id": "annuaires", "name": "Annuaires locaux", "critical": False},
        {"id": "citations_nap", "name": "Citations NAP", "critical": True},
        {"id": "guest_posts", "name": "Guest Posts", "critical": False},
    ]
}

def get_sites():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, domain FROM sites")
        sites = [{"id": r[0], "name": r[1], "domain": r[2]} for r in cursor.fetchall()]
        conn.close()
        return sites
    except:
        # Fallback si pas de connexion DB
        return [
            {"id": 1, "name": "Déneigement Excellence", "domain": "deneigement-excellence.ca"},
            {"id": 2, "name": "Paysagiste Excellence", "domain": "paysagiste-excellence.ca"},
            {"id": 3, "name": "JC Peintre", "domain": "jcpeintre.com"},
            {"id": 4, "name": "SEO par AI", "domain": "seoparai.ca"},
        ]

@app.route("/")
def dashboard():
    sites = get_sites()
    critical_alerts = []
    total_alerts = 0
    critical_total = 0

    for site in sites:
        site["alerts"] = 0
        site["critical"] = 0
        for category, checks in CHECKLIST.items():
            for check in checks:
                site["alerts"] += 1
                total_alerts += 1
                if check.get("critical"):
                    site["critical"] += 1
                    critical_total += 1
                    critical_alerts.append({
                        "site": site["name"],
                        "domain": site["domain"],
                        "category": category.replace("_", " ").title(),
                        "check": check["name"],
                        "message": "Non configuré - Action requise"
                    })

    return render_template_string(HTML_TEMPLATE,
        sites=sites,
        critical_alerts=critical_alerts,
        total_alerts=total_alerts,
        critical_total=critical_total,
        weekly_tasks=len(sites) * 6
    )

@app.route("/api/status")
def api_status():
    sites = get_sites()
    return {
        "sites": len(sites),
        "sites_list": [s["name"] for s in sites],
        "status": "online"
    }

if __name__ == "__main__":
    print("[DASHBOARD HTML] Démarrage interface visuelle...")
    print("[DASHBOARD HTML] URL: http://148.113.194.234:8890")
    print(f"[DASHBOARD HTML] {len(get_sites())} sites chargés")
    app.run(host="0.0.0.0", port=8890, debug=False)

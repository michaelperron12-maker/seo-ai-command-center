#!/usr/bin/env python3
"""
Monitoring Agent - Surveillance continue des sites et alertes
Supporte les 3 sites: deneigement, paysagement, jcpeintre
"""

import os
import json
import sqlite3
import requests
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import socket

SITES = {
    "deneigement": {
        "domain": "deneigement-excellence.ca",
        "url": "https://deneigement-excellence.ca",
        "path": "/var/www/deneigement",
        "critical_pages": ["/", "/services", "/contact"]
    },
    "paysagement": {
        "domain": "paysagiste-excellence.ca",
        "url": "https://paysagiste-excellence.ca",
        "path": "/var/www/paysagement",
        "critical_pages": ["/", "/services", "/contact"]
    },
    "jcpeintre": {
        "domain": "jcpeintre.com",
        "url": "https://jcpeintre.com",
        "path": "/var/www/jcpeintre.com",
        "critical_pages": ["/", "/services", "/contact", "/devis"]
    },
    "seoparai": {
        "domain": "seoparai.ca",
        "url": "https://seoparai.ca",
        "path": "/var/www/seoparai",
        "critical_pages": ["/", "/landing.html"]
    }
}

# Seuils d'alerte
THRESHOLDS = {
    "response_time_warning": 2000,  # ms
    "response_time_critical": 5000,  # ms
    "disk_warning": 80,  # %
    "disk_critical": 90,  # %
    "memory_warning": 85,  # %
    "memory_critical": 95,  # %
    "cpu_load_warning": 2.0,  # load average
    "cpu_load_critical": 4.0
}

class MonitoringAgent:
    def __init__(self, db_path: str = "/opt/seo-agent/db/seo_agent.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialise les tables de monitoring (préfixe mon_ pour éviter conflits)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS mon_uptime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                url TEXT,
                status_code INTEGER,
                response_time_ms REAL,
                is_up BOOLEAN,
                error_message TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mon_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                details TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                resolved BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS mon_ssl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                domain TEXT,
                valid BOOLEAN,
                issuer TEXT,
                expires_at DATETIME,
                days_until_expiry INTEGER,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mon_security (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                scan_type TEXT,
                findings TEXT,
                severity TEXT,
                scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_mon_uptime_site ON mon_uptime(site_id);
            CREATE INDEX IF NOT EXISTS idx_mon_alerts_site ON mon_alerts(site_id);
            CREATE INDEX IF NOT EXISTS idx_mon_alerts_resolved ON mon_alerts(resolved);
        """)
        conn.commit()
        conn.close()

    def check_site_uptime(self, site_id: str) -> Dict:
        """Vérifie si un site est en ligne"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        site = SITES[site_id]
        results = {"site_id": site_id, "checks": [], "overall_status": "up"}

        for page in site["critical_pages"]:
            url = f"{site['url']}{page}"
            try:
                start = datetime.now()
                response = requests.get(url, timeout=30, allow_redirects=True)
                end = datetime.now()

                response_time = (end - start).total_seconds() * 1000
                is_up = response.status_code < 400

                check = {
                    "url": url,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                    "is_up": is_up
                }

                # Sauvegarder
                self._save_uptime_check(site_id, url, response.status_code, response_time, is_up, None)

                # Vérifier les seuils
                if response_time > THRESHOLDS["response_time_critical"]:
                    self._create_alert(site_id, "response_time", "critical",
                                       f"Temps de réponse critique: {response_time}ms pour {url}")
                elif response_time > THRESHOLDS["response_time_warning"]:
                    self._create_alert(site_id, "response_time", "warning",
                                       f"Temps de réponse lent: {response_time}ms pour {url}")

                if not is_up:
                    results["overall_status"] = "down"
                    self._create_alert(site_id, "downtime", "critical",
                                       f"Page inaccessible: {url} (HTTP {response.status_code})")

                results["checks"].append(check)

            except requests.exceptions.Timeout:
                self._save_uptime_check(site_id, url, 0, 0, False, "Timeout")
                self._create_alert(site_id, "downtime", "critical", f"Timeout pour {url}")
                results["checks"].append({"url": url, "error": "timeout", "is_up": False})
                results["overall_status"] = "down"

            except Exception as e:
                self._save_uptime_check(site_id, url, 0, 0, False, str(e))
                results["checks"].append({"url": url, "error": str(e), "is_up": False})
                results["overall_status"] = "error"

        return results

    def _save_uptime_check(self, site_id: str, url: str, status_code: int,
                           response_time: float, is_up: bool, error: str):
        """Sauvegarde un check uptime"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mon_uptime (site_id, url, status_code, response_time_ms, is_up, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (site_id, url, status_code, response_time, is_up, error))
        conn.commit()
        conn.close()

    def _create_alert(self, site_id: str, alert_type: str, severity: str, message: str, details: str = None):
        """Crée une alerte"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Vérifier si une alerte similaire existe déjà (non résolue)
        cursor.execute("""
            SELECT id FROM mon_alerts
            WHERE site_id = ? AND alert_type = ? AND message = ? AND resolved = 0
            AND created_at > datetime('now', '-1 hour')
        """, (site_id, alert_type, message))

        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO mon_alerts (site_id, alert_type, severity, message, details)
                VALUES (?, ?, ?, ?, ?)
            """, (site_id, alert_type, severity, message, details))
            conn.commit()

        conn.close()

    def check_ssl_certificate(self, site_id: str) -> Dict:
        """Vérifie le certificat SSL"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        domain = SITES[site_id]["domain"]

        try:
            import ssl
            import socket
            from datetime import datetime

            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

            # Parser la date d'expiration
            not_after = cert.get('notAfter', '')
            # Format: 'Mar 15 12:00:00 2025 GMT'
            try:
                expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (expiry - datetime.now()).days
            except:
                expiry = None
                days_until_expiry = -1

            issuer = dict(x[0] for x in cert.get('issuer', []))
            issuer_name = issuer.get('organizationName', 'Unknown')

            result = {
                "site_id": site_id,
                "domain": domain,
                "valid": True,
                "issuer": issuer_name,
                "expires_at": not_after,
                "days_until_expiry": days_until_expiry
            }

            # Sauvegarder
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mon_ssl (site_id, domain, valid, issuer, expires_at, days_until_expiry)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (site_id, domain, True, issuer_name, not_after, days_until_expiry))
            conn.commit()
            conn.close()

            # Alertes
            if days_until_expiry < 7:
                self._create_alert(site_id, "ssl", "critical",
                                   f"Certificat SSL expire dans {days_until_expiry} jours!")
            elif days_until_expiry < 30:
                self._create_alert(site_id, "ssl", "warning",
                                   f"Certificat SSL expire dans {days_until_expiry} jours")

            return result

        except Exception as e:
            self._create_alert(site_id, "ssl", "critical", f"Erreur SSL: {str(e)}")
            return {"site_id": site_id, "domain": domain, "valid": False, "error": str(e)}

    def check_server_health(self) -> Dict:
        """Vérifie la santé du serveur"""
        result = {"status": "healthy", "issues": []}

        try:
            # Load average
            with open("/proc/loadavg", "r") as f:
                load = float(f.read().split()[0])

            if load > THRESHOLDS["cpu_load_critical"]:
                result["issues"].append({"type": "cpu", "severity": "critical", "value": load})
                result["status"] = "critical"
                self._create_alert(None, "server_cpu", "critical", f"Charge CPU critique: {load}")
            elif load > THRESHOLDS["cpu_load_warning"]:
                result["issues"].append({"type": "cpu", "severity": "warning", "value": load})
                result["status"] = "warning"

            result["cpu_load"] = load

            # Memory
            mem = subprocess.run(["free", "-m"], capture_output=True, text=True)
            mem_lines = mem.stdout.strip().split("\n")
            if len(mem_lines) > 1:
                mem_values = mem_lines[1].split()
                total = int(mem_values[1])
                used = int(mem_values[2])
                percent = round((used / total) * 100, 1)

                if percent > THRESHOLDS["memory_critical"]:
                    result["issues"].append({"type": "memory", "severity": "critical", "value": percent})
                    result["status"] = "critical"
                    self._create_alert(None, "server_memory", "critical", f"Mémoire critique: {percent}%")
                elif percent > THRESHOLDS["memory_warning"]:
                    result["issues"].append({"type": "memory", "severity": "warning", "value": percent})
                    if result["status"] != "critical":
                        result["status"] = "warning"

                result["memory_percent"] = percent

            # Disk
            disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
            disk_lines = disk.stdout.strip().split("\n")
            if len(disk_lines) > 1:
                disk_percent = int(disk_lines[1].split()[4].replace("%", ""))

                if disk_percent > THRESHOLDS["disk_critical"]:
                    result["issues"].append({"type": "disk", "severity": "critical", "value": disk_percent})
                    result["status"] = "critical"
                    self._create_alert(None, "server_disk", "critical", f"Disque critique: {disk_percent}%")
                elif disk_percent > THRESHOLDS["disk_warning"]:
                    result["issues"].append({"type": "disk", "severity": "warning", "value": disk_percent})
                    if result["status"] != "critical":
                        result["status"] = "warning"

                result["disk_percent"] = disk_percent

            result["checked_at"] = datetime.now().isoformat()
            return result

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def check_nginx_status(self) -> Dict:
        """Vérifie le statut nginx"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "nginx"],
                capture_output=True, text=True
            )
            is_active = result.stdout.strip() == "active"

            if not is_active:
                self._create_alert(None, "nginx", "critical", "Nginx n'est pas actif!")

            return {
                "nginx_active": is_active,
                "status": result.stdout.strip(),
                "checked_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    def check_all_sites(self) -> Dict:
        """Vérifie tous les sites"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "server": self.check_server_health(),
            "nginx": self.check_nginx_status(),
            "sites": {}
        }

        for site_id in SITES:
            results["sites"][site_id] = {
                "uptime": self.check_site_uptime(site_id),
                "ssl": self.check_ssl_certificate(site_id)
            }

        return results

    def get_alerts(self, site_id: str = None, resolved: bool = False) -> List[Dict]:
        """Récupère les alertes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT site_id, alert_type, severity, message, details, acknowledged, resolved, created_at FROM mon_alerts WHERE resolved = ?"
        params = [1 if resolved else 0]

        if site_id:
            query += " AND site_id = ?"
            params.append(site_id)

        query += " ORDER BY created_at DESC LIMIT 100"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            "site_id": r[0], "alert_type": r[1], "severity": r[2],
            "message": r[3], "details": r[4], "acknowledged": bool(r[5]),
            "resolved": bool(r[6]), "created_at": r[7]
        } for r in rows]

    def resolve_alert(self, alert_id: int):
        """Résout une alerte"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE mon_alerts SET resolved = 1, resolved_at = datetime('now')
            WHERE id = ?
        """, (alert_id,))
        conn.commit()
        conn.close()

    def get_uptime_stats(self, site_id: str, hours: int = 24) -> Dict:
        """Statistiques uptime"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) as up_count,
                AVG(response_time_ms) as avg_response,
                MAX(response_time_ms) as max_response,
                MIN(response_time_ms) as min_response
            FROM mon_uptime
            WHERE site_id = ? AND checked_at > datetime('now', ?)
        """, (site_id, f'-{hours} hours'))

        row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            return {
                "site_id": site_id,
                "period_hours": hours,
                "total_checks": row[0],
                "uptime_percent": round((row[1] / row[0]) * 100, 2) if row[0] > 0 else 0,
                "avg_response_ms": round(row[2], 2) if row[2] else 0,
                "max_response_ms": round(row[3], 2) if row[3] else 0,
                "min_response_ms": round(row[4], 2) if row[4] else 0
            }
        return {"site_id": site_id, "error": "Pas de données"}


if __name__ == "__main__":
    agent = MonitoringAgent()
    print("=== Monitoring Agent - 3 Sites ===")

    print("\nVérification des sites...")
    for site_id in SITES:
        result = agent.check_site_uptime(site_id)
        status = result.get("overall_status", "unknown")
        print(f"  {site_id}: {status}")

    print("\nVérification serveur...")
    health = agent.check_server_health()
    print(f"  Status: {health.get('status', 'unknown')}")

    print("\nAgent prêt!")

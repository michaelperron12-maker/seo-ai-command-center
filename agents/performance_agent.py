#!/usr/bin/env python3
"""
Performance Agent - Analyse et optimise les performances serveur/sites
Supporte les 3 sites: deneigement, paysagement, jcpeintre
"""

import os
import json
import sqlite3
import subprocess
import requests
from datetime import datetime
from typing import List, Dict, Optional
import re

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
    }
}

class PerformanceAgent:
    def __init__(self, db_path: str = "/opt/seo-agent/db/seo_agent.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialise les tables performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                metric_type TEXT,
                value REAL,
                unit TEXT,
                details TEXT,
                measured_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS performance_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT NOT NULL,
                issue_type TEXT,
                severity TEXT,
                description TEXT,
                recommendation TEXT,
                fixed BOOLEAN DEFAULT 0,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                fixed_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                optimization_type TEXT,
                before_value REAL,
                after_value REAL,
                improvement_percent REAL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_perf_site ON performance_metrics(site_id);
            CREATE INDEX IF NOT EXISTS idx_issues_site ON performance_issues(site_id);
        """)
        conn.commit()
        conn.close()

    def measure_response_time(self, site_id: str) -> Dict:
        """Mesure le temps de réponse d'un site"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        url = SITES[site_id]["url"]
        try:
            start = datetime.now()
            response = requests.get(url, timeout=30)
            end = datetime.now()

            response_time = (end - start).total_seconds() * 1000  # en ms
            ttfb = response.elapsed.total_seconds() * 1000

            result = {
                "site_id": site_id,
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "ttfb_ms": round(ttfb, 2),
                "content_size_kb": round(len(response.content) / 1024, 2),
                "measured_at": datetime.now().isoformat()
            }

            # Sauvegarder métriques
            self._save_metric(site_id, "response_time", response_time, "ms")
            self._save_metric(site_id, "ttfb", ttfb, "ms")
            self._save_metric(site_id, "content_size", len(response.content) / 1024, "KB")

            return result
        except Exception as e:
            return {"error": str(e), "site_id": site_id}

    def _save_metric(self, site_id: str, metric_type: str, value: float, unit: str):
        """Sauvegarde une métrique"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO performance_metrics (site_id, metric_type, value, unit)
            VALUES (?, ?, ?, ?)
        """, (site_id, metric_type, value, unit))
        conn.commit()
        conn.close()

    def analyze_all_sites(self) -> Dict:
        """Analyse performance de tous les sites"""
        results = {}
        for site_id in SITES:
            results[site_id] = self.measure_response_time(site_id)
        return results

    def check_server_resources(self) -> Dict:
        """Vérifie les ressources serveur"""
        try:
            # CPU
            cpu = subprocess.run(
                ["grep", "-c", "^processor", "/proc/cpuinfo"],
                capture_output=True, text=True
            )
            cpu_count = int(cpu.stdout.strip()) if cpu.returncode == 0 else 0

            # Load average
            with open("/proc/loadavg", "r") as f:
                load = f.read().split()[:3]

            # Memory
            mem = subprocess.run(["free", "-m"], capture_output=True, text=True)
            mem_lines = mem.stdout.strip().split("\n")
            if len(mem_lines) > 1:
                mem_values = mem_lines[1].split()
                total_mem = int(mem_values[1])
                used_mem = int(mem_values[2])
                mem_percent = round((used_mem / total_mem) * 100, 1)
            else:
                total_mem = used_mem = mem_percent = 0

            # Disk
            disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
            disk_lines = disk.stdout.strip().split("\n")
            if len(disk_lines) > 1:
                disk_values = disk_lines[1].split()
                disk_used = disk_values[4].replace("%", "")
            else:
                disk_used = "0"

            return {
                "cpu_cores": cpu_count,
                "load_average": {
                    "1min": float(load[0]),
                    "5min": float(load[1]),
                    "15min": float(load[2])
                },
                "memory": {
                    "total_mb": total_mem,
                    "used_mb": used_mem,
                    "percent": mem_percent
                },
                "disk_used_percent": int(disk_used),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    def check_nginx_config(self) -> Dict:
        """Vérifie la configuration nginx"""
        issues = []
        recommendations = []

        try:
            # Lire config nginx principale
            with open("/etc/nginx/nginx.conf", "r") as f:
                config = f.read()

            # Vérifications
            if "gzip on" not in config:
                issues.append("Gzip non activé")
                recommendations.append("Activer gzip dans nginx.conf")

            if "worker_connections" in config:
                match = re.search(r'worker_connections\s+(\d+)', config)
                if match and int(match.group(1)) < 1024:
                    issues.append("worker_connections trop bas")
                    recommendations.append("Augmenter worker_connections à 2048+")

            if "keepalive_timeout" not in config:
                recommendations.append("Configurer keepalive_timeout")

            if "client_max_body_size" not in config:
                recommendations.append("Configurer client_max_body_size")

            # Vérifier cache
            if "proxy_cache" not in config and "fastcgi_cache" not in config:
                recommendations.append("Configurer le cache nginx")

            return {
                "config_valid": len(issues) == 0,
                "issues": issues,
                "recommendations": recommendations,
                "checked_at": datetime.now().isoformat()
            }
        except FileNotFoundError:
            return {"error": "nginx.conf non trouvé"}
        except Exception as e:
            return {"error": str(e)}

    def analyze_site_assets(self, site_id: str) -> Dict:
        """Analyse les assets d'un site (images, CSS, JS)"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        path = SITES[site_id]["path"]
        results = {"images": [], "css": [], "js": [], "issues": []}

        try:
            # Images
            img_result = subprocess.run(
                ["find", path, "-type", "f", "-name", "*.jpg", "-o",
                 "-name", "*.png", "-o", "-name", "*.gif", "-o", "-name", "*.webp"],
                capture_output=True, text=True
            )
            images = img_result.stdout.strip().split("\n") if img_result.stdout else []

            large_images = []
            for img in images:
                if img:
                    try:
                        size = os.path.getsize(img)
                        if size > 500 * 1024:  # > 500KB
                            large_images.append({"path": img, "size_kb": round(size/1024, 1)})
                    except:
                        pass

            results["images"] = {
                "total": len([i for i in images if i]),
                "large_images": large_images
            }

            if large_images:
                results["issues"].append({
                    "type": "large_images",
                    "severity": "medium",
                    "count": len(large_images),
                    "recommendation": "Optimiser/compresser les images > 500KB"
                })

            # CSS/JS non minifiés
            for ext, key in [("css", "css"), ("js", "js")]:
                find_result = subprocess.run(
                    ["find", path, "-type", "f", "-name", f"*.{ext}"],
                    capture_output=True, text=True
                )
                files = find_result.stdout.strip().split("\n") if find_result.stdout else []
                unminified = []

                for f in files:
                    if f and ".min." not in f:
                        try:
                            size = os.path.getsize(f)
                            if size > 50 * 1024:  # > 50KB
                                unminified.append({"path": f, "size_kb": round(size/1024, 1)})
                        except:
                            pass

                results[key] = {
                    "total": len([f for f in files if f]),
                    "unminified_large": unminified
                }

            return results
        except Exception as e:
            return {"error": str(e)}

    def get_optimization_suggestions(self, site_id: str) -> List[Dict]:
        """Génère des suggestions d'optimisation pour un site"""
        suggestions = []

        # Analyser le site
        perf = self.measure_response_time(site_id)
        assets = self.analyze_site_assets(site_id)

        if "response_time_ms" in perf and perf["response_time_ms"] > 1000:
            suggestions.append({
                "category": "response_time",
                "priority": "high",
                "issue": f"Temps de réponse élevé: {perf['response_time_ms']}ms",
                "actions": [
                    "Activer le cache nginx",
                    "Optimiser les requêtes DB",
                    "Activer la compression gzip"
                ]
            })

        if "issues" in assets:
            for issue in assets["issues"]:
                suggestions.append({
                    "category": issue["type"],
                    "priority": issue["severity"],
                    "issue": issue.get("recommendation", ""),
                    "actions": [issue.get("recommendation", "")]
                })

        return suggestions

    def generate_report(self) -> Dict:
        """Génère un rapport complet de performance"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "server": self.check_server_resources(),
            "nginx": self.check_nginx_config(),
            "sites": {}
        }

        for site_id in SITES:
            report["sites"][site_id] = {
                "performance": self.measure_response_time(site_id),
                "assets": self.analyze_site_assets(site_id),
                "suggestions": self.get_optimization_suggestions(site_id)
            }

        return report

    def log_issue(self, site_id: str, issue_type: str, severity: str,
                  description: str, recommendation: str):
        """Enregistre un problème de performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO performance_issues
            (site_id, issue_type, severity, description, recommendation)
            VALUES (?, ?, ?, ?, ?)
        """, (site_id, issue_type, severity, description, recommendation))
        conn.commit()
        conn.close()

    def get_issues(self, site_id: str = None, fixed: bool = False) -> List[Dict]:
        """Récupère les problèmes enregistrés"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT site_id, issue_type, severity, description, recommendation, fixed, discovered_at FROM performance_issues WHERE fixed = ?"
        params = [1 if fixed else 0]

        if site_id:
            query += " AND site_id = ?"
            params.append(site_id)

        query += " ORDER BY discovered_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            "site_id": r[0], "issue_type": r[1], "severity": r[2],
            "description": r[3], "recommendation": r[4],
            "fixed": bool(r[5]), "discovered_at": r[6]
        } for r in rows]


if __name__ == "__main__":
    agent = PerformanceAgent()
    print("=== Performance Agent - 3 Sites ===")

    print("\nAnalyse des sites...")
    for site_id, info in SITES.items():
        result = agent.measure_response_time(site_id)
        if "response_time_ms" in result:
            print(f"  {site_id}: {result['response_time_ms']}ms")
        else:
            print(f"  {site_id}: {result.get('error', 'erreur')}")

    print("\nRessources serveur:")
    resources = agent.check_server_resources()
    if "error" not in resources:
        print(f"  CPU: {resources['cpu_cores']} cores")
        print(f"  RAM: {resources['memory']['percent']}% utilisée")
        print(f"  Disk: {resources['disk_used_percent']}% utilisé")

    print("\nAgent prêt!")

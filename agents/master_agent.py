#!/usr/bin/env python3
"""
Master Agent - Coordinateur principal de tous les agents
Orchestre les agents: Research, Performance, Learning, Monitoring
Supporte les 3 sites: deneigement, paysagement, jcpeintre
"""

import os
import sys
import json
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import schedule

# Ajouter le path des agents
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from research_agent import ResearchAgent
from performance_agent import PerformanceAgent
from learning_agent import LearningAgent
from monitoring_agent import MonitoringAgent

SITES = ["deneigement", "paysagement", "jcpeintre"]

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/seo-agent/logs/master_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MasterAgent')

class MasterAgent:
    def __init__(self, db_path: str = "/opt/seo-agent/db/seo_agent.db"):
        self.db_path = db_path
        self.research = ResearchAgent(db_path)
        self.performance = PerformanceAgent(db_path)
        self.learning = LearningAgent(db_path)
        self.monitoring = MonitoringAgent(db_path)
        self._init_db()
        self._running = False

    def _init_db(self):
        """Initialise les tables du master agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                task_type TEXT,
                site_id TEXT,
                status TEXT,
                result TEXT,
                duration_seconds REAL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT UNIQUE,
                agent_name TEXT,
                schedule_cron TEXT,
                last_run DATETIME,
                next_run DATETIME,
                enabled BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS agent_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_runs_agent ON agent_runs(agent_name);
            CREATE INDEX IF NOT EXISTS idx_runs_status ON agent_runs(status);
        """)
        conn.commit()
        conn.close()

    def log_run(self, agent_name: str, task_type: str, site_id: str,
                status: str, result: Dict, duration: float):
        """Enregistre une exécution d'agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_runs
            (agent_name, task_type, site_id, status, result, duration_seconds, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (agent_name, task_type, site_id, status, json.dumps(result), duration))
        conn.commit()
        conn.close()

    def run_monitoring_cycle(self) -> Dict:
        """Exécute un cycle de monitoring complet"""
        logger.info("Démarrage cycle monitoring...")
        start = time.time()
        results = {}

        try:
            # Vérification de tous les sites
            results = self.monitoring.check_all_sites()

            # Vérifier les alertes critiques
            alerts = self.monitoring.get_alerts(resolved=False)
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']

            if critical_alerts:
                logger.warning(f"ALERTES CRITIQUES: {len(critical_alerts)}")
                for alert in critical_alerts:
                    logger.warning(f"  - {alert['message']}")
                results['critical_alerts'] = critical_alerts

            duration = time.time() - start
            self.log_run("monitoring", "full_cycle", "all", "success", results, duration)
            logger.info(f"Cycle monitoring terminé en {duration:.2f}s")

        except Exception as e:
            logger.error(f"Erreur monitoring: {e}")
            self.log_run("monitoring", "full_cycle", "all", "error", {"error": str(e)}, time.time() - start)

        return results

    def run_performance_analysis(self) -> Dict:
        """Analyse de performance de tous les sites"""
        logger.info("Démarrage analyse performance...")
        start = time.time()
        results = {}

        try:
            for site_id in SITES:
                logger.info(f"  Analyse {site_id}...")
                site_start = time.time()

                perf = self.performance.measure_response_time(site_id)
                assets = self.performance.analyze_site_assets(site_id)
                suggestions = self.performance.get_optimization_suggestions(site_id)

                results[site_id] = {
                    "performance": perf,
                    "assets": assets,
                    "suggestions": suggestions
                }

                site_duration = time.time() - site_start
                self.log_run("performance", "analysis", site_id, "success", results[site_id], site_duration)

            duration = time.time() - start
            logger.info(f"Analyse performance terminée en {duration:.2f}s")

        except Exception as e:
            logger.error(f"Erreur performance: {e}")
            self.log_run("performance", "analysis", "all", "error", {"error": str(e)}, time.time() - start)

        return results

    def run_learning_scan(self) -> Dict:
        """Scan d'apprentissage de tous les sites"""
        logger.info("Démarrage scan apprentissage...")
        start = time.time()
        results = {}

        try:
            for site_id in SITES:
                logger.info(f"  Scan {site_id}...")
                site_start = time.time()

                scan = self.learning.scan_site_code(site_id)
                results[site_id] = scan

                # Sauvegarder les améliorations trouvées
                for imp in scan.get("improvements", []):
                    self.learning.save_improvement(
                        site_id, imp.get("file", ""),
                        imp.get("type", "unknown"),
                        "", imp.get("suggestion", ""),
                        imp.get("issue", ""),
                        imp.get("priority", "medium")
                    )

                site_duration = time.time() - site_start
                self.log_run("learning", "scan", site_id, "success", scan, site_duration)

            duration = time.time() - start
            logger.info(f"Scan apprentissage terminé en {duration:.2f}s")

        except Exception as e:
            logger.error(f"Erreur learning: {e}")
            self.log_run("learning", "scan", "all", "error", {"error": str(e)}, time.time() - start)

        return results

    def run_research_cycle(self, topics: List[str] = None) -> Dict:
        """Cycle de recherche sur des sujets"""
        if topics is None:
            topics = [
                "nginx performance optimization",
                "Core Web Vitals improvement",
                "local SEO best practices",
                "website security hardening"
            ]

        logger.info(f"Démarrage recherche sur {len(topics)} sujets...")
        start = time.time()
        results = {}

        try:
            for topic in topics:
                logger.info(f"  Recherche: {topic}...")
                topic_start = time.time()

                for site_id in SITES:
                    research = self.research.research_for_site(site_id, topic)
                    if site_id not in results:
                        results[site_id] = {}
                    results[site_id][topic] = research

                topic_duration = time.time() - topic_start
                self.log_run("research", topic, "all", "success",
                             {"topic": topic, "sites": len(SITES)}, topic_duration)

            duration = time.time() - start
            logger.info(f"Recherche terminée en {duration:.2f}s")

        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            self.log_run("research", "cycle", "all", "error", {"error": str(e)}, time.time() - start)

        return results

    def get_dashboard_data(self) -> Dict:
        """Génère les données pour le dashboard"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "sites": {},
            "server": {},
            "alerts": [],
            "improvements": [],
            "recent_runs": []
        }

        # Status des sites
        for site_id in SITES:
            uptime = self.monitoring.get_uptime_stats(site_id, hours=24)
            data["sites"][site_id] = {
                "uptime": uptime,
                "improvements_pending": len(self.learning.get_improvements(site_id, applied=False)),
                "alerts_active": len(self.monitoring.get_alerts(site_id, resolved=False))
            }

        # Status serveur
        data["server"] = self.monitoring.check_server_health()

        # Alertes actives
        data["alerts"] = self.monitoring.get_alerts(resolved=False)[:10]

        # Améliorations suggérées
        all_improvements = self.learning.get_improvements(applied=False)
        data["improvements"] = sorted(all_improvements,
                                       key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3))[:10]

        # Dernières exécutions
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT agent_name, task_type, site_id, status, duration_seconds, completed_at
            FROM agent_runs ORDER BY completed_at DESC LIMIT 20
        """)
        data["recent_runs"] = [
            {
                "agent": r[0], "task": r[1], "site": r[2],
                "status": r[3], "duration": r[4], "completed": r[5]
            }
            for r in cursor.fetchall()
        ]
        conn.close()

        return data

    def run_full_cycle(self) -> Dict:
        """Exécute un cycle complet de tous les agents"""
        logger.info("=" * 50)
        logger.info("DÉMARRAGE CYCLE COMPLET")
        logger.info("=" * 50)

        start = time.time()
        results = {
            "started_at": datetime.now().isoformat(),
            "monitoring": {},
            "performance": {},
            "learning": {},
            "research": {}
        }

        # 1. Monitoring (priorité haute)
        results["monitoring"] = self.run_monitoring_cycle()

        # 2. Performance
        results["performance"] = self.run_performance_analysis()

        # 3. Learning
        results["learning"] = self.run_learning_scan()

        # 4. Research (moins fréquent)
        # results["research"] = self.run_research_cycle()

        duration = time.time() - start
        results["completed_at"] = datetime.now().isoformat()
        results["total_duration_seconds"] = duration

        logger.info("=" * 50)
        logger.info(f"CYCLE COMPLET TERMINÉ en {duration:.2f}s")
        logger.info("=" * 50)

        return results

    def start_scheduler(self):
        """Démarre le planificateur de tâches"""
        logger.info("Démarrage du scheduler...")
        self._running = True

        # Planification des tâches
        schedule.every(5).minutes.do(self.run_monitoring_cycle)
        schedule.every(1).hours.do(self.run_performance_analysis)
        schedule.every(6).hours.do(self.run_learning_scan)
        schedule.every(24).hours.do(self.run_research_cycle)

        while self._running:
            schedule.run_pending()
            time.sleep(60)

    def stop_scheduler(self):
        """Arrête le scheduler"""
        self._running = False
        logger.info("Scheduler arrêté")

    def generate_report(self) -> str:
        """Génère un rapport textuel"""
        data = self.get_dashboard_data()

        report = []
        report.append("=" * 60)
        report.append("RAPPORT SEO AGENT")
        report.append(f"Généré le: {data['timestamp']}")
        report.append("=" * 60)

        report.append("\n--- ÉTAT DES SITES ---")
        for site_id, info in data["sites"].items():
            uptime = info["uptime"]
            report.append(f"\n{site_id}:")
            report.append(f"  Uptime 24h: {uptime.get('uptime_percent', 'N/A')}%")
            report.append(f"  Temps moyen: {uptime.get('avg_response_ms', 'N/A')}ms")
            report.append(f"  Alertes actives: {info['alerts_active']}")
            report.append(f"  Améliorations suggérées: {info['improvements_pending']}")

        report.append("\n--- ÉTAT SERVEUR ---")
        server = data["server"]
        report.append(f"  Status: {server.get('status', 'N/A')}")
        report.append(f"  CPU Load: {server.get('cpu_load', 'N/A')}")
        report.append(f"  Mémoire: {server.get('memory_percent', 'N/A')}%")
        report.append(f"  Disque: {server.get('disk_percent', 'N/A')}%")

        if data["alerts"]:
            report.append("\n--- ALERTES ACTIVES ---")
            for alert in data["alerts"][:5]:
                report.append(f"  [{alert['severity'].upper()}] {alert['message']}")

        if data["improvements"]:
            report.append("\n--- TOP AMÉLIORATIONS ---")
            for imp in data["improvements"][:5]:
                report.append(f"  [{imp['priority'].upper()}] {imp['site_id']}: {imp['reason'][:50]}...")

        report.append("\n" + "=" * 60)
        return "\n".join(report)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master Agent - Coordinateur SEO")
    parser.add_argument("command", choices=[
        "status", "monitor", "performance", "learning", "research",
        "full", "dashboard", "report", "scheduler"
    ], help="Commande à exécuter")
    parser.add_argument("--site", help="Site spécifique (optionnel)")

    args = parser.parse_args()
    agent = MasterAgent()

    if args.command == "status":
        data = agent.get_dashboard_data()
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.command == "monitor":
        result = agent.run_monitoring_cycle()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "performance":
        result = agent.run_performance_analysis()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "learning":
        result = agent.run_learning_scan()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "research":
        result = agent.run_research_cycle()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "full":
        result = agent.run_full_cycle()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "dashboard":
        data = agent.get_dashboard_data()
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.command == "report":
        print(agent.generate_report())

    elif args.command == "scheduler":
        print("Démarrage du scheduler (Ctrl+C pour arrêter)...")
        try:
            agent.start_scheduler()
        except KeyboardInterrupt:
            agent.stop_scheduler()


if __name__ == "__main__":
    main()

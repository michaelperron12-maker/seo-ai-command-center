#!/usr/bin/env python3
"""
DB Helper - Utilitaire simple pour la base de données SEO-AI existante
S'adapte aux tables déjà créées par le système
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = '/opt/seo-agent/db/seo_agent.db'

class DBHelper:
    """Helper pour interagir avec la DB existante"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        """Retourne une connexion à la DB"""
        return sqlite3.connect(self.db_path)

    def query(self, sql, params=None):
        """Exécute une requête SELECT et retourne les résultats en dict"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def execute(self, sql, params=None):
        """Exécute une requête INSERT/UPDATE/DELETE"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id

    # ============================================
    # SITES (colonnes: nom, domaine, actif)
    # ============================================
    def get_all_sites(self):
        """Liste tous les sites actifs"""
        return self.query("SELECT id, nom as name, domaine as domain, chemin_local, categorie as category, actif as is_active FROM sites WHERE actif = 1")

    def get_site(self, domain):
        """Récupère un site par domaine"""
        results = self.query("SELECT id, nom as name, domaine as domain, chemin_local, categorie as category, actif as is_active FROM sites WHERE domaine = ?", [domain])
        return results[0] if results else None

    def add_site(self, domain, name, category=None):
        """Ajoute un nouveau site"""
        return self.execute(
            "INSERT OR IGNORE INTO sites (domaine, nom, categorie) VALUES (?, ?, ?)",
            [domain, name, category]
        )

    # ============================================
    # ALERTES (utilise site_alerts existant)
    # ============================================
    def get_alerts(self, site_id=None, active_only=True):
        """Récupère les alertes"""
        sql = "SELECT * FROM site_alerts WHERE 1=1"
        params = []

        if site_id:
            sql += " AND site_id = ?"
            params.append(site_id)

        if active_only:
            sql += " AND is_active = 1"

        sql += " ORDER BY created_at DESC"
        return self.query(sql, params)

    def create_alert(self, site_id, alert_type, message, priority='medium'):
        """Crée une alerte"""
        return self.execute(
            "INSERT INTO site_alerts (site_id, alert_type, message, priority) VALUES (?, ?, ?, ?)",
            [site_id, alert_type, message, priority]
        )

    def resolve_alert(self, alert_id):
        """Résout une alerte"""
        self.execute(
            "UPDATE site_alerts SET is_active = 0, resolved_at = ? WHERE id = ?",
            [datetime.now().isoformat(), alert_id]
        )

    # ============================================
    # AGENTS
    # ============================================
    def get_agents(self, active_only=True):
        """Liste les agents"""
        sql = "SELECT * FROM agents"
        if active_only:
            sql += " WHERE is_active = 1"
        return self.query(sql)

    def log_agent_run(self, agent_name, site_id, action, status, details=None):
        """Log une exécution d'agent"""
        return self.execute(
            "INSERT INTO agent_logs (agent_name, site_id, action, status, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [agent_name, site_id, action, status, json.dumps(details) if details else None, datetime.now().isoformat()]
        )

    # ============================================
    # TÂCHES
    # ============================================
    def get_pending_tasks(self, limit=50):
        """Récupère les tâches en attente"""
        return self.query(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority ASC, created_at ASC LIMIT ?",
            [limit]
        )

    def create_task(self, site_id, task_type, description, priority=5):
        """Crée une tâche"""
        return self.execute(
            "INSERT INTO tasks (site_id, task_type, description, priority, status) VALUES (?, ?, ?, ?, 'pending')",
            [site_id, task_type, description, priority]
        )

    def complete_task(self, task_id, result=None):
        """Marque une tâche comme terminée"""
        self.execute(
            "UPDATE tasks SET status = 'completed', result = ?, completed_at = ? WHERE id = ?",
            [json.dumps(result) if result else None, datetime.now().isoformat(), task_id]
        )

    # ============================================
    # SEO STATUS
    # ============================================
    def get_site_seo_status(self, site_id):
        """Récupère le statut SEO d'un site"""
        return self.query("SELECT * FROM site_status WHERE site_id = ?", [site_id])

    def update_seo_check(self, site_id, check_type, check_name, is_present, value=None):
        """Met à jour un check SEO"""
        self.execute('''
            INSERT OR REPLACE INTO site_status (site_id, check_type, check_name, is_present, value, last_checked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [site_id, check_type, check_name, is_present, value, datetime.now().isoformat()])

    # ============================================
    # STATISTIQUES DASHBOARD
    # ============================================
    def get_dashboard_stats(self):
        """Statistiques pour le dashboard"""
        stats = {}

        # Sites actifs
        result = self.query("SELECT COUNT(*) as count FROM sites WHERE actif = 1")
        stats['total_sites'] = result[0]['count'] if result else 0

        # Alertes actives
        result = self.query("SELECT COUNT(*) as count FROM site_alerts WHERE is_active = 1")
        stats['active_alerts'] = result[0]['count'] if result else 0

        # Alertes critiques
        result = self.query("SELECT COUNT(*) as count FROM site_alerts WHERE is_active = 1 AND priority = 'critical'")
        stats['critical_alerts'] = result[0]['count'] if result else 0

        # Tâches en attente
        result = self.query("SELECT COUNT(*) as count FROM tasks WHERE status = 'pending'")
        stats['pending_tasks'] = result[0]['count'] if result else 0

        # Agents actifs
        result = self.query("SELECT COUNT(*) as count FROM agents WHERE is_active = 1")
        stats['active_agents'] = result[0]['count'] if result else 0

        return stats

    # ============================================
    # VÉRIFICATION AVANT ACTION (anti-doublon)
    # ============================================
    def check_before_action(self, site_id, check_type, check_name):
        """Vérifie si un élément existe avant de le créer"""
        results = self.query('''
            SELECT is_present, value FROM site_status
            WHERE site_id = ? AND check_type = ? AND check_name = ?
        ''', [site_id, check_type, check_name])

        if results:
            return {'exists': bool(results[0]['is_present']), 'value': results[0]['value']}
        return {'exists': False, 'value': None}


# ============================================
# TEST ET AFFICHAGE
# ============================================
if __name__ == '__main__':
    db = DBHelper()

    print("="*60)
    print("STATUT BASE DE DONNÉES SEO-AI")
    print("="*60)

    # Stats dashboard
    stats = db.get_dashboard_stats()
    print("\n📊 STATISTIQUES:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Sites
    sites = db.get_all_sites()
    print(f"\n🌐 SITES ({len(sites)}):")
    for site in sites:
        print(f"   - {site.get('domain', site.get('name', 'N/A'))}")

    # Alertes actives
    alerts = db.get_alerts()
    print(f"\n⚠️ ALERTES ACTIVES ({len(alerts)}):")
    for alert in alerts[:5]:
        print(f"   - [{alert.get('priority', 'N/A')}] {alert.get('message', 'N/A')[:60]}")
    if len(alerts) > 5:
        print(f"   ... et {len(alerts) - 5} autres")

    # Tâches en attente
    tasks = db.get_pending_tasks(10)
    print(f"\n📋 TÂCHES EN ATTENTE ({len(tasks)}):")
    for task in tasks[:5]:
        print(f"   - {task.get('task_type', 'N/A')}: {task.get('description', 'N/A')[:50]}")

    print("\n" + "="*60)
    print("✅ Base de données opérationnelle")
    print("="*60)

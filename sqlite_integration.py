#!/usr/bin/env python3
"""
SQLite Integration - Base de données centrale pour SEO-AI
Roadmap complète d'intégration dans le système
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Chemin centralisé de la base de données
DB_PATH = '/opt/seo-agent/db/seo_agent.db'

class SEODatabase:
    """Gestionnaire central de la base de données SEO-AI"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_db_exists()
        self.init_all_tables()

    def _ensure_db_exists(self):
        """Crée le répertoire si nécessaire"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        """Retourne une connexion à la DB"""
        return sqlite3.connect(self.db_path)

    def init_all_tables(self):
        """Initialise toutes les tables du système"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # ========================================
        # TABLE 1: SITES - Sites gérés
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                name TEXT,
                category TEXT,
                ssh_host TEXT,
                ssh_user TEXT,
                ssh_key_path TEXT,
                web_root TEXT DEFAULT '/var/www/html',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        # ========================================
        # TABLE 2: SITE_STATUS - État SEO des sites
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                check_type TEXT,
                check_name TEXT,
                is_present BOOLEAN,
                value TEXT,
                last_checked TIMESTAMP,
                UNIQUE(site_id, check_type, check_name),
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 3: SEO_SCORES - Scores SEO
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seo_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                score_type TEXT,
                score_value INTEGER,
                max_score INTEGER DEFAULT 100,
                details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 4: SITE_ALERTS - Alertes par site (nouveau)
        # Note: La table 'alerts' existe déjà avec une autre structure
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                alert_type TEXT,
                severity TEXT,
                title TEXT,
                message TEXT,
                is_resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 5: AGENTS - Agents SEO
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT UNIQUE,
                agent_type TEXT,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                port INTEGER,
                last_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ========================================
        # TABLE 6: AGENT_LOGS - Logs des agents
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER,
                agent_name TEXT,
                site_id INTEGER,
                domain TEXT,
                action TEXT,
                status TEXT,
                message TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id),
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 7: TASKS - Tâches planifiées
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                task_type TEXT,
                task_name TEXT,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                assigned_agent TEXT,
                task_data TEXT,
                result TEXT,
                scheduled_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 8: CONTENT - Contenu généré
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                content_type TEXT,
                title TEXT,
                content TEXT,
                meta_description TEXT,
                keywords TEXT,
                status TEXT DEFAULT 'draft',
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 9: KEYWORDS - Mots-clés suivis
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                keyword TEXT,
                search_volume INTEGER,
                difficulty INTEGER,
                current_position INTEGER,
                target_position INTEGER DEFAULT 1,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 10: BACKLINKS - Liens entrants
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                source_url TEXT,
                target_url TEXT,
                anchor_text TEXT,
                is_dofollow BOOLEAN DEFAULT 1,
                domain_authority INTEGER,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 11: AI_DISCOVERY - Indexation AI
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_discovery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                ai_platform TEXT,
                is_indexed BOOLEAN DEFAULT 0,
                mentions_count INTEGER DEFAULT 0,
                last_mentioned TIMESTAMP,
                discovery_data TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 12: PERFORMANCE - Métriques perf
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                metric_type TEXT,
                metric_value REAL,
                page_url TEXT DEFAULT '/',
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 13: SSL_MONITORING - Certificats
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ssl_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                issuer TEXT,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                days_remaining INTEGER,
                is_valid BOOLEAN DEFAULT 1,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 14: UPTIME - Disponibilité
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uptime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                domain TEXT,
                status_code INTEGER,
                response_time_ms INTEGER,
                is_up BOOLEAN,
                error_message TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # ========================================
        # TABLE 15: CONFIG - Configuration système
        # ========================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE,
                config_value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Créer les index pour performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_site_status_domain ON site_status(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_site_alerts_domain ON site_alerts(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at)')

        conn.commit()
        conn.close()

        print("✅ Toutes les tables initialisées avec succès")

    # ========================================
    # MÉTHODES CRUD GÉNÉRIQUES
    # ========================================

    def insert(self, table, data):
        """Insert générique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        cursor.execute(query, list(data.values()))
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id

    def update(self, table, data, where_clause, where_values):
        """Update générique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
        cursor.execute(query, list(data.values()) + where_values)
        conn.commit()
        conn.close()

    def select(self, table, where_clause=None, where_values=None, order_by=None, limit=None):
        """Select générique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = f'SELECT * FROM {table}'
        if where_clause:
            query += f' WHERE {where_clause}'
        if order_by:
            query += f' ORDER BY {order_by}'
        if limit:
            query += f' LIMIT {limit}'

        cursor.execute(query, where_values or [])
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def delete(self, table, where_clause, where_values):
        """Delete générique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = f'DELETE FROM {table} WHERE {where_clause}'
        cursor.execute(query, where_values)
        conn.commit()
        conn.close()

    # ========================================
    # MÉTHODES SPÉCIFIQUES SITES
    # ========================================

    def add_site(self, domain, name, **kwargs):
        """Ajoute un nouveau site"""
        data = {
            'domain': domain,
            'name': name,
            'created_at': datetime.now().isoformat(),
            **kwargs
        }
        return self.insert('sites', data)

    def get_sites(self, active_only=True):
        """Liste tous les sites"""
        where = 'is_active = 1' if active_only else None
        return self.select('sites', where)

    def get_site_by_domain(self, domain):
        """Récupère un site par domaine"""
        results = self.select('sites', 'domain = ?', [domain])
        return results[0] if results else None

    # ========================================
    # MÉTHODES SPÉCIFIQUES ALERTES
    # ========================================

    def create_alert(self, domain, alert_type, severity, title, message, site_id=None):
        """Crée une nouvelle alerte"""
        data = {
            'site_id': site_id,
            'domain': domain,
            'alert_type': alert_type,
            'severity': severity,
            'title': title,
            'message': message,
            'created_at': datetime.now().isoformat()
        }
        return self.insert('site_alerts', data)

    def get_alerts(self, domain=None, unresolved_only=True):
        """Récupère les alertes"""
        conditions = []
        values = []

        if domain:
            conditions.append('domain = ?')
            values.append(domain)

        if unresolved_only:
            conditions.append('is_resolved = 0')

        where = ' AND '.join(conditions) if conditions else None
        return self.select('site_alerts', where, values, 'created_at DESC')

    def resolve_alert(self, alert_id, resolved_by='system'):
        """Résout une alerte"""
        self.update('site_alerts', {
            'is_resolved': 1,
            'resolved_at': datetime.now().isoformat(),
            'resolved_by': resolved_by
        }, 'id = ?', [alert_id])

    # ========================================
    # MÉTHODES SPÉCIFIQUES AGENTS
    # ========================================

    def register_agent(self, agent_name, agent_type, description=None, port=None):
        """Enregistre un agent"""
        data = {
            'agent_name': agent_name,
            'agent_type': agent_type,
            'description': description,
            'port': port,
            'created_at': datetime.now().isoformat()
        }
        return self.insert('agents', data)

    def log_agent_action(self, agent_name, domain, action, status, message, details=None):
        """Log une action d'agent"""
        data = {
            'agent_name': agent_name,
            'domain': domain,
            'action': action,
            'status': status,
            'message': message,
            'details': json.dumps(details) if details else None,
            'created_at': datetime.now().isoformat()
        }
        return self.insert('agent_logs', data)

    # ========================================
    # MÉTHODES SPÉCIFIQUES TÂCHES
    # ========================================

    def create_task(self, domain, task_type, task_name, priority=5, task_data=None):
        """Crée une nouvelle tâche"""
        data = {
            'domain': domain,
            'task_type': task_type,
            'task_name': task_name,
            'priority': priority,
            'task_data': json.dumps(task_data) if task_data else None,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        return self.insert('tasks', data)

    def get_pending_tasks(self, domain=None):
        """Récupère les tâches en attente"""
        conditions = ["status = 'pending'"]
        values = []

        if domain:
            conditions.append('domain = ?')
            values.append(domain)

        where = ' AND '.join(conditions)
        return self.select('tasks', where, values, 'priority ASC, created_at ASC')

    def complete_task(self, task_id, result=None):
        """Marque une tâche comme terminée"""
        self.update('tasks', {
            'status': 'completed',
            'result': json.dumps(result) if result else None,
            'completed_at': datetime.now().isoformat()
        }, 'id = ?', [task_id])

    # ========================================
    # STATISTIQUES ET RAPPORTS
    # ========================================

    def get_dashboard_stats(self):
        """Statistiques pour le dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Nombre de sites
        cursor.execute('SELECT COUNT(*) FROM sites WHERE is_active = 1')
        stats['total_sites'] = cursor.fetchone()[0]

        # Alertes non résolues
        cursor.execute('SELECT COUNT(*) FROM site_alerts WHERE is_resolved = 0')
        stats['unresolved_alerts'] = cursor.fetchone()[0]

        # Alertes critiques
        cursor.execute("SELECT COUNT(*) FROM site_alerts WHERE is_resolved = 0 AND severity = 'critical'")
        stats['critical_alerts'] = cursor.fetchone()[0]

        # Tâches en attente
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        stats['pending_tasks'] = cursor.fetchone()[0]

        # Agents actifs
        cursor.execute('SELECT COUNT(*) FROM agents WHERE is_active = 1')
        stats['active_agents'] = cursor.fetchone()[0]

        conn.close()
        return stats


# ========================================
# EXEMPLE D'UTILISATION
# ========================================

if __name__ == '__main__':
    print("="*60)
    print("INITIALISATION BASE DE DONNÉES SEO-AI")
    print("="*60)

    db = SEODatabase()

    # Ajouter les sites existants
    sites = [
        ('deneigement-excellence.ca', 'Déneigement Excellence'),
        ('paysagiste-excellence.ca', 'Paysagiste Excellence'),
        ('jcpeintre.com', 'JC Peintre'),
        ('seoparai.ca', 'SEO par AI'),
    ]

    for domain, name in sites:
        try:
            site_id = db.add_site(domain, name)
            print(f"✅ Site ajouté: {domain} (ID: {site_id})")
        except sqlite3.IntegrityError:
            print(f"ℹ️  Site existe déjà: {domain}")

    print("\n" + "="*60)
    print("STATISTIQUES DASHBOARD")
    print("="*60)

    stats = db.get_dashboard_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ Base de données prête!")
    print(f"📁 Chemin: {DB_PATH}")

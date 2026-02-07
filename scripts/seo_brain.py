#!/usr/bin/env python3
"""
SEO Brain - Cerveau principal du SEO Agent
Gère la logique de décision et l'orchestration des tâches
"""

import os
import sys
import sqlite3
import logging
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/seo-agent/brain.log', mode='a')
    ]
)
logger = logging.getLogger('SeoBrain')

# Chemins par défaut
DEFAULT_CONFIG_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/config/config.yaml'
DEFAULT_DB_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/data/seo_agent.db'


class SeoBrain:
    """
    Cerveau principal du SEO Agent.
    Orchestre toutes les décisions et actions.
    """

    def __init__(self, config_path: str = None, db_path: str = None):
        """
        Initialise le cerveau SEO.

        Args:
            config_path: Chemin vers le fichier de configuration YAML
            db_path: Chemin vers la base de données SQLite
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.db_path = db_path or DEFAULT_DB_PATH
        self.config = None
        self.conn = None

        # Charger la configuration
        self._load_config()

        # Initialiser la connexion DB
        self._init_database()

        logger.info("SeoBrain initialisé avec succès")

    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier YAML."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Configuration chargée depuis {self.config_path}")
            else:
                logger.warning(f"Fichier config non trouvé: {self.config_path}")
                self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Retourne la configuration par défaut."""
        return {
            'agent': {
                'name': 'SEO Agent',
                'max_articles_per_day': 3,
                'similarity_threshold': 0.70,
                'working_hours': {'start': 8, 'end': 22}
            },
            'api': {
                'claude_model': 'claude-3-sonnet-20240229',
                'openai_model': 'gpt-4-turbo-preview'
            },
            'notifications': {
                'telegram_enabled': True,
                'email_enabled': True,
                'sms_enabled': False
            },
            'kill_switch': {
                'max_publications_per_day': 5,
                'max_pending_drafts': 20,
                'max_similarity_average': 0.60,
                'max_site_errors': 10
            }
        }

    def _init_database(self) -> None:
        """Initialise la connexion à la base de données SQLite."""
        try:
            # Créer le répertoire si nécessaire
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

            # Créer les tables si elles n'existent pas
            self._create_tables()

            logger.info(f"Base de données connectée: {self.db_path}")
        except Exception as e:
            logger.error(f"Erreur connexion DB: {e}")
            raise

    def _create_tables(self) -> None:
        """Crée les tables nécessaires dans la base de données."""
        cursor = self.conn.cursor()

        # Table des contenus/drafts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE,
                content_html TEXT,
                content_md TEXT,
                meta_description TEXT,
                status TEXT DEFAULT 'draft',
                similarity_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP,
                url TEXT
            )
        ''')

        # Table du kill switch
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kill_switch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_active INTEGER DEFAULT 0,
                reason TEXT,
                activated_at TIMESTAMP,
                deactivate_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table des logs d'actions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                params TEXT,
                result TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table des erreurs du site
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT,
                url TEXT,
                status_code INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def get_config(self, key: str = None) -> Any:
        """
        Récupère la configuration ou une clé spécifique.

        Args:
            key: Clé de configuration (ex: 'agent.max_articles_per_day')

        Returns:
            Configuration complète ou valeur de la clé
        """
        if key is None:
            return self.config

        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Clé de configuration non trouvée: {key}")
            return None

    def check_kill_switch(self) -> Dict[str, Any]:
        """
        Vérifie si le kill switch est actif.

        Returns:
            Dict avec is_active, reason, deactivate_at
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT is_active, reason, deactivate_at
            FROM kill_switch
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()

        if row and row['is_active']:
            # Vérifier si la pause doit être désactivée
            if row['deactivate_at']:
                deactivate_at = datetime.fromisoformat(row['deactivate_at'])
                if datetime.now() > deactivate_at:
                    self._deactivate_kill_switch()
                    return {'is_active': False, 'reason': None, 'deactivate_at': None}

            return {
                'is_active': True,
                'reason': row['reason'],
                'deactivate_at': row['deactivate_at']
            }

        return {'is_active': False, 'reason': None, 'deactivate_at': None}

    def _deactivate_kill_switch(self) -> None:
        """Désactive le kill switch."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE kill_switch SET is_active = 0
            WHERE is_active = 1
        ''')
        self.conn.commit()
        logger.info("Kill switch désactivé automatiquement")

    def get_pending_drafts(self) -> List[Dict]:
        """
        Récupère la liste des drafts en attente de validation.

        Returns:
            Liste des drafts avec leurs informations
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title, slug, meta_description, similarity_score, created_at
            FROM contents
            WHERE status = 'draft'
            ORDER BY created_at DESC
        ''')

        drafts = []
        for row in cursor.fetchall():
            drafts.append({
                'id': row['id'],
                'title': row['title'],
                'slug': row['slug'],
                'meta_description': row['meta_description'],
                'similarity_score': row['similarity_score'],
                'created_at': row['created_at']
            })

        logger.info(f"{len(drafts)} drafts en attente")
        return drafts

    def get_today_publications_count(self) -> int:
        """Compte le nombre de publications aujourd'hui."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count FROM contents
            WHERE status = 'published'
            AND date(published_at) = ?
        ''', (today,))
        return cursor.fetchone()['count']

    def decide_daily_action(self) -> Dict[str, Any]:
        """
        Décide quelle action effectuer aujourd'hui.

        Returns:
            Dict avec action_type et params
        """
        logger.info("Analyse des actions possibles...")

        # Vérifier le kill switch
        ks_status = self.check_kill_switch()
        if ks_status['is_active']:
            logger.warning(f"Kill switch actif: {ks_status['reason']}")
            return {
                'action_type': 'pause',
                'reason': ks_status['reason'],
                'resume_at': ks_status['deactivate_at']
            }

        # Vérifier les heures de travail
        current_hour = datetime.now().hour
        working_hours = self.get_config('agent.working_hours')
        if working_hours:
            if current_hour < working_hours.get('start', 8) or current_hour > working_hours.get('end', 22):
                return {
                    'action_type': 'sleep',
                    'reason': 'Hors des heures de travail',
                    'resume_at': f"Demain à {working_hours.get('start', 8)}h"
                }

        # Vérifier le quota journalier
        today_count = self.get_today_publications_count()
        max_per_day = self.get_config('agent.max_articles_per_day') or 3

        if today_count >= max_per_day:
            return {
                'action_type': 'quota_reached',
                'reason': f'Quota atteint: {today_count}/{max_per_day} articles',
                'resume_at': 'Demain'
            }

        # Vérifier les drafts en attente
        pending_drafts = self.get_pending_drafts()
        if pending_drafts:
            return {
                'action_type': 'review_drafts',
                'params': {
                    'drafts_count': len(pending_drafts),
                    'drafts': pending_drafts[:5]  # Les 5 premiers
                }
            }

        # Générer du nouveau contenu
        return {
            'action_type': 'generate_content',
            'params': {
                'remaining_quota': max_per_day - today_count
            }
        }

    def run_task(self, task_type: str, params: Dict = None) -> Dict[str, Any]:
        """
        Exécute une tâche spécifique.

        Args:
            task_type: Type de tâche (generate, publish, check_similarity, etc.)
            params: Paramètres de la tâche

        Returns:
            Résultat de l'exécution
        """
        params = params or {}
        logger.info(f"Exécution tâche: {task_type} avec params: {params}")

        try:
            if task_type == 'generate':
                from content_generator import ContentGenerator
                generator = ContentGenerator()
                result = generator.generate(params.get('brief', ''))

            elif task_type == 'check_similarity':
                from similarity_checker import SimilarityChecker
                checker = SimilarityChecker(self.conn)
                result = checker.check(params.get('content', ''))

            elif task_type == 'publish':
                from publisher import Publisher
                publisher = Publisher()
                result = publisher.publish(params.get('content_id'))

            elif task_type == 'notify':
                from notifier import Notifier
                notifier = Notifier()
                result = notifier.send_telegram(params.get('message', ''))

            elif task_type == 'check_kill_switch':
                from kill_switch import KillSwitchManager
                ks_manager = KillSwitchManager(self.conn, self.config)
                result = ks_manager.run_all_checks()

            else:
                result = {'success': False, 'error': f'Tâche inconnue: {task_type}'}

            # Logger l'action
            self._log_action(task_type, params, result)

            return result

        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            self._log_action(task_type, params, error_result, status='error')
            logger.error(f"Erreur exécution tâche {task_type}: {e}")
            return error_result

    def _log_action(self, action_type: str, params: Dict, result: Dict, status: str = 'completed') -> None:
        """Enregistre une action dans les logs."""
        import json
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO action_logs (action_type, params, result, status)
            VALUES (?, ?, ?, ?)
        ''', (
            action_type,
            json.dumps(params) if params else None,
            json.dumps(result) if result else None,
            status
        ))
        self.conn.commit()

    def close(self) -> None:
        """Ferme les connexions."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion DB fermée")


def main():
    """Point d'entrée pour les tests standalone."""
    print("=== Test SeoBrain ===\n")

    try:
        brain = SeoBrain()

        # Test get_config
        print("1. Configuration:")
        print(f"   - Nom: {brain.get_config('agent.name')}")
        print(f"   - Max articles/jour: {brain.get_config('agent.max_articles_per_day')}")

        # Test kill switch
        print("\n2. Kill Switch:")
        ks_status = brain.check_kill_switch()
        print(f"   - Actif: {ks_status['is_active']}")
        if ks_status['is_active']:
            print(f"   - Raison: {ks_status['reason']}")

        # Test pending drafts
        print("\n3. Drafts en attente:")
        drafts = brain.get_pending_drafts()
        print(f"   - Nombre: {len(drafts)}")

        # Test décision
        print("\n4. Décision du jour:")
        decision = brain.decide_daily_action()
        print(f"   - Action: {decision['action_type']}")
        if 'reason' in decision:
            print(f"   - Raison: {decision['reason']}")

        brain.close()
        print("\n=== Tests terminés avec succès ===")

    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

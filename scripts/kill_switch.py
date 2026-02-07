#!/usr/bin/env python3
"""
Kill Switch - Système de sécurité pour le SEO Agent
Surveille les indicateurs critiques et peut mettre en pause l'agent
"""

import os
import sys
import sqlite3
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/seo-agent/kill_switch.log', mode='a')
    ]
)
logger = logging.getLogger('KillSwitch')

# Chemins par défaut
DEFAULT_DB_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/data/seo_agent.db'


class KillSwitchManager:
    """
    Gère le kill switch de sécurité pour le SEO Agent.
    Surveille les indicateurs et peut activer/désactiver la pause.
    """

    def __init__(self, conn: sqlite3.Connection = None, config: Dict = None):
        """
        Initialise le Kill Switch Manager.

        Args:
            conn: Connexion SQLite existante
            config: Configuration du kill switch
        """
        self.conn = conn
        self._own_connection = False

        # Configuration par défaut
        self.config = config or {}
        self.thresholds = self.config.get('kill_switch', {
            'max_publications_per_day': 5,
            'max_pending_drafts': 20,
            'max_similarity_average': 0.60,
            'max_site_errors': 10,
            'default_pause_hours': 24
        })

        # Site à surveiller
        self.site_url = self.config.get('site', {}).get('url', 'https://example.com')

        # Initialiser la connexion si non fournie
        if self.conn is None:
            self._init_connection()

        logger.info("KillSwitchManager initialisé")

    def _init_connection(self) -> None:
        """Crée une connexion à la base de données."""
        try:
            self.conn = sqlite3.connect(DEFAULT_DB_PATH)
            self.conn.row_factory = sqlite3.Row
            self._own_connection = True

            # Créer la table kill_switch si elle n'existe pas
            cursor = self.conn.cursor()
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
            self.conn.commit()

            logger.info(f"Connexion DB établie: {DEFAULT_DB_PATH}")
        except Exception as e:
            logger.error(f"Erreur connexion DB: {e}")
            raise

    def check_publication_rate(self) -> Dict[str, Any]:
        """
        Vérifie si le taux de publication est trop élevé.

        Returns:
            Dict avec is_triggered, current_count, max_allowed, message
        """
        try:
            cursor = self.conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT COUNT(*) as count FROM contents
                WHERE status = 'published'
                AND date(published_at) = ?
            ''', (today,))

            current_count = cursor.fetchone()['count']
            max_allowed = self.thresholds.get('max_publications_per_day', 5)
            is_triggered = current_count >= max_allowed

            result = {
                'check': 'publication_rate',
                'is_triggered': is_triggered,
                'current_count': current_count,
                'max_allowed': max_allowed,
                'message': f"Publications aujourd'hui: {current_count}/{max_allowed}"
            }

            if is_triggered:
                logger.warning(f"Kill switch: Taux de publication élevé ({current_count}/{max_allowed})")

            return result

        except Exception as e:
            logger.error(f"Erreur check publication_rate: {e}")
            return {
                'check': 'publication_rate',
                'is_triggered': False,
                'error': str(e)
            }

    def check_similarity_average(self) -> Dict[str, Any]:
        """
        Vérifie si la similarité moyenne du contenu est trop élevée.

        Returns:
            Dict avec is_triggered, current_average, max_allowed, message
        """
        try:
            from similarity_checker import SimilarityChecker

            checker = SimilarityChecker(self.conn)
            current_average = checker.get_average_similarity()
            max_allowed = self.thresholds.get('max_similarity_average', 0.60)
            is_triggered = current_average > max_allowed

            result = {
                'check': 'similarity_average',
                'is_triggered': is_triggered,
                'current_average': round(current_average, 4),
                'max_allowed': max_allowed,
                'message': f"Similarité moyenne: {current_average:.2%} (max: {max_allowed:.2%})"
            }

            if is_triggered:
                logger.warning(f"Kill switch: Similarité trop élevée ({current_average:.2%})")

            return result

        except ImportError:
            logger.warning("Module similarity_checker non disponible")
            return {
                'check': 'similarity_average',
                'is_triggered': False,
                'error': 'Module non disponible'
            }
        except Exception as e:
            logger.error(f"Erreur check similarity_average: {e}")
            return {
                'check': 'similarity_average',
                'is_triggered': False,
                'error': str(e)
            }

    def check_site_errors(self) -> Dict[str, Any]:
        """
        Vérifie s'il y a trop d'erreurs sur le site (404, 500).

        Returns:
            Dict avec is_triggered, error_count, max_allowed, errors, message
        """
        try:
            cursor = self.conn.cursor()

            # Vérifier les erreurs des dernières 24h
            yesterday = (datetime.now() - timedelta(hours=24)).isoformat()

            cursor.execute('''
                SELECT error_type, status_code, COUNT(*) as count
                FROM site_errors
                WHERE created_at > ?
                GROUP BY error_type, status_code
                ORDER BY count DESC
            ''', (yesterday,))

            errors = []
            total_errors = 0
            for row in cursor.fetchall():
                errors.append({
                    'type': row['error_type'],
                    'status_code': row['status_code'],
                    'count': row['count']
                })
                total_errors += row['count']

            max_allowed = self.thresholds.get('max_site_errors', 10)
            is_triggered = total_errors >= max_allowed

            result = {
                'check': 'site_errors',
                'is_triggered': is_triggered,
                'error_count': total_errors,
                'max_allowed': max_allowed,
                'errors': errors[:5],  # Top 5 erreurs
                'message': f"Erreurs site (24h): {total_errors}/{max_allowed}"
            }

            if is_triggered:
                logger.warning(f"Kill switch: Trop d'erreurs site ({total_errors})")

            return result

        except Exception as e:
            logger.error(f"Erreur check site_errors: {e}")
            return {
                'check': 'site_errors',
                'is_triggered': False,
                'error': str(e)
            }

    def check_pending_drafts(self) -> Dict[str, Any]:
        """
        Vérifie s'il y a trop de drafts en attente.

        Returns:
            Dict avec is_triggered, draft_count, max_allowed, message
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) as count FROM contents
                WHERE status = 'draft'
            ''')

            draft_count = cursor.fetchone()['count']
            max_allowed = self.thresholds.get('max_pending_drafts', 20)
            is_triggered = draft_count >= max_allowed

            result = {
                'check': 'pending_drafts',
                'is_triggered': is_triggered,
                'draft_count': draft_count,
                'max_allowed': max_allowed,
                'message': f"Drafts en attente: {draft_count}/{max_allowed}"
            }

            if is_triggered:
                logger.warning(f"Kill switch: Trop de drafts ({draft_count})")

            return result

        except Exception as e:
            logger.error(f"Erreur check pending_drafts: {e}")
            return {
                'check': 'pending_drafts',
                'is_triggered': False,
                'error': str(e)
            }

    def check_site_health(self) -> Dict[str, Any]:
        """
        Vérifie si le site est accessible (ping HTTP).

        Returns:
            Dict avec is_triggered, status_code, response_time, message
        """
        try:
            start_time = datetime.now()
            response = requests.get(self.site_url, timeout=10)
            response_time = (datetime.now() - start_time).total_seconds()

            is_down = response.status_code >= 500
            is_slow = response_time > 5.0  # Plus de 5 secondes

            result = {
                'check': 'site_health',
                'is_triggered': is_down or is_slow,
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'is_down': is_down,
                'is_slow': is_slow,
                'message': f"Site: {response.status_code} ({response_time:.2f}s)"
            }

            if is_down:
                logger.error(f"Kill switch: Site down ({response.status_code})")
            elif is_slow:
                logger.warning(f"Kill switch: Site lent ({response_time:.2f}s)")

            return result

        except requests.exceptions.Timeout:
            logger.error("Kill switch: Site timeout")
            return {
                'check': 'site_health',
                'is_triggered': True,
                'error': 'Timeout',
                'message': 'Site inaccessible (timeout)'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Kill switch: Erreur site - {e}")
            return {
                'check': 'site_health',
                'is_triggered': True,
                'error': str(e),
                'message': f'Erreur connexion site: {e}'
            }

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Exécute tous les checks de sécurité.

        Returns:
            Dict avec tous les résultats et si le kill switch doit être activé
        """
        logger.info("Exécution de tous les checks de sécurité...")

        checks = {
            'publication_rate': self.check_publication_rate(),
            'similarity_average': self.check_similarity_average(),
            'site_errors': self.check_site_errors(),
            'pending_drafts': self.check_pending_drafts(),
            # 'site_health': self.check_site_health()  # Désactivé par défaut
        }

        # Déterminer si le kill switch doit être activé
        triggered_checks = [
            name for name, result in checks.items()
            if result.get('is_triggered', False)
        ]

        should_activate = len(triggered_checks) > 0

        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'triggered_checks': triggered_checks,
            'should_activate': should_activate
        }

        if should_activate:
            reasons = [checks[name].get('message', name) for name in triggered_checks]
            result['reason'] = '; '.join(reasons)
            logger.warning(f"Kill switch devrait être activé: {result['reason']}")
        else:
            logger.info("Tous les checks passés, pas de kill switch nécessaire")

        return result

    def activate_pause(self, reason: str, duration_hours: int = None) -> Dict[str, Any]:
        """
        Active la pause du SEO Agent.

        Args:
            reason: Raison de la pause
            duration_hours: Durée de la pause en heures

        Returns:
            Dict avec success, activated_at, deactivate_at
        """
        try:
            duration = duration_hours or self.thresholds.get('default_pause_hours', 24)
            activated_at = datetime.now()
            deactivate_at = activated_at + timedelta(hours=duration)

            cursor = self.conn.cursor()

            # Désactiver les pauses précédentes
            cursor.execute('UPDATE kill_switch SET is_active = 0 WHERE is_active = 1')

            # Créer la nouvelle pause
            cursor.execute('''
                INSERT INTO kill_switch (is_active, reason, activated_at, deactivate_at)
                VALUES (1, ?, ?, ?)
            ''', (reason, activated_at.isoformat(), deactivate_at.isoformat()))

            self.conn.commit()

            logger.warning(f"Kill switch ACTIVÉ: {reason} (jusqu'à {deactivate_at})")

            # Notifier si possible
            try:
                from notifier import Notifier
                notifier = Notifier()
                notifier.send_telegram(
                    f"KILL SWITCH ACTIVE\n\nRaison: {reason}\n"
                    f"Durée: {duration}h\n"
                    f"Reprise: {deactivate_at.strftime('%d/%m/%Y %H:%M')}"
                )
            except Exception as e:
                logger.warning(f"Notification non envoyée: {e}")

            return {
                'success': True,
                'is_active': True,
                'reason': reason,
                'activated_at': activated_at.isoformat(),
                'deactivate_at': deactivate_at.isoformat(),
                'duration_hours': duration
            }

        except Exception as e:
            logger.error(f"Erreur activation kill switch: {e}")
            return {'success': False, 'error': str(e)}

    def deactivate_pause(self) -> Dict[str, Any]:
        """
        Désactive manuellement la pause.

        Returns:
            Dict avec success, message
        """
        try:
            cursor = self.conn.cursor()

            # Vérifier si une pause est active
            cursor.execute('SELECT id, reason FROM kill_switch WHERE is_active = 1')
            active = cursor.fetchone()

            if not active:
                return {
                    'success': True,
                    'message': 'Aucune pause active à désactiver'
                }

            # Désactiver
            cursor.execute('UPDATE kill_switch SET is_active = 0 WHERE is_active = 1')
            self.conn.commit()

            logger.info(f"Kill switch désactivé manuellement (était: {active['reason']})")

            return {
                'success': True,
                'message': 'Pause désactivée avec succès',
                'previous_reason': active['reason']
            }

        except Exception as e:
            logger.error(f"Erreur désactivation: {e}")
            return {'success': False, 'error': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """
        Récupère le statut actuel du kill switch.

        Returns:
            Dict avec is_active, reason, activated_at, deactivate_at, time_remaining
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT is_active, reason, activated_at, deactivate_at
                FROM kill_switch
                WHERE is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            ''')

            row = cursor.fetchone()

            if row:
                deactivate_at = datetime.fromisoformat(row['deactivate_at'])
                time_remaining = (deactivate_at - datetime.now()).total_seconds()

                if time_remaining < 0:
                    # La pause a expiré, la désactiver
                    self.deactivate_pause()
                    return {
                        'is_active': False,
                        'message': 'Pause expirée et désactivée'
                    }

                return {
                    'is_active': True,
                    'reason': row['reason'],
                    'activated_at': row['activated_at'],
                    'deactivate_at': row['deactivate_at'],
                    'time_remaining_seconds': int(time_remaining),
                    'time_remaining_hours': round(time_remaining / 3600, 1)
                }

            return {
                'is_active': False,
                'message': 'Agent opérationnel'
            }

        except Exception as e:
            logger.error(f"Erreur get_status: {e}")
            return {'is_active': False, 'error': str(e)}

    def close(self) -> None:
        """Ferme la connexion si elle nous appartient."""
        if self._own_connection and self.conn:
            self.conn.close()
            logger.info("Connexion DB fermée")


def main():
    """Point d'entrée pour les tests standalone."""
    print("=== Test Kill Switch Manager ===\n")

    try:
        ks = KillSwitchManager()

        # Statut actuel
        print("1. Statut actuel:")
        status = ks.get_status()
        print(f"   - Actif: {status.get('is_active', False)}")
        if status.get('is_active'):
            print(f"   - Raison: {status.get('reason')}")
            print(f"   - Temps restant: {status.get('time_remaining_hours', 0)}h")

        # Exécuter tous les checks
        print("\n2. Exécution des checks:")
        results = ks.run_all_checks()

        for name, check in results['checks'].items():
            triggered = "ALERTE" if check.get('is_triggered') else "OK"
            print(f"   - {name}: {triggered}")
            print(f"     {check.get('message', 'N/A')}")

        print(f"\n3. Résumé:")
        print(f"   - Checks déclenchés: {results['triggered_checks']}")
        print(f"   - Activation requise: {results['should_activate']}")

        # Test d'activation/désactivation (commenté pour éviter les effets)
        # print("\n4. Test activation:")
        # activate_result = ks.activate_pause("Test automatique", 1)
        # print(f"   - Activé: {activate_result['success']}")
        #
        # print("\n5. Test désactivation:")
        # deactivate_result = ks.deactivate_pause()
        # print(f"   - Désactivé: {deactivate_result['success']}")

        ks.close()
        print("\n=== Test terminé ===")

    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

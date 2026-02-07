#!/usr/bin/env python3
"""
Notifier - Système de notifications multi-canal
Telegram, Email et SMS pour le SEO Agent
"""

import os
import sys
import json
import logging
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/seo-agent/notifier.log', mode='a')
    ]
)
logger = logging.getLogger('Notifier')

# Chemins par défaut
DEFAULT_DB_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/data/seo_agent.db'


class Notifier:
    """
    Système de notifications multi-canal pour le SEO Agent.
    Supporte Telegram, Email et SMS (via Twilio).
    """

    def __init__(self, config: Dict = None):
        """
        Initialise le notifier.

        Args:
            config: Configuration des notifications
        """
        self.config = config or self._load_config()

        # Configuration Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN',
                                        self.config.get('telegram', {}).get('token'))
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID',
                                          self.config.get('telegram', {}).get('chat_id'))

        # Configuration Email
        self.smtp_host = os.getenv('SMTP_HOST',
                                   self.config.get('email', {}).get('host', 'smtp.gmail.com'))
        self.smtp_port = int(os.getenv('SMTP_PORT',
                                       self.config.get('email', {}).get('port', 587)))
        self.smtp_user = os.getenv('SMTP_USER',
                                   self.config.get('email', {}).get('user'))
        self.smtp_password = os.getenv('SMTP_PASSWORD',
                                       self.config.get('email', {}).get('password'))
        self.email_from = os.getenv('EMAIL_FROM',
                                    self.config.get('email', {}).get('from', self.smtp_user))
        self.email_to = os.getenv('EMAIL_TO',
                                  self.config.get('email', {}).get('to'))

        # Configuration Twilio (SMS)
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID',
                                    self.config.get('twilio', {}).get('account_sid'))
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN',
                                      self.config.get('twilio', {}).get('auth_token'))
        self.twilio_from = os.getenv('TWILIO_FROM_NUMBER',
                                     self.config.get('twilio', {}).get('from_number'))
        self.twilio_to = os.getenv('TWILIO_TO_NUMBER',
                                   self.config.get('twilio', {}).get('to_number'))

        # Base de données pour historique
        self.conn = None
        self._init_db()

        logger.info("Notifier initialisé")

    def _load_config(self) -> Dict:
        """Charge la configuration depuis le fichier ou retourne les valeurs par défaut."""
        config_path = '/home/serinityvault/Desktop/projet web/seo-agent-stack/config/config.yaml'

        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('notifications', {})
        except Exception as e:
            logger.warning(f"Erreur chargement config: {e}")

        return {}

    def _init_db(self) -> None:
        """Initialise la table d'historique des notifications."""
        try:
            db_dir = os.path.dirname(DEFAULT_DB_PATH)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            self.conn = sqlite3.connect(DEFAULT_DB_PATH)
            self.conn.row_factory = sqlite3.Row

            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    recipient TEXT,
                    subject TEXT,
                    message TEXT,
                    status TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Erreur init DB notifications: {e}")

    def _log_notification(self, channel: str, recipient: str, subject: str,
                          message: str, status: str, error: str = None) -> None:
        """Enregistre une notification dans l'historique."""
        try:
            if self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO notification_logs
                    (channel, recipient, subject, message, status, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (channel, recipient, subject, message[:500], status, error))
                self.conn.commit()
        except Exception as e:
            logger.warning(f"Erreur log notification: {e}")

    def send_telegram(self, message: str, buttons: List[Dict] = None,
                      parse_mode: str = 'HTML') -> Dict[str, Any]:
        """
        Envoie un message via Telegram.

        Args:
            message: Texte du message
            buttons: Liste de boutons inline (optionnel)
                     Format: [{"text": "Label", "callback_data": "action"}]
            parse_mode: Mode de parsing (HTML ou Markdown)

        Returns:
            Dict avec success, message_id ou error
        """
        if not self.telegram_token or not self.telegram_chat_id:
            error = "Configuration Telegram manquante"
            logger.warning(error)
            return {'success': False, 'error': error}

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            # Ajouter les boutons si fournis
            if buttons:
                inline_keyboard = [[btn] for btn in buttons]
                payload['reply_markup'] = json.dumps({
                    'inline_keyboard': inline_keyboard
                })

            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get('ok'):
                message_id = result['result']['message_id']
                logger.info(f"Telegram envoyé: {message[:50]}...")
                self._log_notification('telegram', self.telegram_chat_id,
                                       None, message, 'sent')
                return {
                    'success': True,
                    'message_id': message_id,
                    'chat_id': self.telegram_chat_id
                }
            else:
                error = result.get('description', 'Erreur inconnue')
                logger.error(f"Erreur Telegram: {error}")
                self._log_notification('telegram', self.telegram_chat_id,
                                       None, message, 'failed', error)
                return {'success': False, 'error': error}

        except requests.exceptions.RequestException as e:
            error = f"Erreur réseau: {e}"
            logger.error(error)
            return {'success': False, 'error': error}
        except Exception as e:
            error = f"Erreur Telegram: {e}"
            logger.error(error)
            return {'success': False, 'error': error}

    def send_email(self, subject: str, body: str, html_body: str = None,
                   to: str = None) -> Dict[str, Any]:
        """
        Envoie un email.

        Args:
            subject: Sujet de l'email
            body: Corps du message (texte)
            html_body: Corps HTML optionnel
            to: Destinataire (utilise la config par défaut si non fourni)

        Returns:
            Dict avec success ou error
        """
        recipient = to or self.email_to

        if not all([self.smtp_host, self.smtp_user, self.smtp_password, recipient]):
            error = "Configuration email incomplète"
            logger.warning(error)
            return {'success': False, 'error': error}

        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = recipient

            # Ajouter le corps texte
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Ajouter le corps HTML si fourni
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Envoyer
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.email_from, [recipient], msg.as_string())

            logger.info(f"Email envoyé à {recipient}: {subject}")
            self._log_notification('email', recipient, subject, body, 'sent')

            return {
                'success': True,
                'to': recipient,
                'subject': subject
            }

        except smtplib.SMTPException as e:
            error = f"Erreur SMTP: {e}"
            logger.error(error)
            self._log_notification('email', recipient, subject, body, 'failed', error)
            return {'success': False, 'error': error}
        except Exception as e:
            error = f"Erreur email: {e}"
            logger.error(error)
            return {'success': False, 'error': error}

    def send_sms(self, message: str, to: str = None) -> Dict[str, Any]:
        """
        Envoie un SMS via Twilio.

        Args:
            message: Texte du message (max 160 caractères recommandé)
            to: Numéro de téléphone destinataire (format E.164)

        Returns:
            Dict avec success, message_sid ou error
        """
        recipient = to or self.twilio_to

        if not all([self.twilio_sid, self.twilio_token, self.twilio_from, recipient]):
            error = "Configuration Twilio incomplète"
            logger.warning(error)
            return {'success': False, 'error': error}

        try:
            from twilio.rest import Client

            client = Client(self.twilio_sid, self.twilio_token)

            # Tronquer le message si nécessaire
            if len(message) > 1600:
                message = message[:1597] + "..."

            sms = client.messages.create(
                body=message,
                from_=self.twilio_from,
                to=recipient
            )

            logger.info(f"SMS envoyé à {recipient}: {message[:50]}...")
            self._log_notification('sms', recipient, None, message, 'sent')

            return {
                'success': True,
                'message_sid': sms.sid,
                'to': recipient,
                'status': sms.status
            }

        except ImportError:
            error = "Module twilio non installé"
            logger.error(error)
            return {'success': False, 'error': error}
        except Exception as e:
            error = f"Erreur Twilio: {e}"
            logger.error(error)
            self._log_notification('sms', recipient, None, message, 'failed', error)
            return {'success': False, 'error': error}

    def notify_new_draft(self, content_id: int) -> Dict[str, Any]:
        """
        Notifie qu'un nouveau draft est prêt pour validation.

        Args:
            content_id: ID du contenu à valider

        Returns:
            Dict avec les résultats des notifications
        """
        try:
            # Récupérer les infos du contenu
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, title, slug, meta_description, similarity_score, created_at
                FROM contents
                WHERE id = ?
            ''', (content_id,))

            row = cursor.fetchone()

            if not row:
                return {'success': False, 'error': f'Contenu {content_id} non trouvé'}

            content = dict(row)
            similarity = content.get('similarity_score', 0) or 0

            # Construire le message
            message = (
                f"<b>Nouveau Draft SEO</b>\n\n"
                f"Titre: {content['title']}\n"
                f"Slug: {content['slug']}\n"
                f"Similarité: {similarity:.1%}\n"
                f"Créé: {content['created_at']}\n\n"
                f"<i>{content.get('meta_description', 'Pas de description')}</i>"
            )

            # Boutons d'action
            buttons = [
                {"text": "Approuver", "callback_data": f"approve_{content_id}"},
                {"text": "Rejeter", "callback_data": f"reject_{content_id}"},
                {"text": "Voir", "callback_data": f"view_{content_id}"}
            ]

            results = {}

            # Envoyer via Telegram
            telegram_result = self.send_telegram(message, buttons)
            results['telegram'] = telegram_result

            # Envoyer par email si configuré
            if self.email_to:
                email_body = f"""
Nouveau Draft SEO à valider

Titre: {content['title']}
Slug: {content['slug']}
Similarité: {similarity:.1%}
Créé: {content['created_at']}

Description: {content.get('meta_description', 'Pas de description')}

--
Pour valider ce contenu, connectez-vous au panneau d'administration.
                """

                email_result = self.send_email(
                    subject=f"[SEO Agent] Nouveau draft: {content['title'][:50]}",
                    body=email_body
                )
                results['email'] = email_result

            # Résumé
            success_count = sum(1 for r in results.values() if r.get('success'))

            logger.info(f"Notification draft {content_id}: {success_count}/{len(results)} envoyées")

            return {
                'success': success_count > 0,
                'content_id': content_id,
                'notifications': results,
                'sent_count': success_count
            }

        except Exception as e:
            error = f"Erreur notification draft: {e}"
            logger.error(error)
            return {'success': False, 'error': error}

    def notify_kill_switch(self, reason: str, duration_hours: int) -> Dict[str, Any]:
        """
        Notifie que le kill switch a été activé.

        Args:
            reason: Raison de l'activation
            duration_hours: Durée de la pause

        Returns:
            Dict avec les résultats des notifications
        """
        message = (
            f"ALERTE KILL SWITCH\n\n"
            f"Le SEO Agent est en pause.\n\n"
            f"Raison: {reason}\n"
            f"Durée: {duration_hours}h\n"
            f"Reprise automatique prévue."
        )

        results = {}

        # Telegram (prioritaire)
        results['telegram'] = self.send_telegram(message)

        # SMS pour les urgences
        if self.twilio_to:
            sms_msg = f"SEO Agent PAUSE: {reason[:100]} ({duration_hours}h)"
            results['sms'] = self.send_sms(sms_msg)

        return {
            'success': any(r.get('success') for r in results.values()),
            'notifications': results
        }

    def notify_publication(self, title: str, url: str) -> Dict[str, Any]:
        """
        Notifie qu'un article a été publié.

        Args:
            title: Titre de l'article
            url: URL de l'article publié

        Returns:
            Dict avec le résultat de la notification
        """
        message = (
            f"Article Publié\n\n"
            f"Titre: {title}\n"
            f"URL: {url}\n\n"
            f"Publication automatique réussie."
        )

        return self.send_telegram(message)

    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """
        Récupère l'historique des notifications.

        Args:
            limit: Nombre maximum de notifications à retourner

        Returns:
            Liste des notifications récentes
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, channel, recipient, subject, message, status, error, created_at
                FROM notification_logs
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Erreur historique: {e}")
            return []

    def close(self) -> None:
        """Ferme les connexions."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion DB fermée")


def main():
    """Point d'entrée pour les tests standalone."""
    print("=== Test Notifier ===\n")

    try:
        notifier = Notifier()

        # Vérifier la configuration
        print("1. Configuration:")
        print(f"   - Telegram: {'Configuré' if notifier.telegram_token else 'Non configuré'}")
        print(f"   - Email: {'Configuré' if notifier.smtp_user else 'Non configuré'}")
        print(f"   - SMS: {'Configuré' if notifier.twilio_sid else 'Non configuré'}")

        # Test Telegram (si configuré)
        if notifier.telegram_token:
            print("\n2. Test Telegram:")
            result = notifier.send_telegram(
                "Test SEO Agent\n\nCeci est un message de test.",
                buttons=[{"text": "OK", "callback_data": "test_ok"}]
            )
            print(f"   - Succès: {result.get('success')}")
            if result.get('error'):
                print(f"   - Erreur: {result.get('error')}")

        # Historique
        print("\n3. Historique récent:")
        history = notifier.get_notification_history(5)
        if history:
            for notif in history:
                print(f"   - [{notif['channel']}] {notif['status']} - {notif['created_at']}")
        else:
            print("   - Aucune notification enregistrée")

        notifier.close()
        print("\n=== Test terminé ===")

    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

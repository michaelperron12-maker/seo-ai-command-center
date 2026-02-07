#!/usr/bin/env python3
"""
Publisher - Publie le contenu validé sur le site
Génère les fichiers HTML et met à jour le sitemap
"""

import os
import sys
import sqlite3
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from xml.etree import ElementTree as ET

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/seo-agent/publisher.log', mode='a')
    ]
)
logger = logging.getLogger('Publisher')

# Chemins par défaut
DEFAULT_DB_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/data/seo_agent.db'
DEFAULT_SITE_PATH = '/var/www/site'
DEFAULT_BLOG_PATH = '/var/www/site/blog'
DEFAULT_SITEMAP_PATH = '/var/www/site/sitemap.xml'
DEFAULT_BASE_URL = 'https://example.com'


class Publisher:
    """
    Publie le contenu validé sur le site web.
    Gère la création des fichiers HTML et la mise à jour du sitemap.
    """

    def __init__(self,
                 db_path: str = None,
                 site_path: str = None,
                 base_url: str = None):
        """
        Initialise le publisher.

        Args:
            db_path: Chemin vers la base de données
            site_path: Chemin vers le répertoire du site
            base_url: URL de base du site
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.site_path = site_path or DEFAULT_SITE_PATH
        self.blog_path = os.path.join(self.site_path, 'blog')
        self.sitemap_path = os.path.join(self.site_path, 'sitemap.xml')
        self.base_url = base_url or DEFAULT_BASE_URL

        self.conn = None
        self._init_connection()

        # Créer les répertoires si nécessaire
        self._ensure_directories()

        logger.info(f"Publisher initialisé (site: {self.site_path})")

    def _init_connection(self) -> None:
        """Initialise la connexion à la base de données."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connexion DB établie: {self.db_path}")
        except Exception as e:
            logger.error(f"Erreur connexion DB: {e}")
            raise

    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires s'ils n'existent pas."""
        try:
            os.makedirs(self.blog_path, exist_ok=True)
            logger.info(f"Répertoire blog vérifié: {self.blog_path}")
        except PermissionError as e:
            logger.warning(f"Permission refusée pour créer {self.blog_path}: {e}")

    def _get_content(self, content_id: int) -> Optional[Dict]:
        """
        Récupère un contenu de la base de données.

        Args:
            content_id: ID du contenu

        Returns:
            Dict avec les informations du contenu ou None
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title, slug, content_html, content_md,
                   meta_description, status, created_at
            FROM contents
            WHERE id = ?
        ''', (content_id,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def _generate_slug(self, title: str) -> str:
        """
        Génère un slug URL-friendly à partir du titre.

        Args:
            title: Titre de l'article

        Returns:
            Slug formaté
        """
        # Convertir en minuscules
        slug = title.lower()

        # Remplacer les accents
        accents = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        for accent, replacement in accents.items():
            slug = slug.replace(accent, replacement)

        # Remplacer les espaces et caractères spéciaux par des tirets
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # Supprimer les tirets en début et fin
        slug = slug.strip('-')

        # Limiter la longueur
        slug = slug[:80]

        return slug

    def _write_html_file(self, slug: str, html_content: str) -> str:
        """
        Écrit le fichier HTML sur le disque.

        Args:
            slug: Slug de l'article
            html_content: Contenu HTML complet

        Returns:
            Chemin du fichier créé
        """
        # Créer le répertoire de l'article
        article_dir = os.path.join(self.blog_path, slug)
        os.makedirs(article_dir, exist_ok=True)

        # Écrire le fichier index.html
        file_path = os.path.join(article_dir, 'index.html')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Fichier HTML créé: {file_path}")
        return file_path

    def _update_sitemap(self, slug: str, last_mod: str = None) -> bool:
        """
        Met à jour le sitemap.xml avec la nouvelle URL.

        Args:
            slug: Slug de l'article
            last_mod: Date de dernière modification (ISO format)

        Returns:
            True si succès, False sinon
        """
        try:
            url = f"{self.base_url}/blog/{slug}/"
            last_mod = last_mod or datetime.now().strftime('%Y-%m-%d')

            # Charger ou créer le sitemap
            if os.path.exists(self.sitemap_path):
                tree = ET.parse(self.sitemap_path)
                root = tree.getroot()
            else:
                # Créer un nouveau sitemap
                root = ET.Element('urlset')
                root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
                tree = ET.ElementTree(root)

            # Namespace pour sitemap
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Vérifier si l'URL existe déjà
            existing_urls = root.findall('.//ns:loc', ns) if ns else root.findall('.//loc')
            for loc in existing_urls:
                if loc.text == url:
                    # Mettre à jour la date
                    parent = loc.getparent() if hasattr(loc, 'getparent') else None
                    if parent is not None:
                        lastmod = parent.find('ns:lastmod', ns) if ns else parent.find('lastmod')
                        if lastmod is not None:
                            lastmod.text = last_mod
                    logger.info(f"URL existante mise à jour dans sitemap: {url}")
                    tree.write(self.sitemap_path, encoding='utf-8', xml_declaration=True)
                    return True

            # Ajouter la nouvelle URL
            url_elem = ET.SubElement(root, 'url')
            loc_elem = ET.SubElement(url_elem, 'loc')
            loc_elem.text = url
            lastmod_elem = ET.SubElement(url_elem, 'lastmod')
            lastmod_elem.text = last_mod
            changefreq_elem = ET.SubElement(url_elem, 'changefreq')
            changefreq_elem.text = 'monthly'
            priority_elem = ET.SubElement(url_elem, 'priority')
            priority_elem.text = '0.8'

            # Écrire le fichier
            tree.write(self.sitemap_path, encoding='utf-8', xml_declaration=True)

            logger.info(f"URL ajoutée au sitemap: {url}")
            return True

        except Exception as e:
            logger.error(f"Erreur mise à jour sitemap: {e}")
            return False

    def _update_content_status(self, content_id: int, url: str) -> None:
        """
        Met à jour le statut du contenu dans la base de données.

        Args:
            content_id: ID du contenu
            url: URL de publication
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE contents
            SET status = 'published',
                published_at = ?,
                url = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), url, content_id))
        self.conn.commit()
        logger.info(f"Contenu {content_id} marqué comme publié")

    def publish(self, content_id: int) -> Dict:
        """
        Publie un contenu validé.

        Args:
            content_id: ID du contenu à publier

        Returns:
            Dict avec success, url, file_path ou error
        """
        try:
            # Récupérer le contenu
            content = self._get_content(content_id)

            if not content:
                return {
                    'success': False,
                    'error': f'Contenu {content_id} non trouvé'
                }

            if content['status'] == 'published':
                return {
                    'success': False,
                    'error': f'Contenu {content_id} déjà publié',
                    'url': content.get('url')
                }

            if not content['content_html']:
                return {
                    'success': False,
                    'error': 'Contenu HTML manquant'
                }

            # Générer ou récupérer le slug
            slug = content['slug'] or self._generate_slug(content['title'])

            # Écrire le fichier HTML
            file_path = self._write_html_file(slug, content['content_html'])

            # Construire l'URL
            url = f"{self.base_url}/blog/{slug}/"

            # Mettre à jour le sitemap
            sitemap_updated = self._update_sitemap(slug)

            # Mettre à jour la base de données
            self._update_content_status(content_id, url)

            result = {
                'success': True,
                'content_id': content_id,
                'title': content['title'],
                'slug': slug,
                'url': url,
                'file_path': file_path,
                'sitemap_updated': sitemap_updated,
                'published_at': datetime.now().isoformat()
            }

            logger.info(f"Publication réussie: {url}")
            return result

        except Exception as e:
            logger.error(f"Erreur publication: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def unpublish(self, content_id: int) -> Dict:
        """
        Dépublie un contenu (supprime le fichier mais garde en base).

        Args:
            content_id: ID du contenu à dépublier

        Returns:
            Dict avec success ou error
        """
        try:
            content = self._get_content(content_id)

            if not content:
                return {'success': False, 'error': f'Contenu {content_id} non trouvé'}

            slug = content['slug']
            if slug:
                article_dir = os.path.join(self.blog_path, slug)
                if os.path.exists(article_dir):
                    shutil.rmtree(article_dir)
                    logger.info(f"Répertoire supprimé: {article_dir}")

            # Mettre à jour le statut
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE contents
                SET status = 'unpublished',
                    url = NULL
                WHERE id = ?
            ''', (content_id,))
            self.conn.commit()

            return {
                'success': True,
                'content_id': content_id,
                'message': 'Contenu dépublié avec succès'
            }

        except Exception as e:
            logger.error(f"Erreur dépublication: {e}")
            return {'success': False, 'error': str(e)}

    def get_published_count(self, date: str = None) -> int:
        """
        Compte le nombre d'articles publiés.

        Args:
            date: Date spécifique (YYYY-MM-DD) ou None pour tous

        Returns:
            Nombre d'articles publiés
        """
        cursor = self.conn.cursor()

        if date:
            cursor.execute('''
                SELECT COUNT(*) as count FROM contents
                WHERE status = 'published'
                AND date(published_at) = ?
            ''', (date,))
        else:
            cursor.execute('''
                SELECT COUNT(*) as count FROM contents
                WHERE status = 'published'
            ''')

        return cursor.fetchone()['count']

    def close(self) -> None:
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion DB fermée")


def main():
    """Point d'entrée pour les tests standalone."""
    print("=== Test Publisher ===\n")

    try:
        publisher = Publisher()

        # Afficher les stats
        total_published = publisher.get_published_count()
        today = datetime.now().strftime('%Y-%m-%d')
        today_published = publisher.get_published_count(today)

        print(f"Articles publiés:")
        print(f"  - Total: {total_published}")
        print(f"  - Aujourd'hui: {today_published}")

        # Test avec un contenu fictif (sans vraiment publier)
        print("\nTest de publication (simulation):")
        print(f"  - Site path: {publisher.site_path}")
        print(f"  - Blog path: {publisher.blog_path}")
        print(f"  - Base URL: {publisher.base_url}")

        # Test génération slug
        test_title = "Comment optimiser votre SEO en 2024 - Guide complet"
        slug = publisher._generate_slug(test_title)
        print(f"\nTest slug:")
        print(f"  - Titre: {test_title}")
        print(f"  - Slug: {slug}")

        publisher.close()
        print("\n=== Test terminé ===")

    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

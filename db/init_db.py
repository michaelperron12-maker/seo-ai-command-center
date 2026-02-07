#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO Agent Stack - Script d'Initialisation de la Base de Données
================================================================
Ce script crée et initialise la base de données SQLite pour le SEO Agent.

Usage:
    python init_db.py [--reset]

Options:
    --reset     Supprime la base existante avant de la recréer
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration
DB_DIR = Path(__file__).parent
DB_FILE = DB_DIR / "seo_agent.db"
SCHEMA_FILE = DB_DIR / "schema.sql"
SEED_FILE = DB_DIR / "seed.sql"


def print_header():
    """Affiche l'en-tête du script."""
    print("=" * 60)
    print("  SEO Agent Stack - Initialisation de la Base de Données")
    print("=" * 60)
    print()


def print_success(message: str):
    """Affiche un message de succès."""
    print(f"[OK] {message}")


def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"[ERREUR] {message}")


def print_info(message: str):
    """Affiche un message d'information."""
    print(f"[INFO] {message}")


def check_files_exist() -> bool:
    """Vérifie que les fichiers SQL requis existent."""
    files_ok = True

    if not SCHEMA_FILE.exists():
        print_error(f"Fichier schema.sql introuvable: {SCHEMA_FILE}")
        files_ok = False
    else:
        print_success(f"schema.sql trouvé")

    if not SEED_FILE.exists():
        print_error(f"Fichier seed.sql introuvable: {SEED_FILE}")
        files_ok = False
    else:
        print_success(f"seed.sql trouvé")

    return files_ok


def execute_sql_file(conn: sqlite3.Connection, filepath: Path) -> bool:
    """
    Exécute un fichier SQL sur la connexion donnée.

    Args:
        conn: Connexion SQLite
        filepath: Chemin vers le fichier SQL

    Returns:
        True si succès, False sinon
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        return True

    except sqlite3.Error as e:
        print_error(f"Erreur SQL dans {filepath.name}: {e}")
        return False
    except IOError as e:
        print_error(f"Erreur lecture {filepath.name}: {e}")
        return False


def verify_database(conn: sqlite3.Connection) -> dict:
    """
    Vérifie l'état de la base de données après initialisation.

    Returns:
        Dictionnaire avec les statistiques
    """
    stats = {}
    cursor = conn.cursor()

    # Compter les tables
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    tables = cursor.fetchall()
    stats['tables'] = [t[0] for t in tables]

    # Compter les enregistrements par table
    stats['counts'] = {}
    for table in stats['tables']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats['counts'][table] = cursor.fetchone()[0]

    # Compter les vues
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='view'
    """)
    views = cursor.fetchall()
    stats['views'] = [v[0] for v in views]

    # Compter les triggers
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='trigger'
    """)
    triggers = cursor.fetchall()
    stats['triggers'] = [t[0] for t in triggers]

    return stats


def display_stats(stats: dict):
    """Affiche les statistiques de la base de données."""
    print()
    print("-" * 40)
    print("  Résumé de la Base de Données")
    print("-" * 40)

    print(f"\nTables créées ({len(stats['tables'])}):")
    for table in stats['tables']:
        count = stats['counts'].get(table, 0)
        print(f"  - {table}: {count} enregistrement(s)")

    print(f"\nVues créées ({len(stats['views'])}):")
    for view in stats['views']:
        print(f"  - {view}")

    print(f"\nTriggers créés ({len(stats['triggers'])}):")
    for trigger in stats['triggers']:
        print(f"  - {trigger}")


def init_database(reset: bool = False) -> bool:
    """
    Initialise la base de données.

    Args:
        reset: Si True, supprime la base existante

    Returns:
        True si succès, False sinon
    """
    print_header()

    # Vérifier les fichiers requis
    print("Vérification des fichiers...")
    if not check_files_exist():
        return False
    print()

    # Gestion du reset
    if DB_FILE.exists():
        if reset:
            print_info(f"Suppression de la base existante: {DB_FILE}")
            os.remove(DB_FILE)
        else:
            print_info(f"Base de données existante trouvée: {DB_FILE}")
            response = input("Voulez-vous la recréer? (o/N): ").strip().lower()
            if response == 'o':
                os.remove(DB_FILE)
                print_success("Base existante supprimée")
            else:
                print_info("Opération annulée")
                return False

    print()

    # Créer la connexion
    print("Création de la base de données...")
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        print_success(f"Base créée: {DB_FILE}")
    except sqlite3.Error as e:
        print_error(f"Impossible de créer la base: {e}")
        return False

    # Exécuter le schéma
    print("\nExécution du schéma...")
    if not execute_sql_file(conn, SCHEMA_FILE):
        conn.close()
        return False
    print_success("Schéma appliqué avec succès")

    # Exécuter le seed
    print("\nInsertion des données initiales...")
    if not execute_sql_file(conn, SEED_FILE):
        conn.close()
        return False
    print_success("Données initiales insérées")

    # Vérifier la base
    print("\nVérification de la base de données...")
    stats = verify_database(conn)
    display_stats(stats)

    # Fermer la connexion
    conn.close()

    # Message final
    print()
    print("=" * 60)
    print("  INITIALISATION TERMINÉE AVEC SUCCÈS")
    print("=" * 60)
    print(f"\nFichier: {DB_FILE}")
    print(f"Taille: {DB_FILE.stat().st_size / 1024:.2f} Ko")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    return True


def main():
    """Point d'entrée principal."""
    reset = "--reset" in sys.argv

    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    success = init_database(reset=reset)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

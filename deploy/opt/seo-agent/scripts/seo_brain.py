#!/usr/bin/env python3
"""
SEO Brain - Cerveau IA avec memoire long-terme SQLite
Gere les 60 agents, le kill-switch, et l'orchestration.
Pas de SaaS - 100% self-hosted.
"""

import os
import sys
import json
import sqlite3
import hashlib
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
BASE_DIR = Path("/opt/seo-agent")
DB_PATH = BASE_DIR / "db" / "seo_brain.db"
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
LOG_DIR = BASE_DIR / "logs"
MIGRATIONS_DIR = BASE_DIR / "migrations"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "seo_brain.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("seo_brain")


class SeoBrain:
    """Cerveau central - memoire long-terme + kill-switch + orchestration."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ═══════════════════════════════════
    # DATABASE
    # ═══════════════════════════════════
    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Applique les migrations SQL."""
        migrations_dir = MIGRATIONS_DIR
        if not migrations_dir.exists():
            logger.warning(f"Migrations dir not found: {migrations_dir}")
            return

        conn = self._get_conn()
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            logger.info(f"Applying migration: {sql_file.name}")
            with open(sql_file) as f:
                conn.executescript(f.read())
        conn.close()
        logger.info("Database initialized")

    # ═══════════════════════════════════
    # KILL SWITCH
    # ═══════════════════════════════════
    def check_kill_switch(self):
        """Verifie si le kill-switch doit etre active.
        Regles:
        - Trop de publications en 24h
        - Contenu trop similaire (moyenne > seuil)
        - Trop d'erreurs 404/500
        """
        conn = self._get_conn()

        # Verifier si deja actif
        row = conn.execute(
            "SELECT value FROM system_state WHERE key='kill_switch_active'"
        ).fetchone()
        if row and row['value'] == 'true':
            # Verifier si la pause est terminee
            ks = conn.execute(
                "SELECT * FROM kill_switch WHERE active=1 ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if ks and ks['pause_until']:
                if datetime.now() > datetime.fromisoformat(ks['pause_until']):
                    self._deactivate_kill_switch(conn, ks['id'])
                    conn.close()
                    return False
            conn.close()
            return True

        # Regle 1: Max publications par jour
        max_pub = int(self._get_state(conn, 'max_publications_per_day', '5'))
        pub_count = conn.execute(
            "SELECT COUNT(*) as c FROM publications WHERE published_at > datetime('now', '-24 hours')"
        ).fetchone()['c']
        if pub_count >= max_pub:
            self._activate_kill_switch(conn, 'max_publications',
                f"Limite atteinte: {pub_count}/{max_pub} publications en 24h")
            conn.close()
            return True

        # Regle 2: Similarite contenu trop elevee
        threshold = float(self._get_state(conn, 'max_similarity_threshold', '0.70'))
        avg_sim = conn.execute(
            "SELECT AVG(similarity_score) as avg FROM content_similarity WHERE checked_at > datetime('now', '-24 hours')"
        ).fetchone()['avg']
        if avg_sim and avg_sim > threshold:
            self._activate_kill_switch(conn, 'similarity',
                f"Similarite moyenne trop elevee: {avg_sim:.2f} > {threshold}")
            conn.close()
            return True

        # Regle 3: Trop d'erreurs
        max_errors = int(self._get_state(conn, 'max_errors_before_pause', '10'))
        error_count = conn.execute(
            "SELECT COUNT(*) as c FROM mon_uptime WHERE is_up=0 AND checked_at > datetime('now', '-24 hours')"
        ).fetchone()['c']
        error_count += conn.execute(
            "SELECT COUNT(*) as c FROM agent_runs WHERE status='failed' AND started_at > datetime('now', '-24 hours')"
        ).fetchone()['c']
        if error_count >= max_errors:
            self._activate_kill_switch(conn, 'errors',
                f"Trop d'erreurs: {error_count}/{max_errors} en 24h")
            conn.close()
            return True

        conn.close()
        return False

    def _activate_kill_switch(self, conn, rule, reason):
        pause_hours = int(self._get_state(conn, 'pause_duration_hours', '48'))
        pause_until = datetime.now() + timedelta(hours=pause_hours)
        conn.execute(
            "INSERT INTO kill_switch (active, reason, triggered_by, trigger_rule, pause_until) VALUES (1, ?, 'auto', ?, ?)",
            (reason, rule, pause_until.isoformat())
        )
        conn.execute(
            "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES ('kill_switch_active', 'true', datetime('now'))"
        )
        conn.execute(
            "INSERT INTO mon_alerts (alert_type, severity, message) VALUES ('killswitch', 'critical', ?)",
            (f"Kill-switch active: {reason}",)
        )
        conn.commit()
        logger.critical(f"KILL SWITCH ACTIVE: {reason} - Pause {pause_hours}h")

    def _deactivate_kill_switch(self, conn, ks_id):
        conn.execute("UPDATE kill_switch SET active=0, deactivated_at=datetime('now') WHERE id=?", (ks_id,))
        conn.execute(
            "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES ('kill_switch_active', 'false', datetime('now'))"
        )
        conn.commit()
        logger.info("Kill-switch desactive (pause terminee)")

    def force_kill_switch(self, reason="Manuel"):
        """Activation manuelle du kill-switch."""
        conn = self._get_conn()
        self._activate_kill_switch(conn, 'manual', reason)
        conn.close()

    def force_resume(self):
        """Desactivation manuelle du kill-switch."""
        conn = self._get_conn()
        ks = conn.execute("SELECT id FROM kill_switch WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
        if ks:
            self._deactivate_kill_switch(conn, ks['id'])
        conn.close()

    # ═══════════════════════════════════
    # CONTENT SIMILARITY
    # ═══════════════════════════════════
    def compute_content_hash(self, content):
        """SHA256 du contenu normalise."""
        normalized = ' '.join(content.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def check_similarity(self, new_content, site_id):
        """Verifie la similarite avec le contenu existant (Jaccard simple)."""
        conn = self._get_conn()
        new_words = set(new_content.lower().split())

        publications = conn.execute(
            "SELECT id, title FROM publications WHERE site_id=? ORDER BY published_at DESC LIMIT 20",
            (site_id,)
        ).fetchall()

        max_similarity = 0.0
        for pub in publications:
            # Recuperer le contenu du draft ou publication
            draft = conn.execute(
                "SELECT content FROM drafts WHERE title=? AND site_id=? LIMIT 1",
                (pub['title'], site_id)
            ).fetchone()
            if draft and draft['content']:
                existing_words = set(draft['content'].lower().split())
                if new_words and existing_words:
                    intersection = new_words & existing_words
                    union = new_words | existing_words
                    similarity = len(intersection) / len(union) if union else 0
                    max_similarity = max(max_similarity, similarity)

        conn.close()
        return max_similarity

    # ═══════════════════════════════════
    # DRAFT MANAGEMENT
    # ═══════════════════════════════════
    def create_draft(self, site_id, title, content, content_type, agent_name, keyword_id=None):
        """Cree un brouillon en attente de validation humaine."""
        conn = self._get_conn()
        content_hash = self.compute_content_hash(content)
        word_count = len(content.split())

        conn.execute(
            """INSERT INTO drafts (site_id, title, content, content_type, content_hash,
               word_count, keyword_id, agent_name, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (site_id, title, content, content_type, content_hash, word_count, keyword_id, agent_name)
        )
        draft_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Verifier similarite
        similarity = self.check_similarity(content, site_id)
        if similarity > 0:
            conn.execute(
                "INSERT INTO content_similarity (draft_id, similarity_score) VALUES (?, ?)",
                (draft_id, similarity)
            )

        conn.commit()
        conn.close()
        logger.info(f"Draft cree: '{title}' pour {site_id} (similarite: {similarity:.2f})")
        return draft_id

    def approve_draft(self, draft_id):
        """Approuve un brouillon pour publication."""
        conn = self._get_conn()
        conn.execute("UPDATE drafts SET status='approved', updated_at=datetime('now') WHERE id=?", (draft_id,))
        conn.commit()
        conn.close()
        logger.info(f"Draft {draft_id} approuve")

    def reject_draft(self, draft_id, reason=""):
        """Rejette un brouillon."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE drafts SET status='rejected', rejection_reason=?, updated_at=datetime('now') WHERE id=?",
            (reason, draft_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"Draft {draft_id} rejete: {reason}")

    def publish_draft(self, draft_id):
        """Publie un brouillon approuve."""
        conn = self._get_conn()
        draft = conn.execute("SELECT * FROM drafts WHERE id=? AND status='approved'", (draft_id,)).fetchone()
        if not draft:
            conn.close()
            return False

        conn.execute(
            """INSERT INTO publications (site_id, title, content_type, content_hash,
               word_count, keyword_id, status) VALUES (?, ?, ?, ?, ?, ?, 'published')""",
            (draft['site_id'], draft['title'], draft['content_type'],
             draft['content_hash'], draft['word_count'], draft['keyword_id'])
        )
        conn.execute("UPDATE drafts SET status='published', updated_at=datetime('now') WHERE id=?", (draft_id,))
        conn.commit()
        conn.close()
        logger.info(f"Draft {draft_id} publie: {draft['title']}")
        return True

    # ═══════════════════════════════════
    # AGENT RUNS
    # ═══════════════════════════════════
    def start_agent_run(self, agent_name, task_type, site_id=None):
        """Enregistre le debut d'execution d'un agent."""
        if self.check_kill_switch():
            logger.warning(f"Kill-switch actif - agent {agent_name} bloque")
            return None

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO agent_runs (agent_name, task_type, site_id, status) VALUES (?, ?, ?, 'running')",
            (agent_name, task_type, site_id)
        )
        run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        logger.info(f"Agent {agent_name} demarre (run #{run_id})")
        return run_id

    def complete_agent_run(self, run_id, status='success', result=None, error=None):
        """Enregistre la fin d'execution d'un agent."""
        conn = self._get_conn()
        started = conn.execute("SELECT started_at FROM agent_runs WHERE id=?", (run_id,)).fetchone()
        duration = 0
        if started:
            start_time = datetime.fromisoformat(started['started_at'])
            duration = (datetime.now() - start_time).total_seconds()

        conn.execute(
            """UPDATE agent_runs SET status=?, result=?, error_message=?,
               duration_seconds=?, completed_at=datetime('now') WHERE id=?""",
            (status, json.dumps(result) if result else None, error, duration, run_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"Agent run #{run_id} termine: {status} ({duration:.1f}s)")

    # ═══════════════════════════════════
    # MONITORING
    # ═══════════════════════════════════
    def record_uptime(self, site_id, is_up, response_time_ms=0, status_code=200, error=None):
        """Enregistre un check uptime."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO mon_uptime (site_id, is_up, response_time_ms, status_code, error_message) VALUES (?, ?, ?, ?, ?)",
            (site_id, 1 if is_up else 0, response_time_ms, status_code, error)
        )
        if not is_up:
            conn.execute(
                "INSERT INTO mon_alerts (site_id, alert_type, severity, message) VALUES (?, 'uptime', 'critical', ?)",
                (site_id, f"Site DOWN: {error or 'HTTP ' + str(status_code)}")
            )
        conn.commit()
        conn.close()

    # ═══════════════════════════════════
    # STATS
    # ═══════════════════════════════════
    def get_stats(self):
        """Retourne les stats globales."""
        conn = self._get_conn()
        stats = {}
        stats['total_publications'] = conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
        stats['publications_24h'] = conn.execute(
            "SELECT COUNT(*) FROM publications WHERE published_at > datetime('now', '-24 hours')"
        ).fetchone()[0]
        stats['pending_drafts'] = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE status='pending'"
        ).fetchone()[0]
        stats['active_alerts'] = conn.execute(
            "SELECT COUNT(*) FROM mon_alerts WHERE resolved=0"
        ).fetchone()[0]
        stats['kill_switch'] = self._get_state(conn, 'kill_switch_active', 'false') == 'true'
        stats['total_agents_runs'] = conn.execute("SELECT COUNT(*) FROM agent_runs").fetchone()[0]
        stats['sites'] = [dict(r) for r in conn.execute("SELECT * FROM sites WHERE active=1").fetchall()]
        conn.close()
        return stats

    # ═══════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════
    def _get_state(self, conn, key, default=''):
        row = conn.execute("SELECT value FROM system_state WHERE key=?", (key,)).fetchone()
        return row['value'] if row else default

    def set_state(self, key, value):
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, str(value))
        )
        conn.commit()
        conn.close()


# ═══════════════════════════════════════
# CLI
# ═══════════════════════════════════════
if __name__ == "__main__":
    brain = SeoBrain()

    if len(sys.argv) < 2:
        print("Usage: seo_brain.py [status|kill|resume|check]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        stats = brain.get_stats()
        print(json.dumps(stats, indent=2, default=str))

    elif cmd == "kill":
        reason = sys.argv[2] if len(sys.argv) > 2 else "Manuel via CLI"
        brain.force_kill_switch(reason)
        print("Kill-switch ACTIVE")

    elif cmd == "resume":
        brain.force_resume()
        print("Kill-switch DESACTIVE")

    elif cmd == "check":
        is_killed = brain.check_kill_switch()
        print(f"Kill-switch: {'ACTIF' if is_killed else 'inactif'}")

    else:
        print(f"Commande inconnue: {cmd}")
        sys.exit(1)

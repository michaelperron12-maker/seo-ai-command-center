"""Self-audit API routes - import into api_server.py"""
import sqlite3
from flask import jsonify, request

DB_PATH = "/opt/seo-agent/db/seo_agent.db"

def register_self_audit_routes(app):
    @app.route("/api/self-audit/results", methods=["GET"])
    def get_self_audit_results():
        site_id = request.args.get("site_id")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = "SELECT id, site_id, check_type, severity, message, fix_level, fix_command, auto_fixed, confirmed, executed, created_at FROM self_audit_results WHERE 1=1"
        params = []
        if site_id:
            query += " AND site_id = ?"
            params.append(site_id)
        query += " ORDER BY created_at DESC LIMIT 100"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"results": [{"id": r[0], "site_id": r[1], "check_type": r[2], "severity": r[3], "message": r[4], "fix_level": r[5], "fix_command": r[6], "auto_fixed": bool(r[7]), "confirmed": bool(r[8]), "executed": bool(r[9]), "created_at": r[10]} for r in rows]})

    @app.route("/api/self-audit/pending", methods=["GET"])
    def get_self_audit_pending():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, site_id, check_type, severity, message, fix_command FROM self_audit_results WHERE fix_level = 'confirm' AND confirmed = 0 AND executed = 0 ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"pending": [{"id": r[0], "site_id": r[1], "check_type": r[2], "severity": r[3], "message": r[4], "fix_command": r[5]} for r in rows]})

    @app.route("/api/self-audit/confirm/<int:fix_id>", methods=["POST"])
    def confirm_self_audit_fix(fix_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE self_audit_results SET confirmed = 1, confirmed_by = 'dashboard', fixed_at = datetime('now') WHERE id = ?", (fix_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "confirmed", "id": fix_id})

    @app.route("/api/self-audit/confirm-all", methods=["POST"])
    def confirm_all_self_audit():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE self_audit_results SET confirmed = 1, confirmed_by = 'dashboard', fixed_at = datetime('now') WHERE fix_level = 'confirm' AND confirmed = 0")
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return jsonify({"status": "confirmed_all", "count": affected})

    @app.route("/api/self-audit/stats", methods=["GET"])
    def get_self_audit_stats():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN auto_fixed = 1 THEN 1 ELSE 0 END), SUM(CASE WHEN fix_level = 'confirm' AND confirmed = 0 THEN 1 ELSE 0 END), SUM(CASE WHEN fix_level = 'manual' AND executed = 0 THEN 1 ELSE 0 END) FROM self_audit_results")
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify({"total": row[0], "auto_fixed": row[1], "pending_confirm": row[2], "manual_required": row[3]})
        return jsonify({"total": 0, "auto_fixed": 0, "pending_confirm": 0, "manual_required": 0})

"""Activity Logger Hook - auto-log agent runs into activity_log table
Import this in master_agent.py or scheduler to auto-log agent activity.
"""
import sqlite3

DB = "/opt/seo-agent/db/seo_agent.db"

def log_activity(source, actor, action, detail=None, site_id=None, category="agent", severity="info"):
    """Log an activity to the timeline"""
    try:
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO activity_log (source, actor, action, detail, site_id, category, severity) VALUES (?,?,?,?,?,?,?)",
            (source, actor, action, detail, site_id, category, severity)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def log_agent_run(agent_name, site_id=None, status="success", detail=None):
    """Shortcut for agent runs"""
    sev = "warning" if status == "error" else "info"
    log_activity("agent", agent_name, "{} run: {}".format(agent_name, status), 
                 detail=detail, site_id=site_id, category="agent", severity=sev)

def log_deploy(actor, message, detail=None):
    """Log a deployment"""
    log_activity("deploy", actor, message, detail=detail, category="deploy", severity="important")

def log_fix(actor, message, site_id=None, detail=None):
    """Log a fix"""
    log_activity("ssh", actor, message, detail=detail, site_id=site_id, category="fix", severity="important")

def sync_recent_agent_runs(hours=1):
    """Pull recent agent_runs into activity_log (avoids duplicates)"""
    try:
        conn = sqlite3.connect(DB)
        conn.execute("""
            INSERT INTO activity_log (timestamp, source, actor, action, site_id, category, severity)
            SELECT started_at, 'agent', agent_name, 
                   agent_name || ' ' || COALESCE(task_type,'run') || ': ' || status,
                   site_id, 
                   CASE 
                     WHEN agent_name LIKE '%monitoring%' OR agent_name LIKE '%Monitoring%' THEN 'monitoring'
                     WHEN agent_name LIKE '%SSL%' OR agent_name LIKE '%Security%' THEN 'security'
                     WHEN agent_name LIKE '%Content%' OR agent_name LIKE '%Blog%' OR agent_name LIKE '%Draft%' THEN 'content'
                     WHEN agent_name LIKE '%Keyword%' OR agent_name LIKE '%SERP%' OR agent_name LIKE '%SEO%' THEN 'seo'
                     WHEN agent_name LIKE '%Scheduler%' THEN 'system'
                     ELSE 'agent'
                   END,
                   CASE WHEN status='error' THEN 'warning' ELSE 'info' END
            FROM agent_runs 
            WHERE started_at > datetime('now', '-' || ? || ' hours')
            AND id NOT IN (SELECT CAST(session_id AS INTEGER) FROM activity_log WHERE source='agent' AND session_id IS NOT NULL)
        """, (hours,))
        count = conn.total_changes
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        return 0

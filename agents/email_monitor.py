#!/usr/bin/env python3
"""
Email Monitor - Checks uptime every 5 min and emails on downtime
Cron: */5 * * * * /usr/bin/python3 /opt/seo-agent/agents/email_monitor.py
"""
import smtplib
import sqlite3
import requests
import time
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

DB_PATH = "/opt/seo-agent/db/seo_agent.db"
ALERT_EMAIL = "michaelperron12@gmail.com"
FROM_EMAIL = "alerts@seoparai.com"
COOLDOWN_MINUTES = 30

SITES = {
    1: {"name": "Deneigement Excellence", "domain": "deneigement-excellence.ca", "url": "https://deneigement-excellence.ca"},
    2: {"name": "Paysagiste Excellence", "domain": "paysagiste-excellence.ca", "url": "https://paysagiste-excellence.ca"},
    3: {"name": "JC Peintre", "domain": "jcpeintre.com", "url": "https://jcpeintre.com"},
    4: {"name": "SEO par AI", "domain": "seoparai.com", "url": "https://seoparai.com"},
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open("/opt/seo-agent/logs/email_monitor.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")

def check_site(site_id, site):
    try:
        r = requests.get(site["url"], timeout=10, allow_redirects=True)
        return {
            "status": "up" if r.status_code == 200 else "down",
            "code": r.status_code,
            "response_time": r.elapsed.total_seconds()
        }
    except requests.exceptions.Timeout:
        return {"status": "down", "code": 0, "response_time": 0, "error": "timeout"}
    except Exception as e:
        return {"status": "down", "code": 0, "response_time": 0, "error": str(e)[:100]}

def was_recently_alerted(site_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cutoff = (datetime.now() - timedelta(minutes=COOLDOWN_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute(
            "SELECT COUNT(*) FROM mon_alerts WHERE site_id=? AND type='downtime_email' AND created_at > ?",
            (str(site_id), cutoff)
        ).fetchone()
        conn.close()
        return row[0] > 0
    except:
        return False

def log_alert(site_id, message):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO mon_alerts (site_id, type, message, severity, created_at) VALUES (?,?,?,?,datetime('now'))",
            (str(site_id), "downtime_email", message, "critical")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"DB error: {e}")

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = ALERT_EMAIL
        msg["Subject"] = subject

        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#1a1a2e;color:#eee;padding:20px;">
        <div style="max-width:600px;margin:0 auto;background:#16213e;border-radius:12px;padding:24px;border:1px solid #e63946;">
            <h2 style="color:#e63946;margin-top:0;">ALERTE - Site DOWN</h2>
            {body}
            <hr style="border-color:#333;margin:20px 0;">
            <p style="font-size:12px;color:#666;">
                SeoparAI Monitoring | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                <a href="https://seoparai.com/dashboard" style="color:#a855f7;">Dashboard</a>
            </p>
        </div>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("localhost", 25) as server:
            server.sendmail(FROM_EMAIL, ALERT_EMAIL, msg.as_string())
        log(f"Email sent to {ALERT_EMAIL}: {subject}")
        return True
    except Exception as e:
        log(f"Email error: {e}")
        return False

def main():
    log("=== Uptime check started ===")
    down_sites = []

    for site_id, site in SITES.items():
        result = check_site(site_id, site)

        # Log to uptime table
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT INTO mon_uptime (site_id, status, response_time, status_code, created_at) VALUES (?,?,?,?,datetime('now'))",
                (str(site_id), result["status"], result.get("response_time", 0), result.get("code", 0))
            )
            conn.commit()
            conn.close()
        except:
            pass

        if result["status"] == "down":
            error_msg = result.get("error", f"HTTP {result.get('code', '?')}")
            log(f"DOWN: {site['name']} ({site['domain']}) - {error_msg}")
            down_sites.append({"id": site_id, "site": site, "error": error_msg})
        else:
            log(f"UP: {site['name']} - {result['response_time']:.2f}s")

    # Send email for down sites
    for ds in down_sites:
        if was_recently_alerted(ds["id"]):
            log(f"Skipped email for {ds['site']['name']} (cooldown)")
            continue

        subject = f"ALERTE: {ds['site']['name']} est DOWN!"
        body = f"""
        <p style="font-size:18px;"><strong>{ds['site']['name']}</strong> ne repond pas!</p>
        <table style="width:100%;border-collapse:collapse;margin:15px 0;">
            <tr><td style="padding:8px;color:#999;">Domaine</td><td style="padding:8px;font-weight:bold;">{ds['site']['domain']}</td></tr>
            <tr><td style="padding:8px;color:#999;">URL</td><td style="padding:8px;">{ds['site']['url']}</td></tr>
            <tr><td style="padding:8px;color:#999;">Erreur</td><td style="padding:8px;color:#e63946;font-weight:bold;">{ds['error']}</td></tr>
            <tr><td style="padding:8px;color:#999;">Heure</td><td style="padding:8px;">{datetime.now().strftime('%H:%M:%S')}</td></tr>
        </table>
        <p>Verifiez le serveur immediatement.</p>
        """
        if send_email(subject, body):
            log_alert(ds["id"], f"DOWNTIME: {ds['site']['domain']} - {ds['error']}")

    if not down_sites:
        log("All sites UP")

    log("=== Check complete ===\n")

if __name__ == "__main__":
    main()

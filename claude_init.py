#!/usr/bin/env python3
"""
Claude Init - Script de démarrage pour sessions Claude
Charge tout le contexte automatiquement
"""

import sqlite3
import requests
import json
from datetime import datetime

DB_PATH = '/opt/seo-agent/db/seo_agent.db'
SYNC_BRIDGE = 'http://localhost:8892'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def load_context():
    """Charge et affiche tout le contexte pour Claude"""
    
    print_header("🤖 CLAUDE SESSION INIT - SEO par AI")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Status des services
    print_header("📡 SERVICES STATUS")
    try:
        status = requests.get(f"{SYNC_BRIDGE}/status", timeout=5).json()
        print(f"SQLite: {status['components']['sqlite']['status']} ({status['components']['sqlite']['sites']} sites, {status['components']['sqlite']['alerts']} alertes)")
        print(f"Ollama: {status['components']['ollama']['status']} - Models: {', '.join(status['components']['ollama']['models'])}")
        print(f"n8n: {status['components']['n8n']['status']}")
    except:
        print("Sync Bridge non disponible - lecture directe SQLite")
    
    # 2. Ports actifs
    print_header("🔌 PORTS ACTIFS")
    ports = {
        8888: "Killswitch (62 agents)",
        8892: "Sync Bridge",
        8893: "Scanner SEO API",
        8895: "Chatbot Michael (DeepSeek V3.2)",
        3002: "JCPeintre API",
        5678: "n8n Workflows",
        11434: "Ollama Local"
    }
    for port, desc in ports.items():
        print(f"  Port {port}: {desc}")
    
    # 3. Sites gérés
    print_header("🌐 SITES GÉRÉS")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, domaine, chemin_local FROM sites WHERE actif = 1")
    for row in cursor.fetchall():
        print(f"  [{row['id']}] {row['nom']}")
        print(f"      Domain: {row['domaine']}")
        print(f"      Path: {row['chemin_local']}")
    
    # 4. Contexte Claude sauvegardé
    print_header("💾 CONTEXTE SAUVEGARDÉ")
    cursor.execute("SELECT key, value FROM claude_context ORDER BY updated_at DESC")
    for row in cursor.fetchall():
        val = row['value'][:50] + '...' if len(str(row['value'])) > 50 else row['value']
        print(f"  {row['key']}: {val}")
    
    # 5. Dernière session
    print_header("📅 DERNIÈRE SESSION")
    cursor.execute("SELECT id, started_at, summary, status FROM claude_sessions ORDER BY id DESC LIMIT 1")
    session = cursor.fetchone()
    if session:
        print(f"  Session #{session['id']} - {session['started_at']}")
        print(f"  Status: {session['status']}")
        print(f"  Summary: {session['summary']}")
    
    # 6. Rappels en attente
    print_header("⚠️ RAPPELS")
    cursor.execute("SELECT reminder, priority FROM claude_reminders WHERE is_done = 0")
    reminders = cursor.fetchall()
    if reminders:
        for r in reminders:
            print(f"  [{r['priority'].upper()}] {r['reminder']}")
    else:
        print("  Aucun rappel en attente")
    
    # 7. Alertes critiques
    print_header("🚨 ALERTES CRITIQUES")
    cursor.execute("""
        SELECT sa.alert_type, sa.message, s.domaine 
        FROM site_alerts sa 
        JOIN sites s ON sa.site_id = s.id 
        WHERE sa.is_active = 1 AND sa.priority = 'critical'
        LIMIT 5
    """)
    alerts = cursor.fetchall()
    if alerts:
        for a in alerts:
            print(f"  [{a['domaine']}] {a['alert_type']}: {a['message'][:60]}")
    else:
        print("  Aucune alerte critique")
    
    # 8. Tâches en attente
    print_header("📋 TÂCHES EN ATTENTE")
    cursor.execute("""
        SELECT t.task_name, t.priority, s.domaine 
        FROM tasks t 
        LEFT JOIN sites s ON t.site_id = s.id 
        WHERE t.status = 'pending'
        ORDER BY 
            CASE t.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
        LIMIT 10
    """)
    tasks = cursor.fetchall()
    if tasks:
        for t in tasks:
            site = t['domaine'] or 'Global'
            print(f"  [{t['priority']}] {site}: {t['task_name']}")
    else:
        print("  Aucune tâche en attente")
    
    conn.close()
    
    # 9. Commandes utiles
    print_header("🛠️ COMMANDES UTILES")
    print("  Scanner un site:    curl 'http://localhost:8893/api/scan?domain=example.com'")
    print("  Chat Michael:       curl -X POST http://localhost:8895/chat -d '{\"message\":\"test\"}'")
    print("  Killswitch status:  curl http://localhost:8888/killswitch/status")
    print("  Sync context:       curl http://localhost:8892/context")
    print("  Sites list:         curl http://localhost:8892/sites")
    
    # 10. Info rapide
    print_header("💡 INFO RAPIDE")
    print("  Chatbot: Michael (DeepSeek V3.2) - Version digitale du fondateur")
    print("  Agents: 62 agents IA actifs 24/7")
    print("  Prix: Base 600$/mois | Pack 750$/mois")
    print("  GitHub: michaelperron12-maker/seo-ai-command-center")
    
    print("\n" + "="*60)
    print("  ✅ CONTEXTE CHARGÉ - PRÊT À TRAVAILLER!")
    print("="*60 + "\n")

def start_new_session(summary=""):
    """Démarre une nouvelle session Claude"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO claude_sessions (summary, status) VALUES (?, 'active')", [summary])
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"\n✅ Session #{session_id} démarrée")
    return session_id

def save_context(key, value):
    """Sauvegarde une info de contexte"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO claude_context (key, value, updated_at) VALUES (?, ?, datetime('now'))", [key, value])
    conn.commit()
    conn.close()
    print(f"✅ Contexte sauvegardé: {key}")

def add_reminder(text, priority="normal"):
    """Ajoute un rappel"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO claude_reminders (reminder, priority) VALUES (?, ?)", [text, priority])
    conn.commit()
    conn.close()
    print(f"✅ Rappel ajouté: {text}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'start':
            summary = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
            start_new_session(summary)
            
        elif cmd == 'save' and len(sys.argv) >= 4:
            save_context(sys.argv[2], ' '.join(sys.argv[3:]))
            
        elif cmd == 'remind' and len(sys.argv) >= 3:
            priority = 'high' if '--high' in sys.argv else 'normal'
            text = ' '.join([a for a in sys.argv[2:] if a != '--high'])
            add_reminder(text, priority)
            
        elif cmd == 'help':
            print("Usage:")
            print("  python3 claude_init.py          # Affiche tout le contexte")
            print("  python3 claude_init.py start    # Démarre nouvelle session")
            print("  python3 claude_init.py save KEY VALUE  # Sauvegarde contexte")
            print("  python3 claude_init.py remind TEXT [--high]  # Ajoute rappel")
    else:
        load_context()

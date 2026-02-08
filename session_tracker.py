#!/usr/bin/env python3
"""
Session Tracker - Suivi Michael <-> Claude
Base SQLite pour garder le contexte entre sessions
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = '/var/www/dashboard/sessions.db'

def init_db():
    """Initialise la base de donnees"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Table sessions - chaque connexion Claude
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            summary TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Table tasks - taches en cours/completees
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            task TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            notes TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    ''')
    
    # Table changes - modifications fichiers
    c.execute('''
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            file_path TEXT,
            change_type TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    ''')
    
    # Table context - infos importantes a retenir
    c.execute('''
        CREATE TABLE IF NOT EXISTS context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table reminders - choses a ne pas oublier
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder TEXT,
            priority TEXT DEFAULT 'normal',
            is_done INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print('Database initialized!')

def start_session():
    """Demarre une nouvelle session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO sessions (status) VALUES ("active")')
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def end_session(session_id, summary=''):
    """Termine une session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE sessions 
        SET ended_at = CURRENT_TIMESTAMP, summary = ?, status = 'completed'
        WHERE id = ?
    ''', (summary, session_id))
    conn.commit()
    conn.close()

def add_task(session_id, task, notes=''):
    """Ajoute une tache"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO tasks (session_id, task, notes) VALUES (?, ?, ?)', 
              (session_id, task, notes))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def complete_task(task_id):
    """Marque une tache comme completee"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE tasks 
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (task_id,))
    conn.commit()
    conn.close()

def log_change(session_id, file_path, change_type, description):
    """Log une modification de fichier"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO changes (session_id, file_path, change_type, description)
        VALUES (?, ?, ?, ?)
    ''', (session_id, file_path, change_type, description))
    conn.commit()
    conn.close()

def set_context(key, value):
    """Sauvegarde une info de contexte"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO context (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (key, value))
    conn.commit()
    conn.close()

def get_context(key):
    """Recupere une info de contexte"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM context WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def add_reminder(reminder, priority='normal'):
    """Ajoute un rappel"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO reminders (reminder, priority) VALUES (?, ?)', 
              (reminder, priority))
    conn.commit()
    conn.close()

def get_pending_reminders():
    """Recupere les rappels non faits"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, reminder, priority FROM reminders WHERE is_done = 0')
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'reminder': r[1], 'priority': r[2]} for r in rows]

def get_session_summary():
    """Resume de la derniere session et contexte"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Derniere session
    c.execute('SELECT id, started_at, summary FROM sessions ORDER BY id DESC LIMIT 1')
    last_session = c.fetchone()
    
    # Taches en cours
    c.execute('SELECT task, notes FROM tasks WHERE status = "pending"')
    pending_tasks = c.fetchall()
    
    # Contexte important
    c.execute('SELECT key, value FROM context ORDER BY updated_at DESC LIMIT 10')
    context_items = c.fetchall()
    
    # Rappels
    c.execute('SELECT reminder, priority FROM reminders WHERE is_done = 0')
    reminders = c.fetchall()
    
    conn.close()
    
    return {
        'last_session': last_session,
        'pending_tasks': pending_tasks,
        'context': dict(context_items),
        'reminders': reminders
    }

def show_status():
    """Affiche le status actuel"""
    summary = get_session_summary()
    
    print('\n' + '='*50)
    print('   SESSION TRACKER - Michael <-> Claude')
    print('='*50)
    
    if summary['last_session']:
        print(f"\nDerniere session: #{summary['last_session'][0]} - {summary['last_session'][1]}")
        if summary['last_session'][2]:
            print(f"Resume: {summary['last_session'][2]}")
    
    if summary['pending_tasks']:
        print(f"\nTaches en cours ({len(summary['pending_tasks'])}):")
        for task, notes in summary['pending_tasks']:
            print(f"  - {task}")
    
    if summary['context']:
        print(f"\nContexte sauvegarde:")
        for key, value in summary['context'].items():
            print(f"  {key}: {value[:50]}..." if len(str(value)) > 50 else f"  {key}: {value}")
    
    if summary['reminders']:
        print(f"\nRappels ({len(summary['reminders'])}):")
        for reminder, priority in summary['reminders']:
            print(f"  [{priority.upper()}] {reminder}")
    
    print('\n' + '='*50 + '\n')

if __name__ == '__main__':
    import sys
    
    init_db()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'status':
            show_status()
        
        elif cmd == 'start':
            sid = start_session()
            print(f'Session #{sid} started')
        
        elif cmd == 'context' and len(sys.argv) >= 4:
            set_context(sys.argv[2], sys.argv[3])
            print(f'Context saved: {sys.argv[2]}')
        
        elif cmd == 'reminder' and len(sys.argv) >= 3:
            add_reminder(' '.join(sys.argv[2:]))
            print('Reminder added')
        
        elif cmd == 'task' and len(sys.argv) >= 3:
            add_task(1, ' '.join(sys.argv[2:]))
            print('Task added')
    else:
        show_status()

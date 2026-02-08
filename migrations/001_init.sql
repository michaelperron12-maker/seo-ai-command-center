-- SEO Brain Database Schema v1.0
-- SQLite - Memoire long-terme pour les agents IA

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ═══════════════════════════════════════
-- SITES GERES
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL UNIQUE,
    root_path TEXT NOT NULL,
    niche TEXT,
    language TEXT DEFAULT 'fr',
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- MOTS-CLES
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL REFERENCES sites(id),
    keyword TEXT NOT NULL,
    volume INTEGER DEFAULT 0,
    difficulty INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 3,  -- 1=haute, 2=moyenne, 3=basse
    status TEXT DEFAULT 'active', -- active, paused, done
    current_position INTEGER,
    best_position INTEGER,
    last_checked DATETIME,
    created_at DATETIME DEFAULT (datetime('now')),
    UNIQUE(site_id, keyword)
);

-- ═══════════════════════════════════════
-- PUBLICATIONS (contenu publie)
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL REFERENCES sites(id),
    title TEXT NOT NULL,
    slug TEXT,
    content_type TEXT NOT NULL, -- article, faq, service_page, geo_page
    content_hash TEXT,          -- SHA256 pour detection similarite
    word_count INTEGER DEFAULT 0,
    keyword_id INTEGER REFERENCES keywords(id),
    file_path TEXT,             -- chemin sur le serveur
    status TEXT DEFAULT 'published', -- published, archived, deleted
    published_at DATETIME DEFAULT (datetime('now')),
    created_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- DRAFTS (en attente de validation)
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL REFERENCES sites(id),
    title TEXT NOT NULL,
    content TEXT,
    content_type TEXT NOT NULL,
    content_hash TEXT,
    word_count INTEGER DEFAULT 0,
    keyword_id INTEGER REFERENCES keywords(id),
    agent_name TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected, published
    rejection_reason TEXT,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- AGENT RUNS (historique executions)
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    site_id TEXT REFERENCES sites(id),
    status TEXT DEFAULT 'running', -- running, success, failed, killed
    result TEXT,                    -- JSON result
    error_message TEXT,
    duration_seconds REAL DEFAULT 0,
    started_at DATETIME DEFAULT (datetime('now')),
    completed_at DATETIME
);

-- ═══════════════════════════════════════
-- BACKLINKS
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS backlinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL REFERENCES sites(id),
    source_url TEXT NOT NULL,
    source_type TEXT, -- reddit, forum, directory, guest_post, web2.0
    anchor_text TEXT,
    status TEXT DEFAULT 'active', -- active, lost, pending
    domain_authority INTEGER,
    discovered_at DATETIME DEFAULT (datetime('now')),
    last_checked DATETIME
);

-- ═══════════════════════════════════════
-- MONITORING - UPTIME
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS mon_uptime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL REFERENCES sites(id),
    is_up INTEGER NOT NULL,
    response_time_ms REAL,
    status_code INTEGER,
    error_message TEXT,
    checked_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- MONITORING - SSL
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS mon_ssl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL REFERENCES sites(id),
    domain TEXT NOT NULL,
    valid INTEGER,
    issuer TEXT,
    expires_at DATETIME,
    days_until_expiry INTEGER,
    checked_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- MONITORING - ALERTES
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS mon_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT REFERENCES sites(id),
    alert_type TEXT NOT NULL, -- uptime, ssl, error_rate, killswitch, similarity
    severity TEXT DEFAULT 'warning', -- info, warning, critical
    message TEXT NOT NULL,
    resolved INTEGER DEFAULT 0,
    resolved_at DATETIME,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- KILL SWITCH STATE
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS kill_switch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    active INTEGER DEFAULT 0,
    reason TEXT,
    triggered_by TEXT,          -- auto, manual
    trigger_rule TEXT,          -- max_publications, similarity, errors
    pause_until DATETIME,
    activated_at DATETIME DEFAULT (datetime('now')),
    deactivated_at DATETIME
);

-- ═══════════════════════════════════════
-- SIMILARITY TRACKING
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS content_similarity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER REFERENCES drafts(id),
    compared_to_id INTEGER REFERENCES publications(id),
    similarity_score REAL NOT NULL, -- 0.0 to 1.0
    checked_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- SYSTEM STATE (key-value store)
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- AI CHAT HISTORY
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context TEXT,
    user_message TEXT,
    ai_response TEXT,
    model TEXT,
    tokens_used INTEGER,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_publications_site ON publications(site_id);
CREATE INDEX IF NOT EXISTS idx_publications_date ON publications(published_at);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_site ON drafts(site_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_keywords_site ON keywords(site_id);
CREATE INDEX IF NOT EXISTS idx_mon_uptime_site ON mon_uptime(site_id, checked_at);
CREATE INDEX IF NOT EXISTS idx_mon_alerts_resolved ON mon_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_backlinks_site ON backlinks(site_id);
CREATE INDEX IF NOT EXISTS idx_kill_switch_active ON kill_switch(active);
CREATE INDEX IF NOT EXISTS idx_similarity_draft ON content_similarity(draft_id);

-- ═══════════════════════════════════════
-- DONNEES INITIALES - 3 SITES
-- ═══════════════════════════════════════
INSERT OR IGNORE INTO sites (id, name, domain, root_path, niche) VALUES
    ('deneigement', 'Deneigement Excellence', 'deneigement-excellence.ca', '/var/www/deneigement/', 'deneigement'),
    ('paysagement', 'Paysagiste Excellence', 'paysagiste-excellence.ca', '/var/www/paysagement/', 'paysagement'),
    ('jcpeintre', 'JC Peintre', 'jcpeintre.com', '/var/www/jcpeintre.com/', 'peinture');

-- Site SEO par AI (le propre site)
INSERT OR IGNORE INTO sites (id, name, domain, root_path, niche) VALUES
    ('seoparai', 'SEO par AI', 'seoparai.ca', '/var/www/html/', 'seo-automation');

-- Etat initial kill switch
INSERT OR IGNORE INTO system_state (key, value) VALUES
    ('kill_switch_active', 'false'),
    ('max_publications_per_day', '5'),
    ('max_similarity_threshold', '0.70'),
    ('max_errors_before_pause', '10'),
    ('pause_duration_hours', '48'),
    ('last_master_run', ''),
    ('schema_version', '1');

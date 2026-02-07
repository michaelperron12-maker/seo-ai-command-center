-- ============================================
-- SEO Agent Stack - Schéma de Base de Données
-- ============================================
-- Version: 1.0
-- Description: Schéma complet pour la gestion automatisée du SEO
-- ============================================

-- Suppression des tables existantes (ordre inverse des dépendances)
DROP TABLE IF EXISTS system_state;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS publications;
DROP TABLE IF EXISTS content;
DROP TABLE IF EXISTS briefs;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS sites;

-- ============================================
-- Table: sites
-- Description: Sites web gérés par le SEO Agent
-- ============================================
CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(255) NOT NULL,
    domaine VARCHAR(255) NOT NULL UNIQUE,
    chemin_local VARCHAR(500),
    categorie VARCHAR(100),
    actif BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sites_domaine ON sites(domaine);
CREATE INDEX idx_sites_actif ON sites(actif);

-- ============================================
-- Table: keywords
-- Description: Mots-clés ciblés pour chaque site
-- ============================================
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    mot_cle VARCHAR(255) NOT NULL,
    volume INTEGER DEFAULT 0,
    difficulte INTEGER DEFAULT 0 CHECK (difficulte >= 0 AND difficulte <= 100),
    position_actuelle INTEGER,
    priorite INTEGER DEFAULT 3 CHECK (priorite >= 1 AND priorite <= 5),
    statut VARCHAR(50) DEFAULT 'nouveau' CHECK (statut IN ('nouveau', 'en_cours', 'brief_cree', 'contenu_cree', 'publie', 'abandonne')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);

CREATE INDEX idx_keywords_site_id ON keywords(site_id);
CREATE INDEX idx_keywords_statut ON keywords(statut);
CREATE INDEX idx_keywords_priorite ON keywords(priorite);
CREATE INDEX idx_keywords_mot_cle ON keywords(mot_cle);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE TRIGGER update_keywords_timestamp
AFTER UPDATE ON keywords
BEGIN
    UPDATE keywords SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- Table: briefs
-- Description: Briefs de contenu générés pour les mots-clés
-- ============================================
CREATE TABLE briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    titre VARCHAR(255) NOT NULL,
    structure_json TEXT,
    statut VARCHAR(50) DEFAULT 'brouillon' CHECK (statut IN ('brouillon', 'valide', 'en_redaction', 'complete', 'rejete')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
);

CREATE INDEX idx_briefs_site_id ON briefs(site_id);
CREATE INDEX idx_briefs_keyword_id ON briefs(keyword_id);
CREATE INDEX idx_briefs_statut ON briefs(statut);

-- ============================================
-- Table: content
-- Description: Contenus rédigés à partir des briefs
-- ============================================
CREATE TABLE content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER NOT NULL,
    site_id INTEGER NOT NULL,
    titre VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    contenu_html TEXT,
    contenu_md TEXT,
    meta_description VARCHAR(160),
    score_similarite REAL DEFAULT 0 CHECK (score_similarite >= 0 AND score_similarite <= 1),
    statut VARCHAR(50) DEFAULT 'brouillon' CHECK (statut IN ('brouillon', 'revue', 'approuve', 'publie', 'archive')),
    validation_humaine BOOLEAN DEFAULT 0,
    valide_par VARCHAR(100),
    valide_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brief_id) REFERENCES briefs(id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);

CREATE INDEX idx_content_brief_id ON content(brief_id);
CREATE INDEX idx_content_site_id ON content(site_id);
CREATE INDEX idx_content_statut ON content(statut);
CREATE INDEX idx_content_slug ON content(slug);
CREATE INDEX idx_content_validation ON content(validation_humaine);

-- ============================================
-- Table: publications
-- Description: Historique des publications sur les sites
-- ============================================
CREATE TABLE publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    site_id INTEGER NOT NULL,
    url_publiee VARCHAR(500),
    date_publication DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(50) DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'publie', 'echec', 'retire')),
    erreurs TEXT,
    FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);

CREATE INDEX idx_publications_content_id ON publications(content_id);
CREATE INDEX idx_publications_site_id ON publications(site_id);
CREATE INDEX idx_publications_statut ON publications(statut);
CREATE INDEX idx_publications_date ON publications(date_publication);

-- ============================================
-- Table: alerts
-- Description: Alertes et notifications du système
-- ============================================
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('info', 'warning', 'error', 'critical', 'success')),
    message TEXT NOT NULL,
    severite INTEGER DEFAULT 1 CHECK (severite >= 1 AND severite <= 5),
    action_prise TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_type ON alerts(type);
CREATE INDEX idx_alerts_severite ON alerts(severite);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);

-- ============================================
-- Table: system_state
-- Description: État global du système (configuration runtime)
-- ============================================
CREATE TABLE system_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cle VARCHAR(100) NOT NULL UNIQUE,
    valeur TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_state_cle ON system_state(cle);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE TRIGGER update_system_state_timestamp
AFTER UPDATE ON system_state
BEGIN
    UPDATE system_state SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- Vues utilitaires
-- ============================================

-- Vue: Aperçu des mots-clés avec leurs sites
CREATE VIEW v_keywords_overview AS
SELECT
    k.id,
    k.mot_cle,
    k.volume,
    k.difficulte,
    k.position_actuelle,
    k.priorite,
    k.statut,
    s.nom AS site_nom,
    s.domaine
FROM keywords k
JOIN sites s ON k.site_id = s.id
WHERE s.actif = 1;

-- Vue: Pipeline de contenu complet
CREATE VIEW v_content_pipeline AS
SELECT
    c.id AS content_id,
    c.titre,
    c.slug,
    c.statut AS content_statut,
    c.validation_humaine,
    b.titre AS brief_titre,
    b.statut AS brief_statut,
    k.mot_cle,
    s.nom AS site_nom,
    s.domaine,
    p.url_publiee,
    p.statut AS publication_statut
FROM content c
JOIN briefs b ON c.brief_id = b.id
JOIN keywords k ON b.keyword_id = k.id
JOIN sites s ON c.site_id = s.id
LEFT JOIN publications p ON c.id = p.content_id;

-- Vue: Statistiques par site
CREATE VIEW v_site_stats AS
SELECT
    s.id,
    s.nom,
    s.domaine,
    COUNT(DISTINCT k.id) AS total_keywords,
    COUNT(DISTINCT CASE WHEN k.statut = 'publie' THEN k.id END) AS keywords_publies,
    COUNT(DISTINCT b.id) AS total_briefs,
    COUNT(DISTINCT c.id) AS total_content,
    COUNT(DISTINCT CASE WHEN c.validation_humaine = 1 THEN c.id END) AS content_valide,
    COUNT(DISTINCT p.id) AS total_publications
FROM sites s
LEFT JOIN keywords k ON s.id = k.site_id
LEFT JOIN briefs b ON s.id = b.site_id
LEFT JOIN content c ON s.id = c.site_id
LEFT JOIN publications p ON s.id = p.site_id
GROUP BY s.id, s.nom, s.domaine;

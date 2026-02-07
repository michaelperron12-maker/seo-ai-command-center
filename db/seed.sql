-- ============================================
-- SEO Agent Stack - Données Initiales (Seed)
-- ============================================
-- Version: 1.0
-- Description: Données de démarrage pour le SEO Agent
-- ============================================

-- ============================================
-- Insertion des Sites
-- ============================================

INSERT INTO sites (nom, domaine, chemin_local, categorie, actif) VALUES
    ('Déneigement Excellence', 'deneigement-excellence.ca', '/var/www/deneigement-excellence', 'services', 1),
    ('Paysagiste Excellence', 'paysagiste-excellence.ca', '/var/www/paysagiste-excellence', 'services', 1),
    ('JC Peintre', 'jcpeintre.com', '/var/www/jcpeintre', 'services', 1);

-- ============================================
-- Insertion des Mots-clés Seed
-- ============================================

-- Mots-clés pour Déneigement Excellence (site_id = 1)
INSERT INTO keywords (site_id, mot_cle, volume, difficulte, priorite, statut) VALUES
    (1, 'déneigement résidentiel montréal', 720, 35, 1, 'nouveau'),
    (1, 'service déneigement commercial', 480, 40, 1, 'nouveau'),
    (1, 'déneigement stationnement', 320, 30, 2, 'nouveau'),
    (1, 'contrat déneigement hiver', 260, 25, 2, 'nouveau'),
    (1, 'déneigement entrée de garage', 590, 28, 1, 'nouveau'),
    (1, 'souffleuse à neige service', 180, 22, 3, 'nouveau'),
    (1, 'déneigement rive-sud', 410, 32, 2, 'nouveau'),
    (1, 'prix déneigement résidentiel', 520, 38, 1, 'nouveau'),
    (1, 'déneigement toiture', 290, 35, 2, 'nouveau'),
    (1, 'service sel et abrasif', 140, 18, 3, 'nouveau');

-- Mots-clés pour Paysagiste Excellence (site_id = 2)
INSERT INTO keywords (site_id, mot_cle, volume, difficulte, priorite, statut) VALUES
    (2, 'paysagiste montréal', 1200, 55, 1, 'nouveau'),
    (2, 'aménagement paysager résidentiel', 880, 45, 1, 'nouveau'),
    (2, 'entretien pelouse', 960, 40, 1, 'nouveau'),
    (2, 'pose de pavé uni', 540, 38, 2, 'nouveau'),
    (2, 'taille de haies', 320, 25, 2, 'nouveau'),
    (2, 'plantation arbres arbustes', 280, 30, 2, 'nouveau'),
    (2, 'aménagement terrasse extérieure', 420, 42, 2, 'nouveau'),
    (2, 'irrigation automatique jardin', 210, 35, 3, 'nouveau'),
    (2, 'muret de soutènement', 180, 28, 3, 'nouveau'),
    (2, 'design jardin moderne', 350, 48, 2, 'nouveau');

-- Mots-clés pour JC Peintre (site_id = 3)
INSERT INTO keywords (site_id, mot_cle, volume, difficulte, priorite, statut) VALUES
    (3, 'peintre montréal', 1450, 52, 1, 'nouveau'),
    (3, 'peinture intérieure maison', 980, 45, 1, 'nouveau'),
    (3, 'peinture extérieure résidentielle', 620, 40, 1, 'nouveau'),
    (3, 'peintre commercial', 380, 35, 2, 'nouveau'),
    (3, 'estimation peinture gratuite', 290, 28, 2, 'nouveau'),
    (3, 'peinture cuisine salle de bain', 410, 32, 2, 'nouveau'),
    (3, 'réparation plâtre avant peinture', 180, 22, 3, 'nouveau'),
    (3, 'peinture plafond texturé', 150, 25, 3, 'nouveau'),
    (3, 'peintre certifié rbq', 220, 30, 2, 'nouveau'),
    (3, 'peinture écologique sans cov', 170, 35, 3, 'nouveau');

-- ============================================
-- État Système Initial
-- ============================================

INSERT INTO system_state (cle, valeur) VALUES
    ('pause_active', '0'),
    ('version', '1.0.0'),
    ('dernier_cycle', NULL),
    ('mode_operation', 'automatique'),
    ('limite_publications_jour', '3'),
    ('validation_humaine_requise', '1'),
    ('notification_email', 'admin@seo-agent.local'),
    ('intervalle_cycle_minutes', '60');

-- ============================================
-- Alerte Initiale
-- ============================================

INSERT INTO alerts (type, message, severite, action_prise) VALUES
    ('info', 'Base de données SEO Agent initialisée avec succès', 1, 'Aucune action requise');

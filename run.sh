#!/bin/bash
# SEO Agent - Script de gestion
# Usage: ./run.sh [command]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Chemins
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
DB_PATH="/opt/seo-agent/db/seo_agent.db"
LOG_PATH="/opt/seo-agent/logs/seo_agent.log"
BACKUP_DIR="/opt/seo-agent/backups"

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Afficher l'aide
show_help() {
    echo "SEO Agent - Script de gestion"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commandes disponibles:"
    echo "  status    - Afficher l'etat (n8n, DB, pause, drafts en attente)"
    echo "  start     - Demarrer docker-compose"
    echo "  stop      - Arreter docker-compose"
    echo "  restart   - Redemarrer les services"
    echo "  pause     - Activer kill-switch manuel"
    echo "  resume    - Desactiver kill-switch"
    echo "  logs      - Voir logs (tail -f)"
    echo "  test      - Lancer tests complets"
    echo "  backup    - Backup DB + config"
    echo "  init      - Initialiser DB + demarrer services"
    echo "  tunnel    - Creer SSH tunnel vers n8n (pour acces local)"
    echo "  help      - Afficher cette aide"
    echo ""
}

# Commande: status
cmd_status() {
    echo "========================================"
    echo "       SEO Agent - Status"
    echo "========================================"
    echo ""

    # Verifier Docker
    log_info "Etat Docker Compose:"
    if docker compose ps 2>/dev/null | grep -q "Up"; then
        docker compose ps
        log_success "Services Docker actifs"
    else
        log_warning "Aucun service Docker actif"
    fi
    echo ""

    # Verifier n8n
    log_info "Etat n8n:"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz 2>/dev/null | grep -q "200"; then
        log_success "n8n est accessible sur http://localhost:5678"
    else
        log_warning "n8n n'est pas accessible"
    fi
    echo ""

    # Verifier la base de donnees
    log_info "Etat Base de donnees:"
    if [ -f "$DB_PATH" ]; then
        log_success "DB existe: $DB_PATH"
        SIZE=$(du -h "$DB_PATH" | cut -f1)
        echo "  Taille: $SIZE"
    else
        log_warning "DB non trouvee: $DB_PATH"
    fi
    echo ""

    # Verifier le mode pause
    log_info "Etat Kill-switch:"
    if grep -q "pause_active: true" "$CONFIG_FILE" 2>/dev/null; then
        log_warning "PAUSE ACTIVE - Aucune publication automatique"
    else
        log_success "Mode normal - Publications actives"
    fi
    echo ""

    # Compter les drafts en attente
    log_info "Drafts en attente:"
    if [ -f "$DB_PATH" ]; then
        DRAFTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM drafts WHERE status='pending';" 2>/dev/null || echo "0")
        echo "  $DRAFTS draft(s) en attente de validation"
    else
        echo "  DB non disponible"
    fi
    echo ""

    echo "========================================"
}

# Commande: start
cmd_start() {
    log_info "Demarrage des services..."
    cd "$SCRIPT_DIR"
    docker compose up -d
    log_success "Services demarres"
    sleep 3
    cmd_status
}

# Commande: stop
cmd_stop() {
    log_info "Arret des services..."
    cd "$SCRIPT_DIR"
    docker compose down
    log_success "Services arretes"
}

# Commande: restart
cmd_restart() {
    log_info "Redemarrage des services..."
    cmd_stop
    sleep 2
    cmd_start
}

# Commande: pause (kill-switch)
cmd_pause() {
    log_warning "Activation du kill-switch..."
    if [ -f "$CONFIG_FILE" ]; then
        sed -i 's/pause_active: false/pause_active: true/' "$CONFIG_FILE"
        log_success "Kill-switch ACTIVE - Publications suspendues"
        # Notification optionnelle
        log_info "Pensez a notifier l'equipe si necessaire"
    else
        log_error "Fichier config non trouve: $CONFIG_FILE"
        exit 1
    fi
}

# Commande: resume
cmd_resume() {
    log_info "Desactivation du kill-switch..."
    if [ -f "$CONFIG_FILE" ]; then
        sed -i 's/pause_active: true/pause_active: false/' "$CONFIG_FILE"
        log_success "Mode normal reactive - Publications actives"
    else
        log_error "Fichier config non trouve: $CONFIG_FILE"
        exit 1
    fi
}

# Commande: logs
cmd_logs() {
    log_info "Affichage des logs (Ctrl+C pour quitter)..."
    if [ -f "$LOG_PATH" ]; then
        tail -f "$LOG_PATH"
    else
        log_warning "Fichier log non trouve: $LOG_PATH"
        log_info "Tentative avec docker compose logs..."
        cd "$SCRIPT_DIR"
        docker compose logs -f
    fi
}

# Commande: test
cmd_test() {
    log_info "Lancement des tests..."
    echo ""

    # Test 1: Config
    log_info "Test 1: Verification config.yaml"
    if python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
        log_success "Config YAML valide"
    else
        log_error "Config YAML invalide"
    fi

    # Test 2: Connexion DB
    log_info "Test 2: Connexion base de donnees"
    if [ -f "$DB_PATH" ]; then
        if sqlite3 "$DB_PATH" "SELECT 1;" >/dev/null 2>&1; then
            log_success "Connexion DB OK"
        else
            log_error "Erreur connexion DB"
        fi
    else
        log_warning "DB non initialisee"
    fi

    # Test 3: Docker
    log_info "Test 3: Docker disponible"
    if docker --version >/dev/null 2>&1; then
        log_success "Docker OK"
    else
        log_error "Docker non disponible"
    fi

    # Test 4: n8n
    log_info "Test 4: Acces n8n"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz 2>/dev/null | grep -q "200"; then
        log_success "n8n accessible"
    else
        log_warning "n8n non accessible"
    fi

    # Test 5: Python dependencies
    log_info "Test 5: Dependances Python"
    if python3 -c "import yaml, requests, jinja2, sklearn" 2>/dev/null; then
        log_success "Dependances Python OK"
    else
        log_warning "Certaines dependances Python manquantes"
    fi

    echo ""
    log_info "Tests termines"
}

# Commande: backup
cmd_backup() {
    log_info "Creation du backup..."

    # Creer le dossier de backup
    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

    # Fichiers a sauvegarder
    FILES_TO_BACKUP=""

    if [ -f "$DB_PATH" ]; then
        FILES_TO_BACKUP="$FILES_TO_BACKUP $DB_PATH"
    fi

    if [ -f "$CONFIG_FILE" ]; then
        FILES_TO_BACKUP="$FILES_TO_BACKUP $CONFIG_FILE"
    fi

    if [ -n "$FILES_TO_BACKUP" ]; then
        tar -czvf "$BACKUP_FILE" $FILES_TO_BACKUP 2>/dev/null
        log_success "Backup cree: $BACKUP_FILE"

        # Garder seulement les 10 derniers backups
        ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
        log_info "Anciens backups nettoyes (garde les 10 derniers)"
    else
        log_error "Aucun fichier a sauvegarder"
    fi
}

# Commande: init
cmd_init() {
    log_info "Initialisation du SEO Agent..."
    echo ""

    # Creer les dossiers necessaires
    log_info "Creation des dossiers..."
    sudo mkdir -p /opt/seo-agent/db
    sudo mkdir -p /opt/seo-agent/logs
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown -R $USER:$USER /opt/seo-agent
    log_success "Dossiers crees"

    # Initialiser la base de donnees
    log_info "Initialisation de la base de donnees..."
    sqlite3 "$DB_PATH" <<EOF
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    titre TEXT NOT NULL,
    contenu TEXT,
    mot_cle TEXT,
    status TEXT DEFAULT 'pending',
    similarite_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    expires_at DATETIME
);

CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER,
    site_id TEXT NOT NULL,
    titre TEXT NOT NULL,
    url TEXT,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (draft_id) REFERENCES drafts(id)
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    mot_cle TEXT NOT NULL,
    volume_recherche INTEGER,
    difficulte INTEGER,
    derniere_utilisation DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_site ON drafts(site_id);
CREATE INDEX IF NOT EXISTS idx_publications_site ON publications(site_id);
EOF
    log_success "Base de donnees initialisee"

    # Creer le fichier de log
    touch "$LOG_PATH"
    log_success "Fichier log cree"

    # Demarrer les services
    log_info "Demarrage des services..."
    cmd_start

    echo ""
    log_success "Initialisation terminee!"
    echo ""
    log_info "Prochaines etapes:"
    echo "  1. Configurer les variables d'environnement (.env)"
    echo "  2. Importer les workflows n8n"
    echo "  3. Tester avec: ./run.sh test"
}

# Commande: tunnel
cmd_tunnel() {
    log_info "Creation du tunnel SSH vers n8n..."
    echo ""
    echo "Cette commande cree un tunnel SSH pour acceder a n8n depuis votre machine locale."
    echo ""
    echo "Syntaxe: ssh -L 5678:localhost:5678 user@serveur"
    echo ""
    read -p "Entrez l'adresse du serveur (user@host): " SERVER

    if [ -n "$SERVER" ]; then
        log_info "Connexion au tunnel..."
        log_info "n8n sera accessible sur http://localhost:5678"
        ssh -L 5678:localhost:5678 "$SERVER"
    else
        log_error "Adresse serveur requise"
    fi
}

# Main
case "${1:-help}" in
    status)
        cmd_status
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    pause)
        cmd_pause
        ;;
    resume)
        cmd_resume
        ;;
    logs)
        cmd_logs
        ;;
    test)
        cmd_test
        ;;
    backup)
        cmd_backup
        ;;
    init)
        cmd_init
        ;;
    tunnel)
        cmd_tunnel
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Commande inconnue: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

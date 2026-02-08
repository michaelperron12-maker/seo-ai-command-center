#!/bin/bash
# ═══════════════════════════════════════════════════
# SEO par AI - Lanceur & Diagnostic
# Usage: ./run.sh [start|stop|status|logs|deploy|init]
# ═══════════════════════════════════════════════════

set -e

DEPLOY_DIR="/home/serinityvault/Desktop/projet web/seo-ai/deploy"
INSTALL_DIR="/opt/seo-agent"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}  SEO par AI - $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""
}

# ─────────────────────────────────────
# INIT - Premiere installation
# ─────────────────────────────────────
cmd_init() {
    header "Initialisation"

    echo -e "${YELLOW}[1/5] Creation structure /opt/seo-agent/${NC}"
    sudo mkdir -p "$INSTALL_DIR"/{scripts,config,db,logs,workflows,migrations}
    sudo chown -R "$USER:$USER" "$INSTALL_DIR"

    echo -e "${YELLOW}[2/5] Copie des fichiers${NC}"
    cp "$DEPLOY_DIR/opt/seo-agent/scripts/"*.py "$INSTALL_DIR/scripts/" 2>/dev/null || true
    cp "$DEPLOY_DIR/opt/seo-agent/migrations/"*.sql "$INSTALL_DIR/migrations/" 2>/dev/null || true
    cp "$DEPLOY_DIR/opt/seo-agent/workflows/"*.json "$INSTALL_DIR/workflows/" 2>/dev/null || true

    echo -e "${YELLOW}[3/5] Initialisation base de donnees${NC}"
    if [ ! -f "$INSTALL_DIR/db/seo_brain.db" ]; then
        sqlite3 "$INSTALL_DIR/db/seo_brain.db" < "$INSTALL_DIR/migrations/001_init.sql"
        echo -e "${GREEN}  Base de donnees creee${NC}"
    else
        echo -e "${GREEN}  Base de donnees existe deja${NC}"
    fi

    echo -e "${YELLOW}[4/5] Verification Python${NC}"
    python3 -c "import sqlite3, json, hashlib; print('  Modules OK')"

    echo -e "${YELLOW}[5/5] Test seo_brain.py${NC}"
    python3 "$INSTALL_DIR/scripts/seo_brain.py" status | python3 -m json.tool | head -10

    echo ""
    echo -e "${GREEN}Initialisation terminee!${NC}"
    echo -e "Prochaine etape: ${CYAN}./run.sh start${NC}"
}

# ─────────────────────────────────────
# START - Lancer les services
# ─────────────────────────────────────
cmd_start() {
    header "Demarrage"

    # Verifier Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker non installe!${NC}"
        echo "  sudo apt install docker.io docker-compose-plugin"
        exit 1
    fi

    echo -e "${YELLOW}[1/3] Demarrage n8n + API...${NC}"
    cd "$DEPLOY_DIR"
    docker compose up -d

    echo -e "${YELLOW}[2/3] Attente services...${NC}"
    sleep 5

    echo -e "${YELLOW}[3/3] Verification...${NC}"
    cmd_status
}

# ─────────────────────────────────────
# STOP - Arreter les services
# ─────────────────────────────────────
cmd_stop() {
    header "Arret"
    cd "$DEPLOY_DIR"
    docker compose down
    echo -e "${GREEN}Services arretes${NC}"
}

# ─────────────────────────────────────
# STATUS - Diagnostic complet
# ─────────────────────────────────────
cmd_status() {
    header "Diagnostic"

    # Docker
    echo -e "${CYAN}── Docker ──${NC}"
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -q seo-agent; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep seo-agent
    else
        echo -e "${RED}  Aucun container seo-agent en cours${NC}"
    fi
    echo ""

    # n8n
    echo -e "${CYAN}── n8n ──${NC}"
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5678/healthz 2>/dev/null | grep -q 200; then
        echo -e "${GREEN}  n8n: OK (port 5678)${NC}"
    else
        echo -e "${RED}  n8n: HORS LIGNE${NC}"
    fi

    # API
    echo -e "${CYAN}── API Backend ──${NC}"
    API_RESPONSE=$(curl -s http://127.0.0.1:8002/api/health 2>/dev/null || echo '{"status":"offline"}')
    if echo "$API_RESPONSE" | grep -q '"ok"'; then
        echo -e "${GREEN}  API: OK (port 8002)${NC}"
    else
        echo -e "${RED}  API: HORS LIGNE${NC}"
    fi

    # Landing page
    echo -e "${CYAN}── Landing Page ──${NC}"
    LANDING_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/landing.html 2>/dev/null)
    if [ "$LANDING_CODE" = "200" ]; then
        echo -e "${GREEN}  Landing: OK (port 8080) - HTTP $LANDING_CODE${NC}"
    else
        echo -e "${RED}  Landing: ERREUR - HTTP $LANDING_CODE${NC}"
    fi

    # Sites web
    echo -e "${CYAN}── Sites Web ──${NC}"
    for site in "deneigement-excellence.ca" "paysagiste-excellence.ca" "jcpeintre.com"; do
        CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://$site" 2>/dev/null)
        if [ "$CODE" = "200" ] || [ "$CODE" = "301" ] || [ "$CODE" = "302" ]; then
            echo -e "${GREEN}  $site: OK (HTTP $CODE)${NC}"
        else
            echo -e "${RED}  $site: ERREUR (HTTP $CODE)${NC}"
        fi
    done

    # SEO Brain
    echo -e "${CYAN}── SEO Brain ──${NC}"
    if [ -f "$INSTALL_DIR/db/seo_brain.db" ]; then
        STATS=$(python3 "$INSTALL_DIR/scripts/seo_brain.py" status 2>/dev/null || echo '{}')
        PUB=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_publications',0))" 2>/dev/null || echo "?")
        DRAFTS=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pending_drafts',0))" 2>/dev/null || echo "?")
        KS=$(echo "$STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ACTIF' if d.get('kill_switch') else 'inactif')" 2>/dev/null || echo "?")
        echo -e "  Publications: ${GREEN}$PUB${NC}"
        echo -e "  Drafts en attente: ${YELLOW}$DRAFTS${NC}"
        echo -e "  Kill-switch: $([ "$KS" = "ACTIF" ] && echo -e "${RED}$KS${NC}" || echo -e "${GREEN}$KS${NC}")"
    else
        echo -e "${YELLOW}  Base de donnees non initialisee (./run.sh init)${NC}"
    fi

    # Disk
    echo -e "${CYAN}── Serveur ──${NC}"
    echo "  $(df -h / | tail -1 | awk '{print "Disque: "$3" / "$2" ("$5" utilise)"}')"
    echo "  $(free -h | grep Mem | awk '{print "RAM: "$3" / "$2}')"
    echo "  Load: $(cat /proc/loadavg | awk '{print $1, $2, $3}')"
    echo ""
}

# ─────────────────────────────────────
# LOGS - Voir les logs
# ─────────────────────────────────────
cmd_logs() {
    header "Logs"
    LOG_TYPE=${2:-brain}

    case $LOG_TYPE in
        brain)   tail -50 "$INSTALL_DIR/logs/seo_brain.log" 2>/dev/null || echo "Pas de logs brain" ;;
        master)  tail -50 "$INSTALL_DIR/logs/master.log" 2>/dev/null || echo "Pas de logs master" ;;
        publish) tail -50 "$INSTALL_DIR/logs/publish.log" 2>/dev/null || echo "Pas de logs publish" ;;
        kill)    tail -50 "$INSTALL_DIR/logs/killswitch.log" 2>/dev/null || echo "Pas de logs kill" ;;
        n8n)     docker logs --tail 50 seo-agent-n8n 2>/dev/null || echo "Container n8n non trouve" ;;
        api)     docker logs --tail 50 seo-agent-api 2>/dev/null || echo "Container API non trouve" ;;
        nginx)   sudo tail -50 /var/log/nginx/error.log 2>/dev/null || echo "Pas de logs nginx" ;;
        *)       echo "Types: brain, master, publish, kill, n8n, api, nginx" ;;
    esac
}

# ─────────────────────────────────────
# DEPLOY - Deployer les mises a jour
# ─────────────────────────────────────
cmd_deploy() {
    header "Deploiement"

    echo -e "${YELLOW}[1/3] Mise a jour des scripts${NC}"
    cp "$DEPLOY_DIR/opt/seo-agent/scripts/"*.py "$INSTALL_DIR/scripts/" 2>/dev/null || true
    cp "$DEPLOY_DIR/opt/seo-agent/workflows/"*.json "$INSTALL_DIR/workflows/" 2>/dev/null || true

    echo -e "${YELLOW}[2/3] Deploiement landing page${NC}"
    local LANDING_SRC="$DEPLOY_DIR/../landing.html"
    if [ -f "$LANDING_SRC" ]; then
        sudo cp "$LANDING_SRC" /var/www/html/landing.html
        sudo cp "$LANDING_SRC" /var/www/dashboard/landing.html
        sudo chown www-data:www-data /var/www/html/landing.html /var/www/dashboard/landing.html
        echo -e "${GREEN}  Landing page deployee${NC}"
    fi

    echo -e "${YELLOW}[3/3] Restart services${NC}"
    cd "$DEPLOY_DIR"
    docker compose restart 2>/dev/null || echo "  Docker non demarre"

    echo -e "${GREEN}Deploiement termine!${NC}"
}

# ─────────────────────────────────────
# MAIN
# ─────────────────────────────────────
case "${1:-help}" in
    init)    cmd_init ;;
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    status)  cmd_status ;;
    logs)    cmd_logs "$@" ;;
    deploy)  cmd_deploy ;;
    kill)    python3 "$INSTALL_DIR/scripts/seo_brain.py" kill "${2:-Manuel}" ;;
    resume)  python3 "$INSTALL_DIR/scripts/seo_brain.py" resume ;;
    *)
        header "Aide"
        echo "Usage: ./run.sh <commande>"
        echo ""
        echo "  init     Premiere installation"
        echo "  start    Demarrer n8n + API"
        echo "  stop     Arreter les services"
        echo "  status   Diagnostic complet"
        echo "  deploy   Deployer les mises a jour"
        echo "  logs     Voir les logs (brain|master|publish|kill|n8n|api|nginx)"
        echo "  kill     Activer le kill-switch"
        echo "  resume   Desactiver le kill-switch"
        echo ""
        ;;
esac

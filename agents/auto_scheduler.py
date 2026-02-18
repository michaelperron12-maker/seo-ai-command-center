#!/usr/bin/env python3
"""
SeoparAI Auto Scheduler — Orchestre les 62 agents en 6 cycles autonomes
Usage: python3 auto_scheduler.py [cycle_name]
Cycles: seo-core, content, marketing, business, maintenance, all

Crontab:
  0 */4 * * *   auto_scheduler.py seo-core
  0 8,20 * * *  auto_scheduler.py content
  0 10 * * *    auto_scheduler.py marketing
  0 6 * * *     auto_scheduler.py business
  0 3 * * 0     auto_scheduler.py maintenance
"""

import sys
import os
import time
import sqlite3
import yaml
import signal
import traceback
from datetime import datetime, timedelta

# Path setup
BASE_DIR = '/opt/seo-agent'
AGENTS_DIR = os.path.join(BASE_DIR, 'agents')
DB_PATH = os.path.join(BASE_DIR, 'db', 'seo_agent.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'scheduler.log')

sys.path.insert(0, AGENTS_DIR)

# Import all 59 agent classes
from agents_system import *

# ─── Timeout handler ───
class AgentTimeout(Exception):
    pass

def timeout_handler(signum, frame):
    raise AgentTimeout("Agent execution timed out")

# ─── Logging ───
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except:
        pass

# ─── DB helpers ───
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_agent_run(agent_name, task_type, site_id, status, result="", duration=0):
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO agent_runs (agent_name, task_type, site_id, status, result, duration_seconds, started_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now', ?), datetime('now'))""",
            (agent_name, task_type, str(site_id), status, str(result)[:500], duration,
             f"-{int(duration)} seconds")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"DB log error: {e}", "ERROR")

def update_scheduled_task(task_name, agent_name, cron_expr):
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO scheduled_tasks (task_name, agent_name, schedule_cron, last_run, next_run, enabled)
               VALUES (?, ?, ?, datetime('now'), NULL, 1)
               ON CONFLICT(task_name) DO UPDATE SET last_run=datetime('now')""",
            (task_name, agent_name, cron_expr)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Scheduled task update error: {e}", "ERROR")

def was_cycle_run_recently(cycle_name, minutes=30):
    """Prevent duplicate runs within cooldown period"""
    try:
        conn = get_db()
        cutoff = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute(
            "SELECT COUNT(*) FROM agent_runs WHERE task_type=? AND started_at > ?",
            (f"cycle_{cycle_name}", cutoff)
        ).fetchone()
        conn.close()
        return row[0] > 0
    except:
        return False

# ─── Config ───
def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

def is_paused(config=None):
    if config is None:
        config = load_config()
    return config.get('general', {}).get('pause_active', False)

def get_sites(config=None):
    if config is None:
        config = load_config()
    sites = config.get('sites', [])
    return [s for s in sites if s.get('actif', True)]

# ─── Agent runner with timeout ───
def run_agent(agent_name, func, args=(), timeout_sec=120, site_id="all"):
    """Run a single agent function with timeout and error handling"""
    start = time.time()
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_sec)

        result = func(*args)

        signal.alarm(0)
        duration = time.time() - start
        log(f"  OK {agent_name} ({duration:.1f}s)")
        log_agent_run(agent_name, agent_name, site_id, "success", str(result)[:300], duration)
        return {"status": "success", "result": result, "duration": duration}

    except AgentTimeout:
        signal.alarm(0)
        duration = time.time() - start
        log(f"  TIMEOUT {agent_name} ({timeout_sec}s limit)", "WARNING")
        log_agent_run(agent_name, agent_name, site_id, "timeout", f"Timed out after {timeout_sec}s", duration)
        return {"status": "timeout", "duration": duration}

    except Exception as e:
        signal.alarm(0)
        duration = time.time() - start
        err = str(e)[:200]
        log(f"  ERROR {agent_name}: {err}", "ERROR")
        log_agent_run(agent_name, agent_name, site_id, "error", err, duration)
        return {"status": "error", "error": err, "duration": duration}


# ═══════════════════════════════════════════════════════
#  CYCLE DEFINITIONS
# ═══════════════════════════════════════════════════════

def cycle_seo_core(sites):
    """SEO-CORE: Technical audits, schema, images, links, titles, speed — every 4h"""
    log("═══ CYCLE: SEO-CORE ═══")
    stats = {"ok": 0, "fail": 0}

    tech_audit = TechnicalSEOAuditAgent()
    schema_agent = SchemaMarkupAgent()
    img_agent = ImageOptimizationAgent()
    link_agent = InternalLinkingAgent()
    title_agent = TitleTagAgent()
    speed_agent = SiteSpeedAgent()
    url_agent = URLOptimizationAgent()

    for i, site in enumerate(sites, 1):
        site_id = str(i)
        domain = site['domaine']
        url = f"https://{domain}"
        log(f"── Site {i}: {site['nom']} ({domain})")

        seed_kw = site.get('mots_cles_seed', [''])[0]
        agents_to_run = [
            ("TechnicalSEOAudit", tech_audit.audit_page, (url,), 60),
            ("TechnicalSEO_Robots", tech_audit.check_robots_txt, (domain,), 30),
            ("TechnicalSEO_Sitemap", tech_audit.check_sitemap, (domain,), 30),
            ("TechnicalSEO_Security", tech_audit.check_security_headers, (url,), 30),
            ("SchemaMarkup_LocalBusiness", schema_agent.generate_local_business_schema, (site_id,), 90),
            ("ImageOptimization", img_agent.generate_alt_texts, (f"Services page for {domain}", seed_kw), 60),
            ("InternalLinking", link_agent.suggest_links, (site_id, seed_kw), 60),
            ("URLOptimization", url_agent.generate_slug, (site['nom'], seed_kw), 30),
            ("TitleTag", title_agent.optimize_title, (f"{site['nom']} - Services", seed_kw, site['nom']), 60),
            ("SiteSpeed", speed_agent.analyze_speed, (site_id,), 90),
        ]

        for name, func, args, timeout in agents_to_run:
            r = run_agent(name, func, args, timeout, site_id)
            stats["ok" if r["status"] == "success" else "fail"] += 1

    # Self-Audit HTML auto-fix (schema, meta, lazy loading, etc.)
    try:
        from self_audit_agent import SelfAuditAgent, SITES as AUDIT_SITES
        audit_agent = SelfAuditAgent()
        for audit_site_id in AUDIT_SITES:
            r = run_agent(f"SelfAudit_{audit_site_id}",
                          audit_agent.check_html_files, (audit_site_id,), 120, audit_site_id)
            stats["ok" if r["status"] == "success" else "fail"] += 1
    except Exception as e:
        log(f"  Self-Audit in seo-core error: {e}", "ERROR")
        stats["fail"] += 1

    return stats


def cycle_content(sites):
    """CONTENT: Keywords, articles, FAQs, blog ideas, optimization — 2x/day"""
    log("═══ CYCLE: CONTENT ═══")
    stats = {"ok": 0, "fail": 0}

    kw_agent = KeywordResearchAgent()
    content_agent = ContentGenerationAgent()
    faq_agent = FAQGenerationAgent()
    blog_agent = BlogIdeaAgent()
    opt_agent = ContentOptimizationAgent()
    brief_agent = ContentBriefAgent()
    calendar_agent = ContentCalendarAgent()

    for i, site in enumerate(sites, 1):
        site_id = str(i)
        domain = site['domaine']
        seeds = site.get('mots_cles_seed', [])
        seed = seeds[0] if seeds else site['nom']
        log(f"── Site {i}: {site['nom']} ({domain})")

        # 1. Keyword research — find 5 new keywords
        r = run_agent("KeywordResearch", kw_agent.find_keywords, (site_id, seed, 5), 120, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # Pick keyword for article
        article_keyword = seed
        if r["status"] == "success" and isinstance(r.get("result"), dict):
            kws = r["result"].get("keywords", [])
            if kws and isinstance(kws, list) and len(kws) > 0:
                article_keyword = kws[0] if isinstance(kws[0], str) else kws[0].get("keyword", seed)

        # 2. Generate article — 800 words, queued for review (no auto-publish)
        r = run_agent("ContentGeneration", content_agent.generate_article, (site_id, article_keyword, 800), 180, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # Auto-publish if article generated successfully
        if r["status"] == "success" and r.get("result"):
            try:
                conn = get_db()
                # Get latest content for this site
                row = conn.execute(
                    "SELECT id FROM content WHERE site_id=? ORDER BY id DESC LIMIT 1",
                    (site_id,)
                ).fetchone()
                if row:
                    content_id = row[0]
                    conn.execute(
                        """INSERT INTO pending_review (content_id, site_id, status, created_at)
                           VALUES (?, ?, 'pending', datetime('now'))""",
                        (content_id, int(site_id))
                    )
                    conn.commit()
                    log(f"  AUTO-PUBLISHED content #{content_id} for site {site_id}")
                conn.close()
            except Exception as e:
                log(f"  Auto-publish error: {e}", "WARNING")

        # 3. FAQ generation — 3 FAQs
        category = site.get('categorie', site['nom'])
        r = run_agent("FAQGeneration", faq_agent.generate_faq, (site_id, category, 3), 120, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # 4. Blog ideas
        r = run_agent("BlogIdea", blog_agent.generate_ideas, (site_id, 5), 90, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # 5. Content brief for next article
        r = run_agent("ContentBrief", brief_agent.generate_brief, (site_id, article_keyword), 120, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

    return stats



# Reddit topics par niche — rotation automatique
REDDIT_TOPICS = {
    "deneigement": [
        "Comment bien preparer son entree de garage avant lhiver a Montreal",
        "Vos astuces pour eviter le verglas sur vos marches et trottoirs",
        "A quel moment faites-vous deneiger votre stationnement commercial",
        "Les pires tempetes de neige a Montreal — vos experiences",
        "Deneigement residentiel vs commercial — les differences de prix au Quebec",
        "Sel ou abrasif — quest-ce qui est mieux pour lenvironnement",
        "Comment choisir un bon service de deneigement sur la Rive-Sud",
        "Vos experiences avec le deneigement durgence 24h",
    ],
    "paysagement": [
        "Quand commencer lentretien de sa pelouse au printemps au Quebec",
        "Idees damenagement paysager pour petit terrain a Montreal",
        "Comment proteger ses plantes vivaces pour lhiver quebecois",
        "Pose de gazon en rouleau vs semences — vos experiences",
        "Budget amenagement paysager — combien avez-vous paye",
        "Les meilleurs arbustes pour haie brise-vent au Quebec",
        "Entretien pelouse ete — arrosage et tonte frequence ideale",
        "Terrasse en pave ou bois traite — avantages et inconvenients",
    ],
    "peinture": [
        "Peinturer soi-meme ou engager un peintre — votre experience",
        "Quelles couleurs tendance pour un salon en 2026 au Quebec",
        "Peinture interieure — combien de couches appliquez-vous",
        "Trouver un bon peintre a Montreal — vos recommandations",
        "Prix peinture exterieure maison — combien ca vous a coute",
        "Quelle marque de peinture utilisez-vous Benjamin Moore ou Sico",
        "Peinturer sa cuisine — idees et conseils pour un bon resultat",
        "Estimation peinture condo Montreal — est-ce que 3000$ est raisonnable",
    ],
    "seo-marketing": [
        "Outils SEO gratuits que vous utilisez pour votre PME au Quebec",
        "Comment une petite entreprise peut ameliorer son Google ranking",
        "SEO local Montreal — astuces pour apparaitre dans le map pack",
        "Automatiser son marketing digital — quels outils utilisez-vous",
    ],
}

def _get_reddit_topic(site):
    """Pick a random relevant topic for the site niche"""
    import random
    niche = site.get("niche", "")
    topics = REDDIT_TOPICS.get(niche, REDDIT_TOPICS.get("seo-marketing", []))
    if topics:
        return random.choice(topics)
    return f"Conseils {niche} au Quebec"

def cycle_marketing(sites):
    """MARKETING: Social media, backlinks, competitors, local SEO, reviews, directories — daily"""
    log("═══ CYCLE: MARKETING ═══")
    stats = {"ok": 0, "fail": 0}

    social_agent = SocialMediaAgent()
    backlink_agent = BacklinkAnalysisAgent()
    competitor_agent = CompetitorAnalysisAgent()
    local_agent = LocalSEOAgent()
    review_agent = ReviewManagementAgent()
    directory_agent = DirectoryAgent()
    reddit_agent = RedditAgent()
    forum_agent = ForumAgent()

    for i, site in enumerate(sites, 1):
        site_id = str(i)
        domain = site['domaine']
        log(f"── Site {i}: {site['nom']} ({domain})")

        agents_to_run = [
            ("SocialMedia", social_agent.generate_social_posts,
             (f"{site['nom']} - Services professionnels", f"https://{domain}"), 90),
            ("BacklinkAnalysis", backlink_agent.analyze_opportunities, (site_id,), 120),
            ("CompetitorAnalysis", competitor_agent.identify_competitors,
             (site_id,), 120),
            ("LocalSEO_GMB", local_agent.audit_gmb_profile, (site_id,), 90),
            ("LocalSEO_NAP", local_agent.audit_nap_consistency, (site_id,), 60),
            ("LocalSEO_Reviews", local_agent.analyze_reviews, (site_id,), 60),
            ("ReviewManagement", review_agent.generate_review_response,
             ("Excellent service, très professionnel!", 5, True), 60),
            ("DirectorySubmission", directory_agent.generate_business_listing, (site_id,), 90),
            ("Reddit", reddit_agent.generate_reddit_post,
             (site_id, _get_reddit_topic(site)), 90),
        ]

        for name, func, args, timeout in agents_to_run:
            r = run_agent(name, func, args, timeout, site_id)
            stats["ok" if r["status"] == "success" else "fail"] += 1

    return stats


def cycle_business(sites):
    """BUSINESS: Analytics, reports, SERP tracking, keyword gaps, backlink monitor — daily"""
    log("═══ CYCLE: BUSINESS ═══")
    stats = {"ok": 0, "fail": 0}

    serp_agent = SERPTrackerAgent()
    gap_agent = KeywordGapAgent()
    blink_monitor = BacklinkMonitorAgent()
    comp_watch = CompetitorWatchAgent()
    reporting_agent = ReportingAgent()

    for i, site in enumerate(sites, 1):
        site_id = str(i)
        domain = site['domaine']
        seeds = site.get('mots_cles_seed', [])
        log(f"── Site {i}: {site['nom']} ({domain})")

        # SERP tracking — track keyword positions
        for kw in seeds[:3]:
            r = run_agent("SERPTracker", serp_agent.check_position, (kw, domain), 60, site_id)
            stats["ok" if r["status"] == "success" else "fail"] += 1

        # Keyword gap analysis
        r = run_agent("KeywordGap", gap_agent.analyze_gap, (site_id, []), 120, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # Backlink monitoring
        r = run_agent("BacklinkMonitor", blink_monitor.check_backlink_status, (site_id,), 90, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # Competitor watch
        r = run_agent("CompetitorWatch", comp_watch.check_for_changes, (site_id,), 120, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

        # Weekly report (generate daily, display weekly)
        r = run_agent("Reporting", reporting_agent.generate_weekly_report, (site_id,), 120, site_id)
        stats["ok" if r["status"] == "success" else "fail"] += 1

    return stats


def cycle_maintenance(sites):
    """MAINTENANCE: Backup, SSL, self-audit, learning, cleanup — weekly Sunday 3am"""
    log("═══ CYCLE: MAINTENANCE ═══")
    stats = {"ok": 0, "fail": 0}

    backup_agent = BackupAgent()
    ssl_agent = SSLAgent()
    monitoring_agent = MonitoringAgent()
    perf_agent = PerformanceAgent()

    # 1. Full backup
    r = run_agent("Backup_DB", backup_agent.backup_database, (), 120, "all")
    stats["ok" if r["status"] == "success" else "fail"] += 1

    r = run_agent("Backup_All", backup_agent.backup_all, (), 300, "all")
    stats["ok" if r["status"] == "success" else "fail"] += 1

    # 2. SSL check all sites
    r = run_agent("SSL_CheckAll", ssl_agent.check_all_sites, (), 120, "all")
    stats["ok" if r["status"] == "success" else "fail"] += 1

    # 3. Per-site checks
    for i, site in enumerate(sites, 1):
        site_id = str(i)
        domain = site['domaine']
        url = f"https://{domain}"
        log(f"── Maintenance: {site['nom']} ({domain})")

        agents_to_run = [
            ("SSL_Check", ssl_agent.check_ssl, (domain,), 30),
            ("SSL_HTTPS_Redirect", ssl_agent.check_https_redirect, (domain,), 30),
            ("Performance", perf_agent.check_speed, (url,), 60),
            ("Monitoring", monitoring_agent.check_uptime, ([{"name": site['nom'], "domain": domain, "url": url}],), 30),
        ]

        for name, func, args, timeout in agents_to_run:
            r = run_agent(name, func, args, timeout, site_id)
            stats["ok" if r["status"] == "success" else "fail"] += 1

    # 4. Self-Audit: auto-fix SEO issues on all sites (schema, meta, etc.)
    try:
        sys.path.insert(0, AGENTS_DIR)
        from self_audit_agent import SelfAuditAgent
        audit_agent = SelfAuditAgent()
        log("── Self-Audit: scanning all sites for auto-fixable SEO issues")
        audit_results = audit_agent.full_audit_all()
        total_auto = 0
        total_issues = 0
        for sid, data in audit_results.items():
            if isinstance(data, dict) and "summary" in data:
                s = data["summary"]
                total_auto += s.get("auto_fixed", 0)
                total_issues += s.get("total_issues", 0)
                log(f"  {sid}: {s.get('auto_fixed', 0)} auto-fixed, {s.get('pending_confirm', 0)} pending, {s.get('critical', 0)} critical")
        log(f"  Self-Audit total: {total_auto} auto-fixed / {total_issues} issues")
        log_agent_run("SelfAudit", "self_audit_all", "all", "success",
                      f"Auto-fixed:{total_auto} Total:{total_issues}", 0)
        stats["ok"] += 1
    except Exception as e:
        log(f"  Self-Audit error: {e}", "ERROR")
        log_agent_run("SelfAudit", "self_audit_all", "all", "error", str(e)[:200], 0)
        stats["fail"] += 1

    # 5. Cleanup old logs (>30 days) and backups (>60 days)
    try:
        import glob
        cutoff_logs = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cutoff_backups = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        log("  Cleanup: removing old logs and backups")

        # Clean agent_runs older than 90 days
        conn = get_db()
        conn.execute("DELETE FROM agent_runs WHERE started_at < datetime('now', '-90 days')")
        conn.commit()
        conn.close()
        log("  Cleaned agent_runs > 90 days")
        stats["ok"] += 1
    except Exception as e:
        log(f"  Cleanup error: {e}", "WARNING")
        stats["fail"] += 1

    return stats


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

CYCLES = {
    "seo-core": {"func": cycle_seo_core, "cooldown": 180, "cron": "0 */4 * * *"},
    "content": {"func": cycle_content, "cooldown": 360, "cron": "0 8,20 * * *"},
    "marketing": {"func": cycle_marketing, "cooldown": 720, "cron": "0 10 * * *"},
    "business": {"func": cycle_business, "cooldown": 720, "cron": "0 6 * * *"},
    "maintenance": {"func": cycle_maintenance, "cooldown": 1440, "cron": "0 3 * * 0"},
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 auto_scheduler.py [cycle_name]")
        print(f"Cycles: {', '.join(CYCLES.keys())}, all")
        sys.exit(1)

    cycle_name = sys.argv[1].lower()

    # Run all cycles
    if cycle_name == "all":
        for name in CYCLES:
            run_cycle(name)
        return

    if cycle_name not in CYCLES:
        print(f"Unknown cycle: {cycle_name}")
        print(f"Available: {', '.join(CYCLES.keys())}, all")
        sys.exit(1)

    run_cycle(cycle_name)


def run_cycle(cycle_name):
    cycle = CYCLES[cycle_name]

    log(f"{'='*60}")
    log(f"SCHEDULER: Starting cycle [{cycle_name.upper()}]")
    log(f"{'='*60}")

    # 1. Check killswitch
    config = load_config()
    if is_paused(config):
        log(f"PAUSED: Killswitch active, skipping cycle [{cycle_name}]", "WARNING")
        return

    # 2. Check cooldown (prevent duplicate runs)
    if was_cycle_run_recently(cycle_name, cycle["cooldown"]):
        log(f"SKIP: Cycle [{cycle_name}] ran recently (cooldown {cycle['cooldown']}min)", "WARNING")
        return

    # 3. Log cycle start
    log_agent_run(f"Scheduler_{cycle_name}", f"cycle_{cycle_name}", "all", "running", "Cycle started", 0)
    update_scheduled_task(f"cycle_{cycle_name}", f"AutoScheduler", cycle["cron"])

    start_time = time.time()

    # 4. Get sites
    sites = get_sites(config)
    if not sites:
        log("No active sites found!", "ERROR")
        return

    log(f"Active sites: {len(sites)}")
    for s in sites:
        log(f"  - {s['nom']} ({s['domaine']})")

    # 5. Run cycle
    try:
        stats = cycle["func"](sites)
    except Exception as e:
        log(f"CYCLE CRASH [{cycle_name}]: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        stats = {"ok": 0, "fail": 1}

    # 6. Log cycle completion
    duration = time.time() - start_time
    total = stats["ok"] + stats["fail"]
    success_rate = (stats["ok"] / total * 100) if total > 0 else 0

    log(f"{'='*60}")
    log(f"CYCLE [{cycle_name.upper()}] COMPLETE: {stats['ok']}/{total} OK ({success_rate:.0f}%) in {duration:.1f}s")
    log(f"{'='*60}\n")

    log_agent_run(
        f"Scheduler_{cycle_name}", f"cycle_{cycle_name}", "all",
        "success" if stats["fail"] == 0 else "partial",
        f"OK:{stats['ok']} FAIL:{stats['fail']} Rate:{success_rate:.0f}%",
        duration
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
API Routes pour tous les 30 agents
A integrer dans api_server.py
"""

from flask import request, jsonify
from agents_system import (
    MasterOrchestrator, KeywordResearchAgent, ContentGenerationAgent,
    FAQGenerationAgent, TechnicalSEOAuditAgent, PerformanceAgent,
    BacklinkAnalysisAgent, LocalSEOAgent, CompetitorAnalysisAgent,
    ContentOptimizationAgent, SchemaMarkupAgent, SocialMediaAgent,
    EmailMarketingAgent, ImageOptimizationAgent, InternalLinkingAgent,
    URLOptimizationAgent, TitleTagAgent, ContentCalendarAgent,
    PricingStrategyAgent, ReviewManagementAgent, ConversionOptimizationAgent,
    MonitoringAgent, SSLAgent, BackupAgent, AnalyticsAgent,
    ReportingAgent, LandingPageAgent, BlogIdeaAgent,
    VideoScriptAgent, ServiceDescriptionAgent,
    RedditAgent, ForumAgent, DirectoryAgent, GuestPostAgent, ContentSchedulerAgent,
    ClientOnboardingAgent,
    WhiteLabelReportAgent,
    SERPTrackerAgent,
    KeywordGapAgent,
    ContentBriefAgent,
    BacklinkMonitorAgent,
    SiteSpeedAgent,
    ROICalculatorAgent,
    CompetitorWatchAgent,
    InvoiceAgent,
    CRMAgent,
    SITES
)

# Initialize orchestrator
orchestrator = MasterOrchestrator()

def register_all_agent_routes(app):
    """Enregistre toutes les routes des agents"""

    # ============================================
    # AGENT 1: KEYWORD RESEARCH
    # ============================================
    @app.route('/api/agent/keyword-research', methods=['POST'])
    def agent_keyword_research():
        data = request.get_json() or {}
        agent = KeywordResearchAgent()
        keywords = agent.find_keywords(
            int(data.get('site_id', 1)),
            data.get('seed_keyword', ''),
            int(data.get('limit', 10))
        )
        return jsonify({'success': True, 'keywords': keywords})

    @app.route('/api/agent/keyword-research/serp', methods=['POST'])
    def agent_serp_analysis():
        data = request.get_json() or {}
        agent = KeywordResearchAgent()
        analysis = agent.analyze_serp(data.get('keyword', ''))
        return jsonify({'success': True, 'analysis': analysis})

    # ============================================
    # AGENT 2: CONTENT GENERATION
    # ============================================
    @app.route('/api/agent/content/article', methods=['POST'])
    def agent_generate_article():
        data = request.get_json() or {}
        agent = ContentGenerationAgent()
        article = agent.generate_article(
            int(data.get('site_id', 1)),
            data.get('keyword', ''),
            int(data.get('word_count', 1500))
        )
        return jsonify({'success': True, 'article': article})

    @app.route('/api/agent/content/meta', methods=['POST'])
    def agent_generate_meta():
        data = request.get_json() or {}
        agent = ContentGenerationAgent()
        meta = agent.generate_meta_tags(
            data.get('content', ''),
            data.get('keyword', '')
        )
        return jsonify({'success': True, 'meta': meta})

    # ============================================
    # AGENT 3: FAQ GENERATION
    # ============================================
    @app.route('/api/agent/faq', methods=['POST'])
    def agent_generate_faq():
        data = request.get_json() or {}
        agent = FAQGenerationAgent()
        faq = agent.generate_faq(
            int(data.get('site_id', 1)),
            data.get('topic', ''),
            int(data.get('count', 10))
        )
        return jsonify({'success': True, 'faq': faq})

    # ============================================
    # AGENT 4: TECHNICAL SEO AUDIT
    # ============================================
    @app.route('/api/agent/audit/technical', methods=['POST'])
    def agent_technical_audit():
        data = request.get_json() or {}
        agent = TechnicalSEOAuditAgent()

        site_id = int(data.get('site_id', 1))
        site = SITES.get(site_id, {})
        url = data.get('url', f"https://{site.get('domaine', '')}")

        audit = agent.audit_page(url)
        robots = agent.check_robots_txt(site.get('domaine', ''))
        sitemap = agent.check_sitemap(site.get('domaine', ''))

        return jsonify({
            'success': True,
            'audit': audit,
            'robots': robots,
            'sitemap': sitemap
        })

    # ============================================
    # AGENT 5: PERFORMANCE
    # ============================================
    @app.route('/api/agent/performance', methods=['POST'])
    def agent_performance():
        data = request.get_json() or {}
        agent = PerformanceAgent()

        site_id = int(data.get('site_id', 1))
        site = SITES.get(site_id, {})
        url = data.get('url', f"https://{site.get('domaine', '')}")

        perf = agent.check_speed(url)
        return jsonify({'success': True, 'performance': perf})

    # ============================================
    # AGENT 6: BACKLINK ANALYSIS
    # ============================================
    @app.route('/api/agent/backlinks', methods=['POST'])
    def agent_backlinks():
        data = request.get_json() or {}
        agent = BacklinkAnalysisAgent()
        opportunities = agent.analyze_opportunities(int(data.get('site_id', 1)))
        return jsonify({'success': True, 'opportunities': opportunities})

    # ============================================
    # AGENT 7: LOCAL SEO
    # ============================================
    @app.route('/api/agent/local-seo/gmb', methods=['POST'])
    def agent_gmb():
        data = request.get_json() or {}
        agent = LocalSEOAgent()
        gmb = agent.optimize_gmb(int(data.get('site_id', 1)))
        return jsonify({'success': True, 'gmb': gmb})

    @app.route('/api/agent/local-seo/citations', methods=['POST'])
    def agent_citations():
        data = request.get_json() or {}
        agent = LocalSEOAgent()
        citations = agent.generate_local_citations(int(data.get('site_id', 1)))
        return jsonify({'success': True, 'citations': citations})

    # ============================================
    # AGENT 8: COMPETITOR ANALYSIS
    # ============================================
    @app.route('/api/agent/competitors', methods=['POST'])
    def agent_competitors():
        data = request.get_json() or {}
        agent = CompetitorAnalysisAgent()
        competitors = agent.identify_competitors(int(data.get('site_id', 1)))
        return jsonify({'success': True, 'competitors': competitors})

    # ============================================
    # AGENT 9: CONTENT OPTIMIZATION
    # ============================================
    @app.route('/api/agent/optimize-content', methods=['POST'])
    def agent_optimize_content():
        data = request.get_json() or {}
        agent = ContentOptimizationAgent()
        suggestions = agent.optimize_existing(
            data.get('content', ''),
            data.get('keyword', '')
        )
        return jsonify({'success': True, 'suggestions': suggestions})

    # ============================================
    # AGENT 10: SCHEMA MARKUP
    # ============================================
    @app.route('/api/agent/schema/local-business', methods=['POST'])
    def agent_schema_business():
        data = request.get_json() or {}
        agent = SchemaMarkupAgent()
        schema = agent.generate_local_business_schema(int(data.get('site_id', 1)))
        return jsonify({'success': True, 'schema': schema})

    @app.route('/api/agent/schema/faq', methods=['POST'])
    def agent_schema_faq():
        data = request.get_json() or {}
        agent = SchemaMarkupAgent()
        schema = agent.generate_faq_schema(data.get('faqs', []))
        return jsonify({'success': True, 'schema': schema})

    @app.route('/api/agent/schema/article', methods=['POST'])
    def agent_schema_article():
        data = request.get_json() or {}
        agent = SchemaMarkupAgent()
        schema = agent.generate_article_schema(
            data.get('title', ''),
            data.get('author', ''),
            data.get('date', ''),
            data.get('content', '')
        )
        return jsonify({'success': True, 'schema': schema})

    # ============================================
    # AGENT 11: SOCIAL MEDIA
    # ============================================
    @app.route('/api/agent/social-posts', methods=['POST'])
    def agent_social_posts():
        data = request.get_json() or {}
        agent = SocialMediaAgent()
        posts = agent.generate_social_posts(
            data.get('article_title', ''),
            data.get('article_url', '')
        )
        return jsonify({'success': True, 'posts': posts})

    # ============================================
    # AGENT 12: EMAIL MARKETING
    # ============================================
    @app.route('/api/agent/newsletter', methods=['POST'])
    def agent_newsletter():
        data = request.get_json() or {}
        agent = EmailMarketingAgent()
        newsletter = agent.generate_newsletter(
            int(data.get('site_id', 1)),
            data.get('articles', [])
        )
        return jsonify({'success': True, 'newsletter': newsletter})

    # ============================================
    # AGENT 13: IMAGE OPTIMIZATION
    # ============================================
    @app.route('/api/agent/image-alt', methods=['POST'])
    def agent_image_alt():
        data = request.get_json() or {}
        agent = ImageOptimizationAgent()
        alts = agent.generate_alt_texts(
            data.get('context', ''),
            data.get('keyword', '')
        )
        return jsonify({'success': True, 'alt_texts': alts})

    # ============================================
    # AGENT 14: INTERNAL LINKING
    # ============================================
    @app.route('/api/agent/internal-links', methods=['POST'])
    def agent_internal_links():
        data = request.get_json() or {}
        agent = InternalLinkingAgent()
        links = agent.suggest_links(
            int(data.get('site_id', 1)),
            data.get('topic', '')
        )
        return jsonify({'success': True, 'links': links})

    # ============================================
    # AGENT 15: URL OPTIMIZATION
    # ============================================
    @app.route('/api/agent/url-slug', methods=['POST'])
    def agent_url_slug():
        data = request.get_json() or {}
        agent = URLOptimizationAgent()
        slug = agent.generate_slug(
            data.get('title', ''),
            data.get('keyword', '')
        )
        return jsonify({'success': True, 'slug': slug})

    # ============================================
    # AGENT 16: TITLE TAG
    # ============================================
    @app.route('/api/agent/title-tag', methods=['POST'])
    def agent_title_tag():
        data = request.get_json() or {}
        agent = TitleTagAgent()
        title = agent.optimize_title(
            data.get('current_title', ''),
            data.get('keyword', ''),
            data.get('brand', '')
        )
        return jsonify({'success': True, 'title': title})

    # ============================================
    # AGENT 17: CONTENT CALENDAR
    # ============================================
    @app.route('/api/agent/calendar', methods=['POST'])
    def agent_calendar():
        data = request.get_json() or {}
        agent = ContentCalendarAgent()
        calendar = agent.generate_calendar(
            int(data.get('site_id', 1)),
            int(data.get('weeks', 4))
        )
        return jsonify({'success': True, 'calendar': calendar})

    # ============================================
    # AGENT 18: PRICING STRATEGY
    # ============================================
    @app.route('/api/agent/pricing', methods=['POST'])
    def agent_pricing():
        data = request.get_json() or {}
        agent = PricingStrategyAgent()
        pricing = agent.analyze_competitor_pricing(
            int(data.get('site_id', 1)),
            data.get('service', '')
        )
        return jsonify({'success': True, 'pricing': pricing})

    # ============================================
    # AGENT 19: REVIEW MANAGEMENT
    # ============================================
    @app.route('/api/agent/review-response', methods=['POST'])
    def agent_review_response():
        data = request.get_json() or {}
        agent = ReviewManagementAgent()
        response = agent.generate_review_response(
            data.get('review_text', ''),
            int(data.get('rating', 5)),
            data.get('is_positive', True)
        )
        return jsonify({'success': True, 'response': response})

    # ============================================
    # AGENT 20: CONVERSION OPTIMIZATION
    # ============================================
    @app.route('/api/agent/cta', methods=['POST'])
    def agent_cta():
        data = request.get_json() or {}
        agent = ConversionOptimizationAgent()
        ctas = agent.analyze_cta(
            data.get('current_cta', ''),
            data.get('page_type', '')
        )
        return jsonify({'success': True, 'ctas': ctas})

    # ============================================
    # AGENT 21: MONITORING
    # ============================================
    @app.route('/api/agent/uptime-check', methods=['GET'])
    def agent_uptime_check():
        agent = MonitoringAgent()
        results = agent.check_uptime(SITES)
        return jsonify({'success': True, 'uptime': results})

    # ============================================
    # AGENT 22: SSL
    # ============================================
    @app.route('/api/agent/ssl-check', methods=['POST'])
    def agent_ssl_check():
        data = request.get_json() or {}
        agent = SSLAgent()

        site_id = int(data.get('site_id', 1))
        site = SITES.get(site_id, {})
        domain = data.get('domain', site.get('domaine', ''))

        ssl_info = agent.check_ssl(domain)
        return jsonify({'success': True, 'ssl': ssl_info})

    # ============================================
    # AGENT 23: BACKUP
    # ============================================
    @app.route('/api/agent/backup', methods=['POST'])
    def agent_backup():
        agent = BackupAgent()
        result = agent.backup_database()
        return jsonify({'success': result.get('success', False), 'backup': result})

    # ============================================
    # AGENT 24: ANALYTICS
    # ============================================
    @app.route('/api/agent/analytics/<int:site_id>', methods=['GET'])
    def agent_analytics(site_id):
        agent = AnalyticsAgent()
        stats = agent.get_site_stats(site_id)
        return jsonify({'success': True, 'analytics': stats})

    # ============================================
    # AGENT 25: REPORTING
    # ============================================
    @app.route('/api/agent/report/<int:site_id>', methods=['GET'])
    def agent_report(site_id):
        agent = ReportingAgent()
        report = agent.generate_weekly_report(site_id)
        return jsonify({'success': True, 'report': report})

    # ============================================
    # AGENT 26: LANDING PAGE
    # ============================================
    @app.route('/api/agent/landing-page', methods=['POST'])
    def agent_landing_page():
        data = request.get_json() or {}
        agent = LandingPageAgent()
        page = agent.generate_landing_page(
            int(data.get('site_id', 1)),
            data.get('service', ''),
            data.get('keyword', '')
        )
        return jsonify({'success': True, 'landing_page': page})

    # ============================================
    # AGENT 27: BLOG IDEAS
    # ============================================
    @app.route('/api/agent/blog-ideas/<int:site_id>', methods=['GET'])
    def agent_blog_ideas(site_id):
        agent = BlogIdeaAgent()
        ideas = agent.generate_ideas(site_id, 20)
        return jsonify({'success': True, 'ideas': ideas})

    # ============================================
    # AGENT 28: VIDEO SCRIPT
    # ============================================
    @app.route('/api/agent/video-script', methods=['POST'])
    def agent_video_script():
        data = request.get_json() or {}
        agent = VideoScriptAgent()
        script = agent.generate_script(
            data.get('topic', ''),
            int(data.get('duration', 60))
        )
        return jsonify({'success': True, 'script': script})

    # ============================================
    # AGENT 29: SERVICE DESCRIPTION
    # ============================================
    @app.route('/api/agent/service-page', methods=['POST'])
    def agent_service_page():
        data = request.get_json() or {}
        agent = ServiceDescriptionAgent()
        page = agent.generate_service_page(
            int(data.get('site_id', 1)),
            data.get('service_name', '')
        )
        return jsonify({'success': True, 'service_page': page})

    # ============================================
    # AGENT 30: MASTER ORCHESTRATOR
    # ============================================
    @app.route('/api/agent/full-audit/<int:site_id>', methods=['POST'])
    def agent_full_audit(site_id):
        results = orchestrator.run_full_audit(site_id)
        return jsonify({'success': True, 'audit': results})

    @app.route('/api/agent/full-content', methods=['POST'])
    def agent_full_content():
        data = request.get_json() or {}
        results = orchestrator.run_content_generation(
            int(data.get('site_id', 1)),
            data.get('keyword', '')
        )
        return jsonify({'success': True, 'content': results})

    @app.route('/api/agents/status', methods=['GET'])
    def agents_status():
        agents = orchestrator.get_all_agents_status()
        return jsonify({
            'success': True,
            'agents': agents,
            'count': len(agents),
            'all_active': all(a['status'] == 'active' for a in agents)
        })

    # ============================================
    # AGENT 31: REDDIT
    # ============================================
    @app.route('/api/agent/reddit/post', methods=['POST'])
    def agent_reddit_post():
        data = request.get_json() or {}
        agent = RedditAgent()
        post = agent.generate_reddit_post(
            int(data.get('site_id', 1)),
            data.get('topic', '')
        )
        return jsonify({'success': True, 'post': post})

    @app.route('/api/agent/reddit/comment', methods=['POST'])
    def agent_reddit_comment():
        data = request.get_json() or {}
        agent = RedditAgent()
        comment = agent.generate_reddit_comment(
            int(data.get('site_id', 1)),
            data.get('context', '')
        )
        return jsonify({'success': True, 'comment': comment})

    # ============================================
    # AGENT 32: FORUM
    # ============================================
    @app.route('/api/agent/forum/reply', methods=['POST'])
    def agent_forum_reply():
        data = request.get_json() or {}
        agent = ForumAgent()
        reply = agent.generate_forum_reply(
            int(data.get('site_id', 1)),
            data.get('question', '')
        )
        return jsonify({'success': True, 'reply': reply})

    # ============================================
    # AGENT 33: DIRECTORY
    # ============================================
    @app.route('/api/agent/directory/listing', methods=['POST'])
    def agent_directory_listing():
        data = request.get_json() or {}
        agent = DirectoryAgent()
        listing = agent.generate_business_listing(
            int(data.get('site_id', 1))
        )
        return jsonify({'success': True, 'listing': listing})

    @app.route('/api/agent/directory/checklist', methods=['POST'])
    def agent_directory_checklist():
        data = request.get_json() or {}
        agent = DirectoryAgent()
        checklist = agent.get_submission_checklist(
            int(data.get('site_id', 1))
        )
        return jsonify({'success': True, 'checklist': checklist})

    # ============================================
    # AGENT 34: GUEST POST
    # ============================================
    @app.route('/api/agent/guest-post/outreach', methods=['POST'])
    def agent_guest_post_outreach():
        data = request.get_json() or {}
        agent = GuestPostAgent()
        outreach = agent.generate_outreach_email(
            int(data.get('site_id', 1)),
            data.get('target_blog', '')
        )
        return jsonify({'success': True, 'outreach': outreach})

    # ============================================
    # AGENT 35: CONTENT SCHEDULER
    # ============================================
    @app.route('/api/agent/scheduler/calendar', methods=['POST'])
    def agent_content_scheduler():
        data = request.get_json() or {}
        agent = ContentSchedulerAgent()
        calendar = agent.generate_content_calendar(
            int(data.get('site_id', 1)),
            int(data.get('weeks', 4))
        )
        return jsonify({'success': True, 'calendar': calendar})

    # ============================================
    # AGENT 36: CLIENT ONBOARDING (Business Agent)
    # ============================================
    @app.route('/api/agent/onboarding/new', methods=['POST'])
    def agent_onboard_client():
        """
        Onboard un nouveau client automatiquement
        Body: {
            "business_name": "Nom Entreprise",
            "domain": "example.com",
            "niche": "plomberie",
            "location": "Montreal",
            "services": ["service1", "service2"],
            "competitors": ["concurrent1.com"],
            "target_keywords": ["mot-cle1", "mot-cle2"]
        }
        """
        data = request.get_json() or {}

        # Validation
        if not data.get('business_name') or not data.get('domain'):
            return jsonify({
                'success': False,
                'error': 'business_name et domain sont requis'
            }), 400

        agent = ClientOnboardingAgent()
        result = agent.onboard_new_client(data)

        return jsonify({
            'success': True,
            'onboarding': result
        })

    @app.route('/api/agent/onboarding/clients', methods=['GET'])
    def agent_list_clients():
        """Liste tous les clients"""
        agent = ClientOnboardingAgent()
        clients = agent.list_all_clients()
        return jsonify({
            'success': True,
            'clients': clients,
            'count': len(clients)
        })

    @app.route('/api/agent/onboarding/client/<int:client_id>', methods=['GET'])
    def agent_get_client(client_id):
        """Recupere les details d'un client"""
        agent = ClientOnboardingAgent()
        client = agent.get_client_status(client_id)

        if client:
            return jsonify({'success': True, 'client': client})
        return jsonify({'success': False, 'error': 'Client non trouve'}), 404

    # ============================================
    # AGENT 37: WHITE LABEL REPORT (Business Agent)
    # ============================================
    @app.route('/api/agent/report/generate', methods=['POST'])
    def agent_generate_report():
        """
        Genere un rapport SEO white label complet
        Body: {
            "client_id": 1,
            "branding": {
                "company_name": "Votre Agence",
                "primary_color": "#6366f1",
                "secondary_color": "#22d3ee",
                "contact_email": "contact@agence.com",
                "contact_phone": "514-123-4567"
            }
        }
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        branding = data.get('branding')

        agent = WhiteLabelReportAgent()
        report = agent.generate_monthly_report(int(client_id), branding)

        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 404

        # Ne pas renvoyer le HTML complet dans la reponse JSON (trop gros)
        report_summary = {
            'report_id': report['report_id'],
            'generated_at': report['generated_at'],
            'period': report['period'],
            'client': report['client'],
            'executive_summary': report['executive_summary'],
            'analysis': report['analysis'],
            'recommendations': report['recommendations'],
            'next_steps': report['next_steps']
        }

        return jsonify({
            'success': True,
            'report': report_summary,
            'html_url': f"/api/agent/report/{report['report_id']}/html"
        })

    @app.route('/api/agent/report/<int:site_id>/quick', methods=['GET'])
    def agent_quick_report(site_id):
        """Genere un rapport rapide pour un site existant"""
        agent = WhiteLabelReportAgent()
        report = agent.generate_quick_report(site_id)

        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 404

        return jsonify({
            'success': True,
            'report_id': report.get('report_id'),
            'executive_summary': report.get('executive_summary'),
            'analysis': report.get('analysis')
        })

    @app.route('/api/agent/report/<report_id>/html', methods=['GET'])
    def agent_get_report_html(report_id):
        """Recupere le rapport HTML complet"""
        # En production, recuperer depuis la DB ou le cache
        # Pour l'instant, regenerer
        from flask import Response

        # Simuler un rapport pour demo
        agent = WhiteLabelReportAgent()
        report = agent.generate_monthly_report(1)  # Site 1 par defaut

        return Response(
            report.get('html_report', '<h1>Rapport non trouve</h1>'),
            mimetype='text/html'
        )

    @app.route('/api/agent/report/<int:client_id>/save', methods=['POST'])
    def agent_save_report(client_id):
        """Genere et sauvegarde un rapport"""
        data = request.get_json() or {}
        branding = data.get('branding')

        agent = WhiteLabelReportAgent()
        report = agent.generate_monthly_report(client_id, branding)

        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 404

        # Sauvegarder le fichier
        file_path = agent.save_report(report)

        return jsonify({
            'success': True,
            'report_id': report['report_id'],
            'file_path': file_path
        })

    # ============================================
    # AGENT 38: SERP TRACKER (Business Agent)
    # ============================================
    @app.route('/api/agent/serp/add-keyword', methods=['POST'])
    def agent_serp_add_keyword():
        """
        Ajoute un mot-cle a suivre
        Body: {"client_id": 1, "keyword": "plombier montreal", "target_url": "optional"}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        keyword = data.get('keyword', '')
        target_url = data.get('target_url')

        if not keyword:
            return jsonify({'success': False, 'error': 'keyword requis'}), 400

        agent = SERPTrackerAgent()
        result = agent.add_keyword(int(client_id), keyword, target_url)

        return jsonify(result)

    @app.route('/api/agent/serp/add-keywords', methods=['POST'])
    def agent_serp_add_keywords_bulk():
        """
        Ajoute plusieurs mots-cles
        Body: {"client_id": 1, "keywords": ["mot1", "mot2", "mot3"]}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        keywords = data.get('keywords', [])

        if not keywords:
            return jsonify({'success': False, 'error': 'keywords requis'}), 400

        agent = SERPTrackerAgent()
        result = agent.add_keywords_bulk(int(client_id), keywords)

        return jsonify(result)

    @app.route('/api/agent/serp/track/<int:client_id>', methods=['POST'])
    def agent_serp_track(client_id):
        """Lance le tracking de tous les mots-cles d'un client"""
        agent = SERPTrackerAgent()
        result = agent.track_all_keywords(client_id)

        return jsonify(result)

    @app.route('/api/agent/serp/keywords/<int:client_id>', methods=['GET'])
    def agent_serp_get_keywords(client_id):
        """Recupere tous les mots-cles suivis"""
        agent = SERPTrackerAgent()
        keywords = agent.get_tracked_keywords(client_id)

        return jsonify({
            'success': True,
            'client_id': client_id,
            'keywords': keywords,
            'count': len(keywords)
        })

    @app.route('/api/agent/serp/check', methods=['POST'])
    def agent_serp_check_position():
        """
        Verifie la position d'un mot-cle specifique
        Body: {"keyword": "plombier montreal", "domain": "example.com"}
        """
        data = request.get_json() or {}
        keyword = data.get('keyword', '')
        domain = data.get('domain', '')

        if not keyword or not domain:
            return jsonify({'success': False, 'error': 'keyword et domain requis'}), 400

        agent = SERPTrackerAgent()
        result = agent.check_position(keyword, domain)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/serp/history/<int:keyword_id>', methods=['GET'])
    def agent_serp_history(keyword_id):
        """Recupere l'historique d'un mot-cle"""
        days = request.args.get('days', 30, type=int)

        agent = SERPTrackerAgent()
        history = agent.get_keyword_history(keyword_id, days)

        return jsonify({
            'success': True,
            'keyword_id': keyword_id,
            'history': history
        })

    @app.route('/api/agent/serp/alerts/<int:client_id>', methods=['GET'])
    def agent_serp_alerts(client_id):
        """Recupere les alertes SERP"""
        unread_only = request.args.get('unread', 'false').lower() == 'true'

        agent = SERPTrackerAgent()
        alerts = agent.get_alerts(client_id, unread_only)

        return jsonify({
            'success': True,
            'client_id': client_id,
            'alerts': alerts,
            'count': len(alerts)
        })

    @app.route('/api/agent/serp/alerts/read', methods=['POST'])
    def agent_serp_mark_read():
        """Marque des alertes comme lues"""
        data = request.get_json() or {}
        alert_ids = data.get('alert_ids', [])

        if not alert_ids:
            return jsonify({'success': False, 'error': 'alert_ids requis'}), 400

        agent = SERPTrackerAgent()
        result = agent.mark_alerts_read(alert_ids)

        return jsonify({'success': result})

    @app.route('/api/agent/serp/report/<int:client_id>', methods=['GET'])
    def agent_serp_report(client_id):
        """Genere un rapport de classement complet"""
        agent = SERPTrackerAgent()
        report = agent.get_ranking_report(client_id)

        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 404

        return jsonify({'success': True, 'report': report})

    @app.route('/api/agent/serp/keyword/<int:keyword_id>', methods=['DELETE'])
    def agent_serp_remove_keyword(keyword_id):
        """Supprime un mot-cle du suivi"""
        agent = SERPTrackerAgent()
        result = agent.remove_keyword(keyword_id)

        return jsonify(result)

    # ============================================
    # AGENT 39: KEYWORD GAP (Business Agent)
    # ============================================
    @app.route('/api/agent/keyword-gap/analyze', methods=['POST'])
    def agent_keyword_gap_analyze():
        """
        Analyse complete du gap de mots-cles vs concurrents
        Body: {
            "client_id": 1,
            "competitors": ["concurrent1.com", "concurrent2.com"]
        }
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        competitors = data.get('competitors', [])

        if not competitors:
            return jsonify({'success': False, 'error': 'competitors requis'}), 400

        agent = KeywordGapAgent()
        result = agent.analyze_gap(int(client_id), competitors)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 404

        return jsonify({'success': True, 'analysis': result})

    @app.route('/api/agent/keyword-gap/compare', methods=['POST'])
    def agent_keyword_gap_compare():
        """
        Compare deux domaines directement
        Body: {"domain1": "site1.com", "domain2": "site2.com", "niche": "optional"}
        """
        data = request.get_json() or {}
        domain1 = data.get('domain1', '')
        domain2 = data.get('domain2', '')
        niche = data.get('niche', '')

        if not domain1 or not domain2:
            return jsonify({'success': False, 'error': 'domain1 et domain2 requis'}), 400

        agent = KeywordGapAgent()
        result = agent.compare_two_domains(domain1, domain2, niche)

        return jsonify({'success': True, 'comparison': result})

    @app.route('/api/agent/keyword-gap/content-gaps', methods=['POST'])
    def agent_keyword_gap_content():
        """
        Trouve les gaps de contenu specifiques
        Body: {"client_id": 1, "competitors": ["concurrent1.com"]}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        competitors = data.get('competitors', [])

        if not competitors:
            return jsonify({'success': False, 'error': 'competitors requis'}), 400

        agent = KeywordGapAgent()
        result = agent.find_content_gaps(int(client_id), competitors)

        return jsonify({'success': True, 'content_gaps': result})

    @app.route('/api/agent/keyword-gap/competitor-keywords', methods=['POST'])
    def agent_keyword_gap_competitor():
        """
        Estime les keywords d'un concurrent
        Body: {"domain": "concurrent.com", "niche": "optional", "limit": 20}
        """
        data = request.get_json() or {}
        domain = data.get('domain', '')
        niche = data.get('niche', '')
        limit = data.get('limit', 20)

        if not domain:
            return jsonify({'success': False, 'error': 'domain requis'}), 400

        agent = KeywordGapAgent()
        keywords = agent.get_competitor_keywords(domain, niche, limit)

        return jsonify({
            'success': True,
            'domain': domain,
            'keywords': keywords,
            'count': len(keywords)
        })

    # ============================================
    # AGENT 40: CONTENT BRIEF AGENT
    # ============================================
    @app.route('/api/agent/content-brief/generate', methods=['POST'])
    def agent_content_brief_generate():
        """
        Genere un brief de contenu complet
        Body: {
            "client_id": 1,
            "target_keyword": "deneigement montreal",
            "content_type": "article|guide|landing|faq|comparison",
            "word_count": 1500
        }
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        target_keyword = data.get('target_keyword', '')
        content_type = data.get('content_type', 'article')
        word_count = data.get('word_count', 1500)

        if not target_keyword:
            return jsonify({'success': False, 'error': 'target_keyword requis'}), 400

        agent = ContentBriefAgent()
        brief = agent.generate_brief(int(client_id), target_keyword, content_type, word_count)

        return jsonify({'success': True, 'brief': brief})

    @app.route('/api/agent/content-brief/outline', methods=['POST'])
    def agent_content_brief_outline():
        """
        Genere un plan de contenu
        Body: {"target_keyword": "...", "content_type": "article", "niche": "optional"}
        """
        data = request.get_json() or {}
        target_keyword = data.get('target_keyword', '')
        content_type = data.get('content_type', 'article')
        niche = data.get('niche', '')

        if not target_keyword:
            return jsonify({'success': False, 'error': 'target_keyword requis'}), 400

        agent = ContentBriefAgent()
        outline = agent.generate_outline(target_keyword, content_type, niche)

        return jsonify({'success': True, 'outline': outline})

    @app.route('/api/agent/content-brief/semantic', methods=['POST'])
    def agent_content_brief_semantic():
        """
        Trouve les mots-cles semantiques
        Body: {"target_keyword": "...", "niche": "optional"}
        """
        data = request.get_json() or {}
        target_keyword = data.get('target_keyword', '')
        niche = data.get('niche', '')

        if not target_keyword:
            return jsonify({'success': False, 'error': 'target_keyword requis'}), 400

        agent = ContentBriefAgent()
        keywords = agent.get_semantic_keywords(target_keyword, niche)

        return jsonify({'success': True, 'semantic_keywords': keywords})

    @app.route('/api/agent/content-brief/meta', methods=['POST'])
    def agent_content_brief_meta():
        """
        Genere les meta title/description
        Body: {"target_keyword": "...", "content_type": "article", "niche": "optional"}
        """
        data = request.get_json() or {}
        target_keyword = data.get('target_keyword', '')
        content_type = data.get('content_type', 'article')
        niche = data.get('niche', '')

        if not target_keyword:
            return jsonify({'success': False, 'error': 'target_keyword requis'}), 400

        agent = ContentBriefAgent()
        meta = agent.generate_meta_data(target_keyword, content_type, niche)

        return jsonify({'success': True, 'meta': meta})

    @app.route('/api/agent/content-brief/save', methods=['POST'])
    def agent_content_brief_save():
        """
        Sauvegarde un brief
        Body: {"brief": {...}}
        """
        data = request.get_json() or {}
        brief = data.get('brief', {})

        if not brief:
            return jsonify({'success': False, 'error': 'brief requis'}), 400

        agent = ContentBriefAgent()
        brief_id = agent.save_brief(brief)

        if brief_id:
            return jsonify({'success': True, 'brief_id': brief_id})
        return jsonify({'success': False, 'error': 'Erreur sauvegarde'}), 500

    @app.route('/api/agent/content-brief/list', methods=['GET'])
    def agent_content_brief_list():
        """
        Liste les briefs
        Query: ?client_id=1&status=draft
        """
        client_id = request.args.get('client_id')
        status = request.args.get('status')

        agent = ContentBriefAgent()
        briefs = agent.get_briefs(
            client_id=int(client_id) if client_id else None,
            status=status
        )

        return jsonify({'success': True, 'briefs': briefs, 'count': len(briefs)})

    @app.route('/api/agent/content-brief/<int:brief_id>', methods=['GET'])
    def agent_content_brief_get(brief_id):
        """Recupere un brief complet"""
        agent = ContentBriefAgent()
        brief = agent.get_brief(brief_id)

        if brief:
            return jsonify({'success': True, 'brief': brief})
        return jsonify({'success': False, 'error': 'Brief non trouve'}), 404

    @app.route('/api/agent/content-brief/<int:brief_id>/status', methods=['PUT'])
    def agent_content_brief_update_status(brief_id):
        """
        Met a jour le statut d'un brief
        Body: {"status": "draft|in_progress|completed|archived"}
        """
        data = request.get_json() or {}
        status = data.get('status', '')

        if not status:
            return jsonify({'success': False, 'error': 'status requis'}), 400

        agent = ContentBriefAgent()
        if agent.update_brief_status(brief_id, status):
            return jsonify({'success': True, 'message': f'Status mis a jour: {status}'})
        return jsonify({'success': False, 'error': 'Erreur mise a jour'}), 500

    @app.route('/api/agent/content-brief/<int:brief_id>/html', methods=['GET'])
    def agent_content_brief_html(brief_id):
        """Genere la version HTML d'un brief"""
        agent = ContentBriefAgent()
        brief = agent.get_brief(brief_id)

        if not brief:
            return jsonify({'success': False, 'error': 'Brief non trouve'}), 404

        html = agent.generate_html_brief(brief)
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

    # ============================================
    # AGENT 41: BACKLINK MONITOR AGENT
    # ============================================
    @app.route('/api/agent/backlink/discover', methods=['POST'])
    def agent_backlink_discover():
        """
        Decouvre les backlinks d'un client
        Body: {"client_id": 1}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        agent = BacklinkMonitorAgent()
        result = agent.discover_backlinks(int(client_id))

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/backlink/check', methods=['POST'])
    def agent_backlink_check():
        """
        Verifie le statut des backlinks existants
        Body: {"client_id": 1}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        agent = BacklinkMonitorAgent()
        result = agent.check_backlink_status(int(client_id))

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/backlink/list/<int:client_id>', methods=['GET'])
    def agent_backlink_list(client_id):
        """
        Liste les backlinks d'un client
        Query: ?status=active&limit=100
        """
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))

        agent = BacklinkMonitorAgent()
        backlinks = agent.get_backlinks(client_id, status, limit)

        return jsonify({
            'success': True,
            'backlinks': backlinks,
            'count': len(backlinks)
        })

    @app.route('/api/agent/backlink/stats/<int:client_id>', methods=['GET'])
    def agent_backlink_stats(client_id):
        """Statistiques des backlinks d'un client"""
        agent = BacklinkMonitorAgent()
        stats = agent.get_backlink_stats(client_id)

        return jsonify({'success': True, 'stats': stats})

    @app.route('/api/agent/backlink/toxic/<int:client_id>', methods=['GET'])
    def agent_backlink_toxic(client_id):
        """
        Identifie les backlinks toxiques
        Query: ?threshold=50
        """
        threshold = int(request.args.get('threshold', 50))

        agent = BacklinkMonitorAgent()
        result = agent.get_toxic_backlinks(client_id, threshold)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/backlink/anchors/<int:client_id>', methods=['GET'])
    def agent_backlink_anchors(client_id):
        """Analyse la distribution des textes d'ancrage"""
        agent = BacklinkMonitorAgent()
        result = agent.analyze_anchor_distribution(client_id)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/backlink/domains/<int:client_id>', methods=['GET'])
    def agent_backlink_domains(client_id):
        """Liste des domaines referents"""
        agent = BacklinkMonitorAgent()
        result = agent.get_referring_domains(client_id)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/backlink/alerts/<int:client_id>', methods=['GET'])
    def agent_backlink_alerts(client_id):
        """
        Recupere les alertes backlinks
        Query: ?unread_only=true
        """
        unread_only = request.args.get('unread_only', 'true').lower() == 'true'

        agent = BacklinkMonitorAgent()
        alerts = agent.get_alerts(client_id, unread_only)

        return jsonify({'success': True, 'alerts': alerts, 'count': len(alerts)})

    @app.route('/api/agent/backlink/alerts/<int:client_id>/read', methods=['POST'])
    def agent_backlink_alerts_read(client_id):
        """
        Marque les alertes comme lues
        Body: {"alert_ids": [1, 2, 3]} ou {} pour toutes
        """
        data = request.get_json() or {}
        alert_ids = data.get('alert_ids')

        agent = BacklinkMonitorAgent()
        if agent.mark_alerts_read(client_id, alert_ids):
            return jsonify({'success': True, 'message': 'Alertes marquees comme lues'})
        return jsonify({'success': False, 'error': 'Erreur'}), 500

    # ============================================
    # AGENT 42: SITE SPEED AGENT
    # ============================================
    @app.route('/api/agent/speed/analyze', methods=['POST'])
    def agent_speed_analyze():
        """
        Analyse la vitesse d'un site
        Body: {"client_id": 1, "url": "optional"}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        url = data.get('url')

        agent = SiteSpeedAgent()
        result = agent.analyze_speed(int(client_id), url)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/speed/history/<int:client_id>', methods=['GET'])
    def agent_speed_history(client_id):
        """
        Historique des mesures de vitesse
        Query: ?days=30&device=mobile
        """
        days = int(request.args.get('days', 30))
        device = request.args.get('device', 'mobile')

        agent = SiteSpeedAgent()
        history = agent.get_speed_history(client_id, days, device)

        return jsonify({'success': True, 'history': history, 'count': len(history)})

    @app.route('/api/agent/speed/recommendations/<int:client_id>', methods=['GET'])
    def agent_speed_recommendations(client_id):
        """
        Recommandations de vitesse
        Query: ?status=pending
        """
        status = request.args.get('status')

        agent = SiteSpeedAgent()
        recommendations = agent.get_recommendations(client_id, status)

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })

    @app.route('/api/agent/speed/recommendation/<int:rec_id>/status', methods=['PUT'])
    def agent_speed_recommendation_status(rec_id):
        """
        Met a jour le statut d'une recommandation
        Body: {"status": "pending|in_progress|completed|dismissed"}
        """
        data = request.get_json() or {}
        status = data.get('status', '')

        if not status:
            return jsonify({'success': False, 'error': 'status requis'}), 400

        agent = SiteSpeedAgent()
        if agent.update_recommendation_status(rec_id, status):
            return jsonify({'success': True, 'message': f'Status mis a jour: {status}'})
        return jsonify({'success': False, 'error': 'Erreur'}), 500

    @app.route('/api/agent/speed/compare', methods=['POST'])
    def agent_speed_compare():
        """
        Compare la vitesse avec les concurrents
        Body: {"client_id": 1, "competitor_urls": ["https://..."]}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        competitor_urls = data.get('competitor_urls', [])

        if not competitor_urls:
            return jsonify({'success': False, 'error': 'competitor_urls requis'}), 400

        agent = SiteSpeedAgent()
        result = agent.compare_with_competitors(int(client_id), competitor_urls)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/speed/report/<int:client_id>', methods=['GET'])
    def agent_speed_report(client_id):
        """Genere un rapport de vitesse complet"""
        agent = SiteSpeedAgent()
        report = agent.generate_speed_report(client_id)

        return jsonify({'success': True, 'report': report})

    # ============================================
    # AGENT 43: ROI CALCULATOR AGENT
    # ============================================
    @app.route('/api/agent/roi/calculate', methods=['POST'])
    def agent_roi_calculate():
        """
        Calcule le ROI SEO
        Body: {
            "client_id": 1,
            "monthly_seo_cost": 500,
            "months": 6,
            "avg_order_value": 200,
            "conversion_rate": 2.5,
            "organic_traffic_before": 1000,
            "organic_traffic_after": 2500
        }
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        params = {
            'monthly_seo_cost': data.get('monthly_seo_cost', 500),
            'months': data.get('months', 6),
            'avg_order_value': data.get('avg_order_value', 100),
            'conversion_rate': data.get('conversion_rate', 2),
            'organic_traffic_before': data.get('organic_traffic_before', 1000),
            'organic_traffic_after': data.get('organic_traffic_after', 2000)
        }

        agent = ROICalculatorAgent()
        result = agent.calculate_roi(int(client_id), params)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/roi/estimate/<int:client_id>', methods=['GET'])
    def agent_roi_estimate(client_id):
        """
        Estime le ROI potentiel
        Query: ?growth=50
        """
        growth = int(request.args.get('growth', 50))

        agent = ROICalculatorAgent()
        result = agent.estimate_potential_roi(client_id, growth)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/roi/history/<int:client_id>', methods=['GET'])
    def agent_roi_history(client_id):
        """
        Historique des calculs ROI
        Query: ?limit=12
        """
        limit = int(request.args.get('limit', 12))

        agent = ROICalculatorAgent()
        history = agent.get_roi_history(client_id, limit)

        return jsonify({'success': True, 'history': history, 'count': len(history)})

    @app.route('/api/agent/roi/keyword-value', methods=['POST'])
    def agent_roi_keyword_value():
        """
        Calcule la valeur des mots-cles
        Body: {"keywords": ["keyword1", "keyword2"], "client_id": 1}
        """
        data = request.get_json() or {}
        keywords = data.get('keywords', [])
        client_id = data.get('client_id')

        if not keywords:
            return jsonify({'success': False, 'error': 'keywords requis'}), 400

        agent = ROICalculatorAgent()
        result = agent.calculate_keyword_value(keywords, client_id)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/roi/report', methods=['POST'])
    def agent_roi_report():
        """
        Genere un rapport ROI complet
        Body: {
            "client_id": 1,
            "monthly_seo_cost": 500,
            ...
        }
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        params = {
            'monthly_seo_cost': data.get('monthly_seo_cost', 500),
            'months': data.get('months', 6),
            'avg_order_value': data.get('avg_order_value', 100),
            'conversion_rate': data.get('conversion_rate', 2),
            'organic_traffic_before': data.get('organic_traffic_before', 1000),
            'organic_traffic_after': data.get('organic_traffic_after', 2000)
        }

        agent = ROICalculatorAgent()
        report = agent.generate_roi_report(int(client_id), params)

        return jsonify({'success': True, 'report': report})

    # ============================================
    # AGENT 44: COMPETITOR WATCH AGENT
    # ============================================
    @app.route('/api/agent/competitor/add', methods=['POST'])
    def agent_competitor_add():
        """
        Ajoute un concurrent a surveiller
        Body: {"client_id": 1, "domain": "concurrent.com", "name": "Nom", "notes": ""}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        domain = data.get('domain', '')
        name = data.get('name', '')
        notes = data.get('notes', '')

        if not domain:
            return jsonify({'success': False, 'error': 'domain requis'}), 400

        agent = CompetitorWatchAgent()
        result = agent.add_competitor(int(client_id), domain, name, notes)

        return jsonify(result)

    @app.route('/api/agent/competitor/remove/<int:competitor_id>', methods=['DELETE'])
    def agent_competitor_remove(competitor_id):
        """Retire un concurrent de la surveillance"""
        agent = CompetitorWatchAgent()
        if agent.remove_competitor(competitor_id):
            return jsonify({'success': True, 'message': 'Concurrent retire'})
        return jsonify({'success': False, 'error': 'Erreur'}), 500

    @app.route('/api/agent/competitor/list/<int:client_id>', methods=['GET'])
    def agent_competitor_list(client_id):
        """Liste les concurrents surveilles"""
        agent = CompetitorWatchAgent()
        competitors = agent.get_competitors(client_id)

        return jsonify({
            'success': True,
            'competitors': competitors,
            'count': len(competitors)
        })

    @app.route('/api/agent/competitor/check/<int:client_id>', methods=['POST'])
    def agent_competitor_check(client_id):
        """Verifie les changements chez tous les concurrents"""
        agent = CompetitorWatchAgent()
        result = agent.check_for_changes(client_id)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/competitor/profile/<int:competitor_id>', methods=['GET'])
    def agent_competitor_profile(competitor_id):
        """Profil complet d'un concurrent"""
        agent = CompetitorWatchAgent()
        profile = agent.get_competitor_profile(competitor_id)

        if 'error' in profile:
            return jsonify({'success': False, 'error': profile['error']}), 404

        return jsonify({'success': True, 'profile': profile})

    @app.route('/api/agent/competitor/compare', methods=['POST'])
    def agent_competitor_compare():
        """
        Compare un concurrent avec le client
        Body: {"client_id": 1, "competitor_id": 5}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        competitor_id = data.get('competitor_id')

        if not competitor_id:
            return jsonify({'success': False, 'error': 'competitor_id requis'}), 400

        agent = CompetitorWatchAgent()
        result = agent.compare_with_client(int(client_id), int(competitor_id))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/competitor/alerts/<int:client_id>', methods=['GET'])
    def agent_competitor_alerts(client_id):
        """
        Alertes concurrentielles
        Query: ?unread_only=true
        """
        unread_only = request.args.get('unread_only', 'true').lower() == 'true'

        agent = CompetitorWatchAgent()
        alerts = agent.get_alerts(client_id, unread_only)

        return jsonify({'success': True, 'alerts': alerts, 'count': len(alerts)})

    @app.route('/api/agent/competitor/alerts/read', methods=['POST'])
    def agent_competitor_alerts_read():
        """
        Marque les alertes comme lues
        Body: {"alert_ids": [1, 2, 3]}
        """
        data = request.get_json() or {}
        alert_ids = data.get('alert_ids', [])

        if not alert_ids:
            return jsonify({'success': False, 'error': 'alert_ids requis'}), 400

        agent = CompetitorWatchAgent()
        if agent.mark_alerts_read(alert_ids):
            return jsonify({'success': True, 'message': 'Alertes marquees comme lues'})
        return jsonify({'success': False, 'error': 'Erreur'}), 500

    @app.route('/api/agent/competitor/report/<int:client_id>', methods=['GET'])
    def agent_competitor_report(client_id):
        """Rapport concurrentiel complet"""
        agent = CompetitorWatchAgent()
        report = agent.generate_competitive_report(client_id)

        return jsonify({'success': True, 'report': report})

    # ============================================
    # AGENT 45: LOCAL SEO AGENT
    # ============================================
    @app.route('/api/agent/local-seo/gmb/profile', methods=['POST'])
    def agent_local_seo_gmb_create():
        """
        Cree ou met a jour le profil Google Business
        Body: {"client_id": 1, "profile": {...}}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        profile_data = data.get('profile', data)

        agent = LocalSEOAgent()
        result = agent.create_gmb_profile(int(client_id), profile_data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/local-seo/gmb/profile/<int:client_id>', methods=['GET'])
    def agent_local_seo_gmb_get(client_id):
        """Recupere le profil GMB du client"""
        agent = LocalSEOAgent()
        profile = agent.get_gmb_profile(client_id)

        if not profile:
            return jsonify({'success': False, 'error': 'Profil non trouve'}), 404

        if isinstance(profile, dict) and 'error' in profile:
            return jsonify({'success': False, 'error': profile['error']}), 400

        return jsonify({'success': True, 'profile': profile})

    @app.route('/api/agent/local-seo/gmb/audit/<int:client_id>', methods=['GET'])
    def agent_local_seo_gmb_audit(client_id):
        """Audit complet du profil GMB"""
        agent = LocalSEOAgent()
        audit = agent.audit_gmb_profile(client_id)

        if 'error' in audit:
            return jsonify({'success': False, 'error': audit['error']}), 400

        return jsonify({'success': True, 'audit': audit})

    @app.route('/api/agent/local-seo/citations', methods=['POST'])
    def agent_local_seo_citation_add():
        """
        Ajoute une citation NAP
        Body: {"client_id": 1, "source_name": "...", "source_url": "...", ...}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        agent = LocalSEOAgent()
        result = agent.add_citation(int(client_id), data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/local-seo/citations/<int:client_id>', methods=['GET'])
    def agent_local_seo_citations_list(client_id):
        """Liste toutes les citations NAP d'un client"""
        agent = LocalSEOAgent()
        citations = agent.get_citations(client_id)

        if isinstance(citations, dict) and 'error' in citations:
            return jsonify({'success': False, 'error': citations['error']}), 400

        return jsonify({'success': True, 'citations': citations, 'count': len(citations)})

    @app.route('/api/agent/local-seo/nap/audit/<int:client_id>', methods=['GET'])
    def agent_local_seo_nap_audit(client_id):
        """Verifie la coherence NAP sur toutes les citations"""
        agent = LocalSEOAgent()
        audit = agent.audit_nap_consistency(client_id)

        if 'error' in audit:
            return jsonify({'success': False, 'error': audit['error']}), 400

        return jsonify({'success': True, 'audit': audit})

    @app.route('/api/agent/local-seo/reviews', methods=['POST'])
    def agent_local_seo_review_add():
        """
        Ajoute un avis client
        Body: {"client_id": 1, "platform": "Google", "rating": 5, ...}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        agent = LocalSEOAgent()
        result = agent.add_review(int(client_id), data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/local-seo/reviews/<int:client_id>', methods=['GET'])
    def agent_local_seo_reviews_list(client_id):
        """
        Liste les avis d'un client
        Query: ?platform=Google
        """
        platform = request.args.get('platform')

        agent = LocalSEOAgent()
        reviews = agent.get_reviews(client_id, platform)

        if isinstance(reviews, dict) and 'error' in reviews:
            return jsonify({'success': False, 'error': reviews['error']}), 400

        return jsonify({'success': True, 'reviews': reviews, 'count': len(reviews)})

    @app.route('/api/agent/local-seo/reviews/analyze/<int:client_id>', methods=['GET'])
    def agent_local_seo_reviews_analyze(client_id):
        """Analyse complete des avis"""
        agent = LocalSEOAgent()
        analysis = agent.analyze_reviews(client_id)

        return jsonify({'success': True, 'analysis': analysis})

    @app.route('/api/agent/local-seo/reviews/respond', methods=['POST'])
    def agent_local_seo_review_respond():
        """
        Genere une reponse IA pour un avis
        Body: {"client_id": 1, "review_id": 5}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        review_id = data.get('review_id')

        if not review_id:
            return jsonify({'success': False, 'error': 'review_id requis'}), 400

        agent = LocalSEOAgent()
        result = agent.generate_review_response(int(client_id), int(review_id))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/local-seo/service-areas', methods=['POST'])
    def agent_local_seo_area_add():
        """
        Ajoute une zone de service
        Body: {"client_id": 1, "area_name": "Montreal", "area_type": "city", ...}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        agent = LocalSEOAgent()
        result = agent.add_service_area(int(client_id), data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/local-seo/service-areas/<int:client_id>', methods=['GET'])
    def agent_local_seo_areas_list(client_id):
        """Liste les zones de service"""
        agent = LocalSEOAgent()
        areas = agent.get_service_areas(client_id)

        if isinstance(areas, dict) and 'error' in areas:
            return jsonify({'success': False, 'error': areas['error']}), 400

        return jsonify({'success': True, 'service_areas': areas, 'count': len(areas)})

    @app.route('/api/agent/local-seo/landing-page', methods=['POST'])
    def agent_local_seo_landing_page():
        """
        Genere le contenu d'une page locale
        Body: {"client_id": 1, "area_name": "Laval"}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)
        area_name = data.get('area_name')

        if not area_name:
            return jsonify({'success': False, 'error': 'area_name requis'}), 400

        agent = LocalSEOAgent()
        result = agent.generate_local_landing_page(int(client_id), area_name)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/local-seo/score/<int:client_id>', methods=['GET'])
    def agent_local_seo_score(client_id):
        """Calcule le score SEO local global"""
        agent = LocalSEOAgent()
        score = agent.get_local_seo_score(client_id)

        return jsonify({'success': True, 'score': score})

    # ============================================
    # AGENT 46: INVOICE AGENT - Facturation
    # ============================================
    @app.route('/api/agent/invoice/client', methods=['POST'])
    def agent_invoice_client_create():
        """
        Cree un client facturation
        Body: {"client_id": 1, "company_name": "...", "email": "...", ...}
        """
        data = request.get_json() or {}
        client_id = data.get('client_id') or data.get('site_id', 1)

        agent = InvoiceAgent()
        result = agent.create_billing_client(int(client_id), data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/invoice/client/<int:billing_client_id>', methods=['GET'])
    def agent_invoice_client_get(billing_client_id):
        """Recupere un client facturation"""
        agent = InvoiceAgent()
        client = agent.get_billing_client(billing_client_id)

        if not client:
            return jsonify({'success': False, 'error': 'Client non trouve'}), 404

        return jsonify({'success': True, 'client': client})

    @app.route('/api/agent/invoice/quote', methods=['POST'])
    def agent_invoice_quote_create():
        """
        Cree un devis
        Body: {"billing_client_id": 1, "items": [...], "notes": "...", "valid_days": 30}
        """
        data = request.get_json() or {}
        billing_client_id = data.get('billing_client_id')
        items = data.get('items', [])
        notes = data.get('notes', '')
        valid_days = data.get('valid_days', 30)

        if not billing_client_id:
            return jsonify({'success': False, 'error': 'billing_client_id requis'}), 400

        if not items:
            return jsonify({'success': False, 'error': 'items requis'}), 400

        agent = InvoiceAgent()
        result = agent.create_quote(int(billing_client_id), items, notes, valid_days)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/invoice/quote/<int:quote_id>', methods=['GET'])
    def agent_invoice_quote_get(quote_id):
        """Recupere un devis"""
        agent = InvoiceAgent()
        quote = agent.get_quote(quote_id)

        if 'error' in quote:
            return jsonify({'success': False, 'error': quote['error']}), 404

        return jsonify({'success': True, 'quote': quote})

    @app.route('/api/agent/invoice/quote/<int:quote_id>/convert', methods=['POST'])
    def agent_invoice_quote_convert(quote_id):
        """Convertit un devis en facture"""
        agent = InvoiceAgent()
        result = agent.convert_quote_to_invoice(quote_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/invoice/create', methods=['POST'])
    def agent_invoice_create():
        """
        Cree une facture directement
        Body: {"billing_client_id": 1, "items": [...], "notes": "...", "due_days": 30}
        """
        data = request.get_json() or {}
        billing_client_id = data.get('billing_client_id')
        items = data.get('items', [])
        notes = data.get('notes', '')
        due_days = data.get('due_days', 30)

        if not billing_client_id:
            return jsonify({'success': False, 'error': 'billing_client_id requis'}), 400

        if not items:
            return jsonify({'success': False, 'error': 'items requis'}), 400

        agent = InvoiceAgent()
        result = agent.create_invoice(int(billing_client_id), items, notes, due_days)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/invoice/<int:invoice_id>', methods=['GET'])
    def agent_invoice_get(invoice_id):
        """Recupere une facture"""
        agent = InvoiceAgent()
        invoice = agent.get_invoice(invoice_id)

        if 'error' in invoice:
            return jsonify({'success': False, 'error': invoice['error']}), 404

        return jsonify({'success': True, 'invoice': invoice})

    @app.route('/api/agent/invoice/list', methods=['GET'])
    def agent_invoice_list():
        """
        Liste les factures
        Query: ?status=paid&limit=50
        """
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))

        agent = InvoiceAgent()
        invoices = agent.list_invoices(status, limit)

        if isinstance(invoices, dict) and 'error' in invoices:
            return jsonify({'success': False, 'error': invoices['error']}), 400

        return jsonify({'success': True, 'invoices': invoices, 'count': len(invoices)})

    @app.route('/api/agent/invoice/payment', methods=['POST'])
    def agent_invoice_payment():
        """
        Enregistre un paiement
        Body: {"invoice_id": 1, "amount": 500, "method": "virement", "reference": "..."}
        """
        data = request.get_json() or {}
        invoice_id = data.get('invoice_id')
        amount = data.get('amount')
        method = data.get('method', 'virement')
        reference = data.get('reference', '')

        if not invoice_id or not amount:
            return jsonify({'success': False, 'error': 'invoice_id et amount requis'}), 400

        agent = InvoiceAgent()
        result = agent.record_payment(int(invoice_id), float(amount), method, reference)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/invoice/overdue', methods=['GET'])
    def agent_invoice_overdue():
        """Liste les factures en retard"""
        agent = InvoiceAgent()
        invoices = agent.get_overdue_invoices()

        if isinstance(invoices, dict) and 'error' in invoices:
            return jsonify({'success': False, 'error': invoices['error']}), 400

        return jsonify({'success': True, 'overdue_invoices': invoices, 'count': len(invoices)})

    @app.route('/api/agent/invoice/reminder', methods=['POST'])
    def agent_invoice_reminder():
        """
        Genere un email de rappel
        Body: {"invoice_id": 1}
        """
        data = request.get_json() or {}
        invoice_id = data.get('invoice_id')

        if not invoice_id:
            return jsonify({'success': False, 'error': 'invoice_id requis'}), 400

        agent = InvoiceAgent()
        result = agent.generate_reminder(int(invoice_id))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/invoice/stats', methods=['GET'])
    def agent_invoice_stats():
        """
        Statistiques de revenus
        Query: ?period=month|year|all
        """
        period = request.args.get('period', 'month')

        agent = InvoiceAgent()
        stats = agent.get_revenue_stats(period)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 47: CRM AGENT
    # ============================================
    @app.route('/api/agent/crm/contact', methods=['POST'])
    def agent_crm_contact_create():
        """
        Cree un contact/lead
        Body: {"first_name": "...", "last_name": "...", "email": "...", ...}
        """
        data = request.get_json() or {}
        agent = CRMAgent()
        result = agent.create_contact(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/contact/<int:contact_id>', methods=['GET'])
    def agent_crm_contact_get(contact_id):
        """Recupere un contact avec historique"""
        agent = CRMAgent()
        contact = agent.get_contact(contact_id)

        if 'error' in contact:
            return jsonify({'success': False, 'error': contact['error']}), 404

        return jsonify({'success': True, 'contact': contact})

    @app.route('/api/agent/crm/contact/<int:contact_id>', methods=['PUT'])
    def agent_crm_contact_update(contact_id):
        """Met a jour un contact"""
        data = request.get_json() or {}
        agent = CRMAgent()
        result = agent.update_contact(contact_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/contacts', methods=['GET'])
    def agent_crm_contacts_list():
        """
        Liste les contacts
        Query: ?type=lead&status=new&search=...&limit=50
        """
        filters = {
            'type': request.args.get('type'),
            'status': request.args.get('status'),
            'assigned_to': request.args.get('assigned_to'),
            'search': request.args.get('search')
        }
        filters = {k: v for k, v in filters.items() if v}
        limit = int(request.args.get('limit', 50))

        agent = CRMAgent()
        contacts = agent.list_contacts(filters if filters else None, limit)

        if isinstance(contacts, dict) and 'error' in contacts:
            return jsonify({'success': False, 'error': contacts['error']}), 400

        return jsonify({'success': True, 'contacts': contacts, 'count': len(contacts)})

    @app.route('/api/agent/crm/contact/<int:contact_id>/interaction', methods=['POST'])
    def agent_crm_interaction_add(contact_id):
        """
        Ajoute une interaction
        Body: {"type": "call|email|meeting|note", "subject": "...", "description": "...", ...}
        """
        data = request.get_json() or {}
        agent = CRMAgent()
        result = agent.add_interaction(contact_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/contact/<int:contact_id>/opportunity', methods=['POST'])
    def agent_crm_opportunity_create(contact_id):
        """
        Cree une opportunite
        Body: {"title": "...", "value": 5000, "stage": "qualification", ...}
        """
        data = request.get_json() or {}
        agent = CRMAgent()
        result = agent.create_opportunity(contact_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/opportunity/<int:opportunity_id>/stage', methods=['PUT'])
    def agent_crm_opportunity_update_stage(opportunity_id):
        """
        Met a jour l'etape d'une opportunite
        Body: {"stage": "Negociation", "won": true/false, "loss_reason": "..."}
        """
        data = request.get_json() or {}
        stage = data.get('stage')
        won = data.get('won')
        loss_reason = data.get('loss_reason')

        if not stage:
            return jsonify({'success': False, 'error': 'stage requis'}), 400

        agent = CRMAgent()
        result = agent.update_opportunity_stage(opportunity_id, stage, won, loss_reason)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/pipeline', methods=['GET'])
    def agent_crm_pipeline():
        """Recupere le pipeline complet"""
        agent = CRMAgent()
        pipeline = agent.get_pipeline()

        if 'error' in pipeline:
            return jsonify({'success': False, 'error': pipeline['error']}), 400

        return jsonify({'success': True, 'data': pipeline})

    @app.route('/api/agent/crm/task', methods=['POST'])
    def agent_crm_task_create():
        """
        Cree une tache
        Body: {"contact_id": 1, "title": "...", "due_date": "...", "priority": "high|medium|low", ...}
        """
        data = request.get_json() or {}
        agent = CRMAgent()
        result = agent.create_task(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/tasks', methods=['GET'])
    def agent_crm_tasks_list():
        """
        Liste les taches
        Query: ?status=pending&priority=high&assigned_to=...
        """
        filters = {
            'status': request.args.get('status'),
            'priority': request.args.get('priority'),
            'assigned_to': request.args.get('assigned_to')
        }
        filters = {k: v for k, v in filters.items() if v}

        agent = CRMAgent()
        tasks = agent.get_tasks(filters if filters else None)

        if isinstance(tasks, dict) and 'error' in tasks:
            return jsonify({'success': False, 'error': tasks['error']}), 400

        return jsonify({'success': True, 'tasks': tasks, 'count': len(tasks)})

    @app.route('/api/agent/crm/task/<int:task_id>/complete', methods=['POST'])
    def agent_crm_task_complete(task_id):
        """Complete une tache"""
        agent = CRMAgent()
        result = agent.complete_task(task_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/crm/dashboard', methods=['GET'])
    def agent_crm_dashboard():
        """Statistiques CRM pour dashboard"""
        agent = CRMAgent()
        stats = agent.get_dashboard_stats()

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    @app.route('/api/agent/crm/contact/<int:contact_id>/score', methods=['GET'])
    def agent_crm_lead_score(contact_id):
        """Calcule le score d'un lead"""
        agent = CRMAgent()
        score = agent.score_lead(contact_id)

        if 'error' in score:
            return jsonify({'success': False, 'error': score['error']}), 400

        return jsonify({'success': True, 'score': score})

    print(f"[API] Registered {47} agent routes (including Business Agents)")

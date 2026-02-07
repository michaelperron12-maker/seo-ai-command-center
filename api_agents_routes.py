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
    AccountingAgent,
    CalendarAgent,
    ChatbotAgent,
    NotificationAgent,
    DashboardAgent,
    LeadScoringAgent,
    EmailCampaignAgent,
    SupportTicketAgent,
    KnowledgeBaseAgent,
    SurveyAgent,
    WebhookAgent,
    AutomationAgent,
    AffiliateAgent,
    LoyaltyAgent,
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

    # ============================================
    # AGENT 48: ACCOUNTING - Comptabilite
    # ============================================

    @app.route('/api/agent/accounting/init', methods=['POST'])
    def agent_accounting_init():
        """Initialise les tables comptables"""
        agent = AccountingAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/accounting/transaction', methods=['POST'])
    def agent_accounting_add_transaction():
        """
        Ajoute une transaction
        Body: {
            date, description, amount, type (revenue|expense),
            category, include_taxes, payment_method, reference
        }
        """
        data = request.get_json() or {}
        agent = AccountingAgent()
        result = agent.add_transaction(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'transaction': result})

    @app.route('/api/agent/accounting/transactions', methods=['GET'])
    def agent_accounting_list_transactions():
        """
        Liste les transactions
        Query: ?type=expense&category=MKTG&start_date=2024-01-01&end_date=2024-12-31&limit=50
        """
        filters = {
            'type': request.args.get('type'),
            'category': request.args.get('category'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }
        filters = {k: v for k, v in filters.items() if v}
        limit = int(request.args.get('limit', 50))

        agent = AccountingAgent()
        transactions = agent.list_transactions(filters if filters else None, limit)

        if isinstance(transactions, dict) and 'error' in transactions:
            return jsonify({'success': False, 'error': transactions['error']}), 400

        return jsonify({'success': True, 'transactions': transactions, 'count': len(transactions)})

    @app.route('/api/agent/accounting/summary', methods=['GET'])
    def agent_accounting_summary():
        """
        Resume financier pour une periode
        Query: ?start_date=2024-01-01&end_date=2024-12-31
        """
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        agent = AccountingAgent()
        summary = agent.get_financial_summary(start_date, end_date)

        if 'error' in summary:
            return jsonify({'success': False, 'error': summary['error']}), 400

        return jsonify({'success': True, 'summary': summary})

    @app.route('/api/agent/accounting/income-statement', methods=['GET'])
    def agent_accounting_income_statement():
        """
        Etat des resultats (Profit & Loss)
        Query: ?start_date=2024-01-01&end_date=2024-12-31
        """
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        agent = AccountingAgent()
        statement = agent.get_income_statement(start_date, end_date)

        if 'error' in statement:
            return jsonify({'success': False, 'error': statement['error']}), 400

        return jsonify({'success': True, 'income_statement': statement})

    @app.route('/api/agent/accounting/balance-sheet', methods=['GET'])
    def agent_accounting_balance_sheet():
        """Bilan comptable"""
        agent = AccountingAgent()
        balance = agent.get_balance_sheet()

        if 'error' in balance:
            return jsonify({'success': False, 'error': balance['error']}), 400

        return jsonify({'success': True, 'balance_sheet': balance})

    @app.route('/api/agent/accounting/tax-report', methods=['GET'])
    def agent_accounting_tax_report():
        """
        Rapport TPS/TVQ pour declaration
        Query: ?quarter=1&year=2024
        """
        quarter = request.args.get('quarter', type=int)
        year = request.args.get('year', type=int)

        agent = AccountingAgent()
        report = agent.get_tax_report(quarter, year)

        if 'error' in report:
            return jsonify({'success': False, 'error': report['error']}), 400

        return jsonify({'success': True, 'tax_report': report})

    @app.route('/api/agent/accounting/expenses', methods=['GET'])
    def agent_accounting_expenses():
        """
        Ventilation des depenses par categorie
        Query: ?start_date=2024-01-01&end_date=2024-12-31
        """
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        agent = AccountingAgent()
        breakdown = agent.get_expense_breakdown(start_date, end_date)

        if 'error' in breakdown:
            return jsonify({'success': False, 'error': breakdown['error']}), 400

        return jsonify({'success': True, 'expense_breakdown': breakdown})

    @app.route('/api/agent/accounting/insights', methods=['GET'])
    def agent_accounting_insights():
        """
        Genere des insights financiers avec AI (Qwen 235B)
        Query: ?months=6
        """
        months = int(request.args.get('months', 6))

        agent = AccountingAgent()
        insights = agent.generate_financial_insights(months)

        if 'error' in insights:
            return jsonify({'success': False, 'error': insights['error']}), 400

        return jsonify({'success': True, 'insights': insights})

    @app.route('/api/agent/accounting/categories', methods=['GET'])
    def agent_accounting_categories():
        """Retourne les categories de depenses et revenus"""
        agent = AccountingAgent()
        categories = agent.get_categories()
        return jsonify({'success': True, 'categories': categories})

    # ============================================
    # AGENT 49: CALENDAR - Calendrier/Reservations
    # ============================================

    @app.route('/api/agent/calendar/init', methods=['POST'])
    def agent_calendar_init():
        """Initialise les tables calendrier"""
        agent = CalendarAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/calendar/event', methods=['POST'])
    def agent_calendar_create_event():
        """
        Cree un evenement
        Body: {title, description, event_type, start_datetime, end_datetime,
               location, video_link, contact_name, contact_email, assigned_to, notes}
        """
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.create_event(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'event': result})

    @app.route('/api/agent/calendar/events', methods=['GET'])
    def agent_calendar_list_events():
        """
        Liste les evenements
        Query: ?start_date=2024-01-01&end_date=2024-12-31&status=confirmed&event_type=MEETING
        """
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        filters = {
            'status': request.args.get('status'),
            'event_type': request.args.get('event_type')
        }
        filters = {k: v for k, v in filters.items() if v}

        agent = CalendarAgent()
        events = agent.get_events(start_date, end_date, filters if filters else None)

        if isinstance(events, dict) and 'error' in events:
            return jsonify({'success': False, 'error': events['error']}), 400

        return jsonify({'success': True, 'events': events, 'count': len(events)})

    @app.route('/api/agent/calendar/event/<int:event_id>', methods=['PUT'])
    def agent_calendar_update_event(event_id):
        """Met a jour un evenement"""
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.update_event(event_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/calendar/event/<int:event_id>/cancel', methods=['POST'])
    def agent_calendar_cancel_event(event_id):
        """Annule un evenement"""
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.cancel_event(event_id, data.get('reason'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/calendar/availability', methods=['GET'])
    def agent_calendar_availability():
        """
        Creneaux disponibles
        Query: ?date=2024-01-15&service_id=1
        """
        date = request.args.get('date')
        service_id = request.args.get('service_id', type=int)

        agent = CalendarAgent()
        availability = agent.get_availability(date, service_id)

        if 'error' in availability:
            return jsonify({'success': False, 'error': availability['error']}), 400

        return jsonify({'success': True, 'availability': availability})

    @app.route('/api/agent/calendar/availability', methods=['POST'])
    def agent_calendar_set_availability():
        """Configure les disponibilites"""
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.set_availability(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/calendar/booking', methods=['POST'])
    def agent_calendar_create_booking():
        """
        Cree une reservation
        Body: {service_id, client_name, client_email, client_phone, booking_date, start_time, notes}
        """
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.create_booking(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'booking': result})

    @app.route('/api/agent/calendar/bookings', methods=['GET'])
    def agent_calendar_list_bookings():
        """
        Liste les reservations
        Query: ?status=pending&date=2024-01-15
        """
        filters = {
            'status': request.args.get('status'),
            'date': request.args.get('date')
        }
        filters = {k: v for k, v in filters.items() if v}
        limit = int(request.args.get('limit', 50))

        agent = CalendarAgent()
        bookings = agent.get_bookings(filters if filters else None, limit)

        if isinstance(bookings, dict) and 'error' in bookings:
            return jsonify({'success': False, 'error': bookings['error']}), 400

        return jsonify({'success': True, 'bookings': bookings, 'count': len(bookings)})

    @app.route('/api/agent/calendar/booking/confirm', methods=['POST'])
    def agent_calendar_confirm_booking():
        """Confirme une reservation par ID ou code"""
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.confirm_booking(data.get('booking_id'), data.get('confirmation_code'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/calendar/booking/cancel', methods=['POST'])
    def agent_calendar_cancel_booking():
        """Annule une reservation par ID ou code"""
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.cancel_booking(data.get('booking_id'), data.get('confirmation_code'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/calendar/service', methods=['POST'])
    def agent_calendar_create_service():
        """
        Cree un service reservable
        Body: {name, description, duration, price, buffer_after, max_advance_days, color}
        """
        data = request.get_json() or {}
        agent = CalendarAgent()
        result = agent.create_service(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'service': result})

    @app.route('/api/agent/calendar/services', methods=['GET'])
    def agent_calendar_list_services():
        """Liste les services reservables"""
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        agent = CalendarAgent()
        services = agent.get_services(active_only)

        if isinstance(services, dict) and 'error' in services:
            return jsonify({'success': False, 'error': services['error']}), 400

        return jsonify({'success': True, 'services': services})

    @app.route('/api/agent/calendar/stats', methods=['GET'])
    def agent_calendar_stats():
        """Statistiques calendrier"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        agent = CalendarAgent()
        stats = agent.get_stats(start_date, end_date)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    @app.route('/api/agent/calendar/event-types', methods=['GET'])
    def agent_calendar_event_types():
        """Types d'evenements disponibles"""
        agent = CalendarAgent()
        return jsonify({'success': True, 'event_types': agent.get_event_types()})

    # ============================================
    # AGENT 50: CHATBOT - Assistant IA
    # ============================================

    @app.route('/api/agent/chatbot/init', methods=['POST'])
    def agent_chatbot_init():
        """Initialise les tables chatbot"""
        agent = ChatbotAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/chatbot/start', methods=['POST'])
    def agent_chatbot_start():
        """
        Demarre une conversation
        Body: {session_id, source, language}
        """
        data = request.get_json() or {}
        session_id = data.get('session_id')

        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

        agent = ChatbotAgent()
        result = agent.start_conversation(
            session_id,
            data.get('source', 'website'),
            data.get('language', 'fr')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'conversation': result})

    @app.route('/api/agent/chatbot/message', methods=['POST'])
    def agent_chatbot_message():
        """
        Envoie un message
        Body: {session_id, message, use_ai}
        """
        data = request.get_json() or {}

        if not data.get('session_id') or not data.get('message'):
            return jsonify({'success': False, 'error': 'session_id et message requis'}), 400

        agent = ChatbotAgent()
        result = agent.send_message(
            data['session_id'],
            data['message'],
            data.get('use_ai', True)
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/chatbot/lead', methods=['POST'])
    def agent_chatbot_capture_lead():
        """
        Capture infos du lead
        Body: {session_id, name, email, phone}
        """
        data = request.get_json() or {}

        if not data.get('session_id'):
            return jsonify({'success': False, 'error': 'session_id requis'}), 400

        agent = ChatbotAgent()
        result = agent.capture_lead(
            data['session_id'],
            data.get('name'),
            data.get('email'),
            data.get('phone')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/chatbot/end', methods=['POST'])
    def agent_chatbot_end():
        """Termine une conversation"""
        data = request.get_json() or {}
        agent = ChatbotAgent()
        result = agent.end_conversation(data.get('session_id'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/chatbot/conversation/<session_id>', methods=['GET'])
    def agent_chatbot_get_conversation(session_id):
        """Obtient une conversation"""
        agent = ChatbotAgent()
        result = agent.get_conversation(session_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'conversation': result})

    @app.route('/api/agent/chatbot/conversations', methods=['GET'])
    def agent_chatbot_list_conversations():
        """Liste les conversations"""
        filters = {
            'status': request.args.get('status'),
            'lead_captured': request.args.get('lead_captured') == 'true',
            'has_email': request.args.get('has_email') == 'true'
        }
        filters = {k: v for k, v in filters.items() if v}
        limit = int(request.args.get('limit', 50))

        agent = ChatbotAgent()
        conversations = agent.list_conversations(filters if filters else None, limit)

        if isinstance(conversations, dict) and 'error' in conversations:
            return jsonify({'success': False, 'error': conversations['error']}), 400

        return jsonify({'success': True, 'conversations': conversations, 'count': len(conversations)})

    @app.route('/api/agent/chatbot/faq', methods=['POST'])
    def agent_chatbot_add_faq():
        """Ajoute une FAQ"""
        data = request.get_json() or {}
        agent = ChatbotAgent()
        result = agent.add_faq(
            data.get('question', ''),
            data.get('answer', ''),
            data.get('keywords'),
            data.get('language', 'fr')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'faq': result})

    @app.route('/api/agent/chatbot/faqs', methods=['GET'])
    def agent_chatbot_list_faqs():
        """Liste les FAQs"""
        language = request.args.get('language', 'fr')
        agent = ChatbotAgent()
        faqs = agent.get_faqs(language)

        if isinstance(faqs, dict) and 'error' in faqs:
            return jsonify({'success': False, 'error': faqs['error']}), 400

        return jsonify({'success': True, 'faqs': faqs})

    @app.route('/api/agent/chatbot/faq/search', methods=['GET'])
    def agent_chatbot_search_faq():
        """Recherche FAQ"""
        query = request.args.get('q', '')
        language = request.args.get('language', 'fr')

        agent = ChatbotAgent()
        results = agent.search_faq(query, language)

        if isinstance(results, dict) and 'error' in results:
            return jsonify({'success': False, 'error': results['error']}), 400

        return jsonify({'success': True, 'results': results})

    @app.route('/api/agent/chatbot/response', methods=['POST'])
    def agent_chatbot_add_response():
        """Ajoute une reponse pre-configuree"""
        data = request.get_json() or {}
        agent = ChatbotAgent()
        result = agent.add_response(
            data.get('intent', ''),
            data.get('response', ''),
            data.get('language', 'fr'),
            data.get('priority', 0)
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/chatbot/config', methods=['GET'])
    def agent_chatbot_get_config():
        """Obtient la config chatbot"""
        agent = ChatbotAgent()
        config = agent.get_config()

        if isinstance(config, dict) and 'error' in config:
            return jsonify({'success': False, 'error': config['error']}), 400

        return jsonify({'success': True, 'config': config})

    @app.route('/api/agent/chatbot/config', methods=['POST'])
    def agent_chatbot_update_config():
        """Met a jour la config"""
        data = request.get_json() or {}
        agent = ChatbotAgent()

        for key, value in data.items():
            agent.update_config(key, value)

        return jsonify({'success': True})

    @app.route('/api/agent/chatbot/stats', methods=['GET'])
    def agent_chatbot_stats():
        """Statistiques chatbot"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        agent = ChatbotAgent()
        stats = agent.get_stats(start_date, end_date)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    @app.route('/api/agent/chatbot/intents', methods=['GET'])
    def agent_chatbot_intents():
        """Liste les intentions"""
        agent = ChatbotAgent()
        return jsonify({'success': True, 'intents': agent.get_intents()})

    # ============================================
    # AGENT 51: NOTIFICATION - Email/SMS/Push
    # ============================================

    @app.route('/api/agent/notification/init', methods=['POST'])
    def agent_notification_init():
        """Initialise les tables notifications"""
        agent = NotificationAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/notification/send', methods=['POST'])
    def agent_notification_send():
        """
        Envoie une notification
        Body: {type, channel, recipient: {email, phone, name}, data: {...}, template_id}
        """
        data = request.get_json() or {}
        agent = NotificationAgent()
        result = agent.send_notification(
            data.get('type', 'CUSTOM'),
            data.get('channel', 'email'),
            data.get('recipient', {}),
            data.get('data', {}),
            data.get('template_id')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'notification': result})

    @app.route('/api/agent/notification/schedule', methods=['POST'])
    def agent_notification_schedule():
        """
        Planifie une notification
        Body: {type, channel, recipient, data, scheduled_at}
        """
        data = request.get_json() or {}
        agent = NotificationAgent()
        result = agent.schedule_notification(
            data.get('type', 'CUSTOM'),
            data.get('channel', 'email'),
            data.get('recipient', {}),
            data.get('data', {}),
            data.get('scheduled_at')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'scheduled': result})

    @app.route('/api/agent/notification/process-queue', methods=['POST'])
    def agent_notification_process_queue():
        """Traite la file d'attente"""
        data = request.get_json() or {}
        limit = int(data.get('limit', 10))

        agent = NotificationAgent()
        result = agent.process_queue(limit)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/notification/list', methods=['GET'])
    def agent_notification_list():
        """Liste les notifications"""
        filters = {
            'type': request.args.get('type'),
            'channel': request.args.get('channel'),
            'status': request.args.get('status')
        }
        filters = {k: v for k, v in filters.items() if v}
        limit = int(request.args.get('limit', 50))

        agent = NotificationAgent()
        notifications = agent.get_notifications(filters if filters else None, limit)

        if isinstance(notifications, dict) and 'error' in notifications:
            return jsonify({'success': False, 'error': notifications['error']}), 400

        return jsonify({'success': True, 'notifications': notifications, 'count': len(notifications)})

    @app.route('/api/agent/notification/template', methods=['POST'])
    def agent_notification_create_template():
        """Cree un template"""
        data = request.get_json() or {}
        agent = NotificationAgent()
        result = agent.create_template(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'template': result})

    @app.route('/api/agent/notification/templates', methods=['GET'])
    def agent_notification_list_templates():
        """Liste les templates"""
        channel = request.args.get('channel')
        notification_type = request.args.get('type')

        agent = NotificationAgent()
        templates = agent.get_templates(channel, notification_type)

        if isinstance(templates, dict) and 'error' in templates:
            return jsonify({'success': False, 'error': templates['error']}), 400

        return jsonify({'success': True, 'templates': templates})

    @app.route('/api/agent/notification/stats', methods=['GET'])
    def agent_notification_stats():
        """Statistiques notifications"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        agent = NotificationAgent()
        stats = agent.get_stats(start_date, end_date)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    @app.route('/api/agent/notification/types', methods=['GET'])
    def agent_notification_types():
        """Types de notifications"""
        agent = NotificationAgent()
        return jsonify({'success': True, 'types': agent.get_notification_types()})

    # ============================================
    # AGENT 52: DASHBOARD - Tableau de Bord Unifie
    # ============================================

    @app.route('/api/agent/dashboard/init', methods=['POST'])
    def agent_dashboard_init():
        """Initialise les tables dashboard"""
        agent = DashboardAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/dashboard/overview', methods=['GET'])
    def agent_dashboard_overview():
        """
        Vue d'ensemble globale
        Query: ?period_days=30
        """
        period_days = int(request.args.get('period_days', 30))
        agent = DashboardAgent()
        overview = agent.get_overview(period_days)

        if 'error' in overview:
            return jsonify({'success': False, 'error': overview['error']}), 400

        return jsonify({'success': True, 'overview': overview})

    @app.route('/api/agent/dashboard/revenue', methods=['GET'])
    def agent_dashboard_revenue():
        """
        Tendance revenus
        Query: ?months=6
        """
        months = int(request.args.get('months', 6))
        agent = DashboardAgent()
        revenue = agent.get_revenue_trend(months)

        if isinstance(revenue, dict) and 'error' in revenue:
            return jsonify({'success': False, 'error': revenue['error']}), 400

        return jsonify({'success': True, 'revenue_trend': revenue})

    @app.route('/api/agent/dashboard/metrics', methods=['GET'])
    def agent_dashboard_metrics():
        """Metriques cles pour widgets"""
        agent = DashboardAgent()
        metrics = agent.get_top_metrics()

        if 'error' in metrics:
            return jsonify({'success': False, 'error': metrics['error']}), 400

        return jsonify({'success': True, 'metrics': metrics})

    @app.route('/api/agent/dashboard/activity', methods=['GET'])
    def agent_dashboard_activity():
        """
        Flux activite recente
        Query: ?limit=20
        """
        limit = int(request.args.get('limit', 20))
        agent = DashboardAgent()
        activity = agent.get_recent_activity(limit)

        if isinstance(activity, dict) and 'error' in activity:
            return jsonify({'success': False, 'error': activity['error']}), 400

        return jsonify({'success': True, 'activity': activity})

    @app.route('/api/agent/dashboard/alerts', methods=['GET'])
    def agent_dashboard_alerts():
        """Alertes et actions requises"""
        agent = DashboardAgent()
        alerts = agent.get_alerts()

        if 'error' in alerts:
            return jsonify({'success': False, 'error': alerts['error']}), 400

        return jsonify({'success': True, 'alerts': alerts})

    @app.route('/api/agent/dashboard/insights', methods=['GET'])
    def agent_dashboard_insights():
        """Insights AI generes"""
        agent = DashboardAgent()
        insights = agent.generate_insights()

        if 'error' in insights:
            return jsonify({'success': False, 'error': insights['error']}), 400

        return jsonify({'success': True, 'insights': insights})

    # ============================================
    # AGENT 53: LEAD SCORING - Qualification IA
    # ============================================

    @app.route('/api/agent/lead-scoring/init', methods=['POST'])
    def agent_lead_scoring_init():
        """Initialise les tables lead scoring"""
        agent = LeadScoringAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/lead-scoring/score', methods=['POST'])
    def agent_lead_scoring_score():
        """
        Score un lead
        Body: {contact_id, data: {source, engagement, budget, timeline, fit, ...}}
        """
        data = request.get_json() or {}
        agent = LeadScoringAgent()
        result = agent.score_lead(
            data.get('contact_id'),
            data.get('data')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/lead-scoring/score-ai/<int:contact_id>', methods=['POST'])
    def agent_lead_scoring_score_ai(contact_id):
        """Score un lead avec analyse IA complete"""
        agent = LeadScoringAgent()
        result = agent.score_lead_ai(contact_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/lead-scoring/batch', methods=['POST'])
    def agent_lead_scoring_batch():
        """Score tous les leads non scores"""
        data = request.get_json() or {}
        limit = int(data.get('limit', 50))

        agent = LeadScoringAgent()
        result = agent.batch_score(limit)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/lead-scoring/hot-leads', methods=['GET'])
    def agent_lead_scoring_hot_leads():
        """Liste les leads chauds"""
        min_score = int(request.args.get('min_score', 70))
        limit = int(request.args.get('limit', 20))

        agent = LeadScoringAgent()
        leads = agent.get_hot_leads(min_score, limit)

        if isinstance(leads, dict) and 'error' in leads:
            return jsonify({'success': False, 'error': leads['error']}), 400

        return jsonify({'success': True, 'leads': leads, 'count': len(leads)})

    @app.route('/api/agent/lead-scoring/history/<int:contact_id>', methods=['GET'])
    def agent_lead_scoring_history(contact_id):
        """Historique des scores d'un contact"""
        limit = int(request.args.get('limit', 10))

        agent = LeadScoringAgent()
        history = agent.get_score_history(contact_id, limit)

        if isinstance(history, dict) and 'error' in history:
            return jsonify({'success': False, 'error': history['error']}), 400

        return jsonify({'success': True, 'history': history})

    @app.route('/api/agent/lead-scoring/action', methods=['POST'])
    def agent_lead_scoring_create_action():
        """Cree une action pour un lead"""
        data = request.get_json() or {}
        agent = LeadScoringAgent()
        result = agent.create_action(
            data.get('contact_id'),
            data.get('action_type', 'call'),
            data.get('description', ''),
            data.get('priority', 3),
            data.get('due_date'),
            data.get('assigned_to')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/lead-scoring/actions', methods=['GET'])
    def agent_lead_scoring_pending_actions():
        """Actions en attente"""
        limit = int(request.args.get('limit', 50))

        agent = LeadScoringAgent()
        actions = agent.get_pending_actions(limit)

        if isinstance(actions, dict) and 'error' in actions:
            return jsonify({'success': False, 'error': actions['error']}), 400

        return jsonify({'success': True, 'actions': actions})

    @app.route('/api/agent/lead-scoring/action/<int:action_id>/complete', methods=['POST'])
    def agent_lead_scoring_complete_action(action_id):
        """Marque une action comme terminee"""
        agent = LeadScoringAgent()
        result = agent.complete_action(action_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/lead-scoring/stats', methods=['GET'])
    def agent_lead_scoring_stats():
        """Statistiques de scoring"""
        agent = LeadScoringAgent()
        stats = agent.get_stats()

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 54: EMAIL CAMPAIGN - Marketing Automation
    # ============================================

    @app.route('/api/agent/email-campaign/init', methods=['POST'])
    def agent_email_campaign_init():
        """Initialise les tables email campaign"""
        agent = EmailCampaignAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/email-campaign/campaign', methods=['POST'])
    def agent_email_campaign_create():
        """
        Cree une campagne email
        Body: {name, subject, content_html, content_text, segment_id, ab_test, send_at}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.create_campaign(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'campaign': result})

    @app.route('/api/agent/email-campaign/generate', methods=['POST'])
    def agent_email_campaign_generate():
        """
        Genere contenu email avec IA
        Body: {campaign_type, context}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.generate_email_ai(
            data.get('campaign_type', 'newsletter'),
            data.get('context', {})
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'email': result})

    @app.route('/api/agent/email-campaign/campaigns', methods=['GET'])
    def agent_email_campaign_list():
        """Liste les campagnes"""
        limit = int(request.args.get('limit', 50))
        agent = EmailCampaignAgent()
        campaigns = agent.get_campaigns(limit)

        if isinstance(campaigns, dict) and 'error' in campaigns:
            return jsonify({'success': False, 'error': campaigns['error']}), 400

        return jsonify({'success': True, 'campaigns': campaigns, 'count': len(campaigns)})

    @app.route('/api/agent/email-campaign/sequence', methods=['POST'])
    def agent_email_campaign_create_sequence():
        """
        Cree une sequence drip
        Body: {name, trigger_type}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.create_sequence(
            data.get('name', 'New Sequence'),
            data.get('trigger_type', 'signup')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'sequence': result})

    @app.route('/api/agent/email-campaign/sequence/<int:sequence_id>/step', methods=['POST'])
    def agent_email_campaign_add_step(sequence_id):
        """
        Ajoute une etape a une sequence
        Body: {subject, content_html, delay_days, content_text}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.add_sequence_step(
            sequence_id,
            data.get('subject', ''),
            data.get('content_html', ''),
            int(data.get('delay_days', 1)),
            data.get('content_text')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'step': result})

    @app.route('/api/agent/email-campaign/sequences', methods=['GET'])
    def agent_email_campaign_list_sequences():
        """Liste les sequences"""
        limit = int(request.args.get('limit', 50))
        agent = EmailCampaignAgent()
        sequences = agent.get_sequences(limit)

        if isinstance(sequences, dict) and 'error' in sequences:
            return jsonify({'success': False, 'error': sequences['error']}), 400

        return jsonify({'success': True, 'sequences': sequences})

    @app.route('/api/agent/email-campaign/enroll', methods=['POST'])
    def agent_email_campaign_enroll():
        """
        Inscrit un contact dans une sequence
        Body: {sequence_id, contact_id}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.enroll_contact(
            int(data.get('sequence_id')),
            int(data.get('contact_id'))
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'enrollment': result})

    @app.route('/api/agent/email-campaign/segment', methods=['POST'])
    def agent_email_campaign_create_segment():
        """
        Cree un segment
        Body: {name, conditions: {source, status, min_score, tags}}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.create_segment(
            data.get('name', 'New Segment'),
            data.get('conditions', {})
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'segment': result})

    @app.route('/api/agent/email-campaign/unsubscribe', methods=['POST'])
    def agent_email_campaign_unsubscribe():
        """
        Desinscrit un email
        Body: {email, reason}
        """
        data = request.get_json() or {}
        agent = EmailCampaignAgent()
        result = agent.unsubscribe(
            data.get('email'),
            data.get('reason')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/email-campaign/stats', methods=['GET'])
    def agent_email_campaign_stats():
        """Statistiques email marketing"""
        days = int(request.args.get('days', 30))
        agent = EmailCampaignAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 55: SUPPORT TICKET - Helpdesk
    # ============================================

    @app.route('/api/agent/support/init', methods=['POST'])
    def agent_support_init():
        """Initialise les tables support"""
        agent = SupportTicketAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/support/ticket', methods=['POST'])
    def agent_support_create_ticket():
        """
        Cree un ticket
        Body: {email, name, subject, description, category, priority, channel, tags}
        """
        data = request.get_json() or {}
        agent = SupportTicketAgent()
        result = agent.create_ticket(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'ticket': result})

    @app.route('/api/agent/support/ticket/<int:ticket_id>', methods=['GET'])
    def agent_support_get_ticket(ticket_id):
        """Recupere un ticket avec messages"""
        agent = SupportTicketAgent()
        ticket = agent.get_ticket(ticket_id)

        if 'error' in ticket:
            return jsonify({'success': False, 'error': ticket['error']}), 404

        return jsonify({'success': True, 'ticket': ticket})

    @app.route('/api/agent/support/ticket/<int:ticket_id>', methods=['PUT'])
    def agent_support_update_ticket(ticket_id):
        """
        Met a jour un ticket
        Body: {status, priority, category, assigned_to, tags}
        """
        data = request.get_json() or {}
        agent = SupportTicketAgent()
        result = agent.update_ticket(ticket_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/support/ticket/<int:ticket_id>/reply', methods=['POST'])
    def agent_support_reply_ticket(ticket_id):
        """
        Repond a un ticket
        Body: {message, sender_type, sender_name, is_internal}
        """
        data = request.get_json() or {}
        agent = SupportTicketAgent()
        result = agent.reply_ticket(
            ticket_id,
            data.get('message', ''),
            data.get('sender_type', 'agent'),
            data.get('sender_name', 'Support'),
            data.get('is_internal', False)
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/support/ticket/<int:ticket_id>/ai-response', methods=['POST'])
    def agent_support_ai_response(ticket_id):
        """Genere reponse IA pour un ticket"""
        agent = SupportTicketAgent()
        result = agent.generate_response_ai(ticket_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'response': result['response']})

    @app.route('/api/agent/support/ticket/<int:ticket_id>/rate', methods=['POST'])
    def agent_support_rate_ticket(ticket_id):
        """
        Note satisfaction
        Body: {score (1-5), feedback}
        """
        data = request.get_json() or {}
        agent = SupportTicketAgent()
        result = agent.rate_ticket(ticket_id, int(data.get('score', 5)), data.get('feedback'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/support/tickets', methods=['GET'])
    def agent_support_list_tickets():
        """
        Liste les tickets
        Query: ?status=open&priority=high&category=technical&assigned_to=agent1&limit=50
        """
        filters = {
            'status': request.args.get('status'),
            'priority': request.args.get('priority'),
            'category': request.args.get('category'),
            'assigned_to': request.args.get('assigned_to')
        }
        filters = {k: v for k, v in filters.items() if v}
        limit = int(request.args.get('limit', 50))

        agent = SupportTicketAgent()
        tickets = agent.get_tickets(filters if filters else None, limit)

        if isinstance(tickets, dict) and 'error' in tickets:
            return jsonify({'success': False, 'error': tickets['error']}), 400

        return jsonify({'success': True, 'tickets': tickets, 'count': len(tickets)})

    @app.route('/api/agent/support/overdue', methods=['GET'])
    def agent_support_overdue():
        """Tickets en retard SLA"""
        agent = SupportTicketAgent()
        tickets = agent.get_overdue_tickets()

        if isinstance(tickets, dict) and 'error' in tickets:
            return jsonify({'success': False, 'error': tickets['error']}), 400

        return jsonify({'success': True, 'tickets': tickets, 'count': len(tickets)})

    @app.route('/api/agent/support/canned-response', methods=['POST'])
    def agent_support_add_canned():
        """
        Ajoute reponse predefinie
        Body: {name, content, category, shortcut}
        """
        data = request.get_json() or {}
        agent = SupportTicketAgent()
        result = agent.add_canned_response(
            data.get('name', 'Reponse'),
            data.get('content', ''),
            data.get('category'),
            data.get('shortcut')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'response': result})

    @app.route('/api/agent/support/canned-responses', methods=['GET'])
    def agent_support_list_canned():
        """Liste reponses predefinies"""
        category = request.args.get('category')
        agent = SupportTicketAgent()
        responses = agent.get_canned_responses(category)

        if isinstance(responses, dict) and 'error' in responses:
            return jsonify({'success': False, 'error': responses['error']}), 400

        return jsonify({'success': True, 'responses': responses})

    @app.route('/api/agent/support/stats', methods=['GET'])
    def agent_support_stats():
        """Statistiques support"""
        days = int(request.args.get('days', 30))
        agent = SupportTicketAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 56: KNOWLEDGE BASE - FAQ & Documentation
    # ============================================

    @app.route('/api/agent/kb/init', methods=['POST'])
    def agent_kb_init():
        """Initialise les tables knowledge base"""
        agent = KnowledgeBaseAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/kb/article', methods=['POST'])
    def agent_kb_create_article():
        """
        Cree un article
        Body: {title, content, excerpt, category_id, author, status, tags, meta_title, meta_description}
        """
        data = request.get_json() or {}
        agent = KnowledgeBaseAgent()
        result = agent.create_article(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'article': result})

    @app.route('/api/agent/kb/article/generate', methods=['POST'])
    def agent_kb_generate_article():
        """
        Genere article avec IA
        Body: {topic, category}
        """
        data = request.get_json() or {}
        agent = KnowledgeBaseAgent()
        result = agent.generate_article_ai(data.get('topic', ''), data.get('category'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'article': result})

    @app.route('/api/agent/kb/article/<int:article_id>', methods=['GET'])
    def agent_kb_get_article(article_id):
        """Recupere un article par ID"""
        agent = KnowledgeBaseAgent()
        article = agent.get_article(article_id=article_id)

        if 'error' in article:
            return jsonify({'success': False, 'error': article['error']}), 404

        return jsonify({'success': True, 'article': article})

    @app.route('/api/agent/kb/article/slug/<slug>', methods=['GET'])
    def agent_kb_get_article_by_slug(slug):
        """Recupere un article par slug"""
        agent = KnowledgeBaseAgent()
        article = agent.get_article(slug=slug)

        if 'error' in article:
            return jsonify({'success': False, 'error': article['error']}), 404

        return jsonify({'success': True, 'article': article})

    @app.route('/api/agent/kb/article/<int:article_id>', methods=['PUT'])
    def agent_kb_update_article(article_id):
        """Met a jour un article"""
        data = request.get_json() or {}
        agent = KnowledgeBaseAgent()
        result = agent.update_article(article_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/kb/article/<int:article_id>/rate', methods=['POST'])
    def agent_kb_rate_article(article_id):
        """
        Note un article
        Body: {is_helpful (bool), comment, email}
        """
        data = request.get_json() or {}
        agent = KnowledgeBaseAgent()
        result = agent.rate_article(article_id, data.get('is_helpful', True), data.get('comment'), data.get('email'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/kb/articles', methods=['GET'])
    def agent_kb_list_articles():
        """
        Liste les articles
        Query: ?category_id=1&status=published&limit=50
        """
        category_id = request.args.get('category_id')
        status = request.args.get('status', 'published')
        limit = int(request.args.get('limit', 50))

        agent = KnowledgeBaseAgent()
        articles = agent.get_articles(int(category_id) if category_id else None, status, limit)

        if isinstance(articles, dict) and 'error' in articles:
            return jsonify({'success': False, 'error': articles['error']}), 400

        return jsonify({'success': True, 'articles': articles, 'count': len(articles)})

    @app.route('/api/agent/kb/search', methods=['GET'])
    def agent_kb_search():
        """
        Recherche articles
        Query: ?q=recherche&limit=20
        """
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))

        agent = KnowledgeBaseAgent()
        results = agent.search_articles(query, limit)

        if isinstance(results, dict) and 'error' in results:
            return jsonify({'success': False, 'error': results['error']}), 400

        return jsonify({'success': True, 'results': results, 'count': len(results)})

    @app.route('/api/agent/kb/ask', methods=['POST'])
    def agent_kb_ask():
        """
        Pose une question, IA repond avec KB
        Body: {question}
        """
        data = request.get_json() or {}
        agent = KnowledgeBaseAgent()
        result = agent.answer_question_ai(data.get('question', ''))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'answer': result['answer'], 'sources': result.get('sources', [])})

    @app.route('/api/agent/kb/faq', methods=['POST'])
    def agent_kb_add_faq():
        """
        Ajoute une FAQ
        Body: {question, answer, category_id}
        """
        data = request.get_json() or {}
        agent = KnowledgeBaseAgent()
        result = agent.add_faq(data.get('question', ''), data.get('answer', ''), data.get('category_id'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'faq': result})

    @app.route('/api/agent/kb/faqs', methods=['GET'])
    def agent_kb_list_faqs():
        """
        Liste les FAQ
        Query: ?category_id=1&limit=50
        """
        category_id = request.args.get('category_id')
        limit = int(request.args.get('limit', 50))

        agent = KnowledgeBaseAgent()
        faqs = agent.get_faqs(int(category_id) if category_id else None, limit)

        if isinstance(faqs, dict) and 'error' in faqs:
            return jsonify({'success': False, 'error': faqs['error']}), 400

        return jsonify({'success': True, 'faqs': faqs})

    @app.route('/api/agent/kb/categories', methods=['GET'])
    def agent_kb_categories():
        """Liste les categories"""
        agent = KnowledgeBaseAgent()
        categories = agent.get_categories()

        if isinstance(categories, dict) and 'error' in categories:
            return jsonify({'success': False, 'error': categories['error']}), 400

        return jsonify({'success': True, 'categories': categories})

    @app.route('/api/agent/kb/popular', methods=['GET'])
    def agent_kb_popular():
        """Articles populaires"""
        limit = int(request.args.get('limit', 10))
        agent = KnowledgeBaseAgent()
        articles = agent.get_popular_articles(limit)

        if isinstance(articles, dict) and 'error' in articles:
            return jsonify({'success': False, 'error': articles['error']}), 400

        return jsonify({'success': True, 'articles': articles})

    @app.route('/api/agent/kb/stats', methods=['GET'])
    def agent_kb_stats():
        """Statistiques knowledge base"""
        agent = KnowledgeBaseAgent()
        stats = agent.get_stats()

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 57: SURVEY - Sondages & Feedback
    # ============================================

    @app.route('/api/agent/survey/init', methods=['POST'])
    def agent_survey_init():
        """Initialise les tables survey"""
        agent = SurveyAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/survey/create', methods=['POST'])
    def agent_survey_create():
        """
        Cree un sondage
        Body: {name, description, type, status, is_anonymous, thank_you_message}
        """
        data = request.get_json() or {}
        agent = SurveyAgent()
        result = agent.create_survey(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'survey': result})

    @app.route('/api/agent/survey/nps', methods=['POST'])
    def agent_survey_create_nps():
        """Cree un sondage NPS predifini"""
        data = request.get_json() or {}
        agent = SurveyAgent()
        result = agent.create_nps_survey(data.get('name', 'Enquete NPS'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'survey': result})

    @app.route('/api/agent/survey/csat', methods=['POST'])
    def agent_survey_create_csat():
        """Cree un sondage CSAT predifini"""
        data = request.get_json() or {}
        agent = SurveyAgent()
        result = agent.create_csat_survey(data.get('name', 'Satisfaction Client'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'survey': result})

    @app.route('/api/agent/survey/<int:survey_id>/question', methods=['POST'])
    def agent_survey_add_question(survey_id):
        """
        Ajoute une question
        Body: {question_type, question_text, description, options, is_required, settings}
        """
        data = request.get_json() or {}
        agent = SurveyAgent()
        result = agent.add_question(survey_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'question': result})

    @app.route('/api/agent/survey/<int:survey_id>', methods=['GET'])
    def agent_survey_get(survey_id):
        """Recupere un sondage avec questions"""
        agent = SurveyAgent()
        survey = agent.get_survey(survey_id)

        if 'error' in survey:
            return jsonify({'success': False, 'error': survey['error']}), 404

        return jsonify({'success': True, 'survey': survey})

    @app.route('/api/agent/survey/<int:survey_id>/respond', methods=['POST'])
    def agent_survey_respond(survey_id):
        """
        Soumet une reponse
        Body: {answers: {question_id: answer, ...}, contact_info: {email, contact_id}}
        """
        data = request.get_json() or {}
        agent = SurveyAgent()
        result = agent.submit_response(survey_id, data.get('answers', {}), data.get('contact_info'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'response': result})

    @app.route('/api/agent/survey/<int:survey_id>/responses', methods=['GET'])
    def agent_survey_responses(survey_id):
        """Liste les reponses d'un sondage"""
        limit = int(request.args.get('limit', 100))
        agent = SurveyAgent()
        responses = agent.get_responses(survey_id, limit)

        if isinstance(responses, dict) and 'error' in responses:
            return jsonify({'success': False, 'error': responses['error']}), 400

        return jsonify({'success': True, 'responses': responses, 'count': len(responses)})

    @app.route('/api/agent/survey/<int:survey_id>/analyze', methods=['POST'])
    def agent_survey_analyze(survey_id):
        """Analyse les feedbacks avec IA"""
        agent = SurveyAgent()
        result = agent.analyze_feedback_ai(survey_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'analysis': result})

    @app.route('/api/agent/survey/surveys', methods=['GET'])
    def agent_survey_list():
        """
        Liste les sondages
        Query: ?status=active&limit=50
        """
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))

        agent = SurveyAgent()
        surveys = agent.get_surveys(status, limit)

        if isinstance(surveys, dict) and 'error' in surveys:
            return jsonify({'success': False, 'error': surveys['error']}), 400

        return jsonify({'success': True, 'surveys': surveys})

    @app.route('/api/agent/survey/nps/record', methods=['POST'])
    def agent_survey_record_nps():
        """
        Enregistre un score NPS
        Body: {score, email, contact_id, feedback, source}
        """
        data = request.get_json() or {}
        agent = SurveyAgent()
        result = agent.record_nps(
            int(data.get('score', 0)),
            data.get('email'),
            data.get('contact_id'),
            data.get('feedback'),
            data.get('source', 'api')
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/survey/nps/score', methods=['GET'])
    def agent_survey_nps_score():
        """
        Calcule le score NPS
        Query: ?days=90
        """
        days = int(request.args.get('days', 90))
        agent = SurveyAgent()
        result = agent.get_nps_score(days)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'nps': result})

    @app.route('/api/agent/survey/stats', methods=['GET'])
    def agent_survey_stats():
        """Statistiques sondages"""
        days = int(request.args.get('days', 30))
        agent = SurveyAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 58: WEBHOOK - Integrations
    # ============================================

    @app.route('/api/agent/webhook/init', methods=['POST'])
    def agent_webhook_init():
        """Initialise les tables webhook"""
        agent = WebhookAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/webhook/outgoing', methods=['POST'])
    def agent_webhook_create_outgoing():
        """
        Cree un webhook sortant
        Body: {name, url, event_type, method, headers, retry_count, timeout_seconds}
        """
        data = request.get_json() or {}
        agent = WebhookAgent()
        result = agent.create_outgoing_webhook(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'webhook': result})

    @app.route('/api/agent/webhook/incoming', methods=['POST'])
    def agent_webhook_create_incoming():
        """
        Cree un webhook entrant (endpoint)
        Body: {name, description, action_type, action_config, require_signature, allowed_ips}
        """
        data = request.get_json() or {}
        agent = WebhookAgent()
        result = agent.create_incoming_webhook(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'webhook': result})

    @app.route('/api/agent/webhook/trigger', methods=['POST'])
    def agent_webhook_trigger():
        """
        Declenche les webhooks pour un evenement
        Body: {event_type, payload}
        """
        data = request.get_json() or {}
        agent = WebhookAgent()
        result = agent.trigger_webhook(data.get('event_type', 'test'), data.get('payload', {}))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/webhook/receive/<endpoint_key>', methods=['POST'])
    def agent_webhook_receive(endpoint_key):
        """Recoit un webhook entrant"""
        payload = request.get_json() or {}
        headers = dict(request.headers)
        ip = request.remote_addr

        agent = WebhookAgent()
        result = agent.receive_webhook(endpoint_key, payload, headers, ip)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), result.get('code', 400)

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/webhook/outgoing/list', methods=['GET'])
    def agent_webhook_list_outgoing():
        """Liste les webhooks sortants"""
        is_active = request.args.get('active')
        limit = int(request.args.get('limit', 50))

        agent = WebhookAgent()
        webhooks = agent.get_webhooks('outgoing', bool(int(is_active)) if is_active else None, limit)

        if isinstance(webhooks, dict) and 'error' in webhooks:
            return jsonify({'success': False, 'error': webhooks['error']}), 400

        return jsonify({'success': True, 'webhooks': webhooks})

    @app.route('/api/agent/webhook/incoming/list', methods=['GET'])
    def agent_webhook_list_incoming():
        """Liste les webhooks entrants"""
        is_active = request.args.get('active')
        limit = int(request.args.get('limit', 50))

        agent = WebhookAgent()
        webhooks = agent.get_webhooks('incoming', bool(int(is_active)) if is_active else None, limit)

        if isinstance(webhooks, dict) and 'error' in webhooks:
            return jsonify({'success': False, 'error': webhooks['error']}), 400

        return jsonify({'success': True, 'webhooks': webhooks})

    @app.route('/api/agent/webhook/logs', methods=['GET'])
    def agent_webhook_logs():
        """
        Liste les logs
        Query: ?webhook_id=1&direction=outgoing&limit=100
        """
        webhook_id = request.args.get('webhook_id')
        direction = request.args.get('direction')
        limit = int(request.args.get('limit', 100))

        agent = WebhookAgent()
        logs = agent.get_logs(int(webhook_id) if webhook_id else None, direction, limit)

        if isinstance(logs, dict) and 'error' in logs:
            return jsonify({'success': False, 'error': logs['error']}), 400

        return jsonify({'success': True, 'logs': logs})

    @app.route('/api/agent/webhook/<int:webhook_id>/toggle', methods=['POST'])
    def agent_webhook_toggle(webhook_id):
        """
        Active/desactive un webhook
        Body: {direction, is_active}
        """
        data = request.get_json() or {}
        agent = WebhookAgent()
        result = agent.toggle_webhook(webhook_id, data.get('direction', 'outgoing'), data.get('is_active', True))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/webhook/<int:webhook_id>', methods=['DELETE'])
    def agent_webhook_delete(webhook_id):
        """Supprime un webhook"""
        direction = request.args.get('direction', 'outgoing')
        agent = WebhookAgent()
        result = agent.delete_webhook(webhook_id, direction)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/webhook/events', methods=['GET'])
    def agent_webhook_events():
        """Liste des types d'evenements"""
        agent = WebhookAgent()
        return jsonify({'success': True, 'events': agent.get_event_types()})

    @app.route('/api/agent/webhook/stats', methods=['GET'])
    def agent_webhook_stats():
        """Statistiques webhooks"""
        days = int(request.args.get('days', 30))
        agent = WebhookAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 59: AUTOMATION - Workflows
    # ============================================

    @app.route('/api/agent/automation/init', methods=['POST'])
    def agent_automation_init():
        """Initialise les tables automation"""
        agent = AutomationAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/automation/create', methods=['POST'])
    def agent_automation_create():
        """
        Cree une automation
        Body: {name, description, trigger_type, trigger_config, is_active}
        """
        data = request.get_json() or {}
        agent = AutomationAgent()
        result = agent.create_automation(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'automation': result})

    @app.route('/api/agent/automation/<int:automation_id>/action', methods=['POST'])
    def agent_automation_add_action(automation_id):
        """
        Ajoute une action
        Body: {action_type, action_config, delay_minutes, condition}
        """
        data = request.get_json() or {}
        agent = AutomationAgent()
        result = agent.add_action(automation_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'action': result})

    @app.route('/api/agent/automation/template/<template_name>', methods=['POST'])
    def agent_automation_template(template_name):
        """Cree une automation depuis un template"""
        agent = AutomationAgent()
        result = agent.create_workflow_template(template_name)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'automation': result})

    @app.route('/api/agent/automation/trigger', methods=['POST'])
    def agent_automation_trigger():
        """
        Declenche les automations
        Body: {trigger_type, trigger_data}
        """
        data = request.get_json() or {}
        agent = AutomationAgent()
        result = agent.trigger_automation(data.get('trigger_type', 'manual'), data.get('trigger_data', {}))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/automation/<int:automation_id>', methods=['GET'])
    def agent_automation_get(automation_id):
        """Recupere une automation avec actions"""
        agent = AutomationAgent()
        automation = agent.get_automation(automation_id)

        if 'error' in automation:
            return jsonify({'success': False, 'error': automation['error']}), 404

        return jsonify({'success': True, 'automation': automation})

    @app.route('/api/agent/automation/list', methods=['GET'])
    def agent_automation_list():
        """Liste les automations"""
        is_active = request.args.get('active')
        limit = int(request.args.get('limit', 50))

        agent = AutomationAgent()
        automations = agent.get_automations(bool(int(is_active)) if is_active else None, limit)

        if isinstance(automations, dict) and 'error' in automations:
            return jsonify({'success': False, 'error': automations['error']}), 400

        return jsonify({'success': True, 'automations': automations})

    @app.route('/api/agent/automation/<int:automation_id>/toggle', methods=['POST'])
    def agent_automation_toggle(automation_id):
        """Active/desactive une automation"""
        data = request.get_json() or {}
        agent = AutomationAgent()
        result = agent.toggle_automation(automation_id, data.get('is_active', True))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/automation/<int:automation_id>', methods=['DELETE'])
    def agent_automation_delete(automation_id):
        """Supprime une automation"""
        agent = AutomationAgent()
        result = agent.delete_automation(automation_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True})

    @app.route('/api/agent/automation/logs', methods=['GET'])
    def agent_automation_logs():
        """Liste les logs"""
        automation_id = request.args.get('automation_id')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))

        agent = AutomationAgent()
        logs = agent.get_logs(int(automation_id) if automation_id else None, status, limit)

        if isinstance(logs, dict) and 'error' in logs:
            return jsonify({'success': False, 'error': logs['error']}), 400

        return jsonify({'success': True, 'logs': logs})

    @app.route('/api/agent/automation/triggers', methods=['GET'])
    def agent_automation_triggers():
        """Liste des types de triggers"""
        agent = AutomationAgent()
        return jsonify({'success': True, 'triggers': agent.get_trigger_types()})

    @app.route('/api/agent/automation/actions', methods=['GET'])
    def agent_automation_actions():
        """Liste des types d'actions"""
        agent = AutomationAgent()
        return jsonify({'success': True, 'actions': agent.get_action_types()})

    @app.route('/api/agent/automation/stats', methods=['GET'])
    def agent_automation_stats():
        """Statistiques automations"""
        days = int(request.args.get('days', 30))
        agent = AutomationAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 60: AFFILIATE - Programme Affiliation
    # ============================================

    @app.route('/api/agent/affiliate/init', methods=['POST'])
    def agent_affiliate_init():
        """Initialise les tables affiliation"""
        agent = AffiliateAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/register', methods=['POST'])
    def agent_affiliate_register():
        """
        Inscription d'un affilie
        Body: {name, email, phone, company, website, payment_method, payment_details, notes}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.register_affiliate(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'affiliate': result})

    @app.route('/api/agent/affiliate/<int:affiliate_id>/approve', methods=['POST'])
    def agent_affiliate_approve(affiliate_id):
        """
        Approuve un affilie
        Body: {commission_rate, tier}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.approve_affiliate(affiliate_id, data.get('commission_rate'), data.get('tier', 'standard'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/click/<referral_code>', methods=['POST'])
    def agent_affiliate_track_click(referral_code):
        """
        Enregistre un clic sur lien affilie
        Body: {ip, user_agent, page, referer, source}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.track_click(referral_code, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/conversion/<referral_code>', methods=['POST'])
    def agent_affiliate_conversion(referral_code):
        """
        Enregistre une conversion
        Body: {customer_email, customer_name, order_id, amount}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.record_conversion(referral_code, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/<int:affiliate_id>', methods=['GET'])
    def agent_affiliate_get(affiliate_id):
        """Recupere un affilie"""
        agent = AffiliateAgent()
        affiliate = agent.get_affiliate(affiliate_id)

        if 'error' in affiliate:
            return jsonify({'success': False, 'error': affiliate['error']}), 404

        return jsonify({'success': True, 'affiliate': affiliate})

    @app.route('/api/agent/affiliate/list', methods=['GET'])
    def agent_affiliate_list():
        """
        Liste les affilies
        Query: ?status=active&tier=gold&limit=50
        """
        status = request.args.get('status')
        tier = request.args.get('tier')
        limit = int(request.args.get('limit', 50))

        agent = AffiliateAgent()
        affiliates = agent.get_affiliates(status, tier, limit)

        if isinstance(affiliates, dict) and 'error' in affiliates:
            return jsonify({'success': False, 'error': affiliates['error']}), 400

        return jsonify({'success': True, 'affiliates': affiliates, 'count': len(affiliates)})

    @app.route('/api/agent/affiliate/referrals', methods=['GET'])
    def agent_affiliate_referrals():
        """
        Liste les referrals
        Query: ?affiliate_id=1&converted=1&limit=100
        """
        affiliate_id = request.args.get('affiliate_id')
        converted = request.args.get('converted')
        limit = int(request.args.get('limit', 100))

        agent = AffiliateAgent()
        referrals = agent.get_referrals(
            int(affiliate_id) if affiliate_id else None,
            bool(int(converted)) if converted else None,
            limit
        )

        if isinstance(referrals, dict) and 'error' in referrals:
            return jsonify({'success': False, 'error': referrals['error']}), 400

        return jsonify({'success': True, 'referrals': referrals})

    @app.route('/api/agent/affiliate/<int:affiliate_id>/payout', methods=['POST'])
    def agent_affiliate_request_payout(affiliate_id):
        """
        Demande de paiement
        Body: {amount}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.request_payout(affiliate_id, data.get('amount'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'payout': result})

    @app.route('/api/agent/affiliate/payout/<int:payout_id>/process', methods=['POST'])
    def agent_affiliate_process_payout(payout_id):
        """
        Traite un paiement
        Body: {payment_reference}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.process_payout(payout_id, data.get('payment_reference'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/payouts', methods=['GET'])
    def agent_affiliate_payouts():
        """
        Liste les paiements
        Query: ?affiliate_id=1&status=pending&limit=50
        """
        affiliate_id = request.args.get('affiliate_id')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))

        agent = AffiliateAgent()
        payouts = agent.get_payouts(int(affiliate_id) if affiliate_id else None, status, limit)

        if isinstance(payouts, dict) and 'error' in payouts:
            return jsonify({'success': False, 'error': payouts['error']}), 400

        return jsonify({'success': True, 'payouts': payouts})

    @app.route('/api/agent/affiliate/tier', methods=['POST'])
    def agent_affiliate_create_tier():
        """
        Cree un palier de commission
        Body: {name, min_sales, commission_rate, bonus_rate, description, benefits}
        """
        data = request.get_json() or {}
        agent = AffiliateAgent()
        result = agent.create_tier(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'tier': result})

    @app.route('/api/agent/affiliate/tiers', methods=['GET'])
    def agent_affiliate_list_tiers():
        """Liste les paliers"""
        agent = AffiliateAgent()
        tiers = agent.get_tiers()

        if isinstance(tiers, dict) and 'error' in tiers:
            return jsonify({'success': False, 'error': tiers['error']}), 400

        return jsonify({'success': True, 'tiers': tiers})

    @app.route('/api/agent/affiliate/tiers/setup', methods=['POST'])
    def agent_affiliate_setup_tiers():
        """Configure les paliers par defaut (Bronze, Silver, Gold, Platinum)"""
        agent = AffiliateAgent()
        result = agent.setup_default_tiers()

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/<int:affiliate_id>/update-tier', methods=['POST'])
    def agent_affiliate_update_tier(affiliate_id):
        """Met a jour le palier selon les ventes"""
        agent = AffiliateAgent()
        result = agent.update_affiliate_tier(affiliate_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/affiliate/<int:affiliate_id>/dashboard', methods=['GET'])
    def agent_affiliate_dashboard(affiliate_id):
        """Dashboard affilie avec stats"""
        agent = AffiliateAgent()
        dashboard = agent.get_affiliate_dashboard(affiliate_id)

        if 'error' in dashboard:
            return jsonify({'success': False, 'error': dashboard['error']}), 400

        return jsonify({'success': True, 'dashboard': dashboard})

    @app.route('/api/agent/affiliate/stats', methods=['GET'])
    def agent_affiliate_stats():
        """Statistiques globales programme affiliation"""
        days = int(request.args.get('days', 30))
        agent = AffiliateAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    # ============================================
    # AGENT 61: LOYALTY - Programme Fidelite
    # ============================================

    @app.route('/api/agent/loyalty/init', methods=['POST'])
    def agent_loyalty_init():
        """Initialise les tables fidelite"""
        agent = LoyaltyAgent()
        result = agent.init_db()
        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/loyalty/enroll', methods=['POST'])
    def agent_loyalty_enroll():
        """
        Inscrit un nouveau membre
        Body: {email, name, phone, customer_id, birthday, referral_code}
        """
        data = request.get_json() or {}
        agent = LoyaltyAgent()
        result = agent.enroll_member(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'member': result})

    @app.route('/api/agent/loyalty/<int:member_id>/earn', methods=['POST'])
    def agent_loyalty_earn_points(member_id):
        """
        Ajoute des points pour un achat
        Body: {amount, order_id}
        """
        data = request.get_json() or {}
        agent = LoyaltyAgent()
        result = agent.earn_points(member_id, data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/loyalty/<int:member_id>/redeem/<int:reward_id>', methods=['POST'])
    def agent_loyalty_redeem(member_id, reward_id):
        """Echange points contre recompense"""
        agent = LoyaltyAgent()
        result = agent.redeem_reward(member_id, reward_id)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'redemption': result})

    @app.route('/api/agent/loyalty/use/<redemption_code>', methods=['POST'])
    def agent_loyalty_use_redemption(redemption_code):
        """Utilise un code d'echange"""
        agent = LoyaltyAgent()
        result = agent.use_redemption(redemption_code)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/loyalty/member/<int:member_id>', methods=['GET'])
    def agent_loyalty_get_member(member_id):
        """Recupere un membre par ID"""
        agent = LoyaltyAgent()
        member = agent.get_member(member_id=member_id)

        if 'error' in member:
            return jsonify({'success': False, 'error': member['error']}), 404

        return jsonify({'success': True, 'member': member})

    @app.route('/api/agent/loyalty/member/email/<email>', methods=['GET'])
    def agent_loyalty_get_member_by_email(email):
        """Recupere un membre par email"""
        agent = LoyaltyAgent()
        member = agent.get_member(email=email)

        if 'error' in member:
            return jsonify({'success': False, 'error': member['error']}), 404

        return jsonify({'success': True, 'member': member})

    @app.route('/api/agent/loyalty/members', methods=['GET'])
    def agent_loyalty_list_members():
        """
        Liste les membres
        Query: ?tier=gold&status=active&limit=50
        """
        tier = request.args.get('tier')
        status = request.args.get('status', 'active')
        limit = int(request.args.get('limit', 50))

        agent = LoyaltyAgent()
        members = agent.get_members(tier, status, limit)

        if isinstance(members, dict) and 'error' in members:
            return jsonify({'success': False, 'error': members['error']}), 400

        return jsonify({'success': True, 'members': members, 'count': len(members)})

    @app.route('/api/agent/loyalty/<int:member_id>/transactions', methods=['GET'])
    def agent_loyalty_transactions(member_id):
        """
        Liste les transactions d'un membre
        Query: ?type=earn&limit=50
        """
        trans_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))

        agent = LoyaltyAgent()
        transactions = agent.get_transactions(member_id, trans_type, limit)

        if isinstance(transactions, dict) and 'error' in transactions:
            return jsonify({'success': False, 'error': transactions['error']}), 400

        return jsonify({'success': True, 'transactions': transactions})

    @app.route('/api/agent/loyalty/reward', methods=['POST'])
    def agent_loyalty_create_reward():
        """
        Cree une recompense
        Body: {name, description, points_cost, type, value, code, stock, tier_required}
        """
        data = request.get_json() or {}
        agent = LoyaltyAgent()
        result = agent.create_reward(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'reward': result})

    @app.route('/api/agent/loyalty/rewards', methods=['GET'])
    def agent_loyalty_list_rewards():
        """
        Liste les recompenses
        Query: ?active=1&tier=silver
        """
        active = request.args.get('active')
        tier = request.args.get('tier')

        agent = LoyaltyAgent()
        is_active = bool(int(active)) if active else True
        rewards = agent.get_rewards(is_active, tier)

        if isinstance(rewards, dict) and 'error' in rewards:
            return jsonify({'success': False, 'error': rewards['error']}), 400

        return jsonify({'success': True, 'rewards': rewards})

    @app.route('/api/agent/loyalty/tier', methods=['POST'])
    def agent_loyalty_create_tier():
        """
        Cree un niveau de fidelite
        Body: {name, min_points, multiplier, benefits, color}
        """
        data = request.get_json() or {}
        agent = LoyaltyAgent()
        result = agent.create_tier(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'tier': result})

    @app.route('/api/agent/loyalty/tiers', methods=['GET'])
    def agent_loyalty_list_tiers():
        """Liste les niveaux"""
        agent = LoyaltyAgent()
        tiers = agent.get_tiers()

        if isinstance(tiers, dict) and 'error' in tiers:
            return jsonify({'success': False, 'error': tiers['error']}), 400

        return jsonify({'success': True, 'tiers': tiers})

    @app.route('/api/agent/loyalty/tiers/setup', methods=['POST'])
    def agent_loyalty_setup_tiers():
        """Configure les niveaux par defaut (Bronze, Silver, Gold, Platinum, Diamond)"""
        agent = LoyaltyAgent()
        result = agent.setup_default_tiers()

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/loyalty/rewards/setup', methods=['POST'])
    def agent_loyalty_setup_rewards():
        """Configure les recompenses par defaut"""
        agent = LoyaltyAgent()
        result = agent.setup_default_rewards()

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/loyalty/promotion', methods=['POST'])
    def agent_loyalty_create_promotion():
        """
        Cree une promotion bonus points
        Body: {name, description, type, value, conditions, valid_from, valid_until}
        """
        data = request.get_json() or {}
        agent = LoyaltyAgent()
        result = agent.create_promotion(data)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'promotion': result})

    @app.route('/api/agent/loyalty/promotions', methods=['GET'])
    def agent_loyalty_list_promotions():
        """Liste les promotions"""
        active = request.args.get('active', '1')

        agent = LoyaltyAgent()
        promotions = agent.get_promotions(bool(int(active)))

        if isinstance(promotions, dict) and 'error' in promotions:
            return jsonify({'success': False, 'error': promotions['error']}), 400

        return jsonify({'success': True, 'promotions': promotions})

    @app.route('/api/agent/loyalty/<int:member_id>/dashboard', methods=['GET'])
    def agent_loyalty_member_dashboard(member_id):
        """Dashboard membre avec stats"""
        agent = LoyaltyAgent()
        dashboard = agent.get_member_dashboard(member_id)

        if 'error' in dashboard:
            return jsonify({'success': False, 'error': dashboard['error']}), 400

        return jsonify({'success': True, 'dashboard': dashboard})

    @app.route('/api/agent/loyalty/<int:member_id>/adjust', methods=['POST'])
    def agent_loyalty_adjust_points(member_id):
        """
        Ajuste les points manuellement
        Body: {points, reason}
        """
        data = request.get_json() or {}
        agent = LoyaltyAgent()
        result = agent.adjust_points(member_id, data.get('points', 0), data.get('reason', 'Ajustement manuel'))

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({'success': True, 'result': result})

    @app.route('/api/agent/loyalty/stats', methods=['GET'])
    def agent_loyalty_stats():
        """Statistiques programme fidelite"""
        days = int(request.args.get('days', 30))
        agent = LoyaltyAgent()
        stats = agent.get_stats(days)

        if 'error' in stats:
            return jsonify({'success': False, 'error': stats['error']}), 400

        return jsonify({'success': True, 'stats': stats})

    print(f"[API] Registered {61} agent routes (including Business Agents)")

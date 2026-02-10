#!/usr/bin/env python3
"""
Comprehensive test of all SEO agents.
Tests ONE method per agent (simplest/most reliable).
Saves results to /opt/seo-agent/logs/test_62_agents.json
"""

import json
import time
import traceback
import sys
import os

sys.path.insert(0, '/opt/seo-agent/agents')
os.chdir('/opt/seo-agent/agents')

results = []
passed = 0
failed = 0

def test_agent(agent_name, init_fn, test_fn, test_method_name):
    global passed, failed
    print(f'[{len(results)+1:02d}] Testing {agent_name}.{test_method_name}()...', end=' ', flush=True)
    start = time.time()
    try:
        instance = init_fn()
        result = test_fn(instance)
        elapsed = round(time.time() - start, 3)
        status = 'OK'
        error = None
        passed += 1
        # Truncate result for JSON if too large
        result_str = str(result)
        if len(result_str) > 500:
            result_str = result_str[:500] + '...[truncated]'
        print(f'OK ({elapsed}s)')
    except Exception as e:
        elapsed = round(time.time() - start, 3)
        status = 'FAIL'
        error = f'{type(e).__name__}: {str(e)}'
        result_str = None
        failed += 1
        print(f'FAIL ({elapsed}s) - {error}')

    results.append({
        'agent': agent_name,
        'method': test_method_name,
        'status': status,
        'elapsed_seconds': elapsed,
        'error': error,
        'result_preview': result_str
    })

# ============================================================
# Import all agents
# ============================================================
print('='*70)
print('IMPORTING AGENTS...')
print('='*70)

from agents_system import (
    AccountingAgent, AffiliateAgent, AnalyticsAgent, AutomationAgent,
    BacklinkAnalysisAgent, BacklinkMonitorAgent, BackupAgent, BlogIdeaAgent,
    CRMAgent, CalendarAgent, ChatbotAgent, ClientOnboardingAgent,
    CompetitorAnalysisAgent, CompetitorWatchAgent, ContentBriefAgent,
    ContentCalendarAgent, ContentGenerationAgent, ContentOptimizationAgent,
    ContentSchedulerAgent, ConversionOptimizationAgent, DashboardAgent,
    DirectoryAgent, EmailCampaignAgent, EmailMarketingAgent,
    FAQGenerationAgent, ForumAgent, GuestPostAgent, ImageOptimizationAgent,
    InternalLinkingAgent, InvoiceAgent, KeywordGapAgent, KeywordResearchAgent,
    KnowledgeBaseAgent, LandingPageAgent, LeadScoringAgent, LocalSEOAgent,
    LoyaltyAgent, MonitoringAgent, NotificationAgent, PerformanceAgent,
    PricingStrategyAgent, ROICalculatorAgent, RedditAgent, ReportingAgent,
    ReviewManagementAgent, SERPTrackerAgent, SSLAgent, SchemaMarkupAgent,
    ServiceDescriptionAgent, SiteSpeedAgent, SocialMediaAgent,
    SupportTicketAgent, SurveyAgent, TechnicalSEOAuditAgent, TitleTagAgent,
    URLOptimizationAgent, VideoScriptAgent, WebhookAgent,
    WhiteLabelReportAgent
)
from self_audit_agent import SelfAuditAgent
from favicon_agent import FaviconAgent
from learning_agent import LearningAgent
from master_agent import MasterAgent
from research_agent import ResearchAgent

print('All imports successful.')
print()
print('='*70)
print('RUNNING TESTS (62 agents)')
print('='*70)

overall_start = time.time()

# 1. AccountingAgent
test_agent('AccountingAgent', AccountingAgent, lambda a: a.get_categories(), 'get_categories')

# 2. AffiliateAgent
test_agent('AffiliateAgent', AffiliateAgent, lambda a: a.get_tiers(), 'get_tiers')

# 3. AnalyticsAgent
test_agent('AnalyticsAgent', AnalyticsAgent, lambda a: a.get_global_stats(), 'get_global_stats')

# 4. AutomationAgent
test_agent('AutomationAgent', AutomationAgent, lambda a: a.get_trigger_types(), 'get_trigger_types')

# 5. BacklinkAnalysisAgent
test_agent('BacklinkAnalysisAgent', BacklinkAnalysisAgent, lambda a: a.analyze_opportunities('demo'), 'analyze_opportunities')

# 6. BacklinkMonitorAgent
test_agent('BacklinkMonitorAgent', BacklinkMonitorAgent, lambda a: a.get_backlink_stats('demo'), 'get_backlink_stats')

# 7. BackupAgent
test_agent('BackupAgent', BackupAgent, lambda a: a.list_backups(), 'list_backups')

# 8. BlogIdeaAgent
test_agent('BlogIdeaAgent', BlogIdeaAgent, lambda a: a.generate_ideas('demo', count=3), 'generate_ideas')

# 9. CRMAgent
test_agent('CRMAgent', CRMAgent, lambda a: a.get_dashboard_stats(), 'get_dashboard_stats')

# 10. CalendarAgent
test_agent('CalendarAgent', CalendarAgent, lambda a: a.get_event_types(), 'get_event_types')

# 11. ChatbotAgent
test_agent('ChatbotAgent', ChatbotAgent, lambda a: a.get_config(), 'get_config')

# 12. ClientOnboardingAgent
test_agent('ClientOnboardingAgent', ClientOnboardingAgent, lambda a: a.list_all_clients(), 'list_all_clients')

# 13. CompetitorAnalysisAgent
test_agent('CompetitorAnalysisAgent', CompetitorAnalysisAgent, lambda a: a.identify_competitors('demo'), 'identify_competitors')

# 14. CompetitorWatchAgent
test_agent('CompetitorWatchAgent', CompetitorWatchAgent, lambda a: a.get_competitors('demo'), 'get_competitors')

# 15. ContentBriefAgent
test_agent('ContentBriefAgent', ContentBriefAgent, lambda a: a.get_briefs(), 'get_briefs')

# 16. ContentCalendarAgent
test_agent('ContentCalendarAgent', ContentCalendarAgent, lambda a: a.generate_calendar('demo', weeks=1), 'generate_calendar')

# 17. ContentGenerationAgent
test_agent('ContentGenerationAgent', ContentGenerationAgent, lambda a: a.generate_meta_tags('Test SEO content about web optimization', 'SEO'), 'generate_meta_tags')

# 18. ContentOptimizationAgent
test_agent('ContentOptimizationAgent', ContentOptimizationAgent, lambda a: a.optimize_existing('Sample content for SEO optimization testing', 'SEO test'), 'optimize_existing')

# 19. ContentSchedulerAgent
test_agent('ContentSchedulerAgent', ContentSchedulerAgent, lambda a: a.generate_content_calendar('demo', weeks=1), 'generate_content_calendar')

# 20. ConversionOptimizationAgent
test_agent('ConversionOptimizationAgent', ConversionOptimizationAgent, lambda a: a.analyze_cta('Buy Now', 'landing'), 'analyze_cta')

# 21. DashboardAgent
test_agent('DashboardAgent', DashboardAgent, lambda a: a.get_overview(), 'get_overview')

# 22. DirectoryAgent
test_agent('DirectoryAgent', DirectoryAgent, lambda a: a.get_submission_checklist('demo'), 'get_submission_checklist')

# 23. EmailCampaignAgent
test_agent('EmailCampaignAgent', EmailCampaignAgent, lambda a: a.get_stats(), 'get_stats')

# 24. EmailMarketingAgent
test_agent('EmailMarketingAgent', EmailMarketingAgent, lambda a: a.generate_newsletter('demo', [{'title': 'Test Article', 'url': 'https://example.com'}]), 'generate_newsletter')

# 25. FAQGenerationAgent
test_agent('FAQGenerationAgent', FAQGenerationAgent, lambda a: a.generate_faq('demo', 'SEO', count=3), 'generate_faq')

# 26. ForumAgent
test_agent('ForumAgent', ForumAgent, lambda a: a.generate_forum_reply('demo', 'How to improve SEO?'), 'generate_forum_reply')

# 27. GuestPostAgent
test_agent('GuestPostAgent', GuestPostAgent, lambda a: a.generate_outreach_email('demo', 'example-blog.com'), 'generate_outreach_email')

# 28. ImageOptimizationAgent
test_agent('ImageOptimizationAgent', ImageOptimizationAgent, lambda a: a.generate_alt_texts('website homepage banner', 'SEO agency'), 'generate_alt_texts')

# 29. InternalLinkingAgent
test_agent('InternalLinkingAgent', InternalLinkingAgent, lambda a: a.suggest_links('demo', 'SEO optimization'), 'suggest_links')

# 30. InvoiceAgent
test_agent('InvoiceAgent', InvoiceAgent, lambda a: a.list_invoices(), 'list_invoices')

# 31. KeywordGapAgent
test_agent('KeywordGapAgent', KeywordGapAgent, lambda a: a.compare_two_domains('example.com', 'competitor.com', niche='SEO'), 'compare_two_domains')

# 32. KeywordResearchAgent
test_agent('KeywordResearchAgent', KeywordResearchAgent, lambda a: a.find_keywords('demo', 'SEO', limit=3), 'find_keywords')

# 33. KnowledgeBaseAgent
test_agent('KnowledgeBaseAgent', KnowledgeBaseAgent, lambda a: a.get_stats(), 'get_stats')

# 34. LandingPageAgent
test_agent('LandingPageAgent', LandingPageAgent, lambda a: a.generate_landing_page('demo', 'SEO Audit', 'seo audit'), 'generate_landing_page')

# 35. LeadScoringAgent
test_agent('LeadScoringAgent', LeadScoringAgent, lambda a: a.get_stats(), 'get_stats')

# 36. LocalSEOAgent
test_agent('LocalSEOAgent', LocalSEOAgent, lambda a: a.get_local_seo_score('demo'), 'get_local_seo_score')

# 37. LoyaltyAgent
test_agent('LoyaltyAgent', LoyaltyAgent, lambda a: a.get_tiers(), 'get_tiers')

# 38. MonitoringAgent
test_agent('MonitoringAgent', MonitoringAgent, lambda a: a.find_alerts_for_site('demo'), 'find_alerts_for_site')

# 39. NotificationAgent
test_agent('NotificationAgent', NotificationAgent, lambda a: a.get_notification_types(), 'get_notification_types')

# 40. PerformanceAgent
test_agent('PerformanceAgent', PerformanceAgent, lambda a: a.compare_sites(), 'compare_sites')

# 41. PricingStrategyAgent
test_agent('PricingStrategyAgent', PricingStrategyAgent, lambda a: a.analyze_competitor_pricing('demo', 'SEO'), 'analyze_competitor_pricing')

# 42. ROICalculatorAgent
test_agent('ROICalculatorAgent', ROICalculatorAgent, lambda a: a.get_roi_history('demo'), 'get_roi_history')

# 43. RedditAgent
test_agent('RedditAgent', RedditAgent, lambda a: a.generate_reddit_post('demo', 'SEO tips'), 'generate_reddit_post')

# 44. ReportingAgent
test_agent('ReportingAgent', ReportingAgent, lambda a: a.generate_weekly_report('demo'), 'generate_weekly_report')

# 45. ReviewManagementAgent
test_agent('ReviewManagementAgent', ReviewManagementAgent, lambda a: a.generate_review_response('Great service!', 5, is_positive=True), 'generate_review_response')

# 46. SERPTrackerAgent
test_agent('SERPTrackerAgent', SERPTrackerAgent, lambda a: a.get_tracked_keywords('demo'), 'get_tracked_keywords')

# 47. SSLAgent
test_agent('SSLAgent', SSLAgent, lambda a: a.check_all_sites(), 'check_all_sites')

# 48. SchemaMarkupAgent
test_agent('SchemaMarkupAgent', SchemaMarkupAgent, lambda a: a.generate_faq_schema([{'q': 'What is SEO?', 'a': 'Search Engine Optimization'}]), 'generate_faq_schema')

# 49. SelfAuditAgent
test_agent('SelfAuditAgent', SelfAuditAgent, lambda a: a.get_ssh_report(), 'get_ssh_report')

# 50. ServiceDescriptionAgent
test_agent('ServiceDescriptionAgent', ServiceDescriptionAgent, lambda a: a.generate_service_page('demo', 'SEO Audit'), 'generate_service_page')

# 51. SiteSpeedAgent
test_agent('SiteSpeedAgent', SiteSpeedAgent, lambda a: a.get_speed_history('demo'), 'get_speed_history')

# 52. SocialMediaAgent
test_agent('SocialMediaAgent', SocialMediaAgent, lambda a: a.generate_social_posts('Test Article', 'https://example.com', platform='all'), 'generate_social_posts')

# 53. SupportTicketAgent
test_agent('SupportTicketAgent', SupportTicketAgent, lambda a: a.get_stats(), 'get_stats')

# 54. SurveyAgent
test_agent('SurveyAgent', SurveyAgent, lambda a: a.get_stats(), 'get_stats')

# 55. TechnicalSEOAuditAgent
test_agent('TechnicalSEOAuditAgent', TechnicalSEOAuditAgent, lambda a: a.check_robots_txt('example.com'), 'check_robots_txt')

# 56. TitleTagAgent
test_agent('TitleTagAgent', TitleTagAgent, lambda a: a.optimize_title('My Page', 'SEO', 'SeoAI'), 'optimize_title')

# 57. URLOptimizationAgent
test_agent('URLOptimizationAgent', URLOptimizationAgent, lambda a: a.generate_slug('Best SEO Tips 2026', 'seo tips'), 'generate_slug')

# 58. VideoScriptAgent
test_agent('VideoScriptAgent', VideoScriptAgent, lambda a: a.generate_script('SEO basics', duration_seconds=30), 'generate_script')

# 59. WebhookAgent
test_agent('WebhookAgent', WebhookAgent, lambda a: a.get_event_types(), 'get_event_types')

# 60. WhiteLabelReportAgent
test_agent('WhiteLabelReportAgent', WhiteLabelReportAgent, lambda a: a.generate_quick_report('demo'), 'generate_quick_report')

# 61. FaviconAgent
test_agent('FaviconAgent', FaviconAgent, lambda a: a.status(), 'status')

# 62. LearningAgent
test_agent('LearningAgent', LearningAgent, lambda a: a.get_learnings(), 'get_learnings')

# Note: MasterAgent and ResearchAgent are subcomponents used by MasterAgent.
# We include MasterAgent.get_dashboard_data as an extra if desired,
# but we already have 62 above.

# ============================================================
# SUMMARY
# ============================================================
overall_elapsed = round(time.time() - overall_start, 2)

print()
print('='*70)
print(f'RESULTS: {passed} OK / {failed} FAIL / {len(results)} TOTAL')
print(f'Total time: {overall_elapsed}s')
print('='*70)

if failed > 0:
    print()
    print('FAILED AGENTS:')
    for r in results:
        if r['status'] == 'FAIL':
            print(f'  - {r[agent]}.{r[method]}(): {r[error]}')

# Save JSON
output = {
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'total_agents': len(results),
    'passed': passed,
    'failed': failed,
    'total_seconds': overall_elapsed,
    'results': results
}

with open('/opt/seo-agent/logs/test_62_agents.json', 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print()
print(f'Results saved to /opt/seo-agent/logs/test_62_agents.json')

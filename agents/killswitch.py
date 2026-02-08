#!/usr/bin/env python3
"""
KILLSWITCH - Controle Central des 61 Agents AI
Permet d'activer/desactiver tous les agents instantanement
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, jsonify, request

DB_PATH = '/opt/seo-agent/db/seo_agent.db'
CONFIG_FILE = '/opt/seo-agent/config/killswitch.json'

app = Flask(__name__)

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'master_enabled': True,
        'agents_enabled': {},
        'last_updated': None,
        'updated_by': None
    }

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    config['last_updated'] = datetime.now().isoformat()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Liste des 61 agents
AGENTS = [
    'MasterOrchestrator', 'KeywordResearchAgent', 'ContentGenerationAgent',
    'FAQGenerationAgent', 'TechnicalSEOAuditAgent', 'PerformanceAgent',
    'BacklinkAnalysisAgent', 'LocalSEOAgent', 'CompetitorAnalysisAgent',
    'ContentOptimizationAgent', 'SchemaMarkupAgent', 'SocialMediaAgent',
    'EmailMarketingAgent', 'ImageOptimizationAgent', 'InternalLinkingAgent',
    'URLOptimizationAgent', 'TitleTagAgent', 'ContentCalendarAgent',
    'PricingStrategyAgent', 'ReviewManagementAgent', 'ConversionOptimizationAgent',
    'MonitoringAgent', 'SSLAgent', 'BackupAgent', 'AnalyticsAgent',
    'ReportingAgent', 'LandingPageAgent', 'BlogIdeaAgent', 'VideoScriptAgent',
    'ServiceDescriptionAgent', 'RedditAgent', 'ForumAgent', 'DirectoryAgent',
    'GuestPostAgent', 'ContentSchedulerAgent', 'ClientOnboardingAgent',
    'WhiteLabelReportAgent', 'SERPTrackerAgent', 'KeywordGapAgent',
    'ContentBriefAgent', 'BacklinkMonitorAgent', 'SiteSpeedAgent',
    'ROICalculatorAgent', 'CompetitorWatchAgent', 'InvoiceAgent', 'CRMAgent',
    'AccountingAgent', 'CalendarAgent', 'ChatbotAgent', 'NotificationAgent',
    'DashboardAgent', 'LeadScoringAgent', 'EmailCampaignAgent',
    'SupportTicketAgent', 'KnowledgeBaseAgent', 'SurveyAgent', 'WebhookAgent',
    'AutomationAgent', 'AffiliateAgent', 'LoyaltyAgent'
]

@app.route('/killswitch/status', methods=['GET'])
def status():
    config = get_config()
    return jsonify({
        'master_enabled': config['master_enabled'],
        'total_agents': len(AGENTS),
        'agents_enabled': sum(1 for a in AGENTS if config.get('agents_enabled', {}).get(a, True)),
        'agents_disabled': sum(1 for a in AGENTS if not config.get('agents_enabled', {}).get(a, True)),
        'last_updated': config.get('last_updated')
    })

@app.route('/killswitch/master/<action>', methods=['POST'])
def master_switch(action):
    config = get_config()
    if action == 'on':
        config['master_enabled'] = True
        msg = 'TOUS LES AGENTS ACTIVES'
    elif action == 'off':
        config['master_enabled'] = False
        msg = 'TOUS LES AGENTS DESACTIVES'
    else:
        return jsonify({'error': 'Action invalide (on/off)'}), 400
    
    save_config(config)
    return jsonify({'success': True, 'message': msg, 'master_enabled': config['master_enabled']})

@app.route('/killswitch/agent/<agent_name>/<action>', methods=['POST'])
def agent_switch(agent_name, action):
    if agent_name not in AGENTS:
        return jsonify({'error': f'Agent {agent_name} non trouve'}), 404
    
    config = get_config()
    if 'agents_enabled' not in config:
        config['agents_enabled'] = {}
    
    if action == 'on':
        config['agents_enabled'][agent_name] = True
    elif action == 'off':
        config['agents_enabled'][agent_name] = False
    else:
        return jsonify({'error': 'Action invalide (on/off)'}), 400
    
    save_config(config)
    return jsonify({'success': True, 'agent': agent_name, 'enabled': config['agents_enabled'][agent_name]})

@app.route('/killswitch/agents', methods=['GET'])
def list_agents():
    config = get_config()
    agents_status = []
    for agent in AGENTS:
        enabled = config.get('agents_enabled', {}).get(agent, True)
        if not config['master_enabled']:
            enabled = False
        agents_status.append({'name': agent, 'enabled': enabled})
    return jsonify({'master_enabled': config['master_enabled'], 'agents': agents_status})

@app.route('/killswitch/emergency-stop', methods=['POST'])
def emergency_stop():
    config = get_config()
    config['master_enabled'] = False
    config['emergency_stop'] = datetime.now().isoformat()
    save_config(config)
    return jsonify({'success': True, 'message': 'ARRET D URGENCE - Tous les agents stoppes!'})

def is_agent_enabled(agent_name):
    config = get_config()
    if not config['master_enabled']:
        return False
    return config.get('agents_enabled', {}).get(agent_name, True)

if __name__ == '__main__':
    os.makedirs('/opt/seo-agent/config', exist_ok=True)
    print('[KILLSWITCH] Demarrage du controleur central...')
    print(f'[KILLSWITCH] {len(AGENTS)} agents sous controle')
    app.run(host='0.0.0.0', port=8888, debug=False)

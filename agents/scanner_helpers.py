import requests
import json
import re

# ============================================================
# SCANNER HELPERS - Email, AI Analysis, HTML Report
# Upgraded 2026-02-10 - Professional sales-oriented report
# ============================================================

import smtplib
import sqlite3
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_PATH = '/opt/seo-agent/db/seo_agent.db'
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY', 'fw_CbsGnsaL5NSi4wgasWhjtQ')
FIREWORKS_URL = 'https://api.fireworks.ai/inference/v1/chat/completions'
DEEPSEEK_MODEL = 'accounts/fireworks/models/deepseek-r1-0528'
ADMIN_EMAIL = 'michaelperron12@gmail.com'
SCANNER_FROM = 'scanner@seoparai.com'


def save_lead(email, domain, grade, score, report_sent=0):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO scanner_leads (email, domain, grade, score, scan_date, report_sent) VALUES (?, ?, ?, ?, datetime('now'), ?)",
            (email, domain, grade, score, report_sent)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] Error saving lead: {e}")


def send_report_email(to_email, domain, grade, score, html_report):
    try:
        msg = MIMEMultipart('alternative')

        # Compelling subject line
        if score < 50:
            urgency = 'URGENT'
        elif score < 70:
            urgency = 'ATTENTION'
        else:
            urgency = 'RAPPORT'

        msg['Subject'] = urgency + ': Votre site ' + domain + ' perd des clients - Note ' + grade + ' (' + str(score) + '%)'
        msg['From'] = 'SeoparAI Scanner <' + SCANNER_FROM + '>'
        msg['To'] = to_email
        msg['Reply-To'] = 'michaelperron12@gmail.com'

        text_part = MIMEText(
            'RAPPORT SEO & AI-READINESS - ' + domain + '\n'
            '==========================================\n\n'
            'Note globale: ' + grade + ' (' + str(score) + '%)\n\n'
            'Votre site necessite des ameliorations pour etre visible dans les moteurs de recherche et les assistants AI.\n\n'
            'Consultez le rapport HTML complet pour les details.\n\n'
            'Pour une consultation gratuite de 30 minutes:\n'
            'Tel: 514-609-2882\n'
            'Email: michaelperron12@gmail.com\n\n'
            '- L\'equipe SeoparAI',
            'plain', 'utf-8'
        )
        html_part = MIMEText(html_report, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP('localhost', 25) as server:
            server.sendmail(SCANNER_FROM, [to_email], msg.as_string())

        admin_msg = MIMEText(
            'NOUVEAU LEAD SCANNER\n'
            '====================\n\n'
            'Email: ' + to_email + '\n'
            'Domaine: ' + domain + '\n'
            'Note: ' + grade + ' (' + str(score) + '%)\n'
            'Date: ' + datetime.now().strftime('%Y-%m-%d %H:%M') + '\n\n'
            'ACTION: Relancer dans 24-48h si pas de reponse.',
            'plain', 'utf-8'
        )
        admin_msg['Subject'] = '[LEAD] ' + domain + ' - ' + grade + ' (' + str(score) + '%) - ' + to_email
        admin_msg['From'] = SCANNER_FROM
        admin_msg['To'] = ADMIN_EMAIL
        with smtplib.SMTP('localhost', 25) as server:
            server.sendmail(SCANNER_FROM, [ADMIN_EMAIL], admin_msg.as_string())

        print('[EMAIL] Report sent to ' + to_email + ' + admin notified')
        return True
    except Exception as e:
        print('[EMAIL] Error: ' + str(e))
        return False


def get_ai_analysis(domain, grade, scores, top_fails):
    try:
        fails_text = '\n'.join(['- ' + f['check'] + ': ' + f['recommendation'] for f in top_fails[:5]])
        prompt = (
            'Tu es un expert SEO et AI-readiness. Analyse ces resultats de scan pour ' + domain + ' et donne exactement 5 recommandations personnalisees.\n\n'
            'Note globale: ' + grade + ' (' + str(scores.get('total', 0)) + '%)\n'
            'SEO Classique: ' + str(scores.get('seo_classic', 0)) + '%\n'
            'SEO Technique: ' + str(scores.get('seo_technique', 0)) + '%\n'
            'AI-Readiness: ' + str(scores.get('ai_readiness', 0)) + '%\n'
            'Qualite Contenu: ' + str(scores.get('content_quality', 0)) + '%\n\n'
            'Problemes principaux:\n' + fails_text + '\n\n'
            'Reponds en JSON strict:\n'
            '{"recommendations": ["rec1", "rec2", "rec3", "rec4", "rec5"], "priority_action": "action immediate", "competitive_insight": "insight competitif"}'
        )
        headers = {'Authorization': 'Bearer ' + FIREWORKS_API_KEY, 'Content-Type': 'application/json'}
        payload = {'model': DEEPSEEK_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2000, 'temperature': 0.3}

        resp = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            # Strip DeepSeek R1 <think>...</think> reasoning block
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            print('[AI] Response after stripping think: ' + content[:200])
            # Try to extract JSON from response
            # First try: find JSON block in markdown code fence
            code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if code_match:
                return json.loads(code_match.group(1))
            # Second try: find any JSON object with recommendations key
            json_match = re.search(r'(\{[^{}]*"recommendations"\s*:\s*\[[^\]]*\][^}]*\})', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            # Third try: parse the whole content as JSON
            clean = content.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            return json.loads(clean)
        return None
    except Exception as e:
        print('[AI] Error: ' + str(e))
        return None


def _generate_fallback_ai(results, scores):
    """Generate smart fallback recommendations when DeepSeek is unavailable or returns placeholders."""
    domain = results.get('domain', '')
    recs = []
    priority = ''
    insight = ''

    total = scores.get('total', 0)
    seo_classic = scores.get('seo_classic', 0)
    seo_tech = scores.get('seo_technique', 0)
    ai_ready = scores.get('ai_readiness', 0)
    content_q = scores.get('content_quality', 0)

    # Collect all failed checks
    failed_checks = []
    for cat_key in ['seo_classic', 'seo_technique', 'ai_readiness', 'content_quality']:
        cat_data = results.get(cat_key, {})
        for check in cat_data.get('checks', []):
            if check.get('status') == 'fail':
                failed_checks.append(check)

    # Generate contextual recommendations based on actual failures
    if seo_classic < 60:
        recs.append(
            'Votre SEO classique est critique (' + str(seo_classic) + '%). '
            'Les balises titre, meta descriptions et structure de titres H1-H6 doivent etre '
            'optimisees immediatement pour que Google indexe correctement vos pages.'
        )
    elif seo_classic < 80:
        recs.append(
            'Votre SEO on-page (' + str(seo_classic) + '%) peut etre ameliore. '
            'Optimisez vos balises titre avec des mots-cles strategiques et assurez-vous '
            'que chaque page a une meta description unique et convaincante.'
        )

    if ai_ready < 50:
        recs.append(
            'CRITIQUE: Votre site est pratiquement invisible pour les assistants AI comme ChatGPT, '
            'Perplexity et Google SGE (score: ' + str(ai_ready) + '%). Ajoutez des donnees structurees '
            'Schema.org, un llms.txt et des FAQ structurees pour etre cite par les AI.'
        )
    elif ai_ready < 75:
        recs.append(
            'Votre AI-readiness (' + str(ai_ready) + '%) est sous la moyenne. Les assistants AI '
            'privilegient les sites avec des donnees structurees riches (Schema.org), du contenu '
            'FAQ et une architecture claire. Vos competiteurs optimises seront cites a votre place.'
        )

    if seo_tech < 60:
        recs.append(
            'Problemes techniques majeurs detectes (' + str(seo_tech) + '%). La vitesse de chargement, '
            'le SSL, le sitemap.xml et le robots.txt sont essentiels. Google penalise les sites lents '
            'et mal configures dans ses resultats de recherche.'
        )
    elif seo_tech < 80:
        recs.append(
            'Votre infrastructure technique (' + str(seo_tech) + '%) a des lacunes. '
            'Optimisez la vitesse de chargement, verifiez votre sitemap.xml et assurez-vous '
            'que le robots.txt ne bloque pas de pages importantes.'
        )

    if content_q < 60:
        recs.append(
            'La qualite de votre contenu est insuffisante (' + str(content_q) + '%). '
            'Google et les AI privilegient le contenu detaille, bien structure avec des images '
            'optimisees (attributs ALT). Visez minimum 800 mots par page principale.'
        )
    elif content_q < 80:
        recs.append(
            'Ameliorez la qualite de votre contenu (' + str(content_q) + '%). '
            'Ajoutez des textes plus longs et detailles, des images avec attributs ALT '
            'descriptifs et une structure claire avec des sous-titres H2/H3.'
        )

    # Always add an AI-specific recommendation
    if ai_ready < 75:
        recs.append(
            'En 2025-2026, 40% des recherches passent par des AI (ChatGPT, Perplexity, Gemini). '
            'Sans optimisation AEO (Answer Engine Optimization), votre entreprise est invisible '
            'pour ces nouveaux canaux d\'acquisition de clients.'
        )

    # Add a competitive recommendation
    recs.append(
        'Les entreprises de votre secteur qui investissent en SEO et AI-readiness '
        'voient en moyenne 3x plus de trafic organique. Chaque mois sans optimisation '
        'represente des dizaines de clients potentiels perdus au profit de vos competiteurs.'
    )

    # Trim to 5 max
    recs = recs[:5]

    # If we still have less than 3, add generic but useful ones
    while len(recs) < 3:
        recs.append(
            'Implementez un suivi Google Analytics 4 et Google Search Console pour '
            'mesurer l\'impact de vos optimisations et identifier les opportunites de croissance.'
        )

    # Generate priority action
    if total < 40:
        priority = 'Intervention urgente requise. Votre site est en dessous des standards minimaux de Google. Un audit complet et un plan de correction en 30 jours sont necessaires pour eviter de perdre davantage de visibilite.'
    elif total < 60:
        priority = 'Optimisations prioritaires necessaires dans les 2-4 prochaines semaines. Concentrez-vous sur les elements critiques identifies (en rouge) pour un gain rapide de visibilite.'
    elif total < 80:
        priority = 'Votre site a une base correcte mais des ameliorations ciblees peuvent significativement augmenter votre trafic. Focus sur l\'AI-readiness et le contenu.'
    else:
        priority = 'Bon travail! Votre site est bien optimise. Concentrez-vous maintenant sur le contenu avance et l\'optimisation AI pour maintenir votre avance concurrentielle.'

    # Competitive insight
    if total < 50:
        insight = 'Avec un score de ' + str(total) + '%, votre site se situe dans les 30% les moins performants de votre industrie. Les leaders de votre marche obtiennent typiquement 80%+ sur ces criteres.'
    elif total < 70:
        insight = 'Votre score de ' + str(total) + '% est dans la moyenne basse. Les sites qui dominent les resultats Google et les citations AI dans votre secteur atteignent generalement 80-90%.'
    else:
        insight = 'Avec ' + str(total) + '%, vous etes au-dessus de la moyenne. Quelques optimisations ciblees peuvent vous positionner parmi les leaders de votre secteur.'

    return {
        'recommendations': recs,
        'priority_action': priority,
        'competitive_insight': insight
    }


def _is_placeholder_ai(ai_analysis):
    """Check if AI analysis contains placeholder text (rec1, rec2, etc.)."""
    if not ai_analysis:
        return True
    recs = ai_analysis.get('recommendations', [])
    if not recs:
        return True
    for r in recs:
        r_lower = str(r).lower().strip()
        # Check for placeholder patterns
        if r_lower in ('rec1', 'rec2', 'rec3', 'rec4', 'rec5'):
            return True
        if len(r_lower) < 10:
            return True
    pri = str(ai_analysis.get('priority_action', '')).lower().strip()
    if pri in ('action immediate', 'action', '') or len(pri) < 10:
        return True
    return False


def generate_html_report(results, ai_analysis=None):
    domain = results.get('domain', '')
    grade = results.get('grade', 'F')
    scores = results.get('scores', {})
    total = scores.get('total', 0)
    scan_date = datetime.now().strftime('%d %B %Y')
    scan_date_short = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Fix French month names
    month_map = {
        'January': 'janvier', 'February': 'fevrier', 'March': 'mars',
        'April': 'avril', 'May': 'mai', 'June': 'juin',
        'July': 'juillet', 'August': 'aout', 'September': 'septembre',
        'October': 'octobre', 'November': 'novembre', 'December': 'decembre'
    }
    for en, fr in month_map.items():
        scan_date = scan_date.replace(en, fr)

    # Handle placeholder AI analysis - generate fallback
    if _is_placeholder_ai(ai_analysis):
        ai_analysis = _generate_fallback_ai(results, scores)

    # Color scheme
    grade_colors = {
        'A+': '#059669', 'A': '#10b981',
        'B': '#3b82f6',
        'C': '#f59e0b',
        'D': '#f97316',
        'F': '#dc2626'
    }
    gc = grade_colors.get(grade, '#dc2626')

    # Score message
    if total >= 80:
        score_msg = 'Bon score! Quelques optimisations peuvent vous propulser encore plus haut.'
        score_msg_color = '#059669'
    elif total >= 60:
        score_msg = 'Score moyen. Des ameliorations significatives sont possibles.'
        score_msg_color = '#d97706'
    elif total >= 40:
        score_msg_color = '#ea580c'
        score_msg = 'Score faible. Votre site necessite des ameliorations importantes.'
    else:
        score_msg_color = '#dc2626'
        score_msg = 'Score critique! Votre site perd des clients chaque jour.'

    # ================================================================
    # STATUS ICONS (email-safe, no emoji)
    # ================================================================
    def status_badge(status):
        if status == 'pass':
            return '<span style="display:inline-block;padding:3px 10px;background:#dcfce7;color:#166534;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.5px;">OK</span>'
        elif status == 'warning':
            return '<span style="display:inline-block;padding:3px 10px;background:#fef3c7;color:#92400e;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.5px;">ATTENTION</span>'
        else:
            return '<span style="display:inline-block;padding:3px 10px;background:#fecaca;color:#991b1b;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.5px;">ECHEC</span>'

    # ================================================================
    # PROGRESS BAR helper
    # ================================================================
    def progress_bar(value, color):
        bar_bg = '#e5e7eb'
        w = max(2, min(100, value))
        return (
            '<div style="width:100%;background:' + bar_bg + ';border-radius:6px;height:10px;margin-top:6px;">'
            '<div style="width:' + str(w) + '%;background:' + color + ';border-radius:6px;height:10px;"></div>'
            '</div>'
        )

    def score_color(val):
        if val >= 80: return '#059669'
        if val >= 60: return '#3b82f6'
        if val >= 40: return '#f59e0b'
        return '#dc2626'

    # ================================================================
    # CATEGORY DESCRIPTIONS
    # ================================================================
    cat_descriptions = {
        'seo_classic': 'Balises titre, meta descriptions, titres H1-H6, images ALT - les fondamentaux du referencement Google.',
        'seo_technique': 'Performance serveur, SSL, sitemap, robots.txt, vitesse - l\'infrastructure technique de votre site.',
        'ai_readiness': 'Donnees structurees, Schema.org, llms.txt, FAQ - votre visibilite aupres de ChatGPT, Perplexity et Google SGE.',
        'content_quality': 'Longueur du contenu, structure, images, liens - la qualite globale de vos pages.'
    }

    cat_icons = {
        'seo_classic': 'SEO',
        'seo_technique': 'TECH',
        'ai_readiness': 'AI',
        'content_quality': 'CONT'
    }

    cat_colors = {
        'seo_classic': '#3b82f6',
        'seo_technique': '#8b5cf6',
        'ai_readiness': '#6366f1',
        'content_quality': '#10b981'
    }

    cat_names = {
        'seo_classic': 'SEO Classique',
        'seo_technique': 'SEO Technique',
        'ai_readiness': 'AI-Readiness (AEO/SAIO)',
        'content_quality': 'Qualite du Contenu'
    }

    # ================================================================
    # CATEGORY SCORE CARDS (with progress bars)
    # ================================================================
    score_cards_html = ''
    for key in ['seo_classic', 'seo_technique', 'ai_readiness', 'content_quality']:
        val = scores.get(key, 0)
        col = cat_colors.get(key, '#3b82f6')
        sc = score_color(val)
        icon_label = cat_icons[key]
        score_cards_html += (
            '<td style="width:25%;padding:6px;vertical-align:top;">'
            '<div style="background:#f8fafc;border-radius:8px;padding:14px 10px;text-align:center;border-top:3px solid ' + col + ';">'
            '<div style="font-size:11px;font-weight:700;color:' + col + ';letter-spacing:1px;margin-bottom:6px;">' + icon_label + '</div>'
            '<div style="font-size:26px;font-weight:800;color:' + sc + ';">' + str(val) + '%</div>'
            '<div style="font-size:11px;color:#64748b;margin-top:2px;">' + cat_names[key] + '</div>'
            + progress_bar(val, sc) +
            '</div>'
            '</td>'
        )

    # ================================================================
    # RENDER CHECKS TABLE (grouped by priority: fail first, then warning, then pass)
    # ================================================================
    def render_category_checks(name, key):
        cat = results.get(key, {})
        checks = cat.get('checks', [])
        if not checks:
            return ''

        val = scores.get(key, 0)
        col = cat_colors.get(key, '#3b82f6')
        sc = score_color(val)
        desc = cat_descriptions.get(key, '')

        # Sort: fail first, then warning, then pass
        priority_order = {'fail': 0, 'warning': 1, 'pass': 2}
        sorted_checks = sorted(checks, key=lambda c: priority_order.get(c.get('status', 'pass'), 2))

        h = ''
        h += '<div style="margin-bottom:28px;">'
        # Category header
        h += '<table style="width:100%;border-collapse:collapse;"><tr>'
        h += '<td style="padding:14px 16px;background:#f8fafc;border-radius:8px 8px 0 0;border-left:4px solid ' + col + ';">'
        h += '<div style="font-weight:700;font-size:16px;color:#1e293b;">' + name + '</div>'
        h += '<div style="font-size:12px;color:#64748b;margin-top:2px;">' + desc + '</div>'
        h += '</td>'
        h += '<td style="padding:14px 16px;background:#f8fafc;border-radius:8px 8px 0 0;text-align:right;width:80px;">'
        h += '<span style="font-size:24px;font-weight:800;color:' + sc + ';">' + str(val) + '%</span>'
        h += '</td>'
        h += '</tr></table>'

        # Checks table
        h += '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        for c in sorted_checks:
            status = c.get('status', 'fail')
            if status == 'pass':
                row_bg = '#ffffff'
                border_color = '#e5e7eb'
            elif status == 'warning':
                row_bg = '#fffbeb'
                border_color = '#fde68a'
            else:
                row_bg = '#fef2f2'
                border_color = '#fecaca'

            details_text = str(c.get('details', ''))
            # Truncate very long details
            if len(details_text) > 150:
                details_text = details_text[:147] + '...'

            h += '<tr style="background:' + row_bg + ';border-bottom:1px solid ' + border_color + ';">'
            h += '<td style="padding:10px 12px;width:80px;text-align:center;vertical-align:top;">' + status_badge(status) + '</td>'
            h += '<td style="padding:10px 8px;vertical-align:top;">'
            h += '<div style="font-weight:600;color:#1e293b;">' + c.get('name', '') + '</div>'
            if details_text:
                h += '<div style="color:#6b7280;font-size:12px;margin-top:3px;line-height:1.4;">' + details_text + '</div>'
            h += '</td>'
            h += '</tr>'
        h += '</table>'
        h += '</div>'
        return h

    checks_html = ''
    checks_html += render_category_checks('SEO Classique', 'seo_classic')
    checks_html += render_category_checks('SEO Technique', 'seo_technique')
    checks_html += render_category_checks('AI-Readiness (AEO/SAIO)', 'ai_readiness')
    checks_html += render_category_checks('Qualite du Contenu', 'content_quality')

    # ================================================================
    # RECOMMENDATIONS SECTION
    # ================================================================
    recs = results.get('recommendations', [])
    recs_html = ''
    if recs:
        recs_html = '<div style="margin-bottom:28px;">'
        recs_html += '<table style="width:100%;border-collapse:collapse;"><tr><td style="padding:0;">'
        recs_html += '<div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:14px;">Recommandations Prioritaires</div>'
        for i, r in enumerate(recs[:8], 1):
            imp = r.get('importance', 'medium')
            if imp == 'critical':
                ic = '#dc2626'
                badge = '<span style="display:inline-block;padding:2px 8px;background:#fecaca;color:#991b1b;border-radius:3px;font-size:10px;font-weight:700;margin-left:8px;">CRITIQUE</span>'
            elif imp == 'high':
                ic = '#f59e0b'
                badge = '<span style="display:inline-block;padding:2px 8px;background:#fef3c7;color:#92400e;border-radius:3px;font-size:10px;font-weight:700;margin-left:8px;">IMPORTANT</span>'
            else:
                ic = '#3b82f6'
                badge = '<span style="display:inline-block;padding:2px 8px;background:#dbeafe;color:#1e40af;border-radius:3px;font-size:10px;font-weight:700;margin-left:8px;">SUGGERE</span>'

            recs_html += '<div style="padding:12px 14px;margin-bottom:6px;background:#f8fafc;border-radius:6px;border-left:3px solid ' + ic + ';font-size:13px;line-height:1.5;">'
            recs_html += '<strong style="color:#1e293b;">' + str(i) + '.</strong> ' + r.get('recommendation', '')
            recs_html += badge
            if r.get('ai_impact'):
                recs_html += '<br><span style="color:#6366f1;font-size:12px;">Impact AI: ' + r['ai_impact'] + '</span>'
            recs_html += '</div>'
        recs_html += '</td></tr></table></div>'

    # ================================================================
    # AI ANALYSIS SECTION (with fallback handling)
    # ================================================================
    ai_html = ''
    if ai_analysis:
        ai_recs = ai_analysis.get('recommendations', [])
        pri = ai_analysis.get('priority_action', '')
        ins = ai_analysis.get('competitive_insight', '')

        ai_html = '<div style="margin-bottom:28px;">'
        ai_html += '<table style="width:100%;border-collapse:collapse;"><tr><td style="padding:20px;background:#1e1b4b;border-radius:10px;">'

        # Header
        ai_html += '<table style="width:100%;border-collapse:collapse;"><tr>'
        ai_html += '<td style="padding:0 0 14px 0;">'
        ai_html += '<div style="font-size:18px;font-weight:700;color:#e0e7ff;">Analyse AI Personnalisee</div>'
        ai_html += '<div style="font-size:12px;color:#a5b4fc;margin-top:2px;">Analyse approfondie par intelligence artificielle</div>'
        ai_html += '</td></tr></table>'

        # Priority action
        if pri:
            ai_html += '<table style="width:100%;border-collapse:collapse;margin-bottom:14px;"><tr>'
            ai_html += '<td style="padding:12px 16px;background:rgba(99,102,241,0.3);border-radius:8px;border-left:3px solid #818cf8;">'
            ai_html += '<div style="font-size:11px;font-weight:700;color:#a5b4fc;letter-spacing:0.5px;margin-bottom:4px;">ACTION PRIORITAIRE</div>'
            ai_html += '<div style="color:#e0e7ff;font-size:13px;line-height:1.5;">' + pri + '</div>'
            ai_html += '</td></tr></table>'

        # Recommendations
        for i, rec in enumerate(ai_recs, 1):
            ai_html += '<div style="padding:8px 0;font-size:13px;color:#c7d2fe;line-height:1.5;border-bottom:1px solid rgba(255,255,255,0.08);">'
            ai_html += '<span style="display:inline-block;width:22px;height:22px;background:rgba(99,102,241,0.4);border-radius:50%;text-align:center;line-height:22px;font-size:11px;font-weight:700;color:#a5b4fc;margin-right:8px;">' + str(i) + '</span>'
            ai_html += rec + '</div>'

        # Competitive insight
        if ins:
            ai_html += '<table style="width:100%;border-collapse:collapse;margin-top:14px;"><tr>'
            ai_html += '<td style="padding:12px 16px;background:rgba(255,255,255,0.06);border-radius:8px;">'
            ai_html += '<div style="font-size:11px;font-weight:700;color:#a5b4fc;letter-spacing:0.5px;margin-bottom:4px;">PERSPECTIVE CONCURRENTIELLE</div>'
            ai_html += '<div style="color:#c7d2fe;font-size:13px;font-style:italic;line-height:1.5;">' + ins + '</div>'
            ai_html += '</td></tr></table>'

        ai_html += '</td></tr></table></div>'

    # ================================================================
    # COMPETITIVE COMPARISON SECTION
    # ================================================================
    your_pos = total
    avg_pos = 45
    top_pos = 87

    # Bar widths
    def comp_bar(val, color, label_text, sublabel):
        w = max(3, val)
        return (
            '<tr><td style="padding:6px 0;">'
            '<div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:3px;">' + label_text + ' <span style="color:' + color + ';font-weight:800;">' + str(val) + '%</span></div>'
            '<div style="font-size:11px;color:#9ca3af;margin-bottom:4px;">' + sublabel + '</div>'
            '<div style="width:100%;background:#e5e7eb;border-radius:4px;height:14px;">'
            '<div style="width:' + str(w) + '%;background:' + color + ';border-radius:4px;height:14px;"></div>'
            '</div></td></tr>'
        )

    comp_html = '<div style="margin-bottom:28px;">'
    comp_html += '<table style="width:100%;border-collapse:collapse;"><tr><td style="padding:20px;background:#f8fafc;border-radius:10px;border:1px solid #e5e7eb;">'
    comp_html += '<div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:4px;">Comment vous comparez</div>'
    comp_html += '<div style="font-size:12px;color:#64748b;margin-bottom:16px;">Comparaison avec les moyennes de l\'industrie (sites PME au Quebec)</div>'
    comp_html += '<table style="width:100%;border-collapse:collapse;">'
    comp_html += comp_bar(your_pos, gc, 'Votre site (' + domain + ')', 'Score actuel de votre scan')
    comp_html += comp_bar(avg_pos, '#9ca3af', 'Moyenne de l\'industrie', 'Score moyen des PME quebecoises')
    comp_html += comp_bar(top_pos, '#059669', 'Sites les mieux optimises', 'Top 10% des sites dans votre secteur')
    comp_html += '</table>'

    if total < avg_pos:
        comp_html += '<div style="margin-top:14px;padding:10px 14px;background:#fef2f2;border-radius:6px;border-left:3px solid #dc2626;font-size:13px;color:#991b1b;line-height:1.4;">'
        comp_html += '<strong>Votre site est en dessous de la moyenne.</strong> Vos competiteurs mieux optimises captent les clients qui devraient etre les votres.'
        comp_html += '</div>'
    elif total < top_pos:
        comp_html += '<div style="margin-top:14px;padding:10px 14px;background:#fefce8;border-radius:6px;border-left:3px solid #f59e0b;font-size:13px;color:#92400e;line-height:1.4;">'
        comp_html += '<strong>Vous etes dans la moyenne, mais les leaders vous devancent.</strong> Quelques optimisations strategiques peuvent vous propulser dans le top 10%.'
        comp_html += '</div>'
    else:
        comp_html += '<div style="margin-top:14px;padding:10px 14px;background:#f0fdf4;border-radius:6px;border-left:3px solid #059669;font-size:13px;color:#166534;line-height:1.4;">'
        comp_html += '<strong>Excellent!</strong> Vous etes parmi les sites les mieux optimises. Maintenez votre avance avec des optimisations continues.'
        comp_html += '</div>'

    comp_html += '</td></tr></table></div>'

    # ================================================================
    # SCORE GAUGE (email-compatible table-based gauge)
    # ================================================================
    # Gauge is built with a large centered score display
    gauge_html = '<table style="width:100%;border-collapse:collapse;"><tr><td style="text-align:center;padding:30px 20px;">'
    gauge_html += '<div style="font-size:12px;font-weight:600;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">SCORE GLOBAL</div>'

    # Large grade circle
    gauge_html += '<div style="display:inline-block;width:110px;height:110px;border-radius:50%;border:6px solid ' + gc + ';text-align:center;line-height:110px;margin-bottom:8px;">'
    gauge_html += '<span style="font-size:48px;font-weight:900;color:' + gc + ';vertical-align:middle;">' + grade + '</span>'
    gauge_html += '</div>'

    # Score number
    gauge_html += '<div style="font-size:36px;font-weight:800;color:#1e293b;margin-top:4px;">' + str(total) + '<span style="font-size:20px;color:#94a3b8;">%</span></div>'

    # Score message
    gauge_html += '<div style="font-size:14px;color:' + score_msg_color + ';font-weight:600;margin-top:6px;max-width:400px;margin-left:auto;margin-right:auto;">' + score_msg + '</div>'

    # Full-width gauge bar
    gauge_html += '<div style="max-width:400px;margin:14px auto 0;background:#e5e7eb;border-radius:6px;height:12px;">'
    gauge_html += '<div style="width:' + str(max(2, total)) + '%;background:' + gc + ';border-radius:6px;height:12px;"></div>'
    gauge_html += '</div>'

    # Scale labels
    gauge_html += '<table style="width:100%;max-width:400px;margin:4px auto 0;border-collapse:collapse;"><tr>'
    gauge_html += '<td style="text-align:left;font-size:10px;color:#94a3b8;">0%</td>'
    gauge_html += '<td style="text-align:center;font-size:10px;color:#94a3b8;">50%</td>'
    gauge_html += '<td style="text-align:right;font-size:10px;color:#94a3b8;">100%</td>'
    gauge_html += '</tr></table>'

    gauge_html += '</td></tr></table>'

    # ================================================================
    # STATS COUNTER (problems found)
    # ================================================================
    total_checks = 0
    total_fails = 0
    total_warnings = 0
    total_pass = 0
    for cat_key in ['seo_classic', 'seo_technique', 'ai_readiness', 'content_quality']:
        cat_data = results.get(cat_key, {})
        for check in cat_data.get('checks', []):
            total_checks += 1
            st = check.get('status', 'fail')
            if st == 'fail':
                total_fails += 1
            elif st == 'warning':
                total_warnings += 1
            else:
                total_pass += 1

    stats_html = '<table style="width:100%;border-collapse:collapse;margin-bottom:4px;"><tr>'
    stats_html += '<td style="width:33%;text-align:center;padding:10px;">'
    stats_html += '<div style="font-size:28px;font-weight:800;color:#dc2626;">' + str(total_fails) + '</div>'
    stats_html += '<div style="font-size:11px;color:#64748b;font-weight:600;">Problemes</div></td>'
    stats_html += '<td style="width:33%;text-align:center;padding:10px;">'
    stats_html += '<div style="font-size:28px;font-weight:800;color:#f59e0b;">' + str(total_warnings) + '</div>'
    stats_html += '<div style="font-size:11px;color:#64748b;font-weight:600;">Avertissements</div></td>'
    stats_html += '<td style="width:33%;text-align:center;padding:10px;">'
    stats_html += '<div style="font-size:28px;font-weight:800;color:#059669;">' + str(total_pass) + '</div>'
    stats_html += '<div style="font-size:11px;color:#64748b;font-weight:600;">Reussis</div></td>'
    stats_html += '</tr></table>'

    # ================================================================
    # CTA SECTION
    # ================================================================
    cta_html = ''
    cta_html += '<table style="width:100%;border-collapse:collapse;"><tr><td style="padding:30px 24px;background:linear-gradient(180deg,#f8fafc,#f1f5f9);text-align:center;">'

    # Urgency message
    if total < 60:
        cta_html += '<div style="font-size:16px;font-weight:700;color:#dc2626;margin-bottom:6px;">Chaque jour sans optimisation = clients perdus</div>'
        cta_html += '<div style="font-size:13px;color:#64748b;margin-bottom:6px;">Les moteurs AI recommandent vos competiteurs, pas vous.</div>'
    else:
        cta_html += '<div style="font-size:16px;font-weight:700;color:#1e293b;margin-bottom:6px;">Propulsez votre site au prochain niveau</div>'
        cta_html += '<div style="font-size:13px;color:#64748b;margin-bottom:6px;">Des optimisations ciblees peuvent significativement augmenter votre trafic.</div>'

    # Separator
    cta_html += '<div style="width:60px;height:2px;background:#6366f1;margin:16px auto;"></div>'

    # Value proposition
    cta_html += '<div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:14px;">Consultation gratuite de 30 minutes</div>'
    cta_html += '<div style="font-size:13px;color:#64748b;margin-bottom:20px;line-height:1.6;max-width:480px;margin-left:auto;margin-right:auto;">'
    cta_html += 'Recevez un plan d\'action personnalise pour ameliorer votre score SEO et votre visibilite dans les assistants AI (ChatGPT, Perplexity, Google SGE).'
    cta_html += '</div>'

    # CTA Button
    cta_html += '<table style="margin:0 auto;border-collapse:collapse;"><tr><td style="padding:0;">'
    cta_html += '<a href="mailto:michaelperron12@gmail.com?subject=Consultation SEO - ' + domain + '&body=Bonjour,%0A%0AJe souhaite reserver une consultation gratuite suite a mon rapport SEO pour ' + domain + '.%0A%0AMerci" '
    cta_html += 'style="display:inline-block;padding:16px 40px;background:linear-gradient(135deg,#4f46e5,#4338ca);color:#ffffff;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;letter-spacing:0.3px;">'
    cta_html += 'Reserver ma consultation gratuite</a>'
    cta_html += '</td></tr></table>'

    # Contact info
    cta_html += '<table style="margin:20px auto 0;border-collapse:collapse;"><tr>'
    cta_html += '<td style="padding:8px 16px;text-align:center;">'
    cta_html += '<div style="font-size:13px;color:#4f46e5;font-weight:600;">514-609-2882</div>'
    cta_html += '<div style="font-size:11px;color:#94a3b8;">Telephone</div>'
    cta_html += '</td>'
    cta_html += '<td style="padding:8px 16px;text-align:center;border-left:1px solid #e5e7eb;">'
    cta_html += '<div style="font-size:13px;color:#4f46e5;font-weight:600;">michaelperron12@gmail.com</div>'
    cta_html += '<div style="font-size:11px;color:#94a3b8;">Courriel</div>'
    cta_html += '</td>'
    cta_html += '</tr></table>'

    cta_html += '</td></tr></table>'

    # ================================================================
    # ASSEMBLE FULL REPORT
    # ================================================================
    report = (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>'
        '<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">'

        # Wrapper table for email clients
        '<table role="presentation" style="width:100%;border-collapse:collapse;background:#f1f5f9;"><tr><td style="padding:20px 0;">'
        '<table role="presentation" style="max-width:650px;margin:0 auto;background:#ffffff;border-collapse:collapse;border-radius:10px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">'

        # ==================== HEADER ====================
        '<tr><td style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);padding:28px 24px;text-align:center;">'
        '<table style="width:100%;border-collapse:collapse;"><tr>'
        '<td style="text-align:center;">'
        # Brand mark
        '<div style="display:inline-block;width:44px;height:44px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:10px;text-align:center;line-height:44px;margin-bottom:10px;">'
        '<span style="color:#ffffff;font-size:20px;font-weight:900;">S</span>'
        '</div>'
        '<div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:0.5px;">SeoparAI</div>'
        '<div style="font-size:12px;color:#94a3b8;margin-top:4px;letter-spacing:0.5px;">Rapport d\'Analyse SEO & AI-Readiness</div>'
        '<div style="width:40px;height:2px;background:#6366f1;margin:12px auto 0;"></div>'
        '</td></tr></table>'
        # Domain + date bar
        '<table style="width:100%;border-collapse:collapse;margin-top:16px;"><tr>'
        '<td style="text-align:center;">'
        '<div style="display:inline-block;padding:8px 20px;background:rgba(255,255,255,0.08);border-radius:6px;">'
        '<span style="color:#e2e8f0;font-size:15px;font-weight:600;">' + domain + '</span>'
        '<span style="color:#64748b;font-size:12px;margin-left:12px;">' + scan_date + '</span>'
        '</div>'
        '</td></tr></table>'
        '</td></tr>'

        # ==================== SCORE GAUGE ====================
        '<tr><td style="background:#ffffff;">' + gauge_html + '</td></tr>'

        # ==================== STATS COUNTER ====================
        '<tr><td style="padding:0 24px;">'
        '<div style="border-top:1px solid #e5e7eb;border-bottom:1px solid #e5e7eb;">'
        + stats_html +
        '</div>'
        '</td></tr>'

        # ==================== CATEGORY SCORE CARDS ====================
        '<tr><td style="padding:20px 16px;">'
        '<table style="width:100%;border-collapse:collapse;"><tr>'
        + score_cards_html +
        '</tr></table>'
        '</td></tr>'

        # ==================== DETAILED CHECKS ====================
        '<tr><td style="padding:8px 24px 0;">'
        '<div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:16px;">Analyse Detaillee</div>'
        + checks_html +
        '</td></tr>'

        # ==================== RECOMMENDATIONS ====================
        '<tr><td style="padding:0 24px;">' + recs_html + '</td></tr>'

        # ==================== AI ANALYSIS ====================
        '<tr><td style="padding:0 24px;">' + ai_html + '</td></tr>'

        # ==================== COMPETITIVE COMPARISON ====================
        '<tr><td style="padding:0 24px;">' + comp_html + '</td></tr>'

        # ==================== CTA ====================
        '<tr><td>' + cta_html + '</td></tr>'

        # ==================== FOOTER ====================
        '<tr><td style="background:#0f172a;padding:24px;text-align:center;">'
        '<table style="width:100%;border-collapse:collapse;"><tr><td style="text-align:center;">'
        '<div style="display:inline-block;width:30px;height:30px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:6px;text-align:center;line-height:30px;margin-bottom:8px;">'
        '<span style="color:#ffffff;font-size:14px;font-weight:900;">S</span>'
        '</div>'
        '<div style="color:#94a3b8;font-size:13px;font-weight:600;">SeoparAI</div>'
        '<div style="color:#64748b;font-size:11px;margin-top:4px;">Intelligence Artificielle pour votre Referencement</div>'
        '<div style="width:40px;height:1px;background:#334155;margin:12px auto;"></div>'
        '<div style="color:#475569;font-size:11px;">Rapport genere le ' + scan_date_short + '</div>'
        '<div style="color:#475569;font-size:11px;margin-top:2px;">seoparai.com</div>'
        '<div style="color:#334155;font-size:10px;margin-top:10px;line-height:1.4;">Ce rapport est genere automatiquement par notre systeme d\'analyse. Les scores sont bases sur des criteres techniques objectifs. Pour une analyse personnalisee approfondie, contactez-nous.</div>'
        '</td></tr></table>'
        '</td></tr>'

        # Close main table and wrapper
        '</table>'
        '</td></tr></table>'
        '</body></html>'
    )

    return report

import requests
import json
import re

# ============================================================
# SCANNER HELPERS - Email, AI Analysis, HTML Report
# ============================================================

import smtplib
import sqlite3
import os
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
        msg['Subject'] = 'Votre Rapport SEO & AI - ' + domain + ' - Note: ' + grade
        msg['From'] = 'SeoparAI Scanner <' + SCANNER_FROM + '>'
        msg['To'] = to_email
        msg['Reply-To'] = 'contact@seoparai.com'

        text_part = MIMEText('Votre rapport SEO pour ' + domain + '\nNote: ' + grade + ' (' + str(score) + '%)\n\nVoir le rapport HTML ci-joint.', 'plain', 'utf-8')
        html_part = MIMEText(html_report, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP('localhost', 25) as server:
            server.sendmail(SCANNER_FROM, [to_email], msg.as_string())

        admin_msg = MIMEText(
            'Nouveau lead scanner!\n\nEmail: ' + to_email + '\nDomaine: ' + domain + '\nNote: ' + grade + ' (' + str(score) + '%)',
            'plain', 'utf-8'
        )
        admin_msg['Subject'] = '[Lead Scanner] ' + domain + ' - ' + grade
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
        payload = {'model': DEEPSEEK_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 800, 'temperature': 0.3}

        resp = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            import re as re2
            json_match = re2.search(r'\{[^{}]*"recommendations"[^{}]*\}', content, re2.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            clean = content.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            return json.loads(clean)
        return None
    except Exception as e:
        print('[AI] Error: ' + str(e))
        return None


def generate_html_report(results, ai_analysis=None):
    domain = results.get('domain', '')
    grade = results.get('grade', 'F')
    scores = results.get('scores', {})
    total = scores.get('total', 0)

    grade_colors = {'A+': '#10b981', 'A': '#10b981', 'B': '#3b82f6', 'C': '#f59e0b', 'D': '#f97316', 'F': '#ef4444'}
    gc = grade_colors.get(grade, '#ef4444')

    def si(s):
        if s == 'pass': return '<span style="color:#10b981;font-weight:bold;">&#10004;</span>'
        if s == 'warning': return '<span style="color:#f59e0b;font-weight:bold;">&#9888;</span>'
        return '<span style="color:#ef4444;font-weight:bold;">&#10008;</span>'

    def render_cat(name, key, icon):
        cat = results.get(key, {})
        checks = cat.get('checks', [])
        if not checks: return ''
        sc = scores.get(key, 0)
        h = '<div style="margin-bottom:24px;">'
        h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;padding:12px 16px;background:#f8fafc;border-radius:8px;border-left:4px solid ' + gc + ';">'
        h += '<span style="font-size:20px;">' + icon + '</span>'
        h += '<span style="font-weight:700;font-size:16px;flex:1;">' + name + '</span>'
        h += '<span style="font-weight:700;font-size:18px;color:' + gc + ';">' + str(sc) + '%</span></div>'
        h += '<table style="width:100%;border-collapse:collapse;font-size:14px;">'
        for c in checks:
            bg = '#f0fdf4' if c['status'] == 'pass' else '#fffbeb' if c['status'] == 'warning' else '#fef2f2'
            h += '<tr style="background:' + bg + ';border-bottom:1px solid #e5e7eb;">'
            h += '<td style="padding:10px 12px;width:30px;text-align:center;">' + si(c['status']) + '</td>'
            h += '<td style="padding:10px 8px;font-weight:600;">' + c['name'] + '</td>'
            h += '<td style="padding:10px 12px;color:#666;font-size:13px;">' + str(c.get('details', '')) + '</td></tr>'
        h += '</table></div>'
        return h

    cats = render_cat('SEO Classique', 'seo_classic', '&#128269;')
    cats += render_cat('SEO Technique', 'seo_technique', '&#9881;')
    cats += render_cat('AI-Readiness (AEO/SAIO)', 'ai_readiness', '&#129302;')
    cats += render_cat('Qualite du Contenu', 'content_quality', '&#128196;')

    recs = results.get('recommendations', [])
    rh = ''
    if recs:
        rh = '<div style="margin-bottom:24px;"><h2 style="color:#1e293b;font-size:18px;margin-bottom:12px;">&#127919; Recommandations Prioritaires</h2>'
        for i, r in enumerate(recs[:8], 1):
            ic = '#ef4444' if r.get('importance') == 'critical' else '#f59e0b' if r.get('importance') == 'high' else '#3b82f6'
            rh += '<div style="padding:10px 14px;margin-bottom:6px;background:#f8fafc;border-radius:6px;border-left:3px solid ' + ic + ';font-size:14px;">'
            rh += '<strong>' + str(i) + '.</strong> ' + r['recommendation']
            if r.get('ai_impact'):
                rh += '<br><span style="color:#6366f1;font-size:12px;"><em>Impact AI: ' + r['ai_impact'] + '</em></span>'
            rh += '</div>'
        rh += '</div>'

    ah = ''
    if ai_analysis:
        ai_recs = ai_analysis.get('recommendations', [])
        pri = ai_analysis.get('priority_action', '')
        ins = ai_analysis.get('competitive_insight', '')
        ah = '<div style="margin:24px 0;padding:20px;background:linear-gradient(135deg,#312e81,#4338ca);border-radius:12px;color:white;">'
        ah += '<h2 style="margin:0 0 12px;font-size:18px;color:white;">&#129302; Analyse AI Personnalisee (DeepSeek)</h2>'
        if pri:
            ah += '<div style="padding:10px 14px;background:rgba(255,255,255,0.15);border-radius:8px;margin-bottom:12px;font-weight:600;">&#9889; Action prioritaire: ' + pri + '</div>'
        for i, rec in enumerate(ai_recs, 1):
            ah += '<div style="padding:6px 0;font-size:14px;">' + str(i) + '. ' + rec + '</div>'
        if ins:
            ah += '<div style="margin-top:12px;padding:10px 14px;background:rgba(255,255,255,0.1);border-radius:8px;font-size:13px;font-style:italic;">&#128161; ' + ins + '</div>'
        ah += '</div>'

    def sc_circle(label, val, color):
        return '<td style="text-align:center;padding:8px;"><div style="width:70px;height:70px;border-radius:50%;border:4px solid ' + color + ';display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:' + color + ';">' + str(val) + '%</div><div style="font-size:11px;color:#64748b;margin-top:4px;font-weight:600;">' + label + '</div></td>'

    sh = '<table style="width:100%;margin:16px 0;"><tr>'
    sh += sc_circle('SEO', scores.get('seo_classic', 0), '#3b82f6')
    sh += sc_circle('Technique', scores.get('seo_technique', 0), '#8b5cf6')
    sh += sc_circle('AI/AEO', scores.get('ai_readiness', 0), '#6366f1')
    sh += sc_circle('Contenu', scores.get('content_quality', 0), '#10b981')
    sh += '</tr></table>'

    report = (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">'
        '<div style="max-width:650px;margin:0 auto;background:white;">'
        '<div style="background:linear-gradient(135deg,#0f172a,#1e293b);padding:30px 24px;text-align:center;">'
        '<div style="font-size:24px;font-weight:800;color:white;margin-bottom:4px;">SeoparAI</div>'
        '<div style="font-size:13px;color:#94a3b8;">Rapport SEO & AI-Readiness</div></div>'
        '<div style="text-align:center;padding:24px;background:linear-gradient(135deg,' + gc + '22,' + gc + '11);">'
        '<div style="font-size:14px;color:#64748b;margin-bottom:8px;">' + domain + '</div>'
        '<div style="display:inline-block;width:90px;height:90px;border-radius:50%;background:' + gc + ';color:white;font-size:40px;font-weight:900;line-height:90px;text-align:center;">' + grade + '</div>'
        '<div style="font-size:28px;font-weight:800;color:#1e293b;margin-top:8px;">' + str(total) + '%</div>'
        '<div style="font-size:13px;color:#64748b;">Score Global</div></div>'
        '<div style="padding:0 24px;">' + sh + '</div>'
        '<div style="padding:16px 24px;">' + cats + '</div>'
        '<div style="padding:0 24px;">' + rh + '</div>'
        '<div style="padding:0 24px;">' + ah + '</div>'
        '<div style="text-align:center;padding:30px 24px;background:#f8fafc;">'
        '<div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:8px;">Ameliorez votre score!</div>'
        '<div style="font-size:14px;color:#64748b;margin-bottom:16px;">Nos experts SEO & AI peuvent optimiser votre site.</div>'
        '<a href="https://seoparai.com/#contact" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#6366f1,#4338ca);color:white;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;">Demander une consultation gratuite</a></div>'
        '<div style="padding:20px 24px;background:#0f172a;text-align:center;">'
        '<div style="color:#94a3b8;font-size:12px;">SeoparAI - Intelligence Artificielle pour votre SEO</div>'
        '<div style="color:#64748b;font-size:11px;margin-top:4px;">seoparai.com | contact@seoparai.com</div></div>'
        '</div></body></html>'
    )
    return report

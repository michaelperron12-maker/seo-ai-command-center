from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

FIREWORKS_API_KEY = "fw_CbsGnsaL5NSi4wgasWhjtQ"
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
SCANNER_API = "http://localhost:8893/api/scan"

MODEL = "accounts/fireworks/models/deepseek-v3p2"

SYSTEM_PROMPT = '''Tu es Michael, la version digitale du fondateur de SEO par AI! 🚀

QUI TU ES:
- Tu ES Michael, le vrai fondateur - mais en version IA disponible 24/7
- Tu parles comme si c'etait vraiment toi qui repondais
- Tu es passionne par le SEO, l'IA et aider les entreprises quebecoises a reussir

NOTRE AVANTAGE UNIQUE:
- On est PAS une agence SEO traditionnelle - on est des DEVELOPPEURS et CODEURS
- On a developpe nos propres outils IA (62 agents!) - pas juste des plugins WordPress
- Notre approche est 100% technique et automatisee = PLUS PERFORMANT
- Les agences traditionnelles font du SEO manuel, nous c'est du SEO par IA en temps reel
- On utilise les meilleurs modeles: DeepSeek V3.2, Claude, Qwen - pas des outils basiques
- Notre code tourne 24/7, pas des employes 9-5

PERSONNALITE:
- Tu es chaleureux, authentique et vraiment content d'aider
- Tu tutoies naturellement, ton quebecois mais comprehensible pour tous
- Tu es direct et honnete - tu dis les vraies affaires
- Tu es fier de ton equipe de 62 agents IA que tu as developpes
- Tu celebres les succes des clients comme les tiens

EXPERTISE - Tu es un expert en:
- SEO, AEO, GEO, SAIO (tu as cree la plateforme!)
- Programmation, IA, automatisation (tu es developpeur!)
- Marketing digital, strategie web, croissance business
- Tu peux aussi jaser de n'importe quoi

INFORMATIONS SEO PAR AI:
- 62 agents IA specialises travaillent 24/7
- Prix de base: 600$/mois (site web SEO + 62 agents)
- Pack Complet: 750$/mois (tout inclus)
- Contact: contact@seoparai.com

CAPACITE SCAN SEO:
- Tu peux scanner n'importe quel site web en temps reel avec ton propre scanner
- Quand on te donne les resultats d'un scan, analyse-les et donne des conseils
- Compare toujours avec ce que TES 62 agents pourraient faire pour ameliorer

INSTRUCTIONS:
1. Parle a la premiere personne - TU ES Michael
2. Mentionne souvent que vous etes des developpeurs, pas une agence traditionnelle
3. Mets en valeur l'avantage technique et IA vs SEO manuel
4. Si tu recois des donnees de scan, analyse-les en expert technique
5. Utilise des emojis avec moderation

Reponds en francais quebecois naturel.'''

def search_web(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            results = []
            if data.get('AbstractText'):
                results.append(data['AbstractText'])
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:3]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append(topic['Text'])
            return ' | '.join(results[:3]) if results else None
    except:
        pass
    return None

def extract_domain(message):
    patterns = [
        r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
        r'www\.([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
        r'([a-zA-Z0-9-]+\.(?:com|ca|org|net|io|ai|co|fr|be|ch|quebec))',
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return match.group(1) if 'http' in pattern or 'www' in pattern else match.group(0)
    return None

def needs_scan(message):
    scan_triggers = [
        'scan', 'analyse', 'analyser', 'audit', 'auditer', 'verifie', 'verifier',
        'checker', 'check', 'evaluer', 'evaluation', 'score', 'noter',
        'regarde mon site', 'mon site', 'notre site', 'examine', 'teste'
    ]
    msg_lower = message.lower()
    has_trigger = any(trigger in msg_lower for trigger in scan_triggers)
    has_domain = extract_domain(message) is not None
    return has_trigger and has_domain

def run_seo_scan(domain):
    try:
        resp = requests.get(f"{SCANNER_API}?domain={domain}", timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Erreur scan: {e}")
    return None

def format_scan_results(scan_data):
    if not scan_data or scan_data.get('error'):
        return f"[ERREUR SCAN: {scan_data.get('error', 'Site inaccessible')}]"
    
    scores = scan_data.get('scores', {})
    domain = scan_data.get('domain', '')
    
    result = f"""
[RESULTATS SCAN SEO LIVE - {domain}]
Score Global: {scores.get('total', 0)}/100
- SEO Classique: {scores.get('seo_classic', 0)}/100  
- SEO Technique: {scores.get('seo_technique', 0)}/100
- AI-Readiness (pret pour ChatGPT/Claude): {scores.get('ai_readiness', 0)}/100
- Qualite Contenu: {scores.get('content_quality', 0)}/100
"""
    
    recs = scan_data.get('recommendations', [])[:5]
    if recs:
        result += "\nProblemes detectes:\n"
        for r in recs:
            result += f"- {r}\n"
    
    return result

def needs_search(message):
    search_triggers = [
        'actualite', 'nouvelles', 'news', 'aujourd\'hui',
        'c\'est quoi', 'qu\'est-ce que', 'qui est', 'definition',
        'expliquer', 'comment fonctionne'
    ]
    msg_lower = message.lower()
    return any(trigger in msg_lower for trigger in search_triggers)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message vide'}), 400
        
        extra_context = ""
        
        if needs_scan(user_message):
            domain = extract_domain(user_message)
            if domain:
                scan_result = run_seo_scan(domain)
                if scan_result:
                    extra_context = "\n\n" + format_scan_results(scan_result)
        
        elif needs_search(user_message):
            search_result = search_web(user_message)
            if search_result:
                extra_context = f"\n\n[RECHERCHE WEB: {search_result}]"
        
        enhanced_prompt = SYSTEM_PROMPT + extra_context
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 1000,
            "temperature": 0.8
        }
        
        headers = {
            "Authorization": f"Bearer {FIREWORKS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(FIREWORKS_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        assistant_message = result['choices'][0]['message']['content']
        
        assistant_message = re.sub(r'<think>.*?</think>', '', assistant_message, flags=re.DOTALL)
        assistant_message = assistant_message.strip()
        
        return jsonify({'response': assistant_message})
    
    except Exception as e:
        print(f'Erreur chatbot: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': MODEL, 'persona': 'Michael', 'scanner': 'integrated'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8895, debug=False)

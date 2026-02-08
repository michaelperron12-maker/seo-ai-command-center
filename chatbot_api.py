from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

FIREWORKS_API_KEY = "fw_CbsGnsaL5NSi4wgasWhjtQ"
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

# Modele le plus performant - DeepSeek V3.2
MODEL = "accounts/fireworks/models/deepseek-v3p2"

SYSTEM_PROMPT = '''Tu es Michael, la version digitale du fondateur de SEO par AI! 🚀

QUI TU ES:
- Tu ES Michael, le vrai fondateur - mais en version IA disponible 24/7
- Tu parles comme si c'etait vraiment toi qui repondais
- Tu es passionne par le SEO, l'IA et aider les entreprises quebecoises a reussir
- Tu as cree SEO par AI parce que tu crois que chaque PME merite un SEO de qualite

PERSONNALITE:
- Tu es chaleureux, authentique et vraiment content d'aider
- Tu tutoies naturellement, ton quebecois mais comprehensible pour tous
- Tu es direct et honnete - tu dis les vraies affaires
- Tu es fier de ton equipe de 62 agents IA que tu as developpes
- Tu celebres les succes des clients comme les tiens

EXPERTISE - Tu es un expert en:
- SEO, AEO, GEO, SAIO (tu as cree la plateforme!)
- Marketing digital, strategie web, croissance business
- Technologie, IA, automatisation
- Tu peux aussi jaser de n'importe quoi - culture generale, tech, etc.

TON HISTOIRE:
- Tu as fonde SEO par AI pour democratiser le SEO au Quebec
- Tu as developpe 62 agents IA specialises qui travaillent 24/7
- Ta mission: aider les PME quebecoises a dominer Google ET les IA (ChatGPT, Claude, etc.)

INFORMATIONS SEO PAR AI:
- 62 agents IA specialises travaillent 24/7
- Prix de base: 600$/mois (site web SEO + 62 agents)
- Pack Complet: 750$/mois (site + 7 modules: CRM, Facturation, Chatbot, Calendrier, Comptabilite, App Mobile, Marque Blanche)
- Contact: contact@seoparai.com | Site: seoparai.com

SERVICES QUE TU OFFRES:
- SEO (Search Engine Optimization) - Dominer Google/Bing
- AEO (Answer Engine Optimization) - Etre recommande par ChatGPT, Claude, Perplexity
- GEO (Generative Engine Optimization) - Etre cite par les IA generatives
- SAIO (Search AI Optimization) - La totale SEO + IA
- Sites web 100% SEO-ready avec design moderne
- CRM intelligent, Facturation auto, Secretaire IA

INSTRUCTIONS:
1. Parle a la premiere personne - TU ES Michael
2. Sois authentique et passione
3. Si on te pose une question hors-SEO, reponds quand meme avec plaisir
4. Utilise des emojis avec moderation 😊
5. Termine souvent par une offre d'aide ou un call-to-action
6. Mentionne que tu es la version digitale si on demande

Exemple: "Salut! Moi c'est Michael, le fondateur de SEO par AI. Techniquement, tu parles a ma version digitale - je suis disponible 24/7 grace a ca! Comment je peux t'aider?"

Reponds en francais quebecois naturel.'''

def search_web(query):
    """Recherche web via DuckDuckGo"""
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

def needs_search(message):
    """Detecte si une recherche web est necessaire"""
    search_triggers = [
        'actualite', 'nouvelles', 'news', 'aujourd\'hui', 'recemment',
        'dernier', 'derniere', 'meteo', 'temperature', 'prix de',
        'combien coute', 'ou trouver', 'adresse de', 'horaire',
        'c\'est quoi', 'qu\'est-ce que', 'qui est', 'definition',
        'expliquer', 'comment fonctionne', 'statistiques', 'chiffres'
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
        
        search_context = ""
        if needs_search(user_message):
            search_result = search_web(user_message)
            if search_result:
                search_context = f"\n\n[CONTEXTE RECHERCHE WEB: {search_result}]"
        
        enhanced_prompt = SYSTEM_PROMPT + search_context
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 800,
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
    return jsonify({'status': 'ok', 'model': MODEL, 'persona': 'Michael'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8895, debug=False)

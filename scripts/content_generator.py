#!/usr/bin/env python3
"""
Content Generator - Générateur de contenu SEO
Utilise Claude ou OpenAI pour générer des articles optimisés SEO
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import random
import time
import yaml

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/seo-agent/content.log', mode='a')
    ]
)
logger = logging.getLogger('ContentGenerator')

# Chemins par défaut
TEMPLATES_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/templates/'


@dataclass
class GeneratedContent:
    """Structure pour le contenu généré."""
    title: str
    slug: str
    html: str
    markdown: str
    meta_description: str
    keywords: list
    word_count: int
    generated_at: str


class ContentGenerator:
    """
    Générateur de contenu SEO utilisant des LLMs.
    Supporte Claude (Anthropic) et OpenAI.
    """

    def __init__(self, provider: str = 'claude'):
        """
        Initialise le générateur de contenu.

        Args:
            provider: 'claude' ou 'openai'
        """
        self.provider = provider
        self.client = None
        self.template = None

        # Initialiser le client API
        self._init_client()

        # Charger le template
        self._load_template()

        logger.info(f"ContentGenerator initialisé avec provider: {provider}")

    def _init_client(self) -> None:
        """Initialise le client API selon le provider."""
        try:
            if self.provider == 'claude':
                import anthropic
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    logger.warning("ANTHROPIC_API_KEY non définie")
                self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
                self.model = os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229')

            elif self.provider == 'openai':
                import openai
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.warning("OPENAI_API_KEY non définie")
                self.client = openai.OpenAI(api_key=api_key) if api_key else None
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')

            else:
                raise ValueError(f"Provider non supporté: {self.provider}")

        except ImportError as e:
            logger.error(f"Module non installé pour {self.provider}: {e}")
            self.client = None

    def _load_template(self) -> None:
        """Charge le template Safe Stack pour les articles."""
        template_file = os.path.join(TEMPLATES_PATH, 'article_template.html')

        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                self.template = f.read()
            logger.info("Template article chargé")
        else:
            logger.warning("Template non trouvé, utilisation du template par défaut")
            self.template = self._get_default_template()

    def _get_default_template(self) -> str:
        """Retourne le template HTML par défaut."""
        return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{{META_DESCRIPTION}}">
    <meta name="keywords" content="{{KEYWORDS}}">
    <title>{{TITLE}}</title>
    <link rel="canonical" href="{{CANONICAL_URL}}">

    <!-- Open Graph -->
    <meta property="og:title" content="{{TITLE}}">
    <meta property="og:description" content="{{META_DESCRIPTION}}">
    <meta property="og:type" content="article">

    <!-- Schema.org -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{{TITLE}}",
        "description": "{{META_DESCRIPTION}}",
        "datePublished": "{{DATE_PUBLISHED}}",
        "author": {
            "@type": "Organization",
            "name": "{{SITE_NAME}}"
        }
    }
    </script>
</head>
<body>
    <article>
        <header>
            <h1>{{TITLE}}</h1>
            <time datetime="{{DATE_PUBLISHED}}">{{DATE_FORMATTED}}</time>
        </header>

        <main class="content">
            {{CONTENT}}
        </main>

        <footer>
            <p>Mots-clés: {{KEYWORDS}}</p>
        </footer>
    </article>
</body>
</html>'''

    def _generate_system_prompt(self) -> str:
        """Génère le prompt système pour la génération de contenu."""
        return """Tu es un expert en rédaction SEO. Tu dois générer des articles optimisés pour le référencement naturel.

Règles à suivre:
1. Structure claire avec H1, H2, H3
2. Introduction accrocheuse avec le mot-clé principal
3. Paragraphes courts (3-4 phrases max)
4. Utilisation naturelle des mots-clés (densité 1-2%)
5. Listes à puces pour la lisibilité
6. Conclusion avec appel à l'action
7. Meta description de 150-160 caractères
8. Contenu original et informatif
9. Ton professionnel mais accessible
10. Minimum 800 mots, idéalement 1200-1500

Format de sortie JSON:
{
    "title": "Titre H1 optimisé SEO",
    "slug": "titre-url-friendly",
    "meta_description": "Description meta de 150-160 caractères",
    "keywords": ["mot-clé1", "mot-clé2", "mot-clé3"],
    "content_html": "<article>Contenu HTML complet</article>",
    "content_md": "# Contenu en Markdown"
}"""

    def generate(self, brief: str, keywords: list = None) -> Dict:
        """
        Génère un article SEO à partir d'un brief.

        Args:
            brief: Description du sujet à traiter
            keywords: Liste de mots-clés à inclure (optionnel)

        Returns:
            Dict avec le contenu généré ou erreur
        """
        if not brief:
            return {'success': False, 'error': 'Brief requis'}

        if not self.client:
            logger.warning("Pas de client API, génération simulée")
            return self._generate_mock_content(brief, keywords)

        try:
            # Construire le prompt utilisateur
            user_prompt = f"""Brief: {brief}

Mots-clés à intégrer: {', '.join(keywords) if keywords else 'À déterminer selon le sujet'}

Génère un article SEO complet en français. Réponds uniquement avec le JSON demandé."""

            # Appeler l'API
            if self.provider == 'claude':
                response = self._call_claude(user_prompt)
            else:
                response = self._call_openai(user_prompt)

            # Parser la réponse
            content = self._parse_response(response)

            if content:
                # Créer l'objet GeneratedContent
                generated = GeneratedContent(
                    title=content['title'],
                    slug=content['slug'],
                    html=self._apply_template(content),
                    markdown=content['content_md'],
                    meta_description=content['meta_description'],
                    keywords=content['keywords'],
                    word_count=len(content['content_md'].split()),
                    generated_at=datetime.now().isoformat()
                )

                logger.info(f"Contenu généré: {generated.title} ({generated.word_count} mots)")

                return {
                    'success': True,
                    'content': {
                        'title': generated.title,
                        'slug': generated.slug,
                        'html': generated.html,
                        'markdown': generated.markdown,
                        'meta_description': generated.meta_description,
                        'keywords': generated.keywords,
                        'word_count': generated.word_count,
                        'generated_at': generated.generated_at
                    }
                }
            else:
                return {'success': False, 'error': 'Impossible de parser la réponse'}

        except Exception as e:
            logger.error(f"Erreur génération: {e}")
            return {'success': False, 'error': str(e)}

    def _call_claude(self, prompt: str) -> str:
        """Appelle l'API Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._generate_system_prompt(),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Appelle l'API OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._generate_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096,
            temperature=0.7
        )
        return response.choices[0].message.content

    def _parse_response(self, response: str) -> Optional[Dict]:
        """Parse la réponse JSON du LLM."""
        try:
            # Extraire le JSON de la réponse
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            return None

    def _apply_template(self, content: Dict) -> str:
        """Applique le template HTML au contenu."""
        html = self.template

        replacements = {
            '{{TITLE}}': content['title'],
            '{{META_DESCRIPTION}}': content['meta_description'],
            '{{KEYWORDS}}': ', '.join(content['keywords']),
            '{{CONTENT}}': content['content_html'],
            '{{DATE_PUBLISHED}}': datetime.now().isoformat(),
            '{{DATE_FORMATTED}}': datetime.now().strftime('%d %B %Y'),
            '{{CANONICAL_URL}}': f"/blog/{content['slug']}/",
            '{{SITE_NAME}}': 'Safe Stack'
        }

        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))

        return html

    def _generate_mock_content(self, brief: str, keywords: list = None) -> Dict:
        """Génère du contenu de test (sans API)."""
        logger.info("Génération de contenu mock pour tests")

        # Créer un slug à partir du brief
        slug = re.sub(r'[^a-z0-9]+', '-', brief.lower())[:50].strip('-')

        mock_content = {
            'title': f"Guide complet: {brief[:50]}",
            'slug': slug,
            'content_html': f"""<article>
                <h1>Guide complet: {brief[:50]}</h1>
                <p>Introduction sur le sujet: {brief}</p>
                <h2>Pourquoi c'est important</h2>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                <h2>Comment procéder</h2>
                <ul>
                    <li>Étape 1: Analyse</li>
                    <li>Étape 2: Planification</li>
                    <li>Étape 3: Exécution</li>
                </ul>
                <h2>Conclusion</h2>
                <p>En résumé, {brief[:30]} est essentiel pour votre succès.</p>
            </article>""",
            'content_md': f"""# Guide complet: {brief[:50]}

Introduction sur le sujet: {brief}

## Pourquoi c'est important

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

## Comment procéder

- Étape 1: Analyse
- Étape 2: Planification
- Étape 3: Exécution

## Conclusion

En résumé, {brief[:30]} est essentiel pour votre succès.""",
            'meta_description': f"Découvrez notre guide complet sur {brief[:80]}. Conseils pratiques et stratégies efficaces.",
            'keywords': keywords or ['guide', 'conseils', 'stratégie']
        }

        html = self._apply_template(mock_content)

        return {
            'success': True,
            'content': {
                'title': mock_content['title'],
                'slug': mock_content['slug'],
                'html': html,
                'markdown': mock_content['content_md'],
                'meta_description': mock_content['meta_description'],
                'keywords': mock_content['keywords'],
                'word_count': len(mock_content['content_md'].split()),
                'generated_at': datetime.now().isoformat()
            },
            'mock': True
        }


def main():
    """Point d'entrée pour les tests standalone."""
    print("=== Test ContentGenerator ===\n")

    try:
        generator = ContentGenerator(provider='claude')

        # Test de génération
        brief = "Comment optimiser son site web pour le SEO en 2024"
        keywords = ["SEO", "optimisation", "référencement", "Google"]

        print(f"Brief: {brief}")
        print(f"Keywords: {keywords}")
        print("\nGénération en cours...\n")

        result = generator.generate(brief, keywords)

        if result['success']:
            content = result['content']
            print(f"Titre: {content['title']}")
            print(f"Slug: {content['slug']}")
            print(f"Meta: {content['meta_description']}")
            print(f"Mots: {content['word_count']}")
            print(f"Mock: {result.get('mock', False)}")
        else:
            print(f"Erreur: {result['error']}")

        print("\n=== Test terminé ===")

    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


# ============================================
# DÉLAI HUMAIN - Pour paraître naturel
# ============================================

def get_human_delay():
    """Retourne un délai aléatoire pour paraître humain (15-30 min)"""
    try:
        with open("/opt/seo-agent/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        min_delay = config.get("timing", {}).get("delai_generation_min", 900)
        max_delay = config.get("timing", {}).get("delai_generation_max", 1800)
    except:
        min_delay, max_delay = 900, 1800
    
    delay = random.randint(min_delay, max_delay)
    logger.info(f"[HUMAN] Attente de {delay//60} minutes pour paraître humain...")
    return delay

def wait_human_delay():
    """Attend un délai aléatoire avant de notifier"""
    delay = get_human_delay()
    time.sleep(delay)
    logger.info("[HUMAN] Délai terminé, prêt pour notification")
    return delay

def is_human_hour():
    """Vérifie si on est dans une heure de publication humaine"""
    try:
        with open("/opt/seo-agent/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        allowed_hours = config.get("timing", {}).get("heures_publication", [9, 10, 11, 14, 15, 16])
    except:
        allowed_hours = [9, 10, 11, 14, 15, 16]
    
    current_hour = datetime.now().hour
    return current_hour in allowed_hours

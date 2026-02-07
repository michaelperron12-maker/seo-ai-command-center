#!/usr/bin/env python3
"""
Research Agent - Recherche les meilleures pratiques web
Supporte les 3 sites: deneigement, paysagement, jcpeintre
"""

import os
import json
import sqlite3
import hashlib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

SITES = {
    "deneigement": {
        "domain": "deneigement-excellence.ca",
        "path": "/var/www/deneigement",
        "keywords": ["deneigement", "neige", "hiver", "Brossard", "Rive-Sud"]
    },
    "paysagement": {
        "domain": "paysagiste-excellence.ca",
        "path": "/var/www/paysagement",
        "keywords": ["paysagiste", "amenagement", "pelouse", "jardin"]
    },
    "jcpeintre": {
        "domain": "jcpeintre.com",
        "path": "/var/www/jcpeintre.com",
        "keywords": ["peintre", "peinture", "renovation", "Montreal"]
    }
}

class ResearchAgent:
    def __init__(self, db_path: str = "/opt/seo-agent/db/seo_agent.db"):
        self.db_path = db_path
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.cache_duration = timedelta(hours=24)
        self._init_db()

    def _init_db(self):
        """Initialise les tables pour la recherche"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS research_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                results TEXT,
                source TEXT,
                site_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS best_practices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                category TEXT,
                title TEXT,
                content TEXT,
                source_url TEXT,
                relevance_score REAL,
                applied BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS tech_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                technology TEXT,
                trend_type TEXT,
                description TEXT,
                impact_score REAL,
                applicable_sites TEXT,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_research_hash ON research_cache(query_hash);
            CREATE INDEX IF NOT EXISTS idx_practices_cat ON best_practices(category);
            CREATE INDEX IF NOT EXISTS idx_practices_site ON best_practices(site_id);
        """)
        conn.commit()
        conn.close()

    def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche via DuckDuckGo HTML"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            response = requests.get(url, headers=headers, timeout=10)

            results = []
            pattern = r'class="result__a" href="([^"]+)"[^>]*>([^<]+)<'
            matches = re.findall(pattern, response.text)

            for link, title in matches[:max_results]:
                results.append({"title": title.strip(), "url": link, "snippet": ""})

            return results
        except Exception as e:
            print(f"[ResearchAgent] Erreur DuckDuckGo: {e}")
            return []

    def fetch_page(self, url: str) -> Optional[str]:
        """Récupère le contenu texte d'une page"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; SEOAgent/1.0)"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            text = re.sub(r'<script[^>]*>.*?</script>', '', response.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            return text[:10000]
        except Exception as e:
            print(f"[ResearchAgent] Erreur fetch {url}: {e}")
            return None

    def analyze_with_claude(self, content: str, context: str) -> Optional[Dict]:
        """Analyse le contenu avec Claude"""
        if not self.api_key:
            return None

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 2000,
                    "messages": [{
                        "role": "user",
                        "content": f"""Analyse ce contenu pour: {context}

Contenu:
{content[:5000]}

Réponds en JSON valide:
{{
    "practices": [
        {{"titre": "...", "description": "...", "priorite": 1-5}}
    ],
    "technologies": ["..."],
    "actions": ["action concrete 1", "action concrete 2"]
}}"""
                    }]
                },
                timeout=30
            )
            response.raise_for_status()
            text = response.json()["content"][0]["text"]
            # Extraire le JSON
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
            return None
        except Exception as e:
            print(f"[ResearchAgent] Erreur Claude: {e}")
            return None

    def research_for_site(self, site_id: str, topic: str) -> Dict:
        """Recherche spécifique pour un site"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        site = SITES[site_id]
        query = f"{topic} {' '.join(site['keywords'][:2])}"
        query_hash = hashlib.md5(f"{site_id}:{query}".encode()).hexdigest()

        # Vérifier cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT results FROM research_cache
            WHERE query_hash = ? AND expires_at > datetime('now')
        """, (query_hash,))
        cached = cursor.fetchone()

        if cached:
            conn.close()
            return json.loads(cached[0])

        # Nouvelle recherche
        search_results = self.search_duckduckgo(query)
        findings = []

        for result in search_results[:3]:
            content = self.fetch_page(result["url"])
            if content:
                analysis = self.analyze_with_claude(content, f"{topic} pour {site['domain']}")
                if analysis:
                    findings.append({
                        "source": result["url"],
                        "title": result["title"],
                        "analysis": analysis
                    })

        final = {
            "site_id": site_id,
            "domain": site["domain"],
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "findings": findings
        }

        # Cache
        cursor.execute("""
            INSERT OR REPLACE INTO research_cache
            (query_hash, query, results, source, site_id, expires_at)
            VALUES (?, ?, ?, 'duckduckgo', ?, datetime('now', '+24 hours'))
        """, (query_hash, query, json.dumps(final), site_id))
        conn.commit()
        conn.close()

        return final

    def research_all_sites(self, topic: str) -> Dict:
        """Recherche pour tous les sites"""
        results = {}
        for site_id in SITES:
            results[site_id] = self.research_for_site(site_id, topic)
        return results

    def get_performance_research(self) -> Dict:
        """Recherche optimisation performance pour tous les sites"""
        topics = [
            "nginx performance optimization",
            "website speed Core Web Vitals",
            "image optimization lazy loading",
            "caching strategies"
        ]

        all_results = {"topics": {}, "timestamp": datetime.now().isoformat()}
        for topic in topics:
            all_results["topics"][topic] = self.research_all_sites(topic)

        return all_results

    def get_seo_research(self) -> Dict:
        """Recherche SEO pour tous les sites"""
        topics = [
            "local SEO optimization",
            "Google Business Profile optimization",
            "schema markup local business",
            "content optimization SEO"
        ]

        all_results = {"topics": {}, "timestamp": datetime.now().isoformat()}
        for topic in topics:
            all_results["topics"][topic] = self.research_all_sites(topic)

        return all_results

    def save_practice(self, site_id: str, category: str, title: str,
                      content: str, source_url: str, score: float):
        """Sauvegarde une bonne pratique"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO best_practices
            (site_id, category, title, content, source_url, relevance_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (site_id, category, title, content, source_url, score))
        conn.commit()
        conn.close()

    def get_practices(self, site_id: str = None, category: str = None) -> List[Dict]:
        """Récupère les bonnes pratiques"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT site_id, category, title, content, source_url, relevance_score, applied FROM best_practices WHERE 1=1"
        params = []

        if site_id:
            query += " AND site_id = ?"
            params.append(site_id)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY relevance_score DESC LIMIT 50"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            "site_id": r[0], "category": r[1], "title": r[2],
            "content": r[3], "source_url": r[4], "score": r[5], "applied": bool(r[6])
        } for r in rows]


if __name__ == "__main__":
    agent = ResearchAgent()
    print("=== Research Agent - 3 Sites ===")
    print(f"Sites: {list(SITES.keys())}")
    print("\nTest recherche performance...")
    for site_id in SITES:
        print(f"  - {site_id}: {SITES[site_id]['domain']}")
    print("\nAgent pret!")

#!/usr/bin/env python3
"""
Learning Agent - Apprentissage continu des meilleures pratiques
Analyse le code existant et suggère des améliorations
Supporte les 3 sites: deneigement, paysagement, jcpeintre
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import hashlib

SITES = {
    "deneigement": {
        "domain": "deneigement-excellence.ca",
        "path": "/var/www/deneigement",
        "tech_stack": ["html", "css", "javascript", "php"]
    },
    "paysagement": {
        "domain": "paysagiste-excellence.ca",
        "path": "/var/www/paysagement",
        "tech_stack": ["html", "css", "javascript", "php"]
    },
    "jcpeintre": {
        "domain": "jcpeintre.com",
        "path": "/var/www/jcpeintre.com",
        "tech_stack": ["html", "css", "javascript", "python", "flask"]
    }
}

class LearningAgent:
    def __init__(self, db_path: str = "/opt/seo-agent/db/seo_agent.db"):
        self.db_path = db_path
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self._init_db()

    def _init_db(self):
        """Initialise les tables d'apprentissage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS code_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                pattern_type TEXT,
                pattern_name TEXT,
                description TEXT,
                example_code TEXT,
                quality_score REAL,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS code_improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                file_path TEXT,
                improvement_type TEXT,
                current_code TEXT,
                suggested_code TEXT,
                reason TEXT,
                priority TEXT,
                applied BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS learning_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                source_url TEXT,
                topic TEXT,
                key_learnings TEXT,
                applicable_to TEXT,
                learned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS technology_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                technology TEXT,
                version_current TEXT,
                version_latest TEXT,
                update_notes TEXT,
                breaking_changes TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_patterns_site ON code_patterns(site_id);
            CREATE INDEX IF NOT EXISTS idx_improvements_site ON code_improvements(site_id);
        """)
        conn.commit()
        conn.close()

    def analyze_code_with_claude(self, code: str, file_type: str, context: str) -> Optional[Dict]:
        """Analyse du code avec Claude pour suggestions"""
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
                        "content": f"""Analyse ce code {file_type} et suggère des améliorations.
Contexte: {context}

Code:
```{file_type}
{code[:3000]}
```

Réponds en JSON:
{{
    "quality_score": 1-10,
    "patterns_detected": ["pattern1", "pattern2"],
    "improvements": [
        {{
            "type": "performance|security|readability|seo",
            "priority": "high|medium|low",
            "issue": "description du problème",
            "suggestion": "code ou action suggérée",
            "reason": "pourquoi c'est important"
        }}
    ],
    "best_practices_missing": ["practice1", "practice2"]
}}"""
                    }]
                },
                timeout=60
            )
            response.raise_for_status()
            text = response.json()["content"][0]["text"]
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
            return None
        except Exception as e:
            print(f"[LearningAgent] Erreur Claude: {e}")
            return None

    def scan_site_code(self, site_id: str) -> Dict:
        """Scanne et analyse le code d'un site"""
        if site_id not in SITES:
            return {"error": f"Site inconnu: {site_id}"}

        site = SITES[site_id]
        path = site["path"]
        results = {"site_id": site_id, "files_analyzed": 0, "improvements": [], "patterns": []}

        # Extensions à analyser
        extensions = {
            "html": [".html", ".htm"],
            "css": [".css"],
            "javascript": [".js"],
            "php": [".php"],
            "python": [".py"]
        }

        try:
            for root, dirs, files in os.walk(path):
                # Ignorer certains dossiers
                dirs[:] = [d for d in dirs if d not in ['node_modules', 'vendor', '.git', '__pycache__']]

                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()

                    # Trouver le type de fichier
                    file_type = None
                    for ftype, exts in extensions.items():
                        if ext in exts:
                            file_type = ftype
                            break

                    if not file_type:
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            code = f.read()

                        if len(code) < 100:  # Ignorer fichiers trop petits
                            continue

                        # Analyse basique sans API
                        basic_issues = self._basic_code_analysis(code, file_type, file_path)
                        results["improvements"].extend(basic_issues)
                        results["files_analyzed"] += 1

                    except Exception as e:
                        print(f"Erreur lecture {file_path}: {e}")

            return results
        except Exception as e:
            return {"error": str(e)}

    def _basic_code_analysis(self, code: str, file_type: str, file_path: str) -> List[Dict]:
        """Analyse basique du code sans API"""
        issues = []

        if file_type == "html":
            # Vérifications HTML
            if "<!DOCTYPE html>" not in code and "<!doctype html>" not in code:
                issues.append({
                    "file": file_path,
                    "type": "seo",
                    "priority": "medium",
                    "issue": "DOCTYPE manquant",
                    "suggestion": "Ajouter <!DOCTYPE html> au début"
                })

            if '<meta name="description"' not in code:
                issues.append({
                    "file": file_path,
                    "type": "seo",
                    "priority": "high",
                    "issue": "Meta description manquante",
                    "suggestion": "Ajouter <meta name=\"description\" content=\"...\">"
                })

            if 'loading="lazy"' not in code and '<img' in code:
                issues.append({
                    "file": file_path,
                    "type": "performance",
                    "priority": "medium",
                    "issue": "Lazy loading non utilisé pour images",
                    "suggestion": "Ajouter loading=\"lazy\" aux balises img"
                })

            if '<script' in code and 'defer' not in code and 'async' not in code:
                issues.append({
                    "file": file_path,
                    "type": "performance",
                    "priority": "medium",
                    "issue": "Scripts bloquants",
                    "suggestion": "Ajouter defer ou async aux scripts"
                })

        elif file_type == "css":
            if len(code) > 50000 and ".min" not in file_path:
                issues.append({
                    "file": file_path,
                    "type": "performance",
                    "priority": "high",
                    "issue": "CSS volumineux non minifié",
                    "suggestion": "Minifier le CSS"
                })

        elif file_type == "javascript":
            if "console.log" in code:
                issues.append({
                    "file": file_path,
                    "type": "readability",
                    "priority": "low",
                    "issue": "console.log en production",
                    "suggestion": "Retirer les console.log"
                })

            if "eval(" in code:
                issues.append({
                    "file": file_path,
                    "type": "security",
                    "priority": "high",
                    "issue": "Utilisation de eval()",
                    "suggestion": "Éviter eval() pour des raisons de sécurité"
                })

        elif file_type == "php":
            if "$_GET" in code or "$_POST" in code:
                if "htmlspecialchars" not in code and "filter_input" not in code:
                    issues.append({
                        "file": file_path,
                        "type": "security",
                        "priority": "high",
                        "issue": "Input non sanitizé",
                        "suggestion": "Utiliser htmlspecialchars() ou filter_input()"
                    })

        return issues

    def learn_from_url(self, url: str, topic: str) -> Dict:
        """Apprend depuis une ressource web"""
        try:
            response = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (compatible; LearningAgent/1.0)"
            })
            response.raise_for_status()

            # Extraire le texte
            text = re.sub(r'<script[^>]*>.*?</script>', '', response.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # Analyser avec Claude si disponible
            if self.api_key:
                analysis = self.analyze_with_claude_learning(text[:5000], topic)
                if analysis:
                    # Sauvegarder
                    self._save_learning(url, topic, analysis)
                    return {"status": "success", "learnings": analysis}

            return {"status": "fetched", "content_length": len(text)}
        except Exception as e:
            return {"error": str(e)}

    def analyze_with_claude_learning(self, content: str, topic: str) -> Optional[Dict]:
        """Extrait les apprentissages d'un contenu"""
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
                    "max_tokens": 1500,
                    "messages": [{
                        "role": "user",
                        "content": f"""Extrais les points clés de ce contenu sur: {topic}

Contenu:
{content}

Réponds en JSON:
{{
    "key_points": ["point 1", "point 2"],
    "actionable_items": ["action 1", "action 2"],
    "code_examples": ["exemple si applicable"],
    "relevance_score": 1-10
}}"""
                    }]
                },
                timeout=30
            )
            response.raise_for_status()
            text = response.json()["content"][0]["text"]
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
            return None
        except Exception as e:
            return None

    def _save_learning(self, url: str, topic: str, learnings: Dict):
        """Sauvegarde un apprentissage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO learning_sources (source_type, source_url, topic, key_learnings, applicable_to)
            VALUES ('web', ?, ?, ?, 'all')
        """, (url, topic, json.dumps(learnings)))
        conn.commit()
        conn.close()

    def save_improvement(self, site_id: str, file_path: str, improvement_type: str,
                         current_code: str, suggested_code: str, reason: str, priority: str):
        """Sauvegarde une suggestion d'amélioration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO code_improvements
            (site_id, file_path, improvement_type, current_code, suggested_code, reason, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (site_id, file_path, improvement_type, current_code, suggested_code, reason, priority))
        conn.commit()
        conn.close()

    def get_improvements(self, site_id: str = None, applied: bool = False) -> List[Dict]:
        """Récupère les améliorations suggérées"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT site_id, file_path, improvement_type, current_code, suggested_code, reason, priority, applied FROM code_improvements WHERE applied = ?"
        params = [1 if applied else 0]

        if site_id:
            query += " AND site_id = ?"
            params.append(site_id)

        query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            "site_id": r[0], "file_path": r[1], "improvement_type": r[2],
            "current_code": r[3], "suggested_code": r[4], "reason": r[5],
            "priority": r[6], "applied": bool(r[7])
        } for r in rows]

    def get_learnings(self, topic: str = None) -> List[Dict]:
        """Récupère les apprentissages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if topic:
            cursor.execute("""
                SELECT source_url, topic, key_learnings, learned_at
                FROM learning_sources WHERE topic LIKE ?
                ORDER BY learned_at DESC
            """, (f"%{topic}%",))
        else:
            cursor.execute("""
                SELECT source_url, topic, key_learnings, learned_at
                FROM learning_sources ORDER BY learned_at DESC LIMIT 50
            """)

        rows = cursor.fetchall()
        conn.close()

        return [{
            "source_url": r[0], "topic": r[1],
            "learnings": json.loads(r[2]) if r[2] else {},
            "learned_at": r[3]
        } for r in rows]

    def scan_all_sites(self) -> Dict:
        """Scanne tous les sites"""
        results = {}
        for site_id in SITES:
            results[site_id] = self.scan_site_code(site_id)
        return results


if __name__ == "__main__":
    agent = LearningAgent()
    print("=== Learning Agent - 3 Sites ===")

    print("\nScan des sites...")
    for site_id in SITES:
        result = agent.scan_site_code(site_id)
        files = result.get("files_analyzed", 0)
        issues = len(result.get("improvements", []))
        print(f"  {site_id}: {files} fichiers, {issues} suggestions")

    print("\nAgent prêt!")

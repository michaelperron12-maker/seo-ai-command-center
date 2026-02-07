#!/usr/bin/env python3
"""
Similarity Checker - Vérificateur de similarité de contenu
Compare le nouveau contenu avec les contenus existants en base de données
Utilise TF-IDF ou des embeddings pour détecter les duplications
"""

import os
import sys
import sqlite3
import logging
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter
import math

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/seo-agent/similarity.log', mode='a')
    ]
)
logger = logging.getLogger('SimilarityChecker')

# Seuil de similarité par défaut
DEFAULT_SIMILARITY_THRESHOLD = 0.70
DEFAULT_DB_PATH = '/home/serinityvault/Desktop/projet web/seo-agent-stack/data/seo_agent.db'


class SimilarityChecker:
    """
    Vérifie la similarité entre le nouveau contenu et les contenus existants.
    Utilise TF-IDF pour calculer la similarité cosinus.
    """

    def __init__(self, conn: sqlite3.Connection = None, threshold: float = None):
        """
        Initialise le vérificateur de similarité.

        Args:
            conn: Connexion SQLite existante (optionnel)
            threshold: Seuil de blocage (0-1), défaut 0.70
        """
        self.threshold = threshold or DEFAULT_SIMILARITY_THRESHOLD
        self.conn = conn
        self._own_connection = False

        # Stop words français pour le nettoyage
        self.stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'en', 'est',
            'que', 'qui', 'dans', 'pour', 'sur', 'avec', 'par', 'au', 'aux', 'ce',
            'cette', 'ces', 'son', 'sa', 'ses', 'leur', 'leurs', 'notre', 'votre',
            'nous', 'vous', 'il', 'elle', 'ils', 'elles', 'je', 'tu', 'on', 'se',
            'ne', 'pas', 'plus', 'mais', 'ou', 'donc', 'car', 'ni', 'si', 'tout',
            'tous', 'toutes', 'comme', 'aussi', 'bien', 'peut', 'fait', 'faire',
            'avoir', 'etre', 'sont', 'ont', 'a', 'y', 'dont', 'cela', 'ceci'
        }

        # Initialiser la connexion si non fournie
        if self.conn is None:
            self._init_connection()

        logger.info(f"SimilarityChecker initialisé (seuil: {self.threshold})")

    def _init_connection(self) -> None:
        """Crée une connexion à la base de données."""
        try:
            self.conn = sqlite3.connect(DEFAULT_DB_PATH)
            self.conn.row_factory = sqlite3.Row
            self._own_connection = True
            logger.info(f"Connexion DB établie: {DEFAULT_DB_PATH}")
        except Exception as e:
            logger.error(f"Erreur connexion DB: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte pour l'analyse.

        Args:
            text: Texte brut (HTML ou Markdown)

        Returns:
            Texte nettoyé en minuscules
        """
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', ' ', text)

        # Supprimer la ponctuation et les chiffres
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)

        # Convertir en minuscules
        text = text.lower()

        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenise le texte en supprimant les stop words.

        Args:
            text: Texte nettoyé

        Returns:
            Liste de tokens
        """
        words = text.split()
        tokens = [w for w in words if w not in self.stop_words and len(w) > 2]
        return tokens

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """
        Calcule le Term Frequency (TF).

        Args:
            tokens: Liste de tokens

        Returns:
            Dict {token: tf_score}
        """
        counter = Counter(tokens)
        total = len(tokens)

        if total == 0:
            return {}

        return {word: count / total for word, count in counter.items()}

    def _compute_idf(self, documents: List[List[str]], vocabulary: set) -> Dict[str, float]:
        """
        Calcule l'Inverse Document Frequency (IDF).

        Args:
            documents: Liste de documents tokenisés
            vocabulary: Ensemble du vocabulaire

        Returns:
            Dict {token: idf_score}
        """
        n_docs = len(documents)
        idf = {}

        for word in vocabulary:
            doc_count = sum(1 for doc in documents if word in doc)
            idf[word] = math.log((n_docs + 1) / (doc_count + 1)) + 1

        return idf

    def _compute_tfidf_vector(self, tf: Dict[str, float], idf: Dict[str, float], vocabulary: set) -> List[float]:
        """
        Calcule le vecteur TF-IDF.

        Args:
            tf: Term frequencies
            idf: Inverse document frequencies
            vocabulary: Vocabulaire ordonné

        Returns:
            Vecteur TF-IDF
        """
        vocab_list = sorted(vocabulary)
        vector = []

        for word in vocab_list:
            tf_val = tf.get(word, 0)
            idf_val = idf.get(word, 0)
            vector.append(tf_val * idf_val)

        return vector

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs.

        Args:
            vec1: Premier vecteur
            vec2: Second vecteur

        Returns:
            Score de similarité (0-1)
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _get_existing_contents(self) -> List[Dict]:
        """
        Récupère tous les contenus existants de la base de données.

        Returns:
            Liste des contenus avec id, title, content_md
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title, content_md, content_html
            FROM contents
            WHERE status IN ('published', 'draft')
            AND (content_md IS NOT NULL OR content_html IS NOT NULL)
        ''')

        contents = []
        for row in cursor.fetchall():
            content_text = row['content_md'] or row['content_html'] or ''
            contents.append({
                'id': row['id'],
                'title': row['title'],
                'content': content_text
            })

        logger.info(f"{len(contents)} contenus existants récupérés")
        return contents

    def check(self, new_content: str, content_id: int = None) -> Dict:
        """
        Vérifie la similarité du nouveau contenu avec les existants.

        Args:
            new_content: Contenu à vérifier (HTML ou Markdown)
            content_id: ID du contenu à exclure de la comparaison (optionnel)

        Returns:
            Dict avec score, is_blocked, similar_contents
        """
        if not new_content:
            return {
                'success': False,
                'error': 'Contenu vide',
                'score': 0,
                'is_blocked': True
            }

        try:
            # Récupérer les contenus existants
            existing_contents = self._get_existing_contents()

            # Exclure le contenu en cours de modification
            if content_id:
                existing_contents = [c for c in existing_contents if c['id'] != content_id]

            if not existing_contents:
                logger.info("Aucun contenu existant pour comparaison")
                return {
                    'success': True,
                    'score': 0.0,
                    'is_blocked': False,
                    'similar_contents': [],
                    'message': 'Premier contenu, pas de comparaison possible'
                }

            # Préparer les documents
            new_clean = self._clean_text(new_content)
            new_tokens = self._tokenize(new_clean)

            existing_docs = []
            for content in existing_contents:
                clean = self._clean_text(content['content'])
                tokens = self._tokenize(clean)
                existing_docs.append({
                    'id': content['id'],
                    'title': content['title'],
                    'tokens': tokens
                })

            # Construire le vocabulaire global
            vocabulary = set(new_tokens)
            for doc in existing_docs:
                vocabulary.update(doc['tokens'])

            # Calculer IDF sur tous les documents
            all_docs = [new_tokens] + [d['tokens'] for d in existing_docs]
            idf = self._compute_idf(all_docs, vocabulary)

            # Calculer le vecteur TF-IDF du nouveau contenu
            new_tf = self._compute_tf(new_tokens)
            new_vector = self._compute_tfidf_vector(new_tf, idf, vocabulary)

            # Comparer avec chaque contenu existant
            similarities = []
            for doc in existing_docs:
                doc_tf = self._compute_tf(doc['tokens'])
                doc_vector = self._compute_tfidf_vector(doc_tf, idf, vocabulary)

                similarity = self._cosine_similarity(new_vector, doc_vector)

                similarities.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'score': round(similarity, 4)
                })

            # Trier par score décroissant
            similarities.sort(key=lambda x: x['score'], reverse=True)

            # Score maximum
            max_score = similarities[0]['score'] if similarities else 0.0
            is_blocked = max_score > self.threshold

            result = {
                'success': True,
                'score': max_score,
                'is_blocked': is_blocked,
                'threshold': self.threshold,
                'similar_contents': similarities[:5],  # Top 5
                'total_compared': len(existing_contents)
            }

            if is_blocked:
                result['message'] = f"Contenu trop similaire à '{similarities[0]['title']}' ({max_score:.2%})"
                logger.warning(result['message'])
            else:
                result['message'] = f"Similarité acceptable: {max_score:.2%}"
                logger.info(result['message'])

            return result

        except Exception as e:
            logger.error(f"Erreur vérification similarité: {e}")
            return {
                'success': False,
                'error': str(e),
                'score': 0,
                'is_blocked': True
            }

    def get_average_similarity(self) -> float:
        """
        Calcule la similarité moyenne entre tous les contenus publiés.
        Utile pour le kill switch.

        Returns:
            Score moyen de similarité
        """
        try:
            contents = self._get_existing_contents()

            if len(contents) < 2:
                return 0.0

            # Préparer les documents
            docs = []
            for content in contents:
                clean = self._clean_text(content['content'])
                tokens = self._tokenize(clean)
                docs.append({
                    'id': content['id'],
                    'tokens': tokens
                })

            # Vocabulaire global
            vocabulary = set()
            for doc in docs:
                vocabulary.update(doc['tokens'])

            # IDF
            all_tokens = [d['tokens'] for d in docs]
            idf = self._compute_idf(all_tokens, vocabulary)

            # Calculer les vecteurs
            vectors = []
            for doc in docs:
                tf = self._compute_tf(doc['tokens'])
                vector = self._compute_tfidf_vector(tf, idf, vocabulary)
                vectors.append(vector)

            # Calculer toutes les paires de similarité
            total_similarity = 0
            pair_count = 0

            for i in range(len(vectors)):
                for j in range(i + 1, len(vectors)):
                    similarity = self._cosine_similarity(vectors[i], vectors[j])
                    total_similarity += similarity
                    pair_count += 1

            average = total_similarity / pair_count if pair_count > 0 else 0.0

            logger.info(f"Similarité moyenne: {average:.2%} ({pair_count} paires)")
            return round(average, 4)

        except Exception as e:
            logger.error(f"Erreur calcul moyenne: {e}")
            return 0.0

    def close(self) -> None:
        """Ferme la connexion si elle nous appartient."""
        if self._own_connection and self.conn:
            self.conn.close()
            logger.info("Connexion DB fermée")


def main():
    """Point d'entrée pour les tests standalone."""
    print("=== Test SimilarityChecker ===\n")

    try:
        checker = SimilarityChecker()

        # Test avec un contenu exemple
        test_content = """
        <article>
            <h1>Guide SEO 2024</h1>
            <p>Le référencement naturel est essentiel pour votre visibilité en ligne.</p>
            <h2>Les bases du SEO</h2>
            <p>Optimisez vos titres, meta descriptions et contenus pour les moteurs de recherche.</p>
            <h2>Stratégies avancées</h2>
            <p>Backlinks, maillage interne et expérience utilisateur sont clés.</p>
        </article>
        """

        print("Contenu de test:")
        print(test_content[:100] + "...\n")

        # Vérifier la similarité
        result = checker.check(test_content)

        print(f"Résultat:")
        print(f"  - Score max: {result['score']:.2%}")
        print(f"  - Bloqué: {result['is_blocked']}")
        print(f"  - Seuil: {result['threshold']:.2%}")
        print(f"  - Message: {result.get('message', 'N/A')}")

        if result.get('similar_contents'):
            print(f"\nContenus similaires:")
            for content in result['similar_contents'][:3]:
                print(f"  - {content['title']}: {content['score']:.2%}")

        # Test similarité moyenne
        print(f"\nSimilarité moyenne globale: {checker.get_average_similarity():.2%}")

        checker.close()
        print("\n=== Test terminé ===")

    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

"""
SEO Agent Stack - Scripts Python
================================

Ce package contient les modules principaux du SEO Agent:

- seo_brain: Cerveau principal et orchestration
- content_generator: Generation de contenu SEO via LLM
- similarity_checker: Verification de similarite TF-IDF
- publisher: Publication des articles sur le site
- kill_switch: Systeme de securite et pause automatique
- notifier: Notifications multi-canal (Telegram, Email, SMS)
"""

__version__ = "1.0.0"
__author__ = "SEO Agent"

from .seo_brain import SeoBrain
from .content_generator import ContentGenerator
from .similarity_checker import SimilarityChecker
from .publisher import Publisher
from .kill_switch import KillSwitchManager
from .notifier import Notifier

__all__ = [
    'SeoBrain',
    'ContentGenerator',
    'SimilarityChecker',
    'Publisher',
    'KillSwitchManager',
    'Notifier'
]

"""app.core.cache

Cache mémoire TTL pour CVision AI.

- Thread-safe (Lock) pour usage multi-thread (ex: FastAPI avec workers / threadpool).
- Zéro dépendance externe.

Le cache stocke uniquement des objets JSON-serializables (dict/list/str/int/float/bool/None).
Ne pas y stocker d'objets SQLAlchemy.
"""

from __future__ import annotations

import time
import threading
from typing import Optional, Any, Callable
from functools import wraps


class TTLCache:
    """Cache en mémoire avec expiration automatique (TTL)."""

    def __init__(self, default_ttl: int = 1800):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._default_ttl = int(default_ttl)
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur si présente et non expirée."""
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._misses += 1
                return None

            value, expiry = item
            if time.time() > expiry:
                self._cache.pop(key, None)
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stocke une valeur avec TTL."""
        with self._lock:
            effective_ttl = self._default_ttl if ttl is None else int(ttl)
            expiry = time.time() + effective_ttl
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Supprime une clé du cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Vide complètement le cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def invalidate_pattern(self, pattern: str) -> int:
        """Supprime toutes les clés contenant un pattern.

        Retourne le nombre de clés supprimées.
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache if pattern in k]
            for k in keys_to_delete:
                self._cache.pop(k, None)
            return len(keys_to_delete)

    def get_stats(self) -> dict[str, Any]:
        """Retourne les statistiques du cache."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        # Le contenu du cache est volontairement omis.
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# === Instances globales du projet ===

# Cache pour les analyses CV (30 min par défaut)
cv_analysis_cache = TTLCache(default_ttl=1800)

# Cache pour les résultats de matching (15 min — données plus volatiles)
matching_cache = TTLCache(default_ttl=900)

# Cache pour les questions d'interview (60 min — peu de changement)
interview_questions_cache = TTLCache(default_ttl=3600)


def cached(ttl: Optional[int] = None, cache_instance: Optional[TTLCache] = None):
    """Décorateur async pour mettre en cache le résultat d'une fonction.

    Construit une clé :
      "{func.__name__}:{args}:{sorted(kwargs.items())}"
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = cache_instance or cv_analysis_cache
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


def invalidate_cv_cache(cv_id: Any) -> int:
    """Invalide toutes les entrées de cache liées à un CV.

    Retourne le nombre total de clés supprimées (tous caches confondus).
    """
    # On utilise un pattern commun "cv:{cv_id}:" pour simplifier.
    pattern = f"cv:{cv_id}:"
    deleted_cv = cv_analysis_cache.invalidate_pattern(pattern)
    deleted_match = matching_cache.invalidate_pattern(pattern)
    return deleted_cv + deleted_match


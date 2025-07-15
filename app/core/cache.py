"""
Module de gestion du cache Redis pour améliorer les performances
"""
import json
import pickle
from typing import Optional, Any, Union, Callable
from datetime import timedelta
import redis
from functools import wraps
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Connexion Redis
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=False  # Pour supporter pickle
)


class CacheManager:
    """Gestionnaire de cache centralisé"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes par défaut
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Génère une clé de cache unique"""
        # Créer une représentation unique des arguments
        key_parts = [prefix]
        
        # Ajouter les arguments positionnels
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Pour les objets complexes, utiliser un hash
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Ajouter les arguments nommés triés
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        try:
            value = self.redis.get(key)
            if value:
                # Essayer de dépickler d'abord (pour les objets complexes)
                try:
                    return pickle.loads(value)
                except:
                    # Si ça échoue, essayer JSON
                    try:
                        return json.loads(value)
                    except:
                        # Sinon retourner comme string
                        return value.decode('utf-8')
        except Exception as e:
            logger.warning(f"Erreur lors de la lecture du cache: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Stocke une valeur dans le cache"""
        try:
            # Convertir timedelta en secondes
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            elif ttl is None:
                ttl = self.default_ttl
            
            # Sérialiser la valeur
            if isinstance(value, (str, int, float, bool)):
                serialized = json.dumps(value)
            else:
                # Pour les objets complexes, utiliser pickle
                serialized = pickle.dumps(value)
            
            return self.redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Erreur lors de l'écriture dans le cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Supprime une valeur du cache"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.warning(f"Erreur lors de la suppression du cache: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Supprime toutes les clés correspondant au pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Erreur lors de la suppression par pattern: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe"""
        return bool(self.redis.exists(key))


# Instance globale du gestionnaire de cache
cache_manager = CacheManager(redis_client)


def cache_key_wrapper(
    prefix: str,
    ttl: Union[int, timedelta] = 300,
    include_user: bool = True
):
    """
    Décorateur pour mettre en cache les résultats de fonctions
    
    Args:
        prefix: Préfixe pour la clé de cache
        ttl: Durée de vie du cache (secondes ou timedelta)
        include_user: Inclure l'ID utilisateur dans la clé
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Construire la clé de cache
            cache_args = []
            
            # Extraire l'ID utilisateur si nécessaire
            if include_user:
                # Chercher current_user dans les kwargs
                current_user = kwargs.get('current_user')
                if current_user and hasattr(current_user, 'id'):
                    cache_args.append(f"user:{current_user.id}")
            
            # Ajouter les autres arguments pertinents
            # (exclure db, current_user, etc.)
            skip_args = {'db', 'current_user', 'cabinet_id'}
            for k, v in kwargs.items():
                if k not in skip_args and v is not None:
                    cache_args.append(f"{k}:{v}")
            
            cache_key = cache_manager._make_key(prefix, *cache_args)
            
            # Vérifier le cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit pour {cache_key}")
                return cached_value
            
            # Exécuter la fonction
            result = await func(*args, **kwargs)
            
            # Mettre en cache le résultat
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss pour {cache_key}, résultat mis en cache")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Version synchrone du wrapper
            cache_args = []
            
            if include_user:
                current_user = kwargs.get('current_user')
                if current_user and hasattr(current_user, 'id'):
                    cache_args.append(f"user:{current_user.id}")
            
            skip_args = {'db', 'current_user', 'cabinet_id'}
            for k, v in kwargs.items():
                if k not in skip_args and v is not None:
                    cache_args.append(f"{k}:{v}")
            
            cache_key = cache_manager._make_key(prefix, *cache_args)
            
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit pour {cache_key}")
                return cached_value
            
            result = func(*args, **kwargs)
            
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss pour {cache_key}, résultat mis en cache")
            
            return result
        
        # Retourner le bon wrapper selon le type de fonction
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(patterns: Union[str, list]):
    """
    Invalide le cache pour un ou plusieurs patterns
    
    Args:
        patterns: Pattern(s) de clés à invalider
    """
    if isinstance(patterns, str):
        patterns = [patterns]
    
    total_deleted = 0
    for pattern in patterns:
        deleted = cache_manager.delete_pattern(pattern)
        total_deleted += deleted
        if deleted:
            logger.info(f"Cache invalidé: {deleted} clés pour pattern '{pattern}'")
    
    return total_deleted


# Décorateurs spécifiques pour différents types de données
cache_dashboard = cache_key_wrapper("dashboard", ttl=timedelta(minutes=5))
cache_dossiers = cache_key_wrapper("dossiers", ttl=timedelta(minutes=10))
cache_stats = cache_key_wrapper("stats", ttl=timedelta(minutes=15))
cache_documents = cache_key_wrapper("documents", ttl=timedelta(minutes=30))
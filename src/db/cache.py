from abc import ABC, abstractmethod
from typing import Optional, Union

__all__ = (
    "PostAbstractCache",
    "AccessAbstractCache",
    "RefreshAbstractCache",
    "get_posts_cache",
    "get_access_cache",
    "get_refresh_cache"
)

from src.core import config


class PostAbstractCache(ABC):
    def __init__(self, cache_instance):
        self.cache = cache_instance

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: Union[bytes, str],
        expire: int = config.CACHE_EXPIRE_IN_SECONDS,
    ):
        pass

    @abstractmethod
    def close(self):
        pass


class RefreshAbstractCache(ABC):
    def __init__(self, cache_instance):
        self.cache = cache_instance

    @abstractmethod
    def add(
        self,
        key: str,
        value: str
    ):
        pass

    @abstractmethod
    def remove(
        self,
        key: str,
        value: str
    ):
        pass

    @abstractmethod
    def get_all(
        self,
        key: str
    ):
        pass

    @abstractmethod
    def clear(
        self,
        key: str
    ):
        pass

    @abstractmethod
    def close(self):
        pass


class AccessAbstractCache(ABC):
    def __init__(self, cache_instance):
        self.cache = cache_instance

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: Union[bytes, str]
    ):
        pass

    @abstractmethod
    def close(self):
        pass


posts_cache: Optional[PostAbstractCache] = None
blocked_access_tokens_cache: Optional[AccessAbstractCache] = None
active_refresh_tokens_cache: Optional[RefreshAbstractCache] = None


# Функции понадобится при внедрении зависимостей
def get_posts_cache() -> PostAbstractCache:
    return posts_cache


def get_access_cache() -> AccessAbstractCache:
    return blocked_access_tokens_cache


def get_refresh_cache() -> RefreshAbstractCache:
    return active_refresh_tokens_cache

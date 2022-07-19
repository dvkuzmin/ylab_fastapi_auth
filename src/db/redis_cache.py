from typing import NoReturn, Optional, Union

from src.core import config
from src.db import PostAbstractCache, AccessAbstractCache, RefreshAbstractCache

__all__ = ("PostCacheRedis", "RefreshCacheRedis", "AccessCacheRedis",)


class PostCacheRedis(PostAbstractCache):
    def get(self, key: str) -> Optional[dict]:
        return self.cache.get(name=key)

    def set(
        self,
        key: str,
        value: Union[bytes, str],
        expire: int = config.CACHE_EXPIRE_IN_SECONDS,
    ):
        self.cache.set(name=key, value=value, ex=expire)

    def close(self) -> NoReturn:
        self.cache.close()


class AccessCacheRedis(AccessAbstractCache):
    def get(self, key: str) -> Optional[dict]:
        return self.cache.get(name=key)

    def set(
        self,
        key: str,
        value: Union[bytes, str],
    ):
        self.cache.set(name=key, value=value)

    def close(self) -> NoReturn:
        self.cache.close()


class RefreshCacheRedis(RefreshAbstractCache):
    def add(
        self,
        key: str,
        value: str
    ):
        self.cache.sadd(key, value)

    def remove(
        self,
        key: str,
        value: str
    ):
        self.cache.srem(key, value)

    def get_all(
        self,
        key: str
    ):
        self.cache.smembers(key)

    def clear(
        self,
        key: str
    ):
        self.cache.delete(key)

    def close(self) -> NoReturn:
        self.cache.close()

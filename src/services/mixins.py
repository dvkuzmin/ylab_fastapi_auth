from sqlmodel import Session

from src.db import PostAbstractCache, AccessAbstractCache, RefreshAbstractCache


class UserServiceMixin:
    def __init__(
            self,
            access_tokens_cache: AccessAbstractCache,
            refresh_tokens_cache: RefreshAbstractCache,
            session: Session
    ):
        self.blocked_access_tokens_cache: AccessAbstractCache = access_tokens_cache
        self.active_refresh_tokens_cache: RefreshAbstractCache = refresh_tokens_cache
        self.session: Session = session


class PostServiceMixin:
    def __init__(
            self,
            posts_cache: PostAbstractCache,
            session: Session
    ):
        self.posts_cache: PostAbstractCache = posts_cache
        self.session: Session = session

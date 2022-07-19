import json
from functools import lru_cache
from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from src.api.v1.schemas import PostCreate, PostModel
from src.db import PostAbstractCache, get_posts_cache, get_session
from src.models import Post
from src.services import PostServiceMixin

__all__ = ("PostService", "get_post_service")


class PostService(PostServiceMixin):
    def get_post_list(self) -> dict:
        """Получить список постов."""
        posts = self.session.query(Post).order_by(Post.created_at).all()
        return {"posts": [PostModel(**post.dict()) for post in posts]}

    def get_post_detail(self, item_id: int) -> Optional[dict]:
        """Получить детальную информацию поста."""
        if cached_post := self.posts_cache.get(key=f"{item_id}"):
            return json.loads(cached_post)

        post = self.session.query(Post).filter(Post.id == item_id).first()
        if post:
            self.posts_cache.set(key=f"{post.id}", value=post.json())
        return post.dict() if post else None

    def create_post(self, post: PostCreate, author_id: str) -> dict:
        """Создать пост."""
        new_post = Post(
            title=post.title,
            description=post.description,
            author_id=author_id
        )
        self.session.add(new_post)
        self.session.commit()
        self.session.refresh(new_post)
        return new_post.dict()


# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_post_service(
    posts_cache: PostAbstractCache = Depends(get_posts_cache),
    session: Session = Depends(get_session),
) -> PostService:
    return PostService(posts_cache=posts_cache, session=session)

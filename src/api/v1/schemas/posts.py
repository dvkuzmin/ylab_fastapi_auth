from datetime import datetime
from typing import List

from pydantic import BaseModel

__all__ = (
    "PostModel",
    "PostCreate",
    "PostListResponse",
)


class PostBase(BaseModel):
    title: str
    description: str


class PostCreate(PostBase):
    ...


class PostModel(PostBase):
    id: int
    created_at: datetime
    author_id: str


class PostListResponse(BaseModel):
    posts: List[PostModel] = []

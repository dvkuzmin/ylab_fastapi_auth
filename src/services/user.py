from functools import lru_cache
import hashlib
from typing import Tuple, Optional, Union
from uuid import uuid4
import datetime

from fastapi import Depends
from sqlalchemy.exc import ProgrammingError, IntegrityError
from sqlmodel import Session
import jwt

from src.api.v1.schemas import UserCreate, UserModel, UserLogin, UserUpdate
from src.db import AccessAbstractCache, RefreshAbstractCache, get_refresh_cache, get_access_cache, get_session
from src.models import User
from src.services import UserServiceMixin
from src.core.config import JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_IN_SECONDS, REFRESH_TOKEN_EXPIRE_IN_DAYS

__all__ = ("UserService", "get_user_service")


class UserService(UserServiceMixin):
    @staticmethod
    def _get_jwt_payload(auth_header: str) -> Optional[dict]:
        """Получение payload из токена"""
        try:
            method, token = auth_header.split()
            if method in ("Bearer", "JWT"):
                return jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        except Exception:
            return

    def _is_access_token_valid(self, payload: dict) -> bool:
        """"Проверка валидности access токена по данным из payload"""
        access_token_uuid = payload.get("jti")
        refresh_token_uuid = payload.get("refresh_uuid")
        exp_time = payload.get("exp")
        user_uuid = payload.get("user_uuid")
        if (access_token_uuid
                and refresh_token_uuid
                and exp_time
                and user_uuid):
            if self.blocked_access_tokens_cache.get(access_token_uuid) is None:
                if not self._is_token_expires(exp_time):
                    # Проверяем, не был ли сделан выход со всех устройств
                    if refresh_tokens := self.active_refresh_tokens_cache.cache.smembers(user_uuid):
                        for token_id in refresh_tokens:
                            if token_id == refresh_token_uuid:
                                return True
                    self.blocked_access_tokens_cache.set(access_token_uuid, "")

    def _is_refresh_token_valid(self, payload: dict) -> bool:
        """Проверка валидности refresh токена по данным из payload"""
        user_uuid = payload.get("user_uuid")
        refresh_token_uuid = payload.get("jti")
        exp_time = payload.get("exp")
        if not self._is_token_expires(exp_time):
            for token_id in self.active_refresh_tokens_cache.cache.smembers(user_uuid):
                if token_id == refresh_token_uuid:
                    return True

    @staticmethod
    def _is_token_expires(exp_time: int) -> bool:
        """Проверка срока действия токена"""
        now = int(datetime.datetime.timestamp(datetime.datetime.now()))
        return now > exp_time

    def _block_access_token(self, access_token_uuid: str):
        """Добавление access токена в черный список"""
        self.blocked_access_tokens_cache.set(access_token_uuid, "")

    def _get_user_by_uuid(self, user_id: str) -> Optional[UserModel]:
        """Получение пользователя по uuid"""
        user = self.session.query(User).filter(User.uuid == user_id).one_or_none()
        if user:
            return UserModel(**user.dict())

    def register(self, user: UserCreate) -> Union[UserModel, str]:
        """Регистрация пользователя"""
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        new_user = User(
            uuid=str(uuid4()),
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        try:
            self.session.add(new_user)
            self.session.commit()
            self.session.refresh(new_user)
            return UserModel(**new_user.dict())
        except ProgrammingError:
            return "Error in database"
        except IntegrityError:
            return "User with such name already exists"

    def get_user_by_credentials(self, user_login: UserLogin) -> Optional[UserModel]:
        """Получение пользователя по имени-паролю"""
        user = self.session.query(User).filter(User.username == user_login.username).one_or_none()
        if user:
            if user.hashed_password == hashlib.sha256(user_login.password.encode()).hexdigest():
                return UserModel(**user.dict())

    def generate_refresh_token(self, user: UserModel) -> tuple:
        """Генерация refresh токена и добавление его uuid в редис"""
        refresh_token_uuid = str(uuid4())
        exp_refresh_token = int(datetime.datetime.timestamp(
            datetime.datetime.now() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_IN_DAYS)
            )
        )
        refresh_token = jwt.encode(
            {
                "user_uuid": user.uuid,
                "exp": exp_refresh_token,
                "jti": refresh_token_uuid,
                "type": "refresh"
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        self.active_refresh_tokens_cache.add(user.uuid, refresh_token_uuid)
        return refresh_token, refresh_token_uuid

    def generate_access_token(self, user: UserModel, refresh_token_uuid: str) -> str:
        """Генерация access токена"""
        access_token_uuid = str(uuid4())
        exp_access_token = int(datetime.datetime.timestamp(
            datetime.datetime.now() + datetime.timedelta(seconds=ACCESS_TOKEN_EXPIRE_IN_SECONDS)
            )
        )
        access_token = jwt.encode(
            {
                "username": user.username,
                "email": user.email,
                "user_uuid": user.uuid,
                "jti": access_token_uuid,
                "refresh_uuid": refresh_token_uuid,
                "exp": exp_access_token,
                "type": "access",
                "created_at": user.created_at.strftime("%a %b %d %H:%M:%S %Y")
            },
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        return access_token

    def get_user_by_access_token(self, auth_header: str) -> Optional[UserModel]:
        """Получение пользователя по access токену"""
        data = self._get_jwt_payload(auth_header)
        if data:
            if self._is_access_token_valid(data):
                user_uuid = data.get("user_uuid")
                user = self.session.query(User).filter(User.uuid == user_uuid).one_or_none()
                return UserModel(**user.dict())

    def refresh_tokens_by_access_token(self, auth_header: str) -> Optional[Tuple[str, str]]:
        """Обновление access и refresh токенов по access токену"""
        data = self._get_jwt_payload(auth_header)
        if data:
            if self._is_access_token_valid(data):
                user_uuid = data.get("user_uuid")
                access_token_uuid = data.get("jti")
                refresh_token_uuid = data.get("refresh_uuid")
                self.active_refresh_tokens_cache.remove(user_uuid, refresh_token_uuid)
                self._block_access_token(access_token_uuid)
                user = self._get_user_by_uuid(user_uuid)
                refresh_token, refresh_token_uuid = self.generate_refresh_token(user)
                access_token = self.generate_access_token(user, refresh_token_uuid)
                return refresh_token, access_token

    def refresh_tokens_by_refresh_token(self, auth_header: str) -> Optional[Tuple[str, str]]:
        """Обновление access и refresh токенов по refresh токену"""
        data = self._get_jwt_payload(auth_header)
        if data:
            if self._is_refresh_token_valid(data):
                user_uuid = data.get("user_uuid")
                refresh_token_uuid = data.get("jti")
                self.active_refresh_tokens_cache.remove(user_uuid, refresh_token_uuid)
                user = self._get_user_by_uuid(user_uuid)
                refresh_token, refresh_token_uuid = self.generate_refresh_token(user)
                access_token = self.generate_access_token(user, refresh_token_uuid)
                return refresh_token, access_token

    def update_user_info(self, user_update: UserUpdate, auth_header: str) -> Optional[tuple]:
        """Изменение данных пользователя"""
        data = self._get_jwt_payload(auth_header)
        if data:
            if self._is_access_token_valid(data):
                user = self.session.query(User).filter(User.uuid == data["user_uuid"]).one_or_none()
                if user_update.email:
                    user.email = user_update.email
                if user_update.username:
                    user.username = user_update.username
                if user_update.password:
                    user.hashed_password = hashlib.sha256(user_update.password.encode()).hexdigest()
                self.session.commit()
                self.session.refresh(user)
                self._block_access_token(data.get("jti"))
                access_token = self.generate_access_token(user, data.get("refresh_uuid"))
                return UserModel(**user.dict()), access_token

    def logout(self, auth_header: str) -> Optional[dict]:
        """Выход с текущего устройства"""
        data = self._get_jwt_payload(auth_header)
        if data:
            if self._is_access_token_valid(data):
                access_jwt_uuid = data.get("jti")
                refresh_jwt_uuid = data.get("refresh_uuid")
                user_uuid = data.get("user_uuid")
                self._block_access_token(access_jwt_uuid)
                self.active_refresh_tokens_cache.remove(user_uuid, refresh_jwt_uuid)
                return {"msg": "You have been logged out."}

    def logout_all(self, auth_header: str) -> Optional[dict]:
        """Выход со всех устройств"""
        data = self._get_jwt_payload(auth_header)
        if data:
            if self._is_access_token_valid(data):
                user_uuid = data.get("user_uuid")
                access_token_uuid = data.get("jti")
                self._block_access_token(access_token_uuid)
                self.active_refresh_tokens_cache.clear(user_uuid)
                return {"msg": "You have been logged out from all devices."}


# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_user_service(
        access_tokens_cache: AccessAbstractCache = Depends(get_access_cache),
        refresh_tokens_cache: RefreshAbstractCache = Depends(get_refresh_cache),
        session: Session = Depends(get_session),
) -> UserService:
    return UserService(
        access_tokens_cache=access_tokens_cache,
        refresh_tokens_cache=refresh_tokens_cache,
        session=session
    )

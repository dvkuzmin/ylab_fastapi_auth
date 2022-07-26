from http import HTTPStatus
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Header

from src.api.v1.schemas import UserCreate, UserModel, UserLogin, UserUpdate
from src.services import UserService, get_user_service

router = APIRouter()


@router.post(
    path="/signup",
    tags=["users"],
    summary="Регистрация",
    status_code=201,
)
def register(
        user_create: UserCreate,
        user_service: UserService = Depends(get_user_service)
):
    error_messages = {
        "Error in database": HTTPStatus.INTERNAL_SERVER_ERROR,
        "User with such name already exists": HTTPStatus.BAD_REQUEST
    }
    result = user_service.register(user=user_create)
    if isinstance(result, UserModel):
        return {
            "msg": "User created.",
            "user": result
        }
    raise HTTPException(
        status_code=error_messages[result],
        detail=result
    )


@router.post(
    path="/login",
    tags=["users"],
    summary="Авторизация",
)
def login(
        user_login: UserLogin,
        user_service: UserService = Depends(get_user_service)
):
    user = user_service.get_user_by_credentials(user_login)
    if user:
        refresh_token, refresh_token_uuid = user_service.generate_refresh_token(user)
        access_token = user_service.generate_access_token(user, refresh_token_uuid)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND,
        detail="No users with such username or password"
    )


@router.post(
    path="/refresh",
    tags=["users"],
    summary="Обновить токены",
)
def refresh(
    authorization: Union[str, None] = Header(default=None),
    user_service: UserService = Depends(get_user_service)
):
    try:
        refresh_token, access_token = user_service.refresh_tokens_by_refresh_token(authorization)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    except TypeError:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized user")


@router.post(
    path="/logout",
    tags=["users"],
    summary="Выйти с текущего устройства",
)
def logout(
    authorization: Union[str, None] = Header(default=None),
    user_service: UserService = Depends(get_user_service)
):
    if msg := user_service.logout(authorization):
        return msg
    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized user")


@router.post(
    path="/logout_all",
    tags=["users"],
    summary="Выйти со всех устройств",
)
def logout_all(
    authorization: Union[str, None] = Header(default=None),
    user_service: UserService = Depends(get_user_service)
):
    if msg := user_service.logout_all(authorization):
        return msg
    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized user")


@router.get(
    path="/me",
    tags=["users"],
    summary="Посмотреть свой профиль",
    response_model=UserModel,
)
def show_user_info(
        authorization: Union[str, None] = Header(default=None),
        user_service: UserService = Depends(get_user_service)
):
    if user := user_service.get_user_by_access_token(authorization):
        return user
    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized user")


@router.patch(
    path="/me",
    tags=["users"],
    summary="Обновить данные профиля",
)
def update_user_info(
        user_update: UserUpdate,
        authorization: Union[str, None] = Header(default=None),
        user_service: UserService = Depends(get_user_service)
):
    try:
        updated_user, new_access_token = user_service.update_user_info(user_update, authorization)
        return {
            "msg": "Update is successful. Please use new access_token.",
            "user": updated_user,
            "access_token": new_access_token
        }
    except TypeError:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unauthorized user")

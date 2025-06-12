from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import (
    FilterPage,
    Message,
    UserList,
    UserPublic,
    UserSchema,
)
from fastapi_zero.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix='/users', tags=['users'])
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
async def create_user(user: UserSchema, session: DbSession):
    db_user = await session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    if db_user:
        if db_user.username == user.username:
            detail_message = 'Username already exists'
        else:
            detail_message = 'Email already exists'

        raise HTTPException(
            detail=detail_message, status_code=HTTPStatus.CONFLICT
        )

    user_data = user.model_dump()
    user_data['password'] = get_password_hash(user.password)

    db_user = User(**user_data)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


@router.get('/', status_code=HTTPStatus.OK, response_model=UserList)
async def read_users(
    session: DbSession,
    current_user: CurrentUser,
    filter_users: Annotated[FilterPage, Query()],
):
    users = await session.scalars(
        select(User).limit(filter_users.limit).offset(filter_users.offset)
    )
    return {'users': users}


@router.get('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
async def read_user(user_id: int, session: DbSession):
    user_db = await session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            detail='User not found!', status_code=HTTPStatus.NOT_FOUND
        )

    return user_db


@router.put('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
async def update_user(
    user_id: int,
    user: UserSchema,
    session: DbSession,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    try:
        user_data = user.model_dump(exclude_unset=True)

        for field, value in user_data.items():
            if field == 'password':
                setattr(current_user, field, get_password_hash(value))
            else:
                setattr(current_user, field, value)

        session.add(current_user)
        await session.commit()
        await session.refresh(current_user)

        return current_user
    except IntegrityError:
        detail_message = 'Username or Email already exists'
        raise HTTPException(
            detail=detail_message, status_code=HTTPStatus.CONFLICT
        )


@router.delete('/{user_id}', response_model=Message)
async def delete_user(
    user_id: int,
    session: DbSession,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    await session.delete(current_user)
    await session.commit()

    return Message(message='User deleted!')

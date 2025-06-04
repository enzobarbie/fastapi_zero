from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import (
    Message,
    Token,
    UserList,
    UserPublic,
    UserSchema,
)
from fastapi_zero.security import (
    create_acess_token,
    get_current_user,
    get_password_hash,
    verify_password,
)

app = FastAPI(title='API DO ENZO!')


@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(
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
    session.commit()
    session.refresh(db_user)  # completa os campos 'id' e os de timestamp

    return db_user


@app.get('/users/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    users = session.scalars(select(User).limit(limit).offset(offset))
    return {'users': users}


@app.get(
    '/user/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            detail='User not found!', status_code=HTTPStatus.NOT_FOUND
        )

    return user_db


@app.put(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def update_user(
    user_id: int,
    user: UserSchema,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
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
        session.commit()
        session.refresh(current_user)

        return current_user
    except IntegrityError:
        detail_message = 'Username or Email already exists'
        raise HTTPException(
            detail=detail_message, status_code=HTTPStatus.CONFLICT
        )


@app.delete('/users/{user_id}', response_model=Message)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    session.delete(current_user)
    session.commit()

    return Message(message='User deleted!')


@app.post('/token', response_model=Token)
def login_for_acess_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorret email or password',
        )

    access_token = create_acess_token({'sub': user.email})
    return {'access_token': access_token, 'token_type': 'Bearer'}

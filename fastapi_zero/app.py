from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import Message, UserList, UserPublic, UserSchema

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

    db_user = User(**user.model_dump())

    session.add(db_user)
    session.commit()
    session.refresh(db_user)  # completa os campos 'id' e os de timestamp

    return db_user


@app.get('/users/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(
    limit: int = 10, offset: int = 0, session: Session = Depends(get_session)
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
    user_id: int, user: UserSchema, session: Session = Depends(get_session)
):
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            detail='User not found!', status_code=HTTPStatus.NOT_FOUND
        )
    try:
        session.execute(
            update(User).where(User.id == user_id).values(**user.model_dump())
        )

        session.add(user_db)
        session.commit()
        session.refresh(user_db)

        return user_db
    except IntegrityError:
        detail_message = 'Username or Email already exists'
        raise HTTPException(
            detail=detail_message, status_code=HTTPStatus.CONFLICT
        )


@app.delete('/users/{user_id}', response_model=Message)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            detail='User not found!', status_code=HTTPStatus.NOT_FOUND
        )

    session.delete(user_db)
    session.commit()

    return Message(message='User deleted!')

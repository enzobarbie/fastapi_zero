from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import Token
from fastapi_zero.security import (
    create_acess_token,
    verify_password,
)

DbSession = Annotated[Session, Depends(get_session)]
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/token', response_model=Token)
def login_for_acess_token(
    form_data: OAuth2Form,
    session: DbSession,
):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorret email or password',
        )

    access_token = create_acess_token({'sub': user.email})
    return {'access_token': access_token, 'token_type': 'Bearer'}

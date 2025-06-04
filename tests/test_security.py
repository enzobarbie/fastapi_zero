from http import HTTPStatus

from jwt import decode

from fastapi_zero.security import (
    ALGORITHM,
    SECRET_KEY,
    create_acess_token,
)


def test_jwt():
    data = {'test': 'test'}

    token = create_acess_token(data)

    decoded = decode(token, SECRET_KEY, algorithms=ALGORITHM)

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


def test_jwt_invalid_token(client, user):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': 'Bearer invalid-token'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}

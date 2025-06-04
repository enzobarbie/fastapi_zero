from http import HTTPStatus

from jwt import decode

from fastapi_zero.security import create_acess_token


def test_jwt(settings):
    data = {'test': 'test'}

    token = create_acess_token(data)

    decoded = decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


def test_jwt_invalid_token(client, user):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': 'Bearer invalid-token'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}

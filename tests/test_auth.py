from http import HTTPStatus

from fastapi_zero.security import create_acess_token


def test_token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = response.json()
    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token


def test_non_user_token(client):
    response = client.post(
        '/auth/token',
        data={'username': 'Hacker', 'password': 'batatinhas_fritas'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorret email or password'}


def test_get_current_user_not_found(client):
    data = {'no-email': 'test'}
    token = create_acess_token(data)

    response = client.delete(
        '/users/1', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_get_current_user_does_not_exists(client):
    data = {'sub': 'batata@teste.com'}
    token = create_acess_token(data)

    response = client.delete(
        '/users/1', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}

from http import HTTPStatus

from fastapi_zero.schemas import UserPublic
from fastapi_zero.security import create_acess_token


def test_create_user(client):
    response = client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'email': 'alice@example.com',
        'username': 'alice',
    }


def test_create_same_username(client, user):
    response = client.post(
        '/users/',
        json={
            'username': 'Teste',
            'email': 'teste@test.com',
            'password': 'testtest',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Username already exists' in response.text


def test_create_same_email(client, user):
    response = client.post(
        '/users/',
        json={
            'username': 'Testudo',
            'email': 'teste@test.com',
            'password': 'testtest',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Email already exists' in response.text


def test_read_users_with_user(client, user, token):
    response = client.get(
        '/users/', headers={'Authorization': f'Bearer {token}'}
    )
    user_schema = UserPublic.model_validate(user).model_dump()
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_get_user(client, user):
    response = client.get(f'/user/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'Teste',
        'email': 'teste@test.com',
        'id': 1,
    }


def test_get_a_non_user(client):
    response = client.get('/user/0')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found!'}


def test_update_user(client, user, token):
    response = client.put(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': 1,
    }


def test_update_a_non_user(client, token):
    response = client.put(
        '/users/0',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}


def test_update_integrity_error(client, user, token):
    client.post(
        '/users',
        json={
            'username': 'fausto',
            'email': 'fausto@example.com',
            'password': 'secret',
        },
    )

    response = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Username or Email already exists' in response.text


def test_delete_user(client, user, token):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert 'User deleted!' in response.text


def test_delete_a_non_user(client, token):
    response = client.delete(
        '/users/0',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}


def test_token(client, user):
    response = client.post(
        '/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    breakpoint()
    token = response.json()
    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token


def test_non_user_token(client):
    response = client.post(
        '/token',
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

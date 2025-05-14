from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.app import app

client = TestClient(app)


def test_root_deve_retornar_hello_world():
    response = client.get('/')

    assert response.json() == {'message': 'Hello World!'}
    assert response.status_code == HTTPStatus.OK


def test_html():
    response = client.get('/html')

    assert response.status_code == HTTPStatus.OK
    assert '<h1>Hello World!</h1>' in response.text

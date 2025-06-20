from http import HTTPStatus


def test_read_root(client):
    response = client.post('/', json={'message': 'Enzo'})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Enzo'}

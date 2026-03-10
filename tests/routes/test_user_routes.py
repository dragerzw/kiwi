def test_get_users(client, auth_headers):
    response = client.get('/users/', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) >= 1

def test_get_user(client, auth_headers):
    response = client.get('/users/admin', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['username'] == 'admin'

def test_get_user_not_found(client, auth_headers):
    response = client.get('/users/unknown', headers=auth_headers)
    assert response.status_code == 403

def test_create_user(client, auth_headers):
    data = {
        "username": "newuser",
        "password": "pwd",
        "firstname": "New",
        "lastname": "User",
        "balance": 500.0
    }
    response = client.post('/users/', json=data, headers=auth_headers)
    assert response.status_code == 201

def test_update_balance(client, auth_headers):
    data = {
        "username": "admin",
        "new_balance": 2000.0
    }
    response = client.put('/users/update-balance', json=data, headers=auth_headers)
    assert response.status_code == 200

def test_delete_user_unauthorized(client, auth_headers):
    response = client.delete('/users/other_user', headers=auth_headers)
    assert response.status_code == 403

def test_delete_user_admin_protected(client, auth_headers):
    response = client.delete('/users/admin', headers=auth_headers)
    assert response.status_code == 400

def test_get_user_transactions(client, auth_headers):
    response = client.get('/users/admin/transactions', headers=auth_headers)
    assert response.status_code == 200

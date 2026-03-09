def test_get_all_portfolios(client, auth_headers):
    response = client.get('/portfolios/', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_create_portfolio(client, auth_headers):
    data = {"name": "Test Port", "description": "Test", "username": "admin"}
    response = client.post('/portfolios/', json=data, headers=auth_headers)
    assert response.status_code == 201
    assert 'portfolio_id' in response.json

def test_create_portfolio_wrong_user(client, auth_headers):
    data = {"name": "Test Port", "description": "Test", "username": "other_user"}
    response = client.post('/portfolios/', json=data, headers=auth_headers)
    assert response.status_code == 403

def test_get_portfolio(client, auth_headers, monkeypatch):
    monkeypatch.setattr('app.routes.portfolio_routes.get_quote', lambda x: None)
    data = {"name": "Test Port", "description": "Test", "username": "admin"}
    create_resp = client.post('/portfolios/', json=data, headers=auth_headers)
    pid = create_resp.json['portfolio_id']
    
    response = client.get(f'/portfolios/{pid}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['name'] == 'Test Port'

def test_delete_portfolio(client, auth_headers):
    data = {"name": "Delete Me", "description": "Test", "username": "admin"}
    create_resp = client.post('/portfolios/', json=data, headers=auth_headers)
    pid = create_resp.json['portfolio_id']
    
    response = client.delete(f'/portfolios/{pid}', headers=auth_headers)
    assert response.status_code == 200

def test_portfolio_access_grant(client, auth_headers):
    data = {"name": "Access Port", "description": "Test", "username": "admin"}
    create_resp = client.post('/portfolios/', json=data, headers=auth_headers)
    pid = create_resp.json['portfolio_id']
    
    client.post('/users/', json={"username": "user2", "password": "x", "firstname": "A", "lastname": "B", "balance": 0.0}, headers=auth_headers)
    
    grant_data = {"username": "user2", "role": "Viewer"}
    response = client.post(f'/portfolios/{pid}/access', json=grant_data, headers=auth_headers)
    assert response.status_code == 200

def test_portfolio_access_revoke(client, auth_headers):
    data = {"name": "Access Port", "description": "Test", "username": "admin"}
    create_resp = client.post('/portfolios/', json=data, headers=auth_headers)
    pid = create_resp.json['portfolio_id']
    
    client.post('/users/', json={"username": "user2", "password": "x", "firstname": "A", "lastname": "B", "balance": 0.0}, headers=auth_headers)
    grant_data = {"username": "user2", "role": "Viewer"}
    client.post(f'/portfolios/{pid}/access', json=grant_data, headers=auth_headers)
    
    response = client.delete(f'/portfolios/{pid}/access/user2', headers=auth_headers)
    assert response.status_code == 200

import pytest
from flask import jsonify
import jwt
from app.auth import require_auth

@pytest.fixture(scope="module", autouse=True)
def setup_auth_route(app):
    with app.app_context():
        @app.route('/test_protected')
        @require_auth
        def test_protected():
            from flask import g
            if hasattr(g, 'username'):
                return jsonify(username=g.username), 200
            return jsonify(success=True), 200

def test_missing_auth_header(client, app):
    response = client.get('/test_protected')
    assert response.status_code == 401
    assert b"Authorization header is expected" in response.data

def test_invalid_bearer(client, app):
    response = client.get('/test_protected', headers={"Authorization": "Token 123"})
    assert response.status_code == 401
    assert b"Authorization header must start with Bearer" in response.data

def test_valid_token_mocked(client, app, monkeypatch):
    monkeypatch.setattr('app.auth.auth.jwt.get_unverified_header', lambda x: {"kid": "key1"})
    monkeypatch.setattr('app.auth.auth.get_jwks', lambda: {"keys": [{"kid": "key1", "kty": "RSA", "alg": "RS256"}]})
    monkeypatch.setattr('app.auth.auth.RSAAlgorithm.from_jwk', lambda x: "dummy_rsa_key")
    
    def mock_decode(*args, **kwargs):
        return {"sub": "user123", "username": "testuser"}
    monkeypatch.setattr('app.auth.auth.jwt.decode', mock_decode)
    
    response = client.get('/test_protected', headers={"Authorization": "Bearer validtoken"})
    assert response.status_code == 200
    assert response.json["username"] == "testuser"

def test_expired_token(client, app, monkeypatch):
    monkeypatch.setattr('app.auth.auth.jwt.get_unverified_header', lambda x: {"kid": "key1"})
    monkeypatch.setattr('app.auth.auth.get_jwks', lambda: {"keys": [{"kid": "key1", "kty": "RSA", "alg": "RS256"}]})
    monkeypatch.setattr('app.auth.auth.RSAAlgorithm.from_jwk', lambda x: "dummy_rsa_key")
    
    def mock_decode_expired(*args, **kwargs):
        raise jwt.ExpiredSignatureError("Expired")
    monkeypatch.setattr('app.auth.auth.jwt.decode', mock_decode_expired)
    
    response = client.get('/test_protected', headers={"Authorization": "Bearer validtoken"})
    assert response.status_code == 401
    assert b"Token is expired" in response.data


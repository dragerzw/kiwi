def test_get_all_securities(client, auth_headers):
    response = client.get('/securities/', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_security_by_ticker(client, auth_headers, monkeypatch):
    from app.service.alpha_vantage_client import SecurityQuote
    def mock_get_quote(ticker):
        if ticker == "AAPL":
            return SecurityQuote(ticker="AAPL", date="2023-11-20", price=150.0, issuer="Apple Inc.")
        return None
    monkeypatch.setattr("app.service.security_service.get_quote", mock_get_quote)
    
    response = client.get('/securities/AAPL', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['ticker'] == 'AAPL'

def test_get_security_not_found(client, auth_headers, monkeypatch):
    def mock_get_quote(ticker):
        return None
    monkeypatch.setattr("app.service.security_service.get_quote", mock_get_quote)
    
    response = client.get('/securities/INVALID', headers=auth_headers)
    assert response.status_code == 404

def test_get_security_transactions(client, auth_headers):
    response = client.get('/securities/AAPL/transactions', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

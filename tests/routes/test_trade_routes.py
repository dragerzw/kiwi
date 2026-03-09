def test_buy_trade(client, auth_headers, monkeypatch):
    from app.service.alpha_vantage_client import SecurityQuote
    def mock_get_quote(ticker):
        return SecurityQuote(ticker="AAPL", date="2023-11-20", price=150.0, issuer="Apple Inc.")
    monkeypatch.setattr("app.service.trade_service.get_quote", mock_get_quote)
    
    create_resp = client.post('/portfolios/', json={"name": "Trade Port 1", "description": "Desc", "username": "admin"}, headers=auth_headers)
    pid = create_resp.json['portfolio_id']
    
    data = {"portfolio_id": pid, "ticker": "AAPL", "quantity": 2}
    response = client.post('/trades/buy', json=data, headers=auth_headers)
    assert response.status_code == 201

def test_sell_trade(client, auth_headers, monkeypatch):
    from app.service.alpha_vantage_client import SecurityQuote
    def mock_get_quote(ticker):
        return SecurityQuote(ticker="AAPL", date="2023-11-20", price=150.0, issuer="Apple Inc.")
    monkeypatch.setattr("app.service.trade_service.get_quote", mock_get_quote)
    
    create_resp = client.post('/portfolios/', json={"name": "Trade Port 2", "description": "Desc", "username": "admin"}, headers=auth_headers)
    pid = create_resp.json['portfolio_id']
    
    buy_data = {"portfolio_id": pid, "ticker": "AAPL", "quantity": 5}
    client.post('/trades/buy', json=buy_data, headers=auth_headers)
    
    sell_data = {"portfolio_id": pid, "ticker": "AAPL", "quantity": 2, "sale_price": 160.0}
    response = client.post('/trades/sell', json=sell_data, headers=auth_headers)
    assert response.status_code == 200

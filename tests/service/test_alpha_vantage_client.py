import pytest
from app.service.alpha_vantage_client import get_company_name, get_price_data, get_quote, AlphaVantageError

def test_get_company_name(monkeypatch, app):
    with app.app_context():
        import requests
        class MockResponse:
            def json(self):
                return {"bestMatches": [{"2. name": "Apple Inc."}]}
            def raise_for_status(self):
                pass
        def mock_get(*args, **kwargs):
            return MockResponse()
        monkeypatch.setattr(requests, "get", mock_get)
        assert get_company_name("AAPL") == "Apple Inc."

def test_get_price_data(monkeypatch, app):
    with app.app_context():
        import requests
        class MockResponse:
            def json(self):
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2023-11-20"}}
            def raise_for_status(self):
                pass
        def mock_get(*args, **kwargs):
            return MockResponse()
        monkeypatch.setattr(requests, "get", mock_get)
        data = get_price_data("AAPL")
        assert data["price"] == 150.0
        assert data["date"] == "2023-11-20"

def test_get_quote(monkeypatch, app):
    with app.app_context():
        import requests
        class MockResponse:
            def json(self):
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2023-11-20"}, "bestMatches": [{"2. name": "Apple Inc."}]}
            def raise_for_status(self):
                pass
        
        def mock_get(url, *args, **kwargs):
            return MockResponse()
        monkeypatch.setattr(requests, "get", mock_get)
        
        quote = get_quote("AAPL")
        assert quote.ticker == "AAPL"
        assert quote.price == 150.0
        assert quote.issuer == "Apple Inc."
        assert quote.date == "2023-11-20"

def test_get_quote_invalid(monkeypatch, app):
    with app.app_context():
        import requests
        class MockResponse:
            def json(self):
                return {"Global Quote": {}}
            def raise_for_status(self):
                pass
        
        def mock_get(url, *args, **kwargs):
            return MockResponse()
        monkeypatch.setattr(requests, "get", mock_get)
        
        assert get_quote("INVALID") is None

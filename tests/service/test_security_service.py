import pytest
from app.service.security_service import get_all_securities, SecurityException, get_security_by_ticker
from app.service.alpha_vantage_client import SecurityQuote

@pytest.fixture(autouse=True)
def mock_alpha_vantage(monkeypatch):
    def mock_get_quote(ticker):
        if ticker == "AAPL":
            return SecurityQuote(ticker="AAPL", date="2023-11-20", price=150.0, issuer="Apple Inc.")
        return None
    
    monkeypatch.setattr("app.service.security_service.get_quote", mock_get_quote)

def test_get_security_by_ticker(db_session):
    security = get_security_by_ticker("AAPL")
    assert security is not None
    assert security.ticker == "AAPL"
    assert security.price == 150.00

def test_get_security_by_invalid_ticker(db_session):
    with pytest.raises(SecurityException) as e:
        get_security_by_ticker("INVALID")
    assert "could not be found" in str(e.value)

def test_get_all_securities(db_session):
    securities = get_all_securities()
    assert securities == []
import pytest
from app.models import User, Portfolio, Investment
from app.service.portfolio_service import create_portfolio
from app.service.trade_service import InsufficientFundsError, execute_purchase_order, TradeExecutionException, liquidate_investment
from app.service.alpha_vantage_client import SecurityQuote
from app.service.user_service import create_user
from app.service import transaction_service

@pytest.fixture(autouse=True)
def setup(db_session):
    create_user(username="user", password="secret", firstname="Firstname", lastname="Lastname", balance=1000.00)
    db_session.commit()
    user = db_session.query(User).filter_by(username="user").one()
    assert user is not None
    create_portfolio("Test Portfolio", "Test Portfolio Description", user)
    db_session.commit()
    portfolio = db_session.query(Portfolio).filter_by(name="Test Portfolio").one()
    assert portfolio is not None
    return {
        "user": user,
        "portfolio": portfolio
    }

@pytest.fixture(autouse=True)
def mock_alpha_vantage(monkeypatch):
    def mock_get_quote(ticker):
        if ticker == "AAPL":
            return SecurityQuote(ticker="AAPL", date="2023-11-20", price=150.0, issuer="Apple Inc.")
        if ticker == "GOOGL":
            return SecurityQuote(ticker="GOOGL", date="2023-11-20", price=2800.0, issuer="Alphabet Inc.")
        return None
    
    monkeypatch.setattr("app.service.trade_service.get_quote", mock_get_quote)

def test_execute_purchase_order(setup, db_session):
    portfolio = setup["portfolio"]
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
    assert len(transactions) == 0
    user = db_session.query(User).filter_by(username="user").one()
    assert user.balance == 1000.00
    execute_purchase_order(portfolio.id, "AAPL", 2)
    db_session.commit()
    user = db_session.query(User).filter_by(username="user").one()
    assert user.balance == 700.00
    user_portfolio = user.portfolios[0]
    assert user_portfolio.investments is not None
    investments = user_portfolio.investments
    assert len(investments) == 1
    investment = investments[0]
    assert investment.ticker == "AAPL"
    assert investment.quantity == 2
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
    assert len(transactions) == 1
    assert transactions[0].ticker == "AAPL"
    assert transactions[0].quantity == 2
    assert transactions[0].price == 150.00
    assert transactions[0].transaction_type == "BUY"

def test_execute_purchase_order_insufficient_funds(setup, db_session):
    portfolio = setup["portfolio"]
    with pytest.raises(InsufficientFundsError) as e:
        execute_purchase_order(portfolio.id, "GOOGL", 1)
    assert str(e.value) == "Insufficient funds to complete the purchase."

def test_execute_order_for_nonexistent_portfolio(db_session):
    with pytest.raises(TradeExecutionException) as e:
        execute_purchase_order(999, "AAPL", 1)
    assert "Portfolio with id 999 does not exist." in str(e.value)

def test_execute_order_for_nonexistent_security(setup, db_session):
    portfolio = setup["portfolio"]
    with pytest.raises(TradeExecutionException) as e:
        execute_purchase_order(portfolio.id, "INVALID", 1)
    assert "Security with ticker INVALID could not be found via Alpha Vantage." in str(e.value)

def test_liquidate_investment(setup, db_session):
    portfolio = setup["portfolio"]
    execute_purchase_order(portfolio.id, "AAPL", 5)
    db_session.commit()
    
    liquidate_investment(portfolio.id, "AAPL", 5, 150.0)
    db_session.commit()
    portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one()
    updated_investment = next((inv for inv in portfolio.investments if inv.ticker == "AAPL"), None)
    assert updated_investment is None
    
def test_liquidate_investment_insufficient_quantity(setup, db_session):
    portfolio = setup["portfolio"]
    execute_purchase_order(portfolio.id, "AAPL", 2)
    db_session.commit()
    
    with pytest.raises(TradeExecutionException) as e:
        liquidate_investment(portfolio.id, "AAPL", 1000, 150.0)
    assert "Cannot liquidate 1000 shares of AAPL" in str(e.value)

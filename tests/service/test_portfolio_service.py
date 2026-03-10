import pytest
import app.service.portfolio_service as portfolio_service
from app.service.trade_service import liquidate_investment, TradeExecutionException
from app.models import Investment, Portfolio, User, PortfolioAccess

@pytest.fixture(autouse=True)
def setup(db_session):
    user = User(username="testuser", password="testpass", firstname="Test", lastname="User", balance=1000.0)
    db_session.add(user)
    db_session.commit()
    portfolio1 = Portfolio(name="Portfolio 1", description="First portfolio", user=user)
    portfolio2 = Portfolio(name="Portfolio 2", description="Second portfolio", user=user)
    db_session.add_all([portfolio1, portfolio2])
    db_session.commit()
    acc1 = PortfolioAccess(username=user.username, role='Owner', portfolio_id=portfolio1.id)
    acc2 = PortfolioAccess(username=user.username, role='Owner', portfolio_id=portfolio2.id)
    db_session.add_all([acc1, acc2])
    portfolio1.investments.append(Investment(ticker="AAPL", quantity=10))
    db_session.commit()
    return {
        "user": user,
        "portfolio1": portfolio1,
        "portfolio2": portfolio2
    }

def test_get_portfolios_by_user_db_failure(db_session, monkeypatch):
    def failing_query(*args, **kwargs):
        raise Exception("Database query error")
    monkeypatch.setattr(portfolio_service.db.session, 'query', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.get_portfolios_by_user(User(username="testuser"))
    assert "Database query error" in str(e.value)

def test_get_all_portfolios(db_session):
    portfolios = portfolio_service.get_all_portfolios()
    assert len(portfolios) >= 2
    names = [p.name for p in portfolios]
    assert "Portfolio 1" in names
    assert "Portfolio 2" in names

def test_get_all_portfolios_db_failure(monkeypatch):
    def failing_get_session(*args, **kwargs):
        raise Exception("Database connection error")
    monkeypatch.setattr(portfolio_service.db.session, 'query', failing_get_session)
    with pytest.raises(Exception) as e:
        portfolio_service.get_all_portfolios()
    assert "Database connection error" in str(e.value)

def test_get_portfolio_by_id(setup, db_session):
    portfolio = setup["portfolio1"]
    retrieved_portfolio = portfolio_service.get_portfolio_by_id(portfolio.id)
    assert retrieved_portfolio is not None
    assert retrieved_portfolio.name == "Portfolio 1"
    assert retrieved_portfolio.description == "First portfolio"

def test_get_portfolio_by_id_db_failure(db_session, monkeypatch):
    def failing_query(*args, **kwargs):
        raise Exception("Database connection error")
    monkeypatch.setattr(portfolio_service.db.session, 'query', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.get_portfolio_by_id(1)
    assert "Database connection error" in str(e.value)

def test_get_portfolio_by_invalid_id(db_session):
    invalid_id = 9999
    assert portfolio_service.get_portfolio_by_id(invalid_id) is None

def test_create_portfolio(setup, db_session):
    user = setup["user"]
    user_portfolios_before = portfolio_service.get_portfolios_by_user(user)
    assert len(user_portfolios_before) == 2
    portfolio_service.create_portfolio("Test Portfolio", "A test portfolio", user)
    user_portfolios_after = portfolio_service.get_portfolios_by_user(user)
    assert len(user_portfolios_after) == 3
    assert user_portfolios_after[-1].name == "Test Portfolio"
    assert user_portfolios_after[-1].description == "A test portfolio"

def test_create_portfolio_invalid_input():
    user = User(username="testuser", password="testpass", firstname="Test", lastname="User", balance=1000.0)
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError):
        portfolio_service.create_portfolio("", "A test portfolio", user)
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError):
        portfolio_service.create_portfolio("Test Portfolio", "", user)

def test_create_portfolio_db_failure(monkeypatch):
    def failing_get_session(*args, **kwargs):
        raise Exception("Database connection error")
    monkeypatch.setattr(portfolio_service.db.session, 'add', failing_get_session)
    with pytest.raises(Exception) as e:
        portfolio_service.create_portfolio("Fail Portfolio", "This should fail", User(username="user1"))
    assert "Database connection error" in str(e.value)
        
def test_delete_portfolio(setup, db_session):
    user = setup["user"]
    portfolio = Portfolio(name="To Be Deleted", description="This portfolio will be deleted", user=user)
    db_session.add(portfolio)
    db_session.commit()
    portfolio_service.delete_portfolio(portfolio.id)
    deleted_portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one_or_none()
    assert deleted_portfolio is None

def test_delete_portfolio_invalid_id(db_session):
    with pytest.raises(Exception):
        portfolio_service.delete_portfolio(9999)

def test_liquidate_investment(setup, db_session):
    portfolio = setup["portfolio1"]
    liquidate_investment(portfolio.id, "AAPL", 5, 150.0)
    db_session.commit()
    portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one()
    updated_investment = next((inv for inv in portfolio.investments if inv.ticker == "AAPL"), None)
    assert updated_investment is not None
    assert updated_investment.quantity == 5
    user = db_session.query(User).filter_by(username="testuser").one()
    assert user.balance == 1000.0 + (5 * 150.0)

def test_liquidate_entire_investment(setup, db_session):
    portfolio = setup["portfolio1"]
    liquidate_investment(portfolio.id, "AAPL", 10, 150.0)
    db_session.commit()
    portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one()
    updated_investment = next((inv for inv in portfolio.investments if inv.ticker == "AAPL"), None)
    assert updated_investment is None
    user = db_session.query(User).filter_by(username="testuser").one()
    assert user.balance == 1000.0 + (10 * 150.0)

def test_liquidate_investment_invalid_portfolio(db_session):
    with pytest.raises(TradeExecutionException):
        liquidate_investment(9999, "AAPL", 5, 150.0)

def test_liquidate_non_existing_investment(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(TradeExecutionException):
        liquidate_investment(portfolio.id, "MSFT", 5, 150.0)

def test_liquidate_investment_insufficient_quantity(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(TradeExecutionException) as e:
        liquidate_investment(portfolio.id, "AAPL", 1000, 150.0)
    assert "Cannot liquidate 1000 shares of AAPL. Only 10 shares available in portfolio" in str(e.value)
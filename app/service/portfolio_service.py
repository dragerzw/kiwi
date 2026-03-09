from typing import List

from app.db import db
from app.models import Portfolio, PortfolioAccess, User


class UnsupportedPortfolioOperationError(Exception):
    pass


class PortfolioOperationError(Exception):
    pass


def create_portfolio(name: str, description: str, user: User) -> Portfolio:
    if not name or not description or not user:
        raise UnsupportedPortfolioOperationError(
            f'Invalid input[name:{name}, description: {description}, user: {user}]. Please try again.'
        )
    portfolio = Portfolio(name=name, description=description, user=user)
    owner_access = PortfolioAccess(username=user.username, role='Owner')
    portfolio.accesses.append(owner_access)
    db.session.add(portfolio)
    return portfolio


def get_portfolios_by_user(user: User) -> List[Portfolio]:
    portfolios = db.session.query(Portfolio).join(Portfolio.accesses).filter(PortfolioAccess.username == user.username).all()
    return portfolios


def get_all_portfolios() -> List[Portfolio]:
    portfolios = db.session.query(Portfolio).all()
    return portfolios


def get_portfolio_by_id(portfolio_id: int) -> Portfolio | None:
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    return portfolio


def delete_portfolio(portfolio_id: int):
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist')
    db.session.delete(portfolio)

def grant_portfolio_access(portfolio_id: int, username: str, role: str):
    if role not in ['Owner', 'Manager', 'Viewer']:
        raise UnsupportedPortfolioOperationError(f'Invalid role {role}. Must be Owner, Manager, or Viewer.')
    
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise UnsupportedPortfolioOperationError(f'Portfolio {portfolio_id} does not exist.')
        
    access = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
    if access:
        access.role = role
    else:
        new_access = PortfolioAccess(username=username, portfolio_id=portfolio_id, role=role)
        db.session.add(new_access)

def revoke_portfolio_access(portfolio_id: int, username: str):
    access = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
    if not access:
        raise UnsupportedPortfolioOperationError(f'Access record for user {username} on portfolio {portfolio_id} does not exist.')
    if access.role == 'Owner':
        raise UnsupportedPortfolioOperationError(f'Cannot revoke access for the portfolio Owner.')
    db.session.delete(access)
    
def has_portfolio_access(portfolio_id: int, username: str, allowed_roles: List[str]) -> bool:
    access = db.session.query(PortfolioAccess).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
    if not access:
        return False
    return access.role in allowed_roles

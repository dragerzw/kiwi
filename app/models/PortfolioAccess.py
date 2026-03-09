from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db

if TYPE_CHECKING:
    from app.models import Portfolio, User

class PortfolioAccess(db.Model):
    __tablename__ = 'portfolio_access'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), ForeignKey('user.username'), nullable=False)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('portfolio.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # either 'Owner', 'Manager', or 'Viewer'

    user: Mapped['User'] = relationship('User', foreign_keys=[username], lazy='selectin')
    portfolio: Mapped['Portfolio'] = relationship(
        'Portfolio',
        foreign_keys=[portfolio_id],
        back_populates='accesses',
        lazy='selectin',
    )

    if TYPE_CHECKING:
        def __init__(
            self,
            *,
            username: str,
            portfolio_id: int,
            role: str,
        ) -> None: ...

    def __str__(self):
        return f'<PortfolioAccess: user={self.username}; portfolio_id={self.portfolio_id}; role={self.role}>'

    def __to_dict__(self):
        return {
            'username': self.username,
            'portfolio_id': self.portfolio_id,
            'role': self.role,
        }

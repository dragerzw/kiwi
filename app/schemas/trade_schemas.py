from pydantic import BaseModel


class TradeBuyRequest(BaseModel):
    portfolio_id: int
    ticker: str
    quantity: int


class TradeSellRequest(BaseModel):
    portfolio_id: int
    ticker: str
    quantity: int
    sale_price: float

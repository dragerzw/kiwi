from pydantic import BaseModel


class PortfolioCreateRequest(BaseModel):
    username: str
    name: str
    description: str

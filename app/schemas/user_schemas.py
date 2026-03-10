from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    username: str
    password: str
    firstname: str
    lastname: str
    balance: float


class UserUpdateBalanceRequest(BaseModel):
    username: str
    new_balance: float

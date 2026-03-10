from pydantic import BaseModel, Field

class PortfolioAccessRequest(BaseModel):
    username: str = Field(..., description="The username of the user to grant access to.")
    role: str = Field(..., description="The role to grant, e.g. Owner, Manager, Viewer.")

from pydantic import BaseModel


class AuthRequest(BaseModel):
    auth_code: str
    name: str
    shop_id: str
    country:str
    company_uid:str

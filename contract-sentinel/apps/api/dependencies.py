from typing import Optional
from fastapi import Header, HTTPException

async def get_tenant_id(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
        
    return token

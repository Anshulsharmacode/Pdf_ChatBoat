from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pymongo.errors import PyMongoError
from conf.db import user_collection

# class CheackAccess:
#     def __init__(self ,user_id:str ):
#         self.user_id = user_id

#     def check_access(self):
#         try:
#             user = user_collection.find_one ({"_id":self.user_id})
#             if user:
#                 return True
#             else:
#                 return False

#         except PyMongoError as e: 
#             print(f"Database error: {e}")
#             return False
#         except Exception as e:  
#             print(f"Unexpected error: {e}")
#             return False


from datetime import datetime, timedelta
from jose import JWTError, jwt


SECRET_KEY = "fadbsfgsuirhfweyerhjgui9yh"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

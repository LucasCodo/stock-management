from datetime import datetime, timedelta
from typing import List, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError, EmailStr
import os

from database import get_user_by_login, create_user, TypeUser
from secrets import token_hex

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None
    scopes: List[str] = []


class User(BaseModel):
    username: str
    fullname: str
    email: EmailStr
    type: int = 3


class UserInDB(User):
    hashed_password: str
    secret_number: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"me": "Read information about the current user."},
)


def verify_password(user: UserInDB, password: str):
    return pwd_context.verify(str(user.username+user.email+password+user.secret_number),
                              user.hashed_password)


def get_password_hash(username: str, email: str, password: str, secret_number: str):
    return pwd_context.hash(str(username+email+password+secret_number))


def get_user(login: str):
    user_dict = get_user_by_login(login)
    return UserInDB(**user_dict)


def authenticate_user(login: str, password: str):
    user = get_user(login)
    if not user:
        return False
    if not verify_password(user, password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    user = get_user(login=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user

root_user = os.getenv("root_user", "root")
if not get_user_by_login(root_user):
    secret_number = token_hex(32)
    username = root_user
    fullname = root_user
    email = os.getenv("root_email", root_user+"@"+root_user+"."+root_user)
    password = root_user
    password_hash = get_password_hash(username, email, password, secret_number)
    create_user(username, fullname, email, TypeUser.root.value, password_hash, secret_number)

if __name__ == "__main__":
    #secret_number = token_hex(32)
    #password_hash = get_password_hash("root", "root@root.root", "root", secret_number)
    #create_user("root", "root", "root@root.root", TypeUser.root.value, password_hash, secret__number)
    #print(get_user_by_login("root"))
    pass

import peewee
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from authenticator import *
from fastapi.security import OAuth2PasswordRequestForm
import database

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Product(BaseModel):
    name: str
    barcode: str
    description: str
    image: str
    unit: str
    quantity: float
    price: float
    pass


# Rota Root
@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/product/all")
async def products(limit: int = 0, current_user: User = Depends(get_current_user)):
    if current_user.type <= TypeUser.viewer.value:
        return database.list_products(limit)
    raise HTTPException(status_code=400, detail="Permission denied.")


@app.post("/product")
async def add_product(product: Product, current_user: User = Depends(get_current_user)):
    if current_user.type >= TypeUser.viewer.value:
        raise HTTPException(status_code=400, detail="Permission denied.")
    try:
        return database.insert_product(**dict(product))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/product")
async def update_product(product: Product, current_user: User = Depends(get_current_user)):
    if current_user.type > TypeUser.admin.value:
        raise HTTPException(status_code=400, detail="Permission denied.")
    try:
        return database.update_product_by_barcode(**dict(product))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/product")
async def delete_product(barcode: str, current_user: User = Depends(get_current_user)):
    if current_user.type > TypeUser.admin.value:
        raise HTTPException(status_code=400, detail="Permission denied.")
    try:
        database.delete_product_by_barcode(barcode)
        return HTTPException(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/sale-order/all")
async def sales_orders(current_user: User = Depends(get_current_user)):
    if current_user.type <= TypeUser.user.value:
        return database.list_sales_orders()
    raise HTTPException(status_code=400, detail="Permission denied.")


@app.post("/sale-order")
async def add_sales_order(table: Dict[str, float], description: str = None,
                          current_user: User = Depends(get_current_user)):
    if current_user.type >= TypeUser.viewer.value:
        raise HTTPException(status_code=400, detail="Permission denied.")
    try:
        return database.create_sales_order(table, description)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/sale-order")
async def update_sales_order(order_id: int, table: Dict[str, float], description: str = None,
                             current_user: User = Depends(get_current_user)):
    if current_user.type > TypeUser.admin.value:
        raise HTTPException(status_code=400, detail="Permission denied.")
    try:
        return database.update_sales_order(order_id, table, description)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/sale-order")
async def delete_sales_order(order_id: int, current_user: User = Depends(get_current_user)):
    if current_user.type > TypeUser.admin.value:
        raise HTTPException(status_code=400, detail="Permission denied.")
    try:
        database.delete_sales_order(order_id)
        return HTTPException(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password.")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/")
async def read_users(current_user: User = Depends(get_current_user)):
    if current_user.type in (TypeUser.root.value, TypeUser.admin.value):
        try:
            return {"Users": database.get_users()}
        except peewee.InternalError as e:
            return HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=400, detail="Permission denied.")


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Security(get_current_user, scopes=["me"])):
    return current_user


@app.post("/users")
async def add_user(user: User, password: str, current_user: User = Depends(get_current_user)):
    if current_user.type > user.type:
        raise HTTPException(status_code=400, detail="Permission denied.")
    if current_user.type in (TypeUser.root.value, TypeUser.admin.value):
        try:
            secret_number = token_hex(32)
            hashed_password = get_password_hash(user.username, user.email, password, secret_number)
            create_user(user.username, user.fullname, user.email, user.type, hashed_password,
                        secret_number)
            return HTTPException(status_code=200, detail="OK")
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
    raise HTTPException(status_code=400, detail="Permission denied.")

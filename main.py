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
async def products(limit: int = 0):
    return database.list_products(limit)


@app.post("/product")
async def add_product(product: Product):
    try:
        return database.insert_product(**dict(product))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/product")
async def update_product(product: Product):
    try:
        return database.update_product_by_barcode(**dict(product))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/product")
async def delete_product(barcode: str):
    try:
        database.delete_product_by_barcode(barcode)
        return HTTPException(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/sale-order/all")
async def sales_orders():
    return database.list_sales_orders()


@app.post("/sale-order")
async def add_sales_order(table: Dict[str, float], description: str = None):
    try:
        return database.create_sales_order(table, description)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/sale-order")
async def update_sales_order(order_id: int, table: Dict[str, float], description: str = None):
    try:
        return database.update_sales_order(order_id, table, description)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/sale-order")
async def delete_sales_order(order_id: int):
    try:
        database.delete_sales_order(order_id)
        return HTTPException(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

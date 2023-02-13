from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
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
def root():
    return {"status": "ok"}


@app.get("/product/all")
def products(limit: int = 0):
    return database.list_products(limit)


@app.post("/product")
def add_product(product: Product):
    try:
        return database.insert_product(**dict(product))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/product")
def update_product(product: Product):
    try:
        return database.update_product_by_barcode(**dict(product))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/product")
def delete_product(barcode: str):
    try:
        database.delete_product_by_barcode(barcode)
        return HTTPException(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/sale-order/all")
def sales_orders():
    return database.list_sales_orders()


@app.post("/sale-order")
def add_sales_order(table: Dict[str, float], description: str = None):
    try:
        return database.create_sales_order(table, description)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/sale-order")
def update_sales_order(order_id: int, table: Dict[str, float], description: str = None):
    try:
        return database.update_sales_order(order_id, table, description)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/sale-order")
def delete_sales_order(order_id: int):
    try:
        database.delete_sales_order(order_id)
        return HTTPException(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

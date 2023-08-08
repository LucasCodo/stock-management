import peewee
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from authenticator import *
from fastapi.security import OAuth2PasswordRequestForm
import database
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile

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
    if current_user.type > TypeUser.admin.value:
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
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.get("/users/")
async def read_users(current_user: User = Depends(get_current_user)):
    if current_user.type in (TypeUser.root.value, TypeUser.admin.value):
        return {"Users": database.get_users()}
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
            database.create_user(user.username, user.fullname, user.email, user.type,
                                 hashed_password, secret_number)
            return HTTPException(status_code=200, detail="OK")
        except peewee.IntegrityError as e:
            raise HTTPException(status_code=422, detail=str(e))
    raise HTTPException(status_code=400, detail="Permission denied.")


@app.put("/users/me/password")
async def update_password_user(password: str, current_user: UserInDB = Depends(get_current_user)):
    try:
        hashed_password = get_password_hash(current_user.username, current_user.email,
                                            password, current_user.secret_number)
        if database.update_user(current_user.username, hashed_password=hashed_password):
            return HTTPException(status_code=200, detail="OK")
    except peewee.IntegrityError as e:
        raise HTTPException(status_code=422, detail=str(e))
    raise HTTPException(status_code=400, detail="Permission denied.")


@app.get("/backup")
async def backup(current_user: UserInDB = Depends(get_current_user)):
    if current_user.type == TypeUser.root.value:
        with NamedTemporaryFile(delete=False) as file:
            file_path = file.name
            database.backup(file_path)
            date = datetime.now().date()
            return FileResponse(file_path, filename=f"backup-{date}.sql")
    else:
        raise HTTPException(status_code=401)


@app.post("/backup/restore")
async def restore_backup(file: UploadFile = File(..., media_type="application/x-sql"),
                         current_user: UserInDB = Depends(get_current_user)):
    if current_user.type == TypeUser.root.value:
        print(file.content_type)
        if file.content_type != "application/x-sql":
            raise HTTPException(status_code=422)
        contents = await file.read()
        file_name = None
        with NamedTemporaryFile(suffix=".sql", delete=False) as f:
            f.write(contents)
            file_name = f.name
        if file_name:
            database.restore_backup(file_name)
        raise HTTPException(status_code=200)
    else:
        raise HTTPException(status_code=401)

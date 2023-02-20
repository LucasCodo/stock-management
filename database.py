from peewee import *
from time import time
from math import fsum
import os

db_name = os.getenv("db_name")
user = os.getenv("db_user")
password = os.getenv("db_password")
host = os.getenv("db_host")
port = int(os.getenv("db_port"))
database = PostgresqlDatabase(database=db_name, user=user, password=password,
                              host=host, port=port)


class BaseModel(Model):
    time_stamp = IntegerField(default=int(time()), null=True)

    class Meta:
        database = database


class Products(BaseModel):
    name = TextField()
    barcode = TextField(unique=True)
    description = TextField(null=True, default="")
    image = TextField()
    quantity = FloatField()
    unit = TextField()
    price = FloatField()


class SalesOrders(BaseModel):
    description = TextField(null=True)
    pass


class ListProducts(BaseModel):
    product_id = ForeignKeyField(Products, backref="ListProducts")
    order_id = ForeignKeyField(SalesOrders, backref="ListProductsOrders")
    amount = FloatField(default=1)
    price = FloatField()


database.create_tables([Products, SalesOrders, ListProducts])


def query_to_dict(query):
    return [a.__dict__["__data__"] for a in query]


def insert_product(name: str, barcode: str, description: str, image: str,
                   quantity: float, unit: str, price: float):
    prod = Products(name=name, barcode=barcode, description=description, image=image,
                    quantity=quantity, unit=unit, price=price)
    prod.save()
    return prod.__dict__["__data__"]


def find_product_by_barcode(barcode: str):
    try:
        product = Products.get(Products.barcode == barcode)
        return product.__dict__["__data__"]
    except DoesNotExist:
        return None


def update_product_by_barcode(barcode: str, **kwargs):
    product = Products.get(Products.barcode == barcode)
    product.name = kwargs.get("name", product.name)
    product.description = kwargs.get("description", product.description)
    product.image = kwargs.get("image", product.image)
    product.quantity = kwargs.get("quantity", product.quantity)
    product.unit = kwargs.get("unit", product.unit)
    product.price = kwargs.get("price", product.price)
    product.save()
    return product.__dict__["__data__"]


def delete_product_by_barcode(barcode: str):
    try:
        product = Products.get(Products.barcode == barcode)
        product.delete_instance()
    except DoesNotExist:
        pass


def list_products(limit: int = 0):
    if limit > 0:
        query = Products.select().limit(limit)
        return query_to_dict(query)
    query = Products.select()
    return query_to_dict(query)


def get_sale_order(order_id):
    query = ListProducts.select().where(ListProducts.order_id == order_id)
    order = SalesOrders.get(SalesOrders.id == order_id)
    list_prod = query_to_dict(query)
    result = list()
    for item in list_prod:
        query = Products.get_by_id(item["product_id"])
        prod = query.__dict__["__data__"]
        d = item | prod
        for a in ["product_id", "order_id", "quantity", "id", "time_stamp"]:
            d.pop(a)
        d["price"] = item["price"]
        result += [d]
    return {"id": order_id, "products": result, "description": order.description,
            "time_stamp": order.time_stamp}


def create_list_products(prod: dict, order_id: int, amount: float):
    list_prods = ListProducts(product_id=prod["id"], order_id=order_id,
                              amount=amount, price=prod["price"])
    list_prods.save()
    update_product_by_barcode(prod["barcode"], **{"quantity": round(prod["quantity"]-amount, 4)})


def verify_quantity(prod: dict, amount: float):
    if amount > prod["quantity"]:
        raise Exception("Quantidade insuficiente! "
                        + prod["barcode"]+" tem disponivel "+str(prod["quantity"]))
    elif amount <= 0:
        raise ValueError("Valor invalido! valor:"+str(amount))


def create_sales_order(table_products: dict, description: str = ""):
    query = [Products.get(Products.barcode == barcode) for barcode in table_products]
    products = query_to_dict(query)
    for prod in products:
        amount = table_products[prod["barcode"]]
        verify_quantity(prod, amount)
    so = SalesOrders(description=description)
    so.save()
    for prod in products:
        amount = table_products[prod["barcode"]]
        create_list_products(prod, so.get_id(), amount)
    return get_sale_order(so.get_id())


def list_sales_orders():
    query = SalesOrders.select()
    result = list()
    for order in query:
        result += [get_sale_order(order.id)]
    return result


def delete_list_products(order_id: int):
    query = ListProducts.delete().where(ListProducts.order_id == order_id)
    sale_order = get_sale_order(order_id)
    for product in sale_order["products"]:
        quantity = find_product_by_barcode(product["barcode"])["quantity"]
        update_product_by_barcode(product["barcode"],
                                  **{"quantity": fsum([quantity, product["amount"]])})
    query.execute()


def delete_sales_order(order_id: int):
    try:
        delete_list_products(order_id)
        order = SalesOrders.get(order_id)
        order.delete_instance()
    except DoesNotExist:
        return None


def update_sales_order(order_id: int, table_products: dict, description: str):
    try:
        delete_list_products(order_id)
        query = [Products.get(Products.barcode == barcode) for barcode in table_products]
        products = query_to_dict(query)
        for prod in products:
            amount = table_products[prod["barcode"]]
            verify_quantity(prod, amount)
        order = SalesOrders.get(SalesOrders.id == order_id)
        order.description = description if description else order.description
        for prod in products:
            amount = table_products[prod["barcode"]]
            create_list_products(prod, order_id, amount)
        order.save()
        return get_sale_order(order_id)
    except DoesNotExist:
        return None


def get_sales_orders_by_time_interval(start: int = None, end: int = None):
    if start and end:
        query1 = SalesOrders.select().where(SalesOrders.time_stamp >= start)
        query2 = SalesOrders.select().where(SalesOrders.time_stamp <= end)
        query = set(query1).intersection(set(query2))
    elif start:
        query = SalesOrders.select().where(SalesOrders.time_stamp >= start)
    elif end:
        query = SalesOrders.select().where(SalesOrders.time_stamp <= end)
    list_orders = []
    for order in query:
        query = ListProducts.select().where(ListProducts.order_id == order.get_id())
        list_prod = query_to_dict(query)
        result = list()
        for item in list_prod:
            query = Products.get_by_id(item["product_id"])
            prod = query.__dict__["__data__"]
            d = item | prod
            for a in ["product_id", "order_id", "quantity", "id", "time_stamp"]:
                d.pop(a)
            result += [d]
        list_orders += [{"id": order.get_id(), "products": result, "description": order.description,
                         "time_stamp": order.time_stamp}]
    return list_orders


if __name__ == "__main__":
    insert_product(name="asdf", barcode="asdf", description="asdf", image="asdf",
                   unit="asdf", quantity=10, price=1.25)
    insert_product(name="asdf", barcode="asdfa", description="asdf", image="asdf",
                   unit="asdf", quantity=10, price=3.1)
    #print(list_products())
    create_sales_order({"asdfa": 2, "asdf": 2})
    #print(create_sales_order({"asdf": 987}))
    #print(get_sale_order(1))
    #dic = {"description": "Marca: barro forte","price": 5.5}
    #update_product_by_barcode("asdf", **dic)
    #delete_product_by_barcode("asdfa")
    #print(list_products())
    #print(find_product_by_barcode("asdfa"))

    #print(list_products())
    #delete_list_products(6)
    #print(list_sales_orders())
    #update_sales_order(6, {"asdfa": 2, "asdf": 1}, "descrição")
    #print(get_sales_orders_by_time_interval(end= 1676206916))
    #print(get_sale_order(6))
    #print(list_products())
    #update_product_by_barcode("asdf", **{"quantity": 50})

    pass

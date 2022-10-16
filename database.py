from peewee import *
from datetime import datetime
import os

user = os.getenv("db_user")
password = os.getenv("db_password")
host = os.getenv("db_host")
port = int(os.getenv("db_port"))
pg_db = PostgresqlDatabase("stock", user=user, password=password,
                           host=host, port=port)


class BaseModel(Model):
    time_stamp = DateTimeField(default=datetime.now, null=True)

    class Meta:
        database = pg_db


class Products(BaseModel):
    name = TextField()
    code_ncm = IntegerField()
    description = TextField()
    number_units = FloatField()
    type_units = TextField()
    value_units = FloatField()
    amount = FloatField(default=(number_units*value_units))


class Orders(BaseModel):
    pass


class ListProducts(BaseModel):
    product_id = ForeignKeyField(Products, backref="ListProducts")
    order_id = ForeignKeyField(Orders, backref="ListProducts")
    number_units = FloatField()
    value_units = FloatField()
    amount = FloatField(default=(number_units * value_units))


pg_db.create_tables([Products, Orders, ListProducts])


if __name__ == "__main__":
    print()

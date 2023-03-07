from string import ascii_uppercase, digits
from secrets import choice
from typing import Dict


class Coupon:
    def __init__(self, table: Dict[str, float], size: int = 8):
        self._coupon: str = "".join([choice(ascii_uppercase+digits) for a in range(size)])
        self._table = table

    def items(self):
        return self._table,

    def __repr__(self):
        return self._coupon


class CouponManager:
    def __init__(self):
        self._coupons: Dict[str, Coupon] = dict()
        pass

    def get_items(self, coupons_code: str):
        item = self._coupons.get(coupons_code, None)
        if item:
            return item.items()
        return None

    def add(self, table: dict):
        coupon = Coupon(table)
        self._coupons[str(coupon)] = coupon
        return str(coupon)


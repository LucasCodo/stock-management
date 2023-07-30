from enum import Enum


class TypeUser(Enum):
    root: int = 0
    admin: int = 1
    user: int = 2
    viewer: int = 3


class TypeUnits(Enum):
    m = "Meters"
    cm = "Centimeters"
    mm = "Millimeter"
    T = "Tonne"
    Kg = "Kilograms"
    g = "Gram"
    L = "Liter"
    ml = "Milliliter"
    m2 = "Square Meter"
    m3 = "Cubic Meter"

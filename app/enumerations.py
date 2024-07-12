from enum import Enum


class TypeUser(Enum):
    root = 0
    admin = 1
    user = 2
    viewer = 3


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

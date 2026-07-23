from typing import NamedTuple, List
from datetime import date

class Estrazione:
    def __new__(cls, data, numeri, jolly, supers):
        return super().__new__(cls)

    def __init__(self, data, numeri, jolly, supers):
        self.data = data
        self.numeri = numeri
        self.jolly = jolly
        self.supers = supers
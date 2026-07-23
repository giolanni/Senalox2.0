# File: src/model/estrazione.py
from datetime import date

class Estrazione:
    def __init__(self, data: date, numeri: list[int], jolly: int, superstar: int):
        self.data = data
        self.numeri = numeri
        self.jolly = jolly
        self.superstar = superstar

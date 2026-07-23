"""
Modello condiviso di una singola estrazione del SuperEnalotto.

La classe espone sia l'attributo ``superstar`` sia l'alias storico ``supers``,
così la versione legacy e New Senalox possono utilizzare lo stesso oggetto
senza modifiche immediate a tutto il codice esistente.
"""

from datetime import date
from typing import List


class Estrazione:
    """
    Rappresenta una singola estrazione.

    Parameters
    ----------
    data
        Data dell'estrazione.
    numeri
        I sei numeri estratti.
    jolly
        Numero Jolly.
    superstar
        Numero SuperStar.
    """

    def __init__(
        self,
        data: date,
        numeri: List[int],
        jolly: int,
        superstar: int
    ):
        self.data = data
        self.numeri = numeri
        self.jolly = jolly
        self.superstar = superstar

    @property
    def supers(self) -> int:
        """
        Alias compatibile con il nome usato nella versione legacy.
        """

        return self.superstar

    @supers.setter
    def supers(self, value: int) -> None:
        """
        Consente al vecchio codice di assegnare ancora ``supers``.
        """

        self.superstar = value
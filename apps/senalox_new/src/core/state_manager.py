from enum import Enum
from datetime import date

class AppMode(Enum):
    FULL = "FULL"
    POST_2009 = "2009"

class ApplicationState:
    def __init__(self):
        self.mode = AppMode.FULL
        self.estrazioni_full = []
        self.estrazioni_filtered = []
        
    def set_mode(self, mode: AppMode):
        self.mode = mode
        cutoff = date(2009, 7, 1) if mode == AppMode.POST_2009 else None
        self.estrazioni_filtered = [e for e in self.estrazioni_full if not cutoff or e.data >= cutoff]
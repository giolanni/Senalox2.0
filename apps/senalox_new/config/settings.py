from enum import Enum
from datetime import datetime

class Mode(Enum):
    FULL = "full"
    POST_2009 = "2009"

# Configurazione globale
CONFIG = {
    'mode': Mode.POST_2009,
    'filter_date': datetime(2009, 7, 1).date(),
    'data_path': './data'
}

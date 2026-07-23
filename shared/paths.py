"""
Gestione centralizzata dei percorsi del progetto Senalox.

Il modulo definisce in un solo punto le cartelle principali usate dal launcher
unificato e dalle due applicazioni.

Il file delle estrazioni è condiviso da Senalox 1.0 e New Senalox e deve
esistere in:

    shared/data/estrazioni.csv
"""
from pathlib import Path


# Cartella principale del progetto Senalox.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cartella che contiene le due applicazioni.
APPS_DIR = PROJECT_ROOT / "apps"

# Cartelle delle due versioni.
LEGACY_DIR = APPS_DIR / "senalox_legacy"
NEW_DIR = APPS_DIR / "senalox_new"

# Cartella condivisa e relativo archivio dati unico.
SHARED_DIR = PROJECT_ROOT / "shared"
DATA_DIR = SHARED_DIR / "data"
ESTRAZIONI_FILE = DATA_DIR / "estrazioni.csv"

# Cartella dei log del progetto.
LOGS_DIR = PROJECT_ROOT / "logs"

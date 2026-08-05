"""Risoluzione robusta della radice del progetto Senalox."""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_root() -> Path:
    """
    Trova la cartella Senalox e la aggiunge a ``sys.path``.

    Consente di eseguire gli script sia dalla radice del progetto sia dalle
    sottocartelle di ``analysis`` senza dipendere dalla directory corrente.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "shared" / "data_loader.py").exists():
            root = parent
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            return root
    raise RuntimeError("Impossibile individuare la radice del progetto Senalox.")

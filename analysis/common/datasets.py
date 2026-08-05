"""Accesso uniforme ai dataset OVERALL e NEW_MODE."""
from __future__ import annotations

from typing import Literal

from analysis.common.project import ensure_project_root

ensure_project_root()

from shared.data_loader import load_estrazioni_new_mode, load_estrazioni_overall
from shared.models.estrazione import Estrazione

DatasetName = Literal["OVERALL", "NEW_MODE"]


def load_dataset(name: DatasetName) -> list[Estrazione]:
    normalized = name.upper()
    if normalized == "OVERALL":
        return load_estrazioni_overall()
    if normalized == "NEW_MODE":
        return load_estrazioni_new_mode()
    raise ValueError(f"Dataset non riconosciuto: {name}")

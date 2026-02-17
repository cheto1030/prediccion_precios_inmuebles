from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple
import json

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# En local puede existir (si entrenaste con el CSV). En Render normalmente NO.
TRAIN_PATH = BASE_DIR / "train.csv"

# En producción (Render) usaremos este JSON con todos los defaults (79 columnas)
DEFAULTS_JSON_PATH = BASE_DIR / "defaults_full.json"


def compute_defaults(train_path: Path) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Calcula valores por defecto desde el dataset de entrenamiento:
    - Numéricas -> mediana
    - Categóricas -> moda (valor más frecuente)
    Devuelve:
      DEFAULTS: dict(columna -> valor por defecto)
      FEATURE_TYPES: dict(columna -> "numeric"|"categorical")
    """
    df = pd.read_csv(train_path)

    # Quitamos columnas que no son features de entrada
    for col in ["SalePrice", "Id"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    defaults: Dict[str, Any] = {}
    types: Dict[str, str] = {}

    # Detectamos columnas numéricas y categóricas
    numeric_cols = df.select_dtypes(include=["number"]).columns
    cat_cols = df.select_dtypes(include=["object"]).columns

    # Numéricas: mediana (más robusto que la media ante outliers)
    for c in numeric_cols:
        types[c] = "numeric"
        defaults[c] = float(df[c].median()) if df[c].notna().any() else 0.0

    # Categóricas: moda (valor más frecuente)
    for c in cat_cols:
        types[c] = "categorical"
        mode = df[c].mode(dropna=True)
        defaults[c] = str(mode.iloc[0]) if len(mode) > 0 else "Unknown"

    return defaults, types


# ----------------------------
# Inicialización robusta
# ----------------------------
# 1) LOCAL: si hay train.csv -> calculamos defaults reales del dataset
# 2) PRODUCCIÓN: si NO hay train.csv -> cargamos defaults_full.json (subido a GitHub)
if TRAIN_PATH.exists():
    DEFAULTS, FEATURE_TYPES = compute_defaults(TRAIN_PATH)

elif DEFAULTS_JSON_PATH.exists():
    # Cargamos defaults desde JSON para que Render pueda arrancar sin el dataset
    DEFAULTS = json.loads(DEFAULTS_JSON_PATH.read_text(encoding="utf-8"))

    # Inferimos el tipo de feature según el valor por defecto del JSON
    FEATURE_TYPES = {}
    for k, v in DEFAULTS.items():
        FEATURE_TYPES[k] = "numeric" if isinstance(v, (int, float)) else "categorical"

else:
    # Si falta todo, fallamos rápido con un error claro (mejor que fallar en /predict)
    raise RuntimeError(
        "No se encontró api/train.csv (local) ni api/defaults_full.json (producción). "
        "No puedo inicializar DEFAULTS/FEATURE_TYPES."
    )


def fill_missing_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rellena las columnas que falten usando DEFAULTS.
    También limpia NaN/Inf para evitar errores de JSON y del modelo.
    """
    filled: Dict[str, Any] = {}

    for col, default_val in DEFAULTS.items():
        val = features.get(col, None)

        # Si viene NaN o Inf, lo convertimos a None (evita InvalidJSONError)
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            val = None

        # Si el usuario no envía la columna -> usamos default
        if val is None:
            val = default_val

        filled[col] = val

    return filled




from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# Path correcto a tu train.csv (en local puede existir, en Render no)
TRAIN_PATH = BASE_DIR / "train.csv"


def compute_defaults(train_path: Path) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Calcula valores por defecto a partir del train:
    - numéricas -> mediana
    - categóricas -> moda
    Devuelve:
      defaults: dict columna -> valor_default
      types: dict columna -> "numeric"|"categorical"
    """
    df = pd.read_csv(train_path)

    # Eliminar columnas no predictoras si existen
    for col in ["SalePrice", "Id"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    defaults: Dict[str, Any] = {}
    types: Dict[str, str] = {}

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    cat_cols = df.select_dtypes(include=["object"]).columns

    # Numéricas: mediana
    for c in numeric_cols:
        types[c] = "numeric"
        defaults[c] = float(df[c].median()) if df[c].notna().any() else 0.0

    # Categóricas: moda
    for c in cat_cols:
        types[c] = "categorical"
        mode = df[c].mode(dropna=True)
        defaults[c] = str(mode.iloc[0]) if len(mode) > 0 else "Unknown"

    return defaults, types


# ----------------------------
# FALLBACK (para producción)
# ----------------------------
# Estos valores permiten arrancar la API en Render aunque NO exista api/train.csv.
# Son defaults "razonables" para los campos que usa tu frontend.
DEFAULTS: Dict[str, Any] = {
    "OverallQual": 5.0,
    "GrLivArea": 1500.0,
    "TotalBsmtSF": 900.0,
    "YearBuilt": 2000.0,
    "Neighborhood": "NAmes",
    "GarageCars": 2.0,
    "FullBath": 2.0,
    "BedroomAbvGr": 3.0,
}

FEATURE_TYPES: Dict[str, str] = {
    "OverallQual": "numeric",
    "GrLivArea": "numeric",
    "TotalBsmtSF": "numeric",
    "YearBuilt": "numeric",
    "Neighborhood": "categorical",
    "GarageCars": "numeric",
    "FullBath": "numeric",
    "BedroomAbvGr": "numeric",
}

# Si existe train.csv (local), recalculamos los defaults reales del dataset
if TRAIN_PATH.exists():
    DEFAULTS, FEATURE_TYPES = compute_defaults(TRAIN_PATH)


def fill_missing_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rellena campos faltantes con defaults.
    Convierte NaN/inf a None para evitar problemas de JSON.
    """
    filled: Dict[str, Any] = {}

    for col, default_val in DEFAULTS.items():
        val = features.get(col, None)

        # Normalización de NaN/inf -> None
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            val = None

        # Si no viene o viene como None -> usar default
        if val is None:
            val = default_val

        filled[col] = val

    return filled


from pathlib import Path
import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_PATH = BASE_DIR / "house_prices_artifact.joblib"

artifact = joblib.load(ARTIFACT_PATH)


def predict_price(raw_df: pd.DataFrame) -> np.ndarray:
    """
    Predice SalePrice en escala original.
    raw_df debe contener las mismas columnas que el modelo espera
    (sin Id y sin SalePrice).
    """

    model = artifact["model"]
    skewed_features = artifact.get("skewed_features", [])

    df = raw_df.copy()

    # Aplicar log1p a columnas sesgadas
    for col in skewed_features:
        if col in df.columns:
            df[col] = np.log1p(df[col])

    pred_log = model.predict(df)

    return np.expm1(pred_log)

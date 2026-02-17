import uuid
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any

from api.model_utils import predict_price

from api.defaults import fill_missing_features, DEFAULTS, FEATURE_TYPES
from fastapi.middleware.cors import CORSMiddleware




BASE_DIR = Path(__file__).resolve().parent
FEEDBACK_PATH = BASE_DIR / "data" / "feedback.csv"

app = FastAPI(
    title="House Prices ML API",
    description="API para predicción de precios y recolección de feedback.",
    version="1.0.0"
)

# Permite llamadas desde el frontend (local + Vercel) a esta API
app.add_middleware(
    CORSMiddleware,
    # Orígenes permitidos (tu Next.js en local y tu dominio de Vercel)
    allow_origins=[
        "http://localhost:3000",
        "https://prediccion-precios-inmuebles.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # Permitimos GET/POST/etc
    allow_headers=["*"],   # Permitimos headers típicos (Content-Type, etc.)
)




class PredictRequest(BaseModel):
    features: Dict[str, Any]


class PredictResponse(BaseModel):
    prediction_id: str
    sale_price: float


class FeedbackRequest(BaseModel):
    features: Dict[str, Any]
    sale_price_real: float = Field(..., gt=0)


class FeedbackResponse(BaseModel):
    saved: bool
    row_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        # Rellenar features faltantes con defaults (permite inputs parciales)
        filled = fill_missing_features(req.features)

        # Convertimos a DataFrame (una fila)
        df = pd.DataFrame([filled])

        # Predicción
        pred = float(predict_price(df)[0])
        
        # Redondeo para no devolver decimales excesivos
        pred = round(pred, 2)

        return PredictResponse(
            prediction_id=str(uuid.uuid4()),
            sale_price=pred
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest):
    try:
        row_id = str(uuid.uuid4())

        # Rellenar features faltantes con defaults (para que siempre haya todas las columnas)
        filled = fill_missing_features(req.features)

        # Predicción actual del modelo para esta vivienda (útil para monitorización)
        df_pred = pd.DataFrame([filled])
        sale_price_pred = float(predict_price(df_pred)[0])
        sale_price_pred = round(sale_price_pred, 2)

        # Construir fila a guardar (features + real + pred + error + id)
        row = filled.copy()
        row["SalePrice_real"] = float(req.sale_price_real)
        row["SalePrice_pred"] = sale_price_pred
        row["Error"] = round(row["SalePrice_real"] - row["SalePrice_pred"], 2)
        row["row_id"] = row_id

        df_row = pd.DataFrame([row])

        FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Guardado robusto: alinear columnas si el CSV ya existe
        if FEEDBACK_PATH.exists():
            old = pd.read_csv(FEEDBACK_PATH)

            # Unión de columnas antiguas + nuevas (manteniendo orden)
            all_cols = list(dict.fromkeys(list(old.columns) + list(df_row.columns)))

            old = old.reindex(columns=all_cols)
            df_row = df_row.reindex(columns=all_cols)

            new_df = pd.concat([old, df_row], ignore_index=True)
            new_df.to_csv(FEEDBACK_PATH, index=False)
        else:
            df_row.to_csv(FEEDBACK_PATH, index=False)

        return FeedbackResponse(saved=True, row_id=row_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    
    
    
@app.get("/schema")
def schema():
    """
    Devuelve información de features para ayudar al frontend:
    - lista de columnas esperadas
    - tipo de cada columna
    - valor por defecto
    """
    return {
        "features": [
            {
                "name": col,
                "type": FEATURE_TYPES.get(col, "unknown"),
                "default": DEFAULTS.get(col, None)
            }
            for col in DEFAULTS.keys()
        ]
    }


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import joblib
import pandas as pd
import numpy as np
import os

# 1. Configuração Inicial
app = FastAPI(title="Smart Home Anomaly API", version="1.0")

#Código que permite que a fastAPI envie os dados para o react
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que qualquer frontend se ligue (localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#Buscamos o local exato onde estão os ficheiros criados no treino do modelo
base_dir = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.abspath(os.path.join(base_dir, "..", 'rf_routine_model.pkl'))
FEATURES_PATH = os.path.abspath(os.path.join(base_dir, "..", 'rf_features.pkl'))
LABEL_MAPPING_PATH = os.path.abspath(os.path.join(base_dir, "..", 'rf_label_mapping.pkl'))

#Limite que é usado para mostrar se uma situação é anomala ou não
ANOMALY_CONFIDENCE_THRESHOLD = 50

# Variáveis globais para guardar a IA na memória
rf_model = None
feature_cols = None
inv_mapping = None

# 2. Carregar a Inteligência Artificial quando a API liga
@app.on_event("startup")
def load_ai():
    global rf_model, feature_cols, inv_mapping
    try:
        rf_model = joblib.load(MODEL_PATH)
        feature_cols = joblib.load(FEATURES_PATH)
        label_mapping = joblib.load(LABEL_MAPPING_PATH)
        # Criamos o dicionário inverso (ex: 8 -> "Sleeping")
        inv_mapping = {v: k for k, v in label_mapping.items()}
        print("✅ Inteligência Artificial carregada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar os modelos: {e}")

# 3. Definir o que o React tem de nos enviar (O "Molde" dos dados)
class SensorData(BaseModel):
    # O React pode mandar um dicionário solto com a hora, dia e os valores dos sensores
    # Ex: {"hour": 23, "day_of_week": 4, "M003": 1.0, "T001": 21.5, ...}
    readings: Dict[str, float]

def predict_activity(readings: dict) -> dict:
    """Função pura reutilizável — usada pelo endpoint e pelo simulador."""
    if rf_model is None:
        raise RuntimeError("Modelo não carregado.")

    input_data = {col: [readings.get(col, 0.0)] for col in feature_cols}
    df_input = pd.DataFrame(input_data)

    pred_encoded = rf_model.predict(df_input)[0]
    pred_proba = rf_model.predict_proba(df_input)[0]
    confianca = float(np.max(pred_proba) * 100)
    atividade = inv_mapping.get(pred_encoded, "Unknown")
    is_anomaly = confianca < ANOMALY_CONFIDENCE_THRESHOLD

    sensores_ativos = [c for c in feature_cols if c.startswith('M') and df_input[c][0] > 0.0]
    motivo = "ao padrão habitual para esta hora do dia e divisão."
    if "M003" in sensores_ativos and atividade == "Sleeping":
        motivo = "ao movimento e presença prolongada detetados na zona da cama."
    elif atividade == "Leave_Home":
        motivo = "à ausência total de movimento no interior da casa nos últimos minutos."
    elif sensores_ativos:
        motivo = f"aos sensores detetados na zona: {sensores_ativos[0]}."

    return {
        "expected_activity": atividade,
        "confidence": round(confianca, 3),
        "is_anomaly": is_anomaly,
        "message": "Padrão não reconhecido!" if is_anomaly else "Tudo normal.",
        "reason": motivo,
    }

# 4. A Ponte Principal (O Endpoint de Previsão)
@app.post("/api/model/infer")
def predict_routine(data: SensorData):
    if rf_model is None:
        raise HTTPException(status_code=500, detail="Modelo de IA não está carregado.")
    try:
        return predict_activity(data.readings)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

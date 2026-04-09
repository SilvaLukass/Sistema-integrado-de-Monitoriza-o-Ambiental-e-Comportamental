from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from data_processor import DataProcessor

#Inicializar a Aplicação FastAPI
app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite qualquer origem (ideal para desenvolvimento)
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos os headers
)

processor = DataProcessor('kaggle_smartHome_data.csv')

#Carregar o modelo e o scaler
try:
    modelo = joblib.load('iforest_model.pkl')
    scaler = joblib.load('scaler.pkl')
    print("Modelo e scaler carregados")
except Exception as e:
    print(f"ERRO a carregar os ficheiros .pkl: {e}")

#Definimos a estrutura de dados que a API Irá receber
class SensorData(BaseModel):
    device_id: str
    co: float
    humidity: float
    light: bool
    lpg: float
    motion: bool
    smoke: float
    temp: float

@app.get("/predict/heatmap")
def heatmap():
    return processor.get_heatmap_stats()

@app.post("/analisar") #Cria uma rota principal para a FastAPI
def analisar_sensores(dados: SensorData):

    #Conversão dos dados para DataFrame que o modelo possa ler
    df_novo = pd.DataFrame([{
        'co':dados.co,
        'humidity':dados.humidity,
        'light':float(dados.light),
        'lpg':dados.lpg,
        'motion':float(dados.motion),
        'smoke':dados.smoke,
        'temp':dados.temp
    }])

    dados_escalonados = scaler.transform(df_novo)

    is_anomaly = modelo.predict(dados_escalonados)[0] #Retorna 0 ou 1

    score = modelo.decision_function(dados_escalonados)[0]

    #Lógica da explicabilidade (O que causou a anomalia?)

    causa = "Nenhuma"
    if is_anomaly == 1:
        desvios = np.abs(dados_escalonados[0])
        index_maiorDesvio=np.argmax(desvios)
        nome_culpado = df_novo.columns[index_maiorDesvio]

        causa = f"Valores anormais detetados no sensor: {nome_culpado.upper()}"

    return {
        "device_id":dados.device_id,
        "anomalia_detetada": bool(is_anomaly == 1),
        "nivel_de_risco": round(float(score),3),
        "diagnostico": causa,
        "mensagem": "ALERTA: Verificar habitação!" if is_anomaly == 1 else "Tudo normal."
    }


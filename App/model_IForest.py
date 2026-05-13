import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
 
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from pyod.models.iforest import IForest
 
from data_processor import DataProcessor

# -----------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------
CONTAMINATION   = 0.05   # Estimativa da % de anomalias nos dados de treino
                          # 0.05 = assumimos ~5% de leituras anómalas
N_ESTIMATORS    = 100     # Número de árvores no IsolationForest
RANDOM_STATE    = 42
MODEL_PATH      = 'iforest_model.pkl'
SCALER_PATH     = 'scaler.pkl'
FEATURE_PATH    = 'feature_columns.pkl'   # guardamos as colunas usadas

#Treinamento do modelo
def train_anomaly_detector(matrix: pd.DataFrame):
    """
    Treina o IsolationForest com os dados históricos.
 
    O IsolationForest é NÃO-supervisionado, por isso a coluna
    'label_encoded' NÃO é usada no treino — serve apenas para avaliação.
    """
    #Separamos as features (dados) das labels
    feature_cols = [c for c in matrix.columns if c != 'label_encoded']
    X = matrix[feature_cols].values

    #Normalizamos os dados, para não haver nenhum dominio por parte de nenhum sensor com escalas diferentes
    scaler=StandardScaler()
    X_scaled = scaler.fit_transform(X)

    #Configuramos o modelo
    model = IForest(
        contamination=CONTAMINATION, 
        n_estimators=N_ESTIMATORS,
        random_state=RANDOM_STATE
        )
    
    #Treinar modelo
    model.fit(X_scaled)     #Desenhamos a linha no gráfico que melhor se aproxime de todos os dados

    # Guardar tudo
    joblib.dump(model,        MODEL_PATH)
    joblib.dump(scaler,       SCALER_PATH)
    joblib.dump(feature_cols, FEATURE_PATH)

    print(f"[Trainer] Modelo treinado com {X.shape[0]:,} amostras e {X.shape[1]} features.")
    print(f"[Trainer] Ficheiros guardados: {MODEL_PATH}, {SCALER_PATH}, {FEATURE_PATH}")
 
    return model, scaler, feature_cols

def test_anomaly_detector(model, scaler, feature_cols: list, matrix: pd.DataFrame):
    """
    Aplica o modelo à matriz completa e imprime métricas de avaliação.
 
    Nota sobre interpretação:
      - O IsolationForest devolve 1 (normal) e -1 (anomalia) na pyod.
      - Na pyod especificamente: predict() devolve 0 (normal) e 1 (anomalia).
      - A 'ground truth' que usamos é simplificada: consideramos 'No_Activity'
        como normal (0) e qualquer outra atividade como potencial evento (1).
        Isto NÃO é a forma correta de avaliar um detetor de anomalias puro,
        mas permite ter uma métrica indicativa com os dados que temos.
    """

    X = matrix[feature_cols].values
    X_scaled = scaler.transform(X)

    # Previsões: 0 = normal, 1 = anomalia (convenção pyod)
    predictions = model.predict(X_scaled)
    scores      = model.decision_function(X_scaled)  # quanto mais negativo, mais anómalo
 
    matrix = matrix.copy()
    matrix['anomaly_predicted'] = predictions
    matrix['anomaly_score']     = scores

    label_map_inv = {v: k for k, v in DataProcessor.__new__(DataProcessor).label_mapping.items()} \
        if False else None  # placeholder — usamos outra abordagem abaixo
    
    # Carregamos o mapeamento diretamente da matriz
    # Como não temos acesso ao processor aqui, fazemos uma ground truth simples:
    # anomalia detetada vs. não detetada (sem ground truth externa)
    n_anomalias = (predictions == 1).sum()
    pct         = 100 * n_anomalias / len(predictions)
    print(f"\n[Avaliação] Total de amostras analisadas : {len(predictions):,}")
    print(f"[Avaliação] Anomalias detetadas          : {n_anomalias:,} ({pct:.2f}%)")
    print(f"[Avaliação] (Contamination configurada   : {CONTAMINATION*100:.1f}%)")

    return matrix

def plot_anomaly_scores(matrix: pd.DataFrame, sensor_temp: str = None):
    """
    Dois gráficos:
      1. Score de anomalia ao longo do tempo
      2. Temperatura (se existir) com anomalias marcadas a vermelho
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
 
    # Gráfico 1 — Score de anomalia
    axes[0].plot(matrix.index, matrix['anomaly_score'], color='steelblue', alpha=0.6, linewidth=0.8)
    axes[0].axhline(0, color='red', linestyle='--', linewidth=1, label='Limiar')
    axes[0].set_ylabel('Score de Anomalia')
    axes[0].set_title('Score de Anomalia ao Longo do Tempo')
    axes[0].legend()
 
    # Gráfico 2 — Sensor de temperatura
    if sensor_temp and sensor_temp in matrix.columns:
        normais   = matrix[matrix['anomaly_predicted'] == 0]
        anomalias = matrix[matrix['anomaly_predicted'] == 1]
 
        axes[1].plot(matrix.index, matrix[sensor_temp],
                     color='steelblue', alpha=0.5, linewidth=0.8, label='Normal')
        axes[1].scatter(anomalias.index, anomalias[sensor_temp],
                        color='red', s=10, label='Anomalia', zorder=5)
        axes[1].set_ylabel('Temperatura (ºC)')
        axes[1].set_title(f'Sensor {sensor_temp} — Anomalias Detetadas')
        axes[1].legend()
    else:
        # Se não há temperatura, mostrar distribuição de anomalias por hora
        anomalias_por_hora = matrix.groupby(matrix.index.hour)['anomaly_predicted'].sum()
        axes[1].bar(anomalias_por_hora.index, anomalias_por_hora.values, color='salmon')
        axes[1].set_xlabel('Hora do Dia')
        axes[1].set_ylabel('Nº de Anomalias')
        axes[1].set_title('Distribuição de Anomalias por Hora')
 
    plt.tight_layout()
    plt.savefig('anomaly_results.png', dpi=150)
    plt.show()
    print("[Visualização] Gráfico guardado em 'anomaly_results.png'")

if __name__ == "__main__":
 
    # 1. Carregar e processar dados
    print("=== Passo 1: Processar dados ===")
    processor = DataProcessor()
    matrix    = processor.get_matrix_for_model()
 
    if matrix.empty:
        print("ERRO: A matriz está vazia. Verifica o ficheiro de dados.")
        exit(1)
 
    # 2. Treinar o modelo
    print("\n=== Passo 2: Treinar modelo ===")
    model, scaler, feature_cols = train_anomaly_detector(matrix)
 
    # 3. Avaliar sobre os mesmos dados históricos
    #    (sem dados de teste separados, isto é treino = teste — aceitável
    #     para uma demonstração académica; idealmente usarias um split temporal)
    print("\n=== Passo 3: Avaliar ===")
    matrix_com_resultados = test_anomaly_detector(model, scaler, feature_cols, matrix)
 
    # 4. Visualizar
    print("\n=== Passo 4: Visualizar ===")
    # Tenta encontrar automaticamente um sensor de temperatura
    temp_sensors = [c for c in feature_cols if c.startswith('T')]
    sensor_para_grafico = temp_sensors[0] if temp_sensors else None
    plot_anomaly_scores(matrix_com_resultados, sensor_temp=sensor_para_grafico)
 
    # 5. Mostrar amostra dos resultados
    print("\n=== Amostra de Anomalias Detetadas ===")
    anomalias = matrix_com_resultados[matrix_com_resultados['anomaly_predicted'] == 1]
    print(anomalias.head(10))
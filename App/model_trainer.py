from pyod.models.iforest import IForest
from data_processor import file_cleaner_loader, transform_to_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import matplotlib.pyplot as plt

COLUNAS_SENSORES = ['co', 'humidity', 'light', 'lpg', 'motion', 'smoke', 'temp']

#Função responsável por treinar modelo de machine Learning

def train_anomaly_detector(matrix):

    matrix = matrix[COLUNAS_SENSORES]

    #Normalizamos os dados
    scaler=StandardScaler()

    #Ajustamos o scaler aos dados e transformamos a matriz
    matrix_scaled = scaler.fit_transform(matrix)

    #Configuramos o modelo
    model = IForest(contamination=0.001, n_estimators=100,random_state=42)
    
    #Treinar modelo
    model.fit(matrix_scaled)

    #Guardamos o modelo treinado para ser utilizado na webApp
    joblib.dump(model,'iforest_model.pkl')
    joblib.dump(scaler,'scaler.pkl')

    print('Modelo treinado e guardado como \'iforest_model.pkl\'')
    return model,scaler

def plot_anomalies(matrix, sensor_id):
    plt.figure(figsize=(12, 6))
    
    sensor_data = matrix.xs(sensor_id, level='device')

    # Desenhar a temperatura normal em azul
    plt.plot(sensor_data.index, sensor_data['temp'], color='blue', label='Temperatura', alpha=0.5)
    
    # Marcar as anomalias com pontos vermelhos
    anomalias = sensor_data[sensor_data['isAnomaly'] == 1]
    plt.scatter(anomalias.index, anomalias['temp'], color='red', label='Anomalia Detetada')
    
    plt.title(f"Deteção de Anomalias no Sensor {sensor_id}")
    plt.legend()
    plt.show()

if __name__ == "__main__":

    df_limpo = file_cleaner_loader('kaggle_smartHome_data.csv')
    matriz = transform_to_matrix(df_limpo)

    detector, scaler = train_anomaly_detector(matriz)

    matriz_prever = matriz[COLUNAS_SENSORES]

    dados_escalonados = scaler.transform(matriz_prever) 
    previsoes = detector.predict(dados_escalonados)

    matriz['isAnomaly'] = previsoes

    plot_anomalies(matriz, 'b8:27:eb:bf:9d:51')

    # print("Resultados da deteção (0=Normal,1=Anomalia):")
    # print(matriz[matriz['isAnomaly']==1])

    # print(matriz)
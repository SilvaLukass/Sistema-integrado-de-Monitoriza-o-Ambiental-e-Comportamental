import datetime as dt
import numpy as np
import pandas as pd

def data_validation(data):      #Como não temos um modelo treinado com dados de gás e humidade, vamos introduzir uma função de validação simples para detetar valores anormais. 
                                #Estes limiares são arbitrários e podem ser ajustados com base em dados reais.
    
    if "gas" in data and data["gas"] >= 400.0:
        return f"Gás detetado - Perigo! Valor: {data['gas']}"
        
    elif "humidity" in data and data["humidity"] >= 85.0:
        return f"Humidade excessiva detetada! Valor: {data['humidity']}%"
    
    elif "CO2" in data and data["CO2"] >= 1000.0:
        return f"Níveis de CO2 moderados detetados! Valor: {data['CO2']} ppm"
    
    else:
        return None
    
# Esta função vai retornar os dados que o modelo espera receber.
def clean_data(data, rf_features_list): 

    dt_now = dt.datetime.now() #Horário atual para criar features temporais

    hour_sin = np.sin(2 * np.pi * dt_now.hour / 24) #Feature cíclica para a hora do dia
    hour_cos = np.cos(2 * np.pi * dt_now.hour / 24)  

    is_weekend = 1 if dt_now.weekday() in [5,6] else 0 #Feature binária para fim de semana

    cleaned_data = {coluna: 0.0 for coluna in rf_features_list} #Ao envez de escrever cada coluna, criamos um dicionário com todas as colunas a 0.0

    #Preenchemos as colunas temporais que criamos para enviar para o modelo
    if 'hour_sin' in cleaned_data: 
        cleaned_data['hour_sin'] = hour_sin
        
    if 'hour_cos' in cleaned_data: 
        cleaned_data['hour_cos'] = hour_cos
        
    if 'is_weekend' in cleaned_data: 
        cleaned_data['is_weekend'] = is_weekend

    #Preenchemos as colunas dos sensores com os dados recebidos, convertendo para float. Se um sensor não estiver presente, fica a 0.0
    for sensor, valor in data.items():
        if sensor in cleaned_data:
            cleaned_data[sensor] = float(valor)

    #Retorna um DataFrame com os dados limpos e organizados na ordem das features que o modelo espera receber
    return pd.DataFrame([cleaned_data], columns=rf_features_list)
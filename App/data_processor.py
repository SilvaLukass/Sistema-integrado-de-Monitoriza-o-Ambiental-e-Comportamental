import pandas as pd
import numpy as np



#Função que fará a limpeza e o carregamento dos dados do ficheiro CSV
def file_cleaner_loader(file_path):

    #Tentamos abrir o ficheiro onde os dados estão guardados
    try:
        df=pd.read_csv(file_path)
    except:
        print("ERRO: Ficheiro não encontrado!")
        return None
    
    #Criar o timeStamp
    df['timestamp'] = pd.to_datetime(df['ts'],unit='s')

    #Ordenar por tempo
    df = df.sort_values(by="timestamp")

    

    return df

def transform_to_matrix(df):

    #Definimos o index como sendo o tempo em que algo aconteceu
    df=df.set_index('timestamp')

    #O modelo Isolation_Forest precisa receber dados a cada minuto.
    #Como o sensor de movimento apenas ativasse quando deteta movimento, precisamos de tornar isso em uma coluna
    #Resample é o responsável por modificar a frequencia de dados
    #Pivot é o responsável por modificar dados para colunas
    matrix = df.groupby('device').resample('1min').max()

    #Caso não sejam recebidos valores, são preenchidos os espaços vazios pelo valor anteriormente registado
    if 'temp' in matrix.columns:
        matrix['temp'] = matrix['temp'].ffill()
    if 'hum' in matrix.columns:
        matrix['hum'] = matrix['hum'].ffill()

    #Para o movimento temos que preencher como falso e não o valor anterior
    if 'motion' in matrix.columns:
        matrix['motion'] = matrix['motion'].fillna(False)
    # #Identificamos colunas de temperatura
    # colunas_temp = [c for c in matrix.columns if c.startswith('T')]

    # #Identificamos colunas de movimento
    # colunas_mov = [c for c in matrix.columns if c.startswith('M')]

    # #Caso não haja novo registro de temperatura, preenchemos com o valor anterior
    # matrix[colunas_temp] = matrix[colunas_temp].ffill()

    # #Caso não haja novo registro de movimento, preenchemos com o valor 0
    # matrix[colunas_mov]= matrix[colunas_mov].fillna(0)

    #Se a matriz não tiver valores para a primeira linhas preenchemos com o valor 0
    matrix = matrix.fillna(0)


    return matrix

if __name__ == "__main__":
    
    dados = file_cleaner_loader("kaggle_smartHome_data.csv")
    if dados is not None:
        matrix_final = transform_to_matrix(dados)

        # --- Configuração de Visualização para o Terminal ---
        pd.set_option('display.max_columns', None)  # Mostra todas as colunas
        pd.set_option('display.width', 1000)        # Ajusta a largura para não quebrar linha
        pd.set_option('display.precision', 2)       # Apenas 2 casas decimais

        print(matrix_final.head(10))

        print("\nColunas detetadas:", matrix_final.columns.tolist())
        # print(dados.head())
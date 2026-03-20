from pyod.models.iforest import IForest
import pandas as pd
import numpy as np

#Abrimos o ficheiro com os dados em modo leitura, separando as colunas por nomes
df = pd.read_csv('casas_data.csv', names =['data', 'hora','sensor_id', 'valor'])

print(df.head())
print(df.info())

#Conversão dos dados para alimentar o modelo IForest

#Converter os dados para dateTime
df['timestamp'] = pd.to_datetime(df['data'+''+df['hora']])

#Contar quantas vezes o sensor disparou num intervalo de 1 minuto
df_matrix = df.set_index('timestamp').groupby('sensor_id').resample('1min').count()

#modificar tabela de modo a ter sensores nas colunas e tempo nas linhas
df_final = df_matrix['valor'].unstack(level=0).fillna(0)


#n_estimator -> Quantidade de árvores que serão criadas. Quanto maior for o número maior será a precisão, 
# contudo menor é a performance, o valor padrão é 100
#max_samples -> Quantidade de linhas 'lidas' para cada árvore. Menos amostras aumentam a velocidade de calculo,
#contudo também torna o modelo mais 'agressivo' no isolamento. 'auto' é o valor padrão.
#max_features -> Quantidade de colunas que cada árvore analisa de uma vez. 1.0 é o valor padrão e indica que todas as colunas são lidas
#bootstrap -> Indica se há reposição de amostras para a seleção. False é o valor padrão.
#contamination -> Indica o número de dados em percentagem que se espera serem anómalos.
#random_state -> número usado para gerar a aleatoriadade da divisão de amostras.
#n_jobs -> número de núcleos que são usados da CPU. Quantos mais núcleos, mais rápido é o calculo, contudo consome performance da máquina. -1 indica que devemos usar todos.

def get_iforest(contamination_rate=0.1):

    #Criamos e configuramos o modelo
 model = IForest(
  n_estimators=100,
  max_samples='auto',
  max_features=1.0,
  bootstrap=False,
  n_jobs=-1,
  random_state=42
 )

 return model




# meu_modelo = get_iforest(contamination_rate=0.1)
# meu_modelo.fit(X_train)
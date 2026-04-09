import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import LabelEncoder #Transforma as labels em números únicos para serem identificados pelo IsolationForest
import os


class DataProcessor:
    #Diferenciamos os tipos de sensor, pois estes têm valores de tipo diferente.
    #Motion tem valores do tipo binário (ON/OFF)
    #Já Temp tem valores do tipo float
    MOTION_PREFIXES = ('M',)
    TEMP_PREFIXES = ('T',)

    def __init__(self,filepath = r"new_labeled_data\aruba.txt"): 

        #Inicializamos todos os locais onde iremos guardar os dados como vazios, para depois serem preenchidos
        self.df = None
        self.matrix = None
        self.label_mapping:dict ={}

        col_names = ['date', 'time', 'sensor', 'value', 'label', 'status']

        base_dir = os.path.dirname(os.path.abspath(__file__))   #Descobre a pasta onde este script Python

        path = os.path.abspath(os.path.join(base_dir, "..", filepath))     #Junta a pasta do script com o caminho do ficheiro

        #Tentamos abrir o ficheiro onde os dados estão guardados
        try:
            # Se o ficheiro for separado por espaços e não tiver nomes de colunas:
            raw = pd.read_csv(
                path,
                sep=r'\s+',
                names=col_names,
                engine='python'
            )
            #Chamamos a função que irá preparar a data que foi lida e passada para a variável 'raw'
            self._prepare_data(raw) 

        except FileNotFoundError:   #Caso o ficheiro não seja encontrado, lançamos um erro
            print(f"ERRO: O ficheiro não foi encontrado em: {path}")
        except Exception as e:  #Caso algum erro inesperado aconteça, lançamos um erro
            print(f"ERRO inesperado: {e}")

    #Função responsável por preparar os dados
    def _prepare_data(self, raw: pd.DataFrame):
        
        df = raw.copy()     #Copiamos o dataFrame lido, para processar

        df['dt'] = pd.to_datetime(      #Convertemos os dados data e tempo para datetime, assim teremos apenas uma coluna timestamp
            df['date'].astype(str) + ' ' + df['time'].astype(str),  
            errors="coerce"
        )

        df = df.dropna(subset=['dt'])   #Removemos qualquer linha onde não foi possível converter os dados para timestamp(DateTime)


        if 'label' in df.columns:
            df['label'] = df['label'].replace(r'^\s*$', np.nan, regex=True)     #Utilizamos regex para avisar o python de que estamos a procurar 
                                                                                # expressões não exatas.
                                                                                # O objetivo aqui é tornar labels que pareçam vazias em labels 
                                                                                # realmente vazias (np.nan).
            
            df['label'] = df['label'].ffill().fillna('No_Activity')             #Nesta linha estamos a preencher todos os espaços vazios da coluna
                                                                                #label para 'No_activity'.        

        #Colunas auxiliares para marcar o tempo
        df['day'] = df['dt'].dt.weekday
        df['hour'] = df['dt'].dt.hour

        df['numeric_value'] = self._parse_value(df['value'])    #Convertemos 'value' para valores numéricos (ON/OFF -> 0/1; número->float).

        df = df.drop(columns=[c for c in ['date', 'time', 'status'] if c in df.columns])      #Removemos as colunas que não serão utilizadas.

        self.df = df    #Guardamos o dataframe para ser usado fora da função
       
        self._prepare_labels()  #Chamamos a função responsável por codificar as labels

    def _prepare_labels(self):
        
        le = LabelEncoder()     #Buscamos a função encoder da biblioteca sklearn
        
        # O LabelEncoder transforma ['Eating', 'Sleeping', 'Eating'] em [0, 1, 0]
        self.df['label_encoded'] = le.fit_transform(self.df['label'])
        
        # Guardamos o mapeamento para saber o que cada número representa
        self.label_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
        print(f"[DataProcessor] Eventos carregados: {len(self.df):,}")
        print(f"[DataProcessor] Atividades: {self.label_mapping}")

    def get_matrix_for_model(self, freq: str = '1min') -> pd.DataFrame:     #Rodamos as linhas e as colunas para que o sensorId seja uma coluna
        """
        Devolve uma matriz com:
          - index  : timestamp (resample a `freq`)
          - colunas: um sensor por coluna
          - última coluna: label_encoded (maioritária no intervalo)
 
        Sensores de movimento/porta (ON/OFF) são agregados com MAX (1 se
        houve pelo menos um evento ON no minuto).
        Sensores de temperatura são agregados com MEAN.
        """
        if self.df is None:
            raise RuntimeError("DataFrame não inicializado.")   #Caso o dataframe não exista levantamos um erro de runtime
        
        df = self.df.copy()         #copiamos o dataframe
        df = df.set_index('dt')     #Determinamos o timestamp como index do dataframe

        sensores = df['sensor'].unique()    #Determinamos todos os sensores do dataframe

        binary = [s for s in sensores if s.startswith(self.MOTION_PREFIXES)]    #Os sensores binários são aqueles que apenas guardam valores 0 e 1 
                                                                                # (Como o  movimento).
        numerical = [s for s in sensores if s not in binary]                    #Todos os outros sensores são númericos

        frames = []

        if binary:  #pivot dos sensores binários
            bin_df = df[df['sensor'].isin(binary)].copy()
            bin_pivot = (
                bin_df
                .pivot_table(
                    index=bin_df.index,
                    columns='sensor',
                    values='numeric_value',
                    aggfunc='max'
                )
                .resample(freq).max()
                .fillna(0)        # sem evento no minuto = inativo
            )
            frames.append(bin_pivot)
        
        if numerical:   #pivot dos sensores numéricos
            num_df = df[df['sensor'].isin(numerical)].copy()
            num_pivot = (
                num_df
                .pivot_table(
                    index=num_df.index,
                    columns='sensor',
                    values='numeric_value',
                    aggfunc='mean'      #Guardamos a média dos valores armazenados em 1 minuto
                )
                .resample(freq).mean()
            )

            num_pivot = num_pivot.interpolate(method='time').ffill().bfill()    #Como a temperatura raramente varia, interpolamos os valores que faltarem.
            frames.append(num_pivot)

        matrix = pd.concat(frames, axis=1) if frames else pd.DataFrame()    #Juntamos tudo em uma matriz

        label_resampled = (         #Adicionámos a label que mais aparece em cada intervalo de tempo
            df[['label_encoded']]
            .resample(freq)
            .agg(lambda x: x.mode()[0] if len(x) > 0 else np.nan)
        )
        matrix = matrix.join(label_resampled, how='left') #Juntamos a coluna das labels à matriz principal de sensores

        matrix['label_encoded'] = matrix['label_encoded'].ffill() #Nos momentos em que não há sinais de sensores, assumimos que a atividade anterior
                                                                  # ainda está a decorrer
        
        matrix['label_encoded'] = matrix['label_encoded'].fillna(-1).astype(int)    #Caso não haja nenhuma label, assumimos que não há atividade

        feature_cols = [c for c in matrix.columns if c != 'label_encoded']
        matrix[feature_cols] = matrix[feature_cols].fillna(0)               #Preenchemos os buracos dos sensores

        matrix.columns.name = None  #Removemos o nome do índice de colunas deixado pelo pivot_table

        self.matrix = matrix

        print(f"[DataProcessor] Matriz: {matrix.shape[0]:,} linhas x {matrix.shape[1]} colunas")

        return matrix
    
    @staticmethod
    def _parse_value(series: pd.Series) -> pd.Series:
        """
        Converte a coluna 'value' do dataset para float:
          ON  -> 1.0
          OFF -> 0.0
          <número> -> float
          outro    -> NaN
        """
        mapping = {
            'ON': 1.0, 'OFF': 0.0,
            'TRUE': 1.0, 'FALSE': 0.0,
        }
        def convert(v):
            s = str(v).strip().upper()
            if s in mapping:
                return mapping[s]
            try:
                return float(s)
            except ValueError:
                return np.nan
 
        return series.apply(convert)

if __name__ == "__main__":
    processor = DataProcessor()
 
    if processor.df is not None:
        print("\n--- Amostra do DataFrame de eventos ---")
        print(processor.df[['dt', 'sensor', 'value', 'numeric_value', 'label', 'label_encoded']].head(10))
 
        print("\n--- A construir a matriz... ---")
        matrix = processor.get_matrix_for_model()
 
        print("\n--- Amostra da Matriz ---")
        print(matrix.head())
 
        print("\n--- Tipos de dados ---")
        print(matrix.dtypes)
 
        print("\n--- Valores em falta ---")
        print(matrix.isnull().sum())
"""
model_trainer.py
================
Pipeline de treino do modelo de rotina residencial.

Estratégia:
  1. O RandomForestClassifier aprende a rotina normal do utilizador
     (ex: "às 23h, sensores M010 e M014 ativos → Sleeping").

  2. Na API, o modelo será usado assim:
       a. Recebe leituras dos sensores em tempo real.
       b. Prevê qual a atividade ESPERADA para aquele momento.
       c. Compara com o que os sensores REALMENTE mostram.
       d. Se a confiança da previsão for baixa → anomalia detetada.

Ficheiros gerados:
  rf_routine_model.pkl  — modelo treinado
  rf_features.pkl       — lista de colunas de features (ordem importa!)
  rf_label_mapping.pkl  — mapeamento número → nome da atividade
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, ConfusionMatrixDisplay
from imblearn.over_sampling import SMOTE


from data_processor import DataProcessor


# -----------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------
MODEL_PATH         = 'rf_routine_model.pkl'
FEATURES_PATH      = 'rf_features.pkl'
LABEL_MAPPING_PATH = 'rf_label_mapping.pkl'

# Limiar de confiança: se o modelo tiver menos de X% de certeza
# na sua previsão, consideramos o momento anómalo.
ANOMALY_CONFIDENCE_THRESHOLD = 0.50   # 50%


# -----------------------------------------------------------------------
# Treino
# -----------------------------------------------------------------------
def train_routine_model(matrix: pd.DataFrame, label_mapping: dict):
    """
    Treina o RandomForest para reconhecer a rotina do utilizador.

    Parâmetros
    ----------
    matrix        : DataFrame com índice temporal e coluna 'label_encoded'
    label_mapping : dict {nome_atividade: número} do DataProcessor
    """

    print("\n=== Passo 1: Preparar Features ===")

    matrix = matrix.copy()

    feature_cols = [c for c in matrix.columns if c != 'label_encoded']  #Features são as caracteristicas que passamos ao modelo para 
                                                                        #depois tentar adivinhar a atividade
    X = matrix[feature_cols]
    y = matrix['label_encoded']

    print(f"  Features: {len(feature_cols)} colunas")
    print(f"  Amostras: {len(X):,}")

    # Distribuição das classes — importante verificar se há desequilíbrio
    print("\n  Distribuição de atividades:")
    inv_mapping = {v: k for k, v in label_mapping.items()}  #Invertemos o id da label pelo nome para ser legível durante o debug
    counts = y.value_counts().sort_index()
    for label_num, count in counts.items():
        nome = inv_mapping.get(label_num, f"Label_{label_num}")
        pct  = 100 * count / len(y)                                 #Aqui convertemos a quantidade de valores em percentagem, verificamos
                                                                    #se há um desiquilibrio grande de dados.
        print(f"    {nome:<25} {count:>6,} amostras  ({pct:.1f}%)")


    print("\n=== Passo 2: Split Temporal 80/20 ===")

    # shuffle=False é OBRIGATÓRIO — não queremos "ver o futuro" durante o treino
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, shuffle=False
    )
    # print(f"  Treino : {len(X_train):,} minutos  (primeiros 80% do histórico)")
    # print(f"  Teste  : {len(X_test):,} minutos  (últimos 20% do histórico)")

    smote = SMOTE(random_state=42, k_neighbors=3) 
    
    print(f"A equilibrar balança... (Treino inicial: {X_train.shape[0]} amostras)")
    
    # O SMOTE vai criar "gémeos" sintéticos das atividades raras até todas terem o mesmo peso
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    print(f"Treino após SMOTE: {X_train_resampled.shape[0]} amostras sintéticas equilibradas")

    print("\n=== Passo 3: Treinar RandomForest ===")

    rf_model = RandomForestClassifier(
        n_estimators=200,         # mais árvores = mais estável (custo: memória/tempo)
        max_depth=20,             # limita profundidade para evitar overfitting
        min_samples_leaf=5,       # cada folha precisa de pelo menos 5 amostras
        class_weight='balanced',  # compensa atividades raras (ex: 'Bathing')
        random_state=42,
        n_jobs=-1                 # Utilizamos todos os núcleos da CPU para processar os dados mais rápido
    )

    rf_model.fit(X_train_resampled, y_train_resampled)
    print("  Treino concluído!")

    print("\n=== Passo 4: Avaliar ===")

    y_pred       = rf_model.predict(X_test)
    y_pred_proba = rf_model.predict_proba(X_test)   # confiança por classe

    acc = accuracy_score(y_test, y_pred)
    print(f"\n  Precisão Global: {acc * 100:.2f}%")

    # Relatório com nomes legíveis em vez de números
    target_names = [inv_mapping.get(i, str(i)) for i in sorted(label_mapping.values())]
    print("\n  Relatório Detalhado:")
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))

    # Simular deteção de anomalias no conjunto de teste
    _avaliar_anomalias(y_pred_proba, rf_model.classes_,
                       ANOMALY_CONFIDENCE_THRESHOLD, inv_mapping)


    print("\n=== Passo 5: Guardar Modelo ===")

    joblib.dump(rf_model,      MODEL_PATH)
    joblib.dump(feature_cols,  FEATURES_PATH)
    joblib.dump(label_mapping, LABEL_MAPPING_PATH)

    print(f"  {MODEL_PATH}")
    print(f"  {FEATURES_PATH}")
    print(f"  {LABEL_MAPPING_PATH}")

    return rf_model, feature_cols, X_test, y_test, y_pred, y_pred_proba


# -----------------------------------------------------------------------
# Avaliação de anomalias (lógica central)
# -----------------------------------------------------------------------
def _avaliar_anomalias(y_pred_proba, classes, threshold: float, inv_mapping: dict):
    """
    Demonstra a lógica de deteção de anomalia por baixa confiança.

    Quando o modelo não consegue encaixar as leituras em nenhuma atividade
    conhecida com confiança suficiente, isso é o sinal de anomalia.
    """
    max_confidence = y_pred_proba.max(axis=1)

    anomalias_idx = np.where(max_confidence < threshold)[0]
    n_total       = len(max_confidence)
    n_anomalias   = len(anomalias_idx)

    print(f"\n  --- Simulação de Deteção de Anomalias ---")
    print(f"  Limiar de confiança : {threshold*100:.0f}%")
    print(f"  Amostras analisadas : {n_total:,}")
    print(f"  Anomalias detetadas : {n_anomalias:,}  ({100*n_anomalias/n_total:.2f}%)")
    print()
    print("  Interpretação:")
    print("  Se o modelo prevê 'Sleeping' com 85% de confiança → NORMAL")
    print(f"  Se o modelo prevê com menos de {threshold*100:.0f}% de confiança → ANOMALIA")
    print("  (padrão de sensores não corresponde a nenhuma rotina conhecida)")


# -----------------------------------------------------------------------
# Visualizações
# -----------------------------------------------------------------------
def plot_results(rf_model, feature_cols, X_test, y_test, y_pred,
                 y_pred_proba, label_mapping):

    inv_mapping  = {v: k for k, v in label_mapping.items()}
    labels_order = sorted(label_mapping.values())
    label_names  = [inv_mapping[i] for i in labels_order]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # --- Gráfico 1: Matriz de Confusão ---
    ConfusionMatrixDisplay.from_predictions(
        y_test, y_pred,
        display_labels=label_names,
        xticks_rotation=45,
        ax=axes[0],
        colorbar=False
    )
    axes[0].set_title("Matriz de Confusão\n(com que frequência confunde atividades)")

    # --- Gráfico 2: Distribuição da confiança das previsões ---
    max_confidence = y_pred_proba.max(axis=1)
    axes[1].hist(max_confidence, bins=50, color='steelblue', edgecolor='white')
    axes[1].axvline(ANOMALY_CONFIDENCE_THRESHOLD, color='red', linestyle='--',
                    linewidth=2, label=f'Limiar ({ANOMALY_CONFIDENCE_THRESHOLD*100:.0f}%)')
    axes[1].set_xlabel('Confiança da Previsão')
    axes[1].set_ylabel('Nº de Amostras')
    axes[1].set_title('Distribuição da Confiança\n(à esquerda do limiar = anomalia)')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig('rf_results.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n[Visualização] rf_results.png guardado")

    # --- Gráfico 3: Importância das features ---
    importances  = pd.Series(rf_model.feature_importances_, index=feature_cols)
    top_features = importances.nlargest(15)

    plt.figure(figsize=(10, 6))
    top_features.sort_values().plot(kind='barh', color='steelblue')
    plt.title('Top 15 Sensores Mais Importantes para a Rotina')
    plt.xlabel('Importância Relativa')
    plt.tight_layout()
    plt.savefig('rf_feature_importance.png', dpi=150)
    plt.show()
    print("[Visualização] rf_feature_importance.png guardado")


# -----------------------------------------------------------------------
# Ponto de entrada
# -----------------------------------------------------------------------
if __name__ == "__main__":

    processor = DataProcessor('aruba.txt')
    matrix    = processor.get_matrix_for_model()

    if matrix.empty:
        print("ERRO: A matriz está vazia. Verifica o DataProcessor.")
        exit(1)

    rf_model, feature_cols, X_test, y_test, y_pred, y_pred_proba = \
        train_routine_model(matrix, processor.label_mapping)

    plot_results(rf_model, feature_cols, X_test, y_test,
                 y_pred, y_pred_proba, processor.label_mapping)
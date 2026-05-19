"""
Testa sistematicamente combinações de hiperparâmetros do RandomForest
e reporta as melhores configurações encontradas.

Fonte: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from data_processor import DataProcessor

# ── Configuração ──────────────────────────────────────────────────────────────
N_ITER   = 30    # quantas combinações testar — mais = mais lento mas mais preciso
CV_FOLDS = 5     # folds de validação cruzada
N_JOBS   = -1    # usar todos os núcleos da CPU

# Espaço de pesquisa — combinações que o RandomizedSearch vai explorar
PARAM_GRID = {
    "classifier__n_estimators":   [100, 200, 300],
    "classifier__max_depth":      [10, 15, 20, 25],
    "classifier__min_samples_leaf": [1, 3, 5, 10],
    "classifier__max_features":   ["sqrt", "log2", 0.3, 0.5],
    "classifier__class_weight":   ["balanced", "balanced_subsample", None],
}

# ── Dados ─────────────────────────────────────────────────────────────────────
processor = DataProcessor("aruba.txt")
matrix    = processor.get_matrix_for_model()

feature_cols = [c for c in matrix.columns if c != "label_encoded"]
X = matrix[feature_cols]
y = matrix["label_encoded"]

# Split temporal 70/30 — a pesquisa corre no treino, teste final separado
n         = len(X)
train_end = int(n * 0.70)
X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
X_test,  y_test  = X.iloc[train_end:],  y.iloc[train_end:]

print(f"Treino: {len(X_train):,} amostras | Teste: {len(X_test):,} amostras")

# ── Pipeline SMOTE + RandomForest ────────────────────────────────────────────
# O Pipeline garante que o SMOTE só corre nos dados de treino de cada fold
pipeline = ImbPipeline([
    ("smote",      SMOTE(random_state=42, k_neighbors=3)),
    ("classifier", RandomForestClassifier(random_state=42, n_jobs=N_JOBS)),
])

# ── Pesquisa aleatória ────────────────────────────────────────────────────────
# StratifiedKFold mantém a proporção de classes em cada fold
cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=False)

search = RandomizedSearchCV(
    estimator  = pipeline,
    param_distributions = PARAM_GRID,
    n_iter     = N_ITER,
    cv         = cv,
    scoring    = "f1_weighted",   # f1_weighted é melhor que accuracy para classes desbalanceadas
    verbose    = 2,
    random_state = 42,
    n_jobs     = N_JOBS,
)

print(f"\nA testar {N_ITER} combinações com {CV_FOLDS}-fold CV...")
search.fit(X_train, y_train)

# ── Resultados ────────────────────────────────────────────────────────────────
print("\n=== Melhores Hiperparâmetros ===")
for param, valor in search.best_params_.items():
    print(f"  {param.replace('classifier__', ''):<25} {valor}")

print(f"\n  F1 médio na validação: {search.best_score_ * 100:.2f}%")

# Avaliar o melhor modelo no teste final
y_pred   = search.best_estimator_.predict(X_test)
acc_test = accuracy_score(y_test, y_pred)
print(f"  Precisão no teste final: {acc_test * 100:.2f}%")

inv_mapping  = {v: k for k, v in processor.label_mapping.items()}
target_names = [inv_mapping.get(i, str(i)) for i in sorted(processor.label_mapping.values())]
print("\n=== Relatório Detalhado (Teste Final) ===")
print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))

# Top 10 combinações testadas
print("\n=== Top 10 Combinações ===")
results = pd.DataFrame(search.cv_results_)
top10   = results.nlargest(10, "mean_test_score")[
    ["mean_test_score", "std_test_score", "params"]
]
for _, row in top10.iterrows():
    params_clean = {k.replace("classifier__", ""): v for k, v in row["params"].items()}
    print(f"  F1: {row['mean_test_score']*100:.2f}% ± {row['std_test_score']*100:.2f}%  →  {params_clean}")

# Guardar os melhores hiperparâmetros para referência
joblib.dump(search.best_params_, "best_hyperparams.pkl")
print("\nbest_hyperparams.pkl guardado — usa estes valores no model_trainer.py")
from pyod.models.iforest import IForest
from pyod.utils.data import generate_data
import matplotlib.pyplot as plt
import numpy as np

def notify(message):

    print("Anomaly detected: ",message)


def main():

    X_train = np.random.rand(50,2)
    X_test = np.random.rand(30,2)

    # --- DEBUG: Vamos ver quem é quem ---
    print(f"DEBUG - X_test (Primeiros 5): {X_test[:5]}")
    print(f"DEBUG - X_test shape: {X_test.shape}")
    # -----------------------------------

    #Inicializar o modelo com a quantidade de contaminação esperada (auto=0.1) e treinar o modelo (fit(X_train))
    model = IForest(contamination=0.1, random_state=42).fit(X_train)  

    y_test_pred = model.predict(X_test)

    normal_points = X_test[y_test_pred == 0]
    anomaly_points = X_test[y_test_pred == 1]

    #Desenhar gráfico que mostra os points
    plt.figure(figsize=(8,6))
    plt.scatter(normal_points[:,0], normal_points[:,1], c='blue', label='Normal')
    plt.scatter(anomaly_points[:,0], anomaly_points[:,1], c='red', label='Anomaly')
    plt.title('Detecção de anomalias com Isolation Forest')
    plt.legend()
    plt.show()
    if np.sum(y_test_pred) > 0:
        notify(f"Detectadas {np.sum(y_test_pred)} anomalias no conjunto do teste!")
    else:
        print("Tudo normal, sem anomalias detectadas.")

if __name__ == "__main__":
    main()




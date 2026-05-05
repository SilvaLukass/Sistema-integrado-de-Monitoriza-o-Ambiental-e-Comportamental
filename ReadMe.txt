# 🏠 Sistema Integrado de Monitorização Ambiental e Comportamental (Backend API)

Este repositório contém o backend em Python para o sistema de deteção de anomalias em ambientes domésticos (focado no apoio a idosos). O modelo utiliza o algoritmo `Isolation Forest` para analisar dados de sensores IoT e uma API em `FastAPI` para comunicar com a aplicação Web.

## ⚠️ 1. Dataset Necessário (Importante)
Para que o código funcione, **tens de descarregar o dataset manualmente**, uma vez que o ficheiro é demasiado pesado para o GitHub.

1. Descarrega o dataset original no Kaggle: [Escreve aqui o nome ou link do dataset do Kaggle]
2. Renomeia o ficheiro descarregado para `kaggle_smartHome_data.csv`.
3. Coloca o ficheiro na mesma pasta onde estão os scripts Python (na raiz do projeto).
*(Nota: O ficheiro .csv está ignorado pelo .gitignore, por isso não será enviado para o repositório em futuros commits).*

## ⚙️ 2. Instalação e Configuração
Certifica-te de que tens o Python instalado. Abre o terminal nesta pasta e segue estes passos:

**Criar e ativar o ambiente virtual (Recomendado):**
```bash
python -m venv venv
# No Windows:
.\venv\Scripts\activate
# No Mac/Linux:
source venv/bin/activate

Bibliotecas

pip install pandas numpy scikit-learn pyod fastapi uvicorn matplotlib joblib

Como Correr o Projeto
Passo A: Treinar o Modelo
Sempre que o dataset for atualizado, precisas de treinar o modelo para gerar os ficheiros .pkl atualizados (com 7 colunas).

python model_trainer.py

Passo B: Ligar a API (Servidor Local)
Para iniciar o servidor que vai ficar à escuta dos dados da aplicação Web:
uvicorn main_api:app --reload

Testar a API
Com o servidor ligado, abre o teu navegador e vai a:
👉 https://www.google.com/search?q=http://127.0.0.1:8000/docs

Aqui poderás usar a interface gráfica do Swagger para enviar dados falsos de sensores e testar se a inteligência artificial devolve o diagnóstico de anomalia corretamente!


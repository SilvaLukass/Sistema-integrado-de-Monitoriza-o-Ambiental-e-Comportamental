import asyncio
from datetime import datetime
from typing import Callable


# ─── 1. Estado global da casa ──────────────────────────────────────────────────
global_home_state: dict[str, float] = {
    "hour": 0.0,
    "minute": 0.0,
    "day_of_week": 0.0,
    "D001": 0.0, "D002": 0.0, "D004": 0.0,
    "LEAVEHOME": 0.0,
    "M001": 0.0, "M002": 0.0, "M003": 0.0, "M004": 0.0, "M005": 0.0,
    "M006": 0.0, "M007": 0.0, "M008": 0.0, "M009": 0.0, "M010": 0.0,
    "M011": 0.0, "M012": 0.0, "M013": 0.0, "M014": 0.0, "M015": 0.0,
    "M016": 0.0, "M017": 0.0, "M018": 0.0, "M019": 0.0, "M020": 0.0,
    "M021": 0.0, "M022": 0.0, "M023": 0.0, "M024": 0.0, "M025": 0.0,
    "M026": 0.0, "M027": 0.0, "M028": 0.0, "M029": 0.0, "M030": 0.0,
    "M031": 0.0,
    "T001": 22.5, "T002": 22.5, "T003": 22.5, "T004": 22.5, "T005": 22.5,
}

simulation_logs: list[dict] = []  # buffer de logs para o React consumir

# ─── 2. Parser de linha ────────────────────────────────────────────────────────
# Formato CASAS: '2010-11-04 08:11:09.966157 M018 ON'
def processar_linha_log(linha_texto: str) -> bool:
    """
    Atualiza global_home_state com base numa linha do ficheiro de log.
    Retorna True se a linha foi processada, False se deve ser ignorada.
    """
    linha = linha_texto.strip()
    if not linha or linha.startswith("#"):
        return False

    partes = linha.split()

    # Formato esperado: DATE TIME SENSOR VALUE [ACTIVITY]
    if len(partes) < 4:
        return False

    try:
        timestamp = datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            timestamp = datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False

    sensor = partes[2].upper()
    valor_raw = partes[3].upper()

    activity_label: str | None = None
    activity_phase: str | None = None  # "begin" ou "end"
    if len(partes) >= 5:
        activity_label = partes[4]       # ex: "Sleeping"
    if len(partes) >= 6:
        activity_phase = partes[5]       # ex: "begin" ou "end"

    global_home_state["hour"] = float(timestamp.hour)
    global_home_state["minute"] = float(timestamp.minute)
    global_home_state["day_of_week"] = float(timestamp.weekday())

    if valor_raw in ("ON", "OPEN", "1", "TRUE"):
        valor = 1.0
    elif valor_raw in ("OFF", "CLOSE", "0", "FALSE"):
        valor = 0.0
    else:
        try:
            valor = float(valor_raw)
        except ValueError:
            return False

    if sensor in global_home_state:
        global_home_state[sensor] = valor

    simulation_logs.append({
        "timestamp": timestamp.isoformat(),
        "sensor": sensor,
        "value": valor,
        "raw_line": linha_texto.strip(),
        # ✅ Ground truth para comparar com a predição do modelo
        "ground_truth_activity": activity_label,
        "ground_truth_phase": activity_phase,
        "state_snapshot": dict(global_home_state),
    })

    if len(simulation_logs) > 500:
        simulation_logs.pop(0)

    return True

# ─── 3. Motor principal ────────────────────────────────────────────────────────
async def correr_simulacao(
    caminho_ficheiro: str,
    predict_fn: Callable,
    velocidade: float = 1.0,
    compasso_segundos: float = 0.5,
):
    simulation_logs.clear()
    ultimo_timestamp: datetime | None = None

    try:
        with open(caminho_ficheiro, "r", encoding="utf-8") as f:
            for linha in f:
                sucesso = processar_linha_log(linha)
                if not sucesso:
                    continue

                evento = simulation_logs[-1]
                timestamp_atual = datetime.fromisoformat(evento["timestamp"])

                # 1. Calcular pausa ANTES de emitir
                if ultimo_timestamp is not None:
                    delta = (timestamp_atual - ultimo_timestamp).total_seconds()
                    pausa = min(delta / velocidade, compasso_segundos)
                    if pausa > 0:
                        await asyncio.sleep(pausa)

                ultimo_timestamp = timestamp_atual

                # 2. Chamar o modelo
                try:
                    evento["prediction"] = predict_fn(evento["state_snapshot"])
                except Exception as e:
                    evento["prediction"] = {"error": str(e)}

                # 3. Emitir UMA vez
                yield evento

    except FileNotFoundError:
        yield {"error": f"Ficheiro não encontrado: {caminho_ficheiro}"}
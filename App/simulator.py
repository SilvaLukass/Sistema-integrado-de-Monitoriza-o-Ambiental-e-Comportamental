import asyncio
import numpy as np
from collections import deque
from datetime import datetime
from typing import Callable

# ─── 1. Estado global da casa ──────────────────────────────────────────────────
global_home_state: dict[str, float] = {
    "hour": 0.0, "minute": 0.0, "day_of_week": 0.0,
    "D001": 0.0, "D002": 0.0, "D004": 0.0, "LEAVEHOME": 0.0,
    "M001": 0.0, "M002": 0.0, "M003": 0.0, "M004": 0.0, "M005": 0.0,
    "M006": 0.0, "M007": 0.0, "M008": 0.0, "M009": 0.0, "M010": 0.0,
    "M011": 0.0, "M012": 0.0, "M013": 0.0, "M014": 0.0, "M015": 0.0,
    "M016": 0.0, "M017": 0.0, "M018": 0.0, "M019": 0.0, "M020": 0.0,
    "M021": 0.0, "M022": 0.0, "M023": 0.0, "M024": 0.0, "M025": 0.0,
    "M026": 0.0, "M027": 0.0, "M028": 0.0, "M029": 0.0, "M030": 0.0,
    "M031": 0.0,
    "T001": 22.5, "T002": 22.5, "T003": 22.5, "T004": 22.5, "T005": 22.5,
}

simulation_logs: list[dict] = []

# ─── Histórico para features derivadas ────────────────────────────────────────
MOTION_SENSORS = [k for k in global_home_state if k.startswith('M')]
# Janelas de 5 e 15 minutos — cada entrada = 1 leitura por minuto
_roll5:  dict[str, deque] = {s: deque(maxlen=5)  for s in MOTION_SENSORS}
_roll15: dict[str, deque] = {s: deque(maxlen=15) for s in MOTION_SENSORS}
_roll30: dict[str, deque] = {s: deque(maxlen=30) for s in MOTION_SENSORS}
_time_since_last_motion: int = 0

def _compute_derived_features(timestamp: datetime) -> dict:
    """Calcula as mesmas features que o DataProcessor cria na matriz."""
    hours_in_day = 24
    hour_sin = float(np.sin(2 * np.pi * timestamp.hour / hours_in_day))
    hour_cos = float(np.cos(2 * np.pi * timestamp.hour / hours_in_day))
    is_weekend = 1.0 if timestamp.weekday() in [5, 6] else 0.0

    # Atualizar histórico rolling para cada sensor de movimento
    for s in MOTION_SENSORS:
        val = global_home_state.get(s, 0.0)
        _roll5[s].append(val)
        _roll15[s].append(val)
        _roll30[s].append(val)

    # total_motion_now
    total_motion = sum(global_home_state.get(s, 0.0) for s in MOTION_SENSORS)

    # time_since_last_motion
    global _time_since_last_motion
    if total_motion > 0:
        _time_since_last_motion = 0
    else:
        _time_since_last_motion += 1

    features = {
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "is_weekend": is_weekend,
        "total_motion_now": total_motion,
        "time_since_last_motion": float(_time_since_last_motion),
    }

    # roll5_sum e roll15_sum para cada sensor de movimento
    for s in MOTION_SENSORS:
        features[f"{s}_roll5_sum"]  = float(sum(_roll5[s]))
        features[f"{s}_roll15_sum"] = float(sum(_roll15[s]))
        features[f"{s}_roll30_sum"] = float(sum(_roll30[s]))

    return features


# ─── 2. Parser de linha ────────────────────────────────────────────────────────
def processar_linha_log(linha_texto: str) -> bool:
    linha = linha_texto.strip()
    if not linha or linha.startswith("#"):
        return False

    partes = linha.split()
    if len(partes) < 4:
        return False

    try:
        timestamp = datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            timestamp = datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False

    sensor    = partes[2].upper()
    valor_raw = partes[3].upper()

    activity_label: str | None = partes[4] if len(partes) >= 5 else None
    activity_phase: str | None = partes[5] if len(partes) >= 6 else None

    global_home_state["hour"]        = float(timestamp.hour)
    global_home_state["minute"]      = float(timestamp.minute)
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

    # Calcular features derivadas
    derived = _compute_derived_features(timestamp)

    # Estado completo = sensores raw + features derivadas
    state_snapshot = {**dict(global_home_state), **derived}

    simulation_logs.append({
        "timestamp":              timestamp.isoformat(),
        "sensor":                 sensor,
        "value":                  valor,
        "raw_line":               linha_texto.strip(),
        "ground_truth_activity":  activity_label,
        "ground_truth_phase":     activity_phase,
        "state_snapshot":         state_snapshot,
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
    hora_inicio: int | None = None,
):
    simulation_logs.clear()
    global _time_since_last_motion
    _time_since_last_motion = 0
    for s in MOTION_SENSORS:
        _roll5[s].clear()
        _roll15[s].clear()

    ultimo_timestamp: datetime | None = None
    hora_encontrada = hora_inicio is None

    try:
        with open(caminho_ficheiro, "r", encoding="utf-8") as f:
            for linha in f:
                if not hora_encontrada:
                    partes = linha.strip().split()
                    if len(partes) >= 2:
                        try:
                            ts = datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                ts = datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                continue
                        if hora_inicio is not None and ts.hour >= hora_inicio:
                            hora_encontrada = True
                        else:
                            continue

                sucesso = processar_linha_log(linha)
                if not sucesso:
                    continue

                evento = simulation_logs[-1]
                timestamp_atual = datetime.fromisoformat(evento["timestamp"])

                if ultimo_timestamp is not None:
                    delta = (timestamp_atual - ultimo_timestamp).total_seconds()
                    pausa = min(delta / velocidade, compasso_segundos)
                    if pausa > 0:
                        await asyncio.sleep(pausa)

                ultimo_timestamp = timestamp_atual

                try:
                    evento["prediction"] = predict_fn(evento["state_snapshot"])
                except Exception as e:
                    evento["prediction"] = {"error": str(e)}

                yield evento

    except FileNotFoundError:
        yield {"error": f"Ficheiro não encontrado: {caminho_ficheiro}"}
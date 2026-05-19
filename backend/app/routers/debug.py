from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
import numpy as np
import pandas as pd
from App.simulator import correr_simulacao

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/simulate")
async def stream_simulacao(request: Request, hora_inicio: int | None = None):
    project_root = request.app.state.project_root
    caminho = project_root / "new_labeled_data" / "aruba.txt"

    model       = request.app.state.ml_model
    features    = request.app.state.ml_features
    mapping     = request.app.state.ml_label_mapping
    inv_mapping = {v: k for k, v in mapping.items()}

    def predict_fn(readings: dict) -> dict:
        input_data = {col: [readings.get(col, 0.0)] for col in features}
        df = pd.DataFrame(input_data)
        pred      = model.predict(df)[0]
        proba     = model.predict_proba(df)[0]
        confianca = float(np.max(proba) * 100)
        return {
            "expected_activity": inv_mapping.get(pred, "Unknown"),
            "confidence": round(confianca, 3),
            "is_anomaly": confianca < 50,
        }

    async def sse_generator():
        async for evento in correr_simulacao(str(caminho), predict_fn, velocidade=10.0, compasso_segundos=0.1, hora_inicio=hora_inicio):
            yield f"data: {json.dumps(evento)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
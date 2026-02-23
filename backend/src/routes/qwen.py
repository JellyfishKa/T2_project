from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.models.qwen_client import QwenClient
from src.models.schemas import Location, Route
from src.services.model_selector import get_model_recommendation


router = APIRouter(prefix="/qwen", tags=["Qwen LLM"])


@router.post("/optimize", response_model=Route)
async def optimize_route(
    locations: List[Location],
    constraints: Dict = None,
    # ML-6: опционально вернуть рекомендацию селектора (какую модель лучше использовать)
    include_recommendation: bool = Query(False, description="Добавить в ответ recommendation (model + reason)"),
    time_constraint: Optional[str] = Query(None, description="urgent | quality | reliability"),
):
    client = QwenClient()
    try:
        route = await client.generate_route(locations, constraints)
        if include_recommendation:
            rec = get_model_recommendation(len(locations), time_constraint)
            route = route.model_copy(update={"recommendation": rec})
        return route
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

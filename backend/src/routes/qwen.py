from fastapi import APIRouter, HTTPException
from src.models.qwen_client import QwenClient
from src.models.schemas import Location, Route
from typing import List, Dict

router = APIRouter(prefix="/qwen", tags=["Qwen LLM"])

@router.post("/optimize", response_model=Route)
async def optimize_route(locations: List[Location], constraints: Dict = {}):
    client = QwenClient()
    try:
        return await client.generate_route(locations, constraints)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

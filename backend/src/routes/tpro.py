from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from src.models.exceptions import (
    TProAuthError,
    TProRateLimitError,
    TProTimeoutError,
    TProValidationError,
)
from src.models.schemas import Location, Route
from src.models.tpro_client import TProClient


router = APIRouter(prefix="/tpro", tags=["T-Pro LLM"])


@router.post("/optimize", response_model=Route, status_code=status.HTTP_200_OK)
async def optimize_route_tpro(locations: List[Location],
                              constraints: Dict = {}):
    client = TProClient()
    try:
        return await client.generate_route(locations, constraints)

    except TProValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации данных: {str(e)}",
        )
    except TProAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка авторизации T-Pro API",
        )
    except TProRateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит запросов к T-Pro",
        )
    except TProTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="T-Pro API не ответил вовремя (timeout > 20s)",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Критическая ошибка T-Pro: {str(e)}",
        )

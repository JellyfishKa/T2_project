from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from src.models.exceptions import (
    LlamaAuthError,
    LlamaRateLimitError,
    LlamaServerError,
    LlamaTimeoutError,
    LlamaValidationError,
)
from src.models.llama_client import LlamaClient
from src.models.schemas import Location, Route


router = APIRouter(prefix="/llama", tags=["Llama LLM"])


@router.post("/optimize", response_model=Route, status_code=status.HTTP_200_OK)
async def optimize_route_llama(locations: List[Location],
                               constraints: Dict = {}):
    client = LlamaClient()
    try:
        return await client.generate_route(locations, constraints)

    except LlamaValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации данных: {str(e)}",
        )
    except LlamaAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка авторизации Llama API",
        )
    except LlamaRateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит запросов к Llama",
        )
    except LlamaTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Llama API не ответил вовремя (timeout > 20s)",
        )
    except LlamaServerError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера Llama: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Критическая ошибка Llama: {str(e)}",
        )

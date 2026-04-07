from fastapi import APIRouter

from src.schemas.routing import (
    RoutePreviewRequest,
    RoutePreviewResponse,
)
from src.services.routing import RoutingService


router = APIRouter(prefix="/routing", tags=["Routing"])


@router.post("/preview", response_model=RoutePreviewResponse)
async def preview_route(
    payload: RoutePreviewRequest,
):
    routing_service = RoutingService()
    preview = await routing_service.build_route_preview(payload.points)
    return RoutePreviewResponse(**preview)

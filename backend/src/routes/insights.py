from typing import Optional

from fastapi import APIRouter, Query

from src.services.model_selector import get_model_recommendation

router = APIRouter(tags=['Insights'])


@router.get('/insights')
async def get_optimization_insights(
    num_locations: int = Query(..., description='Количество локаций'),
    time_constraint: Optional[str] = Query(
        None, description='Ограничение по времени',
    ),
):
    recommendation = get_model_recommendation(
        num_locations=num_locations,
        time_constraint=time_constraint,
    )

    return {
        'input_parameters': {
            'num_locations': num_locations,
            'time_constraint': time_constraint,
        },
        'recommendation': recommendation,
    }

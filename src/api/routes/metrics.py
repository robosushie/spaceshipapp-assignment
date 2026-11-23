from fastapi import APIRouter

from src.api.deps import CurrentUser, SessionDep
from src.schemas.orders.metrics import MetricsResponse
from src.services.orders.metrics import get_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsResponse)
def read_metrics(session: SessionDep, _: CurrentUser) -> MetricsResponse:
    return get_metrics(session)

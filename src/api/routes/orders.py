from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from src.api.deps import CurrentUser, SessionDep
from src.enums import OrderStatus
from src.schemas import OrderPage, OrderRead
from src.services.orders import OrderFilterError, get_order, list_orders, parse_filters

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderPage)
def read_orders(
    session: SessionDep,
    _: CurrentUser,
    status: OrderStatus | None = None,
    region: Annotated[str | None, Query(max_length=16)] = None,
    carrier: Annotated[str | None, Query(max_length=64)] = None,
    client_id: Annotated[str | None, Query(max_length=32)] = None,
    filters: Annotated[list[str] | None, Query(alias="filter")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OrderPage:
    try:
        parsed = parse_filters(filters or [])
    except OrderFilterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return list_orders(
        session,
        status=status,
        region=region,
        carrier=carrier,
        client_id=client_id,
        limit=limit,
        offset=offset,
        filters=parsed,
    )


@router.get("/{order_id}", response_model=OrderRead)
def read_order(order_id: str, session: SessionDep, _: CurrentUser) -> OrderRead:
    order = get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

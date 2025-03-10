from fastapi import APIRouter, Request

from controllers import get_order_details, get_single_order_details

router = APIRouter(
    prefix="/orders",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", tags=["webhook"])
async def handle_get_order_details(req: Request):
    return await get_order_details(req)

@router.get("/{order_id}", tags=["webhook"])
async def handle_get_single_order_details(order_id:str, req: Request):
    query_params = req.query_params._dict
    channel_uid = query_params.get("channel_uid", None)
    return await get_single_order_details(order_id, channel_uid)

order_router = router
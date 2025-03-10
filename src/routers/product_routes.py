from fastapi import APIRouter, Depends, Request

from config.database import get_db
from controllers import get_product_details, update_product_inventory
from serializers import AuthRequest

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{product_id}", tags=["products"])
async def handle_get_product_details(product_id: str,req: Request):
    return await get_product_details(product_id, req)

@router.post("/{product_id}/inventory/update", tags=["products"])
async def handle_update_product_inventory(product_id: str, req: Request):
    return await update_product_inventory(product_id, req)


product_router = router

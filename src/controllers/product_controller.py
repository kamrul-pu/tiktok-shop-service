from http import HTTPStatus

from fastapi import Request
from fastapi.responses import ORJSONResponse

from utils.maps import Tiktok
from utils.helpers import get_channel_and_token


async def get_product_details(product_id: str, req: Request):
    query_params = req.query_params._dict
    channel_uid = query_params.get("channel_uid", None)
    if not channel_uid:
        return ORJSONResponse(
            content={"message": "Channel uid is required"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    try:
        channel = await get_channel_and_token(channel_uid=channel_uid)
        res = await Tiktok.get_single_product_details(
            product_id=product_id,
            access_token=channel.tokens.access_token,
            shop_cipher=channel.shop_cipher,
        )
        return ORJSONResponse(content=res.json())

    except Exception as e:
        return ORJSONResponse(
            content={"message": f"An error occurred {str(e)}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
       )


async def update_product_inventory(product_id: str, req: Request):
    query_params = req.query_params._dict
    channel_uid = query_params.get("channel_uid", None)
    if not channel_uid:
        return ORJSONResponse(
            content={"message": "Channel uid is required"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    try:
        channel = await get_channel_and_token(channel_uid=channel_uid)
        if not channel:
            return ORJSONResponse(
                content={"message": "Failed to get Channel"},
                status_code=HTTPStatus.BAD_REQUEST,
            )

        req_body = await req.body()

        res = await Tiktok.update_product_inventory(
            product_id,
            channel.tokens.access_token, channel.shop_cipher, req_body
        )
        if res.json().get("code")!=0:
            return ORJSONResponse(content={"message": "Failed to update inventory", "data": res.json()}, status_code=HTTPStatus.BAD_REQUEST)
        return ORJSONResponse(content=res.json())

    except Exception as e:
        return ORJSONResponse(
            content={"message": f"An error occurred {str(e)}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

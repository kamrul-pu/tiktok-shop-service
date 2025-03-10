from http import HTTPStatus

from fastapi import Request
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError

from utils.maps import Tiktok
from utils.helpers import get_channel_and_token


async def get_order_details(req: Request):
    try:
        body = await req.body()
        res = await Tiktok.get_order_details(
            req_params=req.query_params._dict,
            headers=req.headers,
            body=body,
        )
        return ORJSONResponse(content=res.json())

    except ValidationError as e:
        error_message = f"Validation failed: {e}"
        print(error_message)
        return error_message


async def get_single_order_details(order_id: str, channel_uid: str):
    if not channel_uid:
        return ORJSONResponse(
            content={"message": "channel_uid is required"},
            status_code=HTTPStatus.BAD_REQUEST,
        )

    channel = await get_channel_and_token(channel_uid=channel_uid)
    if not channel:
        return ORJSONResponse(content={"message": "Failed to get Channel"}, status_code=HTTPStatus.BAD_REQUEST)

    try:
        res = await Tiktok.get_single_order_details(
            order_id=order_id,
            access_token=channel.tokens.access_token,
            shop_cipher=channel.shop_cipher,
        )
        return ORJSONResponse(content=res.json())

    except ValidationError as e:
        error_message = f"Validation failed: {e}"
        print(error_message)
        return error_message

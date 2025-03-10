from http import HTTPStatus

from fastapi import Request
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from models import Channel, Token
from serializers import AuthRequest
from utils.maps import Tiktok
from utils.helpers import get_channel_and_token, create_channel_in_mis

async def get_authorized_shops(req: Request):
    try:
        body = await req.body()

        channel_uid = req.query_params._dict.get("channel_uid", None)
        if not channel_uid:
            return ORJSONResponse(
                content={"message": "channel_uid is required"},
                status_code=HTTPStatus.BAD_REQUEST
            )
        channel = await get_channel_and_token(channel_uid=channel_uid)
        if not channel:
            return ORJSONResponse(content={"message": "Failed to get Channel"}, status_code=HTTPStatus.BAD_REQUEST)

        res = await Tiktok.get_authorized_shops(
            access_token=channel.tokens.access_token
        )
        return ORJSONResponse(content=res.json())

    except ValidationError as e:
        error_message = f"Validation failed: {e}"
        print(error_message)
        return error_message


async def get_active_shops(req: Request):
    try:
        body = await req.body()
        res = await Tiktok.get_active_shops(
            req_params=req.query_params._dict, headers=req.headers, body=body
        )
        return ORJSONResponse(content=res.json())

    except ValidationError as e:
        error_message = f"Validation failed: {e}"
        print(error_message)
        return error_message


async def integrate_channel(payload: AuthRequest, db: Session):
    resp = {}
    try:
        (
            access_token,
            refresh_token,
            access_token_expires_in,
            refresh_token_expires_in,
            err,
        ) = await Tiktok.get_access_token(auth_code=payload.auth_code)

        if err is not None:
            return ORJSONResponse(
                content={"message": err}, status_code=HTTPStatus.BAD_REQUEST
            )

        shops_response = await Tiktok.get_authorized_shops(access_token=access_token)
        shops_response = shops_response.json()
        shop_cipher = None
        if shops_response.get('code')!=0:
            resp.update({'errors':[{'message':'failed to retrieve shop details'}]})
        else:
            shops = shops_response.get('data').get('shops')
            for shop in shops:
                if shop.get('id') == payload.shop_id:
                    shop_cipher = shop.get('cipher')
        # Check if the channel already exists by shop_cipher and shop_id
        existing_channel = db.query(Channel).filter_by(shop_cipher=shop_cipher, shop_id=int(payload.shop_id)).first()
        if existing_channel:
            # Channel exists, update the associated tokens
            existing_token = existing_channel.tokens
            existing_token.access_token = access_token
            existing_token.refresh_token = refresh_token
            existing_token.access_token_expiry = access_token_expires_in
            existing_token.refresh_token_expiry = refresh_token_expires_in
            db.commit()
            resp.update({"message":"channel updated successfully"})
        else:
            # Channel does not exist, create a new channel
            new_channel = Channel(
                company_uuid=payload.company_uid,
                name=payload.name,
                country=payload.country,
                shop_id=payload.shop_id,
                shop_cipher=shop_cipher,
                tokens=Token(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    access_token_expiry=access_token_expires_in,
                    refresh_token_expiry=refresh_token_expires_in,  # Expiry in 1 hour
                ),
            )

            with db:
                db.add(new_channel)
                db.commit()
            # We may need to integrate it to integration service.
            resp.update({"message":"channel added successfully"})
            # Create a new channel in the integration service
            # uncomment this helper function to create a channel in MIS
            # create_channel_in_mis(new_channel)

        return ORJSONResponse(
            content=resp, status_code=HTTPStatus.OK
        )

    except ValidationError as e:
        error_message = f"Validation failed: {e}"
        print(error_message)
        return error_message

import asyncio
import logging as log
from typing import Any, Dict

from sqlalchemy.orm import joinedload

from config.database import get_db
from config.worker import cel_app
from models import Channel
from serializers import OrderData, preprocess_order_data
from utils.helpers import notify_new_order_v2
from utils.maps import Tiktok


@cel_app.task(
    name="tasks.order.process",
    queue="tiktok_high_priority_queue",
    retry_kwargs={"max_retries": 3, "countdown": 5},
    ack_late=True,
)
def process_order(shop_id: int, data: Dict[Any, Any]):
    print(f"shop id ====> {shop_id}")
    order_data = OrderData(**data)
    print(f"order datra from webhook ==> {order_data}")
    db = next(get_db())
    try:
        channel: Channel = (
            db.query(Channel)
            .options(joinedload(Channel.tokens))
            .filter(Channel.shop_id == int(shop_id))
            .first()
        )
        if channel is None:
            log.error({"error": f"channel for shop_id {shop_id} not found"})
            return
    finally:
        db.close()

    # get order details

    loop = asyncio.get_event_loop()
    order_response = loop.run_until_complete( Tiktok.get_single_order_details(order_data.order_id, access_token=channel.tokens.access_token, shop_cipher=channel.shop_cipher))
    print(f'order response ==> {order_response.json()}')
    if order_response.json().get("code") != 0:
        print('order response from  tiktok',order_response)
        log.info(f"failed to fetch order id {order_data.order_id}")
        return

    # preprocess order payload
    order_payload = preprocess_order_data(
        channel_uid=channel.channel_uid,
        order_data=order_response.json().get("data"),
    )

    print("order payload=======>",order_payload)

    # send order data to order service
    notify_new_order_v2(order_payload,channel.channel_uid)
    return

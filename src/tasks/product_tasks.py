import asyncio
import logging as log
from typing import Any, Dict, List
import requests

from config.worker import cel_app
from config.app_vars import MYE_INVENTORY_AND_MAPPING_SERVICE_URL
from serializers import ProductData, RemoteProductData
from models import Channel
from utils.maps import Tiktok
from utils.helpers import get_channel_token_by_shop_id


def process_product_data(
    channel_uid: str, company_uid: str, product_data: Dict[Any, Any]):
    payload: Dict[str, Any] = {
        "channel_uid": channel_uid,
        "company_uid": company_uid,
        "data": [
            {
                "id": str(product_data["id"]),
                "sku": product_data["skus"][0]["seller_sku"],
                "name": product_data["title"],
                "fba_status": False,
                "image": product_data["main_images"][0]["urls"][0],
                "remote_product_name": product_data["title"],
                "remote_product_description": (
                    product_data["description"]
                    if len(product_data["description"]) < 2000
                    else ""
                ),
            }
        ],
    }

    return payload

def send_product_request(product_data: Dict[Any, Any], channel: Channel, task_type: str) -> None:
    # Prepare product data
    product_payload = process_product_data(
        channel_uid=channel.channel_uid,
        company_uid=channel.company_uuid,
        product_data=product_data
    )

    remote_product_add_url = MYE_INVENTORY_AND_MAPPING_SERVICE_URL + "/api/v1/mapping/product/remote-product/add/"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiaWQiOiI4MDYwNzgzMC01MmM5LTRiNWEtYjg0MS03ODY1NDQwYmNiOTMiLCJ1c2VyX2VtYWlsIjoibWlyYXpAZXZpZGVudGJkLmNvbSIsImF2YXRlcl91cmwiOiJodHRwczovL2FwaS5kaWNlYmVhci5jb20vOS54L2luaXRpYWxzL3N2Zz9zZWVkPUV2aWRlbnQlMjBCRCIsImV4cCI6MTczOTM2Mjc1OCwiTmFtZSI6Ik1vaGFtbWVkIE1pcmF6IiwicGhvbmUiOiIwMTgxNzIzIiwiYWRkcmVzcyI6IlV0dGFyYSwgQmFuZ2xhZGVzaCIsInR5cGUiOiJwYXJlbnQiLCJjb21wYW55X3VpZCI6Ijk1MDAyYmIwLWQxODItNGIxZS1hYTgwLTk0MDgwZDRiZWZjNiIsIm5hbWUiOiJSb3VnaCAmIFRvdWdoIiwiY291bnRyeSI6IlVuaXRlZCBLaW5nZG9tIiwic3RhdHVzIjp0cnVlLCJwZXJtaXNzaW9ucyI6W3siaWQiOiIyZTExNWVmNC00ZjMzLTRhOTQtOTlhYS1iN2M3OGViYmY0MWQiLCJuYW1lIjoiQ2hhbm5lbHMiLCJ1cmwiOiIvc2V0dGluZ3MvY2hhbm5lbHMiLCJzZXJ2aWNlIjoibXllIn0seyJpZCI6ImMxMzU5OGFmLTU1MzctNDA0ZS04MmY5LTAwODg5ZjFhZTUxZiIsIm5hbWUiOiJMb2NhdGlvbnMiLCJ1cmwiOiIvc2V0dGluZ3MvbG9jYXRpb25zIiwic2VydmljZSI6Im15ZSJ9LHsiaWQiOiI3Zjc5YjNiNS0yMzVjLTRlZDEtODc2Yy03ODc2OWU0NWIwMWQiLCJuYW1lIjoiQ2FycmllcnMiLCJ1cmwiOiIvc2V0dGluZ3MvY2FyZWVycyIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiYzdkMGZiY2MtNDU0Ni00MmE2LWEwN2EtNjk3MmFiNTc5MWM2IiwibmFtZSI6IlByb2R1Y3RzIiwidXJsIjoiL3NldHRpbmdzL3Byb2R1Y3RzIiwic2VydmljZSI6Im15ZSJ9LHsiaWQiOiI1N2FjMjZkMC1hNzdjLTQyNmMtYmU3NC01ZDdiMDg3OTNiZjIiLCJuYW1lIjoiT3BlbiBPcmRlciBSZXBvcnQiLCJ1cmwiOiIvcmVwb3J0cy9vcGVuLW9yZGVycyIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiZTYzMzcxNGUtYzliYy00Y2NhLWEyMmYtMzRlZjFlMzMzZGYzIiwibmFtZSI6IlNhbGVzIFJlcG9ydCIsInVybCI6Ii9yZXBvcnRzL3NhbGVzLXJlcG9ydCIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiZWE3ZjBiNWEtNzVmMy00Y2UwLTgwMjctZGMzNzA4YTk3NWI1IiwibmFtZSI6IlN0b2NrIFJlcG9ydCIsInVybCI6Ii9yZXBvcnRzL3N0b2NrLXJlcG9ydCIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiNmFiZWMwYzItYTQwYi00MzIwLThlMTctYjU5NjhiYjQ1OWVkIiwibmFtZSI6ImludmVudG9yeSIsInVybCI6Ii9pbnZlbnRvcnkiLCJzZXJ2aWNlIjoibXllIn0seyJpZCI6ImRhNjE5MjY1LTU4NzktNDhhMy1hMzQ1LTg0ZTk0NTdmY2YxNyIsIm5hbWUiOiJpbnZlbnRvcnktdmlldy1vbmx5IiwidXJsIjoiL2ludmVudG9yeSIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiOWJmMTljOTMtODRhMi00MjIwLTllMDEtMWQ5ZDc4NTlkYzViIiwibmFtZSI6ImRhc2hib2FyZCIsInVybCI6Ii9kYXNoYm9hcmQiLCJzZXJ2aWNlIjoibXllIn1dLCJyZXN0cmljdGlvbnMiOnsic3Vic2NyaWJlZCI6ZmFsc2V9fQ.QvYqszOUWxu2UiSCfAEvpLTWi74lxi4cmMP97xkQ04YC18SbckkIh37nTVePw0XaPF_ZHnOCAnuUVr7sxtJ0B9U3QXdlrfE7HedTMqQ3MVBmJe6UkNXCELQFUQpiNhg10eVvw7CoB4gPhHKIWQ_51RKgIlYPyIT_pWoPqQm5v1Bu3uHxbIJcjdkgAKuHY3SXYop6F9jqqNyGezA3lsTzA8t_Xbx0nJm2FSwqO36dwB2zD_005V67slrzYZO-V3t-_Eff9Dt4Q2Vb9Qf0W3GsMb5v1xM_F5g3SSlhTgqLzexr7wJ0jPJdv0uk2-JjpiHnEKn8_ZWgrOxEs9EIkzmcBQ'
    } # AUthorization token is required only for local remove before going live

    # Send the request
    response = requests.post(remote_product_add_url, json=product_payload, headers=headers)

    # Log response based on task type (creation or update)
    if int(response.status_code) != 201:
        log.info(f"Failed to {task_type} remote product. Error code {response.status_code}")
        return
    log.info(f"Product {task_type} successfully {response.json()}")


@cel_app.task(name='tasks.product.sync', retry_kwargs={'max_retries': 3, 'countdown': 5}, ack_late=True)
def process_product_creation(shop_id: str, data: Dict[Any, Any]):
    order_data = ProductData(**data)
    print(f"shop id ====> {shop_id}")
    print(order_data.model_dump())
    channel = get_channel_token_by_shop_id(shop_id=shop_id)
    if not channel:
        log.error(f"Failed to get channel for shop id: {shop_id}")
        return None
    # Run the async function synchronously
    loop = asyncio.get_event_loop()
    product = loop.run_until_complete(Tiktok.get_single_product_details(
        product_id=order_data.product_id,
        access_token=channel.tokens.access_token,
        shop_cipher=channel.shop_cipher,
    ))
    product_json = product.json()
    if product_json.get("code") != 0:
        log.info(f"failed to fetch product id {order_data.product_id}")
        return
    # Send the create request in MIAMS
    send_product_request(product_json["data"], channel, "create")


@cel_app.task(name='tasks.product.update', retry_kwargs={'max_retries': 3, 'countdown': 5}, ack_late=True)
def process_product_update(shop_id: str, data: Dict[Any, Any]):
    product_id: str = str(data.get("product_id", ""))
    required_fields_for_products: List[str] = ["title", "description", "sku", "main_images"]
    changed_fields: List[str] = data.get("changed_fields", [])
    # Check if update is necessary
    if not any(field in changed_fields for field in required_fields_for_products):
        log.info("No update needed for the product.")
        return

    log.info("product need to be updated")
    # Get channel and token from the database
    channel = get_channel_token_by_shop_id(shop_id=shop_id)
    if not channel:
        log.error(f"Failed to get channel for shop id: {shop_id}")
        return None

    # Run the async function synchronously
    loop = asyncio.get_event_loop()
    product = loop.run_until_complete(Tiktok.get_single_product_details(
        product_id=product_id,
        access_token=channel.tokens.access_token,
        shop_cipher=channel.shop_cipher,
    ))
    product_json = product.json()
    if product_json.get("code") != 0:
        log.info(f"failed to fetch product id {product_id}")
        return
    # send the product update request to MIAMS
    send_product_request(product_json["data"], channel, "update")

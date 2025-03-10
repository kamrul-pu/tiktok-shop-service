import hashlib
import hmac
import json
import logging as log
from urllib.parse import parse_qs, urlencode, urlparse
from sqlalchemy.orm import joinedload
import requests
import datetime
from typing import Dict, Any
import asyncio

from config.app_vars import INTEGRATION_SERVICE, MYE_ORDER_SERVICE_URL, APP_KEY, APP_SECRET
from config.database import get_db
from models import Channel, Token

async def calculate_signature(
    url: str, params: dict, headers: dict, secret: str, body: bytes=None, **kwargs
):
    """
    Calculate the signature based on query parameters, request path, and body.

    :param req: A dictionary representing the request with keys 'url', 'headers', and 'body'.
                - 'url' should contain the full URL of the request.
                - 'headers' should be a dictionary of HTTP headers.
                - 'body' should be a byte stream or a string of the request body.
    :param secret: The app secret key used for signing.
    :return: The calculated signature as a hexadecimal string.
    """
    # Parse query parameters from the URL
    url_parts = urlparse(url)
    query_string = urlencode(params, doseq=True)
    queries = parse_qs(query_string)

    for k, v in kwargs.items():
        queries[k] = [str(v)]

    # Extract all query parameters excluding 'sign' and 'access_token'
    keys = [k for k in queries if k not in {"sign", "access_token"}]

    # Reorder the parameters' keys in alphabetical order
    keys.sort()

    # Concatenate all the parameters in the format of {key}{value}
    input_data = ""
    for key in keys:
        input_data += key + "".join(
            queries[key]
        )  # Join query values as a single string

    # Append the request path
    input_data = url_parts.path + input_data

    # Check if Content-Type is not multipart/form-data and append body if needed
    content_type = headers.get("Content-Type", "")
    if not content_type.startswith("multipart/form-data"):
        if isinstance(body, bytes):
            body = body.decode("utf-8")

        if body is not None:
            input_data += body

    # Wrap the generated string with the App secret
    input_data = secret + input_data + secret
    # Generate the HMAC-SHA256 signature
    return generate_sha256(input_data, secret)


def generate_sha256(input_data, secret):
    """
    Generate HMAC-SHA256 signature for the given input and secret.

    :param input_data: The data to be signed.
    :param secret: The secret key used for signing.
    :return: The generated signature in hexadecimal.
    """
    h = hmac.new(secret.encode("utf-8"), input_data.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()


def notify_new_order_v2(open_order, channel_uid, dispatched_order=[]):
    
    try:
        get_channel_url = (
            INTEGRATION_SERVICE
            + f"/api/v1/channel/get-channel-company-uid/{channel_uid}/"
        )
        print("integration url:",get_channel_url)
        get_channel_req = requests.get(url=get_channel_url)
        print("get channel req:",get_channel_req)
        res = json.loads(get_channel_req.text)
        print("response from integration service",res)
        print("------------Order Is sending to order service--------------  ")

        order_service_url = MYE_ORDER_SERVICE_URL + "/api/v1/orders/add-v3/"
        # print(order_service_url)
        order_dict = {
            "channel_uid": channel_uid,
            "company_uid": res.get("data"),
            "data": [open_order],
            "missing_orders": dispatched_order,
        }

        print(
            f"Total New Order -> {len(open_order)} And Dispatched Order -> {len(dispatched_order)}"
        )
        print(f"The Payload that are sending to order service {order_dict}")
        headers = {
            "Content-Type": "application/json",
            'Authorization': f"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiaWQiOiI4MDYwNzgzMC01MmM5LTRiNWEtYjg0MS03ODY1NDQwYmNiOTMiLCJ1c2VyX2VtYWlsIjoibWlyYXpAZXZpZGVudGJkLmNvbSIsImF2YXRlcl91cmwiOiJodHRwczovL2FwaS5kaWNlYmVhci5jb20vOS54L2luaXRpYWxzL3N2Zz9zZWVkPUV2aWRlbnQlMjBCRCIsImV4cCI6MTczOTE3MzAxMSwiTmFtZSI6Ik1vaGFtbWVkIE1pcmF6IiwicGhvbmUiOiIwMTgxNzIzIiwiYWRkcmVzcyI6IlV0dGFyYSwgQmFuZ2xhZGVzaCIsInR5cGUiOiJwYXJlbnQiLCJjb21wYW55X3VpZCI6Ijk1MDAyYmIwLWQxODItNGIxZS1hYTgwLTk0MDgwZDRiZWZjNiIsIm5hbWUiOiJSb3VnaCAmIFRvdWdoIiwiY291bnRyeSI6IlVuaXRlZCBLaW5nZG9tIiwic3RhdHVzIjp0cnVlLCJwZXJtaXNzaW9ucyI6W3siaWQiOiIyZTExNWVmNC00ZjMzLTRhOTQtOTlhYS1iN2M3OGViYmY0MWQiLCJuYW1lIjoiQ2hhbm5lbHMiLCJ1cmwiOiIvc2V0dGluZ3MvY2hhbm5lbHMiLCJzZXJ2aWNlIjoibXllIn0seyJpZCI6ImMxMzU5OGFmLTU1MzctNDA0ZS04MmY5LTAwODg5ZjFhZTUxZiIsIm5hbWUiOiJMb2NhdGlvbnMiLCJ1cmwiOiIvc2V0dGluZ3MvbG9jYXRpb25zIiwic2VydmljZSI6Im15ZSJ9LHsiaWQiOiI3Zjc5YjNiNS0yMzVjLTRlZDEtODc2Yy03ODc2OWU0NWIwMWQiLCJuYW1lIjoiQ2FycmllcnMiLCJ1cmwiOiIvc2V0dGluZ3MvY2FyZWVycyIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiYzdkMGZiY2MtNDU0Ni00MmE2LWEwN2EtNjk3MmFiNTc5MWM2IiwibmFtZSI6IlByb2R1Y3RzIiwidXJsIjoiL3NldHRpbmdzL3Byb2R1Y3RzIiwic2VydmljZSI6Im15ZSJ9LHsiaWQiOiI1N2FjMjZkMC1hNzdjLTQyNmMtYmU3NC01ZDdiMDg3OTNiZjIiLCJuYW1lIjoiT3BlbiBPcmRlciBSZXBvcnQiLCJ1cmwiOiIvcmVwb3J0cy9vcGVuLW9yZGVycyIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiZTYzMzcxNGUtYzliYy00Y2NhLWEyMmYtMzRlZjFlMzMzZGYzIiwibmFtZSI6IlNhbGVzIFJlcG9ydCIsInVybCI6Ii9yZXBvcnRzL3NhbGVzLXJlcG9ydCIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiZWE3ZjBiNWEtNzVmMy00Y2UwLTgwMjctZGMzNzA4YTk3NWI1IiwibmFtZSI6IlN0b2NrIFJlcG9ydCIsInVybCI6Ii9yZXBvcnRzL3N0b2NrLXJlcG9ydCIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiNmFiZWMwYzItYTQwYi00MzIwLThlMTctYjU5NjhiYjQ1OWVkIiwibmFtZSI6ImludmVudG9yeSIsInVybCI6Ii9pbnZlbnRvcnkiLCJzZXJ2aWNlIjoibXllIn0seyJpZCI6ImRhNjE5MjY1LTU4NzktNDhhMy1hMzQ1LTg0ZTk0NTdmY2YxNyIsIm5hbWUiOiJpbnZlbnRvcnktdmlldy1vbmx5IiwidXJsIjoiL2ludmVudG9yeSIsInNlcnZpY2UiOiJteWUifSx7ImlkIjoiOWJmMTljOTMtODRhMi00MjIwLTllMDEtMWQ5ZDc4NTlkYzViIiwibmFtZSI6ImRhc2hib2FyZCIsInVybCI6Ii9kYXNoYm9hcmQiLCJzZXJ2aWNlIjoibXllIn1dLCJyZXN0cmljdGlvbnMiOnsic3Vic2NyaWJlZCI6ZmFsc2V9fQ.fwSbwMpwDlJ0mVj2EJxzzwqyveRdEoJN_nAsV5pQqV6dWbsHgIrcxVmyEo1UiTgSPbKIZgV4j4yve_DWdQzbVv4dDhfhjt4S63ugq9w2rjkpupru_r6ToMduCZjrWZFkUXdHv-EQumn6cZzku5Tcjw5lrX8bvIZnXnf3iNh57esslSDpkfK8x499UZZadBHOgMDlGgVgCtbqHImPP3oTnyPE1Xu9bsrmJoLTcPclNDUCXqHCAtV2zqn6VY8JDLXaoKU-up8Da8nC6Fwgb51B4ORr21AjX0vi2psHOZToQ8oCX0te87muP-YmU1s1dIYj3I8GAgwQwDl85ONcB3UEsA"
        }
        req = requests.post(order_service_url, json=order_dict, headers=headers)
        if int(req.status_code) != 200:
            log.error("Failed to send order in order service {}".format(req.status_code))
            return

        print(f"Order Service Response: {req.status_code}")
        log.info(f"Order service respose: {req.content}")

    except:
        log.error("Error Sending to Order Service")


# Function to get the channel and token based on channel uuid
async def get_channel_and_token(channel_uid: str):
    with next(get_db()) as db:
        channel: Channel = (
            db.query(Channel)
            .options(joinedload(Channel.tokens))
            .filter(Channel.channel_uid == channel_uid)
            .first()
        )

        if not channel:
            return None # No matching channel found
        # Check if the tokes are expired or not. If expired then get the new token
        current_timestamp = int(datetime.datetime.now().timestamp())
        if current_timestamp > channel.tokens.access_token_expiry:
            # need to get the new token and store it in the database
            url: str = "https://auth.tiktok-shops.com/api/v2/token/refresh"
            headers = {
                'Content-Type': 'application/json'
            }
            params: Dict[str, Any] = {
                "app_key": APP_KEY,
                "app_secret": APP_SECRET,
                "refresh_token": channel.tokens.refresh_token,
                "grant_type": "refresh_token"
            }
            response = requests.get(url, params=params, headers=headers).json()
            if response.get("code")!= 0:
                log.error("Failed to get new refresh token")
                return None
    
            data = response.get("data", {})
            channel.tokens.access_token = data.get("access_token", "")
            channel.tokens.refresh_token = data.get("refresh_token", "")
            channel.tokens.access_token_expiry = int(data.get("access_token_expire_in", 0))
            channel.tokens.refresh_token_expiry = int(data.get("refresh_token_expire_in", 0))
            db.commit()

        return channel


def get_channel_token_by_shop_id(shop_id: str):
    with next(get_db()) as db:
        # Fetch the Channel based on shop_id, along with the associated tokens
        channel: Channel = (
            db.query(Channel)
            .options(joinedload(Channel.tokens))
            .filter(Channel.shop_id == int(shop_id))
            .first()
        )

        # If no matching channel is found, return None
        if not channel:
            return None

        # Check if the tokens are expired and need refreshing
        current_timestamp = int(datetime.datetime.now().timestamp())
        if current_timestamp > channel.tokens.access_token_expiry:
            # Tokens are expired, so we need to refresh them
            url = "https://auth.tiktok-shops.com/api/v2/token/refresh"
            headers = {
                'Content-Type': 'application/json'
            }
            params: Dict[str, Any] = {
                "app_key": APP_KEY,
                "app_secret": APP_SECRET,
                "refresh_token": channel.tokens.refresh_token,
                "grant_type": "refresh_token"
            }

            # Make the request to refresh the access token
            response = requests.get(url, params=params, headers=headers).json()

            # If the response code is not 0, it means the refresh token is invalid or there was an issue
            if response.get("code") != 0:
                log.error(f"Failed to refresh token for shop_id {shop_id}. Response: {response}")
                return None

            # Parse the response and update the channel's tokens
            data = response.get("data", {})
            channel.tokens.access_token = data.get("access_token", "")
            channel.tokens.refresh_token = data.get("refresh_token", "")
            channel.tokens.access_token_expiry = int(data.get("access_token_expire_in", 0))
            channel.tokens.refresh_token_expiry = int(data.get("refresh_token_expire_in", 0))

            # Commit the changes to the database
            db.commit()

        # Return the channel with the valid (or refreshed) token
        return channel


async def create_channel_in_mis(channel: Channel):
    """Helper function to create channel in integration service"""
    # Need to check the function after new endpoint integrated in integration service
    url: str = INTEGRATION_SERVICE + "/api/v1/channel/add-channel/tiktok/"
    headers = {
        'Content-Type': 'application/json',
        'secret-key': '6433220e-5f0b-4238-bb11-046f589e9149' # require for calling integraion service from local only
    }
    payload = {
        "name": channel.name,
        "channel_uid": channel.channel_uid,
        "company_uid": channel.company_uuid,
        "channel_type": "tiktok",
        "channel_max_stock": 20,
        "country": channel.country,
        "channel_metadata": {
                "shop_id": channel.shop_id,
                "shop_cipher": channel.shop_cipher,
        }
    }
    payload = json.dumps(payload)
    log.info("Channel data is sending into integration service")
    # Run the async function synchronously
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(requests.post(url, json=payload, headers=headers)).json()
    if response.get("status_code")!=201:
        log.error("Failed to create channel in integration service")
        return None
    log.info("Channel created successfully in integration service")
    return True

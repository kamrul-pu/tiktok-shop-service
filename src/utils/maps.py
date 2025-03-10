from datetime import datetime, timezone
from typing import Any, Dict

import requests

from config.app_vars import APP_KEY, APP_SECRET
from utils.helpers import calculate_signature, get_channel_and_token


class Tiktok:
    """_summary_
    """

    order_status ={
        "UNPAID":"",
        "ON_HOLD":"",
        "AWAITING_SHIPMENT":"OPEN_ORDER",
        "AWAITING_COLLECTION":"",
        "CANCEL":"CANCELLED",
        "IN_TRANSIT":"DISPATCHED",
        "DELIVERED":"",
        "COMPLETED":"COMPLETED"
    }

    webhook_type = {
        1: "order_status_change",
        7: "upcoming_authorization_expiration",
        14: "new_message",
        16: "product_creation",
        27: "inventory_status_change"
    }

    @staticmethod
    async def get_access_token(auth_code:str):
        url = 'https://auth.tiktok-shops.com/api/v2/token/get'
        params = {
            'auth_code':auth_code,
            'app_key':APP_KEY,
            'app_secret':APP_SECRET,
            'grant_type':"authorized_code"
        }
        res = requests.get(url=url, params=params).json()
        if res.get('code') == 0:
            res = res.get('data')
            return (res.get('access_token'), res.get('refresh_token'), res.get('access_token_expire_in'), res.get('refresh_token_expire_in'), None)
        else:
            res = res.get('message')
            return (None, None, None, None, res)


    @staticmethod
    async def get_order_details(req_params:Dict[str, Any], headers:Dict[str, Any], body:bytes):
        channel = get_channel_and_token(channel_uid="YAUNZyZjELCiM82")
        print(req_params)
        print(headers)
        params = req_params

        params.update({
            'shop_cipher':channel.shop_cipher,
            'ids':['576706876408303384']
        })

        url = 'https://open-api.tiktokglobalshop.com/order/202309/orders'

        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = await calculate_signature(url=url, params=req_params, headers=headers, body=body, secret=APP_SECRET, timestamp=timestamp)
        headers={
            'x-tts-access-token':channel.tokens.access_token,
            'Content-Type': 'application/json'
        }
        params.update({'sign':signature, 'timestamp':timestamp})

        response = requests.get(url=url, params=params, headers=headers)

        return response
    
    @staticmethod
    async def get_single_order_details(order_id:str, access_token:str, shop_cipher:str):
        params = {
            "app_key":APP_KEY,
            "shop_cipher":shop_cipher,
            "ids":[order_id]
        }

        headers={
            'x-tts-access-token':access_token,
            'Content-Type': 'application/json'
        }

        url = 'https://open-api.tiktokglobalshop.com/order/202309/orders'

        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = await calculate_signature(url=url, params=params, headers=headers, body=None, secret=APP_SECRET, timestamp=timestamp)
        params.update({'sign':signature, 'timestamp':timestamp})

        response = requests.get(url=url, params=params, headers=headers)

        return response


    @staticmethod
    async def get_authorized_shops(access_token):
        params = {
            "app_key":APP_KEY
        }
        headers={
            'x-tts-access-token':access_token,
            'Content-Type': 'application/json'
        }

        url = 'https://open-api.tiktokglobalshop.com/authorization/202309/shops'

        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = await calculate_signature(url=url, params=params, headers=headers, secret=APP_SECRET, timestamp=timestamp)
        params.update({'sign':signature, 'timestamp':timestamp})

        response = requests.get(url=url, params=params, headers=headers)

        return response
    
    @staticmethod
    async def get_active_shops(req_params:Dict[str, Any], headers:Dict[str, Any], body:bytes):

        url = 'https://open-api.tiktokglobalshop.com/seller/202309/shops'

        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = await calculate_signature(url=url, params=req_params, headers=headers, body=body, secret=APP_SECRET, timestamp=timestamp)
        params = req_params
        headers={
            'x-tts-access-token':'GCP_lePaYgAAAACIqj1W3aFjQhyMu-goOMfTgbuMPWj1RSAzsZMajl87oJZSW7nYnWKDaP4zXiGSSXpw2vK3XZ56Ibdt7gWn-c706N5nR-xiz6yae4o8PtTjeVLJoXJ28SGpJmU79gvAE_boWZPBbcdy8BHQkWhSiVESsejdcRB1tzpiXjmBPhzpJA',
            'Content-Type': 'application/json'
        }
        params.update({'sign':signature, 'timestamp':timestamp})

        response = requests.get(url=url, params=params, headers=headers)

        return response

    @staticmethod
    async def update_product_stock(product_id:str, req_params:Dict[str, Any], headers:Dict[str, Any], body:bytes):

        url = f'https://open-api.tiktokglobalshop.com/product/202309/products/{product_id}/inventory/update'

        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = await calculate_signature(url=url, params=req_params, headers=headers, body=body, secret=APP_SECRET, timestamp=timestamp)
        params = req_params
        headers={
            'x-tts-access-token':'GCP_wkbyFAAAAACIqj1W3aFjQhyMu-goOMfTgbuMPWj1RSAzsZMajl87oJZSW7nYnWKDaP4zXiGSSXpw2vK3XZ56Ibdt7gWn-c70miWrCPt7oaCZWBBFz6GXtrbEW68v_Zrto2-iRbkX-M7OOyq4_iB6nszXSWZ6nFk0Po4n0C5bx_zE2ZxyXCDGSA',
            'Content-Type': 'application/json'
        }
        params.update({'sign':signature, 'timestamp':timestamp})

        response = requests.post(url=url, params=params, headers=headers)

        return response
    
    @staticmethod
    async def get_single_product_details(product_id:str, access_token:str, shop_cipher:str):
        params = {
            "app_key":APP_KEY,
            "shop_cipher":shop_cipher
        }

        headers={
            'x-tts-access-token':access_token,
            'Content-Type': 'application/json'
        }

        url = f"https://open-api.tiktokglobalshop.com/product/202309/products/{product_id}"

        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = await calculate_signature(url=url, params=params, headers=headers, body=None, secret=APP_SECRET, timestamp=timestamp)
        params.update({'sign':signature, 'timestamp':timestamp})

        response = requests.get(url=url, params=params, headers=headers)

        return response
    
    # Static method to update product inventory using TikTok Global Shop API
    @staticmethod
    async def update_product_inventory(product_id: str, access_token: str, shop_cipher: str, payload: Dict[str, Any]):
        # Prepare parameters for the API request
        params = {
            "app_key": APP_KEY,          # Application key for authentication
            "shop_cipher": shop_cipher   # Unique identifier for the shop
        }

        # Set headers for the request, including access token for authorization
        headers = {
            'x-tts-access-token': access_token,  # Access token to authorize the request
            'Content-Type': 'application/json'   # Indicate that the payload is in JSON format
        }

        # Define the URL for the TikTok Global Shop API endpoint to update the product inventory
        url = f"https://open-api.tiktokglobalshop.com/product/202309/products/{product_id}/inventory/update"

        # Get the current timestamp in UTC format, which is used for signature calculation and API request
        timestamp = int(datetime.now(timezone.utc).timestamp())

        # Calculate the request signature using the provided parameters, headers, secret, and timestamp
        signature = await calculate_signature(url=url, params=params, headers=headers, secret=APP_SECRET, timestamp=timestamp, body=payload)

        # Update the params dictionary with the signature and timestamp
        params.update({'sign': signature, 'timestamp': timestamp})

        # Make the POST request to the API with the given URL, parameters, headers, and payload (request body)
        response = requests.post(url=url, params=params, headers=headers, data=payload)

        # Return the API response (this could be used to check for success or failure)
        return response

import json
import logging as log

from celery import bootsteps
from kombu import Consumer, Exchange, Queue

from config.database import get_db
from config.worker import cel_app
from models import Channel, InventoryRequest

exchange = Exchange("mye-tiktok-inventory-exchange")
inventory_update_queue = Queue(
    "mye-tiktok-inventory-queue", exchange, routing_key=""
)

def insert_inventory_update_request(channel_uid, sku, quantity, product_id, request_metadata):
    db = next(get_db())
    with db:
        channel = db.query(Channel).filter(Channel.channel_uid == channel_uid).first()
        
        if not channel:
            print(f'channel {channel_uid} not found')
            return True  # Acknowledge true for unknown channel

        existing_inventory_request = db.query(InventoryRequest).\
            filter(
                InventoryRequest.channel_uid == channel_uid,
                InventoryRequest.sku == sku,
                InventoryRequest.item_id == product_id,
                InventoryRequest.status == InventoryRequest.StatusChoices.PENDING # should be changed
            ).first()

        if existing_inventory_request:
            print("updating quantity")
            existing_inventory_request.quantity = quantity
            
            db.commit()
            db.close()
        
        else:
            
            try:
                inventoryrequest = InventoryRequest(
                    channel_uid=channel.channel_uid,
                    sku=sku,
                    quantity=quantity,
                    item_id=product_id,
                    status=InventoryRequest.StatusChoices.PENDING, # should be changed
                    request_metadata=request_metadata
                )
                
                db.add(inventoryrequest)
                db.commit()
                db.close()
                print(f"inventory request creation successful {sku} - {channel_uid}")
                return True
            except Exception as e:
                db.rollback()
                db.commit()
                db.close()
                print(f"inventory request creation failed for {sku} - {channel_uid}")
                print(f"cause: {str(e)}")
    
    return True

class InventoryRequestProcessWorker(bootsteps.ConsumerStep):
    def get_consumers(self, channel):
        print("Getting inventory consumer")
        return [
            Consumer(
                channel,
                queues=[inventory_update_queue],
                callbacks=[self.on_message],
                accept=["json", "text/plain"],
            )
        ]

    def on_message(self, body, message):
        
        try:
            data = json.loads(body)
            if data.get('channel_type') != "tiktok":
                should_acknowledge = True

            elif data.get('channel_type') == "tiktok":
                print(f"data received: {data['channel_uid']} - {data['sku']} - {data['available_quantity']} - {data['product_id']}")
                should_acknowledge = insert_inventory_update_request(
                    data['channel_uid'],
                    data['sku'],
                    data['available_quantity'],
                    data['product_id'],
                    data.get('request_metadata',{})
                )
            else:
                should_acknowledge = True
            
            if should_acknowledge:
                message.ack()

        except Exception as e:
            log.error({"error":str(e)})
            return


cel_app.steps["consumer"].add(InventoryRequestProcessWorker)

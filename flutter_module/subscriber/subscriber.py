import logging
import asyncio
import os
from typing import Callable, Dict, Tuple

from amqtt.client import MQTTClient, ClientException
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)

# Get broker host from environment or default
BROKER_HOST = os.getenv("HOST", "localhost")

# Handlers map: topic -> (QoS, callback)
subscriptions: Dict[str, Tuple[int, Callable[[str], None]]] = {}

def register_handler(topic: str, qos: int, callback: Callable[[str], None]):
    subscriptions[topic] = (qos, callback)
    logger.debug(f"Registered handler for topic '{topic}' with QoS {qos}")

async def message_receiver():
    client = MQTTClient()
    await client.connect(f"mqtt://{BROKER_HOST}:1883/")

    # Build subscription list: List of (topic, qos)
    subscription_list = [(topic, qos) for topic, (qos, _) in subscriptions.items()]
    await client.subscribe(subscription_list)
    logger.info(f"Subscribed to topics: {subscription_list}")

    try:
        while True:
            message = await client.deliver_message()
            packet = message.publish_packet
            topic = packet.variable_header.topic_name
            payload = packet.payload.data.decode()

            logger.info(f"Received: {topic} => {payload}")

            if topic in subscriptions:
                _, callback = subscriptions[topic]
                callback(payload)
            else:
                logger.warning(f"No handler registered for topic: {topic}")
    except ClientException as ce:
        logger.error(f"Client exception: {ce}")
    except asyncio.CancelledError:
        logger.info("Subscriber coroutine cancelled.")
    finally:
        await client.unsubscribe(list(subscriptions.keys()))
        await client.disconnect()
        logger.info("Disconnected and unsubscribed.")



if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(message_receiver())
    except KeyboardInterrupt:
        print("Subscriber stopped manually.")

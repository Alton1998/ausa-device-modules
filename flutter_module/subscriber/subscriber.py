import logging
import asyncio
import os
import fnmatch
from typing import Callable, List, Tuple

from amqtt.client import MQTTClient, ClientException
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

from authentication_handler.authentication_handler import authentication_handler, otp_verify_handler

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)

# Environment broker config
BROKER_HOST = os.getenv("HOST", "localhost")

# Handler type: (pattern, qos, callback)
subscriptions: List[Tuple[str, int, Callable[[str, str], None]]] = []

def register_handler(topic_pattern: str, qos: int, callback: Callable[[str, str], None]):
    subscriptions.append((topic_pattern, qos, callback))
    logger.debug(f"Registered handler for topic '{topic_pattern}' with QoS {qos}")

async def message_receiver():
    client = MQTTClient()
    await client.connect(f"mqtt://{BROKER_HOST}:1883/")

    # Build subscription list
    topic_qos_list = [(pattern, qos) for pattern, qos, _ in subscriptions]
    await client.subscribe(topic_qos_list)
    logger.info(f"Subscribed to topics: {topic_qos_list}")

    try:
        while True:
            message = await client.deliver_message()
            packet = message.publish_packet
            topic = packet.variable_header.topic_name
            payload = packet.payload.data.decode()

            logger.info(f"Received: {topic} => {payload}")

            matched = False
            for pattern, _, callback in subscriptions:
                if fnmatch.fnmatchcase(topic, pattern.replace("#", "*").replace("+", "?")):
                    callback(topic, payload)
                    matched = True
            if not matched:
                logger.warning(f"No handler matched for topic: {topic}")

    except ClientException as ce:
        logger.error(f"Client exception: {ce}")
    except asyncio.CancelledError:
        logger.info("Subscriber coroutine cancelled.")
    finally:
        await client.unsubscribe([pattern for pattern, _, _ in subscriptions])
        await client.disconnect()
        logger.info("Disconnected and unsubscribed.")

# Run the MQTT subscriber
if __name__ == "__main__":
    register_handler("authentication/#", QOS_2, authentication_handler)
    register_handler("otp/verify/#",QOS_2,otp_verify_handler)
    try:
        asyncio.get_event_loop().run_until_complete(message_receiver())
    except KeyboardInterrupt:
        print("Subscriber stopped manually.")

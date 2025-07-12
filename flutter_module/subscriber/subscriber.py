import logging
import asyncio
import os
import fnmatch
from typing import Callable, List, Tuple

from amqtt.client import MQTTClient, ClientException
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2
from azure.iot.device.iothub.aio import IoTHubModuleClient

from authentication_handler.authentication_handler import authentication_handler, otp_verify_handler, authenticate_user

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)

# Environment broker config
BROKER_HOST = os.getenv("HOST", "localhost")
BROKER_PORT = os.getenv("PORT",2883)

# Handler type: (pattern, qos, callback)
subscriptions: List[Tuple[str, int, Callable[[str, str], None]]] = []


def register_handler(topic_pattern: str, qos: int, callback: Callable[[str, str], None]):
    subscriptions.append((topic_pattern, qos, callback))
    logger.debug(f"Registered handler for topic '{topic_pattern}' with QoS {qos}")


async def message_receiver():
    azure_iot_edge_client = IoTHubModuleClient.create_from_edge_environment()

    def twin_patch_handler(patch):
        logger.info(f"the data in the desired properties patch was:{patch}")
        if "deviceToken" in patch:
            os.environ["DEVICE_TOKEN"] = patch["deviceToken"]["token"]

    azure_iot_edge_client.on_twin_desired_properties_patch_received = twin_patch_handler

    for key, value in os.environ.items():
        logger.info(f"{key}: {value}")
    client = MQTTClient()
    await client.connect(f"mqtt://{BROKER_HOST}:{BROKER_PORT}/")

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
                if topic.endswith("/response"):
                    continue
                if fnmatch.fnmatchcase(topic, pattern.replace("#", "*").replace("+", "?")):
                    response = callback(topic, payload)
                    logger.info(f"Callback:{callback} and Response: {response}")
                    await client.publish(topic + "/response", response, QOS_2)
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
    register_handler("otp/verify/#", QOS_2, otp_verify_handler)
    register_handler("authenticate_user/#",QOS_2, authenticate_user)
    try:
        asyncio.get_event_loop().run_until_complete(message_receiver())
    except KeyboardInterrupt:
        print("Subscriber stopped manually.")

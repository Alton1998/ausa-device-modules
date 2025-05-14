import logging
import asyncio

from amqtt.client import MQTTClient, ClientException
from amqtt.mqtt.constants import QOS_1,QOS_2,QOS_0

logger = logging.getLogger(__name__)


async def message_receiver():
    client = MQTTClient()
    await client.connect("mqtt://127.0.0.1:1883/")

    await client.subscribe([
        ("a/b", QOS_1),
    ])

    logger.info("Subscribed to topic 'a/b'")

    await asyncio.sleep(1)

    try:
        while True:
            message = await client.deliver_message()
            logger.info(message)
            packet = message.publish_packet
            print(
                f"Recieved: {packet.variable_header.topic_name} => {packet.payload.data.decode()}"
            )

    except ClientException as ce:
        logger.error(f"Client exception: {ce}")
    except asyncio.CancelledError:
        logger.info("Subscriber coroutine cancelled.")
    finally:
        await client.unsubscribe(["a/b"])
        await client.disconnect()
        logger.info("Disconnected and unsubscribed.")


if __name__ == "__main__":
    formatter = "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)
    try:
        asyncio.get_event_loop().run_until_complete(message_receiver())
    except KeyboardInterrupt:
        print("Subscriber stopped manually.")

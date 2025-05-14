import logging
import asyncio

from amqtt.client import MQTTClient, ConnectException
from amqtt.mqtt.constants import QOS_1, QOS_2

logger = logging.getLogger(__name__)

config = {
    "will": {
        "topic": "/will/client",
        "message": b"Dead or alive",
        "qos": 0x01,
        "retain": True,
    }
}


async def publish_messages():
    try:
        C = MQTTClient(config=config)
        await C.connect("mqtt://localhost:1883/")

        await C.publish("a/b", b"TEST MESSAGE WITH QOS_0", qos=0x00)
        await C.publish("a/b", b"TEST MESSAGE WITH QOS_1", qos=QOS_1)
        await C.publish("a/b", b"TEST MESSAGE WITH QOS_2", qos=QOS_2)

        logger.info("Messages published")

        await C.disconnect()
    except ConnectException as ce:
        logger.error("Connection failed: %s" % ce)
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    formatter = (
        "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    )
    formatter = "%(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)
    asyncio.get_event_loop().run_until_complete(publish_messages())

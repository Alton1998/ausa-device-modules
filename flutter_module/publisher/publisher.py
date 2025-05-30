import logging
import asyncio

from amqtt.client import MQTTClient, ConnectException
from amqtt.mqtt.constants import QOS_1, QOS_2
import os

logger = logging.getLogger(__name__)

config = {
    "will": {
        "topic": "/will/client",
        "message": b"Dead or alive",
        "qos": 0x01,
        "retain": True,
    }
}

HOST = os.getenv("HOST","broker")

async def publish_messages():
    try:
        C = MQTTClient(config=config)
        await C.connect(f"mqtt://{HOST}:1883/")
        await C.publish("authentication/1231232", b"{\n    \"identifier\" : \"amjad@ausa.health\",\n    \"password\" : \"Admin@Ausa2025\"\n}", qos=QOS_2)
        await C.publish("authenticate_user/1231232",
                        b"{\n    \"identifier\" : \"amjad@ausa.health\",\n    \"password\" : \"Admin@Ausa2025\"\n}",
                        qos=QOS_2)
        await C.publish("otp/verify/1231231231",b"Test",qos=QOS_2)

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

import logging

logger = logging.getLogger(__name__)

def authencation_handler(topic,payload):
    logger.info(f"{topic} received:{payload}")

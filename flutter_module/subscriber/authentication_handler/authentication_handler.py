import logging
import os


logger = logging.getLogger(__name__)

MAIN_SERVER_URI = os.getenv("MAIN_SERVER")


def check_main_server_uri_set(func):
    def actual_check():
        if not MAIN_SERVER_URI:
            raise Exception("Set the Variable Main Server Uri in the environments in the manifest file. Youuuuu Dumb Bruhhhhhh. Like Sooooooo Dumbbb")
    def inner(topic,payload):
        actual_check()
        return func(topic,payload)
    return inner

@check_main_server_uri_set
def authentication_handler(topic, payload):
    logger.info(f" Authentication Handler: {topic} received:{payload}")

@check_main_server_uri_set
def otp_verify_handler(topic,payload):
    logger.info(f" OTP Verify handler : {topic} received:{payload}")
    request_body = {

    }

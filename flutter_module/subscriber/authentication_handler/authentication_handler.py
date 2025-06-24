import asyncio
import logging
import os
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from azure.iot.device.iothub.aio import IoTHubModuleClient
import re
import json
import requests
import httpx

from azure.iot.device.common.auth import connection_string as cs

logger = logging.getLogger(__name__)

MAIN_SERVER_URI = os.getenv("MAIN_SERVER","api.ausa.health")
DEVICE_ID = os.getenv("IOTEDGE_DEVICEID")
CERTIFICATE_FILE_PATH = os.getenv("CERT_PATH","/var/aziot")
CERTIFICATE_PATTERN = r".*-full-chain\.cert\.pem$"
AUTH_TYPE = os.getenv("IOTEDGE_AUTHSCHEME")
MODULE_ID = os.getenv("IOTEDGE_MODULEID","subscriber")

def get_sha256_thumbprint(cert_path):
    with open(cert_path, "rb") as f:
        cert_data = f.read()
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    return cert.fingerprint(hashes.SHA256()).hex().upper()


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
    logger.debug(f"DEVICE ID:{DEVICE_ID}")
    primaryThumbprint = None
    secondaryThumbprint = None
    payload = json.loads(payload)
    try:
        identifier = payload["identifier"]
        password = payload["password"]
    except Exception as e:
        logger.error(e)
        return json.dumps({"status":"Credentials missing"}).encode("utf-8")
    for filename in os.listdir(CERTIFICATE_FILE_PATH):
        logger.info(f"Iterating:{filename}")
        if re.match(CERTIFICATE_PATTERN,filename) and os.path.isfile(os.path.join(CERTIFICATE_FILE_PATH,filename)):
            logger.info(f"Found Certificate:{filename} in {CERTIFICATE_FILE_PATH}")
            primaryThumbprint = get_sha256_thumbprint(os.path.join(CERTIFICATE_FILE_PATH,filename))
            secondaryThumbprint = get_sha256_thumbprint(os.path.join(CERTIFICATE_FILE_PATH,filename))
            break

    request_body = {
        "deviceId":DEVICE_ID,
        "x509Thumbprint":{
            "primaryThumbprint": primaryThumbprint,
            "secondaryThumbprint":secondaryThumbprint,
        },
        "authType":"x509",
        "authModuleId": MODULE_ID,
        "identifier": payload["identifier"],
        "password": payload["password"]
    }
    logger.info(f"Posting: {request_body}")

    with httpx.Client(http2=True) as client:
        response = client.post(f"https://{MAIN_SERVER_URI}/edgeDevices/ausaHub/loginDevice", json=request_body)
    logger.info(f"Response Status Code:{response.status_code}")
    logger.info(f"Response received:{response.text}")
    logger.info(f"Device Token:{os.getenv('DEVICE_TOKEN')}")
    return json.dumps({"device_token":os.getenv('DEVICE_TOKEN')}).encode("utf-8")

@check_main_server_uri_set
def authenticate_user(topic,payload):
    logger.info(f" Authenticate user Handler: {topic} received:{payload}")
    bearer_token = os.getenv("DEVICE_TOKEN")
    payload = json.loads(payload)
    if bearer_token is None:
        logger.info("DEVICE_TOKEN is not set, generated Device Token first")
        authentication_handler(topic,payload)
    try:
        identifier = payload["identifier"]
        password = payload["password"]
    except Exception as e:
        logger.error(e)
        return json.dumps({"status":"Credentials missing"}).encode("utf-8")
    header = {
        "Authorization":f"Bearer {bearer_token}",
        "Content-Type":"application/json"
    }
    request_body = {
    "identifier": payload["identifier"],
    "password": payload["password"]
    }
    with httpx.Client(http2=True) as client:
        response = client.post(f"https://{MAIN_SERVER_URI}/edgeDevices/ausaHub/loginUser", json=request_body,headers=header)
    logger.info(f"Response Status Code:{response.status_code}")
    logger.info(f"Response received:{response.text}")
    if not (response.status_code == 200) :
        return json.dumps({"status": "not authenticated"}).encode("utf-8")
    return json.dumps({"status":"authenticated"}).encode("utf-8")


@check_main_server_uri_set
def otp_verify_handler(topic,payload):
    logger.info(f" OTP Verify handler : {topic} received:{payload}")
    request_body = {

    }
    return "".encode("utf-8")

def user_details(topic,payload):
    pass

import paho.mqtt.client as mqtt
import threading
import time

from paho.mqtt.enums import CallbackAPIVersion


class MQTTClientSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, broker='localhost', port=1883, client_id=""):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_client(broker, port, client_id)
            return cls._instance

    def _init_client(self, broker, port, client_id):
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2,client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.broker = broker
        self.port = port
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = True
        print("Connected to MQTT broker with result code", rc)

    def _on_message(self, client, userdata, msg):
        print(f"[{msg.topic}] {msg.payload.decode()}")

    def connect(self):
        if not self.connected:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()  # non-blocking

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish(self, topic, payload, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)



mqtt_client = MQTTClientSingleton()
mqtt_client.connect()
mqtt_client.subscribe("devices/fridge/status")

# Simulate another part of app using same client
another_client = MQTTClientSingleton()
another_client.publish("devices/fridge/status", "ON")

time.sleep(2)  # Wait for message to be received
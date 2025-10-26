import paho.mqtt.client as mqtt
import ssl

BROKER_URL = "10.72.180.70"
BROKER_PORT = 8883
CA_CERT = "./certs/ca.crt"
CLIENT_CERT = "./certs/client.crt"
CLIENT_KEY = "./certs/client.key"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected successfully")
        client.subscribe("/test") 
    else:
        print(f"MQTT connection failed, code: {rc}")

def on_message(client, userdata, msg):
    print(f"Received on {msg.topic}: {msg.payload.decode()}")

def init_mqtt():
    mqtt_client = mqtt.Client(client_id="smart-light", clean_session=True)

    mqtt_client.tls_set(
        ca_certs=CA_CERT,
        certfile=CLIENT_CERT,
        keyfile=CLIENT_KEY,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )
    mqtt_client.tls_insecure_set(True)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(BROKER_URL, BROKER_PORT, 60)
    mqtt_client.loop_start()

    return mqtt_client
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"   # must match MQTTSettings.server in your robot script
PORT = 1883            # must match MQTTSettings.port
CHANNEL = "v1"         # must match MQTTSettings.channel
ROBOT_ID = 10          # must match the id you gave the robot

# client = mqtt.Client()     
client = mqtt.Client(protocol=mqtt.MQTTv5)

client.connect(BROKER, PORT)
client.loop_start()

topic_single = f"{CHANNEL}/robot/msg/{ROBOT_ID}"
topic_broadcast = f"{CHANNEL}/robot/msg/broadcast"

# helper to publish and show what we sent
def send(topic, payload):
    print(f"-> {topic}: {payload}")
    client.publish(topic, payload)

send(topic_single, "START")
time.sleep(1)
send(topic_single, "STOP")
send(topic_single, "RESET")
send(topic_broadcast, "START")  # start all robots on this channel

# ask the robot to identify itself; listen for reply
def on_msg(_c, _u, m):
    try:
        body = m.payload.decode()
    except Exception:
        body = str(m.payload)
    print(f"<- {m.topic}: {body}")

client.on_message = on_msg
client.subscribe(f"{CHANNEL}/robot/live")
send(topic_single, "ID?")
time.sleep(2)

client.loop_stop()
client.disconnect()
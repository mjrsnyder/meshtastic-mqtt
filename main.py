import meshtastic
import logging
from pubsub import pub
import paho.mqtt.client as mqtt
import json
import geohash2

class PositionUpdate:
    def __init__(self, packet):
        self.latitude = packet["decoded"]["data"]["position"]["latitude"]
        self.longitude = packet["decoded"]["data"]["position"]["longitude"]
        self.altitude = packet["decoded"]["data"]["position"]["altitude"]
        self.node_id = packet["from"]
        self.geohash = geohash2.encode(self.latitude, self.longitude)
        self.rx_snr = None

        if ("rxSnr" in packet):
            self.rx_snr = packet["rxSnr"]

    def get_influxdb_format(self):
        data = [
                {
                    "latitude" : self.latitude,
                    "longitude" : self.longitude,
                    "altitude" : self.altitude
                }
                ,{
                    "node_id" : str(self.node_id),
                    "geohash" : self.geohash
                }
            ]
        if self.rx_snr:
            data[0]["rx_snr"] = self.rx_snr
        
        return json.dumps(data)

def onReceive(packet, interface): # called when a packet arrives
    print(f"Received: {packet}")
    if (len(packet["decoded"]["data"]["payload"])):
        update = PositionUpdate(packet)

        mqtt_client = mqtt.Client()
        mqtt_client.connect("127.0.0.1", 1883, 60)
        mqtt_client.publish("meshtastic/position", update.get_influxdb_format())
        mqtt_client.disconnect()


def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    # defaults to broadcast, specify a destination ID if you wish
    #interface.sendText("hello mesh")
    print(f"Connected to device")

interface = meshtastic.TCPInterface("127.0.0.1")

pub.subscribe(onReceive, "meshtastic.receive.position")
pub.subscribe(onConnection, "meshtastic.connection.established")

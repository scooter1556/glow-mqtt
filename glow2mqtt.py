#
# Copyright (c) 2022 Scott Ware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import json
import sys

import paho.mqtt.client as mqtt

from lib.glow_processor import GlowProcessor
from lib.hass_configurator import HassConfigurator

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Glow MQTT Client')
parser.add_argument('--glow_provider', required=False, default='HILD', help='Glow device provder default: HILD')
parser.add_argument('--glow_device', required=True, help='Glow device ID')
parser.add_argument('--glow_username', required=False, help='Glow username')
parser.add_argument('--glow_password', required=False, help='Glow password')
parser.add_argument('--mqtt_address', required=False, default='localhost',  help='MQTT broker address default: localhost')
parser.add_argument('--mqtt_port', required=False, type=int, default=1883, help='MQTT port default: 1883')
parser.add_argument('--mqtt_username', required=False, default='', help='MQTT username')
parser.add_argument('--mqtt_password', required=False, default='', help='MQTT password')
parser.add_argument('--homeassistant', default=False, action='store_true', help='Enable Home Assistant auto-discovery')
parser.add_argument('--topic', required=False, default='glow', help='Local MQTT topic default: glow')
parser.add_argument('--local', default=False, action='store_true', help='Use local MQTT mode')
parser.add_argument('--cache', default=False, action='store_true', help='Enable data caching')
parser.add_argument('--debug', default=False, action='store_true', help='Print debug information')
args = vars(parser.parse_args())

# Variables
provider = args['glow_provider']
device_id = args['glow_device']
username = args['glow_username']
password = args['glow_password']
mqtt_address = args['mqtt_address']
mqtt_port = int(args['mqtt_port'])
mqtt_username = args['mqtt_username']
mqtt_password = args['mqtt_password']
topic = args['topic']
local = args.get('local')
cache = args.get('cache')
homeassistant = args.get('homeassistant')
debug = args.get('debug')

s_mqtt_topic = "SMART/" + provider + "/" + device_id
p_mqtt_topic = topic + "/" + device_id
l_mqtt_topic = p_mqtt_topic + "/" + "SENSOR" + "/" + "#"

def on_connect(client, obj, flags, rc):
    print("MQTT connected...")

    if local:
        client.subscribe(l_mqtt_topic, 0)

def on_glow_connect(client, obj, flags, rc):
    print("Connected to Glow MQTT broker...")
    client.subscribe(s_mqtt_topic, 0)

def process_msg(client, userdata, message):
    try:
        data = json.loads(message.payload)
    except json.JSONDecodeError:
        return

    if debug:
        print(data)

    if homeassistant:
        HASS_CONFIGURATOR.process_data(data)

    status = GLOW_PROCESSOR.process_data(data)

    print(status)

    mqttc.publish(p_mqtt_topic, json.dumps(status), retain=True)

try:
    # Initialise processor
    GLOW_PROCESSOR = GlowProcessor(cache, local)

    # Create MQTT client
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = process_msg
    mqttc.username_pw_set(mqtt_username,mqtt_password)
    mqttc.connect(mqtt_address, mqtt_port, 60)

    # Home Assistant
    HASS_CONFIGURATOR = None
    if homeassistant:
        HASS_CONFIGURATOR = HassConfigurator(mqttc, device_id, p_mqtt_topic, local)

    if not local:
        # Create Glow MQTT client
        mqttg = mqtt.Client()
        mqttg.on_connect = on_glow_connect
        mqttg.on_message = process_msg
        mqttg.username_pw_set(username,password)
        mqttg.connect("glowmqtt.energyhive.com", 1883, 60)
        mqttc.loop_start()
        mqttg.loop_forever()
    else:
        mqttc.loop_forever()
except KeyboardInterrupt:
    print("...Exiting")

sys.exit()

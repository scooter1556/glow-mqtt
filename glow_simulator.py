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
import os
from pathlib import Path
import sys
import time

import paho.mqtt.client as mqtt

parser = argparse.ArgumentParser(description='Glow MQTT Simulator')
parser.add_argument('--mqtt_address', required=False, default='localhost',  help='MQTT broker address default: localhost')
parser.add_argument('--mqtt_port', required=False, type=int, default=1883, help='MQTT port default: 1883')
parser.add_argument('--mqtt_username', required=False, default='', help='MQTT username')
parser.add_argument('--mqtt_password', required=False, default='', help='MQTT password')
parser.add_argument('--local', default=False, action='store_true', help='Use local MQTT mode')
parser.add_argument('--interval', required=False, type=int, default=10, help='Publishing interval in seconds default: 10')
args = vars(parser.parse_args())

mqtt_address = args['mqtt_address']
mqtt_port = int(args['mqtt_port'])
mqtt_username = args['mqtt_username']
mqtt_password = args['mqtt_password']
local = args.get('local')
interval = int(args['interval'])

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))

def on_connect(client, obj, flags, rc):
    print("MQTT connected...")

def publish_payloads():
    if local:
        data_path = Path(os.path.join(ROOT_DIR, 'test', 'local_data.json'))
    else:
        data_path = Path(os.path.join(ROOT_DIR, 'test', 'data.json'))

    with data_path.open('r') as f:
        data = json.load(f)

    while True:
        if mqttc.is_connected():
            for i in data['payloads']:
                topic = i['topic']
                payload = i['payload']
                print(i)

                mqttc.publish(topic, json.dumps(payload), retain=True)

                time.sleep(interval)

try:
    # Create MQTT client
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.username_pw_set(mqtt_username,mqtt_password)
    mqttc.connect(mqtt_address, mqtt_port, 60)
    mqttc.loop_start()

    publish_payloads()
except KeyboardInterrupt:
    print("...Exiting")

sys.exit()

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

from hass_configurator import HassConfigurator

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
homeassistant = args.get('homeassistant')
debug = args.get('debug')

s_mqtt_topic = "SMART/" + provider + "/" + device_id
p_mqtt_topic = topic + "/" + device_id
l_mqtt_topic = p_mqtt_topic + "/" + "SENSOR" + "/" + "#"

def twos_complement(hexstr):
    value = int(hexstr,16)
    bits = len(hexstr) * 4
    
    if value & (1 << (bits-1)):
        value -= 1 << bits
        
    return value

def on_connect(client, obj, flags, rc):
    print("MQTT connected...")

    if local:
        client.subscribe(l_mqtt_topic, 0)

def on_glow_connect(client, obj, flags, rc):
    print("Connected to Glow MQTT broker...")
    client.subscribe(s_mqtt_topic, 0)

def process_msg(client, userdata, message):
    status = {}
    
    try:
        data = json.loads(message.payload)
    except json.JSONDecodeError:
        return

    if debug:
        print(data)

    if homeassistant:
        HASS_CONFIGURATOR.process_data(data)

    if 'elecMtr' in data:
        if '0702' in data['elecMtr']:
            if '00' in data['elecMtr']['0702'] and \
               '03' in data['elecMtr']['0702']:
                if '00' in data['elecMtr']['0702']['00'] and \
                   '01' in data['elecMtr']['0702']['03'] and \
                   '02' in data['elecMtr']['0702']['03']:
                    elec_imp = int(data['elecMtr']['0702']['00']['00'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

                    if elec_imp > 0:
                        status["elec_imp"] = elec_imp

                if '01' in data['elecMtr']['0702']['00'] and \
                   '01' in data['elecMtr']['0702']['03'] and \
                   '02' in data['elecMtr']['0702']['03']:
                    elec_exp = int(data['elecMtr']['0702']['00']['01'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

                    if elec_exp > 0:
                        status["elec_exp"] = elec_exp

            if '04' in data['elecMtr']['0702']:
                if '00' in data['elecMtr']['0702']['04']:
                    status["watt_now"] = twos_complement(data['elecMtr']['0702']['04']['00'])
        
    if 'gasMtr' in data:
        if '0702' in data['gasMtr']:
            if '00' in data['gasMtr']['0702'] and \
               '03' in data['gasMtr']['0702']:
                if '00' in data['gasMtr']['0702']['00'] and \
                   '01' in data['gasMtr']['0702']['03'] and \
                   '02' in data['gasMtr']['0702']['03']:
                    gas_mtr = int(data['gasMtr']['0702']['00']['00'],16) * int(data['gasMtr']['0702']['03']['01'],16) / int(data['gasMtr']['0702']['03']['02'],16)

                    if gas_mtr > 0:
                        status["gas_mtr"] = gas_mtr

    print(status)

    mqttc.publish(p_mqtt_topic, json.dumps(status), retain=True)

def process_local_msg(client, userdata, message):
    status = {}

    try:
        data = json.loads(message.payload)
    except json.JSONDecodeError:
        return

    if debug:
        print(data)

    if homeassistant:
        HASS_CONFIGURATOR.process_data(data)

    if 'electricitymeter' in data:
        if 'energy' in data['electricitymeter']:
            if 'export' in data['electricitymeter']['energy']:
                if 'cumulative' in data['electricitymeter']['energy']['export']:
                    elec_exp = data['electricitymeter']['energy']['export']['cumulative']

                    if elec_exp > 0:
                        status["elec_exp"] = elec_exp

            if 'import' in data['electricitymeter']['energy']:
                if 'cumulative' in data['electricitymeter']['energy']['import']:
                    elec_imp = data['electricitymeter']['energy']['import']['cumulative']

                    if elec_imp > 0:
                        status["elec_imp"] = elec_imp

        if 'power' in data['electricitymeter']:
            if 'value' in data['electricitymeter']['power']:
                status["watt_now"] = int(data['electricitymeter']['power']['value'] * 1000)

    if 'gasmeter' in data:
        if 'energy' in data['gasmeter']:
            if 'import' in data['gasmeter']['energy']:
                if 'cumulative' in data['gasmeter']['energy']['import']:
                    gas_mtr = data['gasmeter']['energy']['import']['cumulative']

                    if gas_mtr > 0:
                        status["gas_mtr"] = gas_mtr

    print(status)

    mqttc.publish(p_mqtt_topic, json.dumps(status), retain=True)

try:
    # Create MQTT client
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = process_local_msg
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

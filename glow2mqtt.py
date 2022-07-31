#!/usr/bin/python

import paho.mqtt.client as mqtt
import argparse
import sys
import json

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
    except JSONDecodeError:
        return

    if debug:
        print(data)

    if 'elecMtr' in data:
        if '00' in data['elecMtr']['0702']['00']:
            status["elec_imp"] = int(data['elecMtr']['0702']['00']['00'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

        if '00' in data['elecMtr']['0702']['04']:
            status["watt_now"] = twos_complement(data['elecMtr']['0702']['04']['00'])

        if '01' in data['elecMtr']['0702']['00']:
            status["elec_exp"] = int(data['elecMtr']['0702']['00']['01'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)
        
    if 'gasMtr' in data:
        if '00' in data['gasMtr']['0702']['00']:
            status["gas_mtr"] = int(data['gasMtr']['0702']['00']['00'],16) * int(data['gasMtr']['0702']['03']['01'],16) / int(data['gasMtr']['0702']['03']['02'],16)

    print(status)

    mqttc.publish(p_mqtt_topic, json.dumps(status), retain=True)

def process_local_msg(client, userdata, message):
    status = {}

    try:
        data = json.loads(message.payload)
    except JSONDecodeError:
        return

    if debug:
        print(data)

    if 'electricitymeter' in data:
        if 'energy' in data['electricitymeter']:
            if 'export' in data['electricitymeter']['energy']:
                status["elec_exp"] = data['electricitymeter']['energy']['export']['cumulative']

            if 'import' in data['electricitymeter']['energy']:
                status["elec_imp"] = data['electricitymeter']['energy']['import']['cumulative']

        if 'power' in data['electricitymeter']:
            status["watt_now"] = int(data['electricitymeter']['power']['value'] * 1000)

    if 'gasmeter' in data:
        if 'energy' in data['gasmeter']:
            if 'import' in data['gasmeter']['energy']:
                status["gas_mtr"] = data['gasmeter']['energy']['import']['cumulative']

    print(status)

    mqttc.publish(p_mqtt_topic, json.dumps(status), retain=True)

# Create MQTT client
mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = process_local_msg
mqttc.username_pw_set(mqtt_username,mqtt_password)
mqttc.connect(mqtt_address, mqtt_port, 60)

# Home Assistant
if homeassistant:
    print("Configuring Home Assistant...")

    discovery_msgs = []

    # Current power in watts
    watt_now_topic = "homeassistant/sensor/glow_" + device_id + "/watt_now/config"
    watt_now_payload = {"device_class": "power", "state_class": "measurement", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_watt_now", "name": "glow_" + device_id + "_current_power", "state_topic": p_mqtt_topic, "unit_of_measurement": "W", "value_template": "{{ value_json.watt_now}}" }
    mqttc.publish(watt_now_topic, json.dumps(watt_now_payload), retain=True)

    # Electricity import total kWH
    elec_imp_topic = "homeassistant/sensor/glow_" + device_id + "/elec_imp/config"
    elec_imp_payload = {"device_class": "energy", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_elec_imp", "name": "glow_" + device_id + "_electric_import", "state_topic": p_mqtt_topic, "unit_of_measurement": "kWh", "value_template": "{{ value_json.elec_imp}}"}
    mqttc.publish(elec_imp_topic, json.dumps(elec_imp_payload), retain=True)

    # Electricity export total kWH
    elec_exp_topic = "homeassistant/sensor/glow_" + device_id + "/elec_exp/config"
    elec_exp_payload = {"device_class": "energy", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_elec_exp", "name": "glow_" + device_id + "_electric_export", "state_topic": p_mqtt_topic, "unit_of_measurement": "kWh", "value_template": "{{ value_json.elec_exp}}"}
    mqttc.publish(elec_exp_topic, json.dumps(elec_exp_payload), retain=True)

    # Gas total
    gas_unit = "kWh" if local else "m³"
    gas_mtr_topic = "homeassistant/sensor/glow_" + device_id + "/gas_mtr/config"
    gas_mtr_payload = {"device_class": "gas", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_gas_mtr", "name": "glow_" + device_id + "_gas_meter", "state_topic": p_mqtt_topic, "unit_of_measurement": gas_unit, "value_template": "{{ value_json.gas_mtr}}"}
    mqttc.publish(gas_mtr_topic, json.dumps(gas_mtr_payload), retain=True)

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


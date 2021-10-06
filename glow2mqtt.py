#!/usr/bin/python

import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
import sys
import configparser
import getopt
import json

config_file = "config.ini"

def twos_complement(hexstr):
    value = int(hexstr,16)
    bits = len(hexstr) * 4
    
    if value & (1 << (bits-1)):
        value -= 1 << bits
        
    return value

def main(argv):
    # Get command-line arguments
    try:
      opts, args = getopt.getopt(argv,"hc:",["config="])
    except getopt.GetoptError:
        print('glow2mqtt.py -c <configfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('glow2mqtt.py -c <configfile>')
            sys.exit()

        elif opt in ("-c", "--config"):
            config_file = arg

    # Read config file
    config = configparser.ConfigParser()
    config.read_file(open(config_file))

    # Variables
    device_id = config.get('DEFAULT', 'glow_device_id')
    username = config.get('DEFAULT', 'glow_username')
    password = config.get('DEFAULT', 'glow_password')
    mqtt_server = config.get('MQTT', 'mqtt_server', fallback='localhost')
    mqtt_port = config.getint('MQTT', 'mqtt_port', fallback=1883)
    homeassistant = config.getboolean('MQTT', 'homeassistant', fallback=False)
    debug = config.getboolean('MISC', 'debug', fallback=False)
    
    s_mqtt_topic = "SMART/HILD/" + device_id
    p_mqtt_topic = "glow" + "/" + device_id

    # Home Assistant
    if (homeassistant):
        print("Configuring Home Assistant...")

        discovery_msgs = []

        # Current power in watts
        watt_now_topic = "homeassistant/sensor/glow_" + device_id + "/watt_now/config"
        watt_now_payload = {"device_class": "power", "state_class": "measurement", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_watt_now", "name": "glow_" + device_id + "_current_power", "state_topic": p_mqtt_topic, "unit_of_measurement": "W", "value_template": "{{ value_json.watt_now}}" }
        discovery_msgs.append({ 'topic': watt_now_topic, 'payload': json.dumps(watt_now_payload), 'retain': True })

        # Electricity import total kWH
        elec_imp_topic = "homeassistant/sensor/glow_" + device_id + "/elec_imp/config"
        elec_imp_payload = {"device_class": "energy", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_elec_imp", "name": "glow_" + device_id + "_electric_import", "state_topic": p_mqtt_topic, "unit_of_measurement": "kWh", "value_template": "{{ value_json.elec_imp}}"}
        discovery_msgs.append({ 'topic': elec_imp_topic, 'payload': json.dumps(elec_imp_payload), 'retain': True })

        # Electricity export total kWH
        elec_exp_topic = "homeassistant/sensor/glow_" + device_id + "/elec_exp/config"
        elec_exp_payload = {"device_class": "energy", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_elec_exp", "name": "glow_" + device_id + "_electric_export", "state_topic": p_mqtt_topic, "unit_of_measurement": "kWh", "value_template": "{{ value_json.elec_exp}}"}
        discovery_msgs.append({ 'topic': elec_exp_topic, 'payload': json.dumps(elec_exp_payload), 'retain': True })

        # Gas total m³
        gas_mtr_topic = "homeassistant/sensor/glow_" + device_id + "/gas_mtr/config"
        gas_mtr_payload = {"device_class": "gas", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + device_id], "manufacturer": "Glow", "name": device_id}, "unique_id": "glow_" + device_id + "_gas_mtr", "name": "glow_" + device_id + "_gas_meter", "state_topic": p_mqtt_topic, "unit_of_measurement": "m³", "value_template": "{{ value_json.gas_mtr}}"}
        discovery_msgs.append({ 'topic': gas_mtr_topic, 'payload': json.dumps(gas_mtr_payload), 'retain': True })

        publish.multiple(discovery_msgs, hostname=mqtt_server, port=mqtt_port, auth=None)

    def process_msg(client, userdata, message):
        status = {}
        
        data = json.loads(message.payload)

        if(debug):
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

        publish.single(p_mqtt_topic, json.dumps(status), hostname=mqtt_server, port=mqtt_port, auth=None, retain=True)

    subscribe.callback(process_msg, s_mqtt_topic, hostname="glowmqtt.energyhive.com", auth={'username':username, 'password':password})

if __name__ == "__main__":
   main(sys.argv[1:])

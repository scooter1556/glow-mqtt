#
# Copyright (c) 2023 Scott Ware
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

import json

class HassConfigurator():
    def __init__(self,
                 client,
                 device_id,
                 topic,
                 local):
        self.client = client
        self.device_id = device_id
        self.topic = topic
        self.local = local

        # Global Flags
        self.electric_import = False
        self.electric_export = False
        self.gas_meter = False

    def process_data(self, data):
        electric_import = False
        electric_export = False
        electric_units = "kWh"
        gas_meter = False
        gas_units = "kWh"
        gas_class = "energy"

        if self.local:
            if 'electricitymeter' in data:
                if 'energy' in data['electricitymeter']:
                    if not self.electric_export and 'export' in data['electricitymeter']['energy']:
                        if 'cumulative' in data['electricitymeter']['energy']['export']:
                            elec_exp = data['electricitymeter']['energy']['export']['cumulative']

                            if elec_exp > 0:
                                electric_export = True

                    if not self.electric_import and 'import' in data['electricitymeter']['energy']:
                        if 'cumulative' in data['electricitymeter']['energy']['import']:
                            elec_imp = data['electricitymeter']['energy']['import']['cumulative']

                            if elec_imp > 0:
                                electric_import = True

            if 'gasmeter' in data:
                if 'energy' in data['gasmeter']:
                    if not self.gas_meter and 'import' in data['gasmeter']['energy']:
                        if 'cumulative' in data['gasmeter']['energy']['import']:
                            gas_mtr = data['gasmeter']['energy']['import']['cumulative']

                            if gas_mtr > 0:
                                gas_meter = True
                                gas_units = data['gasmeter']['energy']['import']['units']

                                if gas_units == "kWh":
                                    gas_class = "energy"
                                else:
                                    gas_class = "gas"
        else:
            if 'elecMtr' in data:
                if '0702' in data['elecMtr']:
                    if not self.electric_import and \
                    '00' in data['elecMtr']['0702'] and \
                    '03' in data['elecMtr']['0702']:
                        if '00' in data['elecMtr']['0702']['00'] and \
                        '01' in data['elecMtr']['0702']['03'] and \
                        '02' in data['elecMtr']['0702']['03']:
                            elec_imp = int(data['elecMtr']['0702']['00']['00'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

                            if elec_imp > 0:
                                electric_import = True

                        if not self.electric_export and \
                        '01' in data['elecMtr']['0702']['00'] and \
                        '01' in data['elecMtr']['0702']['03'] and \
                        '02' in data['elecMtr']['0702']['03']:
                            elec_exp = int(data['elecMtr']['0702']['00']['01'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

                            if elec_exp > 0:
                                electric_export = True

            if 'gasMtr' in data:
                if '0702' in data['gasMtr']:
                    if '00' in data['gasMtr']['0702'] and \
                    '03' in data['gasMtr']['0702']:
                        if not self.gas_meter and \
                        '00' in data['gasMtr']['0702']['00'] and \
                        '00' in data['gasMtr']['0702']['03'] and \
                        '01' in data['gasMtr']['0702']['03'] and \
                        '02' in data['gasMtr']['0702']['03']:
                            gas_mtr = int(data['gasMtr']['0702']['00']['00'],16) * int(data['gasMtr']['0702']['03']['01'],16) / int(data['gasMtr']['0702']['03']['02'],16)

                            if gas_mtr > 0:
                                gas_meter = True

                                if int(data["gasMtr"]["0702"]["03"]["00"], 16) == 0:
                                    gas_units = "kWh"
                                    gas_class = "energy"
                                elif int(data["gasMtr"]["0702"]["03"]["00"], 16) == 1:
                                    gas_units = "m³"
                                    gas_class = "gas"

        if electric_import:
            # Electricity import total
            elec_imp_topic = "homeassistant/sensor/glow_" + self.device_id + "/elec_imp/config"
            elec_imp_payload = {"device_class": "energy", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + self.device_id], "manufacturer": "Glow", "name": self.device_id}, "unique_id": "glow_" + self.device_id + "_elec_imp", "name": "glow_" + self.device_id + "_electric_import", "state_topic": self.topic, "unit_of_measurement": electric_units, "value_template": "{{ value_json.elec_imp}}"}
            self.client.publish(elec_imp_topic, json.dumps(elec_imp_payload), retain=True)

            self.electric_import = True

        if electric_export:
            # Electricity export total
            elec_exp_topic = "homeassistant/sensor/glow_" + self.device_id + "/elec_exp/config"
            elec_exp_payload = {"device_class": "energy", "state_class": "total_increasing", "device": {"identifiers": ["glow_" + self.device_id], "manufacturer": "Glow", "name": self.device_id}, "unique_id": "glow_" + self.device_id + "_elec_exp", "name": "glow_" + self.device_id + "_electric_export", "state_topic": self.topic, "unit_of_measurement": electric_units, "value_template": "{{ value_json.elec_exp}}"}
            self.client.publish(elec_exp_topic, json.dumps(elec_exp_payload), retain=True)

            self.electric_export = True
        
        if electric_import or electric_export:
            # Current power
            watt_now_topic = "homeassistant/sensor/glow_" + self.device_id + "/watt_now/config"
            watt_now_payload = {"device_class": "power", "state_class": "measurement", "device": {"identifiers": ["glow_" + self.device_id], "manufacturer": "Glow", "name": self.device_id}, "unique_id": "glow_" + self.device_id + "_watt_now", "name": "glow_" + self.device_id + "_current_power", "state_topic": self.topic, "unit_of_measurement": "W", "value_template": "{{ value_json.watt_now}}" }
            self.client.publish(watt_now_topic, json.dumps(watt_now_payload), retain=True)

        if gas_meter:
            # Gas total
            gas_mtr_topic = "homeassistant/sensor/glow_" + self.device_id + "/gas_mtr/config"
            gas_mtr_payload = {"device_class": gas_class, "state_class": "total_increasing", "device": {"identifiers": ["glow_" + self.device_id], "manufacturer": "Glow", "name": self.device_id}, "unique_id": "glow_" + self.device_id + "_gas_mtr", "name": "glow_" + self.device_id + "_gas_meter", "state_topic": self.topic, "unit_of_measurement": gas_units, "value_template": "{{ value_json.gas_mtr}}"}
            self.client.publish(gas_mtr_topic, json.dumps(gas_mtr_payload), retain=True)

            self.gas_meter = True
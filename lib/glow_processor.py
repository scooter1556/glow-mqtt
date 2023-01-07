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

from . import utils

class GlowProcessor():
    def __init__(self,
                 cache,
                 local):
        self.cache = cache
        self.local = local

        # Cache
        self.elec_imp = None
        self.elec_exp = None
        self.watt_now = None
        self.gas_mtr = None

    def process_data(self, data):
        status = {}

        if self.local:
            if 'electricitymeter' in data:
                if 'energy' in data['electricitymeter']:
                    if 'export' in data['electricitymeter']['energy']:
                        if 'cumulative' in data['electricitymeter']['energy']['export']:
                            elec_exp = data['electricitymeter']['energy']['export']['cumulative']

                            if elec_exp > 0:
                                if self.cache:
                                    self.elec_exp = elec_exp
                                else:
                                    status["elec_exp"] = elec_exp

                    if 'import' in data['electricitymeter']['energy']:
                        if 'cumulative' in data['electricitymeter']['energy']['import']:
                            elec_imp = data['electricitymeter']['energy']['import']['cumulative']

                            if elec_imp > 0:
                                if self.cache:
                                    self.elec_imp = elec_imp
                                else:
                                    status["elec_imp"] = elec_imp

                if 'power' in data['electricitymeter']:
                    if 'value' in data['electricitymeter']['power']:
                        watt_now = int(data['electricitymeter']['power']['value'] * 1000)

                        if self.cache:
                            self.watt_now = watt_now
                        else:
                            status["watt_now"] = watt_now

            if 'gasmeter' in data:
                if 'energy' in data['gasmeter']:
                    if 'import' in data['gasmeter']['energy']:
                        if 'cumulative' in data['gasmeter']['energy']['import']:
                            gas_mtr = data['gasmeter']['energy']['import']['cumulative']

                            if gas_mtr > 0:
                                if self.cache:
                                    self.gas_mtr = gas_mtr
                                else:
                                    status["gas_mtr"] = gas_mtr
        
        else:
            if 'elecMtr' in data:
                if '0702' in data['elecMtr']:
                    if '00' in data['elecMtr']['0702'] and \
                    '03' in data['elecMtr']['0702']:
                        if '00' in data['elecMtr']['0702']['00'] and \
                        '01' in data['elecMtr']['0702']['03'] and \
                        '02' in data['elecMtr']['0702']['03']:
                            elec_imp = int(data['elecMtr']['0702']['00']['00'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

                            if elec_imp > 0:
                                if self.cache:
                                    self.elec_imp = elec_imp
                                else:
                                    status["elec_imp"] = elec_imp

                        if '01' in data['elecMtr']['0702']['00'] and \
                        '01' in data['elecMtr']['0702']['03'] and \
                        '02' in data['elecMtr']['0702']['03']:
                            elec_exp = int(data['elecMtr']['0702']['00']['01'],16) * int(data['elecMtr']['0702']['03']['01'],16) / int(data['elecMtr']['0702']['03']['02'],16)

                            if elec_exp > 0:
                                if self.cache:
                                    self.elec_exp = elec_exp
                                else:
                                    status["elec_exp"] = elec_exp

                    if '04' in data['elecMtr']['0702']:
                        if '00' in data['elecMtr']['0702']['04']:
                            watt_now = utils.twos_complement(data['elecMtr']['0702']['04']['00'])

                            if self.cache:
                                self.watt_now = watt_now
                            else:
                                status["watt_now"] = watt_now
                
            if 'gasMtr' in data:
                if '0702' in data['gasMtr']:
                    if '00' in data['gasMtr']['0702'] and \
                    '03' in data['gasMtr']['0702']:
                        if '00' in data['gasMtr']['0702']['00'] and \
                        '01' in data['gasMtr']['0702']['03'] and \
                        '02' in data['gasMtr']['0702']['03']:
                            gas_mtr = int(data['gasMtr']['0702']['00']['00'],16) * int(data['gasMtr']['0702']['03']['01'],16) / int(data['gasMtr']['0702']['03']['02'],16)

                            if gas_mtr > 0:
                                if self.cache:
                                    self.gas_mtr = gas_mtr
                                else:
                                    status["gas_mtr"] = gas_mtr

        if self.cache:
            if self.elec_imp is not None:
                status["elec_imp"] = self.elec_imp

            if self.elec_exp is not None:
                status["elec_exp"] = self.elec_exp

            if self.watt_now is not None:
                status["watt_now"] = self.watt_now

            if self.gas_mtr is not None:
                status["gas_mtr"] = self.gas_mtr

        return status
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

from lib.glow_processor import GlowProcessor

parser = argparse.ArgumentParser(description='Glow Data Test')
parser.add_argument('--local', default=False, action='store_true', help='Use local data')
parser.add_argument('--cache', default=False, action='store_true', help='Use data caching')
args = vars(parser.parse_args())

local = args.get('local')
cache = args.get('cache')

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))

def parse_payloads():    
    if local:
        data_path = Path(os.path.join(ROOT_DIR, 'test', 'local_data.json'))
    else:
        data_path = Path(os.path.join(ROOT_DIR, 'test', 'data.json'))
    
    with data_path.open('r') as f:
        data = json.load(f)

    for i in data['payloads']:
        payload = i['payload']

        status = GLOW_PROCESSOR.process_data(payload)

        print(status)

try:
    # Initialise processor
    GLOW_PROCESSOR = GlowProcessor(cache, local)

    parse_payloads()
except KeyboardInterrupt:
    print("...Exiting")

sys.exit()

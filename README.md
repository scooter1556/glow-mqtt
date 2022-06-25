# Glow to MQTT
Bridge Glow MQTT broker with your own local MQTT broker
Home Assistant auto-discovery supported


# Usage

## Native

    python3 ./glow2mqtt.py --glow_device GLOW_DEVICE --glow_username GLOW_USERNAME --glow_password GLOW_PASSWORD [--glow_provider GLOW_PROVIDER] [--mqtt_address MQTT_ADDRESS] [--mqtt_port MQTT_PORT] [--mqtt_username MQTT_USERNAME] [--mqtt_password MQTT_PASSWORD] [--homeassistant] [--debug]

## Docker

    docker run scootsoftware/glow2mqtt --glow_device GLOW_DEVICE --glow_username GLOW_USERNAME --glow_password GLOW_PASSWORD [--glow_provider GLOW_PROVIDER] [--mqtt_address MQTT_ADDRESS] [--mqtt_port MQTT_PORT] [--mqtt_username MQTT_USERNAME] [--mqtt_password MQTT_PASSWORD] [--homeassistant] [--debug]

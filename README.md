# Glow to MQTT
Bridge Glow MQTT broker with your own local MQTT broker
Home Assistant auto-discovery supported


# Usage
First rename the 'config.ini.template' file and update with your details.

## Native

    python3 ./glow2mqtt.py --config config.ini

## Docker
Your modified 'config.ini' file needs to be available inside the container in the '/config' directory.

    docker run --rm  -v $(PWD):/config scootsoftware/glow2mqtt

## Docker Compose
Your modified 'config.ini' file needs to be available inside the container in the '/config' directory. In the below example the '/etc/glow' directory on the host is used.

    version: "3"
    services:
      glow2mqtt:
        image: scootsoftware/glow2mqtt
        container_name: glow2mqtt
        environment:
          - PYTHONUNBUFFERED=1
        volumes:
          - /etc/glow:/config
        network_mode: host
        restart: unless-stopped

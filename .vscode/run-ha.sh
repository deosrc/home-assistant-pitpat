#!/bin/bash

mkdir .data
chown -R 1000:1000 .data

touch .data/scripts.yaml
touch .data/automations.yaml
touch .data/groups.yaml
touch .data/scenes.yaml

docker run --rm \
    -p 8123:8123 \
    -p 5678:5678 \
    -v $(pwd)/.data:/config:rw \
    -v $(pwd)/debug_configuration.yaml:/config/configuration.yaml:ro \
    -v $(pwd)/custom_components:/config/custom_components:ro \
    --user 1000:1000 \
    --name homeassistant \
    homeassistant/home-assistant:2026.1.3

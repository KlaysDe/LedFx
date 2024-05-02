import json
import logging
import socket

import paho.mqtt.client as mqtt
import voluptuous as vol

from ledfx.color import parse_color
from ledfx.config import save_config
from ledfx.consts import PROJECT_VERSION
from ledfx.effects.audio import AudioInputSource
from ledfx.events import Event
from ledfx.integrations import Integration

_LOGGER = logging.getLogger(__name__)

class MQTT_V2(Integration):
    
    NAME = "MQTT Remote Control"
    DESCRIPTION = "MQTT Integration for LedFX, supporting Homeassistant Autodiscovery"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "name",
                description="Name of this HomeAssistant instance",
                default="Home Assistant",
            ): str,
            vol.Required(
                "topic",
                description="HomeAssistant's discovery prefix",
                default="homeassistant",
            ): str,
            vol.Required(
                "mqtt_host",
                description="MQTT Server Host",
                default="127.0.0.1",
            ): str,
            vol.Required(
                "port", description="MQTT port", default=1883
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Optional(
                "username",
                description="MQTT username",
                default="",
            ): str,
            vol.Optional(
                "password",
                description="MQTT password",
                default="",
            ): str,
            vol.Optional(
                "description",
                description="Internal Description",
                default="MQTT Integration with auto-discovery",
            ): str,
        }
    )
    
    def __init__(self, ledfx, config, active, data):
        super().__init__(ledfx, config, active, data)
        
        
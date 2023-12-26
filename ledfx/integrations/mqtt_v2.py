import logging
import voluptuous as vol
import json

from ledfx.integrations import Integration
from ledfx.core import LedFxCore
from ledfx.devices import Device
from ledfx.virtuals import Virtual

from ledfx.events import Event
from ledfx.events import DeviceCreatedEvent,DeviceUpdateEvent,DeviceDeleteEvent,EffectSetEvent,EffectClearedEvent

from .klays_hass_mqtt import HassClient
from .klays_hass_mqtt.hass_device import HaDevice
from .klays_hass_mqtt.entities.entity_switch import HaSwitch

_LOGGER = logging.getLogger(__name__)

KEY_HA_DEVICE = 'ha_device'
KEY_HA_ENTITIES = 'ha_entities'
KEY_HA_ENTITY_ACTIVE = 'ha_ent_active'

class HaDeviceDefinition:
    Device: HaDevice = None
    EntityActive: HaSwitch = None
    
    def __get_entity_id(self, entity):
        return f'{self.id_base}_{entity}'
    
    def __init__(self, client:HassClient, device_id:str, id_base:str) -> None:
        self.id_base = id_base
        self.Device = HaDevice(client, 'LedFX '+device_id, 'LedFX', id_base)
        self.EntityActive = HaSwitch(client, self.Device, "Active", self.__get_entity_id("active"), False)
        pass
    
    def destroy_ha_device(self):
        self.EntityActive.deleteEntity()
        pass

class MQTT_V2(Integration):
    """MQTT Integration"""

    NAME = "MQTT-V2"
    DESCRIPTION = "MQTT and HA Auto Discovery Integration"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "name",
                description="Name of this HomeAssistant instance",
                default="Home Assistant",
            ): str,
            vol.Required(
                "discovery_topic",
                description="HomeAssistant's discovery prefix",
                default="homeassistant",
            ): str,
            vol.Required(
                "discovery_enabled",
                description="Enable HomeAssistant's auto discovery feature",
                default=True,
            ): bool,
            vol.Required(
                "mqtt_host",
                description="MQTT Server Hostname",
                default="localhost",
            ): str,
            vol.Required(
                "mqtt_port", description="MQTT Server port", default=1883
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Optional(
                "mqtt_user",
                description="MQTT Username",
                default="",
            ): str,
            vol.Optional(
                "mqtt_passwd",
                description="MQTT Password",
                default="",
            ): str,
            vol.Optional(
                "mqtt_data_topic",
                description="Base topic for states and data",
                default="",
            ): str
        }
    )

    def __init__(self, ledfx, config, active, data):
        super().__init__(ledfx, config, active, data)

        self._ledfx : LedFxCore = ledfx
        self._config = config
        self._client : HassClient = None
        self._data = []
        self._listeners = []
        self._haDevices : [str, HaDeviceDefinition] = {}
        self.__prepare_ledfx_listeners()
        _LOGGER.info(f"CONFIG: {self._config}")
        
    async def connect(self):        
        host, port, user, passwd, base_topic = [self._config[f] for f in ["mqtt_host", "mqtt_port", "mqtt_user", "mqtt_passwd", "mqtt_data_topic"]]
        
        self._client = HassClient(host, port, user, passwd, state_topic_base=base_topic)
        
        self.__create_existing_devices_in_ha()
        
    def __create_existing_devices_in_ha(self):
        #for device_id in self._ledfx.devices:
        #    self.__ha_create_new_device(device_id)
        for virtual_id in self._ledfx.virtuals:
            self.__ha_create_new_device(virtual_id)
            
    def __create_unique_id(self, device_id):
        return f'ledfx{self._ledfx.host}_{device_id}'
            
    def __ha_create_new_device(self, device_id):
        virtual : Virtual = self._ledfx.virtuals.get(device_id)
        if not device_id in self._haDevices:
            definition = HaDeviceDefinition(self._client, device_id, self.__create_unique_id(device_id))
            self._haDevices[device_id] = definition
            definition.EntityActive.setCallback(self.__ha_cb_active_changed, device_id)
            definition.EntityActive.publishState(virtual.active_effect == True)
            
        pass

    def __ha_cb_active_changed(self, value, device_id):
        if not value:
            device : Virtual = self._ledfx.virtuals.get(device_id)
            if device:
                device.clear_effect()
        pass

    def __get_ha_device(self, device_id) -> HaDeviceDefinition:
        if device_id in self._haDevices:
            return self._haDevices[device_id]
        return None

    def __ledfx_evt_device_created(self, event:DeviceCreatedEvent):
        self.__ha_create_new_device(event.device_id)
    
    def __ledfx_evt_device_update(self, event:DeviceUpdateEvent):
        pass
    
    def __ledfx_evt_device_deleted(self, event:DeviceDeleteEvent):
        dev = self.__get_ha_device(event.device_id)
        if dev:
            dev.destroy_ha_device()
            
    def __ledfx_evt_effect_set(self, event:EffectSetEvent):
        dev = self.__get_ha_device(event.virtual_id)
        if dev:
            dev.EntityActive.publishState(True)
        pass
    
    def __ledfx_evt_effect_cleared(self, event:EffectClearedEvent):
        dev = self.__get_ha_device(event.virtual_id)
        if dev:
            dev.EntityActive.publishState(False)
        pass
    
    def __prepare_ledfx_listeners(self):
        events = {
            Event.DEVICE_CREATED: self.__ledfx_evt_device_created,
            Event.DEVICE_UPDATE: self.__ledfx_evt_device_update,
            Event.DEVICE_DELETED: self.__ledfx_evt_device_deleted,
            Event.EFFECT_SET: self.__ledfx_evt_effect_set,
            Event.EFFECT_CLEARED: self.__ledfx_evt_effect_cleared
        }
        
        for evt, cb in events.items():
            self._listeners.append(
                self._ledfx.events.add_listener(cb, evt)
            )
        pass
    
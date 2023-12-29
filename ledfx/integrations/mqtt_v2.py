import logging
import voluptuous as vol
import json

from ledfx.integrations import Integration
from ledfx.core import LedFxCore
from ledfx.devices import Device
from ledfx.integrations.klays_hass_mqtt.entities.entity_select import HaSelect
from ledfx.virtuals import Virtual

from ledfx.events import Event, SceneActivatedEvent, SceneCreatedEvent, SceneDeactivatedEvent, SceneDeletedEvent, SceneUpdatedEvent
from ledfx.events import DeviceCreatedEvent,DeviceUpdateEvent,DeviceDeleteEvent,EffectSetEvent,EffectClearedEvent

from .klays_hass_mqtt import HassClient
from .klays_hass_mqtt.hass_device import HaDevice
from .klays_hass_mqtt.entities.entity_switch import HaSwitch

_LOGGER = logging.getLogger(__name__)

KEY_HA_DEVICE = 'ha_device'
KEY_HA_ENTITIES = 'ha_entities'
KEY_HA_ENTITY_ACTIVE = 'ha_ent_active'

HA_SCENE_NAME_ALL_OFF = '__ALL_OFF__'

class HaDeviceDefinition:
    _device: HaDevice = None
    _entity_active: HaSwitch = None
    
    def __init__(self, client:HassClient, device_id:str) -> None:
        self._device = HaDevice(client, 'LedFX '+device_id, 'LedFX')
        self._entity_active = HaSwitch(client, self._device, "Active", False)
        pass
    
    def destroy_ha_device(self):
        self._entity_active.deleteEntity()
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
            #vol.Required(
            #    "discovery_enabled",
            #    description="Enable HomeAssistant's auto discovery feature",
            #    default=True,
            #): bool,
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
        self._ha_devices : [str, HaDeviceDefinition] = {}
        self._known_scenes = [HA_SCENE_NAME_ALL_OFF]
        self.__prepare_ledfx_listeners()
        _LOGGER.info(f"CONFIG: {self._config}")
        
    async def connect(self):        
        if not self._client:
            host, port, user, passwd, base_topic = [self._config[f] for f in ["mqtt_host", "mqtt_port", "mqtt_user", "mqtt_passwd", "mqtt_data_topic"]]
            
            def connect_callback():
                self.__hass_client_connect_cb()
                
            self._client = HassClient(host, port, user, passwd, state_topic_base=base_topic, connect_callback=connect_callback)
            self._ledfxDev = HaDevice(self._client, "LedFX", "LedFX Visualizer")
            self._sceneSelect = HaSelect(self._client, self._ledfxDev, "Active Scene", self._known_scenes)
            self._sceneSelect.setCallback(self.__ha_cb_scene_changed, None)
            self.__ha_update_scene_select()
        
    def __hass_client_connect_cb(self):
        self.__create_existing_devices_in_ha()
        pass
        
    def __create_existing_devices_in_ha(self):
        for virtual_id in self._ledfx.virtuals:
            self.__ha_create_new_device(virtual_id)
            
    def __ha_create_new_device(self, device_id):
        return
        virtual : Virtual = self._ledfx.virtuals.get(device_id)
        if not device_id in self._ha_devices:
            _LOGGER.info("Created Device: "+device_id)
            definition = HaDeviceDefinition(self._client, device_id)
            self._ha_devices[device_id] = definition
            definition._entity_active.setCallback(self.__ha_cb_dev_active_changed, device_id)
            definition._entity_active.publishState(virtual.active_effect == True)
            
        pass

    def __ha_cb_dev_active_changed(self, value, device_id):
        if not value:
            device : Virtual = self._ledfx.virtuals.get(device_id)
            if device:
                device.clear_effect()
        pass

    def __get_ha_device(self, device_id) -> HaDeviceDefinition:
        if device_id in self._ha_devices:
            return self._ha_devices[device_id]
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
            dev._entity_active.publishState(True)
        pass
    
    def __ledfx_evt_effect_cleared(self, event:EffectClearedEvent):
        dev = self.__get_ha_device(event.virtual_id)
        if dev:
            dev._entity_active.publishState(False)
        pass
    
    def __ha_cb_scene_changed(self, selected_scene, cb_data):
        if selected_scene == HA_SCENE_NAME_ALL_OFF:
            #self._sceneSelect.publishState('')
            #pass
            self._ledfx.scenes.deactivate_all()
        elif selected_scene:
            self._ledfx.scenes.activate(selected_scene)
            
        
        pass
    
    def __ha_update_scene_select(self):
        scenes = self._ledfx.scenes.get_all()
        lastValue = self._sceneSelect.value
        self._known_scenes = [HA_SCENE_NAME_ALL_OFF] + [data['name'] for key, data in scenes.items()]
        if lastValue not in self._known_scenes:
            lastValue = HA_SCENE_NAME_ALL_OFF
        self._sceneSelect.updateOptions(self._known_scenes, lastValue)
        pass
    
    def __led_evt_scene_created(self, event:SceneCreatedEvent):
        self.__ha_update_scene_select()
        pass
    def __led_evt_scene_deleted(self, event:SceneDeletedEvent):
        self.__ha_update_scene_select()
        pass
    def __led_evt_scene_updated(self, event:SceneUpdatedEvent):
        self.__ha_update_scene_select()
        pass
    def __led_evt_scene_activated(self, event:SceneActivatedEvent):
        if event.scene_id in self._known_scenes:
            self._sceneSelect.publishState(event.scene_id)
        else:
            self._sceneSelect.publishState('')
    
    def __led_evt_scene_deactivate(self, event:SceneDeactivatedEvent):
        self._sceneSelect.publishState('')
    
    def __prepare_ledfx_listeners(self):
        events = {
            #Event.DEVICE_CREATED: self.__ledfx_evt_device_created,
            #Event.DEVICE_UPDATE: self.__ledfx_evt_device_update,
            #Event.DEVICE_DELETED: self.__ledfx_evt_device_deleted,
            #Event.EFFECT_SET: self.__ledfx_evt_effect_set,
            #Event.EFFECT_CLEARED: self.__ledfx_evt_effect_cleared,
            Event.SCENE_CREATED: self.__led_evt_scene_created,
            Event.SCENE_ACTIVATED: self.__led_evt_scene_activated,
            Event.SCENE_DELETED: self.__led_evt_scene_deleted,
            Event.SCENE_DEACTIVATED: self.__led_evt_scene_deactivate,
            Event.SCENE_UPDATED: self.__led_evt_scene_updated
        }
        
        for evt, cb in events.items():
            self._listeners.append(
                self._ledfx.events.add_listener(cb, evt)
            )
        pass
    
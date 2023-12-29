import logging

import voluptuous as vol

from ledfx.config import save_config
from ledfx.events import SceneActivatedEvent, SceneCreatedEvent, SceneDeactivatedEvent, SceneDeletedEvent, SceneUpdatedEvent
from ledfx.utils import generate_id

_LOGGER = logging.getLogger(__name__)


class Scenes:
    def __init__(self, ledfx) -> None:
        self._ledfx = ledfx
        self._scenes : dict = self._ledfx.config['scenes']
        self._active_scene = None
        
        def virtuals_validator(virtual_ids):
            return list(
                virtual_id
                for virtual_id in virtual_ids
                if self._ledfx.virtuals.get(virtual_id)
            )
            
        self.SCENE_SCHEMA = vol.Schema(
            {
                vol.Required("name", description="Name of the scene"): str,
                vol.Optional(
                    "scene_image",
                    description="Image or icon to display",
                    default="Wallpaper",
                ): str,
                vol.Optional(
                    "scene_tags",
                    description="Tags for filtering",
                ): str,
                vol.Optional(
                    "scene_puturl",
                    description="On Scene Activate, URL to PUT too",
                ): str,
                vol.Optional(
                    "scene_payload",
                    description="On Scene Activate, send this payload to scene_puturl",
                ): str,
                vol.Optional(
                    "scene_midiactivate",
                    description="On MIDI key/note, Activate a scene",
                ): str,
                vol.Required(
                    "virtuals",
                    description="The effects of these virtuals will be saved",
                ): virtuals_validator,
            }
        )
        pass
    
    def __iter__(self):
        return iter(self._scenes)
    
    def __save(self):
        self._ledfx.config["scenes"] = self._scenes
        save_config(
            config=self._ledfx.config,
            config_dir=self._ledfx.config_dir,
        )
        pass
    
    def values(self):
        return self._scenes.values()
    
    def get_all(self):
        return self._scenes
    
    def get(self, *args):
        return self._scenes.get(*args)
    
    def create(self, scene_config, scene_id=None):
        """Creates a scene of current effects of specified virtuals if no ID given, else updates one with matching id"""
        _LOGGER.info("New Scene Created!")
        scene_config = self.SCENE_SCHEMA(scene_config)
        scene_id = (
            scene_id
            if scene_id in self._scenes
            else generate_id(scene_config["name"])
        )

        virtual_effects = {}
        for virtual in scene_config["virtuals"]:
            effect = {}
            if virtual.active_effect:
                effect["type"] = virtual.active_effect.type
                effect["config"] = virtual.active_effect.config
            virtual_effects[virtual.id] = effect
        scene_config["virtuals"] = virtual_effects

        # Update the scene if it already exists, else create it
        self._scenes[scene_id] = scene_config
        self._ledfx.events.fire_event(SceneCreatedEvent(scene_id))
        self.__save()
        
    def destroy(self, scene_id):
        if scene_id not in self._scenes:
            raise Exception(f'Scene with id {scene_id} not found')
        del self._scenes[scene_id]
        self._ledfx.events.fire_event(SceneDeletedEvent(scene_id))
        self.__save()
    
    def activate(self, scene_id):
        """Activate a scene"""
        scene = self.get(scene_id)
        if not scene:
            _LOGGER.error(f"No scene found with id: {scene_id}")
            return

        for virtual_id in scene["virtuals"]:
            virtual = self._ledfx.virtuals.get(virtual_id)
            if not virtual:
                # virtual has been deleted since scene was created
                # remove from scene?
                continue
            # Set effect of virtual to that saved in the scene,
            # clear active effect of virtual if no effect in scene
            if scene["virtuals"][virtual.id]:
                # Create the effect and add it to the virtual
                effect = self._ledfx.effects.create(
                    ledfx=self._ledfx,
                    type=scene["virtuals"][virtual.id]["type"],
                    config=scene["virtuals"][virtual.id]["config"],
                )
                virtual.set_effect(effect)
            else:
                virtual.clear_effect()
        self._ledfx.events.fire_event(SceneActivatedEvent(scene_id))
        pass
    
    def activate_in(self, scene_id, delay_ms):
        self._ledfx.loop.call_later(
            delay_ms, self.activate, scene_id
        )
    
    def deactivate_all(self):
        for virtual in self._ledfx.virtuals.values():
            virtual.clear_effect()
    
    def deactivate(self, scene_id):
        scene = self.get(scene_id)
        self._ledfx.events.fire_event(SceneDeactivatedEvent(scene_id))
        for virtual in scene:
            virtual.clear_effect()
    
    def rename(self, old_id, new_id):
        scene = self.get(old_id)
        scene['name'] = new_id
        self._ledfx.events.fire_event(SceneUpdatedEvent(new_id, old_id))
        self.__save()
    
    def update(self, scene_id, scene_definition):
        old_scene = self._scenes.get(scene_id)
        if old_scene:
            self._ledfx.events.fire_event(SceneUpdatedEvent(scene_id))
        else:
            self._ledfx.events.fire_event(SceneCreatedEvent(scene_id))
        self._scenes[scene_id] = scene_definition
        self.__save()
        pass
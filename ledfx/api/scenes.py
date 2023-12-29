import logging
from json import JSONDecodeError

from aiohttp import web

from ledfx.api import RestEndpoint
from ledfx.config import save_config
from ledfx.events import SceneActivatedEvent
from ledfx.utils import generate_id

_LOGGER = logging.getLogger(__name__)


class ScenesEndpoint(RestEndpoint):
    """REST end-point for querying and managing scenes"""

    ENDPOINT_PATH = "/api/scenes"

    def __init__(self, ledfx):
        super().__init__(ledfx)
        #["activate", "activate_in", "deactivate", "rename"]:
        self._put_actions = {
            'activate': self.put_action_activate,
            'activate_in': self.put_action_activate_in,
            'deactivate': self.put_action_deactivate,
            'rename': self.put_action_rename
        }
    
    async def wrapped_request(self, method, request) -> web.Response:
        try:
            result = await method()
            if not result:
                response = {"status": "success"}
            elif type(result) == str:
                response = {
                    "status": "success",
                    "payload": {
                        "type": "info",
                        "message": result,
                    },
                }
            else:
                response = result
            return web.json_response(data=response, status=200)
        except Exception as e:
            msg = str(e)
            if type(e) == JSONDecodeError:
                msg = f"JSON Decoding failed: {e}"
            response = {
                "status": "failed",
                "reason": str(e),
            }
            return web.json_response(data=response, status=400)


    async def get(self) -> web.Response:
        """Get all scenes"""
        response = {
            "status": "success",
            "scenes": self._ledfx.scenes.get(),
        }
        return web.json_response(data=response, status=200)

    async def delete(self, request) -> web.Response:
        """Delete a scene"""
        await self.wrapped_request(self.delete_action, request)

    async def delete_action(self, request):
        data = await request.json()
        scene_id = data.get("id", None)
        if not scene_id:
            raise Exception("No Scene id provided")
        self._ledfx.scenes.destroy(scene_id)
        
    async def put(self, request) -> web.Response:
        """Activate a scene"""
        await self.wrapped_request(self.put_action, request)
        
    async def put_action(self, request):
        data = await request.json()
        action = data.get("action")
        if not action:
            raise Exception("No Action provided")
        if action not in self._put_actions:
            raise Exception(f"Action {action} is not supported")
        action_method = self._put_actions[action]
        scene_id = data.get("id")
        if not scene_id:
            raise Exception("No Scene id provided")
        scene = self._ledfx.scenes.get(scene_id)
        await action_method(scene, data)
    
    async def put_action_activate_in(self, scene_id, data):
        ms = data.get("ms")
        if ms == None:
            raise Exception("No delay provided")
        self._ledfx.scenes.activate_in(scene_id, ms)
        return f"Activated scene {scene_id}"
        
    async def put_action_activate(self, scene_id, data):
        self._ledfx.scenes.activate(scene_id)
        return  f"Activated scene {scene_id}"
        
    async def put_action_deactivate(self, scene_id, data):
        self._ledfx.scenes.deactivate(scene_id)
        return f"Deactivated scene {scene_id}"

    async def put_action_rename(self, scene_id, data):
        new_name = data.get("name")
        if not new_name:
            raise Exception("No new name for the scene provided")
        self._ledfx.scenes.rename(scene_id, new_name)
        return f"Renamed scene to {new_name}"    

    async def post(self, request) -> web.Response:
        """Save current effects of virtuals as a scene"""
        self.wrapped_request(self.post_action, request)
        
    async def post_action(self, request):
        data = await request.json()

        copied_keys = {
            "name": {'required': True}, 
            "scene_tags": None, 
            "scene_puturl": None, 
            "scene_payload": None, 
            "scene_midiactivate": None, 
            "scene_image": {'default': 'Wallpaper'}
        }
        
        scene_config = {}
        
        for key, cfg in copied_keys.items():
            if key in data:
                scene_config[key] = data[key]
            elif cfg.get('default'):
                scene_config[key] = cfg['default']
            elif cfg.get('required'):
                raise Exception(f'Parameter {key} needs to be set')

        scene_id = generate_id(scene_config['name'])

        if 'virtuals' not in data:
            for virtual in self._ledfx.virtuals.values():
                effect = {}
                if virtual.active_effect:
                    effect["type"] = virtual.active_effect.type
                    effect["config"] = virtual.active_effect.config
                    # effect['name'] = virtual.active_effect.name
                scene_config["virtuals"][virtual.id] = effect
        else:
            virtuals = data.get("virtuals")
            for vid, vdata in virtuals.items():
                scene_config['virtuals'][vid] = {
                    'type': vdata['type'],
                    'config': vdata['config']
                }
        
        self._ledfx.scenes.update(scene_id, scene_config)
        return {
            "status": "success",
            "scene": {"id": scene_id, "config": scene_config},
        }

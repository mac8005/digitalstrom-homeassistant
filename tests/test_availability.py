import ast
import asyncio
import pathlib
import sys
import types
import unittest
from typing import Self

ROOT = pathlib.Path(sys.argv.pop(1))

def load_nodes(path, names, scope):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.AsyncFunctionDef)) and n.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope

class Registry:
    @staticmethod
    def async_get(hass): return hass.registry
    @staticmethod
    def async_entries_for_config_entry(registry, entry_id): return registry

async def update_entity(hass, entity_id):
    hass.updated.append(entity_id)
    device = hass.devices[entity_id]
    hass.values[entity_id] = types.SimpleNamespace(state='off' if device.available else 'unavailable')

scope = {'Self': Self, 'DigitalstromClient': object, 'DigitalstromApartment': object}
Device = load_nodes(ROOT/'api/device.py', {'DigitalstromDevice'}, scope)['DigitalstromDevice']
fn_scope = {'HomeAssistant': object, 'ConfigEntry': object, 'DigitalstromApartment': object, 'er': Registry, 'async_update_entity': update_entity}
load_nodes(ROOT/'__init__.py', {'async_refresh_device_availability'}, fn_scope)

class Recovery(unittest.IsolatedAsyncioTestCase):
    def setup_case(self, available=False, state='unavailable', present=True):
        device = Device(None, None, 'lamp')
        device.available = available
        class Client:
            async def request(self, path):
                assert path == 'apartment/getDevices'
                return [{'dSUID': 'lamp', 'isPresent': present}]
        apartment = types.SimpleNamespace(client=Client(), devices={'lamp': device})
        hass = types.SimpleNamespace(updated=[], values={'light.lamp': types.SimpleNamespace(state=state)}, devices={'light.lamp': device}, registry=[types.SimpleNamespace(entity_id='light.lamp', unique_id='lamp_O0', disabled_by=None)])
        hass.states = types.SimpleNamespace(get=hass.values.get)
        return hass, apartment, device

    async def refresh(self, hass, apartment):
        fn = fn_scope.get('async_refresh_device_availability')
        self.assertIsNotNone(fn, 'Missing periodic authoritative availability reconciliation')
        await fn(hass, types.SimpleNamespace(entry_id='dss'), apartment)

    async def test_missing_ready_event_recovers(self):
        h,a,d=self.setup_case()
        await self.refresh(h,a)
        self.assertTrue(d.available)
        self.assertEqual(h.updated,['light.lamp'])
        self.assertEqual(h.values['light.lamp'].state,'off')

    async def test_real_absence_remains_unavailable(self):
        h,a,d=self.setup_case(present=False)
        await self.refresh(h,a)
        self.assertFalse(d.available)
        self.assertEqual(h.updated,[])

    async def test_new_absence_reaches_entity(self):
        h,a,d=self.setup_case(True,'on',False)
        await self.refresh(h,a)
        self.assertFalse(d.available)
        self.assertEqual(h.values['light.lamp'].state,'unavailable')

    async def test_recovered_event_without_entity_write(self):
        h,a,d=self.setup_case(True,'unavailable',True)
        await self.refresh(h,a)
        self.assertEqual(h.updated,['light.lamp'])

    async def test_missing_presence_is_not_false(self):
        h,a,d=self.setup_case(True,'on',None)
        await self.refresh(h,a)
        self.assertTrue(d.available)
        self.assertEqual(h.updated,[])

    async def test_disabled_entity_not_updated(self):
        h,a,d=self.setup_case()
        h.registry[0].disabled_by='user'
        await self.refresh(h,a)
        self.assertTrue(d.available)
        self.assertEqual(h.updated,[])

    async def test_request_failure_preserves_known_state(self):
        h,a,d=self.setup_case(True,'on',True)
        async def fail(path): raise ConnectionError('test offline')
        a.client.request=fail
        with self.assertRaises(ConnectionError): await self.refresh(h,a)
        self.assertTrue(d.available)
        self.assertEqual(h.updated,[])

    async def test_parent_availability_event_does_not_crash(self):
        parent=Device(None,None,'parent');child=Device(None,None,'child')
        parent.available=child.available=True
        child.parent_device=parent
        child.availability_callback(False,call_parent=True)
        self.assertFalse(child.available)
        self.assertFalse(parent.available)

    async def test_unchanged_does_not_repeat_updates(self):
        h,a,d=self.setup_case()
        await self.refresh(h,a)
        await self.refresh(h,a)
        self.assertEqual(h.updated,['light.lamp'])

unittest.main()

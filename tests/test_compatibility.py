import ast
import asyncio
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock

ROOT = pathlib.Path(sys.argv.pop(1))


def load_nodes(path, names, scope):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.AsyncFunctionDef)) and n.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope


class Entity:
    pass


scope = {'Entity': Entity, 'DigitalstromDevice': object, 'DeviceInfo': dict, 'DOMAIN': 'digitalstrom'}
BaseEntity = load_nodes(ROOT / 'entity.py', {'DigitalstromEntity'}, scope)['DigitalstromEntity']


class Compatibility(unittest.TestCase):
    def test_parent_device_keeps_registry_identity(self):
        parent = types.SimpleNamespace(dsuid='lamp', name='Lamp', unique_device_names=[], manufacturer='digitalSTROM', hw_info='GE-KM', meter_dsuid='meter')
        apartment = types.SimpleNamespace(zones={}, device_registry_ids={'meter': 'registered-meter'})
        device = types.SimpleNamespace(dsuid='lamp', zone_id=1, apartment=apartment, get_parent=lambda: parent)
        entity = BaseEntity(device, 'O0')
        self.assertEqual(entity._attr_unique_id, 'lamp_O0')
        self.assertEqual(entity.device_info['via_device_id'], 'registered-meter')
        self.assertNotIn('via_device', entity.device_info)
        self.assertNotIn('entity_id', vars(entity))

    def test_all_explicit_entity_ids_have_platform_domain(self):
        for name in ('light', 'cover', 'switch', 'binary_sensor', 'sensor', 'climate', 'update', 'event', 'scene'):
            tree = ast.parse((ROOT / (name + '.py')).read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign) or not any(isinstance(t, ast.Attribute) and t.attr == 'entity_id' for t in node.targets):
                    continue
                first = node.value.values[0]
                self.assertIsInstance(first, ast.Constant, name)
                self.assertTrue(first.value.startswith(name + '.'), (name, ast.unparse(node)))

    def test_button_group_does_not_override_home_assistant_group(self):
        tree = ast.parse((ROOT / 'event.py').read_text())
        attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'self'}
        self.assertNotIn('group', attributes)
        self.assertIn('button_group', attributes)


class ClimateSetup(unittest.IsolatedAsyncioTestCase):
    async def test_no_supported_zones_make_no_extra_request(self):
        coordinator = AsyncMock()
        scope = {'HomeAssistant': object, 'ConfigEntry': object, 'AddEntitiesCallback': object, 'DOMAIN': 'digitalstrom', 'CONF_DSUID': 'dsuid', 'DigitalstromClimateCoordinator': coordinator}
        setup = load_nodes(ROOT / 'climate.py', {'async_setup_entry'}, scope)['async_setup_entry']
        apartment = types.SimpleNamespace(zones={1: types.SimpleNamespace(climate_control_mode=0)})
        hass = types.SimpleNamespace(data={'digitalstrom': {'system': {'client': object(), 'apartment': apartment}}})
        await setup(hass, types.SimpleNamespace(data={'dsuid': 'system'}), AsyncMock())
        coordinator.assert_not_called()

    async def test_supported_zone_survives_failed_initial_refresh(self):
        coordinator = types.SimpleNamespace(async_refresh=AsyncMock(), async_config_entry_first_refresh=AsyncMock(side_effect=RuntimeError('not ready')))
        scope = {'HomeAssistant': object, 'ConfigEntry': object, 'AddEntitiesCallback': object, 'DOMAIN': 'digitalstrom', 'CONF_DSUID': 'dsuid', 'DigitalstromClimateCoordinator': lambda *args: coordinator, 'DigitalstromClimateEntity': lambda coord, zone: zone, '_LOGGER': types.SimpleNamespace(debug=lambda *args: None)}
        setup = load_nodes(ROOT / 'climate.py', {'async_setup_entry'}, scope)['async_setup_entry']
        zone = types.SimpleNamespace(climate_control_mode=1)
        hass = types.SimpleNamespace(data={'digitalstrom': {'system': {'client': object(), 'apartment': types.SimpleNamespace(zones={1: zone})}}})
        added = []
        await setup(hass, types.SimpleNamespace(data={'dsuid': 'system'}), added.extend)
        coordinator.async_refresh.assert_awaited_once()
        self.assertEqual(added, [zone])


unittest.main()

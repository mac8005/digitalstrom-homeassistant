import ast
import asyncio
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock

ROOT = pathlib.Path(sys.argv.pop(1))

class CannotConnect(Exception): pass
class AlreadyConfigured(Exception): pass

node = next(n for n in ast.parse((ROOT/'config_flow.py').read_text()).body if isinstance(n, ast.ClassDef) and n.name=='DigitalstromConfigFlow')
method = next(n for n in node.body if isinstance(n, ast.AsyncFunctionDef) and n.name=='async_step_discovery_')
method.returns = None
scope={'CONF_HOST':'host','CannotConnect':CannotConnect}
exec(compile(ast.Module(body=[method],type_ignores=[]),'config_flow.py','exec'),scope)

class Discovery(unittest.IsolatedAsyncioTestCase):
    def flow(self):
        return types.SimpleNamespace(_host='server',_port=8080,hass=types.SimpleNamespace(loop=None),_async_abort_entries_match=Mock(),async_abort=lambda **kw:{'type':'abort',**kw},async_set_unique_id=AsyncMock(),_abort_if_unique_id_configured=Mock(),async_step_user=AsyncMock(return_value={'type':'form'}))
    async def test_existing_host_avoids_network_probe(self):
        f=self.flow();f._async_abort_entries_match.side_effect=AlreadyConfigured
        client=Mock();scope['DigitalstromClient']=client
        with self.assertRaises(AlreadyConfigured):await scope['async_step_discovery_'](f)
        client.assert_not_called();f._async_abort_entries_match.assert_called_once_with({'host':'server'})
    async def test_disconnected_new_server_aborts_cleanly(self):
        f=self.flow();client=types.SimpleNamespace(get_system_dsuid=AsyncMock(side_effect=CannotConnect('disconnected')));scope['DigitalstromClient']=lambda **kw:client
        result=await scope['async_step_discovery_'](f)
        self.assertEqual(result,{'type':'abort','reason':'cannot_connect'});f.async_set_unique_id.assert_not_called()
    async def test_new_server_keeps_unique_identity_and_setup(self):
        f=self.flow();client=types.SimpleNamespace(get_system_dsuid=AsyncMock(return_value='system-id'));scope['DigitalstromClient']=lambda **kw:client
        self.assertEqual(await scope['async_step_discovery_'](f),{'type':'form'})
        f.async_set_unique_id.assert_awaited_once_with('system-id');f._abort_if_unique_id_configured.assert_called_once_with(updates={'host':'server'})

unittest.main()

import ast
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock
from collections.abc import Callable

root = pathlib.Path(sys.argv.pop(1))
scope = {'Callable': Callable, 'DigitalstromDevice': object, 'DigitalstromCircuit': object}
tree = ast.parse((root / 'api/channel.py').read_text())
nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ['DigitalstromChannel', 'DigitalstromMeterSensorChannel']]
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'channel.py', 'exec'), scope)
Channel = scope['DigitalstromMeterSensorChannel']

class Metering(unittest.IsolatedAsyncioTestCase):
    def channel(self, index, result, producer=False, metering=True):
        client = types.SimpleNamespace(request=AsyncMock(return_value=result))
        device = types.SimpleNamespace(dsuid='meter-uid', dsid='meter-id', has_metering=metering, has_metering_producer=producer, client=client)
        return Channel(device, index), client

    async def test_consumption_counter_preserves_watt_seconds(self):
        c, client = self.channel('energy', {'values': [{'dSUID': 'meter-uid', 'value': 4381741728}]})
        self.assertEqual(await c.get_value(), 4381741728)
        client.request.assert_awaited_once_with('metering/getLatest?from=.meters(meter-uid)&type=energy&unit=Ws')

    async def test_power_accepts_real_zero_and_legacy_identifier(self):
        c, client = self.channel('power', {'values': [{'dsid': 'meter-id', 'value': 0}]})
        self.assertEqual(await c.get_value(), 0)
        self.assertIn('type=consumption', client.request.call_args.args[0])

    async def test_missing_meter_never_becomes_zero_or_another_meter(self):
        for data in [{}, {'values': []}, {'values': [{'dSUID': 'other', 'value': 50}]}]:
            c, _ = self.channel('energy', data)
            self.assertIsNone(await c.get_value())

    async def test_producer_energy_preserves_existing_semantics(self):
        c, client = self.channel('energy', {'meterValue': 99}, producer=True)
        self.assertEqual(await c.get_value(), 99)
        client.request.assert_awaited_once_with('circuit/getEnergyMeterValue?id=meter-id')

    async def test_producer_power_preserves_existing_semantics(self):
        c, client = self.channel('power', {'consumption': -40}, producer=True)
        self.assertEqual(await c.get_value(), -40)
        client.request.assert_awaited_once_with('circuit/getConsumption?id=meter-id')

    async def test_no_metering_does_not_query(self):
        c, client = self.channel('power', {}, metering=False)
        self.assertIsNone(await c.get_value())
        client.request.assert_not_awaited()

unittest.main()

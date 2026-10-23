import asyncio
import importlib
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

try:
    import homeassistant.exceptions
except ModuleNotFoundError:
    exceptions = types.ModuleType('homeassistant.exceptions')
    exceptions.HomeAssistantError = type('HomeAssistantError', (Exception,), {})
    sys.modules['homeassistant.exceptions'] = exceptions

root = pathlib.Path(sys.argv.pop(1)).resolve()
package = types.ModuleType('polling_api')
package.__path__ = [str(root / 'api')]
sys.modules[package.__name__] = package
api = importlib.import_module('polling_api.client')
channels = importlib.import_module('polling_api.channel')
devices = importlib.import_module('polling_api.device')


class Polling(unittest.IsolatedAsyncioTestCase):
    def client(self, data=None):
        client = api.DigitalstromClient('test.invalid', 8080)
        client._request_authenticated = AsyncMock(return_value=data or {})
        return client

    def outputs(self, value=42):
        return {'zone1': {
            'ZoneID': 1,
            'lamp': {'dSUID': 'lamp', 'brightness': {'targetValue': value}},
            'blind': {'dSUID': 'blind', 'shadePositionOutside': {'targetValue': 75},
                      'shadeOpeningAngleOutside': {'targetValue': 25}},
            'relay': {'dSUID': 'relay', 'powerState': {'targetValue': 0}},
        }}

    async def test_concurrent_outputs_share_one_cache_only_request(self):
        client = self.client(self.outputs())
        values = await asyncio.gather(*[
            client.get_output_value(1, 'lamp', 'brightness') for _ in range(40)
        ])
        self.assertEqual(values, [42] * 40)
        client._request_authenticated.assert_awaited_once_with(api.OUTPUT_QUERY)

    async def test_device_channels_preserve_position_tilt_and_real_zero(self):
        client = self.client(self.outputs())
        device = devices.DigitalstromDevice(client, None, 'blind')
        device.zone_id = 1
        position = channels.DigitalstromOutputChannel(device, 0, 'shadePositionOutside', '', '')
        tilt = channels.DigitalstromOutputChannel(device, 1, 'shadeOpeningAngleOutside', '', '')
        self.assertEqual(await position.get_value(), 75)
        self.assertEqual(await tilt.get_value(), 25)
        device.dsuid = 'relay'
        self.assertEqual(await device.get_power_state(), 0)
        self.assertEqual(client._request_authenticated.await_count, 1)

    async def test_unknown_channel_device_or_zone_stays_unknown(self):
        client = self.client(self.outputs())
        for zone, device, channel in [(2, 'lamp', 'brightness'), (1, 'other', 'brightness'),
                                      (1, 'lamp', 'powerState')]:
            self.assertIsNone(await client.get_output_value(zone, device, channel))
        self.assertEqual(client._request_authenticated.await_count, 1)

    async def test_snapshot_expires_and_recovers_missing_values(self):
        client = self.client()
        client._request_authenticated.side_effect = [{}, self.outputs(0)]
        with patch.object(api, 'time') as clock:
            clock.monotonic.return_value = 100
            self.assertIsNone(await client.get_output_value(1, 'lamp', 'brightness'))
            clock.monotonic.return_value = 104.9
            self.assertIsNone(await client.get_output_value(1, 'lamp', 'brightness'))
            clock.monotonic.return_value = 105
            self.assertEqual(await client.get_output_value(1, 'lamp', 'brightness'), 0)
        self.assertEqual(client._request_authenticated.await_count, 2)

    async def test_failed_refresh_never_serves_old_data_or_retries_per_entity(self):
        client = self.client()
        client._request_authenticated.side_effect = [self.outputs(), api.ServerError('offline'), self.outputs(10)]
        with patch.object(api, 'time') as clock:
            clock.monotonic.return_value = 100
            self.assertEqual(await client.get_output_value(1, 'lamp', 'brightness'), 42)
            clock.monotonic.return_value = 105
            results = await asyncio.gather(*[
                client.get_output_value(1, 'lamp', 'brightness') for _ in range(40)
            ], return_exceptions=True)
            self.assertTrue(all(isinstance(r, api.ServerError) for r in results))
            self.assertEqual(client._request_authenticated.await_count, 2)
            clock.monotonic.return_value = 110
            self.assertEqual(await client.get_output_value(1, 'lamp', 'brightness'), 10)

    async def test_each_output_command_invalidates_even_when_it_fails(self):
        for command in api.OUTPUT_COMMANDS:
            for error in [None, api.CannotConnect('timeout')]:
                with self.subTest(command=command, error=error):
                    client = self.client(self.outputs())
                    await client.get_output_value(1, 'lamp', 'brightness')
                    client._request_authenticated.side_effect = [error or {}, self.outputs(0)]
                    if error:
                        with self.assertRaises(api.CannotConnect):
                            await client.request(command + '?test=1')
                    else:
                        await client.request(command + '?test=1')
                    self.assertEqual(await client.get_output_value(1, 'lamp', 'brightness'), 0)
                    self.assertEqual(client._request_authenticated.await_count, 3)

    async def test_inflight_read_cannot_repopulate_cache_after_command(self):
        started, release = asyncio.Event(), asyncio.Event()
        value = 42
        async def request(url):
            nonlocal value
            if url == api.OUTPUT_QUERY:
                snapshot = self.outputs(value)
                started.set()
                await release.wait()
                return snapshot
            value = 0
            return {}
        client = self.client()
        client._request_authenticated.side_effect = request
        read = asyncio.create_task(client.get_output_value(1, 'lamp', 'brightness'))
        await started.wait()
        write = asyncio.create_task(client.request('device/setOutputChannelValue?test=1'))
        await asyncio.sleep(0)
        release.set()
        self.assertEqual(await read, 42)
        await write
        self.assertEqual(await client.get_output_value(1, 'lamp', 'brightness'), 0)

    async def test_four_meters_need_two_requests_and_keep_meter_identity(self):
        client = self.client()
        async def request(url):
            energy = 'type=energy' in url
            return {'values': [{'dSUID': f'meter{i}', 'value': i * (3600000 if energy else 10)} for i in range(4)]}
        client._request_authenticated.side_effect = request
        sensors = []
        for i in range(4):
            circuit = types.SimpleNamespace(client=client, dsuid=f'meter{i}', dsid=f'id{i}',
                                            has_metering=True, has_metering_producer=False)
            sensors.extend(channels.DigitalstromMeterSensorChannel(circuit, index) for index in ['power', 'energy'])
        self.assertEqual(await asyncio.gather(*(c.get_value() for c in sensors)),
                         [0, 0, 10, 3600000, 20, 7200000, 30, 10800000])
        self.assertEqual(client._request_authenticated.await_count, 2)
        self.assertEqual({c.args[0] for c in client._request_authenticated.call_args_list}, {
            'metering/getLatest?from=.meters(all)&type=consumption&unit=Ws',
            'metering/getLatest?from=.meters(all)&type=energy&unit=Ws',
        })

    async def test_meter_failure_is_shared_then_retried(self):
        client = self.client()
        client._request_authenticated.side_effect = [api.CannotConnect('offline'), {'values': []}]
        with patch.object(api, 'time') as clock:
            clock.monotonic.return_value = 100
            for _ in range(4):
                with self.assertRaises(api.CannotConnect):
                    await client.get_metering_values('energy')
            self.assertEqual(client._request_authenticated.await_count, 1)
            clock.monotonic.return_value = 105
            self.assertEqual(await client.get_metering_values('energy'), {'values': []})

    async def test_snapshot_is_isolated_between_servers(self):
        one, two = self.client(self.outputs(1)), self.client(self.outputs(2))
        self.assertEqual(await one.get_output_value(1, 'lamp', 'brightness'), 1)
        self.assertEqual(await two.get_output_value(1, 'lamp', 'brightness'), 2)

    async def test_slow_snapshot_times_out_and_releases_waiting_command(self):
        client = self.client()
        async def request(url):
            if url == api.OUTPUT_QUERY:
                await asyncio.Event().wait()
            return {}
        client._request_authenticated.side_effect = request
        timeout = asyncio.timeout
        with patch.object(api.asyncio, 'timeout', side_effect=lambda seconds: timeout(0)):
            with self.assertRaises(TimeoutError):
                await client.get_output_value(1, 'lamp', 'brightness')
        await client.request('device/setOutputChannelValue?test=1')
        self.assertEqual(client._request_authenticated.await_count, 2)


unittest.main()

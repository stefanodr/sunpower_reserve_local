"""Home Assistant level test with a fake Modbus inverter (needs
pytest-homeassistant-custom-component)."""

import asyncio
import struct

import pytest
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sunpower_reserve_local.const import DOMAIN

ROWS = {
    0x0010: "4 41061 2 6375 237 0 0 65528", 0x0018: "0 0 4997 65535 65524 0 0 0",
    0x0100: "1001 65405 700 257 3 1 2 3338", 0x0108: "1 14 3341 1 3 210 1 1",
    0x0110: "220 524 524 1080 900 155 0 0", 0x0120: "0 42048 0 40853 0 544 64264 0",
    0x0400: "2340 0 0 65529 0 0 0 390", 0x0408: "0 0 0 0 0 391 2340 0",
    0x0418: "0 0 0 293 4997 1480 48 0", 0x0420: "687 2180 51 0 1106 0 0 0",
    0x0430: "0 0 0 0 0 540 0 0",
}
MEM = {b + i: int(v) for b, r in ROWS.items() for i, v in enumerate(r.split())}

def _words(text, count):
    raw = text.encode().ljust(count * 2, b"\0")
    return [int.from_bytes(raw[i:i + 2], "big") for i in range(0, count * 2, 2)]


def _add_static(mem):
    for start in (0x0640, 0x0648, 0x0650, 0x0748, 0x0800, 0x08A0):
        for i in range(8):
            mem.setdefault(start + i, 0)
    for i, w in enumerate(_words("01000.165", 5)):
        mem[0x0640 + i] = w
    for i, w in enumerate(_words("SOD000000000000", 8)):
        mem[0x064A + i] = w
    mem.update({0x074B: 0, 0x074C: 11, 0x074D: 50, 0x074E: 0, 0x074F: 17920})
    mem.update({0x0800: 100, 0x0802: 4500, 0x08A3: 4600})


_add_static(MEM)
FCS = []


async def _handle(reader, writer):
    try:
        while True:
            hdr = await reader.readexactly(7)
            txid, _, length, unit = struct.unpack(">HHHB", hdr)
            body = await reader.readexactly(length - 1)
            FCS.append(body[0])
            addr, count = struct.unpack(">HH", body[1:5])
            if addr not in MEM:
                pdu = bytes([0x83, 2])
            else:
                pdu = bytes([3, 2 * count]) + struct.pack(
                    f">{count}H", *[MEM.get(addr + i, 0) for i in range(count)]
                )
            writer.write(struct.pack(">HHHB", txid, 0, len(pdu) + 1, unit) + pdu)
            await writer.drain()
    except asyncio.IncompleteReadError:
        pass
    finally:
        writer.close()


@pytest.fixture
async def inverter(socket_enabled):
    server = await asyncio.start_server(_handle, "127.0.0.1", 0)
    yield server.sockets[0].getsockname()[1]
    server.close()
    await server.wait_closed()


def _state(hass, entry, key):
    reg = er.async_get(hass)
    ent = reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}")
    assert ent, key
    return hass.states.get(ent), reg.async_get(ent)


async def test_setup_and_values(hass, inverter):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "127.0.0.1", "port": inverter, "unit": 85}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for key, want in {
        "battery_soc": 70.0, "battery_power": -1272, "grid_power": -12,
        "pv_power": 1793, "house_load": 509, "grid_energy_import": 1374.47,
        "battery_energy_charged": 4204.8, "pv_energy": 0.0,
        "grid_energy_export_daily": 0.0, "battery_state": "charging",
        "grid_state": "idle",
    }.items():
        state, _ = _state(hass, entry, key)
        assert state is not None, key
        got = state.state if isinstance(want, str) else float(state.state)
        assert got == want, (key, got, want)

    # every sensor is enabled by default
    for key in ("inverter_temperature", "grid_current", "battery_stored_energy"):
        _, reg_entry = _state(hass, entry, key)
        assert reg_entry.disabled_by is None, key
    assert float(_state(hass, entry, "battery_stored_energy")[0].state) == 6.7
    assert float(_state(hass, entry, "battery_usable_energy")[0].state) == 5.75
    assert _state(hass, entry, "inverter_firmware")[0].state == "01000.165"
    assert _state(hass, entry, "bms_firmware")[0].state == "V1.55"
    assert _state(hass, entry, "ems_firmware")[0].state == "V0.11.50F"
    assert float(_state(hass, entry, "export_limit")[0].state) == 100
    assert float(_state(hass, entry, "pv_installed_power")[0].state) == 4.5
    dev = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert dev.sw_version == "01000.165" and dev.serial_number == "SOD000000000000"
    assert set(FCS) == {3}

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_config_flow(hass, inverter):
    res = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    res = await hass.config_entries.flow.async_configure(
        res["flow_id"], {"host": "127.0.0.1", "port": inverter, "unit": 85}
    )
    assert res["type"] == "create_entry"
    assert res["data"]["port"] == inverter
    await hass.async_block_till_done()
    for e in hass.config_entries.async_entries(DOMAIN):
        await hass.config_entries.async_remove(e.entry_id)
    await hass.async_block_till_done()


async def test_config_flow_cannot_connect(hass, socket_enabled):
    res = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    res = await hass.config_entries.flow.async_configure(
        res["flow_id"], {"host": "127.0.0.1", "port": 1, "unit": 85}
    )
    assert res["type"] == "form" and res["errors"] == {"base": "cannot_connect"}


async def test_options_offsets(hass, inverter):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "127.0.0.1", "port": inverter, "unit": 85},
        options={"pv_energy_offset": 12230.3, "house_energy_offset": 10461.84,
                 "battery_usable_capacity": 10.0, "battery_backup_reserve": 20},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert float(_state(hass, entry, "pv_energy")[0].state) == 12230.3
    assert float(_state(hass, entry, "house_energy")[0].state) == 10461.84
    assert float(_state(hass, entry, "pv_energy_daily")[0].state) == 0.0
    assert float(_state(hass, entry, "battery_stored_energy")[0].state) == 7.0
    assert float(_state(hass, entry, "battery_usable_energy")[0].state) == 5.0
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

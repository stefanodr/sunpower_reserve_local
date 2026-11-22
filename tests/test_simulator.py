"""Fake inverter serving the real dump; checks decoding and read-only behaviour.

Run:  python3 tests/test_simulator.py
"""

import asyncio
import importlib.util
import pathlib
import struct
import sys

PKG = pathlib.Path(__file__).parent.parent / "custom_components" / "sunpower_reserve_local"


def load(name):
    spec = importlib.util.spec_from_file_location(name, PKG / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


modbus, registers, energy = load("modbus"), load("registers"), load("energy")

DUMP = {
    0x0010: "4 41061 2 6375 237 0 0 65528", 0x0018: "0 0 4997 65535 65524 0 0 0",
    0x0020: "0 65535 65524 0 0 0 0 0", 0x0028: "0 0 0 0 204 0 0 0",
    0x0100: "1001 65405 700 257 3 1 2 3338", 0x0108: "1 14 3341 1 3 210 1 1",
    0x0110: "220 524 524 1080 900 155 0 0", 0x0118: "1 100 108 1000 0 0 0 0",
    0x0120: "0 42048 0 40853 0 544 64264 0", 0x0128: "0 0 0 0 5250 5250 0 0",
    0x0400: "2340 0 0 65529 0 0 0 390", 0x0408: "0 0 0 0 0 391 2340 0",
    0x0410: "0 13 0 0 0 302 0 0", 0x0418: "0 0 0 293 4997 1480 48 0",
    0x0420: "687 2180 51 0 1106 0 0 0", 0x0428: "0 0 0 0 0 0 0 0",
    0x0430: "0 0 0 0 0 540 0 0", 0x0438: "0 0 0 0 0 0 1 56759",
}
MEM = {}
for base, row in DUMP.items():
    for i, v in enumerate(map(int, row.split())):
        MEM[base + i] = v

seen_fc = []
EXCEPTION_BLOCKS = set()


async def handle(reader, writer):
    try:
        while True:
            hdr = await reader.readexactly(7)
            txid, _, length, unit = struct.unpack(">HHHB", hdr)
            body = await reader.readexactly(length - 1)
            fc = body[0]
            seen_fc.append(fc)
            addr, count = struct.unpack(">HH", body[1:5])
            if addr in EXCEPTION_BLOCKS or addr not in MEM:
                pdu = bytes([0x83, 2])
            else:
                vals = [MEM.get(addr + i, 0) for i in range(count)]
                pdu = bytes([3, 2 * count]) + struct.pack(f">{count}H", *vals)
            writer.write(struct.pack(">HHHB", txid, 0, len(pdu) + 1, unit) + pdu)
            await writer.drain()
    except asyncio.IncompleteReadError:
        pass
    finally:
        writer.close()


async def main():
    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = modbus.ReadOnlyModbusClient("127.0.0.1", port, 85, request_delay=0.01)

    assert await client.read_once(0x0102, 1) == [700]

    regs, refused = await client.read_blocks(registers.BLOCKS, registers.BLOCK_SIZE)
    assert not refused, refused
    d = registers.decode(regs)
    expected = {
        "battery_soc": 70.0, "battery_power": -1272, "grid_power": -12,
        "pv1_power": 687, "pv2_power": 1106, "pv_power": 1793,
        "grid_energy_import": 1374.47, "grid_energy_export": 3032.05,
        "battery_energy_charged": 4204.8, "battery_energy_discharged": 4085.3,
        "battery_voltage": 100.1, "battery_current": -13.1,
        "grid_frequency": 49.97, "inverter_power": 391, "inverter_voltage": 234.0,
        "pv1_voltage": 148.0, "pv2_voltage": 218.0, "inverter_temperature": 54.0,
        "house_load": 509,
    }
    for key, want in expected.items():
        assert abs(d[key] - want) < 1e-6, (key, d[key], want)
    assert d["battery_state"] == "charging" and d["grid_state"] == "idle", (d["battery_state"], d["grid_state"])
    print("decoded values OK:", len(expected), "checked,", len(d), "total")

    # a block refused with a Modbus exception -> its values are None, others fine
    EXCEPTION_BLOCKS.add(0x0430)
    regs, refused = await client.read_blocks(registers.BLOCKS, registers.BLOCK_SIZE)
    assert refused == [0x0430]
    assert registers.decode(regs)["inverter_temperature"] is None
    assert registers.decode(regs)["battery_soc"] == 70.0

    # device unreachable -> connection error
    server.close()
    await server.wait_closed()
    try:
        await client.read_once(0x0102, 1)
    except modbus.ModbusConnectionError:
        pass
    else:
        raise AssertionError("expected ModbusConnectionError")

    assert set(seen_fc) == {3}, set(seen_fc)
    print(f"only function code 3 sent ({len(seen_fc)} requests) OK")


def test_energy():
    from datetime import datetime
    acc = energy.EnergyAccumulator(max_gap=45)
    d0 = {"pv_power": 3600.0, "house_load": 1800.0, "grid_energy_export": 100.0,
          "grid_energy_import": 50.0, "battery_energy_charged": 10.0,
          "battery_energy_discharged": 8.0}
    t0 = datetime(2026, 11, 22, 23, 59, 0)
    acc.update(dict(d0), t0, 0.0)
    d = dict(d0, grid_energy_export=100.5)
    acc.update(d, datetime(2026, 11, 22, 23, 59, 30), 30.0)
    # 3600 W for 30 s = 0.03 kWh ; 1800 W -> 0.015 kWh
    assert abs(d["pv_energy"] - 0.03) < 1e-9 and abs(d["house_energy"] - 0.015) < 1e-9, d
    assert d["grid_energy_export_daily"] == 0.5 and d["grid_energy_export_monthly"] == 0.5
    # gap larger than max_gap: not integrated
    d = dict(d0, grid_energy_export=101.0)
    acc.update(d, datetime(2026, 11, 23, 0, 5, 0), 400.0)
    assert d["pv_energy"] == 0.03, d["pv_energy"]
    # new day: daily resets, month/year/week continue (23 Nov is Monday = new ISO week)
    assert d["grid_energy_export_daily"] == 0.0
    assert d["grid_energy_export_weekly"] == 0.0
    assert d["grid_energy_export_monthly"] == 1.0
    assert d["grid_energy_export_yearly"] == 1.0
    # persistence round trip
    acc2 = energy.EnergyAccumulator(45, acc.to_dict())
    d = dict(d0, grid_energy_export=101.2)
    acc2.update(d, datetime(2026, 11, 23, 0, 6, 0), 1000.0)
    assert d["pv_energy"] == 0.03 and d["grid_energy_export_daily"] == 0.2
    # counter reset (total lower than baseline) restarts the period
    d = dict(d0, grid_energy_export=5.0)
    acc2.update(d, datetime(2026, 11, 23, 0, 7, 0), 1010.0)
    assert d["grid_energy_export_daily"] == 0.0
    # negative power ignored
    d = dict(d0, pv_power=-50.0)
    acc2.update(d, datetime(2026, 11, 23, 0, 8, 0), 1020.0)
    assert d["pv_energy"] >= 0.03
    # states
    assert registers.decode({})["battery_state"] is None
    print("energy accumulator OK")


test_energy()
asyncio.run(main())
print("ALL TESTS PASSED")

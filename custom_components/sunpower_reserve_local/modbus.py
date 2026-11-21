"""Minimal READ-ONLY Modbus TCP client (function code 0x03 only).

There is intentionally no code path that builds any other function code:
this integration can never write to the inverter.
"""

from __future__ import annotations

import asyncio
import struct

FC_READ_HOLDING = 0x03
FC_READ_HOLDING_ERROR = 0x83
MAX_REGISTERS_PER_REQUEST = 8  # conservative: what was verified on the inverter


class ModbusError(Exception):
    """Base error."""


class ModbusConnectionError(ModbusError):
    """Cannot connect / timeout / broken connection / invalid frame."""


class ModbusExceptionResponse(ModbusError):
    """The device answered with a Modbus exception (e.g. illegal address)."""

    def __init__(self, address: int, code: int) -> None:
        super().__init__(f"Modbus exception {code} at 0x{address:04X}")
        self.address = address
        self.code = code


class ReadOnlyModbusClient:
    """Async Modbus TCP client; one short-lived connection per poll."""

    def __init__(
        self,
        host: str,
        port: int = 502,
        unit: int = 85,
        timeout: float = 5.0,
        request_delay: float = 0.25,
    ) -> None:
        self.host = host
        self.port = port
        self.unit = unit
        self.timeout = timeout
        self.request_delay = request_delay
        self._lock = asyncio.Lock()
        self._txid = 0
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    # -- connection ---------------------------------------------------
    async def _open(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), self.timeout
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise ModbusConnectionError(
                f"Cannot connect to {self.host}:{self.port}: {err!r}"
            ) from err

    async def _close(self) -> None:
        writer, self._writer, self._reader = self._writer, None, None
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except (OSError, asyncio.TimeoutError):
                pass

    # -- protocol -----------------------------------------------------
    async def _read(self, address: int, count: int) -> list[int]:
        if not 1 <= count <= MAX_REGISTERS_PER_REQUEST:
            raise ValueError("invalid register count")
        assert self._reader is not None and self._writer is not None
        self._txid = (self._txid % 0xFFFF) + 1
        request = struct.pack(
            ">HHHBBHH", self._txid, 0, 6, self.unit, FC_READ_HOLDING, address, count
        )
        try:
            self._writer.write(request)
            await asyncio.wait_for(self._writer.drain(), self.timeout)
            header = await asyncio.wait_for(
                self._reader.readexactly(7), self.timeout
            )
            txid, proto, length, unit = struct.unpack(">HHHB", header)
            if proto != 0 or not 2 <= length <= 260:
                raise ModbusConnectionError("invalid MBAP header")
            body = await asyncio.wait_for(
                self._reader.readexactly(length - 1), self.timeout
            )
        except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError) as err:
            raise ModbusConnectionError(f"I/O error: {err!r}") from err

        if txid != self._txid or unit != self.unit:
            raise ModbusConnectionError("unexpected transaction/unit id")
        fc = body[0]
        if fc == FC_READ_HOLDING_ERROR and len(body) >= 2:
            raise ModbusExceptionResponse(address, body[1])
        if fc != FC_READ_HOLDING or len(body) < 2 or body[1] != 2 * count:
            raise ModbusConnectionError("unexpected response")
        if len(body) != 2 + 2 * count:
            raise ModbusConnectionError("truncated response")
        return list(struct.unpack(f">{count}H", body[2:]))

    # -- public API ---------------------------------------------------
    async def read_once(self, address: int, count: int = 1) -> list[int]:
        """Open, read one block, close (used by the config flow)."""
        async with self._lock:
            await self._open()
            try:
                return await self._read(address, count)
            finally:
                await self._close()

    async def read_blocks(
        self, starts: list[int], count: int
    ) -> tuple[dict[int, int], list[int]]:
        """Read several blocks on a single connection.

        Returns (registers by address, start addresses refused by the device).
        Connection-level problems raise ModbusConnectionError.
        """
        registers: dict[int, int] = {}
        refused: list[int] = []
        async with self._lock:
            await self._open()
            try:
                for index, start in enumerate(starts):
                    if index:
                        await asyncio.sleep(self.request_delay)
                    try:
                        values = await self._read(start, count)
                    except ModbusExceptionResponse:
                        refused.append(start)
                        continue
                    for offset, value in enumerate(values):
                        registers[start + offset] = value
            finally:
                await self._close()
        return registers, refused

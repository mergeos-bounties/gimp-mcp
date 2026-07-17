"""Socket bridge backend for low-latency GIMP IPC.

This backend uses the socket protocol for long-running GIMP plugin
connections with low-latency operations. Mock mode is the default.
"""

from __future__ import annotations

from typing import Any

from gimp_mcp.bridge import (
    BridgeClient,
    BridgeMessage,
    BridgeProtocol,
    MSG_PING,
    MSG_EXEC,
    MSG_BATCH,
    MSG_STATUS,
    create_default_handlers,
)
from gimp_mcp.config import workspace_dir


class BridgeBackend:
    """Socket bridge backend for GIMP plugin IPC."""

    name = "bridge"

    def __init__(
        self,
        socket_path: str | None = None,
        tcp_host: str | None = None,
        tcp_port: int | None = None,
    ):
        self._client = BridgeClient(
            socket_path=socket_path,
            tcp_host=tcp_host,
            tcp_port=tcp_port,
        )
        self._connected = False
        self._ws = workspace_dir() / "bridge"
        self._ws.mkdir(parents=True, exist_ok=True)

    def connect(self, use_tcp: bool = False) -> bool:
        """Connect to the bridge server."""
        if use_tcp:
            self._connected = self._client.connect_tcp()
        else:
            self._connected = self._client.connect_unix()
        return self._connected

    def disconnect(self) -> None:
        """Disconnect from the bridge server."""
        self._client.disconnect()
        self._connected = False

    def doctor(self) -> dict[str, Any]:
        """Check bridge connectivity."""
        if not self._connected:
            return {
                "ok": False,
                "mode": "bridge",
                "connected": False,
                "message": "Not connected to bridge server",
            }

        try:
            response = self._client.send_command(MSG_PING, {})
            return {
                "ok": True,
                "mode": "bridge",
                "connected": True,
                "version": response.get("version"),
                "workspace": str(self._ws),
            }
        except Exception as e:
            return {
                "ok": False,
                "mode": "bridge",
                "connected": False,
                "error": str(e),
            }

    def exec_operation(
        self, op: str, params: dict[str, Any], timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute a single operation via the bridge."""
        if not self._connected:
            return {"ok": False, "error": "Not connected to bridge"}

        try:
            response = self._client.send_command(
                MSG_EXEC,
                {"op": op, "params": params},
                timeout=timeout,
            )
            return response
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def exec_batch(
        self, operations: list[dict[str, Any]], timeout: float = 60.0
    ) -> dict[str, Any]:
        """Execute multiple operations in a batch."""
        if not self._connected:
            return {"ok": False, "error": "Not connected to bridge"}

        try:
            response = self._client.send_command(
                MSG_BATCH,
                {"operations": operations},
                timeout=timeout,
            )
            return response
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """Get bridge server status."""
        if not self._connected:
            return {"ok": False, "error": "Not connected to bridge"}

        try:
            response = self._client.send_command(MSG_STATUS, {})
            return {"ok": True, **response}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def create_bridge_server(
    socket_path: str | None = None,
    tcp_host: str | None = None,
    tcp_port: int | None = None,
) -> BridgeProtocol:
    """Create a bridge server with default handlers."""
    server = BridgeProtocol(
        socket_path=socket_path,
        tcp_host=tcp_host,
        tcp_port=tcp_port,
    )

    # Register default handlers
    for msg_type, handler in create_default_handlers().items():
        server.register_handler(msg_type, handler)

    # Register exec handler
    def handle_exec(msg: BridgeMessage) -> dict[str, Any]:
        op = msg.payload.get("op")
        params = msg.payload.get("params", {})
        # TODO: Implement actual GIMP operations
        return {"ok": True, "op": op, "params": params, "result": "stub"}

    server.register_handler(MSG_EXEC, handle_exec)

    # Register batch handler
    def handle_batch(msg: BridgeMessage) -> dict[str, Any]:
        operations = msg.payload.get("operations", [])
        results = []
        for op in operations:
            # TODO: Implement actual GIMP operations
            results.append({"ok": True, "op": op.get("op"), "result": "stub"})
        return {"ok": True, "results": results}

    server.register_handler(MSG_BATCH, handle_batch)

    return server

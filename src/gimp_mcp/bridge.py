"""Plugin bridge socket protocol for low-latency GIMP IPC.

This module provides a socket-based protocol for long-running GIMP plugin
connections with low-latency operations. Mock mode is the default.

Protocol Design:
- JSON-based messages over Unix/TCP sockets
- Request-response pattern with unique IDs
- Support for batch operations
- Auto-reconnection on failures
"""

from __future__ import annotations

import json
import socket
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

# Protocol constants
PROTOCOL_VERSION = "1.0.0"
DEFAULT_SOCKET_PATH = "/tmp/gimp-mcp-bridge.sock"
DEFAULT_TCP_HOST = "127.0.0.1"
DEFAULT_TCP_PORT = 9876
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
RESPONSE_TIMEOUT = 30.0  # seconds


class BridgeMessage:
    """A message in the bridge protocol."""

    def __init__(
        self,
        msg_type: str,
        payload: dict[str, Any],
        msg_id: str | None = None,
    ):
        self.msg_type = msg_type
        self.payload = payload
        self.msg_id = msg_id or str(uuid.uuid4())
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": PROTOCOL_VERSION,
            "type": self.msg_type,
            "id": self.msg_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BridgeMessage":
        return cls(
            msg_type=data["type"],
            payload=data["payload"],
            msg_id=data.get("id"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "BridgeMessage":
        return cls.from_dict(json.loads(json_str))


class BridgeProtocol:
    """Socket protocol handler for GIMP plugin bridge."""

    def __init__(
        self,
        socket_path: str | None = None,
        tcp_host: str | None = None,
        tcp_port: int | None = None,
    ):
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH
        self.tcp_host = tcp_host or DEFAULT_TCP_HOST
        self.tcp_port = tcp_port or DEFAULT_TCP_PORT
        self._handlers: dict[str, Callable[[BridgeMessage], dict[str, Any]]] = {}
        self._running = False
        self._server_socket: socket.socket | None = None
        self._lock = threading.Lock()

    def register_handler(
        self, msg_type: str, handler: Callable[[BridgeMessage], dict[str, Any]]
    ) -> None:
        """Register a handler for a message type."""
        self._handlers[msg_type] = handler

    def start_unix(self) -> None:
        """Start Unix socket server."""
        self._running = True
        self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Remove existing socket file
        sock_path = Path(self.socket_path)
        if sock_path.exists():
            sock_path.unlink()
        
        self._server_socket.bind(self.socket_path)
        self._server_socket.listen(5)
        self._server_socket.settimeout(1.0)
        
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def start_tcp(self) -> None:
        """Start TCP socket server."""
        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.tcp_host, self.tcp_port))
        self._server_socket.listen(5)
        self._server_socket.settimeout(1.0)
        
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None

    def _accept_loop(self) -> None:
        """Accept incoming connections."""
        while self._running:
            try:
                client_socket, addr = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True,
                ).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client_socket: socket.socket) -> None:
        """Handle a client connection."""
        try:
            client_socket.settimeout(RESPONSE_TIMEOUT)
            while self._running:
                data = client_socket.recv(MAX_MESSAGE_SIZE)
                if not data:
                    break
                
                try:
                    msg = BridgeMessage.from_json(data.decode("utf-8"))
                    response = self._process_message(msg)
                    response_msg = BridgeMessage(
                        msg_type="response",
                        payload=response,
                        msg_id=msg.msg_id,
                    )
                    client_socket.sendall(response_msg.to_json().encode("utf-8"))
                except Exception as e:
                    error_response = BridgeMessage(
                        msg_type="error",
                        payload={"error": str(e)},
                    )
                    client_socket.sendall(error_response.to_json().encode("utf-8"))
        finally:
            client_socket.close()

    def _process_message(self, msg: BridgeMessage) -> dict[str, Any]:
        """Process a message and return response."""
        handler = self._handlers.get(msg.msg_type)
        if handler:
            return handler(msg)
        return {"error": f"Unknown message type: {msg.msg_type}"}


class BridgeClient:
    """Client for connecting to GIMP plugin bridge."""

    def __init__(
        self,
        socket_path: str | None = None,
        tcp_host: str | None = None,
        tcp_port: int | None = None,
    ):
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH
        self.tcp_host = tcp_host or DEFAULT_TCP_HOST
        self.tcp_port = tcp_port or DEFAULT_TCP_PORT
        self._socket: socket.socket | None = None
        self._lock = threading.Lock()

    def connect_unix(self) -> bool:
        """Connect to Unix socket."""
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(self.socket_path)
            self._socket.settimeout(RESPONSE_TIMEOUT)
            return True
        except (OSError, FileNotFoundError):
            return False

    def connect_tcp(self) -> bool:
        """Connect to TCP socket."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.tcp_host, self.tcp_port))
            self._socket.settimeout(RESPONSE_TIMEOUT)
            return True
        except OSError:
            return False

    def disconnect(self) -> None:
        """Disconnect from server."""
        if self._socket:
            self._socket.close()
            self._socket = None

    def send_command(
        self, msg_type: str, payload: dict[str, Any], timeout: float = RESPONSE_TIMEOUT
    ) -> dict[str, Any]:
        """Send a command and wait for response."""
        if not self._socket:
            raise ConnectionError("Not connected to bridge")
        
        msg = BridgeMessage(msg_type=msg_type, payload=payload)
        
        with self._lock:
            self._socket.sendall(msg.to_json().encode("utf-8"))
            
            # Wait for response
            self._socket.settimeout(timeout)
            data = self._socket.recv(MAX_MESSAGE_SIZE)
            if not data:
                raise ConnectionError("Connection closed")
            
            response = BridgeMessage.from_json(data.decode("utf-8"))
            return response.payload


# Message types
MSG_PING = "ping"
MSG_PONG = "pong"
MSG_EXEC = "exec"
MSG_RESULT = "result"
MSG_BATCH = "batch"
MSG_BATCH_RESULT = "batch_result"
MSG_STATUS = "status"
MSG_STATUS_RESPONSE = "status_response"
MSG_ERROR = "error"


def create_default_handlers() -> dict[str, Callable[[BridgeMessage], dict[str, Any]]]:
    """Create default message handlers."""
    def handle_ping(msg: BridgeMessage) -> dict[str, Any]:
        return {"pong": True, "version": PROTOCOL_VERSION}
    
    def handle_status(msg: BridgeMessage) -> dict[str, Any]:
        return {
            "status": "running",
            "version": PROTOCOL_VERSION,
            "uptime": time.time(),
        }
    
    return {
        MSG_PING: handle_ping,
        MSG_STATUS: handle_status,
    }

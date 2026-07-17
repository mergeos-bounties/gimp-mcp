"""Tests for the plugin bridge socket protocol."""

from __future__ import annotations

import socket
import time

from gimp_mcp.bridge import (
    BridgeClient,
    BridgeMessage,
    BridgeProtocol,
    MSG_PING,
    MSG_EXEC,
    MSG_BATCH,
    MSG_STATUS,
    PROTOCOL_VERSION,
    create_default_handlers,
)


def _get_free_port() -> int:
    """Get a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class TestBridgeMessage:
    """Test BridgeMessage class."""

    def test_create_message(self):
        msg = BridgeMessage(msg_type="test", payload={"key": "value"})
        assert msg.msg_type == "test"
        assert msg.payload == {"key": "value"}
        assert msg.msg_id is not None
        assert msg.timestamp > 0

    def test_to_dict(self):
        msg = BridgeMessage(msg_type="test", payload={"key": "value"})
        d = msg.to_dict()
        assert d["type"] == "test"
        assert d["payload"] == {"key": "value"}
        assert d["version"] == PROTOCOL_VERSION
        assert "id" in d
        assert "timestamp" in d

    def test_from_dict(self):
        data = {
            "type": "test",
            "payload": {"key": "value"},
            "id": "test-id",
            "timestamp": 1234567890,
        }
        msg = BridgeMessage.from_dict(data)
        assert msg.msg_type == "test"
        assert msg.payload == {"key": "value"}
        assert msg.msg_id == "test-id"

    def test_json_roundtrip(self):
        msg = BridgeMessage(msg_type="test", payload={"key": "value"})
        json_str = msg.to_json()
        msg2 = BridgeMessage.from_json(json_str)
        assert msg2.msg_type == msg.msg_type
        assert msg2.payload == msg.payload
        assert msg2.msg_id == msg.msg_id


class TestBridgeProtocol:
    """Test BridgeProtocol class."""

    def test_register_handler(self):
        protocol = BridgeProtocol()

        def handler(msg):
            return {"ok": True}

        protocol.register_handler("test", handler)
        assert "test" in protocol._handlers

    def test_process_message(self):
        protocol = BridgeProtocol()

        def handler(msg):
            return {"ok": True, "type": msg.msg_type}

        protocol.register_handler("test", handler)

        msg = BridgeMessage(msg_type="test", payload={})
        result = protocol._process_message(msg)
        assert result["ok"] is True
        assert result["type"] == "test"

    def test_process_unknown_message(self):
        protocol = BridgeProtocol()
        msg = BridgeMessage(msg_type="unknown", payload={})
        result = protocol._process_message(msg)
        assert "error" in result


class TestBridgeServerClient:
    """Test server and client integration using TCP sockets."""

    def test_tcp_socket_communication(self):
        port = _get_free_port()
        server = BridgeProtocol(tcp_port=port)

        def handle_ping(msg):
            return {"pong": True, "version": PROTOCOL_VERSION}

        server.register_handler(MSG_PING, handle_ping)
        server.start_tcp()

        try:
            time.sleep(0.1)

            client = BridgeClient(tcp_port=port)
            assert client.connect_tcp() is True

            response = client.send_command(MSG_PING, {})
            assert response["pong"] is True
            assert response["version"] == PROTOCOL_VERSION

            client.disconnect()
        finally:
            server.stop()

    def test_exec_operation(self):
        port = _get_free_port()
        server = BridgeProtocol(tcp_port=port)

        def handle_exec(msg):
            op = msg.payload.get("op")
            params = msg.payload.get("params", {})
            return {"ok": True, "op": op, "params": params}

        server.register_handler(MSG_EXEC, handle_exec)
        server.start_tcp()

        try:
            time.sleep(0.1)

            client = BridgeClient(tcp_port=port)
            assert client.connect_tcp() is True

            response = client.send_command(
                MSG_EXEC,
                {"op": "resize", "params": {"width": 100, "height": 100}},
            )
            assert response["ok"] is True
            assert response["op"] == "resize"
            assert response["params"]["width"] == 100

            client.disconnect()
        finally:
            server.stop()

    def test_batch_operation(self):
        port = _get_free_port()
        server = BridgeProtocol(tcp_port=port)

        def handle_batch(msg):
            operations = msg.payload.get("operations", [])
            results = [{"op": op.get("op"), "ok": True} for op in operations]
            return {"ok": True, "results": results}

        server.register_handler(MSG_BATCH, handle_batch)
        server.start_tcp()

        try:
            time.sleep(0.1)

            client = BridgeClient(tcp_port=port)
            assert client.connect_tcp() is True

            response = client.send_command(
                MSG_BATCH,
                {
                    "operations": [
                        {"op": "resize", "params": {"width": 100}},
                        {"op": "crop", "params": {"x": 0, "y": 0}},
                    ]
                },
            )
            assert response["ok"] is True
            assert len(response["results"]) == 2

            client.disconnect()
        finally:
            server.stop()

    def test_multiple_clients(self):
        port = _get_free_port()
        server = BridgeProtocol(tcp_port=port)

        def handle_ping(msg):
            return {"pong": True}

        server.register_handler(MSG_PING, handle_ping)
        server.start_tcp()

        try:
            time.sleep(0.1)

            clients = []
            for _ in range(3):
                client = BridgeClient(tcp_port=port)
                assert client.connect_tcp() is True
                clients.append(client)

            for client in clients:
                response = client.send_command(MSG_PING, {})
                assert response["pong"] is True

            for client in clients:
                client.disconnect()
        finally:
            server.stop()

    def test_message_id_matching(self):
        port = _get_free_port()
        server = BridgeProtocol(tcp_port=port)

        def handle_ping(msg):
            return {"pong": True, "echo_id": msg.msg_id}

        server.register_handler(MSG_PING, handle_ping)
        server.start_tcp()

        try:
            time.sleep(0.1)

            client = BridgeClient(tcp_port=port)
            assert client.connect_tcp() is True

            msg = BridgeMessage(msg_type=MSG_PING, payload={})
            response = client._socket.sendall(msg.to_json().encode("utf-8"))
            data = client._socket.recv(10 * 1024 * 1024)
            response = BridgeMessage.from_json(data.decode("utf-8"))

            assert response.msg_id == msg.msg_id
            assert response.payload["echo_id"] == msg.msg_id

            client.disconnect()
        finally:
            server.stop()


class TestDefaultHandlers:
    """Test default handlers."""

    def test_ping_handler(self):
        handlers = create_default_handlers()
        ping_handler = handlers[MSG_PING]

        msg = BridgeMessage(msg_type=MSG_PING, payload={})
        result = ping_handler(msg)

        assert result["pong"] is True
        assert result["version"] == PROTOCOL_VERSION

    def test_status_handler(self):
        handlers = create_default_handlers()
        status_handler = handlers[MSG_STATUS]

        msg = BridgeMessage(msg_type=MSG_STATUS, payload={})
        result = status_handler(msg)

        assert result["status"] == "running"
        assert result["version"] == PROTOCOL_VERSION
        assert "uptime" in result

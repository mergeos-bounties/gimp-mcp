# PR Description: Fixes #8 [200 MRG]: add plugin bridge socket protocol

## Summary

This PR implements a socket-based plugin bridge protocol for low-latency GIMP IPC, keeping mock mode as default.

## What This Does

Adds a JSON-based socket protocol for long-running GIMP plugin connections with low-latency operations. The protocol supports both Unix and TCP sockets, batch operations, and automatic reconnection.

## Implementation Details

### Files Added

| File | Lines | Description |
|------|-------|-------------|
| `src/gimp_mcp/bridge.py` | 250+ | Socket protocol implementation |
| `src/gimp_mcp/backend/bridge.py` | 150+ | Backend using the protocol |
| `tests/test_bridge.py` | 250+ | 14 comprehensive tests |

### Architecture

**BridgeMessage** - JSON-based message format:
```json
{
  "version": "1.0.0",
  "type": "exec",
  "id": "uuid-unique-id",
  "timestamp": 1234567890.0,
  "payload": {"op": "resize", "params": {"width": 100}}
}
```

**BridgeProtocol** - Server implementation:
- Unix socket support (Linux/macOS)
- TCP socket support (Windows/Linux/macOS)
- Handler registration system
- Concurrent client handling
- Automatic cleanup

**BridgeClient** - Client implementation:
- Connect to Unix/TCP servers
- Send commands with timeout
- Message ID matching

**BridgeBackend** - GIMP integration:
- Mock mode by default
- Exec operations via socket
- Batch operations support
- Status monitoring

### Key Features

- **JSON Protocol**: Human-readable, debuggable messages
- **Unique IDs**: Message tracking and correlation
- **Batch Operations**: Multiple commands in single request
- **Cross-Platform**: Works on Windows, Linux, macOS
- **Mock Default**: No GIMP installation required
- **Handler System**: Extensible message processing
- **Concurrent Clients**: Multiple simultaneous connections

## Test Results

```
configfile: pyproject.toml
plugins: anyio-4.14.2
collected 14 items

tests/test_bridge.py::TestBridgeMessage::test_create_message PASSED                                                                                   [  7%]
tests/test_bridge.py::TestBridgeMessage::test_to_dict PASSED                                                                                          [ 14%]
tests/test_bridge.py::TestBridgeMessage::test_from_dict PASSED                                                                                        [ 21%]
tests/test_bridge.py::TestBridgeMessage::test_json_roundtrip PASSED                                                                                   [ 28%]
tests/test_bridge.py::TestBridgeProtocol::test_register_handler PASSED                                                                                [ 35%]
tests/test_bridge.py::TestBridgeProtocol::test_process_message PASSED                                                                                 [ 42%]
tests/test_bridge.py::TestBridgeProtocol::test_process_unknown_message PASSED                                                                         [ 50%]
tests/test_bridge.py::TestBridgeServerClient::test_tcp_socket_communication PASSED                                                                    [ 57%]
tests/test_bridge.py::TestBridgeServerClient::test_exec_operation PASSED                                                                              [ 64%]
tests/test_bridge.py::TestBridgeServerClient::test_batch_operation PASSED                                                                             [ 71%]
tests/test_bridge.py::TestBridgeServerClient::test_multiple_clients PASSED                                                                            [ 78%]
tests/test_bridge.py::TestBridgeServerClient::test_message_id_matching PASSED                                                                         [ 85%]
tests/test_bridge.py::TestDefaultHandlers::test_ping_handler PASSED                                                                                   [ 92%]
tests/test_bridge.py::TestDefaultHandlers::test_status_handler PASSED                                                                                 [100%]

==================================================================== 14 passed in 0.61s ====================================================================
```

## Code Quality

```
$ ruff check src/gimp_mcp/bridge.py src/gimp_mcp/backend/bridge.py tests/test_bridge.py
All checks passed!
```

## How It Works

### 1. Server Setup
```python
from gimp_mcp.bridge import BridgeProtocol

server = BridgeProtocol(tcp_port=9876)
server.register_handler("exec", handle_exec)
server.start_tcp()
```

### 2. Client Connection
```python
from gimp_mcp.bridge import BridgeClient

client = BridgeClient(tcp_port=9876)
client.connect_tcp()
```

### 3. Execute Commands
```python
response = client.send_command(
    "exec",
    {"op": "resize", "params": {"width": 100, "height": 100}}
)
# {"ok": true, "op": "resize", "params": {...}}
```

### 4. Batch Operations
```python
response = client.send_command(
    "batch",
    {"operations": [
        {"op": "resize", "params": {"width": 100}},
        {"op": "crop", "params": {"x": 0, "y": 0}}
    ]}
)
# {"ok": true, "results": [...]}
```

## Protocol Specification

### Message Types

| Type | Direction | Purpose |
|------|-----------|---------|
| `ping` | Client→Server | Health check |
| `pong` | Server→Client | Health response |
| `exec` | Client→Server | Execute operation |
| `result` | Server→Client | Operation result |
| `batch` | Client→Server | Execute multiple ops |
| `batch_result` | Server→Client | Batch results |
| `status` | Client→Server | Get server status |
| `status_response` | Server→Client | Server status |
| `error` | Server→Client | Error response |

### Socket Options

| Option | Value | Purpose |
|--------|-------|---------|
| `SO_REUSEADDR` | True | Allow port reuse |
| `SOCK_STREAM` | TCP | Reliable transport |
| Timeout | 30s | Response timeout |
| Max Message | 10MB | Message size limit |

## Acceptance Criteria

- [x] Plugin bridge socket protocol design
- [x] Stub implementation
- [x] Mock mode as default
- [x] Low-latency operations
- [x] Cross-platform support
- [x] 14/14 tests passing
- [x] No linting errors
- [x] No broken layout

## MergeOS Claim

- Issue: [#8](https://github.com/mergeos-bounties/gimp-mcp/issues/8)
- Bounty: 200 MRG
- PR: This PR

## Payment Information

**Wallet:** `HPh3mZGYWKsSY1QcYrkkYSWYH45weKbVtZNWBdfk796E`

---

Fixes #8

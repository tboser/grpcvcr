# grpcvr

[![CI](https://github.com/tboser/grpcvr/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/grpcvr/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/grpcvr.svg)](https://badge.fury.io/py/grpcvr)
[![Python versions](https://img.shields.io/pypi/pyversions/grpcvr.svg)](https://pypi.org/project/grpcvr/)

**Record and replay gRPC interactions for testing** - like [VCR.py](https://vcrpy.readthedocs.io/) but for gRPC/HTTP2.

## Installation

```bash
pip install grpcvr
```

## Quick Start

```python
from grpcvr import recorded_channel

# Record on first run, replay on subsequent runs
with recorded_channel("tests/cassettes/my_test.yaml", "localhost:50051") as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
    assert response.name == "Alice"
```

## Features

- **Record & Replay**: Automatically record gRPC interactions and replay them in tests
- **All RPC Types**: Supports unary, server streaming, client streaming, and bidirectional streaming
- **Async Support**: Full support for `grpc.aio` async clients
- **pytest Integration**: Built-in fixtures and markers for easy test integration
- **Flexible Matching**: Match requests by method, metadata, body, or custom logic
- **Multiple Formats**: Store cassettes as YAML or JSON

## Recording Modes

| Mode | Description |
|------|-------------|
| `NEW_EPISODES` | Play existing, record new (default) |
| `NONE` | Playback only - fail if no match |
| `ALL` | Always record, overwrite existing |
| `ONCE` | Record if cassette missing, then playback |

## pytest Integration

```python
import pytest
from grpcvr import RecordMode

@pytest.mark.grpcvr(cassette="user_test.yaml", record_mode=RecordMode.NONE)
def test_get_user(grpcvr_cassette):
    from grpcvr import RecordingChannel

    with RecordingChannel(grpcvr_cassette, "localhost:50051") as rc:
        stub = MyServiceStub(rc.channel)
        response = stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

Run in record mode:
```bash
pytest --grpcvr-record=new_episodes
```

Run in strict playback mode (CI):
```bash
pytest --grpcvr-record=none
```

## Request Matching

```python
from grpcvr import recorded_channel, MethodMatcher, RequestMatcher, MetadataMatcher

# Match on method + request body
matcher = MethodMatcher() & RequestMatcher()

with recorded_channel("test.yaml", "localhost:50051", match_on=matcher) as channel:
    ...

# Ignore certain metadata keys
matcher = MethodMatcher() & MetadataMatcher(ignore_keys=["x-request-id"])
```

## License

MIT

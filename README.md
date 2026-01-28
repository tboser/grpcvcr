# grpcvcr

[![CI](https://github.com/tboser/grpcvcr/actions/workflows/ci.yml/badge.svg)](https://github.com/tboser/grpcvcr/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tboser/grpcvcr/graph/badge.svg)](https://codecov.io/gh/tboser/grpcvcr)
[![Documentation](https://readthedocs.org/projects/grpcvcr/badge/?version=latest)](https://grpcvcr.readthedocs.io)
[![PyPI version](https://img.shields.io/pypi/v/grpcvcr.svg)](https://pypi.org/project/grpcvcr/)
[![Python versions](https://img.shields.io/pypi/pyversions/grpcvcr.svg)](https://pypi.org/project/grpcvcr/)

**Record and replay gRPC interactions for testing** - like [VCR.py](https://vcrpy.readthedocs.io/) but for gRPC.

## Installation

```bash
pip install grpcvcr
```

## Quick Start

```python
from grpcvcr import recorded_channel, RecordMode

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

## Async Support

```python
from grpcvcr import AsyncRecordingChannel, Cassette, RecordMode

cassette = Cassette("test.yaml", record_mode=RecordMode.ALL)

async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
    stub = MyServiceStub(recording.channel)
    response = await stub.GetUser(GetUserRequest(id=1))
```

## pytest Integration

```python
import pytest
from grpcvcr import RecordMode

@pytest.mark.grpcvcr(cassette="user_test.yaml", record_mode=RecordMode.NONE)
def test_get_user(grpcvcr_cassette):
    from grpcvcr import RecordingChannel

    with RecordingChannel(grpcvcr_cassette, "localhost:50051") as rc:
        stub = MyServiceStub(rc.channel)
        response = stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

Run in record mode:

```bash
pytest --grpcvcr-record=new_episodes
```

Run in strict playback mode (CI):

```bash
pytest --grpcvcr-record=none
```

## Request Matching

```python
from grpcvcr import recorded_channel, MethodMatcher, RequestMatcher, MetadataMatcher

# Match on method + request body
matcher = MethodMatcher() & RequestMatcher()

with recorded_channel("test.yaml", "localhost:50051", match_on=matcher) as channel:
    ...

# Ignore certain metadata keys
matcher = MethodMatcher() & MetadataMatcher(ignore_keys=["x-request-id"])
```

## License

MIT

# grpcvcr

**Record and replay gRPC interactions for testing** - like VCR.py but for gRPC/HTTP2.

## What is grpcvcr?

grpcvcr is a testing library that records your gRPC client interactions and replays them during subsequent test runs. This enables:

- **Fast tests**: No network calls during replay
- **Deterministic tests**: Same responses every time
- **Offline development**: Work without access to remote services
- **CI/CD friendly**: No need for live services in pipelines

## Quick Example

```python test="skip"
from grpcvcr import recorded_channel

from myservice_pb2 import GetUserRequest
from myservice_pb2_grpc import UserServiceStub

# First run: records the interaction
# Subsequent runs: replays from cassette
with recorded_channel("tests/cassettes/user_test.yaml", "localhost:50051") as channel:
    stub = UserServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
    assert response.name == "Alice"
```

## Key Features

- **All RPC types**: Unary, server streaming, client streaming, bidirectional
- **Async support**: Full `grpc.aio` compatibility
- **Flexible matching**: Match by method, metadata, body, or custom logic
- **pytest integration**: Built-in fixtures and markers
- **Multiple formats**: YAML or JSON cassette storage

## Installation

```bash test="skip"
pip install grpcvcr
```

## Next Steps

- [Installation Guide](installation.md) - Detailed setup instructions
- [Quick Start](quickstart.md) - Get up and running in minutes
- [Concepts](concepts/cassettes.md) - Understand how grpcvcr works

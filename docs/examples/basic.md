# Basic Usage

This page covers common usage patterns for grpcvr.

## Recording and Playback

The simplest way to use grpcvr is with the `recorded_channel` context manager:

```python
from grpcvr import recorded_channel

# First run: records interactions to cassette
with recorded_channel("tests/cassettes/my_test.yaml", "localhost:50051") as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
    assert response.name == "Alice"

# Subsequent runs: plays back from cassette (no server needed)
```

## Record Modes

Control recording behavior with `RecordMode`:

```python
from grpcvr import recorded_channel, RecordMode

# NONE - Playback only, fail if no match (use in CI)
with recorded_channel("test.yaml", target, record_mode=RecordMode.NONE) as channel:
    ...

# NEW_EPISODES - Play existing, record new (default)
with recorded_channel("test.yaml", target, record_mode=RecordMode.NEW_EPISODES) as channel:
    ...

# ALL - Always record, overwrite existing
with recorded_channel("test.yaml", target, record_mode=RecordMode.ALL) as channel:
    ...

# ONCE - Record if cassette missing, then playback only
with recorded_channel("test.yaml", target, record_mode=RecordMode.ONCE) as channel:
    ...
```

## Using the Cassette Directly

For more control, use `Cassette` and `RecordingChannel` directly:

```python
from grpcvr import Cassette, RecordingChannel, RecordMode

cassette = Cassette(
    path="tests/cassettes/my_test.yaml",
    record_mode=RecordMode.NEW_EPISODES,
)

channel = RecordingChannel(cassette, "localhost:50051")
stub = MyServiceStub(channel.channel)

response = stub.GetUser(GetUserRequest(id=1))

channel.close()  # Saves the cassette
```

## pytest Integration

grpcvr includes a pytest plugin for automatic cassette management:

```python
import pytest
from grpcvr import RecordingChannel

@pytest.fixture
def grpc_target():
    return "localhost:50051"

def test_get_user(cassette, grpc_target):
    """Cassette is automatically named after the test."""
    channel = RecordingChannel(cassette, grpc_target)
    stub = MyServiceStub(channel.channel)

    response = stub.GetUser(GetUserRequest(id=1))
    assert response.name == "Alice"

    channel.close()
```

Use markers to customize cassette behavior:

```python
from grpcvr import RecordMode

@pytest.mark.grpcvr("custom_cassette.yaml", record_mode=RecordMode.ALL)
def test_with_custom_cassette(cassette, grpc_target):
    ...
```

## Async Support

For async gRPC clients, use `AsyncRecordingChannel`:

```python
import asyncio
from grpcvr import Cassette, RecordMode
from grpcvr.channel import AsyncRecordingChannel

async def main():
    cassette = Cassette("test.yaml")

    async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
        stub = MyServiceStub(recording.channel)
        response = await stub.GetUser(GetUserRequest(id=1))
        print(response.name)

asyncio.run(main())
```

## Streaming RPCs

grpcvr supports all gRPC streaming patterns:

### Server Streaming

```python
with recorded_channel("test.yaml", target) as channel:
    stub = MyServiceStub(channel)

    for user in stub.ListUsers(ListUsersRequest(limit=10)):
        print(user.name)
```

### Client Streaming

```python
def request_generator():
    yield CreateUserRequest(name="Alice", email="alice@example.com")
    yield CreateUserRequest(name="Bob", email="bob@example.com")

with recorded_channel("test.yaml", target) as channel:
    stub = MyServiceStub(channel)
    response = stub.CreateUsers(request_generator())
    print(f"Created {response.created_count} users")
```

### Bidirectional Streaming

```python
def chat_messages():
    yield ChatMessage(sender="User", content="Hello")
    yield ChatMessage(sender="User", content="How are you?")

with recorded_channel("test.yaml", target) as channel:
    stub = MyServiceStub(channel)

    for response in stub.Chat(chat_messages()):
        print(f"{response.sender}: {response.content}")
```

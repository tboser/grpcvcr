# Basic Usage

Common patterns for using grpcvcr in your projects.

## Recording and Playback

```python test="skip"
from grpcvcr import recorded_channel

# First run: records interactions to cassette
with recorded_channel("tests/cassettes/my_test.yaml", "localhost:50051") as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
    assert response.name == "Alice"
```

## Record Modes

```python test="skip"
from grpcvcr import RecordMode, recorded_channel

target = "localhost:50051"

# NONE - Playback only, fail if no match (use in CI)
with recorded_channel("test.yaml", target, record_mode=RecordMode.NONE) as channel:
    ...

# NEW_EPISODES - Play existing, record new (default)
with recorded_channel(
    "test.yaml", target, record_mode=RecordMode.NEW_EPISODES
) as channel:
    ...

# ALL - Always record, overwrite existing
with recorded_channel("test.yaml", target, record_mode=RecordMode.ALL) as channel:
    ...
```

## Manual Channel Management

```python test="skip"
from grpcvcr import Cassette, RecordingChannel

cassette = Cassette("tests/cassettes/test.yaml")
channel = RecordingChannel(cassette, "localhost:50051")
stub = MyServiceStub(channel.channel)

response = stub.GetUser(GetUserRequest(id=1))

channel.close()  # Saves the cassette
```

## pytest Integration

```python test="skip"
import pytest

from grpcvcr import RecordingChannel


@pytest.fixture
def grpc_target():
    return "localhost:50051"


def test_get_user(cassette, grpc_target):
    """Cassette is automatically named after the test."""
    channel = RecordingChannel(cassette, grpc_target)
    stub = MyServiceStub(channel.channel)
```

Custom cassette configuration:

```python test="skip"
from grpcvcr import RecordMode


@pytest.mark.grpcvcr("custom_cassette.yaml", record_mode=RecordMode.ALL)
def test_with_custom_cassette(cassette, grpc_target):
    ...
```

## Async Support

```python test="skip"
import asyncio

from grpcvcr import Cassette
from grpcvcr.channel import AsyncRecordingChannel


async def main():
    cassette = Cassette("test.yaml")

    async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
        stub = MyServiceStub(recording.channel)
        response = await stub.GetUser(GetUserRequest(id=1))
        print(response.name)


asyncio.run(main())
```

## Streaming RPCs

### Server Streaming

```python test="skip"
from grpcvcr import recorded_channel

target = "localhost:50051"

with recorded_channel("test.yaml", target) as channel:
    stub = MyServiceStub(channel)

    for user in stub.ListUsers(ListUsersRequest(limit=10)):
        print(user.name)
```

### Client Streaming

```python test="skip"
from grpcvcr import recorded_channel

target = "localhost:50051"


def request_generator():
    yield CreateUserRequest(name="Alice", email="alice@example.com")
    yield CreateUserRequest(name="Bob", email="bob@example.com")


with recorded_channel("test.yaml", target) as channel:
    stub = MyServiceStub(channel)
    response = stub.CreateUsers(request_generator())
    print(f"Created {response.created_count} users")
```

### Bidirectional Streaming

```python test="skip"
from grpcvcr import recorded_channel

target = "localhost:50051"


def chat_messages():
    yield ChatMessage(sender="User", content="Hello")
    yield ChatMessage(sender="User", content="How are you?")


with recorded_channel("test.yaml", target) as channel:
    stub = MyServiceStub(channel)

    for response in stub.Chat(chat_messages()):
        print(f"{response.sender}: {response.content}")
```

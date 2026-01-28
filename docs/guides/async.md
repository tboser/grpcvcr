# Async Usage

grpcvcr fully supports async gRPC with `grpc.aio`.

## Basic Async Usage

Use `AsyncRecordingChannel` for async gRPC clients:

```python
import asyncio

from grpcvcr import Cassette, RecordMode
from grpcvcr.channel import AsyncRecordingChannel


async def main():
    cassette = Cassette("test.yaml", record_mode=RecordMode.NEW_EPISODES)

    async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        response = await stub.GetUser(GetUserRequest(id=1))
        print(response.name)


asyncio.run(main())
```

## Async Streaming

All streaming patterns work with async:

### Server Streaming

```python
async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
    stub = UserServiceStub(recording.channel)
    async for user in stub.ListUsers(ListUsersRequest(limit=10)):
        print(user.name)
```

### Client Streaming

```python
async def request_iterator():
    for name in ["Alice", "Bob"]:
        yield CreateUserRequest(name=name)


async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
    stub = UserServiceStub(recording.channel)
    response = await stub.CreateUsers(request_iterator())
```

### Bidirectional Streaming

```python
async def chat_messages():
    yield ChatMessage(text="Hello")
    yield ChatMessage(text="World")


async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
    stub = ChatServiceStub(recording.channel)
    async for response in stub.Chat(chat_messages()):
        print(response.text)
```

## pytest-asyncio Integration

Use with pytest-asyncio for async tests:

```python
import pytest

from grpcvcr.channel import AsyncRecordingChannel


@pytest.mark.asyncio
async def test_async_get_user(grpcvcr_cassette):
    async with AsyncRecordingChannel(grpcvcr_cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        response = await stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

## Async Channel Factory Fixture

Use the provided fixture for async channels:

```python
@pytest.mark.asyncio
async def test_with_factory(grpcvcr_cassette, grpcvcr_async_channel_factory):
    async with grpcvcr_async_channel_factory(
        grpcvcr_cassette, "localhost:50051"
    ) as recording:
        stub = UserServiceStub(recording.channel)
        response = await stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

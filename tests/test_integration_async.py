"""Async integration tests for gRPC recording and playback."""

from __future__ import annotations

from pathlib import Path

import pytest

from grpcvcr import (
    AsyncRecordingChannel,
    Cassette,
    MethodMatcher,
    RecordMode,
    RequestMatcher,
    async_recorded_channel,
)
from grpcvcr.errors import RecordingDisabledError


@pytest.mark.asyncio
class TestAsyncUnaryRecordingPlayback:
    """Test async unary RPC recording and playback."""

    async def test_record_unary_call(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record an async unary RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = await stub.GetUser(pb2.GetUserRequest(id=42))

        assert response.user.id == 42
        assert response.user.name == "User 42"
        assert grpc_servicer.call_count == 1
        assert tmp_cassette_path.exists()
        assert len(cassette.interactions) == 1

    async def test_playback_unary_call(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record then playback an async unary RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            await stub.GetUser(pb2.GetUserRequest(id=42))

        assert grpc_servicer.call_count == 1

        grpc_servicer.call_count = 0
        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = await stub.GetUser(pb2.GetUserRequest(id=42))

        assert response.user.id == 42
        assert grpc_servicer.call_count == 0

    async def test_async_recorded_channel_context_manager(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Test the async_recorded_channel convenience function."""
        with async_recorded_channel(tmp_cassette_path, grpc_target, record_mode=RecordMode.ALL) as channel:
            stub = pb2_grpc.TestServiceStub(channel)
            response = await stub.GetUser(pb2.GetUserRequest(id=1))

        assert response.user.id == 1
        assert grpc_servicer.call_count == 1
        assert tmp_cassette_path.exists()


@pytest.mark.asyncio
class TestAsyncRecordModes:
    """Test different recording modes with async channels."""

    async def test_none_mode_raises_on_missing_interaction(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """NONE mode raises when interaction not found."""
        matcher = MethodMatcher() & RequestMatcher()
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL, match_on=matcher)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            await stub.GetUser(pb2.GetUserRequest(id=1))

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE, match_on=matcher)
        with pytest.raises(RecordingDisabledError):
            async with AsyncRecordingChannel(cassette2, grpc_target) as recording:
                stub = pb2_grpc.TestServiceStub(recording.channel)
                await stub.GetUser(pb2.GetUserRequest(id=999))

    async def test_new_episodes_mode_records_new(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """NEW_EPISODES mode records new interactions."""
        matcher = MethodMatcher() & RequestMatcher()
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL, match_on=matcher)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            await stub.GetUser(pb2.GetUserRequest(id=1))

        assert grpc_servicer.call_count == 1

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES, match_on=matcher)
        async with AsyncRecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            await stub.GetUser(pb2.GetUserRequest(id=1))
            await stub.GetUser(pb2.GetUserRequest(id=2))

        assert grpc_servicer.call_count == 2
        assert len(cassette2.interactions) == 2


@pytest.mark.asyncio
class TestAsyncServerStreaming:
    """Test async server streaming RPC recording and playback."""

    async def test_record_server_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record an async server streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = []
            async for response in stub.ListUsers(pb2.ListUsersRequest(limit=3)):
                responses.append(response)

        assert len(responses) == 3
        assert responses[0].id == 1
        assert responses[2].id == 3
        assert grpc_servicer.call_count == 1
        assert len(cassette.interactions) == 1
        assert cassette.interactions[0].rpc_type == "server_streaming"

    async def test_playback_server_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Playback an async server streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            async for _ in stub.ListUsers(pb2.ListUsersRequest(limit=3)):
                pass

        grpc_servicer.call_count = 0

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = []
            async for response in stub.ListUsers(pb2.ListUsersRequest(limit=3)):
                responses.append(response)

        assert len(responses) == 3
        assert grpc_servicer.call_count == 0


@pytest.mark.asyncio
class TestAsyncClientStreaming:
    """Test async client streaming RPC recording and playback."""

    async def test_record_client_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record an async client streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        async def request_iterator():
            for name in ["Alice", "Bob", "Charlie"]:
                yield pb2.CreateUserRequest(name=name, email=f"{name.lower()}@example.com")

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = await stub.CreateUsers(request_iterator())

        assert response.created_count == 3
        assert grpc_servicer.call_count == 1
        assert len(cassette.interactions) == 1
        assert cassette.interactions[0].rpc_type == "client_streaming"

    async def test_playback_client_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Playback an async client streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        async def request_iterator():
            for name in ["Alice", "Bob", "Charlie"]:
                yield pb2.CreateUserRequest(name=name, email=f"{name.lower()}@example.com")

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            await stub.CreateUsers(request_iterator())

        grpc_servicer.call_count = 0

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = await stub.CreateUsers(request_iterator())

        assert response.created_count == 3
        assert grpc_servicer.call_count == 0


@pytest.mark.asyncio
class TestAsyncBidiStreaming:
    """Test async bidirectional streaming RPC recording and playback."""

    async def test_record_bidi_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record an async bidirectional streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        async def request_iterator():
            yield pb2.ChatMessage(sender="client", content="Hello", timestamp=1000)
            yield pb2.ChatMessage(sender="client", content="World", timestamp=2000)

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = []
            async for response in stub.Chat(request_iterator()):
                responses.append(response)

        assert len(responses) == 2
        assert responses[0].content == "Echo: Hello"
        assert responses[1].content == "Echo: World"
        assert grpc_servicer.call_count == 1
        assert len(cassette.interactions) == 1
        assert cassette.interactions[0].rpc_type == "bidi_streaming"

    async def test_playback_bidi_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Playback an async bidirectional streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        async def request_iterator():
            yield pb2.ChatMessage(sender="client", content="Hello", timestamp=1000)
            yield pb2.ChatMessage(sender="client", content="World", timestamp=2000)

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            async for _ in stub.Chat(request_iterator()):
                pass

        grpc_servicer.call_count = 0

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = []
            async for response in stub.Chat(request_iterator()):
                responses.append(response)

        assert len(responses) == 2
        assert grpc_servicer.call_count == 0

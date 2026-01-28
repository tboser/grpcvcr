"""Integration tests for gRPC recording and playback."""

from __future__ import annotations

from pathlib import Path

import pytest

from grpcvr import (
    Cassette,
    MethodMatcher,
    RecordingChannel,
    RecordMode,
    RequestMatcher,
    recorded_channel,
)
from grpcvr.errors import RecordingDisabledError


class TestUnaryRecordingPlayback:
    """Test unary RPC recording and playback."""

    def test_record_unary_call(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record a unary RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = stub.GetUser(pb2.GetUserRequest(id=42))

        assert response.user.id == 42
        assert response.user.name == "User 42"
        assert grpc_servicer.call_count == 1
        assert tmp_cassette_path.exists()
        assert len(cassette.interactions) == 1

    def test_playback_unary_call(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record then playback a unary RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=42))

        assert grpc_servicer.call_count == 1

        grpc_servicer.call_count = 0
        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = stub.GetUser(pb2.GetUserRequest(id=42))

        assert response.user.id == 42
        assert grpc_servicer.call_count == 0

    def test_recorded_channel_context_manager(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Test the recorded_channel convenience function."""
        with recorded_channel(tmp_cassette_path, grpc_target, record_mode=RecordMode.ALL) as channel:
            stub = pb2_grpc.TestServiceStub(channel)
            response = stub.GetUser(pb2.GetUserRequest(id=1))

        assert response.user.id == 1
        assert grpc_servicer.call_count == 1
        assert tmp_cassette_path.exists()


class TestRecordModes:
    """Test different recording modes."""

    def test_none_mode_raises_without_cassette(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        pb2,
        pb2_grpc,
    ) -> None:
        """NONE mode raises when cassette doesn't exist."""
        from grpcvr.errors import CassetteNotFoundError

        with pytest.raises(CassetteNotFoundError):
            Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)

    def test_none_mode_raises_on_missing_interaction(
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
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=1))

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE, match_on=matcher)
        with pytest.raises(RecordingDisabledError), RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=999))

    def test_new_episodes_mode_records_new(
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
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=1))

        assert grpc_servicer.call_count == 1

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES, match_on=matcher)
        with RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=1))
            stub.GetUser(pb2.GetUserRequest(id=2))

        assert grpc_servicer.call_count == 2
        assert len(cassette2.interactions) == 2

    def test_all_mode_overwrites(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """ALL mode always records, overwriting existing."""
        matcher = MethodMatcher() & RequestMatcher()
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL, match_on=matcher)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=1))

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL, match_on=matcher)
        with RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.GetUser(pb2.GetUserRequest(id=1))

        assert grpc_servicer.call_count == 2
        assert len(cassette2.interactions) == 1


class TestServerStreaming:
    """Test server streaming RPC recording and playback."""

    def test_record_server_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record a server streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = list(stub.ListUsers(pb2.ListUsersRequest(limit=3)))

        assert len(responses) == 3
        assert responses[0].id == 1
        assert responses[2].id == 3
        assert grpc_servicer.call_count == 1
        assert len(cassette.interactions) == 1
        assert cassette.interactions[0].rpc_type == "server_streaming"

    def test_playback_server_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Playback a server streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            list(stub.ListUsers(pb2.ListUsersRequest(limit=3)))

        grpc_servicer.call_count = 0

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = list(stub.ListUsers(pb2.ListUsersRequest(limit=3)))

        assert len(responses) == 3
        assert grpc_servicer.call_count == 0


class TestClientStreaming:
    """Test client streaming RPC recording and playback."""

    def test_record_client_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record a client streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        def request_iterator():
            for name in ["Alice", "Bob", "Charlie"]:
                yield pb2.CreateUserRequest(name=name, email=f"{name.lower()}@example.com")

        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = stub.CreateUsers(request_iterator())

        assert response.created_count == 3
        assert grpc_servicer.call_count == 1
        assert len(cassette.interactions) == 1
        assert cassette.interactions[0].rpc_type == "client_streaming"

    def test_playback_client_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Playback a client streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        def request_iterator():
            for name in ["Alice", "Bob", "Charlie"]:
                yield pb2.CreateUserRequest(name=name, email=f"{name.lower()}@example.com")

        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.CreateUsers(request_iterator())

        grpc_servicer.call_count = 0

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = stub.CreateUsers(request_iterator())

        assert response.created_count == 3
        assert grpc_servicer.call_count == 0


class TestBidiStreaming:
    """Test bidirectional streaming RPC recording and playback."""

    def test_record_bidi_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Record a bidirectional streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        def request_iterator():
            yield pb2.ChatMessage(sender="client", content="Hello", timestamp=1000)
            yield pb2.ChatMessage(sender="client", content="World", timestamp=2000)

        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = list(stub.Chat(request_iterator()))

        assert len(responses) == 2
        assert responses[0].content == "Echo: Hello"
        assert responses[1].content == "Echo: World"
        assert grpc_servicer.call_count == 1
        assert len(cassette.interactions) == 1
        assert cassette.interactions[0].rpc_type == "bidi_streaming"

    def test_playback_bidi_streaming(
        self,
        grpc_target: str,
        tmp_cassette_path: Path,
        grpc_servicer,
        pb2,
        pb2_grpc,
    ) -> None:
        """Playback a bidirectional streaming RPC call."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)

        def request_iterator():
            yield pb2.ChatMessage(sender="client", content="Hello", timestamp=1000)
            yield pb2.ChatMessage(sender="client", content="World", timestamp=2000)

        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            list(stub.Chat(request_iterator()))

        grpc_servicer.call_count = 0

        cassette2 = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(cassette2, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = list(stub.Chat(request_iterator()))

        assert len(responses) == 2
        assert grpc_servicer.call_count == 0

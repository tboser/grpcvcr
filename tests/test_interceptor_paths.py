"""Interceptor paths beyond the happy path: failed RPCs, playback without
recorded response types, and playback with recording disabled."""

from __future__ import annotations

from pathlib import Path

import grpc
import pytest
import yaml

from grpcvcr import Cassette, RecordingChannel, RecordMode
from grpcvcr.errors import RecordingDisabledError
from tests.conftest import FAIL_ID, FAIL_NAME


def strip_response_types(path: Path) -> None:
    """Drop `response_type` from every interaction, as a hand-written cassette would."""
    data = yaml.safe_load(path.read_text())
    for interaction in data["interactions"]:
        interaction["response"].pop("response_type", None)
    path.write_text(yaml.safe_dump(data))


def chat_messages(pb2, *contents: str):
    for content in contents:
        yield pb2.ChatMessage(sender="client", content=content, timestamp=1)


class TestFailedRpcRecording:
    """A failing RPC is recorded with its status code and replayed as a failure."""

    def test_unary_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                stub.GetUser(pb2.GetUserRequest(id=FAIL_ID))

        assert cassette.interactions[0].response.code == "NOT_FOUND"
        assert cassette.interactions[0].response.details == "user not found"

        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                stub.GetUser(pb2.GetUserRequest(id=FAIL_ID))

    def test_server_streaming_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                list(stub.ListUsers(pb2.ListUsersRequest(limit=FAIL_ID)))

        assert cassette.interactions[0].response.code == "INVALID_ARGUMENT"
        assert cassette.interactions[0].response.details == "limit must be positive"

    def test_client_streaming_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                stub.CreateUsers(iter([pb2.CreateUserRequest(name=FAIL_NAME, email="x@example.com")]))

        assert cassette.interactions[0].response.code == "INVALID_ARGUMENT"

    def test_bidi_streaming_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                list(stub.Chat(chat_messages(pb2, FAIL_NAME)))

        assert cassette.interactions[0].response.code == "INVALID_ARGUMENT"


class TestPlaybackWithoutRecordedResponseType:
    """Cassettes without `response_type` fall back to the request message type."""

    def test_unary(self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc) -> None:
        with (
            Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=7))
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            response = pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=7))

        assert response is not None
        assert grpc_servicer.call_count == 0

    def test_server_streaming(self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc) -> None:
        with (
            Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            list(pb2_grpc.TestServiceStub(recording.channel).ListUsers(pb2.ListUsersRequest(limit=2)))
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            responses = list(pb2_grpc.TestServiceStub(recording.channel).ListUsers(pb2.ListUsersRequest(limit=2)))

        assert len(responses) == 2
        assert grpc_servicer.call_count == 0

    def test_client_streaming(self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc) -> None:
        requests = [pb2.CreateUserRequest(name="A", email="a@example.com")]
        with (
            Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            pb2_grpc.TestServiceStub(recording.channel).CreateUsers(iter(requests))
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            response = pb2_grpc.TestServiceStub(recording.channel).CreateUsers(iter(requests))

        assert response is not None
        assert grpc_servicer.call_count == 0

    def test_bidi_streaming(self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc) -> None:
        with (
            Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            list(pb2_grpc.TestServiceStub(recording.channel).Chat(chat_messages(pb2, "hi")))
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            responses = list(pb2_grpc.TestServiceStub(recording.channel).Chat(chat_messages(pb2, "hi")))

        assert len(responses) == 1
        assert grpc_servicer.call_count == 0


class TestRecordingDisabledOnStreamingRpcs:
    """With recording disabled, an unmatched streaming call fails rather than hitting the network."""

    @pytest.fixture
    def recorded_cassette(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> Path:
        with (
            Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=1))
        return tmp_cassette_path

    def test_server_streaming(self, grpc_target: str, recorded_cassette: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded_cassette, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(RecordingDisabledError):
                list(stub.ListUsers(pb2.ListUsersRequest(limit=1)))

    def test_client_streaming(self, grpc_target: str, recorded_cassette: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded_cassette, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(RecordingDisabledError):
                stub.CreateUsers(iter([pb2.CreateUserRequest(name="A", email="a@example.com")]))

    def test_bidi_streaming(self, grpc_target: str, recorded_cassette: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded_cassette, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(RecordingDisabledError):
                list(stub.Chat(chat_messages(pb2, "hi")))

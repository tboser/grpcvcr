"""Async mirror of the non-happy-path interceptor tests."""

from __future__ import annotations

from pathlib import Path

import grpc
import pytest

from grpcvcr import AsyncRecordingChannel, Cassette, RecordMode
from grpcvcr.errors import RecordingDisabledError
from tests.conftest import FAIL_ID, FAIL_NAME
from tests.test_interceptor_paths import strip_response_types


async def chat_messages(pb2, *contents: str):
    for content in contents:
        yield pb2.ChatMessage(sender="client", content=content, timestamp=1)


@pytest.mark.asyncio
class TestAsyncFailedRpcRecording:
    async def test_unary_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                await stub.GetUser(pb2.GetUserRequest(id=FAIL_ID))

        assert cassette.interactions[0].response.code == "NOT_FOUND"
        assert cassette.interactions[0].response.details == "user not found"

        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                await stub.GetUser(pb2.GetUserRequest(id=FAIL_ID))

    async def test_server_streaming_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                [m async for m in stub.ListUsers(pb2.ListUsersRequest(limit=FAIL_ID))]

        assert cassette.interactions[0].response.code == "INVALID_ARGUMENT"

    async def test_client_streaming_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)

        async def requests():
            yield pb2.CreateUserRequest(name=FAIL_NAME, email="x@example.com")

        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                await stub.CreateUsers(requests())

        assert cassette.interactions[0].response.code == "INVALID_ARGUMENT"

    async def test_bidi_streaming_error(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                [m async for m in stub.Chat(chat_messages(pb2, FAIL_NAME))]

        assert cassette.interactions[0].response.code == "INVALID_ARGUMENT"


@pytest.mark.asyncio
class TestAsyncPlaybackWithoutRecordedResponseType:
    async def test_unary(self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc) -> None:
        with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
            async with AsyncRecordingChannel(cassette, grpc_target) as recording:
                await pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=7))
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            response = await pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=7))

        assert response is not None
        assert grpc_servicer.call_count == 0

    async def test_server_streaming(
        self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc
    ) -> None:
        with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
            async with AsyncRecordingChannel(cassette, grpc_target) as recording:
                stub = pb2_grpc.TestServiceStub(recording.channel)
                assert [m async for m in stub.ListUsers(pb2.ListUsersRequest(limit=2))] != []
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = [m async for m in stub.ListUsers(pb2.ListUsersRequest(limit=2))]

        assert len(responses) == 2
        assert grpc_servicer.call_count == 0

    async def test_client_streaming(
        self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc
    ) -> None:
        async def requests():
            yield pb2.CreateUserRequest(name="A", email="a@example.com")

        with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
            async with AsyncRecordingChannel(cassette, grpc_target) as recording:
                await pb2_grpc.TestServiceStub(recording.channel).CreateUsers(requests())
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            response = await pb2_grpc.TestServiceStub(recording.channel).CreateUsers(requests())

        assert response is not None
        assert grpc_servicer.call_count == 0

    async def test_bidi_streaming(
        self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc
    ) -> None:
        with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
            async with AsyncRecordingChannel(cassette, grpc_target) as recording:
                stub = pb2_grpc.TestServiceStub(recording.channel)
                assert [m async for m in stub.Chat(chat_messages(pb2, "hi"))] != []
        strip_response_types(tmp_cassette_path)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = [m async for m in stub.Chat(chat_messages(pb2, "hi"))]

        assert len(responses) == 1
        assert grpc_servicer.call_count == 0


@pytest.mark.asyncio
class TestAsyncRecordingDisabledOnStreamingRpcs:
    @pytest.fixture
    async def recorded_cassette(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> Path:
        with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
            async with AsyncRecordingChannel(cassette, grpc_target) as recording:
                await pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=1))
        return tmp_cassette_path

    async def test_server_streaming(self, grpc_target: str, recorded_cassette: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded_cassette, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(RecordingDisabledError):
                [m async for m in stub.ListUsers(pb2.ListUsersRequest(limit=1))]

    async def test_client_streaming(self, grpc_target: str, recorded_cassette: Path, pb2, pb2_grpc) -> None:
        async def requests():
            yield pb2.CreateUserRequest(name="A", email="a@example.com")

        playback = Cassette(recorded_cassette, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(RecordingDisabledError):
                await stub.CreateUsers(requests())

    async def test_bidi_streaming(self, grpc_target: str, recorded_cassette: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded_cassette, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(RecordingDisabledError):
                [m async for m in stub.Chat(chat_messages(pb2, "hi"))]

"""The call objects returned during playback, exercised through the stub API."""

from __future__ import annotations

from pathlib import Path

import grpc
import pytest

from grpcvcr import AsyncRecordingChannel, Cassette, RecordingChannel, RecordMode
from grpcvcr.interceptors.aio import _AsyncFakeStreamingCall
from tests.test_interceptor_paths import chat_messages, strip_response_types
from tests.test_interceptor_paths_async import chat_messages as async_chat_messages


@pytest.fixture
def recorded(grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> Path:
    """A cassette holding one unary and one server-streaming interaction."""
    with (
        Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
        RecordingChannel(cassette, grpc_target) as recording,
    ):
        stub = pb2_grpc.TestServiceStub(recording.channel)
        stub.GetUser(pb2.GetUserRequest(id=5))
        list(stub.ListUsers(pb2.ListUsersRequest(limit=2)))
    return tmp_cassette_path


@pytest.fixture
async def async_recorded(grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> Path:
    """The same cassette, recorded through the async channel."""
    with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            await stub.GetUser(pb2.GetUserRequest(id=5))
            [m async for m in stub.ListUsers(pb2.ListUsersRequest(limit=2))]
    return tmp_cassette_path


class TestSyncPlaybackCallMetadata:
    def test_unary_call_exposes_recorded_trailers(self, grpc_target: str, recorded: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            _response, call = stub.GetUser.with_call(pb2.GetUserRequest(id=5))

        assert dict(call.trailing_metadata())["x-trailer"] == "unary"
        assert call.initial_metadata() == ()

    def test_streaming_call_exposes_recorded_trailers(self, grpc_target: str, recorded: Path, pb2, pb2_grpc) -> None:
        playback = Cassette(recorded, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            call = stub.ListUsers(pb2.ListUsersRequest(limit=2))
            list(call)

        assert dict(call.trailing_metadata())["x-trailer"] == "server-stream"
        assert call.initial_metadata() == ()


@pytest.mark.asyncio
class TestAsyncPlaybackCallMetadata:
    async def test_unary_call_exposes_recorded_trailers(
        self, grpc_target: str, async_recorded: Path, pb2, pb2_grpc
    ) -> None:
        playback = Cassette(async_recorded, record_mode=RecordMode.NONE)
        done: list[object] = []
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            call = stub.GetUser(pb2.GetUserRequest(id=5))
            call.add_done_callback(done.append)
            await call
            trailers = await call.trailing_metadata()
            initial = await call.initial_metadata()

        assert dict(trailers)["x-trailer"] == "unary"
        assert initial == ()
        assert done == [call]


class TestPlaybackWithEmptyRequestStream:
    """A client-streaming replay with no requests has no message type to fall back on."""

    @pytest.fixture
    def typeless(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> Path:
        with (
            Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            stub = pb2_grpc.TestServiceStub(recording.channel)
            stub.CreateUsers(iter([pb2.CreateUserRequest(name="A", email="a@example.com")]))
            list(stub.Chat(chat_messages(pb2, "hi")))
        strip_response_types(tmp_cassette_path)
        return tmp_cassette_path

    @pytest.fixture
    async def async_typeless(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> Path:
        async def one_request():
            yield pb2.CreateUserRequest(name="A", email="a@example.com")

        with Cassette(tmp_cassette_path, record_mode=RecordMode.ALL) as cassette:
            async with AsyncRecordingChannel(cassette, grpc_target) as recording:
                stub = pb2_grpc.TestServiceStub(recording.channel)
                await stub.CreateUsers(one_request())
                [m async for m in stub.Chat(async_chat_messages(pb2, "hi"))]
        strip_response_types(tmp_cassette_path)
        return tmp_cassette_path

    def test_sync_client_streaming(self, grpc_target: str, typeless: Path, pb2_grpc) -> None:
        playback = Cassette(typeless, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            response = pb2_grpc.TestServiceStub(recording.channel).CreateUsers(iter([]))

        assert isinstance(response, bytes)

    def test_sync_bidi_streaming(self, grpc_target: str, typeless: Path, pb2_grpc) -> None:
        playback = Cassette(typeless, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            responses = list(pb2_grpc.TestServiceStub(recording.channel).Chat(iter([])))

        assert all(isinstance(m, bytes) for m in responses)

    @pytest.mark.asyncio
    async def test_async_client_streaming(self, grpc_target: str, async_typeless: Path, pb2_grpc) -> None:
        async def no_requests():
            return
            yield

        playback = Cassette(async_typeless, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            response = await pb2_grpc.TestServiceStub(recording.channel).CreateUsers(no_requests())

        assert isinstance(response, bytes)

    @pytest.mark.asyncio
    async def test_async_bidi_streaming(self, grpc_target: str, async_typeless: Path, pb2_grpc) -> None:
        async def no_requests():
            return
            yield

        playback = Cassette(async_typeless, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            responses = [m async for m in stub.Chat(no_requests())]

        assert all(isinstance(m, bytes) for m in responses)


class TestAsyncStreamingFakeCall:
    """The async streaming fake.

    grpc's own `InterceptedStreamStreamCall` wrapper leaves `_call` unset when an
    interceptor short-circuits, so these accessors are unreachable through the stub
    API and are covered directly.
    """

    @pytest.mark.asyncio
    async def test_exposes_recorded_trailers(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(("x-trailer", "server-stream"),),
        )

        assert dict(await call.trailing_metadata())["x-trailer"] == "server-stream"
        assert await call.initial_metadata() == ()

    def test_done_callback_fires_immediately(self) -> None:
        call = _AsyncFakeStreamingCall(messages=[], code=grpc.StatusCode.OK, details=None, trailing_metadata=())
        fired: list[object] = []

        call.add_done_callback(fired.append)

        assert fired == [call]

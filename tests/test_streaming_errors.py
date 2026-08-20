"""A failed streaming RPC must surface as an error, not as a short stream.

Without grpcvcr a failing server-streaming or bidi call raises `grpc.RpcError`
carrying the status code. Recording or replaying it must not change that.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import grpc
import pytest

from grpcvcr import AsyncRecordingChannel, Cassette, RecordingChannel, RecordMode
from tests.conftest import FAIL_ID, FAIL_NAME
from tests.test_interceptor_paths import chat_messages
from tests.test_interceptor_paths_async import chat_messages as async_chat_messages


def status_of(excinfo: pytest.ExceptionInfo[grpc.RpcError]) -> tuple[grpc.StatusCode, str | None]:
    """The status a failed call reports. Sync and async errors expose it differently typed."""
    error: Any = excinfo.value
    return error.code(), error.details()


class TestSyncStreamingErrorsPropagate:
    def test_server_streaming_raises_while_recording(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError) as excinfo:
                list(stub.ListUsers(pb2.ListUsersRequest(limit=FAIL_ID)))

        assert status_of(excinfo) == (grpc.StatusCode.INVALID_ARGUMENT, "limit must be positive")

    def test_server_streaming_raises_on_playback(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                list(stub.ListUsers(pb2.ListUsersRequest(limit=FAIL_ID)))
        cassette.save()

        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError) as excinfo:
                list(stub.ListUsers(pb2.ListUsersRequest(limit=FAIL_ID)))

        assert status_of(excinfo) == (grpc.StatusCode.INVALID_ARGUMENT, "limit must be positive")

    def test_bidi_streaming_raises_while_recording(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError) as excinfo:
                list(stub.Chat(chat_messages(pb2, FAIL_NAME)))

        assert status_of(excinfo) == (grpc.StatusCode.INVALID_ARGUMENT, "bad message")

    def test_partial_stream_yields_messages_then_raises(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        """Messages received before the failure are still delivered, as gRPC does."""
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            received = []
            with pytest.raises(grpc.RpcError):
                for message in stub.Chat(chat_messages(pb2, "hello", FAIL_NAME)):
                    received.append(message)

        assert [m.content for m in received] == ["Echo: hello"]

    def test_successful_stream_still_completes(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            assert len(list(stub.ListUsers(pb2.ListUsersRequest(limit=3)))) == 3


class TestSyncUnaryErrorCarriesStatus:
    def test_replayed_unary_error_reports_its_status(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        with RecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError):
                stub.GetUser(pb2.GetUserRequest(id=FAIL_ID))
        cassette.save()

        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError) as excinfo:
                stub.GetUser(pb2.GetUserRequest(id=FAIL_ID))

        assert status_of(excinfo) == (grpc.StatusCode.NOT_FOUND, "user not found")


@pytest.mark.asyncio
class TestAsyncStreamingErrorsPropagate:
    """The async path already raises; these pin the behaviour the sync path is matching."""

    async def test_server_streaming_raises_while_recording(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError) as excinfo:
                [m async for m in stub.ListUsers(pb2.ListUsersRequest(limit=FAIL_ID))]

        assert status_of(excinfo) == (grpc.StatusCode.INVALID_ARGUMENT, "limit must be positive")

    async def test_bidi_streaming_raises_while_recording(
        self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc
    ) -> None:
        cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)
        async with AsyncRecordingChannel(cassette, grpc_target) as recording:
            stub = pb2_grpc.TestServiceStub(recording.channel)
            with pytest.raises(grpc.RpcError) as excinfo:
                [m async for m in stub.Chat(async_chat_messages(pb2, FAIL_NAME))]

        assert status_of(excinfo) == (grpc.StatusCode.INVALID_ARGUMENT, "bad message")

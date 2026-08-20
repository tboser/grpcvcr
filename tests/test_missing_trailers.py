"""Recording a call whose transport cannot report trailing metadata.

Some gRPC transports raise instead of returning trailers. The interceptors fall
back to empty trailers so the interaction is still recorded; that fallback is
driven here with fakes standing in for the call the continuation returns.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import grpc
import pytest

from grpcvcr import Cassette, RecordMode
from grpcvcr.interceptors.aio import (
    AsyncRecordingStreamStreamInterceptor,
    AsyncRecordingStreamUnaryInterceptor,
    AsyncRecordingUnaryStreamInterceptor,
    AsyncRecordingUnaryUnaryInterceptor,
    _AsyncFakeStreamingCall,
    _AsyncFakeUnaryCall,
)
from grpcvcr.interceptors.sync import (
    RecordingStreamStreamInterceptor,
    RecordingStreamUnaryInterceptor,
    RecordingUnaryStreamInterceptor,
    RecordingUnaryUnaryInterceptor,
)

TRAILER_ERROR = RuntimeError("trailers unavailable")


class CallDetails:
    """The subset of grpc.ClientCallDetails the interceptors read."""

    def __init__(self, method: str) -> None:
        self.method = method
        self.metadata = None


class SyncCallWithoutTrailers:
    """A sync call that yields its payload but cannot report trailers."""

    def __init__(self, result: Any = None, messages: tuple[Any, ...] = ()) -> None:
        self._result = result
        self._messages = messages

    def result(self, timeout: float | None = None) -> Any:
        return self._result

    def __iter__(self) -> Iterator[Any]:
        return iter(self._messages)

    def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        raise TRAILER_ERROR


class AsyncCallWithoutTrailers:
    """The async equivalent, awaitable and async-iterable."""

    def __init__(self, result: Any = None, messages: tuple[Any, ...] = ()) -> None:
        self._result = result
        self._messages = messages

    def __await__(self) -> Any:
        async def _result() -> Any:
            return self._result

        return _result().__await__()

    async def __aiter__(self) -> AsyncIterator[Any]:
        for message in self._messages:
            yield message

    async def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        raise TRAILER_ERROR


@pytest.fixture
def cassette(tmp_cassette_path: Path) -> Cassette:
    return Cassette(tmp_cassette_path, record_mode=RecordMode.NEW_EPISODES)


def recorded_trailers(cassette: Cassette) -> dict[str, list[str]]:
    assert len(cassette.interactions) == 1
    return cassette.interactions[0].response.trailing_metadata


class TestSyncInterceptorsRecordWithoutTrailers:
    def test_unary_unary(self, cassette: Cassette, pb2) -> None:
        request = pb2.GetUserRequest(id=1)
        interceptor = RecordingUnaryUnaryInterceptor(cassette, "localhost:1")

        interceptor.intercept_unary_unary(
            lambda _details, _request: SyncCallWithoutTrailers(result=request),
            CallDetails("/test.TestService/GetUser"),
            request,
        )

        assert recorded_trailers(cassette) == {}

    def test_unary_stream(self, cassette: Cassette, pb2) -> None:
        request = pb2.ListUsersRequest(limit=1)
        interceptor = RecordingUnaryStreamInterceptor(cassette, "localhost:1")

        interceptor.intercept_unary_stream(
            lambda _details, _request: SyncCallWithoutTrailers(messages=(request,)),
            CallDetails("/test.TestService/ListUsers"),
            request,
        )

        assert recorded_trailers(cassette) == {}

    def test_stream_unary(self, cassette: Cassette, pb2) -> None:
        request = pb2.CreateUserRequest(name="A", email="a@example.com")
        interceptor = RecordingStreamUnaryInterceptor(cassette, "localhost:1")

        interceptor.intercept_stream_unary(
            lambda _details, _requests: SyncCallWithoutTrailers(result=request),
            CallDetails("/test.TestService/CreateUsers"),
            iter([request]),
        )

        assert recorded_trailers(cassette) == {}

    def test_stream_stream(self, cassette: Cassette, pb2) -> None:
        request = pb2.ChatMessage(sender="client", content="hi", timestamp=1)
        interceptor = RecordingStreamStreamInterceptor(cassette, "localhost:1")

        interceptor.intercept_stream_stream(
            lambda _details, _requests: SyncCallWithoutTrailers(messages=(request,)),
            CallDetails("/test.TestService/Chat"),
            iter([request]),
        )

        assert recorded_trailers(cassette) == {}


@pytest.mark.asyncio
class TestAsyncInterceptorsRecordWithoutTrailers:
    async def test_unary_unary(self, cassette: Cassette, pb2) -> None:
        request = pb2.GetUserRequest(id=1)
        interceptor = AsyncRecordingUnaryUnaryInterceptor(cassette, "localhost:1")

        async def continuation(_details: Any, _request: Any) -> AsyncCallWithoutTrailers:
            return AsyncCallWithoutTrailers(result=request)

        await interceptor.intercept_unary_unary(continuation, CallDetails("/test.TestService/GetUser"), request)

        assert recorded_trailers(cassette) == {}

    async def test_unary_stream(self, cassette: Cassette, pb2) -> None:
        request = pb2.ListUsersRequest(limit=1)
        interceptor = AsyncRecordingUnaryStreamInterceptor(cassette, "localhost:1")

        async def continuation(_details: Any, _request: Any) -> AsyncCallWithoutTrailers:
            return AsyncCallWithoutTrailers(messages=(request,))

        await interceptor.intercept_unary_stream(continuation, CallDetails("/test.TestService/ListUsers"), request)

        assert recorded_trailers(cassette) == {}

    async def test_stream_unary(self, cassette: Cassette, pb2) -> None:
        request = pb2.CreateUserRequest(name="A", email="a@example.com")
        interceptor = AsyncRecordingStreamUnaryInterceptor(cassette, "localhost:1")

        async def requests() -> AsyncIterator[Any]:
            yield request

        async def continuation(_details: Any, _requests: Any) -> AsyncCallWithoutTrailers:
            return AsyncCallWithoutTrailers(result=request)

        await interceptor.intercept_stream_unary(continuation, CallDetails("/test.TestService/CreateUsers"), requests())

        assert recorded_trailers(cassette) == {}

    async def test_stream_stream(self, cassette: Cassette, pb2) -> None:
        request = pb2.ChatMessage(sender="client", content="hi", timestamp=1)
        interceptor = AsyncRecordingStreamStreamInterceptor(cassette, "localhost:1")

        async def requests() -> AsyncIterator[Any]:
            yield request

        async def continuation(_details: Any, _requests: Any) -> AsyncCallWithoutTrailers:
            return AsyncCallWithoutTrailers(messages=(request,))

        await interceptor.intercept_stream_stream(continuation, CallDetails("/test.TestService/Chat"), requests())

        assert recorded_trailers(cassette) == {}

    async def test_stream_stream_with_no_requests(self, cassette: Cassette) -> None:
        """With no requests and no response messages there is no type to deserialize with."""
        interceptor = AsyncRecordingStreamStreamInterceptor(cassette, "localhost:1")

        async def no_requests() -> AsyncIterator[Any]:
            return
            yield

        async def continuation(_details: Any, _requests: Any) -> AsyncCallWithoutTrailers:
            return AsyncCallWithoutTrailers()

        call = await interceptor.intercept_stream_stream(
            continuation, CallDetails("/test.TestService/Chat"), no_requests()
        )

        assert isinstance(call, _AsyncFakeStreamingCall)
        assert [message async for message in call] == []


class TestAsyncUnaryFakeCall:
    def test_done_callback_fires_immediately(self) -> None:
        call = _AsyncFakeUnaryCall(result=None, code=grpc.StatusCode.OK, details=None, trailing_metadata=())
        fired: list[object] = []

        call.add_done_callback(fired.append)

        assert fired == [call]

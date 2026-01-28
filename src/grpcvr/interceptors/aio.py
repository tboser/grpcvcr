"""Async gRPC interceptors for recording and playback."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING, Any

import grpc
from grpc import aio

from grpcvr.errors import RecordingDisabledError
from grpcvr.record_modes import RecordMode
from grpcvr.serialization import (
    Interaction,
    InteractionRequest,
    InteractionResponse,
    StreamingInteractionResponse,
)

if TYPE_CHECKING:
    from grpcvr.cassette import Cassette


class _AsyncFakeUnaryCall(aio.UnaryUnaryCall):  # type: ignore[misc]
    """Async fake call for unary response playback.

    Implements the gRPC async UnaryUnaryCall interface to return pre-recorded responses
    without making actual network calls.
    """

    def __init__(
        self,
        result: Any,
        code: grpc.StatusCode,
        details: str | None,
        trailing_metadata: tuple[tuple[str, str], ...],
    ) -> None:
        self._result = result
        self._code = code
        self._details = details
        self._trailing_metadata = trailing_metadata

    def __await__(self) -> Any:
        async def _get_result() -> Any:
            if self._code != grpc.StatusCode.OK:
                raise aio.AioRpcError(
                    self._code,
                    (),
                    self._trailing_metadata,
                    self._details,
                )
            return self._result

        return _get_result().__await__()

    async def code(self) -> grpc.StatusCode:
        return self._code

    async def details(self) -> str | None:
        return self._details

    async def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        return self._trailing_metadata

    async def initial_metadata(self) -> tuple[tuple[str, str], ...]:
        return ()

    def cancelled(self) -> bool:
        return False

    def done(self) -> bool:
        return True

    def add_done_callback(self, callback: Callable[..., Any]) -> None:
        callback(self)

    def cancel(self) -> bool:
        return False

    def time_remaining(self) -> float | None:
        return None

    async def wait_for_connection(self) -> None:
        pass


class _AsyncFakeStreamingCall(aio.Call):  # type: ignore[misc]
    """Async fake call for streaming response playback.

    Implements the gRPC async Call interface to iterate over pre-recorded
    streaming responses without making actual network calls.
    """

    def __init__(
        self,
        messages: list[Any],
        code: grpc.StatusCode,
        details: str | None,
        trailing_metadata: tuple[tuple[str, str], ...],
    ) -> None:
        self._messages = messages
        self._code = code
        self._details = details
        self._trailing_metadata = trailing_metadata

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[Any]:
        for msg in self._messages:
            yield msg
        if self._code != grpc.StatusCode.OK:
            raise aio.AioRpcError(
                self._code,
                (),
                self._trailing_metadata,
                self._details,
            )

    async def code(self) -> grpc.StatusCode:
        return self._code

    async def details(self) -> str | None:
        return self._details

    async def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        return self._trailing_metadata

    async def initial_metadata(self) -> tuple[tuple[str, str], ...]:
        return ()

    def cancelled(self) -> bool:
        return False

    def done(self) -> bool:
        return True

    def add_done_callback(self, callback: Callable[..., Any]) -> None:
        callback(self)

    def cancel(self) -> bool:
        return False

    def time_remaining(self) -> float | None:
        return None

    async def wait_for_connection(self) -> None:
        pass


class AsyncRecordingUnaryUnaryInterceptor(aio.UnaryUnaryClientInterceptor):  # type: ignore[misc]
    """Async interceptor for unary-unary RPCs (single request, single response)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    async def intercept_unary_unary(
        self,
        continuation: Callable[..., Any],
        client_call_details: aio.ClientCallDetails,
        request: Any,
    ) -> aio.Call:
        method = client_call_details.method
        request_bytes = request.SerializeToString()
        metadata = client_call_details.metadata

        req = InteractionRequest.from_grpc(method, request_bytes, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response = interaction.response
                assert isinstance(response, InteractionResponse)

                response_class = response.get_response_class()
                deserializer = response_class.FromString if response_class else type(request).FromString
                result = deserializer(response.get_body_bytes())

                return _AsyncFakeUnaryCall(
                    result=result,
                    code=grpc.StatusCode[response.code],
                    details=response.details,
                    trailing_metadata=tuple((k, v) for k, vs in response.trailing_metadata.items() for v in vs),
                )

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        call = await continuation(client_call_details, request)

        try:
            result = await call
            response_bytes = result.SerializeToString()
            response_type = type(result)
            code = "OK"
            details = None
        except aio.AioRpcError as e:
            response_bytes = b""
            response_type = None
            code = e.code().name
            details = e.details()

        try:
            trailing = await call.trailing_metadata()
        except Exception:
            trailing = ()

        recorded = Interaction(
            request=req,
            response=InteractionResponse.from_grpc(
                body=response_bytes,
                code=code,
                details=details,
                trailing_metadata=trailing,
                response_type=response_type,
            ),
            rpc_type="unary",
        )
        self.cassette.record_interaction(recorded)

        return call


class AsyncRecordingUnaryStreamInterceptor(aio.UnaryStreamClientInterceptor):  # type: ignore[misc]
    """Async interceptor for server-streaming RPCs (single request, streaming response)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    async def intercept_unary_stream(
        self,
        continuation: Callable[..., Any],
        client_call_details: aio.ClientCallDetails,
        request: Any,
    ) -> aio.Call:
        method = client_call_details.method
        request_bytes = request.SerializeToString()
        metadata = client_call_details.metadata

        req = InteractionRequest.from_grpc(method, request_bytes, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response = interaction.response
                assert isinstance(response, StreamingInteractionResponse)

                response_class = response.get_response_class()
                deserializer = response_class.FromString if response_class else type(request).FromString
                messages = [deserializer(m) for m in response.get_messages_bytes()]

                return _AsyncFakeStreamingCall(
                    messages=messages,
                    code=grpc.StatusCode[response.code],
                    details=response.details,
                    trailing_metadata=tuple((k, v) for k, vs in response.trailing_metadata.items() for v in vs),
                )

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        call = await continuation(client_call_details, request)

        messages_bytes: list[bytes] = []
        response_type: type | None = None
        code = "OK"
        details = None

        try:
            async for msg in call:
                messages_bytes.append(msg.SerializeToString())
                if response_type is None:
                    response_type = type(msg)
        except aio.AioRpcError as e:
            code = e.code().name
            details = e.details()

        try:
            trailing = await call.trailing_metadata()
        except Exception:
            trailing = ()

        recorded = Interaction(
            request=req,
            response=StreamingInteractionResponse.from_grpc(
                messages=messages_bytes,
                code=code,
                details=details,
                trailing_metadata=trailing,
                response_type=response_type,
            ),
            rpc_type="server_streaming",
        )
        self.cassette.record_interaction(recorded)

        response = recorded.response
        assert isinstance(response, StreamingInteractionResponse)
        response_class = response.get_response_class()
        deserializer = response_class.FromString if response_class else type(request).FromString

        return _AsyncFakeStreamingCall(
            messages=[deserializer(m) for m in response.get_messages_bytes()],
            code=grpc.StatusCode[response.code],
            details=response.details,
            trailing_metadata=trailing,
        )


class AsyncRecordingStreamUnaryInterceptor(aio.StreamUnaryClientInterceptor):  # type: ignore[misc]
    """Async interceptor for client-streaming RPCs (streaming request, single response)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    async def intercept_stream_unary(
        self,
        continuation: Callable[..., Any],
        client_call_details: aio.ClientCallDetails,
        request_iterator: Any,
    ) -> aio.Call:
        method = client_call_details.method
        metadata = client_call_details.metadata

        requests = [r async for r in request_iterator]
        combined_request = b"".join(r.SerializeToString() for r in requests)

        req = InteractionRequest.from_grpc(method, combined_request, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response = interaction.response
                assert isinstance(response, InteractionResponse)

                response_class = response.get_response_class()
                if response_class:
                    result = response_class.FromString(response.get_body_bytes())
                elif requests:
                    result = type(requests[0]).FromString(response.get_body_bytes())
                else:
                    result = response.get_body_bytes()

                return _AsyncFakeUnaryCall(
                    result=result,
                    code=grpc.StatusCode[response.code],
                    details=response.details,
                    trailing_metadata=tuple((k, v) for k, vs in response.trailing_metadata.items() for v in vs),
                )

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        async def replay_requests() -> AsyncIterator[Any]:
            for r in requests:
                yield r

        call = await continuation(client_call_details, replay_requests())

        try:
            result = await call
            response_bytes = result.SerializeToString()
            response_type = type(result)
            code = "OK"
            details = None
        except aio.AioRpcError as e:
            response_bytes = b""
            response_type = None
            code = e.code().name
            details = e.details()

        try:
            trailing = await call.trailing_metadata()
        except Exception:
            trailing = ()

        recorded = Interaction(
            request=req,
            response=InteractionResponse.from_grpc(
                body=response_bytes,
                code=code,
                details=details,
                trailing_metadata=trailing,
                response_type=response_type,
            ),
            rpc_type="client_streaming",
        )
        self.cassette.record_interaction(recorded)

        return call


class AsyncRecordingStreamStreamInterceptor(aio.StreamStreamClientInterceptor):  # type: ignore[misc]
    """Async interceptor for bidirectional streaming RPCs."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    async def intercept_stream_stream(
        self,
        continuation: Callable[..., Any],
        client_call_details: aio.ClientCallDetails,
        request_iterator: Any,
    ) -> aio.Call:
        method = client_call_details.method
        metadata = client_call_details.metadata

        requests = [r async for r in request_iterator]
        combined_request = b"".join(r.SerializeToString() for r in requests)

        req = InteractionRequest.from_grpc(method, combined_request, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response = interaction.response
                assert isinstance(response, StreamingInteractionResponse)

                response_class = response.get_response_class()
                if response_class:
                    messages = [response_class.FromString(m) for m in response.get_messages_bytes()]
                elif requests:
                    messages = [type(requests[0]).FromString(m) for m in response.get_messages_bytes()]
                else:
                    messages = response.get_messages_bytes()

                return _AsyncFakeStreamingCall(
                    messages=messages,
                    code=grpc.StatusCode[response.code],
                    details=response.details,
                    trailing_metadata=tuple((k, v) for k, vs in response.trailing_metadata.items() for v in vs),
                )

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        async def replay_requests() -> AsyncIterator[Any]:
            for r in requests:
                yield r

        call = await continuation(client_call_details, replay_requests())

        messages_bytes: list[bytes] = []
        response_type: type | None = None
        code = "OK"
        details = None

        try:
            async for msg in call:
                messages_bytes.append(msg.SerializeToString())
                if response_type is None:
                    response_type = type(msg)
        except aio.AioRpcError as e:
            code = e.code().name
            details = e.details()

        try:
            trailing = await call.trailing_metadata()
        except Exception:
            trailing = ()

        recorded = Interaction(
            request=req,
            response=StreamingInteractionResponse.from_grpc(
                messages=messages_bytes,
                code=code,
                details=details,
                trailing_metadata=trailing,
                response_type=response_type,
            ),
            rpc_type="bidi_streaming",
        )
        self.cassette.record_interaction(recorded)

        response = recorded.response
        assert isinstance(response, StreamingInteractionResponse)
        response_class = response.get_response_class()
        if response_class:
            deserializer = response_class.FromString
        elif requests:
            deserializer = type(requests[0]).FromString
        else:
            deserializer = lambda x: x  # noqa: E731

        return _AsyncFakeStreamingCall(
            messages=[deserializer(m) for m in response.get_messages_bytes()],
            code=grpc.StatusCode[response.code],
            details=response.details,
            trailing_metadata=trailing,
        )


def create_async_interceptors(cassette: Cassette) -> list[aio.ClientInterceptor]:
    """Create all async interceptors for a cassette.

    Args:
        cassette: The cassette to use for recording/playback.

    Returns:
        List of async interceptors covering all RPC types.
    """
    return [
        AsyncRecordingUnaryUnaryInterceptor(cassette),
        AsyncRecordingUnaryStreamInterceptor(cassette),
        AsyncRecordingStreamUnaryInterceptor(cassette),
        AsyncRecordingStreamStreamInterceptor(cassette),
    ]

"""Shared interceptor logic for creating fake gRPC call objects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import grpc

from grpcvr.serialization import (
    Interaction,
    InteractionResponse,
    StreamingInteractionResponse,
)


def create_unary_response(
    interaction: Interaction,
    response_deserializer: Callable[[bytes], Any],
) -> grpc.Call:
    """Create a fake unary response from a recorded interaction.

    Args:
        interaction: The recorded interaction containing the response data.
        response_deserializer: Function to deserialize the response bytes
            (typically `SomeProtoMessage.FromString`).

    Returns:
        A fake gRPC Call object that returns the recorded response.
    """
    response = interaction.response
    assert isinstance(response, InteractionResponse)

    body_bytes = response.get_body_bytes()
    deserialized = response_deserializer(body_bytes)

    return _FakeUnaryCall(
        result=deserialized,
        code=grpc.StatusCode[response.code],
        details=response.details,
        trailing_metadata=_dict_to_metadata(response.trailing_metadata),
    )


def create_streaming_response(
    interaction: Interaction,
    response_deserializer: Callable[[bytes], Any],
) -> grpc.Call:
    """Create a fake streaming response from a recorded interaction.

    Args:
        interaction: The recorded interaction containing the streaming response data.
        response_deserializer: Function to deserialize each response message
            (typically `SomeProtoMessage.FromString`).

    Returns:
        A fake gRPC Call object that iterates over the recorded messages.
    """
    response = interaction.response
    assert isinstance(response, StreamingInteractionResponse)

    messages = [response_deserializer(m) for m in response.get_messages_bytes()]

    return _FakeStreamingCall(
        messages=messages,
        code=grpc.StatusCode[response.code],
        details=response.details,
        trailing_metadata=_dict_to_metadata(response.trailing_metadata),
    )


def _dict_to_metadata(d: dict[str, list[str]]) -> tuple[tuple[str, str], ...]:
    """Convert metadata dict back to gRPC tuple format."""
    result: list[tuple[str, str]] = []
    for key, values in d.items():
        for value in values:
            result.append((key, value))
    return tuple(result)


def _metadata_to_dict(metadata: tuple[tuple[str, str], ...] | None) -> dict[str, list[str]]:
    """Convert gRPC metadata tuple to dict format for storage."""
    result: dict[str, list[str]] = {}
    if metadata:
        for key, value in metadata:
            result.setdefault(key, []).append(value)
    return result


class _FakeUnaryCall(grpc.Call, grpc.Future):  # type: ignore[misc]
    """Fake call object for playback of unary responses.

    Implements both the gRPC Call and Future interfaces to mimic the behavior
    of a real unary RPC call, allowing recorded responses to be returned
    without making actual network calls.
    """

    def __init__(
        self,
        result: object,
        code: grpc.StatusCode,
        details: str | None,
        trailing_metadata: tuple[tuple[str, str], ...],
    ) -> None:
        self._result = result
        self._code = code
        self._details = details
        self._trailing_metadata = trailing_metadata

    def result(self, timeout: float | None = None) -> object:
        if self._code != grpc.StatusCode.OK:
            raise grpc.RpcError()
        return self._result

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str | None:
        return self._details

    def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        return self._trailing_metadata

    def initial_metadata(self) -> tuple[tuple[str, str], ...]:
        return ()

    def cancelled(self) -> bool:
        return False

    def running(self) -> bool:
        return False

    def done(self) -> bool:
        return True

    def add_done_callback(self, fn: Callable[[Any], None]) -> None:
        fn(self)

    def exception(self, timeout: float | None = None) -> Exception | None:
        if self._code != grpc.StatusCode.OK:
            return grpc.RpcError()
        return None

    def traceback(self, timeout: float | None = None) -> Any:
        return None

    def add_callback(self, callback: Callable[[Any], None]) -> bool:
        callback(self)
        return True

    def is_active(self) -> bool:
        return False

    def time_remaining(self) -> float | None:
        return None

    def cancel(self) -> bool:
        return False


class _FakeStreamingCall(grpc.Call):  # type: ignore[misc]
    """Fake call object for playback of streaming responses.

    Implements the gRPC Call interface with iterator support to mimic the
    behavior of a real streaming RPC call, allowing recorded message sequences
    to be iterated over without making actual network calls.
    """

    def __init__(
        self,
        messages: list[object],
        code: grpc.StatusCode,
        details: str | None,
        trailing_metadata: tuple[tuple[str, str], ...],
    ) -> None:
        self._messages = messages
        self._code = code
        self._details = details
        self._trailing_metadata = trailing_metadata
        self._index = 0

    def __iter__(self) -> _FakeStreamingCall:
        return self

    def __next__(self) -> object:
        if self._index >= len(self._messages):
            raise StopIteration
        msg = self._messages[self._index]
        self._index += 1
        return msg

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str | None:
        return self._details

    def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        return self._trailing_metadata

    def initial_metadata(self) -> tuple[tuple[str, str], ...]:
        return ()

    def cancelled(self) -> bool:
        return False

    def add_callback(self, callback: Callable[[Any], None]) -> bool:
        callback(self)
        return True

    def is_active(self) -> bool:
        return False

    def time_remaining(self) -> float | None:
        return None

    def cancel(self) -> bool:
        return False

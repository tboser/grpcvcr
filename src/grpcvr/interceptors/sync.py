"""Synchronous gRPC interceptors for recording and playback."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import grpc

from grpcvr.errors import RecordingDisabledError
from grpcvr.interceptors._base import (
    create_streaming_response,
    create_unary_response,
)
from grpcvr.record_modes import RecordMode
from grpcvr.serialization import (
    Interaction,
    InteractionRequest,
    InteractionResponse,
    StreamingInteractionResponse,
)

if TYPE_CHECKING:
    from grpcvr.cassette import Cassette


class RecordingUnaryUnaryInterceptor(grpc.UnaryUnaryClientInterceptor):  # type: ignore[misc]
    """Interceptor for unary-unary RPCs (single request, single response)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    def intercept_unary_unary(
        self,
        continuation: Callable[..., Any],
        client_call_details: grpc.ClientCallDetails,
        request: Any,
    ) -> grpc.Call:
        method = client_call_details.method
        request_bytes = request.SerializeToString()
        metadata = client_call_details.metadata

        req = InteractionRequest.from_grpc(method, request_bytes, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response_class = interaction.response.get_response_class()
                if response_class:
                    return create_unary_response(interaction, response_class.FromString)
                return create_unary_response(interaction, type(request).FromString)

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        response = continuation(client_call_details, request)

        try:
            result = response.result()
            response_bytes = result.SerializeToString()
            response_type = type(result)
            code = "OK"
            details = None
        except grpc.RpcError as e:
            response_bytes = b""
            response_type = None
            code = e.code().name  # type: ignore[union-attr]
            details = e.details()  # type: ignore[union-attr]

        try:
            trailing = response.trailing_metadata()
        except Exception:
            trailing = None

        recorded_interaction = Interaction(
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
        self.cassette.record_interaction(recorded_interaction)

        return response


class RecordingUnaryStreamInterceptor(grpc.UnaryStreamClientInterceptor):  # type: ignore[misc]
    """Interceptor for unary-stream RPCs (single request, streaming response)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    def intercept_unary_stream(
        self,
        continuation: Callable[..., Any],
        client_call_details: grpc.ClientCallDetails,
        request: Any,
    ) -> grpc.Call:
        method = client_call_details.method
        request_bytes = request.SerializeToString()
        metadata = client_call_details.metadata

        req = InteractionRequest.from_grpc(method, request_bytes, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response_class = interaction.response.get_response_class()
                if response_class:
                    return create_streaming_response(interaction, response_class.FromString)
                return create_streaming_response(interaction, type(request).FromString)

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        response = continuation(client_call_details, request)

        messages: list[bytes] = []
        response_type: type | None = None
        code = "OK"
        details = None

        try:
            for msg in response:
                messages.append(msg.SerializeToString())
                if response_type is None:
                    response_type = type(msg)
        except grpc.RpcError as e:
            code = e.code().name  # type: ignore[union-attr]
            details = e.details()  # type: ignore[union-attr]

        try:
            trailing = response.trailing_metadata()
        except Exception:
            trailing = None

        recorded_interaction = Interaction(
            request=req,
            response=StreamingInteractionResponse.from_grpc(
                messages=messages,
                code=code,
                details=details,
                trailing_metadata=trailing,
                response_type=response_type,
            ),
            rpc_type="server_streaming",
        )
        self.cassette.record_interaction(recorded_interaction)

        response_class = recorded_interaction.response.get_response_class()
        deserializer = response_class.FromString if response_class else type(request).FromString
        return create_streaming_response(recorded_interaction, deserializer)


class RecordingStreamUnaryInterceptor(grpc.StreamUnaryClientInterceptor):  # type: ignore[misc]
    """Interceptor for stream-unary RPCs (streaming request, single response)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    def intercept_stream_unary(
        self,
        continuation: Callable[..., Any],
        client_call_details: grpc.ClientCallDetails,
        request_iterator: Any,
    ) -> grpc.Call:
        method = client_call_details.method
        metadata = client_call_details.metadata

        requests = list(request_iterator)
        combined_request = b"".join(r.SerializeToString() for r in requests)

        req = InteractionRequest.from_grpc(method, combined_request, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response_class = interaction.response.get_response_class()
                if response_class:
                    return create_unary_response(interaction, response_class.FromString)
                msg_type = type(requests[0]) if requests else None
                if msg_type:
                    return create_unary_response(interaction, msg_type.FromString)
                return create_unary_response(interaction, lambda x: x)

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        response = continuation(client_call_details, iter(requests))

        try:
            result = response.result()
            response_bytes = result.SerializeToString()
            response_type = type(result)
            code = "OK"
            details = None
        except grpc.RpcError as e:
            response_bytes = b""
            response_type = None
            code = e.code().name  # type: ignore[union-attr]
            details = e.details()  # type: ignore[union-attr]

        try:
            trailing = response.trailing_metadata()
        except Exception:
            trailing = None

        recorded_interaction = Interaction(
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
        self.cassette.record_interaction(recorded_interaction)

        return response


class RecordingStreamStreamInterceptor(grpc.StreamStreamClientInterceptor):  # type: ignore[misc]
    """Interceptor for stream-stream RPCs (bidirectional streaming)."""

    def __init__(self, cassette: Cassette) -> None:
        self.cassette = cassette

    def intercept_stream_stream(
        self,
        continuation: Callable[..., Any],
        client_call_details: grpc.ClientCallDetails,
        request_iterator: Any,
    ) -> grpc.Call:
        method = client_call_details.method
        metadata = client_call_details.metadata

        requests = list(request_iterator)
        combined_request = b"".join(r.SerializeToString() for r in requests)

        req = InteractionRequest.from_grpc(method, combined_request, metadata)

        if self.cassette.record_mode != RecordMode.ALL:
            interaction = self.cassette.find_interaction(req)
            if interaction is not None:
                response_class = interaction.response.get_response_class()
                if response_class:
                    return create_streaming_response(interaction, response_class.FromString)
                msg_type = type(requests[0]) if requests else None
                deserializer = msg_type.FromString if msg_type else lambda x: x
                return create_streaming_response(interaction, deserializer)

        if not self.cassette.can_record:
            raise RecordingDisabledError(method)

        response = continuation(client_call_details, iter(requests))

        messages: list[bytes] = []
        response_type: type | None = None
        code = "OK"
        details = None

        try:
            for msg in response:
                messages.append(msg.SerializeToString())
                if response_type is None:
                    response_type = type(msg)
        except grpc.RpcError as e:
            code = e.code().name  # type: ignore[union-attr]
            details = e.details()  # type: ignore[union-attr]

        try:
            trailing = response.trailing_metadata()
        except Exception:
            trailing = None

        recorded_interaction = Interaction(
            request=req,
            response=StreamingInteractionResponse.from_grpc(
                messages=messages,
                code=code,
                details=details,
                trailing_metadata=trailing,
                response_type=response_type,
            ),
            rpc_type="bidi_streaming",
        )
        self.cassette.record_interaction(recorded_interaction)

        response_class = recorded_interaction.response.get_response_class()
        if response_class:
            deserializer = response_class.FromString
        else:
            msg_type = type(requests[0]) if requests else None
            deserializer = msg_type.FromString if msg_type else lambda x: x
        return create_streaming_response(recorded_interaction, deserializer)


def create_interceptors(cassette: Cassette) -> list[grpc.ClientInterceptor]:
    """Create all sync interceptors for a cassette.

    Args:
        cassette: The cassette to use for recording/playback.

    Returns:
        List of interceptors covering all RPC types.
    """
    return [
        RecordingUnaryUnaryInterceptor(cassette),
        RecordingUnaryStreamInterceptor(cassette),
        RecordingStreamUnaryInterceptor(cassette),
        RecordingStreamStreamInterceptor(cassette),
    ]

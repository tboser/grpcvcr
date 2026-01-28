"""Tests for error classes."""

from grpcvcr.errors import (
    CassetteNotFoundError,
    CassetteWriteError,
    GrpcvcrError,
    NoMatchingInteractionError,
    RecordingDisabledError,
    SerializationError,
)
from grpcvcr.serialization import Interaction, InteractionRequest, InteractionResponse


class TestGrpcvcrError:
    def test_base_exception(self) -> None:
        err = GrpcvcrError("test message")
        assert str(err) == "test message"
        assert isinstance(err, Exception)


class TestCassetteNotFoundError:
    def test_message_contains_path(self) -> None:
        err = CassetteNotFoundError("/path/to/cassette.yaml")
        assert "/path/to/cassette.yaml" in str(err)
        assert err.path == "/path/to/cassette.yaml"


class TestNoMatchingInteractionError:
    def test_message_contains_method(self) -> None:
        interactions = [
            Interaction(
                request=InteractionRequest.from_grpc("/test/Method1", b""),
                response=InteractionResponse.from_grpc(b"", "OK"),
                rpc_type="unary",
            )
        ]
        err = NoMatchingInteractionError("/test/TargetMethod", b"request", interactions)
        assert "/test/TargetMethod" in str(err)
        assert err.method == "/test/TargetMethod"
        assert err.available == interactions


class TestRecordingDisabledError:
    def test_message_contains_method(self) -> None:
        err = RecordingDisabledError("/test/Method")
        assert "/test/Method" in str(err)
        assert err.method == "/test/Method"


class TestCassetteWriteError:
    def test_message_contains_path_and_cause(self) -> None:
        cause = OSError("disk full")
        err = CassetteWriteError("/path/to/cassette.yaml", cause)
        assert "/path/to/cassette.yaml" in str(err)
        assert err.cause == cause


class TestSerializationError:
    def test_with_cause(self) -> None:
        cause = ValueError("invalid data")
        err = SerializationError("Failed to serialize", cause)
        assert err.cause == cause

    def test_without_cause(self) -> None:
        err = SerializationError("Generic error")
        assert err.cause is None

"""Custom exceptions for grpcvcr."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grpcvcr.serialization import Interaction


class GrpcvcrError(Exception):
    """Base exception for all grpcvcr errors.

    All grpcvcr exceptions inherit from this class, making it easy to
    catch any grpcvcr-specific error.

    Example:
        ```python
        try:
            with recorded_channel("test.yaml", "localhost:50051") as channel:
                stub = MyServiceStub(channel)
                response = stub.GetUser(request)
        except GrpcvcrError as e:
            print(f"grpcvcr error: {e}")
        ```
    """


class CassetteNotFoundError(GrpcvcrError):
    """Raised when a cassette file cannot be found.

    This occurs when using `RecordMode.NONE` or `RecordMode.ONCE` (after
    initial recording) and the cassette file doesn't exist.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        """Path to the missing cassette file."""
        super().__init__(f"Cassette not found: {path}")


class NoMatchingInteractionError(GrpcvcrError):
    """Raised when no recorded interaction matches the request.

    This typically means the test is making a new RPC call that wasn't
    recorded in the cassette.
    """

    def __init__(
        self,
        method: str,
        request: bytes,
        available: list[Interaction],
    ) -> None:
        self.method = method
        """The gRPC method that was called."""

        self.request = request
        """The serialized request bytes."""

        self.available = available
        """List of available recorded interactions."""

        available_methods = [i.method for i in available]
        super().__init__(f"No matching interaction for {method}. Available: {available_methods}")


class RecordingDisabledError(GrpcvcrError):
    """Raised when recording is attempted but disabled.

    This occurs in `RecordMode.NONE` when a request is made that doesn't
    match any recorded interaction.
    """

    def __init__(self, method: str) -> None:
        self.method = method
        """The gRPC method that was called."""
        super().__init__(f"Recording disabled but no matching interaction for: {method}")


class CassetteWriteError(GrpcvcrError):
    """Raised when a cassette cannot be written to disk.

    This can occur due to permission issues, disk full, or other I/O errors.
    """

    def __init__(self, path: str, cause: Exception) -> None:
        self.path = path
        """Path where the cassette was being written."""

        self.cause = cause
        """The underlying exception that caused the write failure."""
        super().__init__(f"Failed to write cassette {path}: {cause}")


class SerializationError(GrpcvcrError):
    """Raised when request/response serialization fails.

    This can occur when parsing a malformed cassette file or when
    serializing data to save.
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        """The underlying exception, if any."""
        super().__init__(message)

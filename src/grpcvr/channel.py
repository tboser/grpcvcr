"""Channel wrappers for easy integration."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import grpc
from grpc import aio

from grpcvr.cassette import Cassette
from grpcvr.interceptors.aio import create_async_interceptors
from grpcvr.interceptors.sync import create_interceptors
from grpcvr.matchers import DEFAULT_MATCHER, Matcher
from grpcvr.record_modes import RecordMode


class RecordingChannel:
    """A gRPC channel wrapper that records and plays back interactions.

    Wraps a standard gRPC channel with interceptors that record all RPC
    calls to a cassette for later playback.

    Example:
        ```python
        from grpcvr import Cassette, RecordingChannel, RecordMode

        cassette = Cassette("tests/cassettes/test.yaml", record_mode=RecordMode.ALL)

        with RecordingChannel(cassette, "localhost:50051") as recording:
            stub = MyServiceStub(recording.channel)
            response = stub.GetUser(GetUserRequest(id=1))
        ```
    """

    def __init__(
        self,
        cassette: Cassette,
        target: str,
        *,
        credentials: grpc.ChannelCredentials | None = None,
        options: list[tuple[str, str]] | None = None,
    ) -> None:
        """Create a new RecordingChannel.

        Args:
            cassette: The cassette to record to or play back from.
            target: The gRPC server address (e.g., 'localhost:50051').
            credentials: Optional channel credentials for secure channels.
            options: Optional gRPC channel options.
        """
        self.cassette = cassette
        """The cassette being used for recording/playback."""

        self.target = target
        """The gRPC server address."""

        interceptors = create_interceptors(cassette)

        if credentials:
            base_channel = grpc.secure_channel(target, credentials, options=options or [])
        else:
            base_channel = grpc.insecure_channel(target, options=options or [])

        self.channel = grpc.intercept_channel(base_channel, *interceptors)
        """The wrapped gRPC channel with recording interceptors."""

    def close(self) -> None:
        """Close the channel and save the cassette."""
        self.channel.close()
        self.cassette.save()

    def __enter__(self) -> RecordingChannel:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncRecordingChannel:
    """Async version of RecordingChannel for grpc.aio.

    Wraps an async gRPC channel with interceptors that record all RPC
    calls to a cassette for later playback.

    Example:
        ```python
        from grpcvr import Cassette, AsyncRecordingChannel, RecordMode

        cassette = Cassette("tests/cassettes/test.yaml", record_mode=RecordMode.ALL)

        async with AsyncRecordingChannel(cassette, "localhost:50051") as recording:
            stub = MyServiceStub(recording.channel)
            response = await stub.GetUser(GetUserRequest(id=1))
        ```
    """

    def __init__(
        self,
        cassette: Cassette,
        target: str,
        *,
        credentials: grpc.ChannelCredentials | None = None,
        options: list[tuple[str, str]] | None = None,
    ) -> None:
        """Create a new AsyncRecordingChannel.

        Args:
            cassette: The cassette to record to or play back from.
            target: The gRPC server address (e.g., 'localhost:50051').
            credentials: Optional channel credentials for secure channels.
            options: Optional gRPC channel options.
        """
        self.cassette = cassette
        """The cassette being used for recording/playback."""

        self.target = target
        """The gRPC server address."""

        interceptors = create_async_interceptors(cassette)

        if credentials:
            self.channel = aio.secure_channel(target, credentials, options=options or [], interceptors=interceptors)
        else:
            self.channel = aio.insecure_channel(target, options=options or [], interceptors=interceptors)

    async def close(self) -> None:
        """Close the channel and save the cassette."""
        await self.channel.close()
        self.cassette.save()

    async def __aenter__(self) -> AsyncRecordingChannel:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


@contextmanager
def recorded_channel(
    path: str | Path,
    target: str,
    *,
    record_mode: RecordMode = RecordMode.NEW_EPISODES,
    match_on: Matcher | None = None,
    credentials: grpc.ChannelCredentials | None = None,
    options: list[tuple[str, str]] | None = None,
) -> Generator[grpc.Channel, None, None]:
    """Context manager for a recorded gRPC channel.

    This is the simplest API for recording and playing back gRPC calls.
    Creates a cassette and channel, yields the channel, then saves the
    cassette on exit.

    Args:
        path: Path to the cassette file.
        target: The gRPC server address.
        record_mode: How to handle recording vs playback.
        match_on: Matcher to use for finding recorded interactions.
        credentials: Optional channel credentials for secure channels.
        options: Optional gRPC channel options.

    Yields:
        A gRPC channel that records/plays back interactions.

    Example:
        ```python
        from grpcvr import recorded_channel, RecordMode

        # Record interactions
        with recorded_channel("test.yaml", "localhost:50051", record_mode=RecordMode.ALL) as channel:
            stub = MyServiceStub(channel)
            response = stub.GetUser(GetUserRequest(id=1))

        # Play back interactions (no network calls made)
        with recorded_channel("test.yaml", "localhost:50051", record_mode=RecordMode.NONE) as channel:
            stub = MyServiceStub(channel)
            response = stub.GetUser(GetUserRequest(id=1))
        ```
    """
    cassette = Cassette(
        path=Path(path),
        record_mode=record_mode,
        match_on=match_on or DEFAULT_MATCHER,
    )

    recording = RecordingChannel(cassette, target, credentials=credentials, options=options)

    try:
        yield recording.channel
    finally:
        recording.close()


@contextmanager
def async_recorded_channel(
    path: str | Path,
    target: str,
    *,
    record_mode: RecordMode = RecordMode.NEW_EPISODES,
    match_on: Matcher | None = None,
    credentials: grpc.ChannelCredentials | None = None,
    options: list[tuple[str, str]] | None = None,
) -> Generator[aio.Channel, None, None]:
    """Context manager for an async recorded gRPC channel.

    Note: This is a sync context manager that returns an async channel.
    For proper async cleanup, use `AsyncRecordingChannel` directly with
    `async with`.

    Args:
        path: Path to the cassette file.
        target: The gRPC server address.
        record_mode: How to handle recording vs playback.
        match_on: Matcher to use for finding recorded interactions.
        credentials: Optional channel credentials for secure channels.
        options: Optional gRPC channel options.

    Yields:
        An async gRPC channel that records/plays back interactions.

    Example:
        ```python
        from grpcvr import async_recorded_channel

        with async_recorded_channel("test.yaml", "localhost:50051") as channel:
            stub = MyServiceStub(channel)
            response = await stub.GetUser(GetUserRequest(id=1))
        ```
    """
    cassette = Cassette(
        path=Path(path),
        record_mode=record_mode,
        match_on=match_on or DEFAULT_MATCHER,
    )

    recording = AsyncRecordingChannel(cassette, target, credentials=credentials, options=options)

    try:
        yield recording.channel
    finally:
        cassette.save()

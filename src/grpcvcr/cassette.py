"""Cassette management - loading, saving, and using cassettes."""

from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from grpcvcr.errors import (
    CassetteNotFoundError,
    NoMatchingInteractionError,
    RecordingDisabledError,
)
from grpcvcr.matchers import DEFAULT_MATCHER, Matcher, find_matching_interaction
from grpcvcr.record_modes import RecordMode
from grpcvcr.serialization import (
    CassetteData,
    CassetteSerializer,
    Interaction,
    InteractionRequest,
)


@dataclass
class Cassette:
    """A collection of recorded gRPC interactions.

    Cassettes store request/response pairs and can be saved to disk
    for later playback during tests. Use as a context manager to ensure
    changes are saved.

    Example:
        ```python
        from grpcvcr import Cassette, RecordMode, RecordingChannel

        # Record interactions
        with Cassette("tests/cassettes/my_test.yaml", record_mode=RecordMode.ALL) as cassette:
            with RecordingChannel(cassette, "localhost:50051") as recording:
                stub = MyServiceStub(recording.channel)
                response = stub.GetUser(GetUserRequest(id=1))

        # Playback interactions
        with Cassette("tests/cassettes/my_test.yaml", record_mode=RecordMode.NONE) as cassette:
            with RecordingChannel(cassette, "localhost:50051") as recording:
                stub = MyServiceStub(recording.channel)
                response = stub.GetUser(GetUserRequest(id=1))  # Returns recorded response
        ```
    """

    path: Path
    """Path to the cassette file (YAML or JSON)."""

    record_mode: RecordMode = RecordMode.NEW_EPISODES
    """How to handle recording vs playback."""

    match_on: Matcher = field(default_factory=lambda: DEFAULT_MATCHER)
    """Matcher(s) to use for finding recorded interactions."""

    _data: CassetteData = field(default_factory=CassetteData, init=False)
    _dirty: bool = field(default=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        if isinstance(self.path, str):
            self.path = Path(self.path)
        self._load()

    def _load(self) -> None:
        """Load cassette from disk if it exists."""
        if self.path.exists():
            self._data = CassetteSerializer.load(self.path)
        elif self.record_mode == RecordMode.NONE:
            raise CassetteNotFoundError(str(self.path))
        elif self.record_mode == RecordMode.ONCE:
            self._data = CassetteData()

    def save(self) -> None:
        """Save cassette to disk if it has been modified.

        Called automatically when using the cassette as a context manager.
        """
        if self._dirty:
            CassetteSerializer.save(self.path, self._data)
            self._dirty = False

    @property
    def interactions(self) -> list[Interaction]:
        """All recorded interactions in this cassette."""
        return self._data.interactions

    @property
    def can_record(self) -> bool:
        """Whether recording is allowed in the current mode."""
        return self.record_mode in (RecordMode.ALL, RecordMode.NEW_EPISODES, RecordMode.ONCE)

    def find_interaction(self, request: InteractionRequest) -> Interaction | None:
        """Find a matching recorded interaction for a request.

        Args:
            request: The request to match.

        Returns:
            The matching Interaction, or None if not found.
        """
        return find_matching_interaction(request, self.interactions, self.match_on)

    def record_interaction(self, interaction: Interaction) -> None:
        """Record a new interaction to the cassette.

        In `RecordMode.ALL`, existing interactions with the same request
        (based on the matcher) are replaced. In other modes, new
        interactions are appended.

        Args:
            interaction: The interaction to record.
        """
        with self._lock:
            if self.record_mode == RecordMode.ALL:
                self._data.interactions = [
                    i for i in self._data.interactions if not self.match_on.matches(interaction.request, i.request)
                ]

            self._data.interactions.append(interaction)
            self._dirty = True

    def get_response(
        self,
        method: str,
        request_body: bytes,
        metadata: tuple[tuple[str, str], ...] | None = None,
    ) -> Interaction:
        """Get the recorded response for a request.

        Args:
            method: Full gRPC method path.
            request_body: Serialized protobuf request.
            metadata: Optional request metadata (headers).

        Returns:
            The matching recorded interaction.

        Raises:
            NoMatchingInteractionError: If no matching interaction is found
                and recording is enabled.
            RecordingDisabledError: If no matching interaction is found
                and recording is disabled.
        """
        request = InteractionRequest.from_grpc(method, request_body, metadata)
        interaction = self.find_interaction(request)

        if interaction is None:
            if not self.can_record:
                raise RecordingDisabledError(method)
            raise NoMatchingInteractionError(method, request_body, self.interactions)

        return interaction

    def __enter__(self) -> Cassette:
        return self

    def __exit__(self, *args: object) -> None:
        self.save()


@contextmanager
def use_cassette(
    path: str | Path,
    record_mode: RecordMode = RecordMode.NEW_EPISODES,
    match_on: Matcher | None = None,
) -> Generator[Cassette, None, None]:
    """Context manager for using a cassette.

    This is a convenience wrapper around `Cassette` that ensures the
    cassette is saved when the context exits.

    Args:
        path: Path to the cassette file.
        record_mode: How to handle recording vs playback.
        match_on: Matcher to use for finding recorded interactions.

    Yields:
        The Cassette instance.

    Example:
        ```python
        from grpcvcr import use_cassette, RecordMode, RecordingChannel

        with use_cassette("tests/cassettes/test.yaml", record_mode=RecordMode.ALL) as cassette:
            with RecordingChannel(cassette, "localhost:50051") as recording:
                stub = MyServiceStub(recording.channel)
                response = stub.MyMethod(request)
        ```
    """
    cassette = Cassette(
        path=Path(path),
        record_mode=record_mode,
        match_on=match_on or DEFAULT_MATCHER,
    )
    try:
        yield cassette
    finally:
        cassette.save()

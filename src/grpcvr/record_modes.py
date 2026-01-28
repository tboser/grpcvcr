"""Recording mode definitions."""

from enum import Enum


class RecordMode(Enum):
    """Controls how the cassette handles recording and playback.

    Example:
        ```python
        from grpcvr import Cassette, RecordMode

        # Playback only - fails if interaction not found
        cassette = Cassette("test.yaml", record_mode=RecordMode.NONE)

        # Record new interactions, replay existing ones (default)
        cassette = Cassette("test.yaml", record_mode=RecordMode.NEW_EPISODES)

        # Always record, overwriting existing
        cassette = Cassette("test.yaml", record_mode=RecordMode.ALL)

        # Record once, then playback only
        cassette = Cassette("test.yaml", record_mode=RecordMode.ONCE)
        ```
    """

    NONE = "none"
    """Playback only. Raises error if no matching interaction found.
    Use in CI to ensure all interactions are pre-recorded."""

    NEW_EPISODES = "new_episodes"
    """Play back existing interactions, record new ones.
    Default mode - good for iterative test development."""

    ALL = "all"
    """Always record, overwriting existing interactions.
    Use to refresh cassettes after API changes."""

    ONCE = "once"
    """Record if cassette doesn't exist, then playback only.
    Good for one-time setup of test fixtures."""

"""Tests for record modes."""

from grpcvcr.record_modes import RecordMode


class TestRecordMode:
    def test_enum_values(self) -> None:
        assert RecordMode.NONE.value == "none"
        assert RecordMode.NEW_EPISODES.value == "new_episodes"
        assert RecordMode.ALL.value == "all"
        assert RecordMode.ONCE.value == "once"

    def test_from_string(self) -> None:
        assert RecordMode("none") == RecordMode.NONE
        assert RecordMode("new_episodes") == RecordMode.NEW_EPISODES
        assert RecordMode("all") == RecordMode.ALL
        assert RecordMode("once") == RecordMode.ONCE

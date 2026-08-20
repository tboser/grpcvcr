"""Tests for the Cassette API used directly, without a channel."""

from __future__ import annotations

from pathlib import Path

import pytest

from grpcvcr import Cassette, RecordMode
from grpcvcr.errors import NoMatchingInteractionError, RecordingDisabledError
from grpcvcr.serialization import (
    CassetteData,
    CassetteSerializer,
    Interaction,
    InteractionRequest,
    InteractionResponse,
)


class TestGetResponse:
    """`Cassette.get_response` looks an interaction up without going through a channel."""

    def _cassette(self, tmp_path: Path, record_mode: RecordMode) -> Cassette:
        path = tmp_path / "lookup.yaml"
        CassetteSerializer.save(
            path,
            CassetteData(
                interactions=[
                    Interaction(
                        request=InteractionRequest.from_grpc("/test/Method", b"req"),
                        response=InteractionResponse.from_grpc(b"resp", "OK"),
                        rpc_type="unary",
                    )
                ]
            ),
        )
        return Cassette(path, record_mode=record_mode)

    def test_returns_the_matching_interaction(self, tmp_path: Path) -> None:
        cassette = self._cassette(tmp_path, RecordMode.NONE)

        interaction = cassette.get_response("/test/Method", b"req")

        assert interaction.response.get_body_bytes() == b"resp"

    def test_raises_when_recording_is_disabled(self, tmp_path: Path) -> None:
        cassette = self._cassette(tmp_path, RecordMode.NONE)

        with pytest.raises(RecordingDisabledError):
            cassette.get_response("/test/Other", b"req")

    def test_raises_when_recording_is_allowed_but_nothing_matches(self, tmp_path: Path) -> None:
        cassette = self._cassette(tmp_path, RecordMode.NEW_EPISODES)

        with pytest.raises(NoMatchingInteractionError):
            cassette.get_response("/test/Other", b"req")

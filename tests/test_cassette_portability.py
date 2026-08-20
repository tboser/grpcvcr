"""A cassette is a plain, portable artifact.

The sync and async channels must record interchangeable cassettes, and the method
must be written as readable text rather than a binary blob.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from grpcvcr import AsyncRecordingChannel, Cassette, RecordingChannel, RecordMode

METHOD = "/test.TestService/GetUser"


def record_sync(path: Path, target: str, pb2, pb2_grpc) -> None:
    with Cassette(path, record_mode=RecordMode.ALL) as cassette, RecordingChannel(cassette, target) as recording:
        pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=3))


async def record_async(path: Path, target: str, pb2, pb2_grpc) -> None:
    with Cassette(path, record_mode=RecordMode.ALL) as cassette:
        async with AsyncRecordingChannel(cassette, target) as recording:
            await pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=3))


class TestRecordedMethodIsText:
    def test_sync(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        record_sync(tmp_cassette_path, grpc_target, pb2, pb2_grpc)

        assert yaml.safe_load(tmp_cassette_path.read_text())["interactions"][0]["request"]["method"] == METHOD

    @pytest.mark.asyncio
    async def test_async(self, grpc_target: str, tmp_cassette_path: Path, pb2, pb2_grpc) -> None:
        await record_async(tmp_cassette_path, grpc_target, pb2, pb2_grpc)

        assert yaml.safe_load(tmp_cassette_path.read_text())["interactions"][0]["request"]["method"] == METHOD


class TestCassettesReplayAcrossChannelKinds:
    @pytest.mark.asyncio
    async def test_sync_recorded_replays_on_async_channel(
        self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc
    ) -> None:
        record_sync(tmp_cassette_path, grpc_target, pb2, pb2_grpc)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        async with AsyncRecordingChannel(playback, grpc_target) as recording:
            response = await pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=3))

        assert response.user.id == 3
        assert grpc_servicer.call_count == 0

    @pytest.mark.asyncio
    async def test_async_recorded_replays_on_sync_channel(
        self, grpc_target: str, tmp_cassette_path: Path, grpc_servicer, pb2, pb2_grpc
    ) -> None:
        await record_async(tmp_cassette_path, grpc_target, pb2, pb2_grpc)

        grpc_servicer.call_count = 0
        playback = Cassette(tmp_cassette_path, record_mode=RecordMode.NONE)
        with RecordingChannel(playback, grpc_target) as recording:
            response = pb2_grpc.TestServiceStub(recording.channel).GetUser(pb2.GetUserRequest(id=3))

        assert response.user.id == 3
        assert grpc_servicer.call_count == 0

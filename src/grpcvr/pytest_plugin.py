"""pytest plugin for grpcvr integration.

This plugin provides fixtures for using grpcvr in pytest tests, allowing
automatic cassette management based on test names and pytest markers.

Example:
    ```python
    def test_my_grpc_call(grpcvr_cassette):
        with RecordingChannel(grpcvr_cassette, "localhost:50051") as channel:
            stub = MyServiceStub(channel.channel)
            response = stub.GetUser(GetUserRequest(id=1))
    ```
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from grpcvr.cassette import Cassette
from grpcvr.channel import AsyncRecordingChannel, RecordingChannel
from grpcvr.matchers import DEFAULT_MATCHER, Matcher
from grpcvr.record_modes import RecordMode

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add grpcvr command line options to pytest."""
    group = parser.getgroup("grpcvr")
    group.addoption(
        "--grpcvr-record",
        action="store",
        default=None,
        choices=["none", "new_episodes", "all", "once"],
        help="Override record mode for all cassettes",
    )
    group.addoption(
        "--grpcvr-cassette-dir",
        action="store",
        default="tests/cassettes",
        help="Default directory for cassette files",
    )


def pytest_configure(config: Config) -> None:
    """Register grpcvr markers with pytest."""
    config.addinivalue_line(
        "markers",
        "grpcvr(cassette, record_mode, match_on): Mark test to use a specific cassette configuration",
    )


@pytest.fixture
def grpcvr_cassette_dir(request: FixtureRequest) -> Path:
    """Get the cassette directory for the current test."""
    return Path(request.config.getoption("--grpcvr-cassette-dir"))


@pytest.fixture
def grpcvr_record_mode(request: FixtureRequest) -> RecordMode:
    """Get the record mode, considering CLI override and markers.

    Priority order:
    1. CLI option (--grpcvr-record)
    2. pytest.mark.grpcvr marker
    3. Default (NEW_EPISODES)
    """
    cli_mode = request.config.getoption("--grpcvr-record")
    if cli_mode:
        return RecordMode(cli_mode)

    marker = request.node.get_closest_marker("grpcvr")
    if marker and "record_mode" in marker.kwargs:
        mode = marker.kwargs["record_mode"]
        if isinstance(mode, RecordMode):
            return mode
        return RecordMode(mode)

    return RecordMode.NEW_EPISODES


@pytest.fixture
def grpcvr_cassette(
    request: FixtureRequest,
    grpcvr_cassette_dir: Path,
    grpcvr_record_mode: RecordMode,
) -> Generator[Cassette, None, None]:
    """Provide a cassette for the test.

    The cassette path is derived from the test name by default,
    or can be specified via the @pytest.mark.grpcvr marker.

    Example:
        ```python
        def test_my_feature(grpcvr_cassette):
            # Cassette at tests/cassettes/test_my_feature.yaml
            channel = RecordingChannel(grpcvr_cassette, "localhost:50051")
            ...
        ```

        ```python
        @pytest.mark.grpcvr(cassette="custom_name.yaml")
        def test_my_feature(grpcvr_cassette):
            # Cassette at tests/cassettes/custom_name.yaml
            ...
        ```

        ```python
        @pytest.mark.grpcvr(record_mode=RecordMode.ALL, match_on=MethodMatcher())
        def test_my_feature(grpcvr_cassette):
            # Uses ALL mode with method-only matching
            ...
        ```
    """
    marker = request.node.get_closest_marker("grpcvr")

    if marker and marker.args:
        cassette_name = marker.args[0]
    elif marker and "cassette" in marker.kwargs:
        cassette_name = marker.kwargs["cassette"]
    else:
        cassette_name = f"{request.node.name}.yaml"

    cassette_path = grpcvr_cassette_dir / cassette_name

    match_on: Matcher = DEFAULT_MATCHER
    if marker and "match_on" in marker.kwargs:
        match_on = marker.kwargs["match_on"]

    cassette = Cassette(
        path=cassette_path,
        record_mode=grpcvr_record_mode,
        match_on=match_on,
    )

    try:
        yield cassette
    finally:
        cassette.save()


@pytest.fixture
def grpcvr_channel(grpcvr_cassette: Cassette) -> Generator[RecordingChannel, None, None]:
    """Provide a recording channel (requires target to be specified).

    This fixture raises NotImplementedError because it requires a target.
    Use grpcvr_channel_factory or create a RecordingChannel directly
    with grpcvr_cassette instead.
    """
    raise NotImplementedError(
        "grpcvr_channel requires a target. Use grpcvr_channel_factory or create "
        "a RecordingChannel directly with grpcvr_cassette."
    )


@pytest.fixture
def grpcvr_channel_factory(
    grpcvr_cassette: Cassette,
) -> Generator[type[RecordingChannel], None, None]:
    """Provide a factory for creating recording channels.

    Example:
        ```python
        def test_my_feature(grpcvr_channel_factory, grpcvr_cassette):
            with grpcvr_channel_factory(grpcvr_cassette, "localhost:50051") as channel:
                stub = MyServiceStub(channel.channel)
                response = stub.GetUser(GetUserRequest(id=1))
        ```
    """
    yield RecordingChannel


@pytest.fixture
def grpcvr_async_channel_factory(
    grpcvr_cassette: Cassette,
) -> Generator[type[AsyncRecordingChannel], None, None]:
    """Provide a factory for creating async recording channels.

    Example:
        ```python
        async def test_my_feature(grpcvr_async_channel_factory, grpcvr_cassette):
            async with grpcvr_async_channel_factory(grpcvr_cassette, "localhost:50051") as channel:
                stub = MyServiceStub(channel.channel)
                response = await stub.GetUser(GetUserRequest(id=1))
        ```
    """
    yield AsyncRecordingChannel

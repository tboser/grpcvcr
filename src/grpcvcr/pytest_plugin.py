"""pytest plugin for grpcvcr integration.

This plugin provides fixtures for using grpcvcr in pytest tests, allowing
automatic cassette management based on test names and pytest markers.

Example:
    ```python
    def test_my_grpc_call(grpcvcr_cassette):
        with RecordingChannel(grpcvcr_cassette, "localhost:50051") as channel:
            stub = MyServiceStub(channel.channel)
            response = stub.GetUser(GetUserRequest(id=1))
    ```
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from grpcvcr.cassette import Cassette
from grpcvcr.channel import AsyncRecordingChannel, RecordingChannel
from grpcvcr.matchers import DEFAULT_MATCHER, Matcher
from grpcvcr.record_modes import RecordMode

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add grpcvcr command line options to pytest."""
    group = parser.getgroup("grpcvcr")
    group.addoption(
        "--grpcvcr-record",
        action="store",
        default=None,
        choices=["none", "new_episodes", "all", "once"],
        help="Override record mode for all cassettes",
    )
    group.addoption(
        "--grpcvcr-cassette-dir",
        action="store",
        default="tests/cassettes",
        help="Default directory for cassette files",
    )


def pytest_configure(config: Config) -> None:
    """Register grpcvcr markers with pytest."""
    config.addinivalue_line(
        "markers",
        "grpcvcr(cassette, record_mode, match_on): Mark test to use a specific cassette configuration",
    )


@pytest.fixture
def grpcvcr_cassette_dir(request: FixtureRequest) -> Path:
    """Get the cassette directory for the current test."""
    return Path(request.config.getoption("--grpcvcr-cassette-dir"))


@pytest.fixture
def grpcvcr_record_mode(request: FixtureRequest) -> RecordMode:
    """Get the record mode, considering CLI override and markers.

    Priority order:
    1. CLI option (--grpcvcr-record)
    2. pytest.mark.grpcvcr marker
    3. Default (NEW_EPISODES)
    """
    cli_mode = request.config.getoption("--grpcvcr-record")
    if cli_mode:
        return RecordMode(cli_mode)

    marker = request.node.get_closest_marker("grpcvcr")
    if marker and "record_mode" in marker.kwargs:
        mode = marker.kwargs["record_mode"]
        if isinstance(mode, RecordMode):
            return mode
        return RecordMode(mode)

    return RecordMode.NEW_EPISODES


@pytest.fixture
def grpcvcr_cassette(
    request: FixtureRequest,
    grpcvcr_cassette_dir: Path,
    grpcvcr_record_mode: RecordMode,
) -> Generator[Cassette, None, None]:
    """Provide a cassette for the test.

    The cassette path is derived from the test name by default,
    or can be specified via the @pytest.mark.grpcvcr marker.

    Example:
        ```python
        def test_my_feature(grpcvcr_cassette):
            # Cassette at tests/cassettes/test_my_feature.yaml
            channel = RecordingChannel(grpcvcr_cassette, "localhost:50051")
            ...
        ```

        ```python
        @pytest.mark.grpcvcr(cassette="custom_name.yaml")
        def test_my_feature(grpcvcr_cassette):
            # Cassette at tests/cassettes/custom_name.yaml
            ...
        ```

        ```python
        @pytest.mark.grpcvcr(record_mode=RecordMode.ALL, match_on=MethodMatcher())
        def test_my_feature(grpcvcr_cassette):
            # Uses ALL mode with method-only matching
            ...
        ```
    """
    marker = request.node.get_closest_marker("grpcvcr")

    if marker and marker.args:
        cassette_name = marker.args[0]
    elif marker and "cassette" in marker.kwargs:
        cassette_name = marker.kwargs["cassette"]
    else:
        cassette_name = f"{request.node.name}.yaml"

    cassette_path = grpcvcr_cassette_dir / cassette_name

    match_on: Matcher = DEFAULT_MATCHER
    if marker and "match_on" in marker.kwargs:
        match_on = marker.kwargs["match_on"]

    cassette = Cassette(
        path=cassette_path,
        record_mode=grpcvcr_record_mode,
        match_on=match_on,
    )

    try:
        yield cassette
    finally:
        cassette.save()


@pytest.fixture
def grpcvcr_channel(grpcvcr_cassette: Cassette) -> Generator[RecordingChannel, None, None]:
    """Provide a recording channel (requires target to be specified).

    This fixture raises NotImplementedError because it requires a target.
    Use grpcvcr_channel_factory or create a RecordingChannel directly
    with grpcvcr_cassette instead.
    """
    raise NotImplementedError(
        "grpcvcr_channel requires a target. Use grpcvcr_channel_factory or create "
        "a RecordingChannel directly with grpcvcr_cassette."
    )


@pytest.fixture
def grpcvcr_channel_factory(
    grpcvcr_cassette: Cassette,
) -> Generator[type[RecordingChannel], None, None]:
    """Provide a factory for creating recording channels.

    Example:
        ```python
        def test_my_feature(grpcvcr_channel_factory, grpcvcr_cassette):
            with grpcvcr_channel_factory(grpcvcr_cassette, "localhost:50051") as channel:
                stub = MyServiceStub(channel.channel)
                response = stub.GetUser(GetUserRequest(id=1))
        ```
    """
    yield RecordingChannel


@pytest.fixture
def grpcvcr_async_channel_factory(
    grpcvcr_cassette: Cassette,
) -> Generator[type[AsyncRecordingChannel], None, None]:
    """Provide a factory for creating async recording channels.

    Example:
        ```python
        async def test_my_feature(grpcvcr_async_channel_factory, grpcvcr_cassette):
            async with grpcvcr_async_channel_factory(grpcvcr_cassette, "localhost:50051") as channel:
                stub = MyServiceStub(channel.channel)
                response = await stub.GetUser(GetUserRequest(id=1))
        ```
    """
    yield AsyncRecordingChannel

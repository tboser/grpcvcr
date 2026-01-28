# pytest Integration

grpcvcr includes a pytest plugin that provides fixtures and markers for easy test integration.

## Installation

The plugin is automatically registered when you install grpcvcr. No additional configuration needed.

## Fixtures

### grpcvcr_cassette

Provides a `Cassette` instance for the test. By default, the cassette is named after the test function.

```python
# test: skip
from grpcvcr import RecordingChannel


def test_get_user(grpcvcr_cassette):
    # Cassette at: tests/cassettes/test_get_user.yaml
    with RecordingChannel(grpcvcr_cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        response = stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

### grpcvcr_cassette_dir

Returns the cassette directory path (default: `tests/cassettes`).

### grpcvcr_record_mode

Returns the current record mode, considering CLI overrides and markers.

### grpcvcr_channel_factory

Factory for creating recording channels.

```python
# test: skip
def test_with_factory(grpcvcr_cassette, grpcvcr_channel_factory):
    with grpcvcr_channel_factory(grpcvcr_cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        # ...
```

## Markers

Use `@pytest.mark.grpcvcr` to customize cassette behavior:

```python
# test: skip
import pytest

from grpcvcr import MethodMatcher, RecordMode, RequestMatcher


@pytest.mark.grpcvcr(cassette="custom_name.yaml")
def test_custom_cassette_name(grpcvcr_cassette):
    # Cassette at: tests/cassettes/custom_name.yaml
    ...


@pytest.mark.grpcvcr(record_mode=RecordMode.ALL)
def test_always_record(grpcvcr_cassette):
    # Always records, never replays
    ...


@pytest.mark.grpcvcr(match_on=MethodMatcher() & RequestMatcher())
def test_strict_matching(grpcvcr_cassette):
    # Match by method AND request body
    ...


@pytest.mark.grpcvcr(
    cassette="full_config.yaml",
    record_mode=RecordMode.NEW_EPISODES,
    match_on=MethodMatcher() & RequestMatcher(),
)
def test_full_configuration(grpcvcr_cassette):
    ...
```

## CLI Options

### --grpcvcr-record

Override record mode for all tests:

```bash
# test: skip
# Force re-record all cassettes
pytest --grpcvcr-record=all

# Playback only (fail if any interaction is missing)
pytest --grpcvcr-record=none

# Normal mode (record new, replay existing)
pytest --grpcvcr-record=new_episodes
```

### --grpcvcr-cassette-dir

Override the cassette directory:

```bash
# test: skip
pytest --grpcvcr-cassette-dir=my_cassettes/
```

## Example Test File

```python
# test: skip
import pytest

from grpcvcr import MethodMatcher, RecordingChannel, RecordMode, RequestMatcher


class TestUserService:
    """Tests for UserService gRPC calls."""

    def test_get_user(self, grpcvcr_cassette):
        with RecordingChannel(grpcvcr_cassette, "localhost:50051") as recording:
            stub = UserServiceStub(recording.channel)
            response = stub.GetUser(GetUserRequest(id=1))
            assert response.name == "Alice"

    def test_list_users(self, grpcvcr_cassette):
        with RecordingChannel(grpcvcr_cassette, "localhost:50051") as recording:
            stub = UserServiceStub(recording.channel)
            users = list(stub.ListUsers(ListUsersRequest(limit=10)))
            assert len(users) == 10

    @pytest.mark.grpcvcr(
        record_mode=RecordMode.ALL,
        match_on=MethodMatcher() & RequestMatcher(),
    )
    def test_create_user(self, grpcvcr_cassette):
        with RecordingChannel(grpcvcr_cassette, "localhost:50051") as recording:
            stub = UserServiceStub(recording.channel)
            response = stub.CreateUser(CreateUserRequest(name="Bob"))
            assert response.id > 0
```

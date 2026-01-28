# pytest Integration

grpcvr includes a pytest plugin that provides fixtures and markers for easy test integration.

## Installation

The plugin is automatically registered when you install grpcvr. No additional configuration needed.

## Fixtures

### grpcvr_cassette

Provides a `Cassette` instance for the test. By default, the cassette is named after the test function.

```python test="skip"
from grpcvr import RecordingChannel


def test_get_user(grpcvr_cassette):
    # Cassette at: tests/cassettes/test_get_user.yaml
    with RecordingChannel(grpcvr_cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        response = stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

### grpcvr_cassette_dir

Returns the cassette directory path (default: `tests/cassettes`).

### grpcvr_record_mode

Returns the current record mode, considering CLI overrides and markers.

### grpcvr_channel_factory

Factory for creating recording channels.

```python test="skip"
def test_with_factory(grpcvr_cassette, grpcvr_channel_factory):
    with grpcvr_channel_factory(grpcvr_cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        # ...
```

## Markers

Use `@pytest.mark.grpcvr` to customize cassette behavior:

```python test="skip"
import pytest

from grpcvr import MethodMatcher, RecordMode, RequestMatcher


@pytest.mark.grpcvr(cassette="custom_name.yaml")
def test_custom_cassette_name(grpcvr_cassette):
    # Cassette at: tests/cassettes/custom_name.yaml
    ...


@pytest.mark.grpcvr(record_mode=RecordMode.ALL)
def test_always_record(grpcvr_cassette):
    # Always records, never replays
    ...


@pytest.mark.grpcvr(match_on=MethodMatcher() & RequestMatcher())
def test_strict_matching(grpcvr_cassette):
    # Match by method AND request body
    ...


@pytest.mark.grpcvr(
    cassette="full_config.yaml",
    record_mode=RecordMode.NEW_EPISODES,
    match_on=MethodMatcher() & RequestMatcher(),
)
def test_full_configuration(grpcvr_cassette):
    ...
```

## CLI Options

### --grpcvr-record

Override record mode for all tests:

```bash test="skip"
# Force re-record all cassettes
pytest --grpcvr-record=all

# Playback only (fail if any interaction is missing)
pytest --grpcvr-record=none

# Normal mode (record new, replay existing)
pytest --grpcvr-record=new_episodes
```

### --grpcvr-cassette-dir

Override the cassette directory:

```bash test="skip"
pytest --grpcvr-cassette-dir=my_cassettes/
```

## Example Test File

```python test="skip"
import pytest

from grpcvr import MethodMatcher, RecordingChannel, RecordMode, RequestMatcher


class TestUserService:
    """Tests for UserService gRPC calls."""

    def test_get_user(self, grpcvr_cassette):
        with RecordingChannel(grpcvr_cassette, "localhost:50051") as recording:
            stub = UserServiceStub(recording.channel)
            response = stub.GetUser(GetUserRequest(id=1))
            assert response.name == "Alice"

    def test_list_users(self, grpcvr_cassette):
        with RecordingChannel(grpcvr_cassette, "localhost:50051") as recording:
            stub = UserServiceStub(recording.channel)
            users = list(stub.ListUsers(ListUsersRequest(limit=10)))
            assert len(users) == 10

    @pytest.mark.grpcvr(
        record_mode=RecordMode.ALL,
        match_on=MethodMatcher() & RequestMatcher(),
    )
    def test_create_user(self, grpcvr_cassette):
        with RecordingChannel(grpcvr_cassette, "localhost:50051") as recording:
            stub = UserServiceStub(recording.channel)
            response = stub.CreateUser(CreateUserRequest(name="Bob"))
            assert response.id > 0
```

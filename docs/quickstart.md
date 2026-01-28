# Quick Start

This guide will get you up and running with grpcvcr in minutes.

## Basic Usage

The simplest way to use grpcvcr is with the `recorded_channel` context manager:

```python test="skip"
from grpcvcr import recorded_channel

from myservice_pb2 import GetUserRequest
from myservice_pb2_grpc import UserServiceStub

# First run: records the interaction to the cassette file
# Subsequent runs: replays from the cassette (no network calls)
with recorded_channel("tests/cassettes/user.yaml", "localhost:50051") as channel:
    stub = UserServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
    print(response.name)
```

## Recording Modes

Control when grpcvcr records vs replays:

```python
from grpcvcr import RecordMode

# Available modes
print(RecordMode.NEW_EPISODES)  # Default: replay existing, record new
print(RecordMode.ALL)  # Always record (useful for updating cassettes)
print(RecordMode.NONE)  # Playback only (raises error if no match)
print(RecordMode.ONCE)  # Record once if cassette empty
```

## pytest Integration

grpcvcr includes a pytest plugin with helpful fixtures:

```python test="skip"
import pytest
from grpcvcr import RecordingChannel

from myservice_pb2 import GetUserRequest
from myservice_pb2_grpc import UserServiceStub


def test_get_user(grpcvcr_cassette):
    """Cassette automatically named after test: test_get_user.yaml"""
    with RecordingChannel(grpcvcr_cassette, "localhost:50051") as recording:
        stub = UserServiceStub(recording.channel)
        response = stub.GetUser(GetUserRequest(id=1))
        assert response.name == "Alice"
```

Use markers for custom configuration:

```python test="skip"
import pytest
from grpcvcr import MethodMatcher, RecordMode, RequestMatcher


@pytest.mark.grpcvcr(
    cassette="custom_name.yaml",
    record_mode=RecordMode.ALL,
    match_on=MethodMatcher() & RequestMatcher(),
)
def test_with_options(grpcvcr_cassette):
    pass
```

## Request Matching

By default, grpcvcr matches by method name. Customize matching for more precise control:

```python
from grpcvcr import MetadataMatcher, MethodMatcher, RequestMatcher

# Match by method AND request body
matcher = MethodMatcher() & RequestMatcher()
print(matcher)

# Match including specific metadata keys
matcher = MethodMatcher() & MetadataMatcher(keys=["authorization"])
print(matcher)
```

## Next Steps

- Learn about [Cassettes](concepts/cassettes.md) and how interactions are stored
- Explore [Request Matching](concepts/matchers.md) strategies
- Set up [pytest Integration](guides/pytest.md) for your test suite

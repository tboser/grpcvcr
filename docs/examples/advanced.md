# Advanced Patterns

Advanced usage patterns and techniques for grpcvcr.

## Custom Matchers

### Method-Only Matching

```python
# test: skip
from grpcvcr import MethodMatcher, recorded_channel

target = "localhost:50051"

with recorded_channel(
    "test.yaml",
    target,
    match_on=MethodMatcher(),
) as channel:
    stub = MyServiceStub(channel)
    # Any GetUser request will match the first recorded GetUser response
    response = stub.GetUser(GetUserRequest(id=1))
```

### Metadata Matching

```python
# test: skip
from grpcvcr import MetadataMatcher, recorded_channel

target = "localhost:50051"

with recorded_channel(
    "test.yaml",
    target,
    match_on=MetadataMatcher(keys=["authorization"]),
) as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(
        GetUserRequest(id=1),
        metadata=[("authorization", "***")],
    )
```

### Combining Matchers

```python
from grpcvcr import MetadataMatcher, MethodMatcher, RequestMatcher

# Match method AND request body
matcher = MethodMatcher() & RequestMatcher()

# Match method AND specific metadata keys
matcher = MethodMatcher() & MetadataMatcher(keys=["authorization"])
```

### Custom Match Functions

```python
# test: skip
from grpcvcr import CustomMatcher, MethodMatcher
from grpcvcr.serialization import InteractionRequest


def match_by_user_id(request: InteractionRequest, recorded: InteractionRequest) -> bool:
    """Match if the user ID in the request body matches."""
    # Parse your protobuf and compare specific fields
    req_body = YourRequest.FromString(request.get_body_bytes())
    rec_body = YourRequest.FromString(recorded.get_body_bytes())
    return req_body.user_id == rec_body.user_id


matcher = MethodMatcher() & CustomMatcher(func=match_by_user_id)
```

## Cassette Formats

### YAML (Default)

```yaml
# test.yaml
interactions:
  - request:
      method: /myservice.MyService/GetUser
      body_base64: CAE=
      metadata: []
    response:
      body_base64: CgVBbGljZQ==
      code: OK
      details: ""
```

### JSON

```python
# test: skip
from grpcvcr import recorded_channel

target = "localhost:50051"

with recorded_channel("test.json", target) as channel:
    ...
```

The format is determined by the file extension.

## Error Handling

### Catching Recording Errors

```python
# test: skip
from grpcvcr import RecordMode, recorded_channel
from grpcvcr.errors import RecordingDisabledError

target = "localhost:50051"

try:
    with recorded_channel(
        "test.yaml", target, record_mode=RecordMode.NONE
    ) as channel:
        stub = MyServiceStub(channel)
        # This will fail if not in cassette
        stub.GetUser(GetUserRequest(id=999))
except RecordingDisabledError as e:
    print(f"No recorded interaction for: {e.method}")
```

### Secure Channels

```python
# test: skip
import grpc

from grpcvcr import recorded_channel

credentials = grpc.ssl_channel_credentials()

with recorded_channel(
    "test.yaml",
    "api.example.com:443",
    credentials=credentials,
) as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
```

### Channel Options

```python
# test: skip
from grpcvcr import recorded_channel

target = "localhost:50051"

with recorded_channel(
    "test.yaml",
    target,
    options=[
        ("grpc.max_receive_message_length", 1024 * 1024 * 10),
        ("grpc.max_send_message_length", 1024 * 1024 * 10),
    ],
) as channel:
    ...
```

## Recording gRPC Errors

gRPC errors are recorded and replayed:

```python
# test: skip
import grpc

from grpcvcr import RecordMode, recorded_channel

target = "localhost:50051"

# Record an error response
with recorded_channel("error_test.yaml", target) as channel:
    stub = MyServiceStub(channel)
    try:
        stub.GetUser(GetUserRequest(id=999))  # Returns NOT_FOUND
    except grpc.RpcError as e:
        assert e.code() == grpc.StatusCode.NOT_FOUND

# Replay the error
with recorded_channel(
    "error_test.yaml", target, record_mode=RecordMode.NONE
) as channel:
    stub = MyServiceStub(channel)
    try:
        stub.GetUser(GetUserRequest(id=999))
    except grpc.RpcError as e:
        # Same error is replayed
        assert e.code() == grpc.StatusCode.NOT_FOUND
```

## Parallel Test Isolation

```python
# test: skip
import pytest

from grpcvcr import Cassette, RecordingChannel


@pytest.fixture
def cassette_path(tmp_path, request):
    """Generate unique cassette path per test."""
    return tmp_path / f"{request.node.name}.yaml"


def test_one(cassette_path, grpc_target):
    cassette = Cassette(cassette_path)
    ...


def test_two(cassette_path, grpc_target):
    cassette = Cassette(cassette_path)
    ...
```

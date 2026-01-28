# Advanced Patterns

This page covers advanced usage patterns for grpcvr.

## Custom Request Matching

By default, grpcvr matches requests by method name and request body. You can customize this behavior with matchers.

### Match by Method Only

Useful when request bodies contain timestamps or random IDs:

```python
from grpcvr import recorded_channel, MethodMatcher

with recorded_channel(
    "test.yaml",
    target,
    match_on=MethodMatcher(),
) as channel:
    stub = MyServiceStub(channel)
    # Any GetUser request will match the first recorded GetUser response
    response = stub.GetUser(GetUserRequest(id=1))
```

### Match by Specific Metadata

Match requests based on specific metadata keys:

```python
from grpcvr import recorded_channel, MetadataMatcher

with recorded_channel(
    "test.yaml",
    target,
    match_on=MetadataMatcher(keys=["authorization"]),
) as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(
        GetUserRequest(id=1),
        metadata=[("authorization", "Bearer token123")],
    )
```

### Ignore Dynamic Metadata

Ignore metadata that changes between requests:

```python
from grpcvr import MetadataMatcher

matcher = MetadataMatcher(ignore_keys=["x-request-id", "x-timestamp"])
```

### Combining Matchers

Combine matchers with the `&` operator:

```python
from grpcvr import MethodMatcher, RequestMatcher, MetadataMatcher

# Match method AND request body
matcher = MethodMatcher() & RequestMatcher()

# Match method AND specific metadata
matcher = MethodMatcher() & MetadataMatcher(keys=["authorization"])
```

### Custom Matcher Functions

For complex matching logic, use `CustomMatcher`:

```python
from grpcvr import CustomMatcher, MethodMatcher
from grpcvr.serialization import InteractionRequest

def match_by_user_id(request: InteractionRequest, recorded: InteractionRequest) -> bool:
    """Match if the user ID in the request body matches."""
    # Parse your protobuf and compare specific fields
    req_body = YourRequest.FromString(request.get_body_bytes())
    rec_body = YourRequest.FromString(recorded.get_body_bytes())
    return req_body.user_id == rec_body.user_id

matcher = MethodMatcher() & CustomMatcher(func=match_by_user_id)
```

## Working with Cassette Files

### Cassette Format

Cassettes are stored as YAML (or JSON) files:

```yaml
version: 1
interactions:
  - request:
      method: /mypackage.MyService/GetUser
      body: CAE=  # base64-encoded protobuf
      metadata:
        authorization:
          - Bearer token123
    response:
      body: CAESBUFsaWNl  # base64-encoded protobuf
      code: OK
      details: null
      trailing_metadata: {}
    rpc_type: unary
```

### Inspecting Cassettes

Load and inspect recorded interactions:

```python
from grpcvr import Cassette

cassette = Cassette("test.yaml")

for interaction in cassette.interactions:
    print(f"Method: {interaction.request.method}")
    print(f"RPC Type: {interaction.rpc_type}")
    print(f"Status: {interaction.response.code}")
```

### JSON Format

Use `.json` extension for JSON format:

```python
with recorded_channel("test.json", target) as channel:
    ...
```

## Error Handling

### Handling Missing Cassettes

```python
from grpcvr import Cassette, RecordMode
from grpcvr.errors import CassetteNotFoundError

try:
    cassette = Cassette("missing.yaml", record_mode=RecordMode.NONE)
except CassetteNotFoundError as e:
    print(f"Cassette not found: {e.path}")
```

### Handling Unmatched Requests

```python
from grpcvr import recorded_channel, RecordMode
from grpcvr.errors import RecordingDisabledError

try:
    with recorded_channel("test.yaml", target, record_mode=RecordMode.NONE) as channel:
        stub = MyServiceStub(channel)
        # This will fail if not in cassette
        stub.GetUser(GetUserRequest(id=999))
except RecordingDisabledError as e:
    print(f"No recorded interaction for: {e.method}")
```

## Secure Channels

Use credentials for TLS connections:

```python
import grpc
from grpcvr import recorded_channel

credentials = grpc.ssl_channel_credentials()

with recorded_channel(
    "test.yaml",
    "myservice.example.com:443",
    credentials=credentials,
) as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
```

## Channel Options

Pass gRPC channel options:

```python
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

## Testing Recorded Errors

grpcvr records and replays gRPC errors:

```python
import grpc
from grpcvr import recorded_channel, RecordMode

# Record an error response
with recorded_channel("error_test.yaml", target) as channel:
    stub = MyServiceStub(channel)
    try:
        stub.GetUser(GetUserRequest(id=999))  # Returns NOT_FOUND
    except grpc.RpcError as e:
        assert e.code() == grpc.StatusCode.NOT_FOUND

# Replay the error
with recorded_channel("error_test.yaml", target, record_mode=RecordMode.NONE) as channel:
    stub = MyServiceStub(channel)
    try:
        stub.GetUser(GetUserRequest(id=999))
    except grpc.RpcError as e:
        # Same error is replayed
        assert e.code() == grpc.StatusCode.NOT_FOUND
        assert "not found" in e.details().lower()
```

## Parallel Test Execution

Each test should use its own cassette file to avoid conflicts:

```python
import pytest
from grpcvr import Cassette, RecordingChannel

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

The built-in `cassette` fixture from the pytest plugin already handles this automatically.

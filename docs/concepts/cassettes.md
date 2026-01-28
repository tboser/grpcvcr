# Cassettes

Cassettes store recorded gRPC interactions for replay during tests.

## What is a Cassette?

A cassette is a file (YAML or JSON) containing recorded gRPC request/response pairs. When you run tests with grpcvcr, interactions are recorded to cassettes on the first run and replayed from cassettes on subsequent runs.

## Cassette Format

Cassettes are stored as YAML by default:

```yaml
# test: skip
interactions:
  - request:
      method: /myservice.UserService/GetUser
      body: "base64-encoded-protobuf"
      metadata:
        authorization:
          - "Bearer token123"
    response:
      body: "base64-encoded-protobuf"
      code: OK
      trailing_metadata: {}
      response_type: "myservice.user_pb2.GetUserResponse"
    rpc_type: unary
    recorded_at: "2024-01-15T10:30:00Z"
```

## Cassette Location

By default, cassettes are stored in `tests/cassettes/`. You can customize this:

```python
# test: skip
from grpcvcr import Cassette

# Explicit path
cassette = Cassette("path/to/my_cassette.yaml")

# JSON format
cassette = Cassette("path/to/my_cassette.json")
```

With pytest:

```bash
# test: skip
# Override cassette directory
pytest --grpcvcr-cassette-dir=my_cassettes/
```

## Managing Cassettes

### Updating Cassettes

To re-record all interactions:

```python
# test: skip
from grpcvcr import Cassette, RecordMode

cassette = Cassette("test.yaml", record_mode=RecordMode.ALL)
```

Or via CLI:

```bash
# test: skip
pytest --grpcvcr-record=all
```

### Committing Cassettes

Cassettes should be committed to version control. This allows:

- Reproducible tests across machines
- CI/CD without live services
- Code review of expected responses

### Clearing Old Cassettes

Delete cassette files to force re-recording:

```bash
# test: skip
rm tests/cassettes/*.yaml
pytest  # Re-records all cassettes
```

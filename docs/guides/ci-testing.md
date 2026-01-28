# CI/CD Testing

Best practices for using grpcvcr in continuous integration environments.

## Automatic CI Detection

grpcvcr automatically detects CI environments and sets `RecordMode.NONE` by default. This ensures tests fail fast if cassettes are missing or outdated.

```python
from grpcvcr import RecordingChannel


# No special configuration needed - this just works in CI
def test_get_user(cassette, grpc_target):
    channel = RecordingChannel(cassette, grpc_target)
    stub = MyServiceStub(channel.channel)
    stub.GetUser(GetUserRequest(id=1))
    channel.close()
```

CI is detected via the `CI` environment variable (set by GitHub Actions, GitLab CI, CircleCI, etc.).

## GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[test]"

      - name: Run tests
        run: pytest tests/ -v
```

## Cassette Management

### Committing Cassettes

Cassettes should be committed to version control:

```text
tests/
  cassettes/
    test_get_user.yaml
    test_create_user.yaml
    test_list_users.yaml
```

This ensures reproducible tests across environments.

### Updating Cassettes

When API responses change, re-record cassettes locally:

```bash
# Re-record all cassettes
pytest tests/ --grpcvcr-record=all

# Re-record specific tests
pytest tests/test_users.py --grpcvcr-record=all
```

Then commit the updated cassettes.

### Cassette Naming

The pytest plugin automatically names cassettes after tests:

- `test_get_user` -> `tests/cassettes/test_get_user.yaml`
- `test_users.py::TestUserAPI::test_create` -> `tests/cassettes/test_users/TestUserAPI/test_create.yaml`

## Debugging CI Failures

### Common Errors

**CassetteNotFoundError**: The cassette file doesn't exist.

```text
grpcvcr.errors.CassetteNotFoundError: Cassette not found: tests/cassettes/test_new_feature.yaml
```

Solution: Record the cassette locally and commit it.

**NoMatchingInteractionError**: No recorded interaction matches the request.

```text
grpcvcr.errors.NoMatchingInteractionError: No matching interaction for method: /myservice.MyService/GetUser
```

Solution: The request has changed. Re-record the cassette.

**RecordingDisabledError**: Attempted to record in CI.

```text
grpcvcr.errors.RecordingDisabledError: Recording disabled for method: /myservice.MyService/NewEndpoint
```

Solution: Record the new interaction locally first.

### Inspecting Cassettes

Cassettes are human-readable YAML/JSON:

```yaml
interactions:
  - request:
      method: /myservice.MyService/GetUser
      body_base64: CAE=
      metadata:
        - ["authorization", "Bearer ***"]
    response:
      body_base64: CgVBbGljZQ==
      code: OK
      details: ""
```

### Force Recording in CI

For special cases (like integration test suites), you can override:

```yaml
- name: Run integration tests
  run: pytest tests/integration/ --grpcvcr-record=all
  env:
    GRPC_TARGET: ${{ secrets.STAGING_GRPC_TARGET }}
```

**Warning**: This makes tests non-deterministic. Use sparingly.

## Best Practices

### 1. Keep Cassettes Small

Record only what's needed for each test. Avoid recording unnecessary metadata:

```python
from grpcvcr import MetadataMatcher, recorded_channel

target = "localhost:50051"

# Ignore volatile metadata
with recorded_channel(
    "test.yaml",
    target,
    match_on=MetadataMatcher(ignore_keys=["x-request-id", "date"]),
) as channel:
    ...
```

### 2. Use Meaningful Test Names

Since cassettes are named after tests, use descriptive names:

```python
# Good
def test_get_user_returns_not_found_for_invalid_id():
    ...


# Bad
def test_1():
    ...
```

### 3. Separate Recording and Playback Tests

For complex scenarios, consider separate test files:

```text
tests/
  test_users.py           # Normal tests (playback in CI)
  test_users_record.py    # Recording tests (skip in CI)
```

### 4. Review Cassette Changes

Treat cassette changes like code changes in PR reviews:

- Are new fields being recorded?
- Has response structure changed?
- Are sensitive values properly filtered?

### 5. Environment-Specific Cassettes

For tests that differ by environment:

```python
import os
from pathlib import Path

import pytest


@pytest.fixture
def cassette_path(request):
    env = os.environ.get("TEST_ENV", "default")
    base_dir = Path("tests/cassettes") / env
    return base_dir / f"{request.node.name}.yaml"
```

## Security Considerations

### Sensitive Data

Never commit cassettes with real credentials. Filter sensitive metadata:

```python
from grpcvcr import MetadataMatcher, recorded_channel

target = "localhost:50051"

# Use test-safe credentials during recording
with recorded_channel(
    "test.yaml",
    target,
    match_on=MetadataMatcher(ignore_keys=["authorization", "x-api-key"]),
) as channel:
    ...
```

### Secrets in CI

Use environment variables for real credentials:

```yaml
- name: Run tests
  run: pytest tests/
  env:
    GRPC_TARGET: ${{ secrets.GRPC_TARGET }}
    API_KEY: ${{ secrets.API_KEY }}
```

Cassettes will use recorded responses, not make real calls in CI.

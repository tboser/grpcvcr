# CI/CD Testing Patterns

This guide covers best practices for using grpcvr in continuous integration environments.

## Basic CI Setup

The key principle: **record locally, playback in CI**.

1. Run tests locally with `RecordMode.NEW_EPISODES` (default) to record interactions
2. Commit cassette files to version control
3. Run tests in CI with `RecordMode.NONE` to ensure all interactions are pre-recorded

## Automatic CI Detection

grpcvr's pytest plugin automatically switches to `RecordMode.NONE` when the `CI` environment variable is set:

```python
# No special configuration needed - this just works in CI
def test_get_user(cassette, grpc_target):
    channel = RecordingChannel(cassette, grpc_target)
    stub = MyServiceStub(channel.channel)
    response = stub.GetUser(GetUserRequest(id=1))
    channel.close()
```

Most CI systems (GitHub Actions, GitLab CI, CircleCI, etc.) set `CI=true` automatically.

## GitHub Actions Example

```yaml
name: CI

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
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest
        # CI=true is set automatically by GitHub Actions
        # Tests will use RecordMode.NONE
```

## Explicit Record Mode Override

Override the record mode via CLI for all tests:

```bash
# Force playback only (fail if cassette missing)
pytest --grpcvr-record=none

# Force recording (refresh all cassettes)
pytest --grpcvr-record=all

# Record new interactions only
pytest --grpcvr-record=new_episodes
```

## Cassette Directory Configuration

Configure the default cassette directory:

```bash
# Use custom cassette directory
pytest --grpcvr-cassette-dir=fixtures/cassettes
```

Or in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--grpcvr-cassette-dir=tests/fixtures/cassettes"
```

## Handling Cassette Drift

When your API changes, cassettes may become outdated. Strategies to handle this:

### 1. Refresh All Cassettes

```bash
# Locally, with a running server
pytest --grpcvr-record=all
git add tests/cassettes/
git commit -m "Refresh cassettes for API v2"
```

### 2. Refresh Specific Tests

```bash
# Re-record specific test cassettes
pytest tests/test_users.py --grpcvr-record=all
```

### 3. Delete and Re-record

```bash
rm -rf tests/cassettes/
pytest --grpcvr-record=new_episodes
```

## Failing Fast on Missing Cassettes

In CI, you want tests to fail immediately if a cassette is missing rather than attempting to record:

```python
from grpcvr.errors import CassetteNotFoundError, RecordingDisabledError

# These errors indicate missing or mismatched cassettes:
# - CassetteNotFoundError: Cassette file doesn't exist
# - RecordingDisabledError: No matching interaction in cassette
```

Both errors will cause test failures in CI, making it clear that cassettes need to be updated.

## Cassette Versioning Strategy

### Commit Cassettes to Git

The recommended approach is to commit cassettes alongside your tests:

```
tests/
├── cassettes/
│   ├── test_get_user.yaml
│   ├── test_list_users.yaml
│   └── TestUserService/
│       └── test_create_user.yaml
├── test_users.py
└── conftest.py
```

Benefits:
- Cassettes are versioned with code
- PRs show cassette changes for review
- Easy to see what API interactions tests depend on

### .gitignore Considerations

Don't ignore cassettes:

```gitignore
# Don't add this!
# tests/cassettes/
```

You may want to ignore temporary test cassettes:

```gitignore
# Ignore temp cassettes from local debugging
tests/cassettes/tmp_*.yaml
```

## Parallel Test Execution

grpcvr cassettes work with parallel test execution (pytest-xdist):

```bash
pytest -n auto
```

Each test uses its own cassette file, so there are no conflicts. The pytest plugin generates unique cassette paths based on test names.

## Debugging CI Failures

When tests fail in CI due to cassette issues:

### 1. Check for Missing Cassettes

```bash
# List all cassette files
find tests/cassettes -name "*.yaml" | sort

# Compare with test files
pytest --collect-only -q | grep "test_"
```

### 2. Validate Cassette Contents

```python
from grpcvr import Cassette

cassette = Cassette("tests/cassettes/test_get_user.yaml")
for i, interaction in enumerate(cassette.interactions):
    print(f"{i}: {interaction.request.method} -> {interaction.response.code}")
```

### 3. Re-record Locally

```bash
# Delete the problematic cassette
rm tests/cassettes/test_failing.yaml

# Run the test to re-record
pytest tests/test_module.py::test_failing -v

# Verify and commit
git diff tests/cassettes/
git add tests/cassettes/test_failing.yaml
```

## Environment-Specific Cassettes

If you need different cassettes for different environments:

```python
import os
import pytest
from pathlib import Path

@pytest.fixture
def cassette_path(request):
    env = os.environ.get("TEST_ENV", "default")
    base_dir = Path("tests/cassettes") / env
    return base_dir / f"{request.node.name}.yaml"
```

## Security Considerations

Cassettes may contain sensitive data. Before committing:

1. **Review cassettes** for secrets, tokens, or PII
2. **Sanitize metadata** using `MetadataMatcher(ignore_keys=["authorization"])`
3. **Use test credentials** that are safe to commit
4. **Consider `.gitignore`** for cassettes with real credentials

```python
# Use test-safe credentials during recording
with recorded_channel(
    "test.yaml",
    target,
    match_on=MetadataMatcher(ignore_keys=["authorization", "x-api-key"]),
) as channel:
    ...
```

# Handoff: Get Test Coverage to 100%

## Current State

- **48 tests passing**, all linting/type checking passes
- **Coverage at 81.37%** (target: 100%)
- Docs infrastructure set up with mkdocs + mkdocstrings

## Coverage Gaps

Run `make testcov` to see current coverage. Main gaps:

| File | Coverage | Missing |
|------|----------|---------|
| `interceptors/aio.py` | 50.75% | Async interceptor methods |
| `interceptors/_base.py` | 65.38% | `_FakeUnaryCall` and `_FakeStreamingCall` helper methods |
| `channel.py` | 67.69% | `AsyncRecordingChannel` class |
| `cassette.py` | 86.11% | JSON format, some edge cases |
| `serialization.py` | 90.41% | Some edge cases |
| `matchers.py` | 95.06% | Lines 59, 121 |

## What Needs to Be Done

### 1. Add Async Integration Tests

Create `tests/test_integration_async.py` mirroring `tests/test_integration.py` but using:
- `AsyncRecordingChannel` instead of `RecordingChannel`
- `pytest.mark.asyncio` decorator
- `async with` context managers
- `async for` for streaming

Example pattern:
```python
@pytest.mark.asyncio
async def test_async_unary_call(grpc_target, tmp_cassette_path, grpc_servicer, pb2, pb2_grpc):
    cassette = Cassette(tmp_cassette_path, record_mode=RecordMode.ALL)
    async with AsyncRecordingChannel(cassette, grpc_target) as recording:
        stub = pb2_grpc.TestServiceStub(recording.channel)
        response = await stub.GetUser(pb2.GetUserRequest(id=42))
    assert response.user.id == 42
```

### 2. Test the Fake Call Objects

The `_FakeUnaryCall` and `_FakeStreamingCall` classes in `interceptors/_base.py` have many untested methods (like `cancelled()`, `running()`, `exception()`, etc.). Add unit tests for these.

### 3. Test Edge Cases

- JSON cassette format (currently only YAML tested)
- Error paths in `cassette.py` (lines 67, 77, 161, 164, 196-204)
- Matchers edge cases (lines 59, 121)

## Key Files

- `tests/conftest.py` - Has `GrpcTestServer` fixture that works for both sync and async
- `tests/test_integration.py` - Sync tests to mirror for async
- `src/grpcvr/channel.py` - `AsyncRecordingChannel` class (lines 196-243)
- `src/grpcvr/interceptors/aio.py` - Async interceptors

## Commands

```bash
make testcov          # Run tests with coverage report
make test             # Run tests without coverage
make lint             # Run linter
make typecheck        # Run type checker
```

## Notes

- The grpc.aio stubs may need different handling than sync stubs
- Coverage config excludes `pytest_plugin.py` and `_version.py` (see `pyproject.toml`)
- Tests run with `-p no:grpcvr` to disable the pytest plugin during coverage measurement

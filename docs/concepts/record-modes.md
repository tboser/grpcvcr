# Record Modes

Record modes control when grpcvr records new interactions versus playing back existing ones.

## Available Modes

### NONE

Playback only. Never records new interactions.

```python test="skip"
from grpcvr import Cassette, RecordMode

cassette = Cassette("test.yaml", record_mode=RecordMode.NONE)
```

- If a matching interaction exists: returns recorded response
- If no match: raises `RecordingDisabledError`
- If cassette doesn't exist: raises `CassetteNotFoundError`

**Use case**: CI/CD pipelines where you want to ensure all interactions are pre-recorded.

### NEW_EPISODES

Records new interactions, replays existing ones. This is the default mode.

```python test="skip"
from grpcvr import Cassette, RecordMode

cassette = Cassette("test.yaml", record_mode=RecordMode.NEW_EPISODES)
```

- If a matching interaction exists: returns recorded response
- If no match: makes real call, records it, returns response

**Use case**: Normal development workflow.

### ALL

Always records, never replays.

```python test="skip"
from grpcvr import Cassette, RecordMode

cassette = Cassette("test.yaml", record_mode=RecordMode.ALL)
```

- Always makes real calls
- Always overwrites cassette with new recordings

**Use case**: Updating cassettes after API changes.

### ONCE

Records once if cassette is empty, then playback only.

```python test="skip"
from grpcvr import Cassette, RecordMode

cassette = Cassette("test.yaml", record_mode=RecordMode.ONCE)
```

- If cassette is empty: records interactions
- If cassette has content: playback only (like NONE)

**Use case**: Initial test setup.

## CLI Override

Override record mode for all tests:

```bash test="skip"
# Force re-record everything
pytest --grpcvr-record=all

# Playback only (fail if missing)
pytest --grpcvr-record=none
```

## Comparison Table

| Mode | Cassette Empty | Match Found | No Match |
|------|---------------|-------------|----------|
| NONE | Error | Playback | Error |
| NEW_EPISODES | Record | Playback | Record |
| ALL | Record | Record | Record |
| ONCE | Record | Playback | Error |

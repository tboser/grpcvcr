# Record Modes

Record modes control when grpcvr records new interactions versus playing back existing ones.

## Overview

```python
from grpcvr import RecordMode

# Always record (useful for updating cassettes)
print(RecordMode.ALL)

# Never record (playback only, raises if no match)
print(RecordMode.NONE)

# Record only new interactions (default)
print(RecordMode.NEW_EPISODES)

# Record once if cassette empty
print(RecordMode.ONCE)
```

## Mode Comparison

| Mode | Existing Match | No Match |
|------|---------------|----------|
| `NONE` | Playback | Raises error |
| `NEW_EPISODES` | Playback | Record |
| `ALL` | Record | Record |
| `ONCE` | Playback | Record (if cassette empty) |

## API Reference

::: grpcvr.RecordMode
    options:
      members:
        - NONE
        - NEW_EPISODES
        - ALL
        - ONCE

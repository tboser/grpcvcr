# Errors

Exception classes raised by grpcvcr.

## Overview

All grpcvcr exceptions inherit from `GrpcvrError`, making it easy to catch any grpcvcr-specific error.

```python test="skip"
from grpcvcr import (
    CassetteNotFoundError,
    GrpcvrError,
    RecordingDisabledError,
    RecordMode,
    recorded_channel,
)

try:
    with recorded_channel(
        "missing.yaml", "localhost:50051", record_mode=RecordMode.NONE
    ) as channel:
        ...
except CassetteNotFoundError:
    print("Cassette file not found")
except RecordingDisabledError:
    print("No matching interaction and recording is disabled")
except GrpcvrError:
    print("Some other grpcvcr error")
```

## API Reference

::: grpcvcr.GrpcvrError

::: grpcvcr.CassetteNotFoundError

::: grpcvcr.CassetteWriteError

::: grpcvcr.NoMatchingInteractionError

::: grpcvcr.RecordingDisabledError

::: grpcvcr.SerializationError

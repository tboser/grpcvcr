# Errors

Exception classes raised by grpcvr.

## Overview

All grpcvr exceptions inherit from `GrpcvrError`, making it easy to catch any grpcvr-specific error.

```python test="skip"
from grpcvr import (
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
    print("Some other grpcvr error")
```

## API Reference

::: grpcvr.GrpcvrError

::: grpcvr.CassetteNotFoundError

::: grpcvr.CassetteWriteError

::: grpcvr.NoMatchingInteractionError

::: grpcvr.RecordingDisabledError

::: grpcvr.SerializationError

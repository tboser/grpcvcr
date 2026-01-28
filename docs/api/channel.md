# Channel

Recording channel wrappers that intercept gRPC calls for recording and playback.

## Overview

grpcvr provides channel wrappers that intercept all gRPC calls, recording them during the first run and replaying them from the cassette on subsequent runs.

```python test="skip"
from grpcvr import RecordMode, recorded_channel

# Simple usage with context manager
with recorded_channel("test.yaml", "localhost:50051", record_mode=RecordMode.ALL) as channel:
    stub = MyServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
```

## API Reference

::: grpcvr.RecordingChannel
    options:
      members:
        - __init__
        - __enter__
        - __exit__
        - channel

::: grpcvr.recorded_channel

# Cassette

The `Cassette` class is the core container for recording and replaying gRPC interactions.

## Overview

A cassette stores a collection of recorded gRPC interactions (request/response pairs) and provides methods to find matching interactions during playback.

```python
# test: skip
from grpcvcr import Cassette, RecordMode, RecordingChannel

# Create a cassette for recording
cassette = Cassette("tests/cassettes/my_test.yaml", record_mode=RecordMode.NEW_EPISODES)

# Use with a RecordingChannel
with RecordingChannel(cassette, "localhost:50051") as recording:
    stub = MyServiceStub(recording.channel)
    response = stub.GetUser(GetUserRequest(id=1))
```

## API Reference

::: grpcvcr.Cassette
    options:
      members:
        - __init__
        - load
        - save
        - find_interaction
        - record_interaction
        - interactions
        - record_mode
        - can_record

::: grpcvcr.use_cassette

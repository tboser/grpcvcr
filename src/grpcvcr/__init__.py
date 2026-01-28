"""grpcvcr - Record and replay gRPC interactions for testing.

grpcvcr (gRPC Video Recorder) is a library for recording and replaying gRPC
interactions, similar to VCR.py for HTTP. It's designed to make testing
gRPC services easier by allowing you to record real interactions and
replay them in tests.

Example:
    ```python
    from grpcvcr import recorded_channel, RecordMode

    # Record interactions to a cassette file
    with recorded_channel("test.yaml", "localhost:50051", record_mode=RecordMode.ALL) as channel:
        stub = MyServiceStub(channel)
        response = stub.GetUser(GetUserRequest(id=1))

    # Play back interactions (no network calls made)
    with recorded_channel("test.yaml", "localhost:50051", record_mode=RecordMode.NONE) as channel:
        stub = MyServiceStub(channel)
        response = stub.GetUser(GetUserRequest(id=1))  # Returns recorded response
    ```
"""

from grpcvcr._version import __version__
from grpcvcr.cassette import Cassette, use_cassette
from grpcvcr.channel import (
    AsyncRecordingChannel,
    RecordingChannel,
    async_recorded_channel,
    recorded_channel,
)
from grpcvcr.errors import (
    CassetteNotFoundError,
    CassetteWriteError,
    GrpcvcrError,
    NoMatchingInteractionError,
    RecordingDisabledError,
    SerializationError,
)
from grpcvcr.matchers import (
    AllMatcher,
    CustomMatcher,
    Matcher,
    MetadataMatcher,
    MethodMatcher,
    RequestMatcher,
)
from grpcvcr.record_modes import RecordMode

__all__ = [
    "__version__",
    "AllMatcher",
    "AsyncRecordingChannel",
    "Cassette",
    "CassetteNotFoundError",
    "CassetteWriteError",
    "CustomMatcher",
    "GrpcvcrError",
    "Matcher",
    "MetadataMatcher",
    "MethodMatcher",
    "NoMatchingInteractionError",
    "RecordingChannel",
    "RecordingDisabledError",
    "RecordMode",
    "RequestMatcher",
    "SerializationError",
    "async_recorded_channel",
    "recorded_channel",
    "use_cassette",
]

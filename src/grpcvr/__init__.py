"""grpcvr - Record and replay gRPC interactions for testing.

grpcvr (gRPC Video Recorder) is a library for recording and replaying gRPC
interactions, similar to VCR.py for HTTP. It's designed to make testing
gRPC services easier by allowing you to record real interactions and
replay them in tests.

Example:
    ```python
    from grpcvr import recorded_channel, RecordMode

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

from grpcvr._version import __version__
from grpcvr.cassette import Cassette, use_cassette
from grpcvr.channel import (
    AsyncRecordingChannel,
    RecordingChannel,
    async_recorded_channel,
    recorded_channel,
)
from grpcvr.errors import (
    CassetteNotFoundError,
    CassetteWriteError,
    GrpcvrError,
    NoMatchingInteractionError,
    RecordingDisabledError,
    SerializationError,
)
from grpcvr.matchers import (
    AllMatcher,
    CustomMatcher,
    Matcher,
    MetadataMatcher,
    MethodMatcher,
    RequestMatcher,
)
from grpcvr.record_modes import RecordMode

__all__ = [
    "__version__",
    "AllMatcher",
    "AsyncRecordingChannel",
    "Cassette",
    "CassetteNotFoundError",
    "CassetteWriteError",
    "CustomMatcher",
    "GrpcvrError",
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

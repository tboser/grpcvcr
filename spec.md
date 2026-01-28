  grpcvr - Complete Implementation Sketch

  Project Overview

  Name: grpcvr (gRPC Video Recorder - like VCR for gRPC)
  Tagline: Record and replay gRPC interactions for testing

  Directory Structure

  grpcvr/
  ├── src/
  │   └── grpcvr/
  │       ├── __init__.py              # Public API exports
  │       ├── _version.py              # Version (git-based)
  │       ├── cassette.py              # Cassette storage and management
  │       ├── serialization.py         # Protobuf <-> JSON/binary serialization
  │       ├── matchers.py              # Request matching strategies
  │       ├── record_modes.py          # Recording mode enum
  │       ├── errors.py                # Custom exceptions
  │       ├── interceptors/
  │       │   ├── __init__.py
  │       │   ├── _base.py             # Shared interceptor logic
  │       │   ├── sync.py              # Sync grpc interceptors
  │       │   └── aio.py               # Async grpc.aio interceptors
  │       ├── channel.py               # Wrapped channel with recording
  │       ├── pytest_plugin.py         # pytest fixtures and markers
  │       └── py.typed                 # PEP 561 marker
  ├── tests/
  │   ├── conftest.py                  # Shared fixtures, test server
  │   ├── protos/                      # Test .proto files
  │   │   └── test_service.proto
  │   ├── generated/                   # Generated protobuf code
  │   │   ├── test_service_pb2.py
  │   │   └── test_service_pb2_grpc.py
  │   ├── cassettes/                   # Test cassette files
  │   ├── test_unary.py                # Unary RPC tests
  │   ├── test_streaming.py            # Streaming RPC tests
  │   ├── test_async.py                # Async client tests
  │   ├── test_matchers.py             # Matcher tests
  │   ├── test_serialization.py        # Serialization tests
  │   ├── test_record_modes.py         # Record mode behavior tests
  │   ├── test_errors.py               # Error handling tests
  │   └── test_examples.py             # Documentation example tests
  ├── docs/
  │   ├── index.md                     # Homepage
  │   ├── installation.md              # Installation guide
  │   ├── quickstart.md                # Getting started
  │   ├── concepts/
  │   │   ├── cassettes.md             # Cassette format and storage
  │   │   ├── matchers.md              # Request matching
  │   │   ├── record-modes.md          # Recording modes
  │   │   └── streaming.md             # Streaming RPC support
  │   ├── guides/
  │   │   ├── pytest.md                # pytest integration
  │   │   ├── async.md                 # Async usage
  │   │   ├── custom-matchers.md       # Custom matchers
  │   │   └── ci-testing.md            # CI/CD patterns
  │   ├── api/
  │   │   └── reference.md             # API reference (auto-generated)
  │   └── examples/
  │       ├── basic.md                 # Basic examples
  │       └── advanced.md              # Advanced patterns
  ├── examples/
  │   ├── basic_recording.py
  │   ├── pytest_usage.py
  │   └── streaming_example.py
  ├── .github/
  │   └── workflows/
  │       ├── ci.yml                   # Main CI workflow
  │       └── release.yml              # Release workflow
  ├── pyproject.toml                   # Build config, dependencies, tools
  ├── Makefile                         # Dev commands
  ├── mkdocs.yml                       # Documentation config
  ├── .pre-commit-config.yaml          # Pre-commit hooks
  ├── LICENSE                          # MIT License
  └── README.md                        # Project readme

  ---
  Core Implementation

  src/grpcvr/__init__.py

  """grpcvr - Record and replay gRPC interactions for testing."""

  from grpcvr._version import __version__
  from grpcvr.cassette import Cassette, use_cassette
  from grpcvr.channel import RecordingChannel, recorded_channel
  from grpcvr.record_modes import RecordMode
  from grpcvr.matchers import (
      Matcher,
      MethodMatcher,
      MetadataMatcher,
      RequestMatcher,
      AllMatcher,
  )
  from grpcvr.errors import (
      GrpcvrError,
      CassetteNotFoundError,
      NoMatchingInteractionError,
      RecordingDisabledError,
  )

  __all__ = [
      "__version__",
      # Core
      "Cassette",
      "use_cassette",
      "RecordingChannel",
      "recorded_channel",
      # Modes
      "RecordMode",
      # Matchers
      "Matcher",
      "MethodMatcher",
      "MetadataMatcher",
      "RequestMatcher",
      "AllMatcher",
      # Errors
      "GrpcvrError",
      "CassetteNotFoundError",
      "NoMatchingInteractionError",
      "RecordingDisabledError",
  ]

  src/grpcvr/record_modes.py

  """Recording mode definitions."""

  from enum import Enum


  class RecordMode(Enum):
      """Controls how the cassette handles recording and playback.

      Attributes:
          NONE: Playback only. Raises error if no matching interaction found.
              Use in CI to ensure all interactions are pre-recorded.
          NEW_EPISODES: Play back existing interactions, record new ones.
              Default mode - good for iterative test development.
          ALL: Always record, overwriting existing interactions.
              Use to refresh cassettes after API changes.
          ONCE: Record if cassette doesn't exist, then playback only.
              Good for one-time setup of test fixtures.
      """

      NONE = "none"
      NEW_EPISODES = "new_episodes"
      ALL = "all"
      ONCE = "once"

  src/grpcvr/errors.py

  """Custom exceptions for grpcvr."""

  from __future__ import annotations

  from typing import TYPE_CHECKING

  if TYPE_CHECKING:
      from grpcvr.cassette import Interaction


  class GrpcvrError(Exception):
      """Base exception for all grpcvr errors."""


  class CassetteNotFoundError(GrpcvrError):
      """Raised when a cassette file cannot be found in NONE or ONCE mode."""

      def __init__(self, path: str) -> None:
          self.path = path
          super().__init__(f"Cassette not found: {path}")


  class NoMatchingInteractionError(GrpcvrError):
      """Raised when no recorded interaction matches the request."""

      def __init__(
          self,
          method: str,
          request: bytes,
          available: list[Interaction],
      ) -> None:
          self.method = method
          self.request = request
          self.available = available

          available_methods = [i.method for i in available]
          super().__init__(
              f"No matching interaction for {method}. "
              f"Available: {available_methods}"
          )


  class RecordingDisabledError(GrpcvrError):
      """Raised when recording is attempted but disabled."""

      def __init__(self, method: str) -> None:
          self.method = method
          super().__init__(
              f"Recording disabled but no matching interaction for: {method}"
          )


  class CassetteWriteError(GrpcvrError):
      """Raised when cassette cannot be written to disk."""

      def __init__(self, path: str, cause: Exception) -> None:
          self.path = path
          self.cause = cause
          super().__init__(f"Failed to write cassette {path}: {cause}")


  class SerializationError(GrpcvrError):
      """Raised when request/response serialization fails."""

      def __init__(self, message: str, cause: Exception | None = None) -> None:
          self.cause = cause
          super().__init__(message)

  src/grpcvr/serialization.py

  """Serialization utilities for protobuf messages and cassettes."""

  from __future__ import annotations

  import base64
  import json
  from dataclasses import dataclass, field, asdict
  from pathlib import Path
  from typing import Any, Literal

  import yaml

  from grpcvr.errors import SerializationError


  @dataclass
  class InteractionRequest:
      """Recorded gRPC request."""

      method: str  # Full method path: /package.Service/Method
      body: str  # Base64-encoded protobuf bytes
      metadata: dict[str, list[str]] = field(default_factory=dict)

      @classmethod
      def from_grpc(
          cls,
          method: str,
          body: bytes,
          metadata: tuple[tuple[str, str], ...] | None = None,
      ) -> InteractionRequest:
          """Create from gRPC call details."""
          meta_dict: dict[str, list[str]] = {}
          if metadata:
              for key, value in metadata:
                  meta_dict.setdefault(key, []).append(value)

          return cls(
              method=method,
              body=base64.b64encode(body).decode("ascii"),
              metadata=meta_dict,
          )

      def get_body_bytes(self) -> bytes:
          """Decode body back to bytes."""
          return base64.b64decode(self.body)


  @dataclass
  class InteractionResponse:
      """Recorded gRPC response."""

      body: str  # Base64-encoded protobuf bytes (or list for streaming)
      code: str  # gRPC status code name (e.g., "OK", "NOT_FOUND")
      details: str | None = None  # Error details if any
      trailing_metadata: dict[str, list[str]] = field(default_factory=dict)

      @classmethod
      def from_grpc(
          cls,
          body: bytes,
          code: str,
          details: str | None = None,
          trailing_metadata: tuple[tuple[str, str], ...] | None = None,
      ) -> InteractionResponse:
          """Create from gRPC response."""
          meta_dict: dict[str, list[str]] = {}
          if trailing_metadata:
              for key, value in trailing_metadata:
                  meta_dict.setdefault(key, []).append(value)

          return cls(
              body=base64.b64encode(body).decode("ascii"),
              code=code,
              details=details,
              trailing_metadata=meta_dict,
          )

      def get_body_bytes(self) -> bytes:
          """Decode body back to bytes."""
          return base64.b64decode(self.body)


  @dataclass
  class StreamingInteractionResponse:
      """Recorded gRPC streaming response."""

      messages: list[str]  # List of base64-encoded protobuf messages
      code: str
      details: str | None = None
      trailing_metadata: dict[str, list[str]] = field(default_factory=dict)

      @classmethod
      def from_grpc(
          cls,
          messages: list[bytes],
          code: str,
          details: str | None = None,
          trailing_metadata: tuple[tuple[str, str], ...] | None = None,
      ) -> StreamingInteractionResponse:
          """Create from gRPC streaming response."""
          meta_dict: dict[str, list[str]] = {}
          if trailing_metadata:
              for key, value in trailing_metadata:
                  meta_dict.setdefault(key, []).append(value)

          return cls(
              messages=[base64.b64encode(m).decode("ascii") for m in messages],
              code=code,
              details=details,
              trailing_metadata=meta_dict,
          )

      def get_messages_bytes(self) -> list[bytes]:
          """Decode all messages back to bytes."""
          return [base64.b64decode(m) for m in self.messages]


  @dataclass
  class Interaction:
      """A single recorded gRPC interaction (request + response)."""

      request: InteractionRequest
      response: InteractionResponse | StreamingInteractionResponse
      rpc_type: Literal["unary", "server_streaming", "client_streaming", "bidi_streaming"]

      def to_dict(self) -> dict[str, Any]:
          """Convert to dictionary for serialization."""
          return {
              "request": asdict(self.request),
              "response": asdict(self.response),
              "rpc_type": self.rpc_type,
          }

      @classmethod
      def from_dict(cls, data: dict[str, Any]) -> Interaction:
          """Create from dictionary."""
          rpc_type = data["rpc_type"]
          request = InteractionRequest(**data["request"])

          if rpc_type in ("server_streaming", "bidi_streaming"):
              response = StreamingInteractionResponse(**data["response"])
          else:
              response = InteractionResponse(**data["response"])

          return cls(request=request, response=response, rpc_type=rpc_type)


  @dataclass
  class CassetteData:
      """Complete cassette file contents."""

      version: int = 1
      interactions: list[Interaction] = field(default_factory=list)

      def to_dict(self) -> dict[str, Any]:
          """Convert to dictionary for serialization."""
          return {
              "version": self.version,
              "interactions": [i.to_dict() for i in self.interactions],
          }

      @classmethod
      def from_dict(cls, data: dict[str, Any]) -> CassetteData:
          """Create from dictionary."""
          return cls(
              version=data.get("version", 1),
              interactions=[
                  Interaction.from_dict(i) for i in data.get("interactions", [])
              ],
          )


  class CassetteSerializer:
      """Handles cassette file serialization."""

      @staticmethod
      def load(path: Path) -> CassetteData:
          """Load cassette from file."""
          if not path.exists():
              raise FileNotFoundError(path)

          content = path.read_text(encoding="utf-8")

          try:
              if path.suffix == ".json":
                  data = json.loads(content)
              else:  # Default to YAML
                  data = yaml.safe_load(content)
          except Exception as e:
              raise SerializationError(f"Failed to parse {path}", e) from e

          return CassetteData.from_dict(data)

      @staticmethod
      def save(path: Path, data: CassetteData) -> None:
          """Save cassette to file."""
          path.parent.mkdir(parents=True, exist_ok=True)

          dict_data = data.to_dict()

          try:
              if path.suffix == ".json":
                  content = json.dumps(dict_data, indent=2)
              else:  # Default to YAML
                  content = yaml.dump(
                      dict_data,
                      default_flow_style=False,
                      allow_unicode=True,
                      sort_keys=False,
                  )
              path.write_text(content, encoding="utf-8")
          except Exception as e:
              raise SerializationError(f"Failed to write {path}", e) from e

  src/grpcvr/matchers.py

  """Request matching strategies for finding recorded interactions."""

  from __future__ import annotations

  from abc import ABC, abstractmethod
  from dataclasses import dataclass
  from typing import Callable

  from grpcvr.serialization import Interaction, InteractionRequest


  class Matcher(ABC):
      """Base class for request matchers."""

      @abstractmethod
      def matches(
          self,
          request: InteractionRequest,
          recorded: InteractionRequest,
      ) -> bool:
          """Return True if request matches the recorded interaction."""
          ...

      def __and__(self, other: Matcher) -> AllMatcher:
          """Combine matchers with AND logic."""
          if isinstance(self, AllMatcher):
              return AllMatcher([*self.matchers, other])
          return AllMatcher([self, other])


  @dataclass
  class MethodMatcher(Matcher):
      """Matches on gRPC method path.

      This is the default matcher. Method paths look like:
      /package.ServiceName/MethodName

      Example:
          >>> matcher = MethodMatcher()
          >>> matcher.matches(request, recorded)  # Compares .method
      """

      def matches(
          self,
          request: InteractionRequest,
          recorded: InteractionRequest,
      ) -> bool:
          return request.method == recorded.method


  @dataclass
  class MetadataMatcher(Matcher):
      """Matches on specific metadata keys.

      Args:
          keys: Metadata keys that must match. If None, matches all metadata.
          ignore_keys: Metadata keys to ignore (e.g., timestamps, request IDs).

      Example:
          >>> matcher = MetadataMatcher(keys=["authorization"])
          >>> # Only compares 'authorization' header

          >>> matcher = MetadataMatcher(ignore_keys=["x-request-id"])
          >>> # Compares all metadata except 'x-request-id'
      """

      keys: list[str] | None = None
      ignore_keys: list[str] | None = None

      def matches(
          self,
          request: InteractionRequest,
          recorded: InteractionRequest,
      ) -> bool:
          req_meta = request.metadata
          rec_meta = recorded.metadata

          if self.keys is not None:
              # Only check specified keys
              for key in self.keys:
                  if req_meta.get(key) != rec_meta.get(key):
                      return False
              return True

          # Check all keys except ignored ones
          ignore = set(self.ignore_keys or [])
          all_keys = set(req_meta.keys()) | set(rec_meta.keys())

          for key in all_keys:
              if key in ignore:
                  continue
              if req_meta.get(key) != rec_meta.get(key):
                  return False

          return True


  @dataclass
  class RequestMatcher(Matcher):
      """Matches on request body content.

      Compares the raw protobuf bytes. For semantic comparison,
      use a custom matcher that deserializes the protobuf.

      Example:
          >>> matcher = RequestMatcher()
          >>> # Compares raw request body bytes
      """

      def matches(
          self,
          request: InteractionRequest,
          recorded: InteractionRequest,
      ) -> bool:
          return request.body == recorded.body


  @dataclass
  class CustomMatcher(Matcher):
      """Custom matcher using a user-provided function.

      Args:
          func: Function that takes (request, recorded) and returns bool.
          name: Optional name for debugging.

      Example:
          >>> def match_user_id(req, rec):
          ...     # Custom logic to extract and compare user IDs
          ...     return extract_user_id(req) == extract_user_id(rec)
          >>> matcher = CustomMatcher(match_user_id)
      """

      func: Callable[[InteractionRequest, InteractionRequest], bool]
      name: str | None = None

      def matches(
          self,
          request: InteractionRequest,
          recorded: InteractionRequest,
      ) -> bool:
          return self.func(request, recorded)


  @dataclass
  class AllMatcher(Matcher):
      """Combines multiple matchers with AND logic.

      All matchers must return True for the request to match.

      Example:
          >>> matcher = MethodMatcher() & RequestMatcher()
          >>> # Must match both method AND request body
      """

      matchers: list[Matcher]

      def matches(
          self,
          request: InteractionRequest,
          recorded: InteractionRequest,
      ) -> bool:
          return all(m.matches(request, recorded) for m in self.matchers)


  # Default matcher - method only
  DEFAULT_MATCHER = MethodMatcher()


  def find_matching_interaction(
      request: InteractionRequest,
      interactions: list[Interaction],
      matcher: Matcher = DEFAULT_MATCHER,
  ) -> Interaction | None:
      """Find first interaction matching the request."""
      for interaction in interactions:
          if matcher.matches(request, interaction.request):
              return interaction
      return None

  src/grpcvr/cassette.py

  """Cassette management - loading, saving, and using cassettes."""

  from __future__ import annotations

  import threading
  from contextlib import contextmanager
  from dataclasses import dataclass, field
  from pathlib import Path
  from typing import Iterator, Generator

  from grpcvr.errors import (
      CassetteNotFoundError,
      NoMatchingInteractionError,
      RecordingDisabledError,
  )
  from grpcvr.matchers import Matcher, DEFAULT_MATCHER, find_matching_interaction
  from grpcvr.record_modes import RecordMode
  from grpcvr.serialization import (
      Interaction,
      InteractionRequest,
      InteractionResponse,
      StreamingInteractionResponse,
      CassetteData,
      CassetteSerializer,
  )


  @dataclass
  class Cassette:
      """A collection of recorded gRPC interactions.

      Cassettes store request/response pairs and can be saved to disk
      for later playback during tests.

      Args:
          path: Path to the cassette file (YAML or JSON).
          record_mode: How to handle recording vs playback.
          match_on: Matcher(s) to use for finding recorded interactions.

      Example:
          ```python
          with Cassette("tests/cassettes/my_test.yaml") as cassette:
              # Use cassette.channel or cassette.intercept()
              pass
          ```
      """

      path: Path
      record_mode: RecordMode = RecordMode.NEW_EPISODES
      match_on: Matcher = field(default_factory=lambda: DEFAULT_MATCHER)

      _data: CassetteData = field(default_factory=CassetteData, init=False)
      _dirty: bool = field(default=False, init=False)
      _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

      def __post_init__(self) -> None:
          if isinstance(self.path, str):
              self.path = Path(self.path)
          self._load()

      def _load(self) -> None:
          """Load cassette from disk if it exists."""
          if self.path.exists():
              self._data = CassetteSerializer.load(self.path)
          elif self.record_mode == RecordMode.NONE:
              raise CassetteNotFoundError(str(self.path))
          elif self.record_mode == RecordMode.ONCE:
              # ONCE mode allows creation if file doesn't exist
              self._data = CassetteData()

      def save(self) -> None:
          """Save cassette to disk if modified."""
          if self._dirty:
              CassetteSerializer.save(self.path, self._data)
              self._dirty = False

      @property
      def interactions(self) -> list[Interaction]:
          """All recorded interactions."""
          return self._data.interactions

      @property
      def can_record(self) -> bool:
          """Whether recording is allowed in current mode."""
          return self.record_mode in (RecordMode.ALL, RecordMode.NEW_EPISODES, RecordMode.ONCE)

      def find_interaction(self, request: InteractionRequest) -> Interaction | None:
          """Find a matching recorded interaction for the request."""
          return find_matching_interaction(request, self.interactions, self.match_on)

      def record_interaction(self, interaction: Interaction) -> None:
          """Record a new interaction to the cassette.

          If an interaction with the same request already exists (based on matcher),
          it will be replaced in ALL mode, or skipped in other modes.
          """
          with self._lock:
              if self.record_mode == RecordMode.ALL:
                  # Remove existing matching interaction
                  self._data.interactions = [
                      i for i in self._data.interactions
                      if not self.match_on.matches(interaction.request, i.request)
                  ]

              self._data.interactions.append(interaction)
              self._dirty = True

      def get_response(
          self,
          method: str,
          request_body: bytes,
          metadata: tuple[tuple[str, str], ...] | None = None,
      ) -> Interaction:
          """Get recorded response for a request.

          Args:
              method: Full gRPC method path.
              request_body: Serialized protobuf request.
              metadata: Request metadata (headers).

          Returns:
              The matching recorded interaction.

          Raises:
              NoMatchingInteractionError: If no matching interaction found.
              RecordingDisabledError: If recording disabled and no match.
          """
          request = InteractionRequest.from_grpc(method, request_body, metadata)
          interaction = self.find_interaction(request)

          if interaction is None:
              if not self.can_record:
                  raise RecordingDisabledError(method)
              raise NoMatchingInteractionError(method, request_body, self.interactions)

          return interaction

      def __enter__(self) -> Cassette:
          return self

      def __exit__(self, *args: object) -> None:
          self.save()


  @contextmanager
  def use_cassette(
      path: str | Path,
      record_mode: RecordMode = RecordMode.NEW_EPISODES,
      match_on: Matcher | None = None,
  ) -> Generator[Cassette, None, None]:
      """Context manager for using a cassette.

      This is the primary API for recording and playing back gRPC interactions.

      Args:
          path: Path to the cassette file.
          record_mode: How to handle recording vs playback.
          match_on: Matcher to use for finding recorded interactions.

      Example:
          ```python
          from grpcvr import use_cassette, RecordMode

          with use_cassette("tests/cassettes/test.yaml") as cassette:
              channel = cassette.wrap_channel(grpc.insecure_channel("localhost:50051"))
              stub = MyServiceStub(channel)
              response = stub.MyMethod(request)
          ```
      """
      cassette = Cassette(
          path=Path(path),
          record_mode=record_mode,
          match_on=match_on or DEFAULT_MATCHER,
      )
      try:
          yield cassette
      finally:
          cassette.save()

  src/grpcvr/interceptors/_base.py

  """Shared interceptor logic."""

  from __future__ import annotations

  from typing import TYPE_CHECKING

  import grpc

  from grpcvr.serialization import (
      Interaction,
      InteractionRequest,
      InteractionResponse,
      StreamingInteractionResponse,
  )

  if TYPE_CHECKING:
      from grpcvr.cassette import Cassette


  def create_unary_response(
      interaction: Interaction,
      response_deserializer: callable,
  ) -> grpc.Call:
      """Create a fake unary response from recorded interaction."""
      response = interaction.response
      assert isinstance(response, InteractionResponse)

      body_bytes = response.get_body_bytes()
      deserialized = response_deserializer(body_bytes)

      return _FakeUnaryCall(
          result=deserialized,
          code=grpc.StatusCode[response.code],
          details=response.details,
          trailing_metadata=_dict_to_metadata(response.trailing_metadata),
      )


  def create_streaming_response(
      interaction: Interaction,
      response_deserializer: callable,
  ) -> grpc.Call:
      """Create a fake streaming response from recorded interaction."""
      response = interaction.response
      assert isinstance(response, StreamingInteractionResponse)

      messages = [
          response_deserializer(m) for m in response.get_messages_bytes()
      ]

      return _FakeStreamingCall(
          messages=messages,
          code=grpc.StatusCode[response.code],
          details=response.details,
          trailing_metadata=_dict_to_metadata(response.trailing_metadata),
      )


  def _dict_to_metadata(d: dict[str, list[str]]) -> tuple[tuple[str, str], ...]:
      """Convert metadata dict back to tuple format."""
      result = []
      for key, values in d.items():
          for value in values:
              result.append((key, value))
      return tuple(result)


  def _metadata_to_dict(metadata: tuple[tuple[str, str], ...] | None) -> dict[str, list[str]]:
      """Convert metadata tuple to dict format."""
      result: dict[str, list[str]] = {}
      if metadata:
          for key, value in metadata:
              result.setdefault(key, []).append(value)
      return result


  class _FakeUnaryCall(grpc.Call, grpc.Future):
      """Fake call object for playback of unary responses."""

      def __init__(
          self,
          result: object,
          code: grpc.StatusCode,
          details: str | None,
          trailing_metadata: tuple[tuple[str, str], ...],
      ) -> None:
          self._result = result
          self._code = code
          self._details = details
          self._trailing_metadata = trailing_metadata

      def result(self, timeout: float | None = None) -> object:
          if self._code != grpc.StatusCode.OK:
              raise grpc.RpcError()
          return self._result

      def code(self) -> grpc.StatusCode:
          return self._code

      def details(self) -> str | None:
          return self._details

      def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
          return self._trailing_metadata

      def initial_metadata(self) -> tuple[tuple[str, str], ...]:
          return ()

      def cancelled(self) -> bool:
          return False

      def running(self) -> bool:
          return False

      def done(self) -> bool:
          return True

      def add_done_callback(self, fn: callable) -> None:
          fn(self)

      def exception(self, timeout: float | None = None) -> Exception | None:
          if self._code != grpc.StatusCode.OK:
              return grpc.RpcError()
          return None


  class _FakeStreamingCall(grpc.Call):
      """Fake call object for playback of streaming responses."""

      def __init__(
          self,
          messages: list[object],
          code: grpc.StatusCode,
          details: str | None,
          trailing_metadata: tuple[tuple[str, str], ...],
      ) -> None:
          self._messages = messages
          self._code = code
          self._details = details
          self._trailing_metadata = trailing_metadata
          self._index = 0

      def __iter__(self):
          return iter(self._messages)

      def __next__(self):
          if self._index >= len(self._messages):
              raise StopIteration
          msg = self._messages[self._index]
          self._index += 1
          return msg

      def code(self) -> grpc.StatusCode:
          return self._code

      def details(self) -> str | None:
          return self._details

      def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
          return self._trailing_metadata

      def initial_metadata(self) -> tuple[tuple[str, str], ...]:
          return ()

      def cancelled(self) -> bool:
          return False

  src/grpcvr/interceptors/sync.py

  """Synchronous gRPC interceptors for recording and playback."""

  from __future__ import annotations

  from typing import TYPE_CHECKING, Any, Callable

  import grpc

  from grpcvr.errors import NoMatchingInteractionError
  from grpcvr.serialization import (
      Interaction,
      InteractionRequest,
      InteractionResponse,
      StreamingInteractionResponse,
  )
  from grpcvr.interceptors._base import (
      create_unary_response,
      create_streaming_response,
      _metadata_to_dict,
  )

  if TYPE_CHECKING:
      from grpcvr.cassette import Cassette


  class RecordingUnaryUnaryInterceptor(grpc.UnaryUnaryClientInterceptor):
      """Intercepts unary-unary RPCs for recording/playback.

      This interceptor handles the simplest case: single request, single response.
      """

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      def intercept_unary_unary(
          self,
          continuation: Callable,
          client_call_details: grpc.ClientCallDetails,
          request: Any,
      ) -> grpc.Call:
          method = client_call_details.method
          request_bytes = request.SerializeToString()
          metadata = client_call_details.metadata

          # Create request object for matching
          req = InteractionRequest.from_grpc(method, request_bytes, metadata)

          # Try to find recorded interaction
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              # Playback mode - return recorded response
              return create_unary_response(
                  interaction,
                  type(request).FromString,  # Use same message type for response
              )

          if not self.cassette.can_record:
              from grpcvr.errors import RecordingDisabledError
              raise RecordingDisabledError(method)

          # Record mode - make real call
          response = continuation(client_call_details, request)

          # Wait for response and record it
          try:
              result = response.result()
              response_bytes = result.SerializeToString()
              code = "OK"
              details = None
          except grpc.RpcError as e:
              response_bytes = b""
              code = e.code().name
              details = e.details()

          # Get trailing metadata
          try:
              trailing = response.trailing_metadata()
          except Exception:
              trailing = None

          # Record the interaction
          recorded_interaction = Interaction(
              request=req,
              response=InteractionResponse.from_grpc(
                  body=response_bytes,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="unary",
          )
          self.cassette.record_interaction(recorded_interaction)

          return response


  class RecordingUnaryStreamInterceptor(grpc.UnaryStreamClientInterceptor):
      """Intercepts unary-stream (server streaming) RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      def intercept_unary_stream(
          self,
          continuation: Callable,
          client_call_details: grpc.ClientCallDetails,
          request: Any,
      ) -> grpc.Call:
          method = client_call_details.method
          request_bytes = request.SerializeToString()
          metadata = client_call_details.metadata

          req = InteractionRequest.from_grpc(method, request_bytes, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              return create_streaming_response(
                  interaction,
                  type(request).FromString,
              )

          if not self.cassette.can_record:
              from grpcvr.errors import RecordingDisabledError
              raise RecordingDisabledError(method)

          # Make real call and consume stream
          response = continuation(client_call_details, request)

          messages: list[bytes] = []
          code = "OK"
          details = None

          try:
              for msg in response:
                  messages.append(msg.SerializeToString())
          except grpc.RpcError as e:
              code = e.code().name
              details = e.details()

          try:
              trailing = response.trailing_metadata()
          except Exception:
              trailing = None

          recorded_interaction = Interaction(
              request=req,
              response=StreamingInteractionResponse.from_grpc(
                  messages=messages,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="server_streaming",
          )
          self.cassette.record_interaction(recorded_interaction)

          # Return a new iterator over recorded messages
          return create_streaming_response(
              recorded_interaction,
              type(request).FromString,
          )


  class RecordingStreamUnaryInterceptor(grpc.StreamUnaryClientInterceptor):
      """Intercepts stream-unary (client streaming) RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      def intercept_stream_unary(
          self,
          continuation: Callable,
          client_call_details: grpc.ClientCallDetails,
          request_iterator: Any,
      ) -> grpc.Call:
          method = client_call_details.method
          metadata = client_call_details.metadata

          # Consume request iterator to get all messages
          requests = list(request_iterator)

          # For client streaming, concatenate all request bodies
          # (Alternative: store as list, but this complicates matching)
          combined_request = b"".join(r.SerializeToString() for r in requests)

          req = InteractionRequest.from_grpc(method, combined_request, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              # Get the message type from first request for deserialization
              msg_type = type(requests[0]) if requests else None
              if msg_type:
                  return create_unary_response(interaction, msg_type.FromString)
              return create_unary_response(interaction, lambda x: x)

          if not self.cassette.can_record:
              from grpcvr.errors import RecordingDisabledError
              raise RecordingDisabledError(method)

          # Make real call with consumed requests
          response = continuation(client_call_details, iter(requests))

          try:
              result = response.result()
              response_bytes = result.SerializeToString()
              code = "OK"
              details = None
          except grpc.RpcError as e:
              response_bytes = b""
              code = e.code().name
              details = e.details()

          try:
              trailing = response.trailing_metadata()
          except Exception:
              trailing = None

          recorded_interaction = Interaction(
              request=req,
              response=InteractionResponse.from_grpc(
                  body=response_bytes,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="client_streaming",
          )
          self.cassette.record_interaction(recorded_interaction)

          return response


  class RecordingStreamStreamInterceptor(grpc.StreamStreamClientInterceptor):
      """Intercepts stream-stream (bidirectional streaming) RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      def intercept_stream_stream(
          self,
          continuation: Callable,
          client_call_details: grpc.ClientCallDetails,
          request_iterator: Any,
      ) -> grpc.Call:
          method = client_call_details.method
          metadata = client_call_details.metadata

          # Consume request iterator
          requests = list(request_iterator)
          combined_request = b"".join(r.SerializeToString() for r in requests)

          req = InteractionRequest.from_grpc(method, combined_request, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              msg_type = type(requests[0]) if requests else None
              deserializer = msg_type.FromString if msg_type else lambda x: x
              return create_streaming_response(interaction, deserializer)

          if not self.cassette.can_record:
              from grpcvr.errors import RecordingDisabledError
              raise RecordingDisabledError(method)

          # Make real call
          response = continuation(client_call_details, iter(requests))

          messages: list[bytes] = []
          code = "OK"
          details = None

          try:
              for msg in response:
                  messages.append(msg.SerializeToString())
          except grpc.RpcError as e:
              code = e.code().name
              details = e.details()

          try:
              trailing = response.trailing_metadata()
          except Exception:
              trailing = None

          recorded_interaction = Interaction(
              request=req,
              response=StreamingInteractionResponse.from_grpc(
                  messages=messages,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="bidi_streaming",
          )
          self.cassette.record_interaction(recorded_interaction)

          msg_type = type(requests[0]) if requests else None
          deserializer = msg_type.FromString if msg_type else lambda x: x
          return create_streaming_response(recorded_interaction, deserializer)


  def create_interceptors(cassette: Cassette) -> list[grpc.ClientInterceptor]:
      """Create all interceptors for a cassette."""
      return [
          RecordingUnaryUnaryInterceptor(cassette),
          RecordingUnaryStreamInterceptor(cassette),
          RecordingStreamUnaryInterceptor(cassette),
          RecordingStreamStreamInterceptor(cassette),
      ]

  src/grpcvr/interceptors/aio.py

  """Async gRPC interceptors for recording and playback."""

  from __future__ import annotations

  from typing import TYPE_CHECKING, Any, Callable, AsyncIterator

  import grpc
  from grpc import aio

  from grpcvr.errors import NoMatchingInteractionError, RecordingDisabledError
  from grpcvr.serialization import (
      Interaction,
      InteractionRequest,
      InteractionResponse,
      StreamingInteractionResponse,
  )

  if TYPE_CHECKING:
      from grpcvr.cassette import Cassette


  class _AsyncFakeUnaryCall(aio.Call):
      """Async fake call for unary response playback."""

      def __init__(
          self,
          result: Any,
          code: grpc.StatusCode,
          details: str | None,
          trailing_metadata: tuple[tuple[str, str], ...],
      ) -> None:
          self._result = result
          self._code = code
          self._details = details
          self._trailing_metadata = trailing_metadata

      def __await__(self):
          async def _get_result():
              if self._code != grpc.StatusCode.OK:
                  raise aio.AioRpcError(
                      self._code,
                      (),
                      self._trailing_metadata,
                      self._details,
                  )
              return self._result
          return _get_result().__await__()

      async def code(self) -> grpc.StatusCode:
          return self._code

      async def details(self) -> str | None:
          return self._details

      async def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
          return self._trailing_metadata

      async def initial_metadata(self) -> tuple[tuple[str, str], ...]:
          return ()

      def cancelled(self) -> bool:
          return False

      def done(self) -> bool:
          return True

      def add_done_callback(self, callback: Callable) -> None:
          callback(self)

      def cancel(self) -> bool:
          return False


  class _AsyncFakeStreamingCall(aio.Call):
      """Async fake call for streaming response playback."""

      def __init__(
          self,
          messages: list[Any],
          code: grpc.StatusCode,
          details: str | None,
          trailing_metadata: tuple[tuple[str, str], ...],
      ) -> None:
          self._messages = messages
          self._code = code
          self._details = details
          self._trailing_metadata = trailing_metadata

      def __aiter__(self):
          return self._iterate()

      async def _iterate(self) -> AsyncIterator[Any]:
          for msg in self._messages:
              yield msg
          if self._code != grpc.StatusCode.OK:
              raise aio.AioRpcError(
                  self._code,
                  (),
                  self._trailing_metadata,
                  self._details,
              )

      async def code(self) -> grpc.StatusCode:
          return self._code

      async def details(self) -> str | None:
          return self._details

      async def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
          return self._trailing_metadata

      async def initial_metadata(self) -> tuple[tuple[str, str], ...]:
          return ()

      def cancelled(self) -> bool:
          return False

      def done(self) -> bool:
          return True

      def add_done_callback(self, callback: Callable) -> None:
          callback(self)

      def cancel(self) -> bool:
          return False


  class AsyncRecordingUnaryUnaryInterceptor(aio.UnaryUnaryClientInterceptor):
      """Async interceptor for unary-unary RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      async def intercept_unary_unary(
          self,
          continuation: Callable,
          client_call_details: aio.ClientCallDetails,
          request: Any,
      ) -> aio.Call:
          method = client_call_details.method
          request_bytes = request.SerializeToString()
          metadata = client_call_details.metadata

          req = InteractionRequest.from_grpc(method, request_bytes, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              response = interaction.response
              assert isinstance(response, InteractionResponse)
              result = type(request).FromString(response.get_body_bytes())

              return _AsyncFakeUnaryCall(
                  result=result,
                  code=grpc.StatusCode[response.code],
                  details=response.details,
                  trailing_metadata=tuple(
                      (k, v) for k, vs in response.trailing_metadata.items() for v in vs
                  ),
              )

          if not self.cassette.can_record:
              raise RecordingDisabledError(method)

          # Make real call
          call = await continuation(client_call_details, request)

          try:
              result = await call
              response_bytes = result.SerializeToString()
              code = "OK"
              details = None
          except aio.AioRpcError as e:
              response_bytes = b""
              code = e.code().name
              details = e.details()

          try:
              trailing = await call.trailing_metadata()
          except Exception:
              trailing = ()

          recorded = Interaction(
              request=req,
              response=InteractionResponse.from_grpc(
                  body=response_bytes,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="unary",
          )
          self.cassette.record_interaction(recorded)

          return call


  class AsyncRecordingUnaryStreamInterceptor(aio.UnaryStreamClientInterceptor):
      """Async interceptor for server-streaming RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      async def intercept_unary_stream(
          self,
          continuation: Callable,
          client_call_details: aio.ClientCallDetails,
          request: Any,
      ) -> aio.Call:
          method = client_call_details.method
          request_bytes = request.SerializeToString()
          metadata = client_call_details.metadata

          req = InteractionRequest.from_grpc(method, request_bytes, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              response = interaction.response
              assert isinstance(response, StreamingInteractionResponse)
              messages = [
                  type(request).FromString(m) for m in response.get_messages_bytes()
              ]

              return _AsyncFakeStreamingCall(
                  messages=messages,
                  code=grpc.StatusCode[response.code],
                  details=response.details,
                  trailing_metadata=tuple(
                      (k, v) for k, vs in response.trailing_metadata.items() for v in vs
                  ),
              )

          if not self.cassette.can_record:
              raise RecordingDisabledError(method)

          # Make real call and consume stream
          call = await continuation(client_call_details, request)

          messages: list[bytes] = []
          code = "OK"
          details = None

          try:
              async for msg in call:
                  messages.append(msg.SerializeToString())
          except aio.AioRpcError as e:
              code = e.code().name
              details = e.details()

          try:
              trailing = await call.trailing_metadata()
          except Exception:
              trailing = ()

          recorded = Interaction(
              request=req,
              response=StreamingInteractionResponse.from_grpc(
                  messages=messages,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="server_streaming",
          )
          self.cassette.record_interaction(recorded)

          # Return iterator over recorded messages
          response = recorded.response
          assert isinstance(response, StreamingInteractionResponse)
          return _AsyncFakeStreamingCall(
              messages=[type(request).FromString(m) for m in response.get_messages_bytes()],
              code=grpc.StatusCode[response.code],
              details=response.details,
              trailing_metadata=trailing,
          )


  class AsyncRecordingStreamUnaryInterceptor(aio.StreamUnaryClientInterceptor):
      """Async interceptor for client-streaming RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      async def intercept_stream_unary(
          self,
          continuation: Callable,
          client_call_details: aio.ClientCallDetails,
          request_iterator: Any,
      ) -> aio.Call:
          method = client_call_details.method
          metadata = client_call_details.metadata

          # Consume async iterator
          requests = [r async for r in request_iterator]
          combined_request = b"".join(r.SerializeToString() for r in requests)

          req = InteractionRequest.from_grpc(method, combined_request, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              response = interaction.response
              assert isinstance(response, InteractionResponse)
              msg_type = type(requests[0]) if requests else None

              if msg_type:
                  result = msg_type.FromString(response.get_body_bytes())
              else:
                  result = response.get_body_bytes()

              return _AsyncFakeUnaryCall(
                  result=result,
                  code=grpc.StatusCode[response.code],
                  details=response.details,
                  trailing_metadata=tuple(
                      (k, v) for k, vs in response.trailing_metadata.items() for v in vs
                  ),
              )

          if not self.cassette.can_record:
              raise RecordingDisabledError(method)

          # Make real call
          async def replay_requests():
              for r in requests:
                  yield r

          call = await continuation(client_call_details, replay_requests())

          try:
              result = await call
              response_bytes = result.SerializeToString()
              code = "OK"
              details = None
          except aio.AioRpcError as e:
              response_bytes = b""
              code = e.code().name
              details = e.details()

          try:
              trailing = await call.trailing_metadata()
          except Exception:
              trailing = ()

          recorded = Interaction(
              request=req,
              response=InteractionResponse.from_grpc(
                  body=response_bytes,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="client_streaming",
          )
          self.cassette.record_interaction(recorded)

          return call


  class AsyncRecordingStreamStreamInterceptor(aio.StreamStreamClientInterceptor):
      """Async interceptor for bidirectional streaming RPCs."""

      def __init__(self, cassette: Cassette) -> None:
          self.cassette = cassette

      async def intercept_stream_stream(
          self,
          continuation: Callable,
          client_call_details: aio.ClientCallDetails,
          request_iterator: Any,
      ) -> aio.Call:
          method = client_call_details.method
          metadata = client_call_details.metadata

          requests = [r async for r in request_iterator]
          combined_request = b"".join(r.SerializeToString() for r in requests)

          req = InteractionRequest.from_grpc(method, combined_request, metadata)
          interaction = self.cassette.find_interaction(req)

          if interaction is not None:
              response = interaction.response
              assert isinstance(response, StreamingInteractionResponse)
              msg_type = type(requests[0]) if requests else None

              if msg_type:
                  messages = [msg_type.FromString(m) for m in response.get_messages_bytes()]
              else:
                  messages = response.get_messages_bytes()

              return _AsyncFakeStreamingCall(
                  messages=messages,
                  code=grpc.StatusCode[response.code],
                  details=response.details,
                  trailing_metadata=tuple(
                      (k, v) for k, vs in response.trailing_metadata.items() for v in vs
                  ),
              )

          if not self.cassette.can_record:
              raise RecordingDisabledError(method)

          async def replay_requests():
              for r in requests:
                  yield r

          call = await continuation(client_call_details, replay_requests())

          messages: list[bytes] = []
          code = "OK"
          details = None

          try:
              async for msg in call:
                  messages.append(msg.SerializeToString())
          except aio.AioRpcError as e:
              code = e.code().name
              details = e.details()

          try:
              trailing = await call.trailing_metadata()
          except Exception:
              trailing = ()

          recorded = Interaction(
              request=req,
              response=StreamingInteractionResponse.from_grpc(
                  messages=messages,
                  code=code,
                  details=details,
                  trailing_metadata=trailing,
              ),
              rpc_type="bidi_streaming",
          )
          self.cassette.record_interaction(recorded)

          response = recorded.response
          assert isinstance(response, StreamingInteractionResponse)
          msg_type = type(requests[0]) if requests else None

          if msg_type:
              replay_messages = [msg_type.FromString(m) for m in response.get_messages_bytes()]
          else:
              replay_messages = response.get_messages_bytes()

          return _AsyncFakeStreamingCall(
              messages=replay_messages,
              code=grpc.StatusCode[response.code],
              details=response.details,
              trailing_metadata=trailing,
          )


  def create_async_interceptors(cassette: Cassette) -> list[aio.ClientInterceptor]:
      """Create all async interceptors for a cassette."""
      return [
          AsyncRecordingUnaryUnaryInterceptor(cassette),
          AsyncRecordingUnaryStreamInterceptor(cassette),
          AsyncRecordingStreamUnaryInterceptor(cassette),
          AsyncRecordingStreamStreamInterceptor(cassette),
      ]

  src/grpcvr/channel.py

  """Channel wrappers for easy integration."""

  from __future__ import annotations

  from contextlib import contextmanager
  from pathlib import Path
  from typing import Generator, overload

  import grpc
  from grpc import aio

  from grpcvr.cassette import Cassette
  from grpcvr.matchers import Matcher, DEFAULT_MATCHER
  from grpcvr.record_modes import RecordMode
  from grpcvr.interceptors.sync import create_interceptors
  from grpcvr.interceptors.aio import create_async_interceptors


  class RecordingChannel:
      """A gRPC channel wrapper that records/plays back interactions.

      This provides a cleaner API than manually creating interceptors.

      Example:
          ```python
          cassette = Cassette("test.yaml")
          channel = RecordingChannel(cassette, "localhost:50051")
          stub = MyServiceStub(channel.channel)
          response = stub.MyMethod(request)
          ```
      """

      def __init__(
          self,
          cassette: Cassette,
          target: str,
          *,
          credentials: grpc.ChannelCredentials | None = None,
          options: list[tuple[str, str]] | None = None,
      ) -> None:
          self.cassette = cassette
          self.target = target

          interceptors = create_interceptors(cassette)

          if credentials:
              base_channel = grpc.secure_channel(
                  target, credentials, options=options or []
              )
          else:
              base_channel = grpc.insecure_channel(target, options=options or [])

          self.channel = grpc.intercept_channel(base_channel, *interceptors)

      def close(self) -> None:
          """Close the channel and save the cassette."""
          self.channel.close()
          self.cassette.save()

      def __enter__(self) -> RecordingChannel:
          return self

      def __exit__(self, *args: object) -> None:
          self.close()


  class AsyncRecordingChannel:
      """Async version of RecordingChannel for grpc.aio.

      Example:
          ```python
          cassette = Cassette("test.yaml")
          channel = AsyncRecordingChannel(cassette, "localhost:50051")
          stub = MyServiceStub(channel.channel)
          response = await stub.MyMethod(request)
          ```
      """

      def __init__(
          self,
          cassette: Cassette,
          target: str,
          *,
          credentials: grpc.ChannelCredentials | None = None,
          options: list[tuple[str, str]] | None = None,
      ) -> None:
          self.cassette = cassette
          self.target = target

          interceptors = create_async_interceptors(cassette)

          if credentials:
              self.channel = aio.secure_channel(
                  target, credentials, options=options or [], interceptors=interceptors
              )
          else:
              self.channel = aio.insecure_channel(
                  target, options=options or [], interceptors=interceptors
              )

      async def close(self) -> None:
          """Close the channel and save the cassette."""
          await self.channel.close()
          self.cassette.save()

      async def __aenter__(self) -> AsyncRecordingChannel:
          return self

      async def __aexit__(self, *args: object) -> None:
          await self.close()


  @contextmanager
  def recorded_channel(
      path: str | Path,
      target: str,
      *,
      record_mode: RecordMode = RecordMode.NEW_EPISODES,
      match_on: Matcher | None = None,
      credentials: grpc.ChannelCredentials | None = None,
      options: list[tuple[str, str]] | None = None,
  ) -> Generator[grpc.Channel, None, None]:
      """Context manager for a recorded gRPC channel.

      This is the simplest API for recording/playing back gRPC calls.

      Args:
          path: Path to cassette file.
          target: gRPC server address.
          record_mode: How to handle recording.
          match_on: Request matcher.
          credentials: Optional channel credentials.
          options: Optional channel options.

      Example:
          ```python
          from grpcvr import recorded_channel

          with recorded_channel("test.yaml", "localhost:50051") as channel:
              stub = MyServiceStub(channel)
              response = stub.GetUser(GetUserRequest(id=1))
          ```
      """
      cassette = Cassette(
          path=Path(path),
          record_mode=record_mode,
          match_on=match_on or DEFAULT_MATCHER,
      )

      recording = RecordingChannel(
          cassette, target, credentials=credentials, options=options
      )

      try:
          yield recording.channel
      finally:
          recording.close()


  @contextmanager
  def async_recorded_channel(
      path: str | Path,
      target: str,
      *,
      record_mode: RecordMode = RecordMode.NEW_EPISODES,
      match_on: Matcher | None = None,
      credentials: grpc.ChannelCredentials | None = None,
      options: list[tuple[str, str]] | None = None,
  ) -> Generator[aio.Channel, None, None]:
      """Context manager for an async recorded gRPC channel.

      Note: Use `async with` for proper async cleanup.

      Example:
          ```python
          from grpcvr import async_recorded_channel

          async with async_recorded_channel("test.yaml", "localhost:50051") as channel:
              stub = MyServiceStub(channel)
              response = await stub.GetUser(GetUserRequest(id=1))
          ```
      """
      cassette = Cassette(
          path=Path(path),
          record_mode=record_mode,
          match_on=match_on or DEFAULT_MATCHER,
      )

      recording = AsyncRecordingChannel(
          cassette, target, credentials=credentials, options=options
      )

      # Note: This is a sync context manager that returns an async channel
      # For true async, users should use AsyncRecordingChannel directly
      try:
          yield recording.channel
      finally:
          # Can't await here in sync context - cassette.save() is sync
          cassette.save()

  src/grpcvr/pytest_plugin.py

  """pytest plugin for grpcvr integration."""

  from __future__ import annotations

  import os
  from pathlib import Path
  from typing import TYPE_CHECKING, Generator

  import pytest

  from grpcvr.cassette import Cassette
  from grpcvr.channel import RecordingChannel, AsyncRecordingChannel
  from grpcvr.matchers import DEFAULT_MATCHER, Matcher
  from grpcvr.record_modes import RecordMode

  if TYPE_CHECKING:
      from _pytest.config import Config
      from _pytest.fixtures import FixtureRequest


  def pytest_addoption(parser: pytest.Parser) -> None:
      """Add grpcvr command line options."""
      group = parser.getgroup("grpcvr")
      group.addoption(
          "--grpcvr-record",
          action="store",
          default=None,
          choices=["none", "new_episodes", "all", "once"],
          help="Override record mode for all cassettes",
      )
      group.addoption(
          "--grpcvr-cassette-dir",
          action="store",
          default="tests/cassettes",
          help="Default directory for cassette files",
      )


  def pytest_configure(config: Config) -> None:
      """Register grpcvr markers."""
      config.addinivalue_line(
          "markers",
          "grpcvr(cassette, record_mode, match_on): "
          "Mark test to use a specific cassette configuration",
      )


  @pytest.fixture
  def grpcvr_cassette_dir(request: FixtureRequest) -> Path:
      """Get the cassette directory for the current test."""
      return Path(request.config.getoption("--grpcvr-cassette-dir"))


  @pytest.fixture
  def grpcvr_record_mode(request: FixtureRequest) -> RecordMode:
      """Get the record mode, considering CLI override."""
      cli_mode = request.config.getoption("--grpcvr-record")
      if cli_mode:
          return RecordMode(cli_mode)

      # Check for marker
      marker = request.node.get_closest_marker("grpcvr")
      if marker and "record_mode" in marker.kwargs:
          mode = marker.kwargs["record_mode"]
          if isinstance(mode, str):
              return RecordMode(mode)
          return mode

      # Default based on CI environment
      if os.environ.get("CI"):
          return RecordMode.NONE
      return RecordMode.NEW_EPISODES


  @pytest.fixture
  def grpcvr_cassette_path(
      request: FixtureRequest,
      grpcvr_cassette_dir: Path,
  ) -> Path:
      """Generate cassette path based on test name."""
      # Check for marker with explicit cassette name
      marker = request.node.get_closest_marker("grpcvr")
      if marker and marker.args:
          cassette_name = marker.args[0]
      else:
          # Generate from test name
          cassette_name = f"{request.node.name}.yaml"

      # Handle nested test classes
      if request.node.cls:
          cassette_name = f"{request.node.cls.__name__}/{cassette_name}"

      return grpcvr_cassette_dir / cassette_name


  @pytest.fixture
  def cassette(
      grpcvr_cassette_path: Path,
      grpcvr_record_mode: RecordMode,
      request: FixtureRequest,
  ) -> Generator[Cassette, None, None]:
      """Fixture providing a cassette for the test.

      Example:
          ```python
          def test_my_grpc_call(cassette):
              channel = RecordingChannel(cassette, "localhost:50051")
              # ...
          ```
      """
      # Get matcher from marker if specified
      marker = request.node.get_closest_marker("grpcvr")
      match_on = DEFAULT_MATCHER
      if marker and "match_on" in marker.kwargs:
          match_on = marker.kwargs["match_on"]

      cassette = Cassette(
          path=grpcvr_cassette_path,
          record_mode=grpcvr_record_mode,
          match_on=match_on,
      )

      yield cassette

      cassette.save()


  @pytest.fixture
  def grpc_channel(
      cassette: Cassette,
      request: FixtureRequest,
  ) -> Generator[RecordingChannel, None, None]:
      """Fixture providing a recording gRPC channel.

      Requires the test to define a `grpc_target` fixture or marker.

      Example:
          ```python
          @pytest.fixture
          def grpc_target():
              return "localhost:50051"

          def test_my_call(grpc_channel):
              stub = MyServiceStub(grpc_channel.channel)
              # ...
          ```
      """
      # Get target from marker or fixture
      marker = request.node.get_closest_marker("grpcvr")
      target = None
      if marker and "target" in marker.kwargs:
          target = marker.kwargs["target"]

      if target is None:
          # Try to get from fixture
          if "grpc_target" in request.fixturenames:
              target = request.getfixturevalue("grpc_target")
          else:
              raise ValueError(
                  "grpc_channel requires 'target' in @pytest.mark.grpcvr or a grpc_target fixture"
              )

      channel = RecordingChannel(cassette, target)
      yield channel
      channel.close()

  ---
  Build Configuration

  pyproject.toml

  [build-system]
  requires = ["hatchling", "hatch-vcs"]
  build-backend = "hatchling.build"

  [project]
  name = "grpcvr"
  description = "Record and replay gRPC interactions for testing"
  readme = "README.md"
  license = "MIT"
  requires-python = ">=3.10"
  authors = [{ name = "Your Name", email = "you@example.com" }]
  classifiers = [
      "Development Status :: 4 - Beta",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Programming Language :: Python :: 3.13",
      "Topic :: Software Development :: Testing",
      "Framework :: Pytest",
      "Typing :: Typed",
  ]
  keywords = ["grpc", "testing", "vcr", "recording", "mocking"]
  dynamic = ["version"]

  dependencies = [
      "grpcio>=1.50.0",
      "pyyaml>=6.0",
  ]

  [project.optional-dependencies]
  # For async support
  aio = ["grpcio>=1.50.0"]  # aio is included in grpcio

  [project.entry-points.pytest11]
  grpcvr = "grpcvr.pytest_plugin"

  [project.urls]
  Homepage = "https://github.com/yourname/grpcvr"
  Documentation = "https://grpcvr.readthedocs.io"
  Repository = "https://github.com/yourname/grpcvr"
  Changelog = "https://github.com/yourname/grpcvr/blob/main/CHANGELOG.md"

  [tool.hatch.version]
  source = "vcs"

  [tool.hatch.build.targets.sdist]
  exclude = [
      "/.github",
      "/docs",
      "/tests",
      "/examples",
  ]

  [tool.hatch.build.targets.wheel]
  packages = ["src/grpcvr"]

  # ============== Dependency Groups ==============

  [dependency-groups]
  dev = [
      "pytest>=8.0",
      "pytest-asyncio>=0.23",
      "pytest-cov>=4.0",
      "pytest-examples>=0.0.13",
      "pytest-xdist>=3.5",
      "grpcio-tools>=1.50.0",
      "coverage[toml]>=7.0",
      "dirty-equals>=0.7",
  ]
  lint = [
      "ruff>=0.4",
      "pyright>=1.1.350",
      "mypy>=1.8",
      "mypy-protobuf>=3.5",
  ]
  docs = [
      "mkdocs>=1.5",
      "mkdocs-material>=9.5",
      "mkdocstrings[python]>=0.24",
      "mkdocs-gen-files>=0.5",
      "mkdocs-literate-nav>=0.6",
  ]

  # ============== Tool Configuration ==============

  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  filterwarnings = [
      "error",
      "ignore::DeprecationWarning:grpc.*",
  ]
  markers = [
      "grpcvr: configure grpcvr cassette for test",
  ]

  [tool.coverage.run]
  source = ["src/grpcvr"]
  branch = true
  parallel = true

  [tool.coverage.report]
  fail_under = 95
  exclude_lines = [
      "pragma: no cover",
      "if TYPE_CHECKING:",
      "@overload",
      "@abstractmethod",
      "raise NotImplementedError",
      "\\.\\.\\.",
  ]

  [tool.ruff]
  line-length = 100
  target-version = "py310"
  src = ["src", "tests"]

  [tool.ruff.lint]
  select = [
      "E",      # pycodestyle errors
      "W",      # pycodestyle warnings
      "F",      # pyflakes
      "I",      # isort
      "B",      # flake8-bugbear
      "C4",     # flake8-comprehensions
      "UP",     # pyupgrade
      "ARG",    # flake8-unused-arguments
      "SIM",    # flake8-simplify
      "TCH",    # flake8-type-checking
      "PTH",    # flake8-use-pathlib
      "RUF",    # ruff-specific rules
  ]
  ignore = [
      "E501",   # line too long (handled by formatter)
  ]

  [tool.ruff.lint.isort]
  known-first-party = ["grpcvr"]

  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"

  [tool.pyright]
  pythonVersion = "3.10"
  typeCheckingMode = "strict"
  include = ["src"]
  exclude = ["tests"]
  reportMissingTypeStubs = false
  reportPrivateUsage = false

  [tool.mypy]
  python_version = "3.10"
  strict = true
  warn_return_any = true
  warn_unused_configs = true
  plugins = ["mypy_protobuf.main"]

  [[tool.mypy.overrides]]
  module = "grpc.*"
  ignore_missing_imports = true

  Makefile

  .PHONY: install format lint typecheck test testcov docs docs-serve clean proto all

  # Default Python version
  PYTHON ?= python3.12

  install:
        uv sync --all-groups

  format:
        uv run ruff format src tests
        uv run ruff check --fix src tests

  lint:
        uv run ruff format --check src tests
        uv run ruff check src tests

  typecheck:
        uv run pyright

  typecheck-all: typecheck
        uv run mypy src

  test:
        uv run pytest -x -v

  testcov:
        uv run pytest --cov --cov-report=term-missing --cov-report=html

  test-parallel:
        uv run pytest -n auto --dist=loadgroup

  # Generate protobuf files for tests
  proto:
        uv run python -m grpc_tools.protoc \
                -I tests/protos \
                --python_out=tests/generated \
                --grpc_python_out=tests/generated \
                --mypy_out=tests/generated \
                tests/protos/*.proto

  docs:
        uv run mkdocs build

  docs-serve:
        uv run mkdocs serve

  clean:
        rm -rf build dist .eggs *.egg-info
        rm -rf .coverage htmlcov .pytest_cache
        rm -rf .mypy_cache .pyright .ruff_cache
        find . -type d -name __pycache__ -exec rm -rf {} +

  # Run all checks
  all: format lint typecheck testcov

  ---
  Test Suite

  tests/protos/test_service.proto

  syntax = "proto3";

  package test;

  service TestService {
    // Unary RPC
    rpc GetUser(GetUserRequest) returns (User);

    // Server streaming
    rpc ListUsers(ListUsersRequest) returns (stream User);

    // Client streaming
    rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);

    // Bidirectional streaming
    rpc Chat(stream ChatMessage) returns (stream ChatMessage);

    // Error cases
    rpc FailingMethod(Empty) returns (Empty);
  }

  message Empty {}

  message GetUserRequest {
    int32 id = 1;
  }

  message User {
    int32 id = 1;
    string name = 2;
    string email = 3;
  }

  message ListUsersRequest {
    int32 limit = 1;
  }

  message CreateUserRequest {
    string name = 1;
    string email = 2;
  }

  message CreateUsersResponse {
    int32 created_count = 1;
    repeated int32 ids = 2;
  }

  message ChatMessage {
    string sender = 1;
    string content = 2;
    int64 timestamp = 3;
  }

  tests/conftest.py

  """Shared test fixtures and configuration."""

  from __future__ import annotations

  import asyncio
  import threading
  from concurrent import futures
  from pathlib import Path
  from typing import Generator, AsyncGenerator

  import grpc
  from grpc import aio
  import pytest

  # Import generated protobuf code
  from tests.generated import test_service_pb2 as pb2
  from tests.generated import test_service_pb2_grpc as pb2_grpc


  # ============== Test Server Implementation ==============

  class TestServiceServicer(pb2_grpc.TestServiceServicer):
      """Test gRPC service implementation."""

      def __init__(self) -> None:
          self.users = {
              1: pb2.User(id=1, name="Alice", email="alice@example.com"),
              2: pb2.User(id=2, name="Bob", email="bob@example.com"),
              3: pb2.User(id=3, name="Charlie", email="charlie@example.com"),
          }
          self.next_id = 4

      def GetUser(
          self, request: pb2.GetUserRequest, context: grpc.ServicerContext
      ) -> pb2.User:
          if request.id not in self.users:
              context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.id} not found")
          return self.users[request.id]

      def ListUsers(
          self, request: pb2.ListUsersRequest, context: grpc.ServicerContext
      ) -> Generator[pb2.User, None, None]:
          limit = request.limit or len(self.users)
          for i, user in enumerate(self.users.values()):
              if i >= limit:
                  break
              yield user

      def CreateUsers(
          self, request_iterator, context: grpc.ServicerContext
      ) -> pb2.CreateUsersResponse:
          ids = []
          for request in request_iterator:
              user_id = self.next_id
              self.next_id += 1
              self.users[user_id] = pb2.User(
                  id=user_id, name=request.name, email=request.email
              )
              ids.append(user_id)
          return pb2.CreateUsersResponse(created_count=len(ids), ids=ids)

      def Chat(
          self, request_iterator, context: grpc.ServicerContext
      ) -> Generator[pb2.ChatMessage, None, None]:
          for message in request_iterator:
              # Echo back with "Bot: " prefix
              yield pb2.ChatMessage(
                  sender="Bot",
                  content=f"Echo: {message.content}",
                  timestamp=message.timestamp,
              )

      def FailingMethod(
          self, request: pb2.Empty, context: grpc.ServicerContext
      ) -> pb2.Empty:
          context.abort(grpc.StatusCode.INTERNAL, "Intentional failure")


  # ============== Fixtures ==============

  @pytest.fixture(scope="session")
  def grpc_server() -> Generator[str, None, None]:
      """Start a test gRPC server and return its address."""
      server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
      pb2_grpc.add_TestServiceServicer_to_server(TestServiceServicer(), server)

      port = server.add_insecure_port("[::]:0")  # Random available port
      server.start()

      address = f"localhost:{port}"
      yield address

      server.stop(grace=1)


  @pytest.fixture
  def grpc_target(grpc_server: str) -> str:
      """Alias for grpc_server for compatibility with grpcvr fixtures."""
      return grpc_server


  @pytest.fixture
  def cassette_dir(tmp_path: Path) -> Path:
      """Temporary cassette directory for tests."""
      cassette_path = tmp_path / "cassettes"
      cassette_path.mkdir()
      return cassette_path


  @pytest.fixture
  def cassette_path(cassette_dir: Path, request: pytest.FixtureRequest) -> Path:
      """Generate a unique cassette path for each test."""
      return cassette_dir / f"{request.node.name}.yaml"


  # ============== Async Server Fixtures ==============

  @pytest.fixture(scope="session")
  def event_loop():
      """Create event loop for async tests."""
      loop = asyncio.new_event_loop()
      yield loop
      loop.close()


  class AsyncTestServiceServicer(pb2_grpc.TestServiceServicer):
      """Async version of test service."""

      def __init__(self) -> None:
          self.users = {
              1: pb2.User(id=1, name="Alice", email="alice@example.com"),
              2: pb2.User(id=2, name="Bob", email="bob@example.com"),
          }

      async def GetUser(
          self, request: pb2.GetUserRequest, context: aio.ServicerContext
      ) -> pb2.User:
          if request.id not in self.users:
              await context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.id} not found")
          return self.users[request.id]

      async def ListUsers(
          self, request: pb2.ListUsersRequest, context: aio.ServicerContext
      ) -> AsyncGenerator[pb2.User, None]:
          for user in self.users.values():
              yield user


  @pytest.fixture
  async def async_grpc_server() -> AsyncGenerator[str, None]:
      """Start an async test gRPC server."""
      server = aio.server()
      pb2_grpc.add_TestServiceServicer_to_server(AsyncTestServiceServicer(), server)

      port = server.add_insecure_port("[::]:0")
      await server.start()

      address = f"localhost:{port}"
      yield address

      await server.stop(grace=1)

  tests/test_unary.py

  """Tests for unary RPC recording and playback."""

  from __future__ import annotations

  from pathlib import Path

  import grpc
  import pytest

  from grpcvr import Cassette, RecordMode, recorded_channel, RecordingChannel
  from grpcvr.errors import NoMatchingInteractionError, RecordingDisabledError

  from tests.generated import test_service_pb2 as pb2
  from tests.generated import test_service_pb2_grpc as pb2_grpc


  class TestUnaryRecording:
      """Test recording of unary RPCs."""

      def test_record_and_playback(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test basic record then playback flow."""
          # Record
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              response = stub.GetUser(pb2.GetUserRequest(id=1))
              assert response.name == "Alice"

          # Verify cassette was created
          assert cassette_path.exists()

          # Playback (no server needed theoretically, but we have it)
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.NONE
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              response = stub.GetUser(pb2.GetUserRequest(id=1))
              assert response.name == "Alice"

      def test_record_mode_none_fails_without_cassette(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test that NONE mode raises when cassette doesn't exist."""
          from grpcvr.errors import CassetteNotFoundError

          with pytest.raises(CassetteNotFoundError):
              with recorded_channel(
                  cassette_path, grpc_server, record_mode=RecordMode.NONE
              ) as channel:
                  pass

      def test_record_mode_none_fails_on_missing_interaction(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test that NONE mode raises for unrecorded interactions."""
          # Record user 1
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              stub.GetUser(pb2.GetUserRequest(id=1))

          # Try to get user 2 in NONE mode
          with pytest.raises(RecordingDisabledError):
              with recorded_channel(
                  cassette_path, grpc_server, record_mode=RecordMode.NONE
              ) as channel:
                  stub = pb2_grpc.TestServiceStub(channel)
                  stub.GetUser(pb2.GetUserRequest(id=2))

      def test_record_mode_all_overwrites(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test that ALL mode overwrites existing recordings."""
          # Initial recording
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              stub.GetUser(pb2.GetUserRequest(id=1))

          # Re-record with ALL mode
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.ALL
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              stub.GetUser(pb2.GetUserRequest(id=1))

          # Should still work
          cassette = Cassette(cassette_path)
          assert len(cassette.interactions) == 1

      def test_record_mode_new_episodes_adds(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test that NEW_EPISODES adds new interactions."""
          # Initial recording
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              stub.GetUser(pb2.GetUserRequest(id=1))

          # Add new episode
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.NEW_EPISODES
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              stub.GetUser(pb2.GetUserRequest(id=2))

          cassette = Cassette(cassette_path)
          assert len(cassette.interactions) == 2

      def test_grpc_error_recording(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test that gRPC errors are recorded and replayed."""
          # Record error
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              with pytest.raises(grpc.RpcError) as exc_info:
                  stub.GetUser(pb2.GetUserRequest(id=999))
              assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

          # Playback error
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.NONE
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              with pytest.raises(grpc.RpcError) as exc_info:
                  stub.GetUser(pb2.GetUserRequest(id=999))
              assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


  class TestUnaryMetadata:
      """Test metadata handling in unary RPCs."""

      def test_request_metadata_recorded(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test that request metadata is recorded."""
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              stub.GetUser(
                  pb2.GetUserRequest(id=1),
                  metadata=[("authorization", "Bearer token123")],
              )

          cassette = Cassette(cassette_path)
          interaction = cassette.interactions[0]
          assert "authorization" in interaction.request.metadata
          assert interaction.request.metadata["authorization"] == ["Bearer token123"]

  tests/test_streaming.py

  """Tests for streaming RPC recording and playback."""

  from __future__ import annotations

  from pathlib import Path

  import grpc
  import pytest

  from grpcvr import Cassette, RecordMode, recorded_channel

  from tests.generated import test_service_pb2 as pb2
  from tests.generated import test_service_pb2_grpc as pb2_grpc


  class TestServerStreaming:
      """Test server streaming RPC recording."""

      def test_record_and_playback_stream(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test recording and playing back a server stream."""
          # Record
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              responses = list(stub.ListUsers(pb2.ListUsersRequest(limit=2)))
              assert len(responses) == 2
              assert responses[0].name == "Alice"

          # Playback
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.NONE
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              responses = list(stub.ListUsers(pb2.ListUsersRequest(limit=2)))
              assert len(responses) == 2
              assert responses[0].name == "Alice"

      def test_empty_stream(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test recording an empty stream."""
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              responses = list(stub.ListUsers(pb2.ListUsersRequest(limit=0)))
              assert len(responses) == 0

          cassette = Cassette(cassette_path)
          assert cassette.interactions[0].rpc_type == "server_streaming"


  class TestClientStreaming:
      """Test client streaming RPC recording."""

      def test_record_and_playback_client_stream(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test recording and playing back a client stream."""
          def request_generator():
              yield pb2.CreateUserRequest(name="Dave", email="dave@example.com")
              yield pb2.CreateUserRequest(name="Eve", email="eve@example.com")

          # Record
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              response = stub.CreateUsers(request_generator())
              assert response.created_count == 2

          # Playback
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.NONE
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              response = stub.CreateUsers(request_generator())
              assert response.created_count == 2


  class TestBidirectionalStreaming:
      """Test bidirectional streaming RPC recording."""

      def test_record_and_playback_bidi_stream(
          self, grpc_server: str, cassette_path: Path
      ) -> None:
          """Test recording and playing back a bidirectional stream."""
          def request_generator():
              yield pb2.ChatMessage(sender="User", content="Hello", timestamp=1000)
              yield pb2.ChatMessage(sender="User", content="World", timestamp=2000)

          # Record
          with recorded_channel(cassette_path, grpc_server) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              responses = list(stub.Chat(request_generator()))
              assert len(responses) == 2
              assert responses[0].content == "Echo: Hello"

          # Playback
          with recorded_channel(
              cassette_path, grpc_server, record_mode=RecordMode.NONE
          ) as channel:
              stub = pb2_grpc.TestServiceStub(channel)
              responses = list(stub.Chat(request_generator()))
              assert len(responses) == 2
              assert responses[0].content == "Echo: Hello"

  tests/test_async.py

  """Tests for async gRPC recording and playback."""

  from __future__ import annotations

  from pathlib import Path

  import grpc
  from grpc import aio
  import pytest

  from grpcvr import Cassette, RecordMode
  from grpcvr.channel import AsyncRecordingChannel

  from tests.generated import test_service_pb2 as pb2
  from tests.generated import test_service_pb2_grpc as pb2_grpc


  @pytest.mark.asyncio
  class TestAsyncUnary:
      """Test async unary RPC recording."""

      async def test_record_and_playback(
          self, async_grpc_server: str, cassette_path: Path
      ) -> None:
          """Test async record and playback."""
          cassette = Cassette(cassette_path)

          # Record
          async with AsyncRecordingChannel(cassette, async_grpc_server) as recording:
              stub = pb2_grpc.TestServiceStub(recording.channel)
              response = await stub.GetUser(pb2.GetUserRequest(id=1))
              assert response.name == "Alice"

          # Playback
          cassette = Cassette(cassette_path, record_mode=RecordMode.NONE)
          async with AsyncRecordingChannel(cassette, async_grpc_server) as recording:
              stub = pb2_grpc.TestServiceStub(recording.channel)
              response = await stub.GetUser(pb2.GetUserRequest(id=1))
              assert response.name == "Alice"


  @pytest.mark.asyncio
  class TestAsyncStreaming:
      """Test async streaming RPC recording."""

      async def test_server_streaming(
          self, async_grpc_server: str, cassette_path: Path
      ) -> None:
          """Test async server streaming."""
          cassette = Cassette(cassette_path)

          async with AsyncRecordingChannel(cassette, async_grpc_server) as recording:
              stub = pb2_grpc.TestServiceStub(recording.channel)
              responses = []
              async for response in stub.ListUsers(pb2.ListUsersRequest()):
                  responses.append(response)
              assert len(responses) == 2

  tests/test_matchers.py

  """Tests for request matchers."""

  from __future__ import annotations

  import pytest

  from grpcvr.matchers import (
      MethodMatcher,
      MetadataMatcher,
      RequestMatcher,
      CustomMatcher,
      AllMatcher,
  )
  from grpcvr.serialization import InteractionRequest


  class TestMethodMatcher:
      """Test method matching."""

      def test_matches_same_method(self) -> None:
          matcher = MethodMatcher()
          req1 = InteractionRequest(method="/test.Service/Method", body="", metadata={})
          req2 = InteractionRequest(method="/test.Service/Method", body="", metadata={})
          assert matcher.matches(req1, req2)

      def test_rejects_different_method(self) -> None:
          matcher = MethodMatcher()
          req1 = InteractionRequest(method="/test.Service/Method1", body="", metadata={})
          req2 = InteractionRequest(method="/test.Service/Method2", body="", metadata={})
          assert not matcher.matches(req1, req2)


  class TestMetadataMatcher:
      """Test metadata matching."""

      def test_matches_specific_keys(self) -> None:
          matcher = MetadataMatcher(keys=["auth"])
          req1 = InteractionRequest(
              method="/test.Service/Method",
              body="",
              metadata={"auth": ["token"], "other": ["value1"]},
          )
          req2 = InteractionRequest(
              method="/test.Service/Method",
              body="",
              metadata={"auth": ["token"], "other": ["value2"]},
          )
          assert matcher.matches(req1, req2)

      def test_ignores_specified_keys(self) -> None:
          matcher = MetadataMatcher(ignore_keys=["request-id"])
          req1 = InteractionRequest(
              method="/test.Service/Method",
              body="",
              metadata={"auth": ["token"], "request-id": ["123"]},
          )
          req2 = InteractionRequest(
              method="/test.Service/Method",
              body="",
              metadata={"auth": ["token"], "request-id": ["456"]},
          )
          assert matcher.matches(req1, req2)


  class TestRequestMatcher:
      """Test request body matching."""

      def test_matches_same_body(self) -> None:
          matcher = RequestMatcher()
          req1 = InteractionRequest(method="/m", body="AQID", metadata={})  # base64
          req2 = InteractionRequest(method="/m", body="AQID", metadata={})
          assert matcher.matches(req1, req2)

      def test_rejects_different_body(self) -> None:
          matcher = RequestMatcher()
          req1 = InteractionRequest(method="/m", body="AQID", metadata={})
          req2 = InteractionRequest(method="/m", body="BAUG", metadata={})
          assert not matcher.matches(req1, req2)


  class TestMatcherCombination:
      """Test combining matchers."""

      def test_and_operator(self) -> None:
          combined = MethodMatcher() & RequestMatcher()
          assert isinstance(combined, AllMatcher)
          assert len(combined.matchers) == 2

      def test_all_matcher_requires_all(self) -> None:
          matcher = MethodMatcher() & RequestMatcher()

          # Same method, same body -> match
          req1 = InteractionRequest(method="/m", body="AQID", metadata={})
          req2 = InteractionRequest(method="/m", body="AQID", metadata={})
          assert matcher.matches(req1, req2)

          # Same method, different body -> no match
          req3 = InteractionRequest(method="/m", body="BAUG", metadata={})
          assert not matcher.matches(req1, req3)


  class TestCustomMatcher:
      """Test custom matchers."""

      def test_custom_function(self) -> None:
          def match_by_service(req: InteractionRequest, rec: InteractionRequest) -> bool:
              # Match if same service, regardless of method
              return req.method.rsplit("/", 1)[0] == rec.method.rsplit("/", 1)[0]

          matcher = CustomMatcher(match_by_service)

          req1 = InteractionRequest(method="/test.Service/Method1", body="", metadata={})
          req2 = InteractionRequest(method="/test.Service/Method2", body="", metadata={})
          assert matcher.matches(req1, req2)

  tests/test_examples.py

  """Test code examples from documentation."""

  from __future__ import annotations

  import pytest
  from pytest_examples import CodeExample, find_examples, EvalExample


  @pytest.mark.parametrize(
      "example",
      find_examples("docs"),
      ids=str,
  )
  def test_docs_examples(example: CodeExample, eval_example: EvalExample) -> None:
      """Run all code examples in documentation."""
      if example.config.get("test") == "skip":
          pytest.skip("Example marked as skip")

      eval_example.run_print_check(example)

  ---
  Documentation

  mkdocs.yml

  site_name: grpcvr
  site_description: Record and replay gRPC interactions for testing
  site_url: https://grpcvr.readthedocs.io
  repo_url: https://github.com/yourname/grpcvr
  repo_name: yourname/grpcvr

  theme:
    name: material
    palette:
      - scheme: default
        primary: blue grey
        accent: blue
        toggle:
          icon: material/brightness-7
          name: Switch to dark mode
      - scheme: slate
        primary: blue grey
        accent: blue
        toggle:
          icon: material/brightness-4
          name: Switch to light mode
    features:
      - content.code.copy
      - content.code.annotate
      - navigation.sections
      - navigation.expand
      - navigation.top
      - search.highlight
      - toc.follow

  nav:
    - Home: index.md
    - Installation: installation.md
    - Quickstart: quickstart.md
    - Concepts:
      - Cassettes: concepts/cassettes.md
      - Matchers: concepts/matchers.md
      - Record Modes: concepts/record-modes.md
      - Streaming RPCs: concepts/streaming.md
    - Guides:
      - pytest Integration: guides/pytest.md
      - Async Usage: guides/async.md
      - Custom Matchers: guides/custom-matchers.md
      - CI Testing: guides/ci-testing.md
    - API Reference: api/reference.md
    - Examples:
      - Basic Usage: examples/basic.md
      - Advanced Patterns: examples/advanced.md

  plugins:
    - search
    - mkdocstrings:
        handlers:
          python:
            options:
              show_source: true
              show_root_heading: true
              heading_level: 2
              members_order: source
              separate_signature: true
              docstring_style: google

  markdown_extensions:
    - admonition
    - pymdownx.details
    - pymdownx.superfences
    - pymdownx.highlight:
        anchor_linenums: true
    - pymdownx.inlinehilite
    - pymdownx.snippets
    - pymdownx.tabbed:
        alternate_style: true
    - toc:
        permalink: true

  docs/index.md

  # grpcvr

  **Record and replay gRPC interactions for testing.**

  grpcvr is a testing library that records gRPC calls during test runs and replays
  them later, eliminating the need for a live server during playback. Think
  [VCR.py](https://vcrpy.readthedocs.io/) but for gRPC.

  ## Features

  - **Simple API** - Context managers and pytest fixtures for easy integration
  - **All RPC types** - Unary, server streaming, client streaming, bidirectional
  - **Async support** - Full support for `grpc.aio`
  - **Flexible matching** - Match by method, metadata, request body, or custom logic
  - **pytest plugin** - Automatic cassette management per test
  - **CI-friendly** - Fail fast when cassettes are missing

  ## Quick Example

  ```python
  from grpcvr import recorded_channel

  # First run: records to cassette
  with recorded_channel("tests/cassettes/test.yaml", "localhost:50051") as channel:
      stub = MyServiceStub(channel)
      response = stub.GetUser(GetUserRequest(id=1))
      assert response.name == "Alice"

  # Subsequent runs: plays back from cassette (no server needed)

  Installation

  pip install grpcvr

  Why grpcvr?

  Testing gRPC services presents challenges:

  1. Server dependency - Tests need a running server
  2. Slow tests - Network calls are slow
  3. Flaky tests - Network issues cause random failures
  4. Complex setup - CI needs server infrastructure

  grpcvr solves these by recording interactions once, then replaying them:

  - No server needed - Playback works offline
  - Fast tests - No network latency
  - Reliable tests - Deterministic responses
  - Simple CI - Just commit cassettes to git

  ### `docs/quickstart.md`

  ```markdown
  # Quickstart

  This guide will get you up and running with grpcvr in minutes.

  ## Installation

  ```bash
  pip install grpcvr

  Basic Usage

  Recording

  The simplest way to use grpcvr is with the recorded_channel context manager:

  from grpcvr import recorded_channel

  # This will record to "test.yaml" on first run
  with recorded_channel("test.yaml", "localhost:50051") as channel:
      stub = MyServiceStub(channel)
      response = stub.GetUser(GetUserRequest(id=1))
      print(response.name)  # "Alice"

  Playback

  On subsequent runs, grpcvr plays back the recorded response:

  from grpcvr import recorded_channel, RecordMode

  # Force playback only - fails if cassette missing
  with recorded_channel(
      "test.yaml",
      "localhost:50051",
      record_mode=RecordMode.NONE
  ) as channel:
      stub = MyServiceStub(channel)
      response = stub.GetUser(GetUserRequest(id=1))
      # Returns recorded response - no server needed!

  pytest Integration

  grpcvr includes a pytest plugin for automatic cassette management:

  import pytest
  from grpcvr import RecordingChannel

  @pytest.fixture
  def grpc_target():
      return "localhost:50051"

  def test_get_user(cassette, grpc_target):
      """Cassette auto-created at tests/cassettes/test_get_user.yaml"""
      channel = RecordingChannel(cassette, grpc_target)
      stub = MyServiceStub(channel.channel)
      response = stub.GetUser(GetUserRequest(id=1))
      assert response.name == "Alice"

  Run with --grpcvr-record=none in CI to ensure all cassettes exist:

  pytest --grpcvr-record=none

  Record Modes
  ┌──────────────┬──────────────────────────────────────────┐
  │     Mode     │                 Behavior                 │
  ├──────────────┼──────────────────────────────────────────┤
  │ NEW_EPISODES │ Record new, play back existing (default) │
  ├──────────────┼──────────────────────────────────────────┤
  │ NONE         │ Playback only, error if missing          │
  ├──────────────┼──────────────────────────────────────────┤
  │ ALL          │ Always record, overwrite existing        │
  ├──────────────┼──────────────────────────────────────────┤
  │ ONCE         │ Record if cassette doesn't exist         │
  └──────────────┴──────────────────────────────────────────┘
  Next Steps

  - concepts/cassettes.md - Learn about the cassette format
  - concepts/matchers.md - Customize request matching
  - concepts/streaming.md - Handle streaming RPCs
  - guides/pytest.md - Full pytest integration

  ---

  ## CI Configuration

  ### `.github/workflows/ci.yml`

  ```yaml
  name: CI

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  env:
    PYTHON_VERSION: "3.12"
    UV_FROZEN: "1"

  jobs:
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
          with:
            enable-cache: true
        - run: uv sync --group lint
        - run: uv run ruff format --check src tests
        - run: uv run ruff check src tests
        - run: uv run pyright

    test:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: ["3.10", "3.11", "3.12", "3.13"]
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
          with:
            enable-cache: true
        - name: Set up Python ${{ matrix.python-version }}
          run: uv python install ${{ matrix.python-version }}
        - run: uv sync --group dev --python ${{ matrix.python-version }}
        - run: uv run make proto
        - run: uv run pytest --cov --cov-report=xml
        - uses: codecov/codecov-action@v4
          if: matrix.python-version == '3.12'
          with:
            token: ${{ secrets.CODECOV_TOKEN }}

    test-examples:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
          with:
            enable-cache: true
        - run: uv sync --group dev
        - run: uv run pytest tests/test_examples.py -v

    docs:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
          with:
            enable-cache: true
        - run: uv sync --group docs
        - run: uv run mkdocs build --strict

    all-checks:
      if: always()
      needs: [lint, test, test-examples, docs]
      runs-on: ubuntu-latest
      steps:
        - name: Check all jobs passed
          uses: re-actors/alls-green@release/v1
          with:
            jobs: ${{ toJSON(needs) }}

  .github/workflows/release.yml

  name: Release

  on:
    push:
      tags:
        - "v*"

  jobs:
    release:
      runs-on: ubuntu-latest
      permissions:
        id-token: write
        contents: write
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
        - run: uv build
        - uses: pypa/gh-action-pypi-publish@release/v1
        - name: Create GitHub Release
          uses: softprops/action-gh-release@v2
          with:
            generate_release_notes: true

  .pre-commit-config.yaml

  repos:
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.5.0
      hooks:
        - id: check-yaml
        - id: check-toml
        - id: end-of-file-fixer
        - id: trailing-whitespace
        - id: check-added-large-files
          args: ["--maxkb=1000"]

    - repo: local
      hooks:
        - id: format
          name: Format
          entry: uv run ruff format src tests
          language: system
          pass_filenames: false
          types: [python]

        - id: lint
          name: Lint
          entry: uv run ruff check --fix src tests
          language: system
          pass_filenames: false
          types: [python]

        - id: typecheck
          name: Typecheck
          entry: uv run pyright
          language: system
          pass_filenames: false
          types: [python]

  ---
  Summary

  This sketch provides a complete, production-ready gRPC recording library with:
  ┌───────────────┬──────────────┬──────────────────────────────────────────────────┐
  │   Component   │ Lines (est.) │                   Description                    │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ Core library  │ ~1,200       │ Cassettes, serialization, matchers, interceptors │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ Async support │ ~400         │ Full grpc.aio interceptors                       │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ pytest plugin │ ~150         │ Fixtures, markers, CLI options                   │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ Tests         │ ~600         │ Comprehensive test coverage                      │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ Documentation │ ~500         │ Guides, API docs, examples                       │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ Build/CI      │ ~300         │ pyproject.toml, Makefile, GitHub Actions         │
  ├───────────────┼──────────────┼──────────────────────────────────────────────────┤
  │ Total         │ ~3,150       │ Complete package                                 │
  └───────────────┴──────────────┴──────────────────────────────────────────────────┘
  Key design decisions:

  1. Interceptor-based - Uses gRPC's official extension mechanism, no monkey-patching
  2. One interaction = one RPC - Abstracts away HTTP/2 complexity
  3. Base64 for bodies - Safe serialization of protobuf bytes
  4. Composable matchers - Flexible request matching via & operator
  5. pytest-first - Deep pytest integration with auto cassette naming
  6. CI-ready - RecordMode.NONE for strict playback in CI

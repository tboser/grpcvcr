"""Serialization utilities for protobuf messages and cassettes."""

from __future__ import annotations

import base64
import importlib
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from grpcvcr.errors import SerializationError


def _get_importable_module_path(cls: type) -> str:
    """Get the actual importable module path for a class.

    Protobuf-generated classes report their __module__ as the proto file name,
    not the actual Python module path. This function finds the real importable
    path by searching sys.modules.

    Args:
        cls: The class to find the module path for.

    Returns:
        The fully qualified class path that can be used with importlib.
    """
    class_name = cls.__name__
    reported_module = cls.__module__

    for module_name, module in sys.modules.items():
        if module is None:
            continue
        try:
            if getattr(module, class_name, None) is cls:
                return f"{module_name}.{class_name}"
        except Exception:
            continue

    return f"{reported_module}.{class_name}"


def _load_class(type_path: str) -> type:
    """Load a class from its fully qualified path.

    Args:
        type_path: Fully qualified class path (e.g., 'mypackage.module.ClassName').

    Returns:
        The loaded class.

    Raises:
        ModuleNotFoundError: If the module cannot be imported.
        AttributeError: If the class doesn't exist in the module.
    """
    module_path, class_name = type_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@dataclass
class InteractionRequest:
    """Recorded gRPC request.

    Stores all information needed to match and replay a gRPC request,
    including the method path, serialized body, and metadata.

    Example:
        ```python
        request = InteractionRequest.from_grpc(
            method="/mypackage.MyService/GetUser",
            body=b"serialized_protobuf",
            metadata=(("authorization", "Bearer token"),),
        )
        ```
    """

    method: str
    """Full gRPC method path (e.g., '/package.Service/Method')."""

    body: str
    """Base64-encoded protobuf bytes."""

    metadata: dict[str, list[str]] = field(default_factory=dict)
    """Request metadata as a dict mapping header names to lists of values."""

    @classmethod
    def from_grpc(
        cls,
        method: str,
        body: bytes,
        metadata: tuple[tuple[str, str], ...] | None = None,
    ) -> InteractionRequest:
        """Create an InteractionRequest from gRPC call details.

        Args:
            method: Full gRPC method path.
            body: Raw protobuf bytes.
            metadata: Optional request metadata as tuples of (key, value).

        Returns:
            A new InteractionRequest instance.

        Example:
            ```python
            request = InteractionRequest.from_grpc(
                method="/test.TestService/GetUser",
                body=get_user_request.SerializeToString(),
                metadata=(("x-request-id", "123"),),
            )
            ```
        """
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
        """Decode the body back to raw protobuf bytes.

        Returns:
            The original protobuf bytes.
        """
        return base64.b64decode(self.body)


@dataclass
class InteractionResponse:
    """Recorded gRPC unary response.

    Stores the response body, status code, and metadata for replay.
    """

    body: str
    """Base64-encoded protobuf response bytes."""

    code: str
    """gRPC status code name (e.g., 'OK', 'NOT_FOUND', 'INTERNAL')."""

    details: str | None = None
    """Error details message, if the call failed."""

    trailing_metadata: dict[str, list[str]] = field(default_factory=dict)
    """Response trailing metadata as a dict mapping header names to lists of values."""

    response_type: str | None = None
    """Fully qualified response class name for deserialization (e.g., 'mypackage.pb2.GetUserResponse')."""

    @classmethod
    def from_grpc(
        cls,
        body: bytes,
        code: str,
        details: str | None = None,
        trailing_metadata: tuple[tuple[str, str], ...] | None = None,
        response_type: type | None = None,
    ) -> InteractionResponse:
        """Create an InteractionResponse from gRPC response data.

        Args:
            body: Raw protobuf response bytes.
            code: gRPC status code name.
            details: Optional error details.
            trailing_metadata: Optional trailing metadata as tuples.
            response_type: Optional response class for later deserialization.

        Returns:
            A new InteractionResponse instance.
        """
        meta_dict: dict[str, list[str]] = {}
        if trailing_metadata:
            for key, value in trailing_metadata:
                meta_dict.setdefault(key, []).append(value)

        type_str = None
        if response_type is not None:
            type_str = _get_importable_module_path(response_type)

        return cls(
            body=base64.b64encode(body).decode("ascii"),
            code=code,
            details=details,
            trailing_metadata=meta_dict,
            response_type=type_str,
        )

    def get_body_bytes(self) -> bytes:
        """Decode the body back to raw protobuf bytes.

        Returns:
            The original protobuf bytes.
        """
        return base64.b64decode(self.body)

    def get_response_class(self) -> type | None:
        """Load and return the response protobuf class.

        Returns:
            The response class if type info is available, None otherwise.

        Raises:
            ModuleNotFoundError: If the response type's module cannot be imported.
        """
        if not self.response_type:
            return None
        return _load_class(self.response_type)


@dataclass
class StreamingInteractionResponse:
    """Recorded gRPC streaming response.

    Stores multiple response messages for server-streaming or
    bidirectional streaming RPCs.
    """

    messages: list[str]
    """List of base64-encoded protobuf message bytes."""

    code: str
    """gRPC status code name."""

    details: str | None = None
    """Error details message, if the stream failed."""

    trailing_metadata: dict[str, list[str]] = field(default_factory=dict)
    """Response trailing metadata."""

    response_type: str | None = None
    """Fully qualified response message class name."""

    @classmethod
    def from_grpc(
        cls,
        messages: list[bytes],
        code: str,
        details: str | None = None,
        trailing_metadata: tuple[tuple[str, str], ...] | None = None,
        response_type: type | None = None,
    ) -> StreamingInteractionResponse:
        """Create a StreamingInteractionResponse from gRPC streaming data.

        Args:
            messages: List of raw protobuf message bytes.
            code: gRPC status code name.
            details: Optional error details.
            trailing_metadata: Optional trailing metadata as tuples.
            response_type: Optional response message class.

        Returns:
            A new StreamingInteractionResponse instance.
        """
        meta_dict: dict[str, list[str]] = {}
        if trailing_metadata:
            for key, value in trailing_metadata:
                meta_dict.setdefault(key, []).append(value)

        type_str = None
        if response_type is not None:
            type_str = _get_importable_module_path(response_type)

        return cls(
            messages=[base64.b64encode(m).decode("ascii") for m in messages],
            code=code,
            details=details,
            trailing_metadata=meta_dict,
            response_type=type_str,
        )

    def get_messages_bytes(self) -> list[bytes]:
        """Decode all messages back to raw protobuf bytes.

        Returns:
            List of original protobuf bytes.
        """
        return [base64.b64decode(m) for m in self.messages]

    def get_response_class(self) -> type | None:
        """Load and return the response protobuf class.

        Returns:
            The response class if type info is available, None otherwise.
        """
        if not self.response_type:
            return None
        return _load_class(self.response_type)


@dataclass
class Interaction:
    """A single recorded gRPC interaction (request + response pair).

    Represents one complete RPC call that can be matched and replayed.
    """

    request: InteractionRequest
    """The recorded request."""

    response: InteractionResponse | StreamingInteractionResponse
    """The recorded response (unary or streaming)."""

    rpc_type: Literal["unary", "server_streaming", "client_streaming", "bidi_streaming"]
    """The type of RPC call."""

    @property
    def method(self) -> str:
        """The gRPC method path from the request."""
        return self.request.method

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for serialization.

        Returns:
            Dictionary representation suitable for YAML/JSON serialization.
        """
        return {
            "request": asdict(self.request),
            "response": asdict(self.response),
            "rpc_type": self.rpc_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Interaction:
        """Create an Interaction from a dictionary.

        Args:
            data: Dictionary with 'request', 'response', and 'rpc_type' keys.

        Returns:
            A new Interaction instance.
        """
        rpc_type = data["rpc_type"]
        request = InteractionRequest(**data["request"])

        if rpc_type in ("server_streaming", "bidi_streaming"):
            response = StreamingInteractionResponse(**data["response"])
        else:
            response = InteractionResponse(**data["response"])

        return cls(request=request, response=response, rpc_type=rpc_type)


@dataclass
class CassetteData:
    """Complete cassette file contents.

    Contains version information and all recorded interactions.
    """

    version: int = 1
    """Cassette format version for future compatibility."""

    interactions: list[Interaction] = field(default_factory=list)
    """All recorded interactions in this cassette."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for serialization.

        Returns:
            Dictionary representation suitable for YAML/JSON serialization.
        """
        return {
            "version": self.version,
            "interactions": [i.to_dict() for i in self.interactions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CassetteData:
        """Create CassetteData from a dictionary.

        Args:
            data: Dictionary with optional 'version' and 'interactions' keys.

        Returns:
            A new CassetteData instance.
        """
        return cls(
            version=data.get("version", 1),
            interactions=[Interaction.from_dict(i) for i in data.get("interactions", [])],
        )


class CassetteSerializer:
    """Handles cassette file serialization to YAML or JSON.

    Example:
        ```python
        # Save a cassette
        CassetteSerializer.save(Path("test.yaml"), cassette_data)

        # Load a cassette
        data = CassetteSerializer.load(Path("test.yaml"))
        ```
    """

    @staticmethod
    def load(path: Path) -> CassetteData:
        """Load cassette data from a file.

        The format is determined by file extension: `.json` for JSON,
        anything else (including `.yaml`, `.yml`) for YAML.

        Args:
            path: Path to the cassette file.

        Returns:
            The loaded CassetteData.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            SerializationError: If the file cannot be parsed.
        """
        if not path.exists():
            raise FileNotFoundError(path)

        content = path.read_text(encoding="utf-8")

        try:
            if path.suffix == ".json":
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)
        except Exception as e:
            raise SerializationError(f"Failed to parse {path}", e) from e

        return CassetteData.from_dict(data)

    @staticmethod
    def save(path: Path, data: CassetteData) -> None:
        """Save cassette data to a file.

        Creates parent directories if they don't exist. The format is
        determined by file extension: `.json` for JSON, anything else
        for YAML.

        Args:
            path: Path to save the cassette file.
            data: The CassetteData to save.

        Raises:
            SerializationError: If the file cannot be written.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        dict_data = data.to_dict()

        try:
            if path.suffix == ".json":
                content = json.dumps(dict_data, indent=2)
            else:
                content = yaml.dump(
                    dict_data,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to write {path}", e) from e

"""Tests for serialization module."""

import base64
import tempfile
from pathlib import Path

import pytest

from grpcvcr.serialization import (
    CassetteData,
    CassetteSerializer,
    Interaction,
    InteractionRequest,
    InteractionResponse,
    StreamingInteractionResponse,
)


class TestInteractionRequest:
    def test_from_grpc_basic(self) -> None:
        req = InteractionRequest.from_grpc(
            method="/test.Service/Method",
            body=b"hello",
            metadata=None,
        )
        assert req.method == "/test.Service/Method"
        assert req.body == base64.b64encode(b"hello").decode("ascii")
        assert req.metadata == {}

    def test_from_grpc_with_metadata(self) -> None:
        req = InteractionRequest.from_grpc(
            method="/test.Service/Method",
            body=b"hello",
            metadata=(("key1", "value1"), ("key1", "value2"), ("key2", "value3")),
        )
        assert req.metadata == {"key1": ["value1", "value2"], "key2": ["value3"]}

    def test_get_body_bytes(self) -> None:
        req = InteractionRequest.from_grpc(
            method="/test.Service/Method",
            body=b"hello world",
        )
        assert req.get_body_bytes() == b"hello world"

    def test_from_grpc_default_target_is_none(self) -> None:
        req = InteractionRequest.from_grpc(
            method="/test.Service/Method",
            body=b"hello",
        )
        assert req.target is None

    def test_from_grpc_with_target(self) -> None:
        req = InteractionRequest.from_grpc(
            method="/test.Service/Method",
            body=b"hello",
            target="localhost:50051",
        )
        assert req.target == "localhost:50051"


class TestInteractionResponse:
    def test_from_grpc_success(self) -> None:
        resp = InteractionResponse.from_grpc(
            body=b"response",
            code="OK",
        )
        assert resp.code == "OK"
        assert resp.details is None
        assert resp.get_body_bytes() == b"response"

    def test_from_grpc_error(self) -> None:
        resp = InteractionResponse.from_grpc(
            body=b"",
            code="NOT_FOUND",
            details="Resource not found",
        )
        assert resp.code == "NOT_FOUND"
        assert resp.details == "Resource not found"


class TestStreamingInteractionResponse:
    def test_from_grpc(self) -> None:
        resp = StreamingInteractionResponse.from_grpc(
            messages=[b"msg1", b"msg2", b"msg3"],
            code="OK",
        )
        assert len(resp.messages) == 3
        assert resp.get_messages_bytes() == [b"msg1", b"msg2", b"msg3"]


class TestInteraction:
    def test_to_dict_and_from_dict_unary(self) -> None:
        interaction = Interaction(
            request=InteractionRequest.from_grpc("/test/Method", b"req"),
            response=InteractionResponse.from_grpc(b"resp", "OK"),
            rpc_type="unary",
        )

        data = interaction.to_dict()
        restored = Interaction.from_dict(data)

        assert restored.rpc_type == "unary"
        assert restored.request.method == "/test/Method"
        assert isinstance(restored.response, InteractionResponse)

    def test_to_dict_and_from_dict_streaming(self) -> None:
        interaction = Interaction(
            request=InteractionRequest.from_grpc("/test/Method", b"req"),
            response=StreamingInteractionResponse.from_grpc([b"m1", b"m2"], "OK"),
            rpc_type="server_streaming",
        )

        data = interaction.to_dict()
        restored = Interaction.from_dict(data)

        assert restored.rpc_type == "server_streaming"
        assert isinstance(restored.response, StreamingInteractionResponse)

    def test_to_dict_and_from_dict_preserves_target(self) -> None:
        interaction = Interaction(
            request=InteractionRequest.from_grpc("/test/Method", b"req", target="localhost:50051"),
            response=InteractionResponse.from_grpc(b"resp", "OK"),
            rpc_type="unary",
        )

        data = interaction.to_dict()
        restored = Interaction.from_dict(data)

        assert restored.request.target == "localhost:50051"

    def test_from_dict_legacy_request_without_target(self) -> None:
        data = {
            "request": {"method": "/test/Method", "body": "aGVsbG8=", "metadata": {}},
            "response": {"body": "cmVzcA==", "code": "OK"},
            "rpc_type": "unary",
        }

        restored = Interaction.from_dict(data)

        assert restored.request.target is None


class TestCassetteSerializer:
    def test_save_and_load_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"

            data = CassetteData(
                version=1,
                interactions=[
                    Interaction(
                        request=InteractionRequest.from_grpc("/test/Method", b"req"),
                        response=InteractionResponse.from_grpc(b"resp", "OK"),
                        rpc_type="unary",
                    )
                ],
            )

            CassetteSerializer.save(path, data)
            assert path.exists()

            loaded = CassetteSerializer.load(path)
            assert loaded.version == 1
            assert len(loaded.interactions) == 1
            assert loaded.interactions[0].request.method == "/test/Method"

    def test_save_and_load_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"

            data = CassetteData(
                version=1,
                interactions=[
                    Interaction(
                        request=InteractionRequest.from_grpc("/test/Method", b"req"),
                        response=InteractionResponse.from_grpc(b"resp", "OK"),
                        rpc_type="unary",
                    )
                ],
            )

            CassetteSerializer.save(path, data)
            loaded = CassetteSerializer.load(path)

            assert len(loaded.interactions) == 1

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            CassetteSerializer.load(Path("/nonexistent/path.yaml"))

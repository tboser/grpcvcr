"""Tests for edge cases and untested code paths."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import grpc
import pytest
from grpc import aio

from grpcvcr import (
    AllMatcher,
    Cassette,
    MetadataMatcher,
    MethodMatcher,
    RecordMode,
    use_cassette,
)
from grpcvcr.channel import AsyncRecordingChannel, RecordingChannel
from grpcvcr.errors import SerializationError
from grpcvcr.interceptors._base import _FakeStreamingCall, _FakeUnaryCall
from grpcvcr.interceptors.aio import _AsyncFakeStreamingCall, _AsyncFakeUnaryCall
from grpcvcr.serialization import (
    CassetteData,
    CassetteSerializer,
    Interaction,
    InteractionRequest,
    InteractionResponse,
    StreamingInteractionResponse,
    _get_importable_module_path,
)


class TestCassetteEdgeCases:
    def test_path_string_to_path_conversion(self, tmp_path: Path) -> None:
        path_str = str(tmp_path / "test.yaml")
        cassette = Cassette(path_str, record_mode=RecordMode.ALL)  # type: ignore
        assert isinstance(cassette.path, Path)

    def test_record_mode_once_creates_empty_cassette(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "once_test.yaml"
        cassette = Cassette(cassette_path, record_mode=RecordMode.ONCE)
        assert len(cassette.interactions) == 0
        assert cassette.can_record

    def test_cassette_context_manager(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "context_test.yaml"
        with Cassette(cassette_path, record_mode=RecordMode.ALL) as cassette:
            interaction = Interaction(
                request=InteractionRequest(method="/test/Method", body="dGVzdA==", metadata={}),
                response=InteractionResponse(body="dGVzdA==", code="OK"),
                rpc_type="unary",
            )
            cassette.record_interaction(interaction)

        assert cassette_path.exists()

    def test_use_cassette_function(self, tmp_path: Path, grpc_target: str, pb2, pb2_grpc, grpc_servicer) -> None:
        cassette_path = tmp_path / "use_cassette_test.yaml"

        with (
            use_cassette(cassette_path, record_mode=RecordMode.ALL) as cassette,
            RecordingChannel(cassette, grpc_target) as recording,
        ):
            stub = pb2_grpc.TestServiceStub(recording.channel)
            response = stub.GetUser(pb2.GetUserRequest(id=1))

        assert response.user.id == 1
        assert cassette_path.exists()


class TestChannelEdgeCases:
    def test_recording_channel_with_credentials(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "secure_test.yaml"
        cassette = Cassette(cassette_path, record_mode=RecordMode.ALL)
        credentials = grpc.ssl_channel_credentials()

        recording = RecordingChannel(
            cassette,
            "localhost:50051",
            credentials=credentials,
            options=[("grpc.ssl_target_name_override", "localhost")],
        )
        recording.close()

    def test_async_recording_channel_with_credentials(self, tmp_path: Path) -> None:
        cassette_path = tmp_path / "async_secure_test.yaml"
        cassette = Cassette(cassette_path, record_mode=RecordMode.ALL)
        credentials = grpc.ssl_channel_credentials()

        AsyncRecordingChannel(
            cassette,
            "localhost:50051",
            credentials=credentials,
            options=[("grpc.ssl_target_name_override", "localhost")],
        )
        cassette.save()


class TestFakeCallEdgeCases:
    def test_fake_unary_call_result_raises_on_error(self) -> None:
        call = _FakeUnaryCall(
            result=None,
            code=grpc.StatusCode.INTERNAL,
            details="Internal error",
            trailing_metadata=(),
        )
        with pytest.raises(grpc.RpcError):
            call.result()

    def test_fake_unary_call_code(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.code() == grpc.StatusCode.OK

    def test_fake_unary_call_details(self) -> None:
        call = _FakeUnaryCall(
            result=None,
            code=grpc.StatusCode.NOT_FOUND,
            details="Not found",
            trailing_metadata=(),
        )
        assert call.details() == "Not found"

    def test_fake_unary_call_cancelled(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancelled() is False

    def test_fake_unary_call_running(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.running() is False

    def test_fake_unary_call_done(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.done() is True

    def test_fake_unary_call_add_done_callback(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        called = []
        call.add_done_callback(lambda c: called.append(c))
        assert len(called) == 1
        assert called[0] is call

    def test_fake_unary_call_exception_returns_error_on_failure(self) -> None:
        call = _FakeUnaryCall(
            result=None,
            code=grpc.StatusCode.INTERNAL,
            details="Error",
            trailing_metadata=(),
        )
        exc = call.exception()
        assert isinstance(exc, grpc.RpcError)

    def test_fake_unary_call_exception_returns_none_on_success(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.exception() is None

    def test_fake_unary_call_traceback(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.traceback() is None

    def test_fake_unary_call_add_callback(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        called = []
        result = call.add_callback(lambda c: called.append(c))
        assert result is True
        assert len(called) == 1

    def test_fake_unary_call_is_active(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.is_active() is False

    def test_fake_unary_call_time_remaining(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.time_remaining() is None

    def test_fake_unary_call_cancel(self) -> None:
        call = _FakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancel() is False

    def test_fake_streaming_call_code(self) -> None:
        call = _FakeStreamingCall(
            messages=["msg1", "msg2"],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.code() == grpc.StatusCode.OK

    def test_fake_streaming_call_details(self) -> None:
        call = _FakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.INTERNAL,
            details="Error",
            trailing_metadata=(),
        )
        assert call.details() == "Error"

    def test_fake_streaming_call_cancelled(self) -> None:
        call = _FakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancelled() is False

    def test_fake_streaming_call_add_callback(self) -> None:
        call = _FakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        called = []
        result = call.add_callback(lambda c: called.append(c))
        assert result is True
        assert len(called) == 1

    def test_fake_streaming_call_is_active(self) -> None:
        call = _FakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.is_active() is False

    def test_fake_streaming_call_time_remaining(self) -> None:
        call = _FakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.time_remaining() is None

    def test_fake_streaming_call_cancel(self) -> None:
        call = _FakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancel() is False


class TestAsyncFakeCallSyncMethods:
    def test_async_fake_unary_call_cancelled(self) -> None:
        call = _AsyncFakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancelled() is False

    def test_async_fake_unary_call_done(self) -> None:
        call = _AsyncFakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.done() is True

    def test_async_fake_unary_call_cancel(self) -> None:
        call = _AsyncFakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancel() is False

    def test_async_fake_unary_call_time_remaining(self) -> None:
        call = _AsyncFakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.time_remaining() is None

    def test_async_fake_streaming_call_cancelled(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancelled() is False

    def test_async_fake_streaming_call_done(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.done() is True

    def test_async_fake_streaming_call_cancel(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.cancel() is False

    def test_async_fake_streaming_call_time_remaining(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert call.time_remaining() is None


@pytest.mark.asyncio
class TestAsyncFakeCallAsyncMethods:
    async def test_async_fake_unary_call_await_raises_on_error(self) -> None:
        call = _AsyncFakeUnaryCall(
            result=None,
            code=grpc.StatusCode.INTERNAL,
            details="Internal error",
            trailing_metadata=(),
        )
        with pytest.raises(aio.AioRpcError):
            await call

    async def test_async_fake_unary_call_code(self) -> None:
        call = _AsyncFakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert await call.code() == grpc.StatusCode.OK

    async def test_async_fake_unary_call_details(self) -> None:
        call = _AsyncFakeUnaryCall(
            result=None,
            code=grpc.StatusCode.NOT_FOUND,
            details="Not found",
            trailing_metadata=(),
        )
        assert await call.details() == "Not found"

    async def test_async_fake_unary_call_wait_for_connection(self) -> None:
        call = _AsyncFakeUnaryCall(
            result="test",
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        await call.wait_for_connection()

    async def test_async_fake_streaming_call_iterate_raises_on_error(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=["msg1", "msg2"],
            code=grpc.StatusCode.INTERNAL,
            details="Stream error",
            trailing_metadata=(),
        )
        messages = []
        with pytest.raises(aio.AioRpcError):
            async for msg in call:
                messages.append(msg)

        assert messages == ["msg1", "msg2"]

    async def test_async_fake_streaming_call_code(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=["msg"],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        assert await call.code() == grpc.StatusCode.OK

    async def test_async_fake_streaming_call_details(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.INTERNAL,
            details="Error",
            trailing_metadata=(),
        )
        assert await call.details() == "Error"

    async def test_async_fake_streaming_call_wait_for_connection(self) -> None:
        call = _AsyncFakeStreamingCall(
            messages=[],
            code=grpc.StatusCode.OK,
            details=None,
            trailing_metadata=(),
        )
        await call.wait_for_connection()


class TestMatcherEdgeCases:
    def test_all_matcher_chaining(self) -> None:
        matcher1 = MethodMatcher()
        matcher2 = MetadataMatcher()
        matcher3 = MetadataMatcher(keys=["x-custom"])

        combined = matcher1 & matcher2
        assert isinstance(combined, AllMatcher)
        assert len(combined.matchers) == 2

        combined2 = combined & matcher3
        assert isinstance(combined2, AllMatcher)
        assert len(combined2.matchers) == 3

    def test_metadata_matcher_keys_mismatch(self) -> None:
        matcher = MetadataMatcher(keys=["authorization"])

        request = InteractionRequest(
            method="/test/Method",
            body="dGVzdA==",
            metadata={"authorization": ["Bearer token1"]},
        )
        recorded = InteractionRequest(
            method="/test/Method",
            body="dGVzdA==",
            metadata={"authorization": ["Bearer token2"]},
        )

        assert matcher.matches(request, recorded) is False


class TestSerializationEdgeCases:
    def test_get_importable_module_path_fallback(self) -> None:
        class UnregisteredClass:
            pass

        UnregisteredClass.__module__ = "fake.module"

        path = _get_importable_module_path(UnregisteredClass)
        assert path == "fake.module.UnregisteredClass"

    def test_get_importable_module_path_with_none_module(self) -> None:
        original_value = sys.modules.get("_test_none_module_")

        try:
            sys.modules["_test_none_module_"] = None  # type: ignore

            class TestClass:
                pass

            TestClass.__module__ = "nonexistent.module"
            path = _get_importable_module_path(TestClass)
            assert path == "nonexistent.module.TestClass"
        finally:
            if original_value is None:
                sys.modules.pop("_test_none_module_", None)
            else:
                sys.modules["_test_none_module_"] = original_value

    def test_get_importable_module_path_handles_getattr_exception(self) -> None:
        class BadModule(ModuleType):
            def __getattr__(self, name: str) -> None:
                raise RuntimeError("Cannot get attribute")

        original_value = sys.modules.get("_test_bad_module_")

        try:
            bad_module = BadModule("_test_bad_module_")
            sys.modules["_test_bad_module_"] = bad_module

            class AnotherTestClass:
                pass

            AnotherTestClass.__module__ = "another.module"
            path = _get_importable_module_path(AnotherTestClass)
            assert path == "another.module.AnotherTestClass"
        finally:
            if original_value is None:
                sys.modules.pop("_test_bad_module_", None)
            else:
                sys.modules["_test_bad_module_"] = original_value

    def test_interaction_response_get_response_class_none(self) -> None:
        response = InteractionResponse(
            body="dGVzdA==",
            code="OK",
            response_type=None,
        )
        assert response.get_response_class() is None

    def test_streaming_response_get_response_class_none(self) -> None:
        response = StreamingInteractionResponse(
            messages=["dGVzdA=="],
            code="OK",
            response_type=None,
        )
        assert response.get_response_class() is None

    def test_cassette_serializer_load_json_error(self, tmp_path: Path) -> None:
        json_path = tmp_path / "invalid.json"
        json_path.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(SerializationError) as exc_info:
            CassetteSerializer.load(json_path)

        assert "Failed to parse" in str(exc_info.value)

    def test_cassette_serializer_save_json_error(self, tmp_path: Path) -> None:
        unwritable_path = tmp_path / "nonexistent" / "deep" / "nested" / "test.json"
        data = CassetteData()

        with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
            with pytest.raises(SerializationError) as exc_info:
                CassetteSerializer.save(unwritable_path, data)

            assert "Failed to write" in str(exc_info.value)

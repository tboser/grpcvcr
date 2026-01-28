"""Shared test fixtures and configuration."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from concurrent import futures
from pathlib import Path
from typing import TYPE_CHECKING

import grpc
import pytest

if TYPE_CHECKING:
    from tests.generated import test_service_pb2


def _import_generated() -> tuple:
    """Import generated proto modules."""
    from tests.generated import test_service_pb2, test_service_pb2_grpc

    return test_service_pb2, test_service_pb2_grpc


class TestServiceServicer:
    """Test service implementation for integration tests."""

    def __init__(self) -> None:
        self.pb2, _ = _import_generated()
        self.call_count = 0

    def GetUser(
        self,
        request: test_service_pb2.GetUserRequest,
        context: grpc.ServicerContext,
    ) -> test_service_pb2.GetUserResponse:
        self.call_count += 1
        user = self.pb2.User(
            id=request.id,
            name=f"User {request.id}",
            email=f"user{request.id}@example.com",
        )
        return self.pb2.GetUserResponse(user=user)

    def ListUsers(
        self,
        request: test_service_pb2.ListUsersRequest,
        context: grpc.ServicerContext,
    ) -> Iterator[test_service_pb2.User]:
        self.call_count += 1
        for i in range(request.limit):
            yield self.pb2.User(
                id=i + 1,
                name=f"User {i + 1}",
                email=f"user{i + 1}@example.com",
            )

    def CreateUsers(
        self,
        request_iterator: Iterator[test_service_pb2.CreateUserRequest],
        context: grpc.ServicerContext,
    ) -> test_service_pb2.CreateUsersResponse:
        self.call_count += 1
        ids = []
        for i, _req in enumerate(request_iterator):
            ids.append(i + 1)
        return self.pb2.CreateUsersResponse(created_count=len(ids), ids=ids)

    def Chat(
        self,
        request_iterator: Iterator[test_service_pb2.ChatMessage],
        context: grpc.ServicerContext,
    ) -> Iterator[test_service_pb2.ChatMessage]:
        self.call_count += 1
        for msg in request_iterator:
            yield self.pb2.ChatMessage(
                sender="server",
                content=f"Echo: {msg.content}",
                timestamp=msg.timestamp,
            )


class GrpcTestServer:
    """Manages a gRPC test server for integration tests."""

    def __init__(self) -> None:
        self.server: grpc.Server | None = None
        self.servicer: TestServiceServicer | None = None
        self.port: int | None = None
        self._started = threading.Event()

    def start(self) -> str:
        """Start the test server and return the target address."""
        _, pb2_grpc = _import_generated()

        self.servicer = TestServiceServicer()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        pb2_grpc.add_TestServiceServicer_to_server(self.servicer, self.server)

        self.port = self.server.add_insecure_port("[::]:0")
        self.server.start()
        self._started.set()

        return f"localhost:{self.port}"

    def stop(self) -> None:
        """Stop the test server."""
        if self.server:
            self.server.stop(grace=0)
            self.server.wait_for_termination(timeout=5)
            self.server = None

    @property
    def call_count(self) -> int:
        """Number of RPC calls received by the server."""
        return self.servicer.call_count if self.servicer else 0

    def reset_call_count(self) -> None:
        """Reset the call counter."""
        if self.servicer:
            self.servicer.call_count = 0


@pytest.fixture(scope="session")
def grpc_test_server() -> Generator[GrpcTestServer, None, None]:
    """Session-scoped gRPC test server."""
    server = GrpcTestServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def grpc_target(grpc_test_server: GrpcTestServer) -> str:
    """Get the gRPC server target address."""
    return f"localhost:{grpc_test_server.port}"


@pytest.fixture
def grpc_servicer(grpc_test_server: GrpcTestServer) -> TestServiceServicer:
    """Get the test servicer instance."""
    grpc_test_server.reset_call_count()
    assert grpc_test_server.servicer is not None
    return grpc_test_server.servicer


@pytest.fixture
def tmp_cassette_path(tmp_path: Path) -> Path:
    """Temporary path for a cassette file."""
    return tmp_path / "test_cassette.yaml"


@pytest.fixture
def pb2():
    """Get the test_service_pb2 module."""
    pb2, _ = _import_generated()
    return pb2


@pytest.fixture
def pb2_grpc():
    """Get the test_service_pb2_grpc module."""
    _, pb2_grpc = _import_generated()
    return pb2_grpc

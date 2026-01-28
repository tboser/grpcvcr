"""Tests for matchers module."""

from grpcvcr.matchers import (
    AllMatcher,
    CustomMatcher,
    MetadataMatcher,
    MethodMatcher,
    RequestMatcher,
    find_matching_interaction,
)
from grpcvcr.serialization import (
    Interaction,
    InteractionRequest,
    InteractionResponse,
)


def make_request(
    method: str = "/test/Method",
    body: bytes = b"body",
    metadata: dict[str, list[str]] | None = None,
) -> InteractionRequest:
    """Helper to create InteractionRequest."""
    req = InteractionRequest.from_grpc(method, body)
    if metadata:
        req.metadata = metadata
    return req


class TestMethodMatcher:
    def test_matches_same_method(self) -> None:
        matcher = MethodMatcher()
        req1 = make_request(method="/test/Method")
        req2 = make_request(method="/test/Method")
        assert matcher.matches(req1, req2)

    def test_not_matches_different_method(self) -> None:
        matcher = MethodMatcher()
        req1 = make_request(method="/test/Method1")
        req2 = make_request(method="/test/Method2")
        assert not matcher.matches(req1, req2)


class TestRequestMatcher:
    def test_matches_same_body(self) -> None:
        matcher = RequestMatcher()
        req1 = make_request(body=b"same")
        req2 = make_request(body=b"same")
        assert matcher.matches(req1, req2)

    def test_not_matches_different_body(self) -> None:
        matcher = RequestMatcher()
        req1 = make_request(body=b"body1")
        req2 = make_request(body=b"body2")
        assert not matcher.matches(req1, req2)


class TestMetadataMatcher:
    def test_matches_all_metadata(self) -> None:
        matcher = MetadataMatcher()
        req1 = make_request(metadata={"key": ["value"]})
        req2 = make_request(metadata={"key": ["value"]})
        assert matcher.matches(req1, req2)

    def test_not_matches_different_metadata(self) -> None:
        matcher = MetadataMatcher()
        req1 = make_request(metadata={"key": ["value1"]})
        req2 = make_request(metadata={"key": ["value2"]})
        assert not matcher.matches(req1, req2)

    def test_matches_specific_keys(self) -> None:
        matcher = MetadataMatcher(keys=["important"])
        req1 = make_request(metadata={"important": ["same"], "other": ["diff1"]})
        req2 = make_request(metadata={"important": ["same"], "other": ["diff2"]})
        assert matcher.matches(req1, req2)

    def test_ignores_specified_keys(self) -> None:
        matcher = MetadataMatcher(ignore_keys=["x-request-id"])
        req1 = make_request(metadata={"x-request-id": ["123"], "auth": ["token"]})
        req2 = make_request(metadata={"x-request-id": ["456"], "auth": ["token"]})
        assert matcher.matches(req1, req2)


class TestCustomMatcher:
    def test_custom_function(self) -> None:
        def always_true(req: InteractionRequest, rec: InteractionRequest) -> bool:
            return True

        matcher = CustomMatcher(func=always_true)
        req1 = make_request()
        req2 = make_request(method="/different")
        assert matcher.matches(req1, req2)

    def test_custom_function_false(self) -> None:
        def always_false(req: InteractionRequest, rec: InteractionRequest) -> bool:
            return False

        matcher = CustomMatcher(func=always_false)
        req1 = make_request()
        req2 = make_request()
        assert not matcher.matches(req1, req2)


class TestAllMatcher:
    def test_all_must_match(self) -> None:
        matcher = AllMatcher(matchers=[MethodMatcher(), RequestMatcher()])
        req1 = make_request(method="/test", body=b"body")
        req2 = make_request(method="/test", body=b"body")
        assert matcher.matches(req1, req2)

    def test_fails_if_any_fails(self) -> None:
        matcher = AllMatcher(matchers=[MethodMatcher(), RequestMatcher()])
        req1 = make_request(method="/test", body=b"body1")
        req2 = make_request(method="/test", body=b"body2")
        assert not matcher.matches(req1, req2)

    def test_combine_with_and(self) -> None:
        matcher = MethodMatcher() & RequestMatcher()
        assert isinstance(matcher, AllMatcher)
        assert len(matcher.matchers) == 2


class TestFindMatchingInteraction:
    def test_finds_match(self) -> None:
        interactions = [
            Interaction(
                request=make_request(method="/test/Method1"),
                response=InteractionResponse.from_grpc(b"resp1", "OK"),
                rpc_type="unary",
            ),
            Interaction(
                request=make_request(method="/test/Method2"),
                response=InteractionResponse.from_grpc(b"resp2", "OK"),
                rpc_type="unary",
            ),
        ]

        result = find_matching_interaction(
            make_request(method="/test/Method2"),
            interactions,
            MethodMatcher(),
        )

        assert result is not None
        assert result.request.method == "/test/Method2"

    def test_returns_none_when_no_match(self) -> None:
        interactions = [
            Interaction(
                request=make_request(method="/test/Method1"),
                response=InteractionResponse.from_grpc(b"resp", "OK"),
                rpc_type="unary",
            ),
        ]

        result = find_matching_interaction(
            make_request(method="/test/Other"),
            interactions,
            MethodMatcher(),
        )

        assert result is None

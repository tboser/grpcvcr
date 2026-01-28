"""Request matching strategies for finding recorded interactions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field

from grpcvr.serialization import Interaction, InteractionRequest


class Matcher(ABC):
    """Base class for request matchers.

    Matchers determine whether an incoming request matches a recorded
    interaction. They can be combined using the `&` operator.

    Example:
        ```python
        # Match on method and request body
        matcher = MethodMatcher() & RequestMatcher()

        cassette = Cassette("test.yaml", match_on=matcher)
        ```
    """

    @abstractmethod
    def matches(
        self,
        request: InteractionRequest,
        recorded: InteractionRequest,
    ) -> bool:
        """Check if a request matches a recorded interaction.

        Args:
            request: The incoming request to match.
            recorded: The recorded request to compare against.

        Returns:
            True if the requests match, False otherwise.
        """
        ...

    def __and__(self, other: Matcher) -> AllMatcher:
        """Combine this matcher with another using AND logic.

        Args:
            other: Another matcher to combine with.

        Returns:
            An AllMatcher that requires both matchers to succeed.

        Example:
            ```python
            matcher = MethodMatcher() & RequestMatcher()
            ```
        """
        if isinstance(self, AllMatcher):
            return AllMatcher(matchers=[*self.matchers, other])
        return AllMatcher(matchers=[self, other])


@dataclass
class MethodMatcher(Matcher):
    """Matches requests by gRPC method path.

    This is the default matcher. Method paths have the format:
    `/package.ServiceName/MethodName`

    Example:
        ```python
        matcher = MethodMatcher()
        # Matches if request.method == recorded.method
        ```
    """

    def matches(
        self,
        request: InteractionRequest,
        recorded: InteractionRequest,
    ) -> bool:
        """Check if method paths match exactly."""
        return request.method == recorded.method


@dataclass
class MetadataMatcher(Matcher):
    """Matches requests by metadata (headers).

    Can be configured to match specific keys only, or to ignore
    certain keys (like timestamps or request IDs).

    Example:
        ```python
        # Only compare authorization header
        matcher = MetadataMatcher(keys=["authorization"])

        # Compare all metadata except request ID
        matcher = MetadataMatcher(ignore_keys=["x-request-id"])
        ```
    """

    keys: list[str] | None = None
    """If set, only these metadata keys are compared."""

    ignore_keys: list[str] | None = None
    """If set, these metadata keys are ignored during comparison."""

    def matches(
        self,
        request: InteractionRequest,
        recorded: InteractionRequest,
    ) -> bool:
        """Check if metadata matches according to configured rules."""
        req_meta = request.metadata
        rec_meta = recorded.metadata

        if self.keys is not None:
            for key in self.keys:
                if req_meta.get(key) != rec_meta.get(key):
                    return False
            return True

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
    """Matches requests by body content.

    Compares the base64-encoded protobuf bytes directly. For semantic
    comparison of protobuf fields, use a CustomMatcher.

    Example:
        ```python
        # Exact body match
        matcher = MethodMatcher() & RequestMatcher()
        ```
    """

    def matches(
        self,
        request: InteractionRequest,
        recorded: InteractionRequest,
    ) -> bool:
        """Check if request bodies match exactly."""
        return request.body == recorded.body


@dataclass
class CustomMatcher(Matcher):
    """Matches requests using a custom function.

    Useful for complex matching logic like comparing specific protobuf
    fields or implementing fuzzy matching.

    Example:
        ```python
        def match_user_id(req: InteractionRequest, rec: InteractionRequest) -> bool:
            # Deserialize and compare specific fields
            req_msg = UserRequest.FromString(req.get_body_bytes())
            rec_msg = UserRequest.FromString(rec.get_body_bytes())
            return req_msg.user_id == rec_msg.user_id

        matcher = MethodMatcher() & CustomMatcher(func=match_user_id)
        ```
    """

    func: Callable[[InteractionRequest, InteractionRequest], bool]
    """The matching function. Takes (request, recorded) and returns bool."""

    name: str | None = None
    """Optional name for debugging and logging."""

    def matches(
        self,
        request: InteractionRequest,
        recorded: InteractionRequest,
    ) -> bool:
        """Delegate to the custom matching function."""
        return self.func(request, recorded)


@dataclass
class AllMatcher(Matcher):
    """Combines multiple matchers with AND logic.

    All contained matchers must return True for the request to match.
    Usually created implicitly via the `&` operator.

    Example:
        ```python
        # These are equivalent:
        matcher = AllMatcher(matchers=[MethodMatcher(), RequestMatcher()])
        matcher = MethodMatcher() & RequestMatcher()
        ```
    """

    matchers: list[Matcher] = field(default_factory=list)
    """List of matchers that must all succeed."""

    def matches(
        self,
        request: InteractionRequest,
        recorded: InteractionRequest,
    ) -> bool:
        """Check if all contained matchers succeed."""
        return all(m.matches(request, recorded) for m in self.matchers)


DEFAULT_MATCHER = MethodMatcher()
"""The default matcher used when none is specified. Matches on method path only."""


def find_matching_interaction(
    request: InteractionRequest,
    interactions: list[Interaction],
    matcher: Matcher = DEFAULT_MATCHER,
) -> Interaction | None:
    """Find the first interaction that matches a request.

    Args:
        request: The incoming request to match.
        interactions: List of recorded interactions to search.
        matcher: The matcher to use for comparison.

    Returns:
        The first matching Interaction, or None if no match is found.

    Example:
        ```python
        interaction = find_matching_interaction(
            request,
            cassette.interactions,
            matcher=MethodMatcher() & RequestMatcher(),
        )
        if interaction:
            return interaction.response
        ```
    """
    for interaction in interactions:
        if matcher.matches(request, interaction.request):
            return interaction
    return None

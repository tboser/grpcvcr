# Custom Matchers

Create custom matching logic for complex scenarios.

## When to Use Custom Matchers

Custom matchers are useful when:

- Requests contain timestamps or UUIDs that change between runs
- You want to match on specific fields rather than the entire request
- You need complex comparison logic

## Creating a Custom Matcher

Use `CustomMatcher` with a function that takes two `InteractionRequest` objects:

```python
from grpcvcr import CustomMatcher


def ignore_timestamp(request, recorded_request):
    """Match by method only, ignoring any timestamp differences."""
    return request.method == recorded_request.method


matcher = CustomMatcher(ignore_timestamp)
```

## Accessing Request Data

The `InteractionRequest` object provides access to:

```python
# test: skip
def my_matcher(request, recorded_request):
    # Method name (e.g., "/package.Service/Method")
    request.method

    # Request body as base64-encoded string
    request.body

    # Request body as bytes
    request.get_body_bytes()

    # Metadata as dict[str, list[str]]
    request.metadata

    return True  # or False
```

## Combining Custom with Built-in Matchers

Combine custom matchers with built-in ones:

```python
from grpcvcr import CustomMatcher, MethodMatcher


def check_auth_header(request, recorded_request):
    """Ensure authorization header matches."""
    req_auth = request.metadata.get("authorization", [])
    rec_auth = recorded_request.metadata.get("authorization", [])
    return req_auth == rec_auth


# Match by method AND custom auth check
matcher = MethodMatcher() & CustomMatcher(check_auth_header)
```

## Example: Ignoring Dynamic Fields

If your requests contain fields that change (like timestamps), you can deserialize and compare specific fields:

```python
# test: skip
from grpcvcr import CustomMatcher, MethodMatcher


def match_user_id_only(request, recorded_request):
    """Match GetUserRequest by id field only."""
    if request.method != recorded_request.method:
        return False

    # Deserialize and compare specific fields
    # (You'll need access to your proto classes)
    from myservice import user_pb2

    req = user_pb2.GetUserRequest.FromString(request.get_body_bytes())
    rec = user_pb2.GetUserRequest.FromString(recorded_request.get_body_bytes())

    return req.id == rec.id


matcher = CustomMatcher(match_user_id_only)
```

## Example: Partial Metadata Matching

Match some metadata keys while ignoring others:

```python
from grpcvcr import CustomMatcher, MethodMatcher, RequestMatcher

IMPORTANT_HEADERS = ["authorization", "x-api-key"]


def match_important_headers(request, recorded_request):
    """Match only specific metadata keys."""
    for key in IMPORTANT_HEADERS:
        if request.metadata.get(key) != recorded_request.metadata.get(key):
            return False
    return True


# Combine with method and body matching
matcher = MethodMatcher() & RequestMatcher() & CustomMatcher(match_important_headers)
```

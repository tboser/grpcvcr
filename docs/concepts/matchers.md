# Request Matching

Matchers determine how grpcvr finds the right recorded response for each request.

## Default Matching

By default, grpcvr matches requests by method name only:

```python test="skip"
from grpcvr import Cassette

# Uses MethodMatcher by default
cassette = Cassette("test.yaml")
```

This means two requests to the same method will match the same recorded response, regardless of their request body or metadata.

## Available Matchers

### MethodMatcher

Matches by the gRPC method name (e.g., `/package.Service/Method`).

```python
from grpcvr import MethodMatcher

matcher = MethodMatcher()
```

### RequestMatcher

Matches by the serialized request body.

```python
from grpcvr import RequestMatcher

matcher = RequestMatcher()
```

### MetadataMatcher

Matches by request metadata (headers).

```python
from grpcvr import MetadataMatcher

# Match all metadata
matcher = MetadataMatcher()

# Match only specific keys
matcher = MetadataMatcher(keys=["authorization", "x-request-id"])

# Ignore specific keys
matcher = MetadataMatcher(ignore_keys=["x-timestamp"])
```

## Combining Matchers

Use `&` to combine matchers:

```python
from grpcvr import MetadataMatcher, MethodMatcher, RequestMatcher

# Match by method AND body
matcher = MethodMatcher() & RequestMatcher()

# Match by method, body, AND auth header
matcher = MethodMatcher() & RequestMatcher() & MetadataMatcher(keys=["authorization"])
```

## Custom Matchers

Create custom matching logic:

```python
from grpcvr import CustomMatcher


def my_matcher(request, recorded_request):
    # Custom comparison logic
    return request.method == recorded_request.method


matcher = CustomMatcher(my_matcher)
```

## Using Matchers

Pass matchers when creating a cassette:

```python test="skip"
from grpcvr import Cassette, MethodMatcher, RequestMatcher

matcher = MethodMatcher() & RequestMatcher()
cassette = Cassette("test.yaml", match_on=matcher)
```

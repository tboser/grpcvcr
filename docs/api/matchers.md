# Matchers

Matchers determine how recorded interactions are matched to incoming requests during playback.

## Overview

By default, grpcvcr matches requests by method name only. You can customize matching behavior using different matchers or combining them.

```python
from grpcvcr import MethodMatcher, RequestMatcher

# Match by method name and request body
matcher = MethodMatcher() & RequestMatcher()
```

## Built-in Matchers

| Matcher | Description |
|---------|-------------|
| [`MethodMatcher`][grpcvcr.MethodMatcher] | Match by RPC method name |
| [`RequestMatcher`][grpcvcr.RequestMatcher] | Match by request body |
| [`MetadataMatcher`][grpcvcr.MetadataMatcher] | Match by request metadata |
| [`AllMatcher`][grpcvcr.AllMatcher] | Combine multiple matchers |
| [`CustomMatcher`][grpcvcr.CustomMatcher] | Custom matching function |

## API Reference

::: grpcvcr.Matcher
    options:
      members:
        - matches
        - __and__

::: grpcvcr.MethodMatcher

::: grpcvcr.RequestMatcher

::: grpcvcr.MetadataMatcher

::: grpcvcr.AllMatcher

::: grpcvcr.CustomMatcher

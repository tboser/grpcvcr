# Matchers

Matchers determine how recorded interactions are matched to incoming requests during playback.

## Overview

By default, grpcvr matches requests by method name only. You can customize matching behavior using different matchers or combining them.

```python
from grpcvr import MethodMatcher, RequestMatcher

# Match by method name and request body
matcher = MethodMatcher() & RequestMatcher()
```

## Built-in Matchers

| Matcher | Description |
|---------|-------------|
| [`MethodMatcher`][grpcvr.MethodMatcher] | Match by RPC method name |
| [`RequestMatcher`][grpcvr.RequestMatcher] | Match by request body |
| [`MetadataMatcher`][grpcvr.MetadataMatcher] | Match by request metadata |
| [`AllMatcher`][grpcvr.AllMatcher] | Combine multiple matchers |
| [`CustomMatcher`][grpcvr.CustomMatcher] | Custom matching function |

## API Reference

::: grpcvr.Matcher
    options:
      members:
        - matches
        - __and__

::: grpcvr.MethodMatcher

::: grpcvr.RequestMatcher

::: grpcvr.MetadataMatcher

::: grpcvr.AllMatcher

::: grpcvr.CustomMatcher

# API Reference

This section provides detailed API documentation for all public classes and functions in grpcvcr.

## Core Components

- **[Cassette](cassette.md)** - Recording/playback container for gRPC interactions
- **[Channel](channel.md)** - Recording channel wrapper for gRPC channels
- **[Matchers](matchers.md)** - Request matching strategies
- **[Record Modes](record-modes.md)** - Recording behavior modes
- **[Errors](errors.md)** - Exception classes

## Quick Links

| Class | Description |
|-------|-------------|
| [`Cassette`][grpcvcr.Cassette] | Container for recorded interactions |
| [`RecordingChannel`][grpcvcr.RecordingChannel] | Sync recording channel |
| [`recorded_channel`][grpcvcr.recorded_channel] | Context manager for easy usage |
| [`RecordMode`][grpcvcr.RecordMode] | Recording behavior enum |
| [`MethodMatcher`][grpcvcr.MethodMatcher] | Match by RPC method name |
| [`RequestMatcher`][grpcvcr.RequestMatcher] | Match by request body |

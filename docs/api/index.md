# API Reference

This section provides detailed API documentation for all public classes and functions in grpcvr.

## Core Components

- **[Cassette](cassette.md)** - Recording/playback container for gRPC interactions
- **[Channel](channel.md)** - Recording channel wrapper for gRPC channels
- **[Matchers](matchers.md)** - Request matching strategies
- **[Record Modes](record-modes.md)** - Recording behavior modes
- **[Errors](errors.md)** - Exception classes

## Quick Links

| Class | Description |
|-------|-------------|
| [`Cassette`][grpcvr.Cassette] | Container for recorded interactions |
| [`RecordingChannel`][grpcvr.RecordingChannel] | Sync recording channel |
| [`recorded_channel`][grpcvr.recorded_channel] | Context manager for easy usage |
| [`RecordMode`][grpcvr.RecordMode] | Recording behavior enum |
| [`MethodMatcher`][grpcvr.MethodMatcher] | Match by RPC method name |
| [`RequestMatcher`][grpcvr.RequestMatcher] | Match by request body |

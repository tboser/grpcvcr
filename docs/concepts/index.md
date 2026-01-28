# Concepts

Understanding the core concepts behind grpcvcr.

## Overview

grpcvcr works by intercepting gRPC calls at the channel level. When you wrap a channel with grpcvcr:

1. **Recording**: Outgoing requests are passed through to the real server, and the request/response pair is saved to a cassette file
2. **Playback**: Incoming requests are matched against recorded interactions, and the stored response is returned without making a network call

## Core Concepts

### [Cassettes](cassettes.md)

Cassettes are YAML or JSON files that store recorded gRPC interactions. Each cassette contains a list of request/response pairs that can be replayed during tests.

### [Request Matching](matchers.md)

When replaying, grpcvcr needs to find the right recorded response for each request. Matchers define how requests are compared to find matches.

### [Record Modes](record-modes.md)

Record modes control when grpcvcr records new interactions versus playing back existing ones. Different modes are useful for different stages of development.

### [Streaming](streaming.md)

grpcvcr supports all four gRPC call types: unary, server streaming, client streaming, and bidirectional streaming.

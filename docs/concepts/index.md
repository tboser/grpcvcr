# Concepts

Understanding the core concepts behind grpcvr.

## Overview

grpcvr works by intercepting gRPC calls at the channel level. When you wrap a channel with grpcvr:

1. **Recording**: Outgoing requests are passed through to the real server, and the request/response pair is saved to a cassette file
2. **Playback**: Incoming requests are matched against recorded interactions, and the stored response is returned without making a network call

## Core Concepts

### [Cassettes](cassettes.md)

Cassettes are YAML or JSON files that store recorded gRPC interactions. Each cassette contains a list of request/response pairs that can be replayed during tests.

### [Request Matching](matchers.md)

When replaying, grpcvr needs to find the right recorded response for each request. Matchers define how requests are compared to find matches.

### [Record Modes](record-modes.md)

Record modes control when grpcvr records new interactions versus playing back existing ones. Different modes are useful for different stages of development.

### [Streaming](streaming.md)

grpcvr supports all four gRPC call types: unary, server streaming, client streaming, and bidirectional streaming.

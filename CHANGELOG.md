# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of grpcvcr
- Recording and playback of gRPC interactions via interceptors
- Support for all RPC types: unary, server streaming, client streaming, bidirectional streaming
- Async support with `AsyncRecordingChannel` for `grpc.aio`
- YAML and JSON cassette formats
- Flexible request matching with `MethodMatcher`, `RequestMatcher`, `MetadataMatcher`, and `CustomMatcher`
- Matcher composition with `&` operator
- Four record modes: `NONE`, `NEW_EPISODES`, `ALL`, `ONCE`
- pytest plugin with automatic cassette management
- CLI options: `--grpcvcr-record`, `--grpcvcr-cassette-dir`
- Automatic `RecordMode.NONE` in CI environments
- `@pytest.mark.grpcvcr` marker for per-test configuration
- Context managers: `recorded_channel`, `async_recorded_channel`, `use_cassette`
- Full type annotations (PEP 561 compatible)
- Documentation with MkDocs Material theme

# Contributing to grpcvr

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Getting Started

```bash
# Clone the repository
git clone https://github.com/yourusername/grpcvr.git
cd grpcvr

# Install dependencies and set up pre-commit hooks
make install
```

## Development Workflow

### Common Commands

```bash
make install      # Install dependencies + pre-commit hooks
make sync         # Update dependencies
make format       # Format code with ruff
make lint         # Check code style
make typecheck    # Run pyright type checking
make test         # Run tests
make testcov      # Run tests with coverage report
make all          # Run format, lint, typecheck, and tests
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make testcov

# Run specific test file
uv run pytest tests/test_matchers.py -v

# Run specific test
uv run pytest tests/test_matchers.py::TestMethodMatcher::test_matches_same_method -v
```

### Code Quality

The project uses:
- **ruff** for linting and formatting
- **pyright** for type checking
- **pytest** for testing

All checks run automatically via pre-commit hooks on commit. You can run them manually:

```bash
make all
```

### Generating Protobuf Code

If you modify the test proto files:

```bash
make proto
```

## Project Structure

```
grpcvr/
├── src/grpcvr/           # Main library code
│   ├── interceptors/     # gRPC interceptors (sync and async)
│   ├── cassette.py       # Cassette management
│   ├── channel.py        # Channel wrappers
│   ├── matchers.py       # Request matching
│   ├── serialization.py  # Protobuf serialization
│   └── pytest_plugin.py  # pytest integration
├── tests/                # Test suite
│   ├── protos/           # Test .proto files
│   ├── generated/        # Generated protobuf code
│   └── cassettes/        # Test cassette files
└── docs/                 # Documentation
```

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make all` to ensure all checks pass
5. Submit a pull request

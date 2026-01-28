# Installation

## Requirements

- Python 3.11 or higher
- grpcio 1.50.0 or higher

## Install with pip

```bash test="skip"
pip install grpcvr
```

## Install with uv

```bash test="skip"
uv add grpcvr
```

## Development Installation

To contribute to grpcvr or run the test suite:

```bash test="skip"
git clone https://github.com/tboser/grpcvcr.git
cd grpcvcr
make install
```

This will:

1. Install all dependencies including dev tools
2. Set up pre-commit hooks
3. Generate proto files for tests

## Verify Installation

```python
import grpcvr

print(grpcvr.__version__)
```

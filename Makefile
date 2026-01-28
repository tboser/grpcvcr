.DEFAULT_GOAL := all
sources = src/grpcvcr tests

.PHONY: install
install:
	uv sync --all-extras
	uv run pre-commit install

.PHONY: sync
sync:
	uv sync --all-extras

.PHONY: format
format:
	uv run ruff format $(sources)
	uv run ruff check --fix $(sources)

.PHONY: lint
lint:
	uv run ruff format --check $(sources)
	uv run ruff check $(sources)

.PHONY: typecheck
typecheck:
	uv run pyright

.PHONY: test
test:
	uv run pytest tests/ -v --ignore=tests/test_examples.py

.PHONY: test-examples
test-examples:
	uv run pytest tests/test_examples.py -v

.PHONY: test-all
test-all:
	uv run pytest tests/ -v

.PHONY: testcov
testcov:
	uv run pytest tests/ --ignore=tests/test_examples.py -p no:grpcvcr --cov=src/grpcvcr --cov-report=term-missing --cov-report=html

.PHONY: proto
proto:
	uv run python -m grpc_tools.protoc \
		-Itests/protos \
		--python_out=tests/generated \
		--grpc_python_out=tests/generated \
		tests/protos/*.proto
	touch tests/generated/__init__.py
	# Fix absolute imports to relative imports for proper package resolution
	sed -i '' 's/^import test_service_pb2/from tests.generated import test_service_pb2/' tests/generated/test_service_pb2_grpc.py

.PHONY: docs
docs:
	uv run mkdocs build

.PHONY: docs-serve
docs-serve:
	uv run mkdocs serve

.PHONY: clean
clean:
	rm -rf build dist .eggs *.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov site
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: all
all: format lint typecheck testcov

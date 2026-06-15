SOURCE := $(wildcard src/dpsprep/*.py)

.PHONY: lint test test-multienv build-docs

lint:
	uv run ruff check
	uv run mypy

test:
	uv run pytest

test-multienv:
	uv run tox

docs:
	mkdir docs

docs/dpsprep.1: $(SOURCE) pyproject.toml docs/examples.man | docs
	uv run python -c 'from src.helpers.docs import build_man_page; build_man_page()'

# Render the man page as text and indent the entire file so that it is a valid markdown code block
docs/dpsprep.1.md: docs/dpsprep.1
	uv run python -c 'from src.helpers.docs import build_man_md; build_man_md()'

build-docs: docs/dpsprep.1.md

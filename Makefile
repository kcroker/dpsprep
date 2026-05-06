SOURCE := $(wildcard src/dpsprep/*.py)

.PHONY: lint test build-docs

lint:
	uv run ruff check
	uv run mypy

test:
	uv run pytest

docs:
	mkdir docs

docs/dpsprep.1: $(SOURCE) pyproject.toml docs/examples.man | docs
	uv run click-man dpsprep \
		--target docs \
		--man-version $(shell git describe --tags) \
		--man-date $(shell git log --max-count 1 --format=%as)

	cat docs/examples.man >> docs/dpsprep.1

# Render the man page as text and indent the entire file so that it is a valid markdown code block
docs/dpsprep.1.md: docs/dpsprep.1
	echo -n '    ' > docs/dpsprep.1.md
	MANWIDTH=100 man docs/dpsprep.1 | sed --null-data 's/\n/\n    /g' | head --lines=-1 >> docs/dpsprep.1.md

build-docs: docs/dpsprep.1.md

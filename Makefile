.PHONY: lint test

lint:
	uv run ruff check
	uv run mypy

test:
	uv run pytest

dpsprep.1: dpsprep.1.ronn
	ronn --roff dpsprep.1.ronn

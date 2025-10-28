.PHONY: lint test

lint:
	poetry run ruff check
	poetry run mypy

test:
	poetry run pytest

dpsprep.1: dpsprep.1.ronn
	ronn --roff dpsprep.1.ronn

.PHONY: lint test

lint:
	poetry run ruff check dpsprep
	poetry run mypy --package dpsprep

test:
	poetry run pytest --capture tee-sys

dpsprep.1: dpsprep.1.ronn
	ronn --roff dpsprep.1.ronn

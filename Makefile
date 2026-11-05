PYTHON := python3
FUNC_DEF ?= data/input/functions_definition.json
INPUT ?= data/input/function_calling_tests.json
OUTPUT ?= data/output/function_calls.json

install:
	uv sync --locked

run:
	uv run python src/Main.py \
	--function_definition $(FUNC_DEF) --input $(INPUT) --output $(OUTPUT)

debug:
	$(PYTHON) -m pdb src/Main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache

lint: mypy flake8

lint-strict: lint
	mypy . --strict

flake8:
	flake8 .

mypy:
	mypy . --warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

.PHONY: lint mypy flake8 run clean install debug lint-strict
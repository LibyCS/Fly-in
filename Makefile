MAIN = main.py

install:
	python3 -m pip install -U flake8 mypy

run:
	python3 $(MAIN)

debug:
	python3 -m pdb $(MAIN)

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	flake8 .
	mypy .

lint-strict:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-stict
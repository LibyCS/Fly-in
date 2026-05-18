MAIN = main.py

venv:
	@test -d venv || python3 -m venv venv

install: venv
	venv/bin/python3 -m pip install -U flake8 mypy
	venv/bin/python3 -m pip install matplotlib
	venv/bin/python3 -m pip install pydantic
	venv/bin/python3 -m pip install pytest

run: venv
	venv/bin/python3 $(MAIN) $(FILE)

debug: venv
	venv/bin/python3 -m pdb $(MAIN)

clean:
	rm -rf __pycache__ .mypy_cache visualiser.png

lint: venv
	venv/bin/flake8 . --exclude venv
	venv/bin/mypy . --exclude venv

lint-strict: venv
	venv/bin/flake8 . --exclude venv
	venv/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude venv

pytest: install
	pytest

.PHONY: venv install run debug clean lint lint-stict pytest
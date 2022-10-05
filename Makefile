SHELL := /bin/bash
PYTHON_SRC= $(wildcard tests/*.py) $(wildcard momomail/*/*.py)

fmt:
	@echo "Running black"
	@source venv/bin/activate;\
	black $(PYTHON_SRC)

flake:
	@echo "Running autoflake"
	@source venv/bin/activate;\
	autoflake --in-place --remove-all-unused-imports $(PYTHON_SRC);\
	flake8 $(PYTHON_SRC)

pytype:
	@echo "Running pytype"
	source venv/bin/activate;\
	pytype $(PYTHON_SRC)

ck: fmt flake pytype

clear:
	find . -type d -name "__pycache__" -o -type d -name "*.egg-info" -o -type d -name ".pytype" -o -maxdepth 1 -type d -name "build" | xargs rm -rf
SHELL := /bin/bash
PYTHON_SRC= $(wildcard *.py) $(wildcard */*.py)

fmt:
	@echo "Running black"
	@source venv/bin/activate;\
	black -l 70 $(PYTHON_SRC)

flake:
	@echo "Running autoflake"
	@source venv/bin/activate;\
	autoflake --in-place --remove-all-unused-imports $(PYTHON_SRC);\
	flake8 $(PYTHON_SRC)

pytype:
	@echo "Running pytype"
	@source venv/bin/activate;\
	pytype $(PYTHON_SRC)

ck: fmt flake pytype
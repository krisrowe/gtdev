VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: setup test install clean

setup:
	python3 -m venv $(VENV)
	$(PIP) install --index-url https://pypi.org/simple --upgrade pip
	$(PIP) install --index-url https://pypi.org/simple -e .[dev]

test: setup
	$(VENV)/bin/pytest

install:
	pipx install -e . --force

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

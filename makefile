PYTHON_EXE=python
PYTHON_ARGS?=

SETUP_REQUIRES=src/build/setup.py build.yaml


.PHONY: all
all: test build

.PHONY: install
install: $(SETUP_REQUIRES) test
	@echo "Attempting to install package..."
	$(PYTHON_EXE) $(PYTHON_ARGS) $< install

	@echo "Install successful."

build: $(SETUP_REQUIRES) test
	@echo "Attempting to build distributables..."
	$(PYTHON_EXE) $(PYTHON_ARGS) $< sdist
	$(PYTHON_EXE) $(PYTHON_ARGS) $< bdist

	@echo "Build successful."

.PHONY: test # Not implemented so skipping for now
test:
	@echo "Tests have not been implemented yet. Skipping for now."

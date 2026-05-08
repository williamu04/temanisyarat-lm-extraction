.PHONY: all venv augment extract

VENV_DIR = .venv

all: venv augment extract

venv:
	python -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

augment: venv
	./augmentation.sh

extract: augment
	./extract.sh $(VENV_DIR)

.PHONY: all venv augment extract clean

all: venv augment extract

venv:
	python -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

augment: venv
	./augmentation.sh

extract: augment
	./extract.sh

clean:
	rm -rf $(VENV_DIR) $(VIDEO_OUT) $(NPY_OUT)

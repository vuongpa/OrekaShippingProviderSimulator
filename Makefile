APP_NAME := OrekaShippingProviderSimulator
PYTHON ?= python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
SOURCES := app.py api.py providers.py config.py

.DEFAULT_GOAL := help
.PHONY: help dev run check venv build build-macos clean distclean

help: ## Liệt kê các lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

dev: check ## Chạy app (không cần cài gì thêm)
	$(PYTHON) app.py

run: dev ## Bí danh của dev

check: ## Kiểm tra python và tkinter có sẵn
	@$(PYTHON) -c "import tkinter" 2>/dev/null \
		|| { echo "Thiếu tkinter. macOS: brew install python-tk"; exit 1; }
	@$(PYTHON) -m py_compile $(SOURCES) && echo "OK: python + tkinter sẵn sàng"

venv: ## Tạo .venv và cài công cụ đóng gói
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements-dev.txt

build: build-macos ## Bí danh của build-macos

build-macos: venv ## Đóng gói bản macOS (.app + zip) vào dist/
	$(VENV)/bin/pyinstaller \
		--noconfirm \
		--clean \
		--windowed \
		--name $(APP_NAME) \
		app.py
	xattr -cr dist/$(APP_NAME).app
	codesign --force --deep --sign - dist/$(APP_NAME).app
	cd dist && zip -qry $(APP_NAME)-macos.zip $(APP_NAME).app
	@echo "Đã đóng gói: dist/$(APP_NAME)-macos.zip"

clean: ## Xoá sản phẩm build
	rm -rf build dist $(APP_NAME).spec __pycache__

distclean: clean ## Xoá cả .venv
	rm -rf $(VENV)

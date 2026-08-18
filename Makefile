APP_NAME := OrekaShippingProviderSimulator
VENV := .venv
SOURCES := app.py api.py providers.py config.py

ifeq ($(OS),Windows_NT)
	HOST_OS := windows
	VENV_BIN := $(VENV)/Scripts
	PYTHON ?= python
else
	VENV_BIN := $(VENV)/bin
	PYTHON ?= python3
	ifeq ($(shell uname -s),Darwin)
		HOST_OS := macos
	else
		HOST_OS := linux
	endif
endif

VENV_PY := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip
PYINSTALLER := $(VENV_BIN)/pyinstaller

.DEFAULT_GOAL := help
.PHONY: help dev run check venv build build-macos build-windows clean distclean

help: ## Liệt kê các lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

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

build: ## Đóng gói bản cho hệ điều hành đang chạy
ifeq ($(HOST_OS),windows)
	$(MAKE) build-windows
else
	$(MAKE) build-macos
endif

build-macos: ## Đóng gói bản macOS (.app + .zip) vào dist/
ifneq ($(HOST_OS),macos)
	@echo "Chỉ build được .app trên macOS. Máy này: $(HOST_OS)."
	@echo "Không có máy macOS: dùng .github/workflows/build.yml (GitHub Actions)."
	@exit 1
else
	$(MAKE) venv
	$(PYINSTALLER) \
		--noconfirm \
		--clean \
		--windowed \
		--name $(APP_NAME) \
		app.py
	xattr -cr dist/$(APP_NAME).app
	codesign --force --deep --sign - dist/$(APP_NAME).app
	cd dist && zip -qry $(APP_NAME)-macos.zip $(APP_NAME).app
	@echo "Đã đóng gói: dist/$(APP_NAME)-macos.zip"
endif

build-windows: ## Đóng gói bản Windows (.exe) vào dist/
ifneq ($(HOST_OS),windows)
	@echo "Chỉ build được .exe trên Windows — PyInstaller không cross-compile. Máy này: $(HOST_OS)."
	@echo "Trên Windows: double-click build_windows.bat, hoặc make build-windows trong Git Bash."
	@echo "Không có máy Windows: dùng .github/workflows/build.yml (GitHub Actions)."
	@exit 1
else
	$(MAKE) venv
	$(PYINSTALLER) \
		--noconfirm \
		--clean \
		--windowed \
		--onefile \
		--name $(APP_NAME) \
		app.py
	@echo "Đã đóng gói: dist/$(APP_NAME).exe"
endif

clean: ## Xoá sản phẩm build
	rm -rf build dist $(APP_NAME).spec __pycache__

distclean: clean ## Xoá cả .venv
	rm -rf $(VENV)

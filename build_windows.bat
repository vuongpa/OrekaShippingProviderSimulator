@echo off
setlocal
set APP_NAME=OrekaShippingProviderSimulator
cd /d "%~dp0"

where py >nul 2>nul && (set PY=py -3) || (set PY=python)

%PY% -m venv .venv-win || goto :error
call .venv-win\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
python -m pip install -r requirements-dev.txt || goto :error

pyinstaller --noconfirm --clean --windowed --onefile --name %APP_NAME% app.py || goto :error

echo.
echo Da dong goi: dist\%APP_NAME%.exe
exit /b 0

:error
echo.
echo Build that bai.
exit /b 1

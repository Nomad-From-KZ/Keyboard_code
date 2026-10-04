@echo off
chcp 65001 > nul
cd /d "%~dp0"

if not exist "venv" (
    echo [1/3] Создание виртуального окружения...
    python -m venv venv
    echo [2/3] Установка PyQt6...
    .\venv\Scripts\python.exe -m pip install PyQt6
)

echo [3/3] Запуск программы...
echo --------------------------------------------------
.\venv\Scripts\python.exe main.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Программа завершилась с ошибкой.
)
pause
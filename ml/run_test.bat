@echo off
REM Скрипт для запуска тестирования моделей из виртуального окружения

echo ========================================
echo Запуск тестирования LLM моделей
echo ========================================
echo.

REM Проверка наличия виртуального окружения
if not exist "..\ml_env\Scripts\python.exe" (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Создайте его командой: python -m venv ml_env
    echo Затем установите зависимости: ml_env\Scripts\pip install -r ml\requirements.txt
    pause
    exit /b 1
)

REM Запуск скрипта через Python из виртуального окружения
echo Используется Python из виртуального окружения...
echo.
..\ml_env\Scripts\python.exe ml\test_models.py

pause

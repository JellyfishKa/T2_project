@echo off
REM Скрипт для запуска бенчмарка из виртуального окружения

echo ========================================
echo Запуск бенчмарка LLM моделей
echo ========================================
echo.

REM Проверка наличия виртуального окружения
if not exist "..\..\ml_env\Scripts\python.exe" (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Создайте его командой: python -m venv ml_env
    pause
    exit /b 1
)

REM Запуск бенчмарка
echo Используется Python из виртуального окружения...
echo.
echo Параметры:
echo   --iterations N  : Количество итераций (по умолчанию: 5)
echo   --mock          : Использовать mock режим (без загрузки моделей)
echo.
echo Примеры:
echo   run_benchmark.bat
echo   run_benchmark.bat --iterations 3
echo   run_benchmark.bat --mock
echo.

..\..\ml_env\Scripts\python.exe llm_benchmark.py %*

pause

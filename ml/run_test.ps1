# Скрипт для запуска тестирования моделей из виртуального окружения (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Запуск тестирования LLM моделей" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия виртуального окружения
$venvPython = Join-Path $PSScriptRoot "..\ml_env\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ОШИБКА: Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Создайте его командой: python -m venv ml_env" -ForegroundColor Yellow
    Write-Host "Затем установите зависимости: ml_env\Scripts\pip install -r ml\requirements.txt" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Запуск скрипта через Python из виртуального окружения
Write-Host "Используется Python из виртуального окружения..." -ForegroundColor Green
Write-Host ""

& $venvPython (Join-Path $PSScriptRoot "test_models.py")

Read-Host "`nНажмите Enter для выхода"

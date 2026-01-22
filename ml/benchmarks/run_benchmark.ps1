# Скрипт для запуска бенчмарка из виртуального окружения (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Запуск бенчмарка LLM моделей" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия виртуального окружения
$venvPython = Join-Path $PSScriptRoot "..\..\ml_env\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ОШИБКА: Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Создайте его командой: python -m venv ml_env" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Используется Python из виртуального окружения..." -ForegroundColor Green
Write-Host ""
Write-Host "Параметры:" -ForegroundColor Yellow
Write-Host "  --iterations N  : Количество итераций (по умолчанию: 5)" -ForegroundColor White
Write-Host "  --mock          : Использовать mock режим (без загрузки моделей)" -ForegroundColor White
Write-Host ""
Write-Host "Примеры:" -ForegroundColor Yellow
Write-Host "  .\run_benchmark.ps1" -ForegroundColor White
Write-Host "  .\run_benchmark.ps1 --iterations 3" -ForegroundColor White
Write-Host "  .\run_benchmark.ps1 --mock" -ForegroundColor White
Write-Host ""

# Запуск бенчмарка с переданными аргументами
& $venvPython (Join-Path $PSScriptRoot "llm_benchmark.py") $args

Read-Host "`nНажмите Enter для выхода"

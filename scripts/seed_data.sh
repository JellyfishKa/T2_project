#!/usr/bin/env bash
# seed_data.sh — Загрузка тестовых данных в T2 API
# Использование: bash scripts/seed_data.sh [HOST] [PORT]

set -euo pipefail

HOST="${1:-localhost}"
PORT="${2:-8000}"
BASE_URL="http://${HOST}:${PORT}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../data"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; }

echo "========================================"
echo "  T2 Seed Data Script"
echo "  Target: ${BASE_URL}"
echo "========================================"
echo ""

# --- 1. Health check ---
echo "--- Шаг 1: Проверка здоровья сервера ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    info "Сервер доступен (HTTP ${HTTP_CODE})"
else
    fail "Сервер недоступен (HTTP ${HTTP_CODE}). Запустите: docker compose up -d"
    exit 1
fi
echo ""

# --- 2. Upload CSV locations (Mordovia) ---
echo "--- Шаг 2: Загрузка локаций Мордовии (CSV) ---"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/locations/upload" \
    -F "file=@${DATA_DIR}/locations_mordovia.csv" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "201" ]; then
    TOTAL=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['total_processed'])" 2>/dev/null || echo "?")
    CREATED=$(echo "$BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['created']))" 2>/dev/null || echo "?")
    info "Загружено ${CREATED}/${TOTAL} локаций Мордовии"
else
    fail "Ошибка загрузки CSV (HTTP ${HTTP_CODE})"
    echo "$BODY" | head -5
fi
echo ""

# --- 3. Verify locations ---
echo "--- Шаг 3: Проверка загруженных локаций ---"
LOC_COUNT=$(curl -s "${BASE_URL}/api/v1/locations/" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$LOC_COUNT" -gt 0 ] 2>/dev/null; then
    info "В базе ${LOC_COUNT} локаций"
else
    warn "Не удалось получить количество локаций"
fi
echo ""

# --- 4. Run optimization (Qwen, 4 points) ---
echo "--- Шаг 4: Тестовая оптимизация Qwen (4 точки) ---"
REQUEST=$(python3 -c "
import json
with open('${DATA_DIR}/test_optimize_requests.json') as f:
    data = json.load(f)
print(json.dumps(data['requests'][1]['body']))
" 2>/dev/null)

if [ -n "$REQUEST" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/qwen/optimize" \
        -H "Content-Type: application/json" \
        -d "$REQUEST" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    if [ "$HTTP_CODE" = "200" ]; then
        info "Qwen оптимизация: OK"
    else
        warn "Qwen оптимизация: HTTP ${HTTP_CODE} (модель может быть не загружена)"
    fi
else
    warn "Не удалось прочитать тестовый запрос"
fi
echo ""

# --- 5. Run optimization (Llama, 2 points) ---
echo "--- Шаг 5: Тестовая оптимизация Llama (2 точки) ---"
REQUEST=$(python3 -c "
import json
with open('${DATA_DIR}/test_optimize_requests.json') as f:
    data = json.load(f)
print(json.dumps(data['requests'][0]['body']))
" 2>/dev/null)

if [ -n "$REQUEST" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/llama/optimize" \
        -H "Content-Type: application/json" \
        -d "$REQUEST" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    if [ "$HTTP_CODE" = "200" ]; then
        info "Llama оптимизация: OK"
    else
        warn "Llama оптимизация: HTTP ${HTTP_CODE} (модель может быть не загружена)"
    fi
else
    warn "Не удалось прочитать тестовый запрос"
fi
echo ""

# --- 6. Run benchmark ---
echo "--- Шаг 6: Запуск бенчмарка ---"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/benchmark/run?iterations=2&use_mock=false" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
    info "Бенчмарк запущен"
else
    warn "Бенчмарк: HTTP ${HTTP_CODE}"
fi
echo ""

# --- Summary ---
echo "========================================"
echo "  Итог"
echo "========================================"
echo "  Локаций в БД: ${LOC_COUNT}"
echo "  Swagger UI:   ${BASE_URL}/docs"
echo "  Frontend:     http://${HOST}"
echo "========================================"

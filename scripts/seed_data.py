#!/usr/bin/env python3
"""seed_data.py — Загрузка тестовых данных в T2 API.

Использование:
    python3 scripts/seed_data.py [--host localhost] [--port 8000]
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"


def api(base: str, method: str, path: str,
        json_data: dict | None = None,
        file_path: Path | None = None,
        file_field: str = "file") -> tuple[int, dict | list | str]:
    """Make an API request. Returns (status_code, response_body)."""
    url = f"{base}{path}"

    if file_path is not None:
        import mimetypes
        boundary = "----SeedDataBoundary"
        content_type = (
            mimetypes.guess_type(str(file_path))[0]
            or "application/octet-stream"
        )
        file_data = file_path.read_bytes()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    elif json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = Request(url, method=method)

    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except URLError as e:
        if hasattr(e, "code"):
            raw = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
            try:
                return e.code, json.loads(raw)
            except (json.JSONDecodeError, AttributeError):
                return e.code, raw
        raise


def main():
    parser = argparse.ArgumentParser(description="T2 Seed Data Loader")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    args = parser.parse_args()

    base = f"http://{args.host}:{args.port}"
    print(f"{'=' * 40}")
    print(f"  T2 Seed Data Script")
    print(f"  Target: {base}")
    print(f"{'=' * 40}\n")

    # 1. Health check
    print("--- Шаг 1: Проверка здоровья сервера ---")
    try:
        code, body = api(base, "GET", "/health")
        if code == 200:
            print(f"  [OK] Сервер доступен")
        else:
            print(f"  [FAIL] Сервер вернул HTTP {code}")
            sys.exit(1)
    except Exception as e:
        print(f"  [FAIL] Сервер недоступен: {e}")
        print("  Запустите: docker compose up -d")
        sys.exit(1)
    print()

    # 2. Upload CSV
    print("--- Шаг 2: Загрузка локаций Мордовии (CSV) ---")
    csv_path = DATA_DIR / "locations_mordovia.csv"
    if not csv_path.exists():
        print(f"  [FAIL] Файл не найден: {csv_path}")
        sys.exit(1)

    code, body = api(base, "POST", "/api/v1/locations/upload",
                     file_path=csv_path)
    if code == 201:
        total = body.get("total_processed", "?")
        created = len(body.get("created", []))
        errors = body.get("errors", [])
        print(f"  [OK] Загружено {created}/{total} локаций")
        if errors:
            print(f"  [WARN] Ошибки: {len(errors)}")
            for err in errors[:3]:
                print(f"    Row {err.get('row')}: {err.get('error', '')[:80]}")
    else:
        print(f"  [FAIL] HTTP {code}")
    print()

    # 3. Verify
    print("--- Шаг 3: Проверка загруженных локаций ---")
    code, body = api(base, "GET", "/api/v1/locations/")
    loc_count = len(body) if isinstance(body, list) else 0
    print(f"  [OK] В базе {loc_count} локаций")
    print()

    # 4. Qwen optimization (4 points)
    print("--- Шаг 4: Тестовая оптимизация Qwen (4 точки) ---")
    requests_file = DATA_DIR / "test_optimize_requests.json"
    with open(requests_file) as f:
        test_requests = json.load(f)["requests"]

    try:
        code, body = api(base, "POST", "/api/v1/qwen/optimize",
                         json_data=test_requests[1]["body"])
        if code == 200:
            print("  [OK] Qwen оптимизация завершена")
        else:
            print(f"  [WARN] Qwen: HTTP {code}")
    except Exception as e:
        print(f"  [WARN] Qwen недоступен: {e}")
    print()

    # 5. Llama optimization (2 points)
    print("--- Шаг 5: Тестовая оптимизация Llama (2 точки) ---")
    try:
        code, body = api(base, "POST", "/api/v1/llama/optimize",
                         json_data=test_requests[0]["body"])
        if code == 200:
            print("  [OK] Llama оптимизация завершена")
        else:
            print(f"  [WARN] Llama: HTTP {code}")
    except Exception as e:
        print(f"  [WARN] Llama недоступен: {e}")
    print()

    # 6. Benchmark
    print("--- Шаг 6: Запуск бенчмарка ---")
    try:
        code, body = api(base, "POST",
                         "/api/v1/benchmark/run?iterations=2&use_mock=false")
        if code in (200, 202):
            print("  [OK] Бенчмарк запущен")
        else:
            print(f"  [WARN] Бенчмарк: HTTP {code}")
    except Exception as e:
        print(f"  [WARN] Бенчмарк недоступен: {e}")
    print()

    # Summary
    print(f"{'=' * 40}")
    print(f"  Итог")
    print(f"{'=' * 40}")
    print(f"  Локаций в БД: {loc_count}")
    print(f"  Swagger UI:   {base}/docs")
    print(f"  Frontend:     http://{args.host}")
    print(f"{'=' * 40}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Генератор PDF-отчёта для T2 Project.

Использование:
    python docs/MVP/generate_project_report.py

Создаёт: docs/MVP/T2_Project_Report_v1.2.0.pdf

Зависимости: fpdf2  (pip install fpdf2)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# ── Попытка импортировать fpdf2 ───────────────────────────────────────────────
try:
    from fpdf import FPDF
except ImportError:
    print("Ошибка: fpdf2 не установлен. Выполните: pip install fpdf2")
    sys.exit(1)

DOCS_DIR = Path(__file__).parent
PROJECT_ROOT = DOCS_DIR.parent.parent
VERSION = "1.2.0"
REPORT_DATE = "10 марта 2026"
OUTPUT_FILE = DOCS_DIR / f"T2_Project_Report_v{VERSION}.pdf"


def read_md(path: Path) -> str:
    """Читает Markdown-файл и возвращает текст без Markdown-разметки."""
    if not path.exists():
        return f"[Файл не найден: {path}]"
    text = path.read_text(encoding="utf-8")
    # Убираем базовую разметку
    lines = []
    for line in text.splitlines():
        # Убираем заголовки (#)
        stripped = line.lstrip("#").strip()
        # Убираем code fences
        if stripped.startswith("```"):
            continue
        lines.append(stripped)
    return "\n".join(lines)


class T2PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 100, 200)
        self.cell(0, 8, f"T2 Project Report v{VERSION}", align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 100, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"T2 Logistics AI Platform | {REPORT_DATE} | Стр. {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 100, 200)
        self.ln(4)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 220, 255)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)
        self.set_text_color(30, 30, 30)

    def body_text(self, text: str, max_chars_per_line: int = 1000):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        for line in text.splitlines():
            if not line.strip():
                self.ln(3)
                continue
            # Ограничиваем длину строки
            if len(line) > max_chars_per_line:
                line = line[:max_chars_per_line] + "…"
            # Фильтруем непечатаемые символы
            safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
            self.multi_cell(0, 5, safe_line)
        self.ln(2)

    def table_row(self, cells: list[str], widths: list[int], header: bool = False):
        if header:
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(30, 100, 200)
            self.set_text_color(255, 255, 255)
        else:
            self.set_font("Helvetica", "", 9)
            self.set_fill_color(240, 245, 255)
            self.set_text_color(40, 40, 40)
        for cell, w in zip(cells, widths):
            safe = str(cell).encode("latin-1", errors="replace").decode("latin-1")
            self.cell(w, 6, safe[:40], border=1, fill=True)
        self.ln()


def build_report():
    pdf = T2PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)

    # ── Титульная страница ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 100, 200)
    pdf.ln(30)
    pdf.cell(0, 12, "T2 Logistics AI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, f"Project Report v{VERSION}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, REPORT_DATE, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)

    # Краткое описание
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    description = (
        "AI-powered platform for route optimization and visit scheduling\n"
        "for Mordovia retail network sales representatives.\n"
        "Stack: FastAPI + PostgreSQL + Vue 3 + Qwen/Llama LLMs"
    )
    for line in description.splitlines():
        pdf.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

    # ── Секция 1: Обзор проекта ───────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("1. Project Overview")
    overview = (
        "T2 is a comprehensive logistics route optimization platform built for\n"
        "retail sales representatives in the Mordovia Republic.\n\n"
        "Key capabilities:\n"
        "- Monthly visit schedule generation (A/B/C/D priority categories)\n"
        "- AI-powered route optimization using local LLMs (Qwen 0.5B, Llama 1B)\n"
        "- Force majeure handling with automatic visit redistribution\n"
        "- Time tracking per visit (time_in / time_out)\n"
        "- Excel export/import (5 sheets including AuditLog)\n"
        "- Visit state machine with validated status transitions\n"
        "- AuditLog for all critical operations\n\n"
        "Team: 3 developers + 1 TL/PM | Duration: 5 weeks | Methodology: Agile Lite"
    )
    pdf.body_text(overview)

    # ── Секция 2: Статус реализации ───────────────────────────────────────────
    pdf.section_title("2. Implementation Status")

    status_table = [
        ("Component", "Status", "Details"),
        ("Backend API (FastAPI)", "DONE", "33+ endpoints, async SQLAlchemy"),
        ("Frontend (Vue 3)", "DONE", "6 pages, TypeScript, Tailwind"),
        ("LLM Integration", "DONE", "Qwen 0.5B + Llama 1B, GGUF"),
        ("Database (PostgreSQL)", "DONE", "8 tables, 3 migrations, ORM"),
        ("SchedulePlanner", "DONE", "A/B/C/D categories, 14 TT/day max"),
        ("Force Majeure", "DONE", "Auto-redistribution"),
        ("State Machine", "DONE", "5-state visit FSM, 422 on invalid"),
        ("AuditLog", "DONE", "Table + 5th Excel sheet"),
        ("Health Check v2", "DONE", "disk_free_mb, visits_today, version"),
        ("Excel Export", "DONE", "5 sheets incl. AuditLog"),
        ("Tests", "DONE", "~189 frontend + 61+ backend"),
    ]
    widths = [60, 25, 95]
    for i, row in enumerate(status_table):
        pdf.table_row(list(row), widths, header=(i == 0))
    pdf.ln(4)

    # ── Секция 3: Версионная история ─────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("3. Version History")

    versions = [
        ("v1.0.0", "25 Feb 2026", "MVP: Route optimization, LLM integration, 4 UI pages"),
        ("v1.1.0", "27 Feb 2026", "Schedule mgmt, force majeure, Excel export/import, RepsView"),
        ("v1.2.0", "10 Mar 2026", "State machine, AuditLog, health v2, localStorage, 189 tests"),
    ]
    widths2 = [20, 28, 132]
    pdf.table_row(["Version", "Date", "Summary"], widths2, header=True)
    for row in versions:
        pdf.table_row(list(row), widths2)
    pdf.ln(4)

    pdf.section_title("v1.2.0 Highlights")
    highlights = (
        "- Visit Status Machine: planned->completed/skipped/cancelled/rescheduled\n"
        "  skipped->planned/cancelled | rescheduled->completed/skipped/cancelled\n"
        "  completed/cancelled: LOCKED (returns 422 on any transition attempt)\n\n"
        "- Schedule Duplicate Protection: POST /schedule/generate returns 409 if\n"
        "  planned visits already exist for the month. Use ?force=true to regenerate.\n\n"
        "- AuditLog: New table audit_log (migration 003) tracks:\n"
        "  visit_status_change | force_majeure_created | schedule_generated\n\n"
        "- Extended Health Check: disk_free_mb, visits_today, version fields added\n\n"
        "- GET /schedule/ now supports from_date / to_date query params\n\n"
        "- Frontend: requestId pattern prevents stale data in AnalyticsView\n"
        "- Frontend: localStorage persists model preference and month offset"
    )
    pdf.body_text(highlights)

    # ── Секция 4: API Overview ────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("4. API Overview")

    api_groups = [
        ("Optimization", [
            "POST /optimize - Route optimization (auto-fallback Qwen->Llama->Greedy)",
            "POST /optimize/variants - 3 route variants with LLM pros/cons",
            "POST /optimize/confirm - Save selected variant to DB",
        ]),
        ("Schedule", [
            "POST /schedule/generate?force= - Generate monthly plan (409 if exists)",
            "GET /schedule/?month=&from_date=&to_date= - Monthly plan with date filter",
            "GET /schedule/daily?date= - All rep routes for specific day",
            "PATCH /schedule/{id} - Update visit status (state machine validated)",
        ]),
        ("Sales Reps", [
            "GET/POST /reps - List / Create reps",
            "PATCH /reps/{id} - Update (returns warning if sick/vacation)",
            "DELETE /reps/{id} - Delete rep",
        ]),
        ("Force Majeure", [
            "POST /force_majeure - Register event + auto-redistribute visits",
            "GET /force_majeure?month= - History",
        ]),
        ("Export / Import", [
            "GET /export/schedule?month= - Excel with 5 sheets (incl. AuditLog)",
            "POST /import/schedule - Upload filled Excel, update statuses",
        ]),
        ("System", [
            "GET /health - Health check with disk_free_mb, visits_today, version",
            "GET /api/v1/health - Same for frontend",
            "GET /insights?month= - Coverage by category and district",
        ]),
    ]

    for group_name, endpoints in api_groups:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 100, 200)
        pdf.cell(0, 7, group_name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        for ep in endpoints:
            safe = ep.encode("latin-1", errors="replace").decode("latin-1")
            pdf.cell(5)
            pdf.multi_cell(0, 5, f"- {safe}")
        pdf.ln(2)

    # ── Секция 5: Метрики тестирования ───────────────────────────────────────
    pdf.add_page()
    pdf.section_title("5. Test Metrics")

    test_table = [
        ("Suite", "Count", "Framework", "Status"),
        ("Frontend views", "~50", "Vitest", "PASS"),
        ("Frontend components", "~100", "Vitest", "PASS"),
        ("Frontend services", "~39", "Vitest", "PASS"),
        ("ScheduleView.spec", "8", "Vitest", "NEW v1.2"),
        ("RepsView.spec", "7", "Vitest", "NEW v1.2"),
        ("Backend routes", "40+", "pytest", "PASS"),
        ("Backend services", "21+", "pytest", "PASS"),
        ("TOTAL", "~189 FE + 61 BE", "—", "ALL GREEN"),
    ]
    widths3 = [70, 30, 40, 40]
    for i, row in enumerate(test_table):
        pdf.table_row(list(row), widths3, header=(i == 0))
    pdf.ln(4)

    pdf.section_title("Quality Gates")
    quality = (
        "- TypeScript: 0 errors\n"
        "- ESLint: 0 warnings in CI\n"
        "- Backend: All 422/409 edge cases covered\n"
        "- State machine: all valid/invalid transitions tested\n"
        "- Frontend: stale-request protection (requestId pattern) tested"
    )
    pdf.body_text(quality)

    # ── Финальная страница ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("6. System Requirements")

    req_table = [
        ("Resource", "Minimum", "Recommended"),
        ("RAM", "4 GB", "8 GB"),
        ("Disk", "5 GB free", "10 GB free"),
        ("CPU", "2 cores", "4 cores"),
        ("OS", "Ubuntu 22.04+", "Ubuntu 24.04 LTS"),
        ("Python", "3.11+", "3.12"),
        ("Node.js", "18+", "20 LTS"),
    ]
    widths4 = [50, 60, 70]
    for i, row in enumerate(req_table):
        pdf.table_row(list(row), widths4, header=(i == 0))
    pdf.ln(6)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 6, f"Generated: {generated_at} | T2 Project v{VERSION}", align="C")

    # ── Сохраняем PDF ─────────────────────────────────────────────────────────
    pdf.output(str(OUTPUT_FILE))
    print(f"PDF создан: {OUTPUT_FILE}")
    print(f"Размер: {OUTPUT_FILE.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build_report()

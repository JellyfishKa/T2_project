"""
Unit-тесты для выбора модели (ML-6): select_best_model и get_model_recommendation.
Модели: только qwen (primary) и llama (fallback).
"""

import pytest
from src.services.model_selector import (
    select_best_model,
    get_model_recommendation,
    MODEL_QWEN,
    MODEL_LLAMA,
    CONSTRAINT_URGENT,
    CONSTRAINT_QUALITY,
    CONSTRAINT_RELIABILITY,
)


class TestSelectBestModel:
    """Проверка логики select_best_model: всегда primary = qwen."""

    def test_always_qwen_for_any_input(self):
        """Для любых num_locations и time_constraint селектор возвращает qwen."""
        for n in (0, 1, 10, 50, 150):
            for c in (None, CONSTRAINT_URGENT, CONSTRAINT_QUALITY, CONSTRAINT_RELIABILITY):
                assert select_best_model(n, c) == MODEL_QWEN


class TestGetModelRecommendation:
    """Проверка структуры ответа для API (опциональное поле recommendation)."""

    def test_returns_model_and_reason(self):
        """В ответе есть model и reason; модель — всегда qwen, reason упоминает fallback Llama."""
        r = get_model_recommendation(50, CONSTRAINT_QUALITY)
        assert r["model"] == MODEL_QWEN
        assert "reason" in r and len(r["reason"]) > 0
        assert "Qwen" in r["reason"]
        assert "Llama" in r["reason"] or "fallback" in r["reason"].lower()

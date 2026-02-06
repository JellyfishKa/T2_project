import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Create a simplified test that avoids importing the full modules
# We'll mock at a higher level to avoid dependency issues

class TestIntegration:

    def test_api_response_structure_consistency(self):
        """TC-INT-004: Тест согласованности структуры ответа API."""
        
        # Import the schemas directly without importing the whole route chain
        from src.models.schemas import Location, Route
        
        # Create a sample route response
        locations_data = [{
            "ID": "loc1",
            "name": "Store A",
            "address": "123 Main St",
            "lat": 55.7558,
            "lon": 37.6173,
            "time_window_start": "09:00",
            "time_window_end": "18:00",
            "priority": "high"
        }]

        route = Route(
            ID="test_route",
            name="Test Route",
            locations=locations_data,
            total_distance_km=12.5,
            total_time_hours=2.0,
            total_cost_rub=2000.0,
            model_used="TestModel",
            created_at=datetime.now()
        )

        # Verify all required fields are present
        assert hasattr(route, 'ID')
        assert hasattr(route, 'name')
        assert hasattr(route, 'locations')
        assert hasattr(route, 'total_distance_km')
        assert hasattr(route, 'total_time_hours')
        assert hasattr(route, 'total_cost_rub')
        assert hasattr(route, 'model_used')
        assert hasattr(route, 'created_at')

        # Verify types
        assert isinstance(route.ID, str)
        assert isinstance(route.total_distance_km, float)
        assert isinstance(route.total_time_hours, float)
        assert isinstance(route.total_cost_rub, float)
        assert isinstance(route.model_used, str)

        # Verify values
        assert route.ID == "test_route"
        assert route.total_distance_km == 12.5
        assert route.model_used == "TestModel"
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock dependencies for the backend components
mock_fastapi = MagicMock()
mock_pytest_asyncio = MagicMock()
mock_requests = MagicMock()

# Add our mock modules to sys.modules to prevent import errors
sys.modules['fastapi'] = mock_fastapi
sys.modules['pytest_asyncio'] = mock_pytest_asyncio
sys.modules['requests'] = mock_requests

# Also mock other dependencies that might be imported
mock_uvorn = MagicMock()
mock_src_models_qwen_client = MagicMock()
mock_src_models_schemas = MagicMock()

sys.modules['uvicorn'] = mock_uvorn
sys.modules['src.models.qwen_client'] = mock_src_models_qwen_client
sys.modules['src.models.schemas'] = mock_src_models_schemas

# Import the route after mocking dependencies
from src.routes.qwen import router, optimize_route
from src.models.schemas import Location, Route

class TestIntegration:

    @pytest.mark.asyncio
    async def test_frontend_backend_integration_optimization(self):
        """TC-INT-001: Тест интеграции фронтенд-бэкенд для оптимизации маршрута."""
        
        # Create mock locations similar to what would come from the frontend
        locations_data = [
            {
                "ID": "loc1",
                "name": "Store A",
                "address": "123 Main St",
                "lat": 55.7558,
                "lon": 37.6173,
                "time_window_start": "09:00",
                "time_window_end": "18:00",
                "priority": "high"
            },
            {
                "ID": "loc2", 
                "name": "Store B",
                "address": "456 Oak Ave",
                "lat": 55.7557,
                "lon": 37.6174,
                "time_window_start": "10:00",
                "time_window_end": "17:00",
                "priority": "medium"
            }
        ]
        
        # Convert to Pydantic models
        locations = [Location(**loc) for loc in locations_data]
        
        # Mock the QwenClient and its generate_route method
        with patch('src.routes.qwen.QwenClient') as MockQwenClient:
            mock_client_instance = AsyncMock()
            MockQwenClient.return_value = mock_client_instance
            
            # Mock the generate_route method to return a sample route
            mock_route_result = Route(
                ID="route1",
                name="Optimized Route",
                locations=locations_data,
                total_distance_km=15.5,
                total_time_hours=2.5,
                total_cost_rub=2500.0,
                model_used="Qwen",
                created_at="2023-01-01T00:00:00"
            )
            mock_client_instance.generate_route = AsyncMock(return_value=mock_route_result)
            
            # Call the endpoint function directly
            result = await optimize_route(locations=locations, constraints={})
            
            # Verify the result
            assert result.ID == "route1"
            assert result.total_distance_km == 15.5
            assert result.total_time_hours == 2.5
            assert result.model_used == "Qwen"
            
            # Verify that the client's generate_route method was called with correct params
            mock_client_instance.generate_route.assert_called_once_with(locations, {})

    @pytest.mark.asyncio
    async def test_frontend_backend_integration_error_handling(self):
        """TC-INT-002: Тест обработки ошибок в интеграции фронтенд-бэкенд."""
        
        # Create mock locations
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
        locations = [Location(**loc) for loc in locations_data]
        
        # Mock the QwenClient to raise an exception
        with patch('src.routes.qwen.QwenClient') as MockQwenClient:
            mock_client_instance = AsyncMock()
            MockQwenClient.return_value = mock_client_instance
            
            # Make the generate_route method raise an exception
            mock_client_instance.generate_route.side_effect = Exception("Model unavailable")
            
            # Expect an HTTPException to be raised
            with pytest.raises(Exception):
                await optimize_route(locations=locations, constraints={})

    @pytest.mark.asyncio
    async def test_multiple_llm_integration(self):
        """TC-INT-003: Тест интеграции с несколькими LLM моделями."""
        
        # Create mock locations
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
        locations = [Location(**loc) for loc in locations_data]
        
        # Test different model responses
        models_to_test = ["Qwen", "GigaChat", "Cotype", "T-Pro"]
        
        for model_name in models_to_test:
            with patch('src.routes.qwen.QwenClient') as MockQwenClient:
                mock_client_instance = AsyncMock()
                MockQwenClient.return_value = mock_client_instance
                
                # Mock the generate_route method to return a route with specific model
                mock_route_result = Route(
                    ID=f"route_{model_name.lower()}",
                    name=f"Route via {model_name}",
                    locations=locations_data,
                    total_distance_km=10.0 + len(model_name),
                    total_time_hours=1.0 + len(model_name)/10,
                    total_cost_rub=1000.0 + len(model_name)*100,
                    model_used=model_name,
                    created_at="2023-01-01T00:00:00"
                )
                mock_client_instance.generate_route = AsyncMock(return_value=mock_route_result)
                
                # Call the endpoint
                result = await optimize_route(locations=locations, constraints={})
                
                # Verify the result has the correct model
                assert result.model_used == model_name
                assert result.ID == f"route_{model_name.lower()}"

    def test_api_response_structure_consistency(self):
        """TC-INT-004: Тест согласованности структуры ответа API."""
        
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
            created_at="2023-01-01T00:00:00"
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

    @pytest.mark.asyncio
    async def test_constraint_handling_in_integration(self):
        """TC-INT-005: Тест обработки ограничений в интеграции."""
        
        # Create mock locations
        locations_data = [
            {
                "ID": "loc1",
                "name": "Store A",
                "address": "123 Main St",
                "lat": 55.7558,
                "lon": 37.6173,
                "time_window_start": "09:00",
                "time_window_end": "18:00",
                "priority": "high"
            }
        ]
        locations = [Location(**loc) for loc in locations_data]
        
        # Test with various constraint types
        test_constraints = [
            {},  # No constraints
            {"max_distance_km": 20.0},  # Distance constraint
            {"vehicle_capacity": 5, "time_limit_hours": 8.0},  # Multiple constraints
            {"forbidden_roads": ["road1", "road2"]}  # Road restrictions
        ]
        
        for i, constraints in enumerate(test_constraints):
            with patch('src.routes.qwen.QwenClient') as MockQwenClient:
                mock_client_instance = AsyncMock()
                MockQwenClient.return_value = mock_client_instance
                
                # Mock response
                mock_route_result = Route(
                    ID=f"route_constraint_{i}",
                    name="Constraint Test Route",
                    locations=locations_data,
                    total_distance_km=10.0 + i,
                    total_time_hours=1.0 + i/10,
                    total_cost_rub=1000.0 + i*100,
                    model_used="Qwen",
                    created_at="2023-01-01T00:00:00"
                )
                mock_client_instance.generate_route = AsyncMock(return_value=mock_route_result)
                
                # Call with constraints
                result = await optimize_route(locations=locations, constraints=constraints)
                
                # Verify the constraints were passed to the model
                mock_client_instance.generate_route.assert_called_with(locations, constraints)
                assert result.ID == f"route_constraint_{i}"
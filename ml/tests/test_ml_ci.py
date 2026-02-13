import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock dependencies before importing test_models
# We need to keep references to these mocks to configure them in tests
mock_transformers = MagicMock()
mock_torch = MagicMock()
mock_psutil = MagicMock()

sys.modules['transformers'] = mock_transformers
sys.modules['torch'] = mock_torch
sys.modules['psutil'] = mock_psutil

# Bypass Windows-specific stdout reconfiguration and FileHandler creation
with patch('sys.platform', 'linux'), \
     patch('logging.FileHandler'):
    # Import the module as an alias to avoid pytest collecting 'test_qwen' etc. as standalone tests
    import ml.test_models as tm

class TestModelsCI:

    def setup_method(self):
        # Reset mocks before each test
        mock_transformers.reset_mock()
        mock_torch.reset_mock()

    def test_qwen_success(self):
        """TC-ML-001: Тест Qwen возвращает успех (Mock)."""
        # Setup AutoTokenizer mock
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        # Setup AutoConfig mock
        mock_config_instance = MagicMock()
        mock_config_instance.num_parameters.return_value = 1000000
        mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance

        success, info = tm.test_qwen()

        assert success is True
        assert info['status'] == 'available'
        assert info['model_name'] == "Qwen/Qwen2-0.5B-Instruct"

    def test_llama_success(self):
        """TC-ML-002: Тест Llama возвращает успех (Mock)."""
        # Simulate CUDA available for heavier path
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "Mock GPU"

        # Setup Tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_tokenizer_instance.return_value.to.return_value = {}
        mock_tokenizer_instance.decode.return_value = "mock response"
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        # Setup Config
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        # Setup Model for GPU loading
        mock_model_instance = MagicMock()
        mock_model_instance.device = 'cuda'
        mock_model_instance.generate.return_value = [b"mock output"]
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model_instance

        success, info = tm.test_llama()

        assert success is True
        assert info['model_name'] == "meta-llama/Llama-3.2-1B-Instruct"

    def test_tpro_success(self):
        """TC-ML-003: Тест T-Pro возвращает успех (Mock)."""
        # Setup Tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 3000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        # Setup Config
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        success, info = tm.test_tpro()

        assert success is True
        assert info['model_name'] == "t-tech/T-pro-it-1.0"

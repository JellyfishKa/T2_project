import sys
import pytest
from unittest.mock import MagicMock, patch

mock_transformers = MagicMock()
mock_torch = MagicMock()
mock_psutil = MagicMock()

sys.modules['transformers'] = mock_transformers
sys.modules['torch'] = mock_torch
sys.modules['psutil'] = mock_psutil

with patch('sys.platform', 'linux'), \
     patch('logging.FileHandler'):
<<<<<<< Updated upstream
    # Import the module as an alias to avoid pytest collecting 'test_gigachat' etc. as standalone tests
=======
>>>>>>> Stashed changes
    import ml.test_models as tm


class TestModelsCI:
    
    def setup_method(self):
        mock_transformers.reset_mock()
        mock_torch.reset_mock()
<<<<<<< Updated upstream
        
    def test_gigachat_success(self):
        """TC-ML-001: Тест GigaChat возвращает успех (Mock)."""
        # Configure mocks
        
        # Setup AutoTokenizer mock
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Setup AutoConfig mock
=======
        mock_transformers.AutoTokenizer.from_pretrained.side_effect = None
        mock_transformers.AutoConfig.from_pretrained.side_effect = None
        mock_transformers.AutoModelForCausalLM.from_pretrained.side_effect = None

    def test_qwen_success(self):
        """TC-ML-001: Тест Qwen возвращает успех (Mock)."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

>>>>>>> Stashed changes
        mock_config_instance = MagicMock()
        mock_config_instance.num_parameters.return_value = 1000000
        mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance
        
        success, info = tm.test_gigachat()
        
        assert success is True
        assert info['status'] == 'available'
        assert info['model_name'] == "ai-sage/GigaChat3-10B-A1.8B"

<<<<<<< Updated upstream
    def test_cotype_success(self):
        """TC-ML-002: Тест Cotype возвращает успех (Mock)."""
        # Simulate CUDA available for heavier path
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "Mock GPU"
        
        # Setup Tokenizer
=======
    def test_llama_success(self):
        """TC-ML-002: Тест Llama возвращает успех (Mock)."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "Mock GPU"

>>>>>>> Stashed changes
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_tokenizer_instance.return_value.to.return_value = {} # inputs.to(device)
        mock_tokenizer_instance.decode.return_value = "mock response"
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
<<<<<<< Updated upstream
        
        # Setup Config
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()
        
        # Setup Model for GPU loading
=======

        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

>>>>>>> Stashed changes
        mock_model_instance = MagicMock()
        mock_model_instance.device = 'cuda'
        mock_model_instance.generate.return_value = [b"mock output"]
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model_instance
        
        success, info = tm.test_cotype()
        
        assert success is True
        assert info['model_name'] == "MTSAIR/Cotype-Nano"

    def test_qwen_cpu_mode(self):
        """TC-ML-003: Тест Qwen в CPU режиме."""
        mock_torch.cuda.is_available.return_value = False

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
<<<<<<< Updated upstream
        
        # Setup Config
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()
        
        success, info = tm.test_tpro()
        
=======

        mock_config_instance = MagicMock()
        mock_config_instance.num_parameters.return_value = 1000000
        mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance

        success, info = tm.test_qwen()

>>>>>>> Stashed changes
        assert success is True
        assert info['status'] == 'available'

    def test_llama_cpu_mode(self):
        """TC-ML-004: Тест Llama в CPU режиме."""
        mock_torch.cuda.is_available.return_value = False

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        success, info = tm.test_llama()

        assert success is True
        assert info['model_name'] == "meta-llama/Llama-3.2-1B-Instruct"


class TestFallbackChain:
    """Тесты fallback-цепочки Qwen -> Llama -> Greedy (Неделя 3)."""

    def test_two_models_only(self):
        """TC-FB3-004: Проверяем, что только Qwen и Llama тестируются."""
        results = {}
        
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        qwen_success, qwen_info = tm.test_qwen()
        results["qwen"] = {"success": qwen_success, "info": qwen_info}

        llama_success, llama_info = tm.test_llama()
        results["llama"] = {"success": llama_success, "info": llama_info}

        assert "qwen" in results
        assert "llama" in results
        assert "tpro" not in results, "T-Pro должен быть удалён из тестов"
        assert results["qwen"]["success"] is True
        assert results["llama"]["success"] is True

    def test_system_info_collection(self):
        """TC-ML-005: Тест структуры информации о системе."""
        sys_info = tm.get_system_info()

        assert 'cpu_count' in sys_info
        assert 'ram_total_gb' in sys_info
        assert 'cuda_available' in sys_info
        assert isinstance(sys_info['cpu_count'], int)
        assert isinstance(sys_info['ram_total_gb'], float)
        assert isinstance(sys_info['cuda_available'], bool)
        if sys_info['cuda_available']:
            assert 'cuda_device_count' in sys_info
            assert 'cuda_device_name' in sys_info
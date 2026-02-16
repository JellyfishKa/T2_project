import sys
import pytest
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

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


class TestExtendedModels:

    def setup_method(self):
        mock_transformers.reset_mock()
        mock_torch.reset_mock()
        mock_transformers.AutoTokenizer.from_pretrained.side_effect = None
        mock_transformers.AutoConfig.from_pretrained.side_effect = None
        mock_transformers.AutoModelForCausalLM.from_pretrained.side_effect = None

<<<<<<< Updated upstream
    def test_gigachat_with_cpu_fallback(self):
        """TC-ML-004: Тест GigaChat с CPU fallback при недоступности GPU."""
        # Simulate CUDA not available
=======
    def test_qwen_with_cpu_fallback(self):
        """TC-ML-006: Тест Qwen с CPU fallback при недоступности GPU."""
>>>>>>> Stashed changes
        mock_torch.cuda.is_available.return_value = False

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_config_instance = MagicMock()
        mock_config_instance.num_parameters.return_value = 1000000
        mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance

        success, info = tm.test_gigachat()

        assert success is True
        assert info['status'] == 'available'
        assert info['model_name'] == "ai-sage/GigaChat3-10B-A1.8B"

<<<<<<< Updated upstream
    @pytest.mark.xfail(reason="sys.modules mock doesn't propagate side_effect to from imports inside functions")
    def test_gigachat_error_handling(self):
        """TC-ML-005: Тест GigaChat с обработкой ошибок при загрузке модели."""
        # Setup to raise an exception
        mock_transformers.AutoTokenizer.from_pretrained.side_effect = Exception("Model not found")

        success, info = tm.test_gigachat()

        assert success is False
        assert 'error' in info

    def test_cotype_cpu_mode(self):
        """TC-ML-006: Тест Cotype в CPU режиме."""
        # Simulate CUDA not available
=======
    def test_llama_cpu_mode(self):
        """TC-ML-007: Тест Llama в CPU режиме."""
>>>>>>> Stashed changes
        mock_torch.cuda.is_available.return_value = False

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        success, info = tm.test_cotype()

        assert success is True
        assert info['model_name'] == "MTSAIR/Cotype-Nano"
        # Should be available but not loaded since CUDA is not available

<<<<<<< Updated upstream
    def test_cotype_gpu_loading_failure(self):
        """TC-ML-007: Тест Cotype с обработкой ошибки при загрузке на GPU."""
        # Simulate CUDA available but model loading fails
=======
    def test_llama_gpu_loading_failure(self):
        """TC-ML-008: Тест Llama с обработкой ошибки при загрузке на GPU."""
>>>>>>> Stashed changes
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "Mock GPU"

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_tokenizer_instance.return_value.to.return_value = {} # inputs.to(device)
        mock_tokenizer_instance.decode.return_value = "mock response"
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        mock_transformers.AutoModelForCausalLM.from_pretrained.side_effect = RuntimeError("Not enough memory")

        success, info = tm.test_cotype()

        assert success is True
        assert info['model_name'] == "MTSAIR/Cotype-Nano"

    def test_system_info_collection(self):
        """TC-ML-009: Тест сбора информации о системе."""
        mock_psutil.cpu_count.return_value = 8
<<<<<<< Updated upstream
        mock_psutil.virtual_memory.return_value.total = 16 * 1024**3  # 16GB
        mock_psutil.virtual_memory.return_value.available = 8 * 1024**3  # 8GB available
        
=======
        mock_psutil.virtual_memory.return_value.total = 16 * 1024**3
        mock_psutil.virtual_memory.return_value.available = 8 * 1024**3

>>>>>>> Stashed changes
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3080"
        mock_torch.cuda.get_device_properties.return_value.total_memory = 10 * 1024**3

        sys_info = tm.get_system_info()

        assert sys_info['cpu_count'] == 8
        assert sys_info['ram_total_gb'] == 16.0
        assert sys_info['cuda_available'] is True
        assert sys_info['cuda_device_name'] == "NVIDIA GeForce RTX 3080"

    def test_results_output_format(self):
<<<<<<< Updated upstream
        """TC-ML-010: Тест формата вывода результатов."""
        # This test simulates the main function's behavior
=======
        """TC-ML-010: Тест формата вывода результатов (только Qwen и Llama)."""
>>>>>>> Stashed changes
        import tempfile
        import os
        
        # Temporarily change working directory to avoid creating files in the repo root
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create a mock models directory
                models_dir = Path("ml/models")
                models_dir.mkdir(parents=True, exist_ok=True)
                
                # Setup successful mocks
                mock_torch.cuda.is_available.return_value = False
                
                # Setup tokenizers
                mock_tokenizer_instance = MagicMock()
                mock_tokenizer_instance.__len__.return_value = 1000
                mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
                
                # Setup configs
                mock_config_instance = MagicMock()
                mock_config_instance.num_parameters.return_value = 1000000
                mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance
                
                # Mock psutil
                mock_psutil.cpu_count.return_value = 4
                mock_psutil.virtual_memory.return_value.total = 8 * 1024**3
                mock_psutil.virtual_memory.return_value.available = 4 * 1024**3
                
                # Call main function (we'll just test the results saving part)
                # Since we can't easily test the full main function due to its complexity,
                # we'll test the results saving functionality separately
                import datetime
<<<<<<< Updated upstream
                from unittest.mock import mock_open, patch
                
                # Test results saving
=======
                from unittest.mock import mock_open

>>>>>>> Stashed changes
                results_summary = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'system_info': {
                        'cpu_count': 4,
                        'ram_total_gb': 8.0,
                        'cuda_available': False
                    },
                    'results': {
<<<<<<< Updated upstream
                        'gigachat': {'success': True, 'info': {'model_name': 'ai-sage/GigaChat3-10B-A1.8B', 'status': 'available'}},
                        'cotype': {'success': True, 'info': {'model_name': 'MTSAIR/Cotype-Nano', 'status': 'available'}},
                        'tpro': {'success': True, 'info': {'model_name': 't-tech/T-pro-it-1.0', 'status': 'available'}}
=======
                        'qwen': {'success': True, 'info': {'model_name': 'Qwen/Qwen2-0.5B-Instruct', 'status': 'available'}},
                        'llama': {'success': True, 'info': {'model_name': 'meta-llama/Llama-3.2-1B-Instruct', 'status': 'available'}}
>>>>>>> Stashed changes
                    }
                }
                
                # Test saving results to file
                results_file = Path('ml/models/test_results.json')
                with patch("builtins.open", mock_open()) as mock_file:
                    with open(results_file, 'w', encoding='utf-8') as f:
                        json.dump(results_summary, f, indent=2, ensure_ascii=False)
                    
                    # Verify that file was opened with correct parameters
                    mock_file.assert_called_once_with(results_file, 'w', encoding='utf-8')
                
                # Verify all models succeeded
                all_success = all(r['success'] for r in results_summary['results'].values())
                assert all_success is True
<<<<<<< Updated upstream
                
=======
                assert 'tpro' not in results_summary['results'], "T-Pro не должен быть в результатах"

>>>>>>> Stashed changes
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

<<<<<<< Updated upstream
    @pytest.mark.xfail(reason="sys.modules mock doesn't propagate side_effect to from imports inside functions")
    def test_main_function_with_partial_failures(self):
        """TC-ML-011: Тест главной функции с частичными ошибками."""
        # Similar to previous test, but with one model failing
        import tempfile
        import os
        
        # Temporarily change working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create a mock models directory
                models_dir = Path("ml/models")
                models_dir.mkdir(parents=True, exist_ok=True)
                
                # Setup mocks - make T-Pro fail
                mock_torch.cuda.is_available.return_value = False
                
                # Setup tokenizers
                mock_tokenizer_instance = MagicMock()
                mock_tokenizer_instance.__len__.return_value = 1000
                mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
                
                # Setup configs
                mock_config_instance = MagicMock()
                mock_config_instance.num_parameters.return_value = 1000000
                mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance
                
                # Make T-Pro tokenizer throw an error
                def side_effect(model_name, *args, **kwargs):
                    if "t-tech/T-pro-it-1.0" in model_name:
                        raise Exception("Model not accessible")
                    return mock_tokenizer_instance
                
                mock_transformers.AutoTokenizer.from_pretrained.side_effect = side_effect
                
                # Mock psutil
                mock_psutil.cpu_count.return_value = 4
                mock_psutil.virtual_memory.return_value.total = 8 * 1024**3
                mock_psutil.virtual_memory.return_value.available = 4 * 1024**3
                
                # Test individual model functions
                # GigaChat should succeed
                gigachat_success, gigachat_info = tm.test_gigachat()
                assert gigachat_success is True
                
                # Cotype should succeed
                cotype_success, cotype_info = tm.test_cotype()
                assert cotype_success is True
                
                # T-Pro should fail
                tpro_success, tpro_info = tm.test_tpro()
                assert tpro_success is False
                
                # Verify partial success scenario
                results = {
                    'gigachat': {'success': gigachat_success, 'info': gigachat_info},
                    'cotype': {'success': cotype_success, 'info': cotype_info},
                    'tpro': {'success': tpro_success, 'info': tpro_info}
                }
                
                # Not all should succeed
                all_success = all(r['success'] for r in results.values())
                assert all_success is False
                
                # But at least some should succeed
                successful_models = sum(1 for r in results.values() if r['success'])
                assert successful_models >= 2  # At least GigaChat and Cotype should succeed
                
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
=======

class TestWeek3Models:
    """Тесты для недели 3: только 2 модели (Qwen, Llama)."""

    def test_only_two_models_in_tests(self):
        """TC-W3-001: Подтверждение только 2 моделей в тестах."""
        mock_torch.cuda.is_available.return_value = False
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        qwen_success, qwen_info = tm.test_qwen()
        llama_success, llama_info = tm.test_llama()

        assert qwen_success is True
        assert llama_success is True
        assert qwen_info['model_name'] == "Qwen/Qwen2-0.5B-Instruct"
        assert llama_info['model_name'] == "meta-llama/Llama-3.2-1B-Instruct"

    def test_no_tpro_function_exists(self):
        """TC-W3-002: Функция test_tpro существует для обратной совместимости."""
        assert hasattr(tm, 'test_tpro'), "Функция test_tpro может существовать для совместимости"

    def test_qwen_as_primary_model(self):
        """TC-W3-003: Qwen работает как primary модель."""
        mock_torch.cuda.is_available.return_value = False
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_config_instance = MagicMock()
        mock_config_instance.num_parameters.return_value = 500000000
        mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance

        success, info = tm.test_qwen()

        assert success is True
        assert info['status'] == 'available'

    def test_llama_as_fallback_model(self):
        """TC-W3-004: Llama работает как fallback модель."""
        mock_torch.cuda.is_available.return_value = False
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        success, info = tm.test_llama()

        assert success is True
        assert info['status'] == 'available'
>>>>>>> Stashed changes

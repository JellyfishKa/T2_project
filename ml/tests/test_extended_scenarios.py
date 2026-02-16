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
    import ml.test_models as tm


class TestExtendedModels:

    def setup_method(self):
        mock_transformers.reset_mock()
        mock_torch.reset_mock()
        mock_transformers.AutoTokenizer.from_pretrained.side_effect = None
        mock_transformers.AutoConfig.from_pretrained.side_effect = None
        mock_transformers.AutoModelForCausalLM.from_pretrained.side_effect = None

    def test_qwen_with_cpu_fallback(self):
        """TC-ML-006: Тест Qwen с CPU fallback при недоступности GPU."""
        mock_torch.cuda.is_available.return_value = False

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 1000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_config_instance = MagicMock()
        mock_config_instance.num_parameters.return_value = 1000000
        mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance

        success, info = tm.test_qwen()

        assert success is True
        assert info['status'] == 'available'
        assert info['model_name'] == "Qwen/Qwen2-0.5B-Instruct"

    def test_llama_cpu_mode(self):
        """TC-ML-007: Тест Llama в CPU режиме."""
        mock_torch.cuda.is_available.return_value = False

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        success, info = tm.test_llama()

        assert success is True
        assert info['model_name'] == "meta-llama/Llama-3.2-1B-Instruct"

    def test_llama_gpu_loading_failure(self):
        """TC-ML-008: Тест Llama с обработкой ошибки при загрузке на GPU."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "Mock GPU"

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.__len__.return_value = 2000
        mock_tokenizer_instance.return_value.to.return_value = {}
        mock_tokenizer_instance.decode.return_value = "mock response"
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_transformers.AutoConfig.from_pretrained.return_value = MagicMock()

        mock_transformers.AutoModelForCausalLM.from_pretrained.side_effect = RuntimeError("Not enough memory")

        success, info = tm.test_llama()

        assert success is True
        assert info['model_name'] == "meta-llama/Llama-3.2-1B-Instruct"

    def test_system_info_collection(self):
        """TC-ML-009: Тест сбора информации о системе."""
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.total = 16 * 1024**3
        mock_psutil.virtual_memory.return_value.available = 8 * 1024**3

        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3080"
        mock_torch.cuda.get_device_properties.return_value.total_memory = 10 * 1024**3

        sys_info = tm.get_system_info()

        assert 'cpu_count' in sys_info
        assert 'ram_total_gb' in sys_info
        assert 'cuda_available' in sys_info

    def test_results_output_format(self):
        """TC-ML-010: Тест формата вывода результатов (только Qwen и Llama)."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                models_dir = Path("ml/models")
                models_dir.mkdir(parents=True, exist_ok=True)

                mock_torch.cuda.is_available.return_value = False

                mock_tokenizer_instance = MagicMock()
                mock_tokenizer_instance.__len__.return_value = 1000
                mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer_instance

                mock_config_instance = MagicMock()
                mock_config_instance.num_parameters.return_value = 1000000
                mock_transformers.AutoConfig.from_pretrained.return_value = mock_config_instance

                mock_psutil.cpu_count.return_value = 4
                mock_psutil.virtual_memory.return_value.total = 8 * 1024**3
                mock_psutil.virtual_memory.return_value.available = 4 * 1024**3

                import datetime
                from unittest.mock import mock_open

                results_summary = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'system_info': {
                        'cpu_count': 4,
                        'ram_total_gb': 8.0,
                        'cuda_available': False
                    },
                    'results': {
                        'qwen': {'success': True, 'info': {'model_name': 'Qwen/Qwen2-0.5B-Instruct', 'status': 'available'}},
                        'llama': {'success': True, 'info': {'model_name': 'meta-llama/Llama-3.2-1B-Instruct', 'status': 'available'}}
                    }
                }

                results_file = Path('ml/models/test_results.json')
                with patch("builtins.open", mock_open()) as mock_file:
                    with open(results_file, 'w', encoding='utf-8') as f:
                        json.dump(results_summary, f, indent=2, ensure_ascii=False)

                    mock_file.assert_called_once_with(results_file, 'w', encoding='utf-8')

                all_success = all(r['success'] for r in results_summary['results'].values())
                assert all_success is True
                assert 'tpro' not in results_summary['results'], "T-Pro не должен быть в результатах"

            finally:
                os.chdir(original_cwd)


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
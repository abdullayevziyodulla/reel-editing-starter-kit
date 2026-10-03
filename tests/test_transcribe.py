"""Model selection and fallback regression tests; no credentials or network calls."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import transcribe


class TranscriptionModelsTests(unittest.TestCase):
    def test_default_and_template_use_original_chain(self):
        with patch.dict(os.environ, {}, clear=True):
            for config in ({}, {'GEMINI_MODEL': ''}, {'GEMINI_MODEL': 'gemini-3.5-flash'}):
                self.assertEqual(transcribe.select_models(config=config), list(transcribe.DEFAULT_MODELS))

    def test_explicit_model_overrides_environment_and_config(self):
        with patch.dict(os.environ, {'GEMINI_MODEL': 'environment-model'}, clear=True):
            self.assertEqual(transcribe.select_models(' chosen-model ', {'GEMINI_MODEL': 'file-model'}), ['chosen-model'])
            self.assertEqual(transcribe.select_models(config={'GEMINI_MODEL': 'file-model'}), ['environment-model'])

    def test_file_override_and_whitespace_environment(self):
        with patch.dict(os.environ, {'GEMINI_MODEL': '  '}, clear=True):
            self.assertEqual(transcribe.select_models(config={'GEMINI_MODEL': ' file-model '}), ['file-model'])

    def test_retries_then_uses_next_model_and_records_it(self):
        generate = Mock(side_effect=[RuntimeError('unavailable')] * 3 + [SimpleNamespace(text='[{"i":1,"text":"Salom"}]')])
        client = SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        with patch.object(transcribe, 'MODELS', list(transcribe.DEFAULT_MODELS)), patch.object(transcribe.time, 'sleep'):
            texts, model = transcribe.transcribe(client, [b'fake-audio'])
        self.assertEqual(texts, ['Salom'])
        self.assertEqual(model, 'gemini-3.8-flash')
        self.assertEqual([call.kwargs['model'] for call in generate.call_args_list], ['gemini-3.5-flash'] * 3 + ['gemini-3.8-flash'])


if __name__ == '__main__':
    unittest.main()

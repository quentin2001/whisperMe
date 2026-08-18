import pytest
from app.core.transcriber import clean_sensevoice_text, detect_funasr_model_type


class TestSenseVoiceUtils:
    def test_clean_sensevoice_text_strips_tags(self):
        raw = "<|zh|><|HAPPY|><|Speech|><|withitn|>只要你有创业的想法，你做事的风格都会改变。<|zh|><|ANGRY|><|Speech|><|withitn|>一个人干不完的！"
        cleaned = clean_sensevoice_text(raw)
        assert "<|" not in cleaned
        assert "|>" not in cleaned
        assert "只要你有创业的想法，你做事的风格都会改变。一个人干不完的！" in cleaned

    def test_clean_sensevoice_text_empty_and_spaces(self):
        assert clean_sensevoice_text("") == ""
        assert clean_sensevoice_text(None) == ""
        assert clean_sensevoice_text("   <|zh|>   hello   world   ") == "hello world"

    def test_clean_sensevoice_text_removes_the_dot_artifact(self):
        raw = "<|zh|><|Speech|>The. 这是一个关于测试的句子。"
        cleaned = clean_sensevoice_text(raw)
        assert "The." not in cleaned
        assert "这是一个关于测试的句子。" in cleaned

    def test_detect_funasr_model_type_sensevoice(self):
        assert detect_funasr_model_type("iic/SenseVoiceSmall") == "sensevoice"
        assert detect_funasr_model_type(r"E:\Projects\whisperMe\models\SenseVoiceSmall") == "sensevoice"
        assert detect_funasr_model_type(r"models/sensevoice_custom") == "sensevoice"

    def test_detect_funasr_model_type_paraformer(self):
        assert detect_funasr_model_type("") == "paraformer"
        assert detect_funasr_model_type("paraformer-zh") == "paraformer"
        assert detect_funasr_model_type("iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch") == "paraformer"
        assert detect_funasr_model_type(r"E:\Projects\whisperMe\models\funasr") == "paraformer"

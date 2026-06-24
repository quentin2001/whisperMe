"""
whisperMe Config API 测试
覆盖：配置读写、热更新、ASR providers、prompt 管理
"""
import pytest


class TestGetConfig:
    """GET /api/config"""

    def test_get_config(self, client):
        """返回完整配置字典"""
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        # 应该包含核心配置字段
        assert "ffmpeg_path" in data
        assert "ollama_url" in data
        assert "ollama_model" in data
        assert "asr_mode" in data
        assert "summary_mode" in data
        assert "language" in data

    def test_get_config_returns_dict(self, client):
        """返回值是字典类型"""
        resp = client.get("/api/config")
        assert isinstance(resp.json(), dict)


class TestUpdateConfig:
    """POST /api/config"""

    def test_update_config(self, client):
        """配置持久化"""
        # 先获取当前配置
        resp = client.get("/api/config")
        assert resp.status_code == 200
        cfg = resp.json()

        # 修改一个字段
        cfg["language"] = "zh"
        resp2 = client.post("/api/config", json=cfg)
        assert resp2.status_code == 200
        assert resp2.json()["success"] is True

        # 验证更新生效
        resp3 = client.get("/api/config")
        assert resp3.json()["language"] == "zh"

    def test_update_config_missing_required(self, client):
        """缺少必填字段返回 422"""
        resp = client.post("/api/config", json={"ffmpeg_path": ""})
        assert resp.status_code == 422

    def test_update_config_changes_ollama_model(self, client):
        """修改 Ollama 模型配置"""
        resp = client.get("/api/config")
        cfg = resp.json()
        cfg["ollama_model"] = "qwen2.5:14b"
        resp2 = client.post("/api/config", json=cfg)
        assert resp2.status_code == 200

        resp3 = client.get("/api/config")
        assert resp3.json()["ollama_model"] == "qwen2.5:14b"


class TestAsrProviders:
    """GET /api/asr-providers"""

    def test_list_asr_providers(self, client):
        """返回可用的 ASR providers 列表"""
        resp = client.get("/api/asr-providers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))


class TestPrompt:
    """GET/POST /api/prompt"""

    def test_get_prompt(self, client):
        """返回 prompt 模板"""
        resp = client.get("/api/prompt")
        assert resp.status_code == 200

    def test_set_prompt(self, client):
        """保存 prompt 模板"""
        resp = client.post("/api/prompt", json={
            "system_prompt": "你是一个播客分析助手。",
            "user_prompt_template": "请分析以下播客转录内容：{transcript}"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # 验证保存成功
        resp2 = client.get("/api/prompt")
        assert resp2.status_code == 200

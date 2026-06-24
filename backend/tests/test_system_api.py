"""
whisperMe System API 测试
覆盖：性能监控、依赖检查、版本检查
"""
import pytest
from unittest.mock import patch, MagicMock


class TestPerformance:
    """GET /api/performance"""

    def test_get_performance(self, client):
        """返回性能指标结构"""
        resp = client.get("/api/performance")
        assert resp.status_code == 200
        data = resp.json()
        # 应包含基本结构
        assert "cpu" in data
        assert "ram" in data
        assert "disk" in data
        assert "queue" in data
        assert "llm_status" in data

    def test_performance_ram_structure(self, client):
        """RAM 指标结构正确"""
        resp = client.get("/api/performance")
        ram = resp.json()["ram"]
        assert "total" in ram
        assert "used" in ram
        assert "percent" in ram


class TestDependencies:
    """GET /api/dependencies"""

    def test_check_dependencies(self, client):
        """返回依赖状态结构"""
        resp = client.get("/api/dependencies")
        assert resp.status_code == 200
        data = resp.json()
        assert "ffmpeg" in data
        assert "huggingface" in data
        assert "ollama" in data
        assert "gpu" in data

    def test_check_dependencies_ffmpeg_structure(self, client):
        """FFmpeg 检查结构正确"""
        resp = client.get("/api/dependencies")
        ffmpeg = resp.json()["ffmpeg"]
        assert "available" in ffmpeg

    def test_check_dependencies_huggingface_structure(self, client):
        """HuggingFace 检查结构正确"""
        resp = client.get("/api/dependencies")
        hf = resp.json()["huggingface"]
        assert "token_valid" in hf

    def test_check_dependencies_with_custom_ffmpeg(self, client):
        """传入自定义 ffmpeg 路径"""
        resp = client.get("/api/dependencies?ffmpeg_path=C:\\ffmpeg\\bin\\ffmpeg.exe")
        assert resp.status_code == 200
        data = resp.json()
        assert "ffmpeg" in data


class TestVersionCheck:
    """GET /api/version/check"""

    def test_version_check(self, client):
        """返回版本检查结果"""
        resp = client.get("/api/version/check")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_version" in data
        assert "latest_version" in data
        assert "has_update" in data
        assert "release_url" in data

    def test_version_check_force(self, client):
        """强制刷新版本检查"""
        resp = client.get("/api/version/check?force=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_version" in data
        assert isinstance(data["has_update"], bool)

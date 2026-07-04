"""
Suite 2 (DLS): 下载器策略模式测试
测试对象: downloader.py, strategies/
核心验证点: 8 大策略精确路由、can_handle() 优先级
"""
import os
import pytest
from app.core.downloader import PodcastDownloader


class TestDLSRoute:
    """DLS_RT_01~05: 策略路由"""

    def setup_method(self):
        self.downloader = PodcastDownloader()

    def test_xiaoyuzhou_route(self):
        """小宇宙链接 → XiaoyuzhouStrategy"""
        strategy = self.downloader._get_strategy("https://xiaoyuzhoufm.com/episode/abc123")
        assert "Xiaoyuzhou" in strategy.__class__.__name__

    def test_bilibili_long_url_route(self):
        """Bilibili 长链接 → BilibiliStrategy"""
        strategy = self.downloader._get_strategy("https://www.bilibili.com/video/BV1xx411x7h7")
        assert "Bilibili" in strategy.__class__.__name__

    def test_bilibili_short_url_route(self):
        """Bilibili 短链接 → BilibiliStrategy"""
        strategy = self.downloader._get_strategy("https://b23.tv/abcXYZ")
        assert "Bilibili" in strategy.__class__.__name__

    def test_local_file_route(self):
        """本地文件路径 → LocalStrategy"""
        # 需要真实存在的文件
        fixture_path = os.path.abspath("tests/fixtures/short_audio.mp3")
        assert os.path.exists(fixture_path), f"Fixture not found: {fixture_path}"
        strategy = self.downloader._get_strategy(fixture_path)
        assert "Local" in strategy.__class__.__name__

    def test_unknown_route_falls_to_ytdlp(self):
        """未知链接 → YtDlpStrategy（兜底）"""
        strategy = self.downloader._get_strategy("https://unknown-platform.com/ep/42")
        assert "YtDlp" in strategy.__class__.__name__

    def test_strategy_priority_local_over_ytdlp(self):
        """策略链顺序：Local 优先于 YtDlp"""
        # 同名路径优先匹配 LocalStrategy（os.path.exists）
        strategies = self.downloader.strategies
        strategy_names = [s.__class__.__name__ for s in strategies]
        assert "LocalStrategy" in strategy_names
        assert "YtDlpStrategy" in strategy_names
        # 确保 Local 在 YtDlp 前面
        local_idx = strategy_names.index("LocalStrategy")
        ytdlp_idx = strategy_names.index("YtDlpStrategy")
        assert local_idx < ytdlp_idx, "LocalStrategy must come before YtDlpStrategy"

    def test_empty_url_routes_to_ytdlp(self):
        """空字符串路由到兜底策略"""
        strategy = self.downloader._get_strategy("")
        assert "YtDlp" in strategy.__class__.__name__

    def test_garbage_url_routes_to_ytdlp(self):
        """纯中文非链接路由到兜底策略"""
        strategy = self.downloader._get_strategy("纯中文非链接")
        assert "YtDlp" in strategy.__class__.__name__


class TestDLSStrategyBehavior:
    """DLS_META_06~08: 策略行为验证"""

    def setup_method(self):
        self.downloader = PodcastDownloader()

    def test_local_strategy_metadata(self):
        """本地策略返回正确元数据结构"""
        from app.core.strategies.local_strategy import LocalStrategy
        strategy = LocalStrategy()
        fixture = os.path.abspath("tests/fixtures/short_audio.mp3")
        meta = strategy.parse_metadata(fixture)
        assert meta["source"] == "local"
        assert meta["podcast_name"] == "本地导入"

    def test_all_strategies_have_can_handle(self):
        """每个策略都实现了 can_handle 方法"""
        downloader = PodcastDownloader()
        for s in downloader.strategies:
            assert hasattr(s, "can_handle"), f"{s.__class__.__name__} missing can_handle"
            assert callable(s.can_handle)
            assert hasattr(s, "parse_metadata"), f"{s.__class__.__name__} missing parse_metadata"
            assert hasattr(s, "download_audio"), f"{s.__class__.__name__} missing download_audio"

    def test_ytdlp_is_last_strategy(self):
        """YtDlpStrategy 是策略链最后一个（兜底）"""
        downloader = PodcastDownloader()
        assert "YtDlpStrategy" == downloader.strategies[-1].__class__.__name__

    def test_parse_metadata_for_unknown_url_uses_ytdlp(self, monkeypatch):
        """未知链接走 YtDlp 解析（mock 网络调用）"""
        from app.core.strategies.ytdlp_strategy import YtDlpStrategy
        def mock_parse(self, url):
            return {"title": "Mocked", "podcast_name": "Test", "source": "ytdlp"}
        monkeypatch.setattr(YtDlpStrategy, "parse_metadata", mock_parse)
        meta = self.downloader.parse_metadata("https://example.com/some/podcast")
        assert isinstance(meta, dict)
        assert meta["source"] == "ytdlp"


class TestDLSBVExtract:
    """DLS_META_07: Bilibili BV 号提取"""

    def test_extract_bvid_from_long_url(self):
        """从 Bilibili 长链接中提取 BV 号"""
        import re
        url = "https://www.bilibili.com/video/BV1GJ411x7h7?spm=xxx"
        match = re.search(r"(BV[a-zA-Z0-9]+)", url)
        assert match is not None
        assert match.group(1) == "BV1GJ411x7h7"

    def test_extract_bvid_from_short_url(self):
        """短链接需要先还原（这里只测正则，不测网络）"""
        import re
        url = "https://b23.tv/abcXYZ"
        # 短链接本身不包含 BV 号，但策略会先 follow 重定向再提取
        # 验证 b23.tv 可以被 can_handle 识别
        from app.core.strategies.bilibili_strategy import BilibiliStrategy
        strategy = BilibiliStrategy()
        assert strategy.can_handle(url) is True

    def test_bv_regex_no_match_raises(self):
        """无 BV 号时策略抛出明确异常"""
        from app.core.strategies.bilibili_strategy import BilibiliStrategy
        strategy = BilibiliStrategy()
        with pytest.raises(Exception) as exc:
            strategy.parse_metadata("https://example.com/not-bilibili")
        assert "BV" in str(exc.value) or "未能在链接中解析" in str(exc.value)


class TestDLSCacheSkip:
    """DLS_SKIP_09: YtDlp 缓存跳过"""

    def test_ytdlp_skip_if_local_file_exists(self, monkeypatch, tmp_path):
        """已下载文件 > 1MB 时跳过 yt-dlp 下载"""
        from app.core.strategies.ytdlp_strategy import YtDlpStrategy

        # 创建 > 1MB 的 mock 文件
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_bytes(b"x" * (1024 * 1024 + 1))  # 1MB + 1 byte

        parse_called = False
        def mock_parse(self, url):
            nonlocal parse_called
            parse_called = True
            return {"title": "Cached", "podcast_name": "Test", "source": "ytdlp"}

        monkeypatch.setattr(YtDlpStrategy, "parse_metadata", mock_parse)

        strategy = YtDlpStrategy()
        result = strategy.download_audio("https://example.com/test", str(audio_file))
        assert parse_called is True
        assert result["title"] == "Cached"
        assert result["source"] == "ytdlp"

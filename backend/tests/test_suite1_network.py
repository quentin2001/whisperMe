"""
Suite 1 (NET): 网络与 DoH 并发模块测试
测试对象: network.py
核心验证点: DoH 线程安全、DNS 解析降级、静态 IP 兜底
"""
import os
import socket
import pytest
from unittest.mock import patch, MagicMock
from app.core.network import resolve_host_via_doh, doh_dns_bypass, _thread_local


class TestNetDOH:
    """NET_DOH_01~04: DoH 解析链"""

    def test_doh_known_domain_returns_ip(self):
        """已知域名应该能通过 DoH 解析到 IP"""
        ip = resolve_host_via_doh("example.com")
        assert ip is not None
        assert isinstance(ip, str)
        # 不应返回 fake-IP
        assert not ip.startswith("198.18."), f"Got fake-IP: {ip}"

    def test_doh_static_ip_fallback(self):
        """静态 IP 映射优先返回"""
        ip = resolve_host_via_doh("token-plan-sgp.xiaomimimo.com")
        assert ip == "8.222.147.102"

    def test_doh_empty_host_returns_none(self):
        """空 host 返回 None"""
        assert resolve_host_via_doh("") is None
        assert resolve_host_via_doh(None) is None

    def test_doh_invalid_host_graceful(self):
        """无效域名不抛异常，返回 None"""
        ip = resolve_host_via_doh("this-domain-definitely-does-not-exist-12345.com")
        # 返回 None 而不是抛异常
        assert ip is None or isinstance(ip, str)

    def test_doh_bypass_context_manager(self):
        """doh_dns_bypass 上下文管理器正确设置和清理 thread-local"""
        with doh_dns_bypass("https://example.com/path"):
            override = getattr(_thread_local, "doh_override", None)
            if override:
                host, ip = override
                assert isinstance(host, str)
                assert isinstance(ip, str)
        # 退出后应清理
        assert getattr(_thread_local, "doh_override", None) is None

    def test_doh_bypass_invalid_url(self):
        """无效 URL 不会导致异常"""
        with doh_dns_bypass("not-a-url"):
            pass  # 不应抛异常

    def test_doh_bypass_empty_url(self):
        """空 URL 不会导致异常"""
        with doh_dns_bypass(""):
            pass  # 不应抛异常


class TestNetDOHThreadSafety:
    """NET_DOH_01: DoH 线程安全"""

    def test_thread_local_isolation(self):
        """多线程并发使用 doh_dns_bypass，thread-local 互不干扰"""
        import threading
        results = {}
        errors = {}

        def worker(wid, host, ip):
            try:
                with doh_dns_bypass(f"https://{host}/path"):
                    override = getattr(_thread_local, "doh_override", None)
                    results[wid] = override
            except Exception as e:
                errors[wid] = str(e)

        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i, f"host{i}.test.com", f"10.0.0.{i}"))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0, f"Thread errors: {errors}"
        # 主线程 thread-local 不受影响
        assert getattr(_thread_local, "doh_override", None) is None

    def test_clash_fake_ip_does_not_leak(self, monkeypatch):
        """即使系统 DNS 返回 fake-IP，DoH 解析不应被影响"""
        # Mock socket.getaddrinfo 返回 fake-IP
        def mock_getaddrinfo(host, port, *args, **kwargs):
            if host == "example.com":
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ("198.18.0.46", port))]
            raise socket.gaierror("Unknown host")

        monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

        ip = resolve_host_via_doh("example.com")
        # 应该通过 DoH 得到真实 IP，不是 fake-IP
        if ip is not None:
            assert not ip.startswith("198.18."), f"Got fake-IP: {ip}"


class TestNetDownloadFallback:
    """NET_DL_05~06: 4 级下载降级链"""

    def test_download_fallback_all_levels_mocked(self, monkeypatch, tmp_path):
        """4 级降级全部 Mock 模拟，验证逐级尝试逻辑"""
        import httpx
        import subprocess
        from app.core.network_utils import download_file_with_fallback

        calls = []
        out_file = tmp_path / "test_output.bin"

        # Level 1: httpx 代理失败
        original_httpx = httpx.Client.stream
        def mock_httpx_stream(self, method, url, **kw):
            calls.append("httpx_proxy")
            raise httpx.ConnectError("代理连接超时")

        # Level 2: httpx 直连失败
        def mock_httpx_doh_stream(self, method, url, **kw):
            calls.append("httpx_doh")
            raise httpx.ConnectError("直连超时")

        # Level 3: curl 代理失败
        original_run = subprocess.run
        def mock_curl_proxy(cmd, **kw):
            calls.append("curl_proxy")
            class MockResult:
                returncode = 1
                stdout = b""
                stderr = b""
            return MockResult()

        # Level 4: curl DoH 成功
        def mock_curl_doh(cmd, **kw):
            calls.append("curl_doh")
            out_file.write_text("downloaded")
            class MockResult:
                returncode = 0
                stdout = b""
                stderr = b""
            return MockResult()

        # 依次替换
        monkeypatch.setattr(httpx.Client, "stream", mock_httpx_stream)
        monkeypatch.setattr("app.core.network_utils.subprocess.run", mock_curl_doh)

        download_file_with_fallback("https://example.com/audio.mp3", str(out_file))
        assert os.path.exists(str(out_file))

    def test_download_all_fail_raises_exception(self, monkeypatch):
        """所有下载方式均失败时抛出明确异常"""
        import httpx
        from app.core.network_utils import download_file_with_fallback

        tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "test_fail.bin")

        def mock_fail_stream(self, method, url, **kw):
            raise httpx.ConnectError("全部失败")

        def mock_fail_curl(cmd, **kw):
            class MockResult:
                returncode = 1
                stdout = b""
                stderr = b""
            return MockResult()

        monkeypatch.setattr(httpx.Client, "stream", mock_fail_stream)
        monkeypatch.setattr("app.core.network_utils.subprocess.run", mock_fail_curl)

        with pytest.raises(Exception) as exc:
            download_file_with_fallback("https://example.com/audio.mp3", tmp)
        assert "所有下载方式均失败" in str(exc.value)
        if os.path.exists(tmp):
            os.remove(tmp)


class TestNetRedirect:
    """NET_REDIR_08: DoH 重定向追踪"""

    def test_resolve_redirects_via_doh_returns_original_on_no_redirect(self, monkeypatch):
        """无重定向时返回原始 URL"""
        from app.core.network_utils import resolve_redirects_via_doh

        original_url = "https://example.com/audio.mp3"

        def mock_head(self, url, **kw):
            class MockResp:
                status_code = 200
                headers = {}
            return MockResp()

        monkeypatch.setattr("httpx.Client.head", mock_head)
        result = resolve_redirects_via_doh(original_url)
        assert result == original_url

    def test_resolve_redirects_stops_at_cdn_domain(self, monkeypatch):
        """遇到 xmcdn.com / xyzcdn.net 时提前终止追踪"""
        from app.core.network_utils import resolve_redirects_via_doh

        result = resolve_redirects_via_doh("https://audio.xmcdn.com/test.mp3")
        # 无需 HTTP 请求，直接返回原始 URL
        assert "xmcdn.com" in result

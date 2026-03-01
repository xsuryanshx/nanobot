"""Tests for web tools proxy support."""

import pytest

from nanobot.agent.tools.web import WebFetchTool, WebSearchTool


class TestWebSearchToolProxy:
    """Tests for WebSearchTool proxy parameter."""

    def test_init_without_proxy(self) -> None:
        """Test WebSearchTool initializes without proxy."""
        tool = WebSearchTool()
        assert tool.proxy is None

    def test_init_with_proxy(self) -> None:
        """Test WebSearchTool initializes with proxy."""
        proxy_url = "http://127.0.0.1:7890"
        tool = WebSearchTool(proxy=proxy_url)
        assert tool.proxy == proxy_url

    def test_init_with_proxy_socks5(self) -> None:
        """Test WebSearchTool initializes with SOCKS5 proxy."""
        proxy_url = "socks5://127.0.0.1:1080"
        tool = WebSearchTool(proxy=proxy_url)
        assert tool.proxy == proxy_url

    def test_init_with_api_key_and_proxy(self) -> None:
        """Test WebSearchTool initializes with both api_key and proxy."""
        proxy_url = "http://127.0.0.1:7890"
        api_key = "test_api_key"
        tool = WebSearchTool(api_key=api_key, proxy=proxy_url)
        assert tool.proxy == proxy_url
        assert tool.api_key == api_key

    def test_api_key_property_from_env(self, monkeypatch) -> None:
        """Test WebSearchTool resolves API key from environment."""
        monkeypatch.setenv("BRAVE_API_KEY", "env_api_key")
        tool = WebSearchTool()  # No api_key passed
        assert tool.api_key == "env_api_key"

    def test_api_key_property_init_key_takes_precedence(self, monkeypatch) -> None:
        """Test that init api_key takes precedence over env var."""
        monkeypatch.setenv("BRAVE_API_KEY", "env_api_key")
        tool = WebSearchTool(api_key="init_api_key")
        assert tool.api_key == "init_api_key"


class TestWebFetchToolProxy:
    """Tests for WebFetchTool proxy parameter."""

    def test_init_without_proxy(self) -> None:
        """Test WebFetchTool initializes without proxy."""
        tool = WebFetchTool()
        assert tool.proxy is None

    def test_init_with_proxy(self) -> None:
        """Test WebFetchTool initializes with proxy."""
        proxy_url = "http://127.0.0.1:7890"
        tool = WebFetchTool(proxy=proxy_url)
        assert tool.proxy == proxy_url

    def test_init_with_proxy_socks5(self) -> None:
        """Test WebFetchTool initializes with SOCKS5 proxy."""
        proxy_url = "socks5://127.0.0.1:1080"
        tool = WebFetchTool(proxy=proxy_url)
        assert tool.proxy == proxy_url

    def test_init_with_max_chars_and_proxy(self) -> None:
        """Test WebFetchTool initializes with max_chars and proxy."""
        proxy_url = "http://127.0.0.1:7890"
        max_chars = 10000
        tool = WebFetchTool(max_chars=max_chars, proxy=proxy_url)
        assert tool.proxy == proxy_url
        assert tool.max_chars == max_chars

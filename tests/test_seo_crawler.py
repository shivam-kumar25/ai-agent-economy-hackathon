from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.seo.crawler import crawl_urls


@pytest.mark.asyncio
async def test_crawl_urls_returns_list():
    mock_doc = MagicMock()
    mock_doc.page_content = "<html><head><title>Test Page</title></head><body><p>Hello</p></body></html>"
    mock_doc.metadata = {"source": "https://example.com"}

    with patch("src.modules.seo.crawler.WebBaseLoader") as MockLoader:
        instance = MockLoader.return_value
        instance.load.return_value = [mock_doc]

        results = await crawl_urls(["https://example.com"])

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com"
    assert results[0]["title"] == "Test Page"


@pytest.mark.asyncio
async def test_crawl_urls_handles_failure():
    with patch("src.modules.seo.crawler.WebBaseLoader") as MockLoader:
        MockLoader.return_value.load.side_effect = Exception("network error")
        results = await crawl_urls(["https://broken.example.com"])

    assert results == []


@pytest.mark.asyncio
async def test_crawl_urls_empty_input():
    results = await crawl_urls([])
    assert results == []

# -*- coding: utf-8 -*-
"""Retrieve Productoo roadmap pages for later processing."""

from __future__ import annotations

from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def _extract_text(html: str) -> str:
    """Return clean text from HTML preserving basic structure."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    # Use newline as separator to roughly keep paragraphs and headings
    text = soup.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    # Remove empty lines but keep intentional paragraph breaks
    cleaned = "\n".join([line for line in lines if line])
    return cleaned


def retrieve_roadmap_documents(base_url: str) -> List[Dict[str, str]]:
    """Crawl all pages under ``base_url`` and return their text content.

    Parameters
    ----------
    base_url:
        Root URL of the roadmap. All subpages beginning with this URL will be
        fetched recursively.
    """

    visited: Set[str] = set()
    documents: List[Dict[str, str]] = []
    queue: List[str] = [base_url.rstrip("/")]

    parsed_base = urlparse(base_url)
    base_netloc = parsed_base.netloc

    while queue:
        url = queue.pop()
        if url in visited:
            continue
        visited.add(url)

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            continue

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        content = _extract_text(html)
        documents.append({"title": title, "url": url, "content": content})

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            absolute = urljoin(url, href)
            parsed = urlparse(absolute)
            if parsed.netloc != base_netloc:
                continue
            if not absolute.startswith(base_url.rstrip("/")):
                continue
            if absolute not in visited:
                queue.append(absolute)

    return documents

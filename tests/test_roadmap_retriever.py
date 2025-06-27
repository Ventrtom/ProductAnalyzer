import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from retrievers.roadmap_retriever import _extract_text, retrieve_roadmap_documents


def test_extract_text_removes_scripts_and_styles():
    html = """
    <html>
        <head>
            <style>body {background:red;}</style>
            <script>console.log('hello');</script>
        </head>
        <body>
            <p>First paragraph.</p>
            <script>alert('x');</script>
            <p>Second paragraph.</p>
        </body>
    </html>
    """
    text = _extract_text(html)
    assert "script" not in text
    assert "style" not in text
    assert "First paragraph." in text
    assert "Second paragraph." in text
    # paragraphs should remain separated
    parts = text.split("\n")
    assert "First paragraph." in parts[0]
    assert "Second paragraph." in parts[-1]


def test_retrieve_roadmap_documents(monkeypatch):
    main_html = """
    <html>
        <head><title>Main Page</title></head>
        <body>
            <a href='/page1'>Page1</a>
            <a href='http://other.com/bad'>Offsite</a>
            <p>Main content</p>
        </body>
    </html>
    """
    page1_html = """
    <html>
        <head><title>Page1</title></head>
        <body>
            <p>Page1 content</p>
        </body>
    </html>
    """

    def fake_get(url, timeout=30):
        response = mock.Mock()
        if url.endswith('/page1'):
            response.text = page1_html
        else:
            response.text = main_html
        response.raise_for_status = mock.Mock()
        return response

    monkeypatch.setattr('requests.get', fake_get)

    def fake_bs(html, parser):
        from bs4 import BeautifulSoup as RealBS
        return RealBS(html, parser)

    monkeypatch.setattr('retrievers.roadmap_retriever.BeautifulSoup', fake_bs)

    docs = retrieve_roadmap_documents('http://test.com')
    titles = [d['title'] for d in docs]
    urls = [d['url'] for d in docs]

    assert titles == ['Main Page', 'Page1']
    assert urls == ['http://test.com', 'http://test.com/page1']

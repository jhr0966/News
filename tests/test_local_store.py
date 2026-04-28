from __future__ import annotations

from pathlib import Path

from local_store import LocalNewsRepository


def test_save_and_load_latest_articles(tmp_path: Path) -> None:
    repo = LocalNewsRepository(data_root=tmp_path / "data")
    articles = [
        {"title": "A", "link": "https://example.com/a", "press": "X"},
        {"title": "B", "link": "https://example.com/b", "press": "Y"},
    ]

    saved = repo.save_articles_batch("naver", articles, keyword="ai")

    assert saved["raw"].endswith(".jsonl")
    assert saved["processed"].endswith(".parquet")
    assert Path(saved["raw"]).exists()
    assert Path(saved["processed"]).exists()

    loaded = repo.load_latest_articles("naver")
    assert len(loaded) == 2
    assert loaded[0]["query_keyword"] == "ai"
    assert loaded[0]["source_batch"] == "naver"


def test_empty_cases(tmp_path: Path) -> None:
    repo = LocalNewsRepository(data_root=tmp_path / "data")

    assert repo.load_latest_articles("tech") == []
    assert repo.save_articles_batch("tech", []) == {}


from __future__ import annotations

import pandas as pd

from proposal_engine import (
    list_recent_proposal_artifacts,
    proposals_to_markdown,
    save_proposals_artifacts,
    score_article_for_task,
    suggest_for_tasks,
)


def test_score_article_for_task_overlap() -> None:
    task = {"task_name": "용접 자동화", "description": "블록 용접 품질 개선", "process": "용접"}
    article = {
        "title": "조선소 용접 자동화 기술 도입 사례",
        "summary": "블록 용접 품질 향상",
        "content": "",
        "keywords": "용접,자동화,품질",
    }
    score, terms = score_article_for_task(task, article)
    assert score > 0
    assert "용접" in terms


def test_suggest_for_tasks_topk() -> None:
    tasks_df = pd.DataFrame(
        [
            {"task_id": "T-1", "process": "도장", "task_name": "표면 처리", "description": "품질 검사 자동화"},
            {"task_id": "T-2", "process": "용접", "task_name": "블록 용접", "description": "자동 용접 기술"},
        ]
    )
    articles = [
        {
            "title": "용접 자동화 사례",
            "summary": "조선 블록 품질 향상",
            "content": "",
            "keywords": "용접,자동화",
            "published_at": "2026-04-27T00:00:00+00:00",
            "press": "AITimes",
        },
        {"title": "도장 공정 로봇", "summary": "표면 처리 효율", "content": "", "keywords": "도장,로봇"},
    ]

    out = suggest_for_tasks(tasks_df, articles, top_k=1)
    assert len(out) == 2
    assert "priority_score" in out[0]
    assert out[0]["recommendation_count"] <= 1
    assert out[1]["recommendation_count"] <= 1
    if out[0]["recommendations"]:
        rec = out[0]["recommendations"][0]
        assert "freshness_score" in rec
        assert "source_score" in rec


def test_save_proposals_artifacts(tmp_path) -> None:
    proposals = [
        {
            "task_id": "T-1",
            "task_name": "블록 용접",
            "process": "용접",
            "recommendation_count": 1,
            "recommendations": [
                {"title": "용접 자동화 사례", "score": 0.5, "overlap_terms": ["용접"], "link": "https://example.com"}
            ],
        }
    ]
    paths = save_proposals_artifacts(proposals, data_root=tmp_path / "data")
    md = proposals_to_markdown(proposals, template="execution")
    hist = list_recent_proposal_artifacts(data_root=tmp_path / "data", limit=5)

    assert "블록 용접" in md
    assert "실행안" in md
    assert "json" in paths and "markdown_exec" in paths and "markdown_exec_plan" in paths
    assert len(hist) >= 1

from __future__ import annotations

import pandas as pd

from proposal_engine import (
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
        {"title": "용접 자동화 사례", "summary": "조선 블록 품질 향상", "content": "", "keywords": "용접,자동화"},
        {"title": "도장 공정 로봇", "summary": "표면 처리 효율", "content": "", "keywords": "도장,로봇"},
    ]

    out = suggest_for_tasks(tasks_df, articles, top_k=1)
    assert len(out) == 2
    assert out[0]["recommendation_count"] <= 1
    assert out[1]["recommendation_count"] <= 1


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
    md = proposals_to_markdown(proposals)

    assert "블록 용접" in md
    assert "json" in paths and "markdown" in paths

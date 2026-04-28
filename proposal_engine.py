"""작업-뉴스 매칭 기반 자동화 과제 제안 엔진 (Rule-based v1)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd


_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]{2,}")
_STOPWORDS = {"작업", "공정", "및", "에서", "으로", "대한", "관련", "기술", "자동화"}
_SOURCE_TRUST = {
    "aitimes": 0.85,
    "오토메이션월드": 0.8,
    "automation-world": 0.8,
    "연합뉴스": 0.9,
}


def _tokens(text: str) -> list[str]:
    words = _TOKEN_RE.findall((text or "").lower())
    return [w for w in words if w not in _STOPWORDS]


def _to_num(value: Any, default: float = 0.5) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            mapping = {
                "low": 0.2,
                "medium": 0.5,
                "high": 0.8,
                "낮음": 0.2,
                "보통": 0.5,
                "높음": 0.8,
            }
            if value.lower() in mapping:
                return mapping[value.lower()]
        num = float(value)
        if num > 1:
            num = num / 10.0
        return min(max(num, 0.0), 1.0)
    except Exception:
        return default


def _task_priority(task: dict[str, Any]) -> float:
    """작업 우선순위(효과/난이도/위험) 점수."""
    effect = _to_num(task.get("expected_effect", task.get("effect_score", 0.6)), 0.6)
    difficulty = _to_num(task.get("automation_level", task.get("difficulty", 0.5)), 0.5)
    risk = _to_num(task.get("risk_level", 0.4), 0.4)
    # 효과/위험 높고 난이도 낮을수록 우선
    priority = (0.5 * effect) + (0.3 * risk) + (0.2 * (1.0 - difficulty))
    return round(priority, 4)


def _freshness_score(article: dict[str, Any]) -> float:
    published = article.get("published_at", "")
    if not published:
        return 0.5
    try:
        dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = max((now - dt).days, 0)
        if days <= 2:
            return 1.0
        if days <= 7:
            return 0.8
        if days <= 30:
            return 0.6
        return 0.4
    except Exception:
        return 0.5


def _source_score(article: dict[str, Any]) -> float:
    press = str(article.get("press", "")).strip().lower()
    if not press:
        return 0.5
    for k, v in _SOURCE_TRUST.items():
        if k in press:
            return v
    return 0.6


def score_article_for_task(task: dict[str, Any], article: dict[str, Any]) -> tuple[float, list[str]]:
    """단순 토큰 중첩 기반 점수."""
    task_text = " ".join(
        [
            str(task.get("task_name", "")),
            str(task.get("description", "")),
            str(task.get("process", "")),
        ]
    )
    art_text = " ".join(
        [
            str(article.get("title", "")),
            str(article.get("summary", "")),
            str(article.get("content", "")),
            str(article.get("keywords", "")),
        ]
    )

    task_tokens = _tokens(task_text)
    art_tokens = _tokens(art_text)
    if not task_tokens or not art_tokens:
        return 0.0, []

    task_counter = Counter(task_tokens)
    art_counter = Counter(art_tokens)
    overlap = sorted(set(task_counter) & set(art_counter))
    if not overlap:
        return 0.0, []

    overlap_strength = sum(min(task_counter[t], art_counter[t]) for t in overlap)
    score = overlap_strength / max(1, len(set(task_tokens)))
    return round(float(score), 4), overlap[:5]


def suggest_for_tasks(
    tasks_df: pd.DataFrame,
    articles: list[dict[str, Any]],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """작업별 추천 기사 top_k와 제안 초안 생성."""
    if tasks_df.empty or not articles:
        return []

    results: list[dict[str, Any]] = []
    for _, row in tasks_df.iterrows():
        task = row.to_dict()
        scored = []
        for art in articles:
            relevance_score, overlaps = score_article_for_task(task, art)
            if relevance_score <= 0:
                continue
            freshness = _freshness_score(art)
            source_reliability = _source_score(art)
            final_score = round((0.7 * relevance_score) + (0.2 * freshness) + (0.1 * source_reliability), 4)
            scored.append(
                {
                    "score": final_score,
                    "relevance_score": relevance_score,
                    "freshness_score": freshness,
                    "source_score": source_reliability,
                    "overlap_terms": overlaps,
                    "title": art.get("title", ""),
                    "press": art.get("press", ""),
                    "link": art.get("link", ""),
                    "summary": art.get("summary", ""),
                    "img_url": art.get("img_url", ""),
                    "date": art.get("date", ""),
                    "published_at": art.get("published_at", ""),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:top_k]

        results.append(
            {
                "task_id": task.get("task_id", ""),
                "task_name": task.get("task_name", ""),
                "process": task.get("process", ""),
                "priority_score": _task_priority(task),
                "recommendation_count": len(top),
                "recommendations": top,
            }
        )
    results.sort(key=lambda x: (x["priority_score"], x["recommendation_count"]), reverse=True)
    return results


def proposals_to_markdown(proposals: list[dict[str, Any]], template: str = "executive") -> str:
    lines = ["# 자동화 과제 제안 결과", ""]
    for p in proposals:
        lines.append(
            f"## {p.get('task_id', '')} · {p.get('task_name', '')} ({p.get('process', '')}) "
            f"[priority={p.get('priority_score', 0)}]"
        )
        recs = p.get("recommendations", [])
        if not recs:
            lines.append("- 추천 기사 없음")
            lines.append("")
            continue
        if template == "execution":
            lines.append("### 실행안")
            lines.append("- 목적: 해당 공정 자동화 적용 검토")
            lines.append("- 예상효과: 품질/시간/안전 지표 개선")
            lines.append("- PoC: 2~4주 파일럿 + 현장 검증")
        lines.append("### 근거 기사")
        for i, rec in enumerate(recs, start=1):
            lines.append(f"- {i}. {rec.get('title', '')} (score={rec.get('score', 0)})")
            lines.append(f"  - overlap: {', '.join(rec.get('overlap_terms', []))}")
            if rec.get("link"):
                lines.append(f"  - source: {rec['link']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def save_proposals_artifacts(
    proposals: list[dict[str, Any]],
    data_root: str | Path = "data",
) -> dict[str, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    out_dir = Path(data_root) / "artifacts" / "proposals" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"proposals_{stamp}.json"
    md_exec_path = out_dir / f"proposals_executive_{stamp}.md"
    md_action_path = out_dir / f"proposals_execution_{stamp}.md"

    json_path.write_text(json.dumps(proposals, ensure_ascii=False, indent=2), encoding="utf-8")
    md_exec_path.write_text(proposals_to_markdown(proposals, template="executive"), encoding="utf-8")
    md_action_path.write_text(proposals_to_markdown(proposals, template="execution"), encoding="utf-8")

    return {"json": str(json_path), "markdown_exec": str(md_exec_path), "markdown_exec_plan": str(md_action_path)}


def list_recent_proposal_artifacts(data_root: str | Path = "data", limit: int = 20) -> list[dict[str, str]]:
    base = Path(data_root) / "artifacts" / "proposals"
    if not base.exists():
        return []

    files = sorted(
        [p for p in base.glob("*/*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    return [{"path": str(p), "name": p.name, "date": p.parent.name} for p in files]

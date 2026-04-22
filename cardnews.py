"""Cardnews: 기사 dict를 카드형 HTML 또는 PNG 이미지로 렌더한다.

docs/ARCHITECTURE.md 의 모듈 계약을 따른다.
- render_html  -> str  (HTML; assets/styles.css 의 .cn-* 클래스 의존)
- render_png   -> bytes (Pillow; 폰트/여백 상수는 이 파일 상단에 하나만)
- render_deck  -> list[bytes] (다수 기사 일괄)
- available_templates -> list[str]
"""
from __future__ import annotations

import html
import io
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent / "components" / "cardnews_template"
_DEFAULT_TEMPLATE = "default"

# Pillow 이미지 렌더 상수 (유일한 정의 지점)
CARD_SIZE_DEFAULT = (1080, 1080)
CARD_BG = "#FFFFFF"
CARD_TEXT = "#1A1918"
CARD_ACCENT = "#1D6FE8"
CARD_PAD = 72
FONT_TITLE_SIZE = 56
FONT_META_SIZE = 28


def available_templates() -> list[str]:
    """components/cardnews_template/*.html 에서 템플릿 목록."""
    if not _TEMPLATE_DIR.exists():
        return [_DEFAULT_TEMPLATE]
    return sorted(p.stem for p in _TEMPLATE_DIR.glob("*.html")) or [_DEFAULT_TEMPLATE]


def _safe(article: dict, key: str, fallback: str = "") -> str:
    return html.escape(str(article.get(key) or fallback))


def _load_template(name: str) -> str:
    path = _TEMPLATE_DIR / f"{name}.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    # fallback: 인라인 기본 템플릿
    return (
        '<div class="cn-card cn-{template}">'
        '  <div class="cn-meta"><span class="cn-press">{press}</span>'
        '    <span class="cn-date">{date}</span></div>'
        '  <h1 class="cn-title">{title}</h1>'
        '  <p class="cn-summary">{summary}</p>'
        '  <div class="cn-keywords">{keywords}</div>'
        "</div>"
    )


def render_html(article: dict, template: str = _DEFAULT_TEMPLATE) -> str:
    """기사 1건을 HTML 카드로 변환. 외부 문자열은 모두 escape."""
    tpl = _load_template(template)
    return tpl.format(
        template=html.escape(template),
        title=_safe(article, "title"),
        press=_safe(article, "press"),
        date=_safe(article, "date"),
        summary=_safe(article, "summary"),
        keywords=_safe(article, "keywords"),
    )


def render_png(
    article: dict,
    template: str = _DEFAULT_TEMPLATE,
    size: tuple[int, int] = CARD_SIZE_DEFAULT,
) -> bytes:
    """Pillow 로 카드 이미지(PNG bytes). Pillow 미설치 시 ImportError 명시."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise ImportError(
            "cardnews.render_png 는 Pillow 가 필요합니다. "
            "requirements.txt 에 'Pillow' 를 추가하세요."
        ) from exc

    img = Image.new("RGB", size, CARD_BG)
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("NotoSerifKR-Bold.otf", FONT_TITLE_SIZE)
        meta_font = ImageFont.truetype("IBMPlexSansKR-Regular.otf", FONT_META_SIZE)
    except OSError:
        title_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    x = CARD_PAD
    y = CARD_PAD
    press = article.get("press") or ""
    date = article.get("date") or ""
    title = article.get("title") or ""

    if press or date:
        draw.text((x, y), f"{press}   {date}".strip(), fill=CARD_ACCENT, font=meta_font)
        y += FONT_META_SIZE + 24

    # 간이 wrap (정밀 타이포는 후속 이슈)
    max_chars = max(1, (size[0] - 2 * CARD_PAD) // (FONT_TITLE_SIZE // 2))
    for i in range(0, len(title), max_chars):
        draw.text((x, y), title[i : i + max_chars], fill=CARD_TEXT, font=title_font)
        y += FONT_TITLE_SIZE + 12

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_deck(
    articles: list[dict],
    template: str = _DEFAULT_TEMPLATE,
) -> list[bytes]:
    """다수 기사를 PNG bytes 리스트로."""
    return [render_png(a, template=template) for a in articles]

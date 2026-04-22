import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, urljoin, urlparse
from collections import Counter

# ── HTML 파서 선택 ──────────────────────────────────────
# lxml이 설치돼 있으면 속도를 위해 사용, 아니면 표준 html.parser로 fallback.
try:
    import lxml  # noqa: F401
    _HTML_PARSER = "lxml"
except ImportError:
    _HTML_PARSER = "html.parser"


def _soup(markup: str) -> BeautifulSoup:
    return BeautifulSoup(markup, _HTML_PARSER)

# ── User-Agent 풀 ──────────────────────────────────────────
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# 매직 넘버 상수화
MIN_TITLE_LEN = 15
MIN_CONTENT_LEN = 80
MAX_BODY_PREVIEW = 300
REQUEST_TIMEOUT = 15
MAX_CONTENT_WORKERS = 4


def _headers():
    return {
        "User-Agent": random.choice(UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        "Referer": "https://search.naver.com/",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Upgrade-Insecure-Requests": "1"
    }


def _build_session() -> requests.Session:
    """429/5xx에 대해 지수 백오프로 재시도하는 requests 세션."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ── 뉴스 목록 셀렉터 ──────────────────────────────────────
LIST_SELECTORS = [
    "div.fds-news-item-list-tab > div", "ul.list_news > li.bx",
    "div[class*='fds-news-item-list-tab'] > div", "div[class*='fds-news-item']",
    "ul.list_news_infinite_list > li", "ul[class*='list_news'] > li",
    "div.news_wrap", "div.news_area", "li.bx", "div.item_news",
]

TITLE_SELECTORS = ["a.news_tit", "a[class*='news_tit']", "a[class*='title']", "a[class*='tit']"]
PRESS_SELECTORS = ["span[class*='press']", "a[class*='press']", "a.info.press", "span.info.press", "a.press"]
DATE_SELECTORS  = ["span[class*='time']", "span[class*='date']", "span.info", "i.time"]
DESC_SELECTORS  = ["div[class*='dsc']", "div[class*='desc']", "div[class*='summary']", "div.news_dsc", "div.dsc_wrap", "a.api_txt_lines"]

# ── 키워드 추출 로직 ──────────────────────────────────────
STOPWORDS = {
    "기자", "연합뉴스", "뉴스", "사진", "무단전재", "재배포", "금지", "특파원", "이", "그", "저",
    "것", "수", "등", "및", "하는", "있는", "위해", "대해", "관련", "이번", "가운데", "따르면",
    "대비", "했다", "결과", "대해서", "통해", "위한", "비해", "경우", "때문에", "따라", "최근", "대한", "가장",
    "오늘", "내일", "어제", "올해", "작년", "지난", "이날", "당시", "현재", "지금", "이후", "이전",
    "보도", "기사", "취재", "발표", "전했다", "밝혔다", "말했다", "설명했다", "이라고",
    "있다", "없다", "된다", "한다", "있습니다",
}


def extract_keywords(text: str, top_n: int = 5) -> str:
    if not text:
        return ""
    words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
    filtered = [w for w in words if len(w) > 1 and w not in STOPWORDS]
    if not filtered:
        return ""
    counter = Counter(filtered)
    keywords = [word for word, _ in counter.most_common(top_n)]
    return ", ".join(keywords)


# ── 헬퍼 함수 ─────────────────────────────────────────────
def _first_text(parent, selectors: list) -> str:
    for sel in selectors:
        tag = parent.select_one(sel)
        if tag:
            return tag.get_text(strip=True)
    return ""


def _first_tag(parent, selectors: list):
    for sel in selectors:
        tag = parent.select_one(sel)
        if tag:
            return tag
    return None


def _find_news_items(soup: BeautifulSoup, debug: bool = False) -> list:
    """LIST_SELECTORS를 순서대로 시도해 2개 이상 매치되는 첫 셀렉터를 채택.
    2개 이상이 전혀 없으면 1개라도 매치되는 것, 그래도 없으면 fender 루트 fallback."""
    first_single = []
    for sel in LIST_SELECTORS:
        items = soup.select(sel)
        if debug and items:
            print(f"[_find_news_items] '{sel}' → {len(items)}건")
        if len(items) >= 2:
            return items
        if not first_single and items:
            first_single = items
    if first_single:
        return first_single

    fender_roots = soup.select("div[data-fender-root]")
    if fender_roots:
        items = [r for r in fender_roots if r.find("a", href=lambda h: h and h.startswith("http"))]
        if debug:
            print(f"[_find_news_items] fender fallback → {len(items)}건")
        if items:
            return items
    if debug:
        print("[_find_news_items] 매치된 셀렉터 없음")
    return []


# ── 1. 네이버 뉴스 검색 로직 ─────────────────────────────────────
def search_naver_news(keyword: str, max_results: int = 10, debug: bool = False) -> list[dict]:
    encoded = quote(keyword)
    url = f"https://search.naver.com/search.naver?where=news&sm=tab_jum&query={encoded}&sort=1"

    session = _build_session()
    try:
        session.get("https://www.naver.com", headers=_headers(), timeout=8)
        time.sleep(random.uniform(0.3, 0.6))
        resp = session.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"네이버 검색 요청 실패: {e}")

    soup = _soup(resp.text)
    items = _find_news_items(soup, debug=debug)
    if debug:
        print(f"[search_naver_news] 후보 아이템 {len(items)}건, max_results={max_results}")
    articles = []
    seen_links = set()

    for item in items[:max_results * 2]:
        if len(articles) >= max_results:
            break
        try:
            title_tag = _first_tag(item, TITLE_SELECTORS)
            if not title_tag:
                for a in item.find_all("a", href=True):
                    href = a.get("href", "")
                    txt = a.get_text(strip=True)
                    if href.startswith("http") and len(txt) > 10:
                        title_tag = a
                        break

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            original_link = title_tag.get("href", "")

            best_link = original_link
            for a in item.find_all("a", href=True):
                txt = a.get_text(strip=True)
                if txt == "네이버뉴스" and "n.news.naver.com" in a.get("href", ""):
                    best_link = a.get("href")
                    break

            if best_link in seen_links:
                continue
            seen_links.add(best_link)

            press = _first_text(item, PRESS_SELECTORS)

            date_str = ""
            for sel in DATE_SELECTORS:
                tags = item.select(sel)
                for tag in tags:
                    txt = tag.get_text(strip=True)
                    if any(x in txt for x in ["전", "분", "시간", "일", ".", ":"]) and len(txt) < 30:
                        date_str = txt
                        break
                if date_str:
                    break

            summary = _first_text(item, DESC_SELECTORS)

            img_url = ""
            for img in item.find_all("img"):
                src = img.get("data-lazysrc") or img.get("data-src") or img.get("src", "")
                if src and src.startswith("http"):
                    if "logo" not in src.lower() and "favicon" not in src.lower():
                        img_url = src
                        break

            articles.append({
                "title":   title,
                "press":   press,
                "date":    date_str,
                "link":    best_link,
                "summary": summary,
                "content": "",
                "keywords": "",
                "img_url": img_url,
            })
        except Exception:
            continue

    return articles


# ── 2. 타겟 기술 사이트 메인 홈페이지 스크래핑 로직 ────────────────
# 명백한 네비게이션/비기사 경로만 차단 (과도하게 막지 않도록 최소화)
_NAV_BLOCKLIST = (
    "javascript:", "mailto:", "tel:",
    "/login", "/logout", "/signup", "/join", "/member/join",
    "/privacy", "/terms", "/policy", "/sitemap", "/rss",
    "/tag/", "/tags/", "/category/", "/categories/", "/cat/",
    "/search?", "/search.",
)


def _root_domain(host: str) -> str:
    """www. 접두사를 떼어낸 루트 도메인 반환."""
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def _same_root_domain(candidate_host: str, site_host: str) -> bool:
    if not candidate_host:
        return True  # 상대 경로는 허용
    root = _root_domain(site_host)
    cand = _root_domain(candidate_host)
    return cand == root or cand.endswith("." + root)


def _is_plausible_article_link(href: str, site_host: str) -> bool:
    """최소한의 도메인/네비게이션 필터만 적용. 제목 길이로 대부분 걸러진다는 가정."""
    if not href:
        return False
    lower = href.lower()
    if any(bad in lower for bad in _NAV_BLOCKLIST):
        return False
    if href.startswith("#"):
        return False
    try:
        parsed = urlparse(href)
    except ValueError:
        return False
    if not _same_root_domain(parsed.netloc, site_host):
        return False
    # 경로가 너무 짧으면(홈, 루트 등) 제외
    path = (parsed.path or "").rstrip("/")
    if len(path) < 2:
        return False
    return True


def fetch_latest_tech_news(site_name: str, site_url: str, max_results: int = 10, debug: bool = False) -> list[dict]:
    session = _build_session()
    site_host = urlparse(site_url).netloc
    try:
        time.sleep(random.uniform(0.5, 1.2))
        resp = session.get(site_url, headers=_headers(), timeout=REQUEST_TIMEOUT)
        # raise_for_status는 생략 — 일부 사이트가 비정상 코드여도 유효 HTML을 반환하는 경우 존재
        if resp.status_code >= 400:
            if debug:
                print(f"[{site_name}] HTTP {resp.status_code} 수신 — 파싱 계속 시도")

        soup = _soup(resp.text)
        all_anchors = soup.find_all("a", href=True)
        if debug:
            print(f"[{site_name}] 전체 앵커 {len(all_anchors)}개 스캔")

        articles = []
        seen_links = set()
        seen_titles = set()
        rejected = {"short_title": 0, "not_plausible": 0, "dup": 0}

        for a in all_anchors:
            if len(articles) >= max_results:
                break

            href = a.get("href")
            title = a.get_text(strip=True)

            if len(title) <= MIN_TITLE_LEN or title in seen_titles:
                rejected["short_title"] += 1
                continue

            full_link = urljoin(site_url, href)
            if full_link in seen_links:
                rejected["dup"] += 1
                continue
            if not _is_plausible_article_link(full_link, site_host):
                rejected["not_plausible"] += 1
                continue

            img_url = ""
            parent = a.find_parent(['div', 'li', 'article'])
            if parent:
                for img in parent.find_all('img'):
                    src = img.get("data-lazysrc") or img.get("data-src") or img.get("src", "")
                    if src and not src.startswith("data:image"):
                        img_url = urljoin(site_url, src)
                        break

            seen_links.add(full_link)
            seen_titles.add(title)

            articles.append({
                "title": title,
                "press": site_name,
                "date": "최신 동향",
                "link": full_link,
                "summary": "",
                "content": "",
                "keywords": "",
                "img_url": img_url
            })

        if debug:
            print(f"[{site_name}] 수집 {len(articles)}건, 거부: {rejected}")
        return articles
    except Exception as e:
        if debug:
            print(f"[{site_name}] 크롤링 실패: {type(e).__name__}: {e}")
        return []


# ── 기사 본문 및 고화질 이미지 추출 ────────────────────────
CONTENT_SELECTORS = [
    "div#dic_area", "div#articleBodyContents", "div.newsct_article", "div._article_body_contents",
    "div#cnbc-front-articleContent-area-font", "div.ab_text",
    "div[itemprop='articleBody']", "article[itemprop='articleBody']", "div.editor-p",
    "div#aticle_txt", "div#article_txt", "div.text_area", "div.article_cont", "div.news_cnt_detail",
    "div#cont_newstext", "div.detail-body", "div.news_txt", "div.article_content",
    "div.v_article", "div.art_txt", "div.view_con", "div#articleBody", "article#articleBody",
    "div.article_body", "div.article-body", "div#news_body_id", "div.news_body",
    "div#content-body", "div.news_content", "div.txt_article", "div.atc_body", "div.article_view",
]


def fetch_article_content(url: str) -> tuple:
    if not url or not url.startswith("http"):
        return "", ""
    session = _build_session()
    try:
        time.sleep(random.uniform(0.3, 0.8))
        resp = session.get(url, headers=_headers(), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        if resp.encoding is None or resp.encoding.lower() == 'iso-8859-1':
            resp.encoding = resp.apparent_encoding

        soup = _soup(resp.text)

        og_img = soup.find("meta", property="og:image")
        high_res_img = og_img["content"] if og_img and og_img.get("content") else ""

        for noise in soup.select("script, style, .ad, .advertisement, figure, figcaption, header, footer, nav, .header, .footer"):
            noise.decompose()

        for sel in CONTENT_SELECTORS:
            tag = soup.select_one(sel)
            if tag:
                text = tag.get_text(separator=" ", strip=True)
                text = re.sub(r"\s{2,}", " ", text)
                if len(text) > 50:
                    return text, high_res_img

        paragraphs = [p.get_text(strip=True) for p in soup.select("p") if len(p.get_text(strip=True)) > 30]
        if paragraphs:
            text = " ".join(paragraphs)
            if len(text) > MIN_CONTENT_LEN:
                return text, high_res_img

        best_text = ""
        candidates = soup.find_all(['div', 'article', 'section'])

        for tag in candidates:
            if len(tag.find_all('a')) > 8:
                continue
            text = tag.get_text(separator=" ", strip=True)
            text = re.sub(r"\s{2,}", " ", text)
            if len(text) > len(best_text):
                best_text = text

        if len(best_text) > MIN_CONTENT_LEN:
            return best_text, high_res_img

        return "본문을 가져올 수 없습니다. (동적 페이지 로딩 혹은 완전히 차단된 페이지)", high_res_img

    except Exception as e:
        return f"본문 로드 실패: {str(e)[:80]}", ""


def enrich_articles_parallel(articles: list, progress_cb=None, max_workers: int = MAX_CONTENT_WORKERS) -> list:
    """여러 기사의 본문/이미지/키워드를 병렬로 채워 넣는다.

    progress_cb: 진행률 콜백. (done, total, article) 형태로 호출된다.
    입력 리스트를 in-place로 갱신하며 동일 리스트를 반환한다(순서 유지).
    """
    total = len(articles)
    if total == 0:
        return articles

    def _work(idx_art):
        idx, art = idx_art
        if art.get("link"):
            content, high_res_img = fetch_article_content(art["link"])
            art["content"] = content
            if high_res_img:
                art["img_url"] = high_res_img
            art["keywords"] = extract_keywords(content)
        return idx, art

    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_work, (i, art)) for i, art in enumerate(articles)]
        for fut in as_completed(futures):
            try:
                _idx, art = fut.result()
            except Exception:
                art = None
            done += 1
            if progress_cb:
                try:
                    progress_cb(done, total, art)
                except Exception:
                    pass
    return articles


def articles_to_dataframe(articles: list[dict]) -> pd.DataFrame:
    if not articles:
        return pd.DataFrame()
    df = pd.DataFrame(articles)
    col_map = {
        "title":   "제목", "press":   "언론사", "date":    "발행일시",
        "link":    "링크", "keywords": "추출키워드", "summary": "요약", "content": "본문내용", "img_url": "이미지URL"
    }
    existing = [c for c in col_map if c in df.columns]
    df = df[existing].rename(columns={c: col_map[c] for c in existing})
    df.index = range(1, len(df) + 1)
    df.index.name = "번호"
    return df

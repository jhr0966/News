import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from urllib.parse import quote
from collections import Counter

# ── User-Agent 풀 ──────────────────────────────────────────
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

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
    "대비", "했다", "결과", "대해서", "통해", "위한", "비해", "경우", "때문에", "따라", "최근", "대한", "가장"
}

def extract_keywords(text: str, top_n: int = 5) -> str:
    if not text: return ""
    words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
    filtered = [w for w in words if len(w) > 1 and w not in STOPWORDS]
    if not filtered: return ""
    counter = Counter(filtered)
    keywords = [word for word, count in counter.most_common(top_n)]
    return ", ".join(keywords)

# ── 헬퍼 함수 ─────────────────────────────────────────────
def _first_text(parent, selectors: list) -> str:
    for sel in selectors:
        tag = parent.select_one(sel)
        if tag: return tag.get_text(strip=True)
    return ""

def _first_tag(parent, selectors: list):
    for sel in selectors:
        tag = parent.select_one(sel)
        if tag: return tag
    return None

def _find_news_items(soup: BeautifulSoup, debug: bool = False) -> list:
    for sel in LIST_SELECTORS:
        items = soup.select(sel)
        if len(items) >= 1: return items
    fender_roots = soup.select("div[data-fender-root]")
    if fender_roots:
        items = [r for r in fender_roots if r.find("a", href=lambda h: h and h.startswith("http"))]
        if items: return items
    return []

# ── 메인 뉴스 검색 로직 ─────────────────────────────────────
def search_naver_news(keyword: str, max_results: int = 10, debug: bool = False) -> list[dict]:
    encoded = quote(keyword)
    url = f"https://search.naver.com/search.naver?where=news&sm=tab_jum&query={encoded}&sort=1"

    try:
        session = requests.Session()
        session.get("https://www.naver.com", headers=_headers(), timeout=8)
        time.sleep(random.uniform(0.3, 0.6))
        resp = session.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"네이버 검색 요청 실패: {e}")

    soup = BeautifulSoup(resp.text, "lxml")
    items = _find_news_items(soup, debug=debug)
    articles = []
    seen_links = set()

    for item in items[:max_results * 2]:
        if len(articles) >= max_results: break
        try:
            title_tag = _first_tag(item, TITLE_SELECTORS)
            if not title_tag:
                for a in item.find_all("a", href=True):
                    href = a.get("href", "")
                    txt  = a.get_text(strip=True)
                    if href.startswith("http") and len(txt) > 10:
                        title_tag = a
                        break

            if not title_tag: continue

            title = title_tag.get_text(strip=True)
            original_link = title_tag.get("href", "")
            
            best_link = original_link
            for a in item.find_all("a", href=True):
                txt = a.get_text(strip=True)
                if txt == "네이버뉴스" and "n.news.naver.com" in a.get("href", ""):
                    best_link = a.get("href")
                    break

            if best_link in seen_links: continue
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
                if date_str: break

            summary = _first_text(item, DESC_SELECTORS)

            # 저화질 썸네일(임시용) 추출
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

# ── 기사 본문 추출 ────────────────────────
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

# ✅ 텍스트와 함께 '고화질 이미지(og:image)'를 반환하도록 변경
def fetch_article_content(url: str) -> tuple:
    if not url or not url.startswith("http"): return "", ""
    try:
        time.sleep(random.uniform(0.5, 1.2))
        resp = requests.get(url, headers=_headers(), timeout=15)
        
        if resp.encoding is None or resp.encoding.lower() == 'iso-8859-1':
            resp.encoding = resp.apparent_encoding

        soup = BeautifulSoup(resp.text, "lxml")
        
        # ✅ 카카오톡 공유용 등에 쓰이는 고화질 원본 이미지 URL 추출
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
            if len(text) > 80:
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

        if len(best_text) > 80:
            return best_text, high_res_img

        return "본문을 가져올 수 없습니다. (동적 페이지 로딩 혹은 완전히 차단된 페이지)", high_res_img
        
    except Exception as e:
        return f"본문 로드 실패: {str(e)[:80]}", ""

def articles_to_dataframe(articles: list[dict]) -> pd.DataFrame:
    if not articles: return pd.DataFrame()
    df = pd.DataFrame(articles)
    col_map = {
        "title":   "제목", "press":   "언론사", "date":    "발행일시",
        "link":    "링크", "keywords":"추출키워드", "summary": "요약", "content": "본문내용", "img_url": "이미지URL"
    }
    existing = [c for c in col_map if c in df.columns]
    df = df[existing].rename(columns={c: col_map[c] for c in existing})
    df.index = range(1, len(df) + 1)
    df.index.name = "번호"
    return df
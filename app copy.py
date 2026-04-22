import streamlit as st
import pandas as pd
import io
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from scraper import search_naver_news, fetch_article_content, extract_keywords, articles_to_dataframe, _headers

def _show_debug():
    log = st.session_state.debug_log
    if log:
        st.markdown(f'<div class="debug-box">{log}</div>', unsafe_allow_html=True)
    else:
        st.info("디버그 체크박스를 켜고 검색하면 셀렉터 탐색 과정이 여기에 표시됩니다.")

    st.markdown("---")
    st.markdown("#### 🛠 셀렉터 자가진단")
    diag_kw = st.text_input("진단용 키워드", value=st.session_state.keyword or "인공지능", key="diag_kw")
    if st.button("🔍 HTML 구조 진단 실행", key="diag_btn"):
        with st.spinner("네이버 HTML 분석 중..."):
            try:
                encoded = quote(diag_kw)
                url = f"https://search.naver.com/search.naver?where=news&query={encoded}&sort=1"
                sess = requests.Session()
                sess.get("https://www.naver.com", headers=_headers(), timeout=8)
                import time as _t; _t.sleep(0.5)
                resp = sess.get(url, headers=_headers(), timeout=10)
                soup = BeautifulSoup(resp.text, "lxml")

                found = {}
                for tag in soup.find_all(True):
                    for cls in tag.get("class", []):
                        if any(x in cls.lower() for x in ["news","article","bx","result","item","wrap","tit","press","info","dsc"]):
                            found[cls] = found.get(cls, 0) + 1

                sorted_cls = sorted(found.items(), key=lambda x: -x[1])
                lines = [f"  {cnt:>4}회  .{cls}" for cls, cnt in sorted_cls[:50]]
                st.markdown(
                    f'<div class="debug-box">HTTP {resp.status_code} | {len(resp.text)} bytes\n\n'
                    f'뉴스 관련 클래스 (빈도순):\n' + "\n".join(lines) + "</div>",
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"진단 실패: {e}")

# ─────────────────────────────────────────────
# 페이지 설정 및 전역 CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="네이버 뉴스 스크래퍼", page_icon="📰", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&family=IBM+Plex+Sans+KR:wght@300;400;500;600&display=swap');

:root {
    --accent:    #1D6FE8;
    --bg:        #F7F6F2;
    --card-bg:   #FFFFFF;
    --border:    #E2E0D8;
    --text-1:    #1A1918;
    --text-2:    #5A5854;
    --text-3:    #9A9690;
    --green:     #1A8C5B;
    --tag-bg:    #EEF3FD;
    --tag-txt:   #1D6FE8;
}

.stApp { background: var(--bg) !important; }
.block-container { padding: 2rem 3rem !important; max-width: 1400px !important; }

.header-wrap {
    display: flex; align-items: baseline; gap: 14px;
    border-bottom: 3px solid var(--text-1);
    padding-bottom: 10px; margin-bottom: 2rem;
}
.header-logo { font-family: 'Noto Serif KR', serif; font-size: 2rem; font-weight: 700; color: var(--text-1); letter-spacing: -0.03em; }
.header-sub { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.82rem; color: var(--text-3); font-weight: 300; letter-spacing: 0.04em; }

.stTextInput > div > div > input {
    font-family: 'IBM Plex Sans KR', sans-serif !important; font-size: 1rem !important;
    border: 2px solid var(--border) !important; border-radius: 6px !important;
    background: var(--card-bg) !important; padding: 0.65rem 1rem !important; color: var(--text-1) !important;
}
.stTextInput > div > div > input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(29,111,232,.1) !important; }

.stButton > button {
    font-family: 'IBM Plex Sans KR', sans-serif !important; font-weight: 600 !important; font-size: 0.9rem !important;
    background: var(--text-1) !important; color: #fff !important; border: none !important; border-radius: 6px !important;
    padding: 0.6rem 1.6rem !important; transition: background .2s;
}
.stButton > button:hover { background: var(--accent) !important; }

.news-card {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.25rem 1.3rem; margin-bottom: 1.1rem; transition: box-shadow .2s, transform .2s;
    display: flex; flex-direction: column; box-shadow: 0 1px 3px rgba(0,0,0,.04); min-height: 280px;
}
.news-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,.09); transform: translateY(-2px); }

/* ✅ 이미지 스타일 - 16:9 와이드 비율로 자동 조정 (정사각형 크롭 방지) */
.card-img {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    border-radius: 6px;
    margin-bottom: 1rem;
    background-color: #f1f3f5;
    border: 1px solid var(--border);
}
.card-img-placeholder {
    width: 100%;
    aspect-ratio: 16 / 9;
    border-radius: 6px;
    margin-bottom: 1rem;
    background-color: #f1f3f5;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-3);
    font-size: 0.8rem;
    font-family: 'IBM Plex Sans KR', sans-serif;
    border: 1px solid var(--border);
}

.card-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 0.65rem; flex-wrap: wrap; }
.card-press { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.72rem; font-weight: 600; background: var(--tag-bg); color: var(--tag-txt); padding: 2px 8px; border-radius: 20px; }
.card-date { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.72rem; color: var(--text-3); font-weight: 300; }
.card-num { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.72rem; color: var(--text-3); margin-left: auto; }
.card-title { font-family: 'Noto Serif KR', serif; font-size: 0.95rem; font-weight: 700; color: var(--text-1); line-height: 1.55; margin-bottom: 0.6rem; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

/* 키워드 뱃지 스타일 */
.card-keywords { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 0.8rem; }
.keyword-badge { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.7rem; background-color: #F1F5F9; color: #475569; padding: 3px 8px; border-radius: 4px; border: 1px solid #E2E8F0; }

.card-body { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.82rem; color: var(--text-2); line-height: 1.7; flex: 1; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 0.9rem; }
.card-link a { font-family: 'IBM Plex Sans KR', sans-serif; font-size: 0.78rem; font-weight: 600; color: var(--accent); text-decoration: none; }

.result-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; padding: 0.8rem 1rem; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; font-family: 'IBM Plex Sans KR', sans-serif; }
.result-kw { font-size: 1.05rem; font-weight: 600; color: var(--accent); }
.result-count { font-size: 0.85rem; color: var(--text-2); }
.result-badge { margin-left: auto; font-size: 0.72rem; color: var(--green); font-weight: 500; background: #EBF7F2; padding: 3px 10px; border-radius: 20px; }

.stProgress > div > div > div { background: var(--accent) !important; }
hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
.stTabs [data-baseweb="tab"] { font-family: 'IBM Plex Sans KR', sans-serif !important; font-size: 0.88rem !important; font-weight: 500 !important; }
.debug-box { background: #0D1117; color: #C9D1D9; font-family: monospace; font-size: 0.8rem; padding: 1rem; border-radius: 8px; white-space: pre-wrap; line-height: 1.6; max-height: 400px; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 헤더 & 세션 상태
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-wrap">
    <span class="header-logo">📰 뉴스 스크래퍼</span>
    <span class="header-sub">NAVER NEWS · 최신순 · 카드뉴스 뷰어</span>
</div>
""", unsafe_allow_html=True)

for k, v in [("articles", []), ("keyword", ""), ("debug_log", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# 검색 UI
# ─────────────────────────────────────────────
col_inp, col_btn, col_opt, col_debug = st.columns([4, 1, 1, 1])

with col_inp:
    keyword = st.text_input("키워드", placeholder="검색할 키워드 (예: 인공지능, 기후변화...)", label_visibility="collapsed")
with col_btn:
    search_clicked = st.button("검색", use_container_width=True)
with col_opt:
    max_results = st.selectbox("수집 건수", [5, 10, 15, 20, 30], index=1, label_visibility="visible")
with col_debug:
    debug_mode = st.checkbox("🔧 디버그", value=False)

# ─────────────────────────────────────────────
# 스크래핑 실행
# ─────────────────────────────────────────────
if search_clicked and keyword.strip():
    st.session_state.keyword  = keyword.strip()
    st.session_state.articles = []
    st.session_state.debug_log = ""
    collected = []

    import io as _io, contextlib
    status_box = st.empty()
    prog_bar   = st.progress(0)

    status_box.markdown(f"🔍 **'{keyword}'** 검색 중...")

    try:
        log_buf = _io.StringIO()
        with contextlib.redirect_stdout(log_buf):
            arts_list = search_naver_news(keyword.strip(), max_results=max_results, debug=debug_mode)

        st.session_state.debug_log = log_buf.getvalue()

        if not arts_list:
            status_box.empty(); prog_bar.empty()
            st.warning("⚠️ 검색 결과 0건 — 브라우저로 직접 확인 후 셀렉터를 수정해 주세요.")
        else:
            total = len(arts_list)
            for i, art in enumerate(arts_list):
                if art["link"]:
                    # ✅ 고화질 이미지를 함께 받아오도록 처리
                    content, high_res_img = fetch_article_content(art["link"])
                    art["content"] = content
                    if high_res_img:
                        art["img_url"] = high_res_img  # 저화질 썸네일 덮어쓰기
                    art["keywords"] = extract_keywords(content)
                collected.append(art)
                prog_bar.progress(int((i + 1) / total * 100))
                status_box.markdown(f"📄 기사 수집 중 **{i+1}/{total}** — {art.get('title','')[:40]}...")

            st.session_state.articles = collected
            status_box.empty(); prog_bar.empty()
            st.success(f"✅ **{len(collected)}건** 수집 완료!")

    except RuntimeError as e:
        status_box.empty(); prog_bar.empty()
        st.error(f"❌ 오류 발생: {e}")

elif search_clicked and not keyword.strip():
    st.warning("키워드를 입력해 주세요.")

# ─────────────────────────────────────────────
# 결과 렌더링 & 필터링 로직
# ─────────────────────────────────────────────
if st.session_state.articles:
    articles = st.session_state.articles
    kw       = st.session_state.keyword

    all_kws = set()
    for art in articles:
        if art.get("keywords"):
            for k in art["keywords"].split(","):
                if k.strip(): all_kws.add(k.strip())
    
    st.markdown("##### 🏷️ 키워드 필터링")
    selected_kws = st.multiselect(
        "기사에서 추출된 핵심 단어로 결과를 필터링해보세요.",
        options=sorted(list(all_kws)),
        default=[]
    )

    if selected_kws:
        filtered_articles = []
        for art in articles:
            art_kws = [k.strip() for k in art.get("keywords", "").split(",") if k.strip()]
            if any(k in art_kws for k in selected_kws):
                filtered_articles.append(art)
    else:
        filtered_articles = articles

    df = articles_to_dataframe(filtered_articles)

    st.markdown(f"""
    <div class="result-bar">
        <span style="font-size:.85rem;color:var(--text-2);">검색어</span>
        <span class="result-kw">"{kw}"</span>
        <span class="result-count">— 총 {len(articles)}건 중 {len(filtered_articles)}건 표시</span>
        <span class="result-badge">최신순</span>
    </div>
    """, unsafe_allow_html=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, encoding="utf-8-sig")
    st.download_button(
        label="⬇ CSV 다운로드",
        data=csv_buf.getvalue().encode("utf-8-sig"),
        file_name=f"naver_news_{kw}_filtered_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    tab_card, tab_table, tab_debug = st.tabs(["🗞 카드뉴스", "📊 데이터 테이블", "🔧 디버그"])

    # ── 카드뉴스 탭 ──
    with tab_card:
        if not filtered_articles:
            st.info("선택한 키워드가 포함된 기사가 없습니다.")
        else:
            cols_per_row = 3
            rows = [filtered_articles[i:i+cols_per_row] for i in range(0, len(filtered_articles), cols_per_row)]
            for row in rows:
                cols = st.columns(cols_per_row, gap="medium")
                for col, art in zip(cols, row):
                    with col:
                        title   = art.get("title", "제목 없음")
                        press   = art.get("press", "")
                        date    = art.get("date",  "")
                        link    = art.get("link",  "#")
                        summary = art.get("summary", "")
                        content = art.get("content", "")
                        img_url = art.get("img_url", "")
                        num     = articles.index(art) + 1

                        body_text = content if len(content) > 50 else summary
                        body_text = body_text[:300] + ("..." if len(body_text) > 300 else "")

                        keywords_str = art.get("keywords", "")
                        kw_html = ""
                        if keywords_str:
                            kw_list = keywords_str.split(',')
                            kw_badges = "".join([f'<span class="keyword-badge">#{k.strip()}</span>' for k in kw_list if k.strip()])
                            kw_html = f'<div class="card-keywords">{kw_badges}</div>'

                        press_html = f'<span class="card-press">{press}</span>' if press else ""
                        date_html  = f'<span class="card-date">{date}</span>'   if date  else ""
                        
                        if img_url:
                            img_html = f'<img src="{img_url}" class="card-img" alt="기사 썸네일">'
                        else:
                            img_html = f'<div class="card-img-placeholder">No Image</div>'

                        st.markdown(f"""
<div class="news-card">
{img_html}
<div class="card-meta">
{press_html}{date_html}
<span class="card-num">#{num}</span>
</div>
<div class="card-title">{title}</div>
{kw_html}
<div class="card-body">{body_text or '본문 내용 없음'}</div>
<div class="card-link"><a href="{link}" target="_blank">원문 보기 →</a></div>
</div>
""", unsafe_allow_html=True)

    # ── 테이블 탭 ──
    with tab_table:
        st.dataframe(
            df,
            use_container_width=True,
            height=500,
            column_config={
                "링크": st.column_config.LinkColumn("링크", display_text="열기"),
                "이미지URL": st.column_config.LinkColumn("이미지URL", display_text="보기"),
                "제목": st.column_config.TextColumn("제목", width="medium"),
                "본문내용": st.column_config.TextColumn("본문내용", width="large"),
                "추출키워드": st.column_config.TextColumn("추출키워드", width="medium"),
            },
        )

    # ── 디버그 탭 ──
    with tab_debug:
        _show_debug()

elif st.session_state.debug_log:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔧 디버그 로그")
    _show_debug()

# ─────────────────────────────────────────────
# 초기 안내
# ─────────────────────────────────────────────
if not st.session_state.articles and not st.session_state.debug_log:
    st.markdown("""
<div style="margin-top:4rem;text-align:center;font-family:'IBM Plex Sans KR',sans-serif;color:var(--text-3);">
    <div style="font-size:3rem;margin-bottom:1rem;">🔎</div>
    <div style="font-size:1.05rem;font-weight:500;color:var(--text-2);margin-bottom:.5rem;">
        키워드를 입력하고 검색 버튼을 눌러주세요
    </div>
    <div style="font-size:.85rem;">
        네이버 뉴스를 스크래핑하고 핵심 키워드를 자동 추출합니다.
    </div>
</div>
""", unsafe_allow_html=True)
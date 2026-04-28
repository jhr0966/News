# News

뉴스 스크래퍼 기반 3대 도메인 Streamlit 앱:

1. **🔍 뉴스 스크래핑** — 네이버 뉴스 검색 · 사이트별 최신 기사 수집 (`scraper.py`)
2. **📊 인사이트 보드** — 언론사 랭킹 · 키워드 빈도 · 일자별 트렌드 (`insights.py`)
3. **🎨 카드뉴스** — 기사를 카드형 HTML/PNG 로 렌더 (`cardnews.py`)

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

- Python ≥ 3.10
- 최초 실행 시 `lxml` 설치 실패 시 `html.parser` 로 자동 fallback (`scraper._pick_parser`).


## 빠른 개발 환경 세팅 (Streamlit)

```bash
./scripts/dev_setup.sh
source .venv/bin/activate
make run
```

또는 수동 설치:

```bash
make install
make run
```

- Streamlit 설정: `.streamlit/config.toml`
- 개발 운영 청사진: `docs/VIBE_CODING_BLUEPRINT.md`

## 개발 문서

| 문서 | 언제 읽나 |
|---|---|
| [`CLAUDE.md`](./CLAUDE.md) | 작업 시작 전 **항상** (단일 참조점) |
| [`DEV_GUIDELINES.md`](./DEV_GUIDELINES.md) | 라우팅 표 · 검증 명령 |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | 모듈 계약 · article 스키마 |
| [`docs/INVARIANTS.md`](./docs/INVARIANTS.md) | state/위젯 불변식 |
| [`docs/WORKFLOW.md`](./docs/WORKFLOW.md) | 브랜치 → 커밋 → 머지 루프 |
| [`docs/SESSIONS.md`](./docs/SESSIONS.md) | 이전 세션 복원 (상단 1개만) |
| [`CHANGELOG.md`](./CHANGELOG.md) | 릴리스 이력 |
| [`docs/VIBE_CODING_BLUEPRINT.md`](./docs/VIBE_CODING_BLUEPRINT.md) | 제품/아키텍처/개발전략 청사진 |
| [`docs/DEVELOPMENT_PHASES.md`](./docs/DEVELOPMENT_PHASES.md) | Streamlit + Local First 단계별 실행 계획 |

## 배포

Streamlit Cloud 가 `main` 브랜치를 트래킹 — **`main` 머지 = 즉시 배포**.
작업은 반드시 브랜치에서:

```bash
git checkout -b <category>-<slug>    # fix|feat|refactor|style|docs|chore
```

## 커밋 전 검증

```bash
python -m py_compile app.py scraper.py insights.py cardnews.py
grep -nE 'on_click\s*=' app.py                                # 0
grep -nE 'requests\.(get|post|Session)\(' scraper.py          # _build_session 내부 1건만
```

## 페이지 스모크 테스트

지금까지 개발된 4개 페이지(네이버 검색/최신 기술 동향/인사이트 보드/카드뉴스)가
최소 렌더링에서 크래시 없이 뜨는지 자동으로 검사할 수 있습니다.

```bash
make test
```

개별 실행:

```bash
pytest -q tests/test_app_pages_smoke.py
```

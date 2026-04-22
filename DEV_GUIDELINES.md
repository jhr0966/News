# SOTONG_M 개발 지침

> CLAUDE.md의 규칙을 정리한 개발자용 요약 문서.

## 1. 토큰 절약 규칙 (최우선)

1. **코드 파일은 수정 대상만 읽는다.** "전체 파악"을 위해 모든 파일을 읽지 마라.
2. **docs/는 라우팅 표에 해당하는 문서만 1개 읽는다.** 2개 이상 동시에 읽지 마라.
3. **SESSIONS.md는 상단 1개 세션만.** 전체를 읽지 마라.
4. **단순 수정은 해당 파일만 읽고 바로 수정.** 관련 없는 파일 탐색 금지.
5. **읽기 전에 자문**: "이 파일을 안 읽으면 작업이 불가능한가?" — 아니면 읽지 마라.

## 2. 파일별 줄 수 및 읽는 시점

| 파일 | 줄 수 | 언제 읽나 |
|---|---|---|
| `app.py` | 388 | app.py 수정 시에만 |
| `translator.py` | 140 | 번역 로직 수정 시에만 |
| `assets/styles.css` | 208 | CSS 수정 시에만 |
| `components/bottombar/index.html` | 134 | 바텀바/언어선택/단문 마이크 수정 시 |
| `components/realtime_chat/index.html` | 271 | 실시간 통역 UI/STT 수정 시 |
| `docs/INVARIANTS.md` | 254 | state/위젯 관련 작업 시에만 |
| `docs/ARCHITECTURE.md` | 270 | 아키텍처 이해 필요 시에만 |
| `docs/WORKFLOW.md` | 220 | 멀티에이전트 워크플로 시에만 |
| `docs/SESSIONS.md` | 264 | 이전 세션 복원 시에만 (상단 1개만) |
| `CHANGELOG.md` | 280 | 릴리스/버전 작업 시에만 |

## 3. 라우팅 표

| 작업 | 읽을 파일 (이것만) |
|---|---|
| app.py UI 수정 | `app.py` |
| CSS/스타일 수정 | `assets/styles.css` |
| 번역 로직 수정 | `translator.py` |
| 단문 페이지 마이크/언어 선택 수정 | `components/bottombar/index.html` |
| 실시간 통역 UI/STT 수정 | `components/realtime_chat/index.html` + `app.py` (realtime 블록) |
| state/위젯 버그 | `app.py` + `docs/INVARIANTS.md` |
| 새 기능 추가 (BE) | `app.py` + `docs/INVARIANTS.md` |
| 아키텍처 파악 | `docs/ARCHITECTURE.md` |
| 이전 세션 복원 | `docs/SESSIONS.md` (상단 1개) |
| 릴리스/버전 | `CHANGELOG.md` |
| 단순 문답 | **CLAUDE.md 만으로 충분** |

## 4. 불변 규칙 요약

자세한 내용: [`docs/INVARIANTS.md`](./INVARIANTS.md)

- **I-1** STT 결과 쓰기는 `_stt_pending` 플래그로 다음 run 최상단에서만 (text_area 인스턴스화 이전).
- **I-2** 위젯 state 쓰기는 최상단 pending-flag 핸들러에서만.
- **I-3** `on_click=` 금지. `if st.button():` + `_do_*` 플래그 + `st.rerun()`.
- **I-5** `_cached_translate`가 유일한 번역 진입점.
- **I-7** `app.py`는 평탄 스크립트. `render_*` 마크업 헬퍼 금지.
- **I-12** 실시간 통역 state 는 `rt_` prefix 네임스페이스, pending 은 `_rt_` prefix.
- **I-13** 실시간 utterance 는 id 기반 idempotent (중복 emit 방어).

## 5. 브랜치 전략

- **`main`**: 안정 코드만. 직접 push 금지. 머지만 허용.
- **작업 브랜치**: 수정 요청마다 별도 브랜치. Streamlit Cloud 테스트 후 main 머지.
- **네이밍**: `<카테고리>-<설명>` (슬래시 금지, 하이픈 구분)
  - `fix-grey-button`
  - `feat-history`
  - `style-unify-buttons`
  - `refactor-reset`
  - `docs-invariants`

## 6. 검증 (커밋 전 필수)

```bash
python -m py_compile app.py translator.py
grep -nE 'on_click\s*=|render_mic|render_input_card' app.py   # 0 매치
```

## 7. 변경 시 갱신

작업 브랜치의 같은 커밋에서 다음을 함께 업데이트:

1. `CHANGELOG.md` [Unreleased] 섹션에 엔트리 추가
2. `docs/SESSIONS.md` 상단에 세션 항목 추가
3. 새로운 invariant 발생 시 → `docs/INVARIANTS.md`에 추가

## 8. 스택

- **Streamlit** ≥ 1.32 · `app.py` 단일 평탄 스크립트
- **Langbly API** (Google Translate v2 호환) · `translator.py`
- **`assets/styles.css`** · Pretendard · Material Dark 토큰
- **배포**: Streamlit Cloud → `main` 브랜치 추적

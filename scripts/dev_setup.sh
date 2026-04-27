#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[OK] 개발 환경 준비 완료"
echo "다음 명령으로 앱을 실행하세요:"
echo "source .venv/bin/activate && streamlit run app.py"

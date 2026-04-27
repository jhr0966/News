.PHONY: install run check test format clean

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	streamlit run app.py

check:
	python -m py_compile app.py scraper.py insights.py cardnews.py
	grep -nE 'on_click\s*=' app.py || true
	grep -nE 'requests\.(get|post|Session)\(' scraper.py || true

test:
	pytest -q tests/test_app_pages_smoke.py

format:
	python -m pip install ruff
	ruff format app.py scraper.py insights.py cardnews.py

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +

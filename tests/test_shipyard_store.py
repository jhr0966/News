from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

import shipyard_store


def test_ingest_shipyard_excel_success(tmp_path: Path, monkeypatch) -> None:
    df = pd.DataFrame(
        [
            {"task_id": "T-1", "process": "도장", "task_name": "표면 처리", "description": "샌딩 작업"},
            {"task_id": "T-2", "process": "용접", "task_name": "블록 용접", "description": "자동 용접"},
        ]
    )
    monkeypatch.setattr(shipyard_store.pd, "read_excel", lambda _: df)
    result = shipyard_store.ingest_shipyard_excel(
        "tasks.xlsx",
        file_obj=io.BytesIO(b"dummy"),
        data_root=tmp_path / "data",
    )

    assert result.is_valid is True
    assert result.row_count == 2
    assert result.parquet_path is not None
    assert Path(result.raw_path).exists()
    assert Path(result.parquet_path).exists()


def test_ingest_shipyard_excel_missing_columns(tmp_path: Path, monkeypatch) -> None:
    df = pd.DataFrame([{"task_id": "T-1", "process": "도장"}])
    monkeypatch.setattr(shipyard_store.pd, "read_excel", lambda _: df)
    result = shipyard_store.ingest_shipyard_excel(
        "tasks.xlsx",
        file_obj=io.BytesIO(b"dummy"),
        data_root=tmp_path / "data",
    )

    assert result.is_valid is False
    assert result.parquet_path is None
    assert any("필수 컬럼 누락" in e for e in result.errors)


def test_ingest_shipyard_excel_missing_engine(tmp_path: Path, monkeypatch) -> None:
    def _raise_import_error(_):
        raise ImportError("openpyxl missing")

    monkeypatch.setattr(shipyard_store.pd, "read_excel", _raise_import_error)
    result = shipyard_store.ingest_shipyard_excel(
        "tasks.xlsx",
        file_obj=io.BytesIO(b"dummy"),
        data_root=tmp_path / "data",
    )

    assert result.is_valid is False
    assert any("openpyxl" in e for e in result.errors)

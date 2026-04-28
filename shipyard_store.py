"""Shipyard 작업 데이터(Excel) 업로드/검증/Parquet 저장."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import pandas as pd


REQUIRED_COLUMNS = ["task_id", "process", "task_name", "description"]


@dataclass
class ShipyardIngestResult:
    is_valid: bool
    errors: list[str]
    raw_path: str | None = None
    parquet_path: str | None = None
    row_count: int = 0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _dated_dir(base: Path, when: datetime) -> Path:
    path = base / when.strftime("%Y-%m-%d")
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_shipyard_df(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if df.empty:
        errors.append("엑셀 데이터가 비어 있습니다.")
        return errors

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"필수 컬럼 누락: {', '.join(missing)}")
        return errors

    for col in REQUIRED_COLUMNS:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            errors.append(f"필수 컬럼 '{col}'에 빈 값이 {null_count}개 있습니다.")

    if "task_id" in df.columns:
        dup_count = int(df["task_id"].duplicated().sum())
        if dup_count > 0:
            errors.append(f"'task_id' 중복이 {dup_count}개 있습니다.")

    return errors


def ingest_shipyard_excel(
    file_name: str,
    file_obj: BinaryIO,
    data_root: str | Path = "data",
) -> ShipyardIngestResult:
    """업로드한 엑셀을 raw 저장 후 검증하고 parquet 저장."""
    root = Path(data_root)
    raw_base = root / "shipyard" / "raw"
    processed_base = root / "shipyard" / "processed"

    now = _utc_now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    raw_dir = _dated_dir(raw_base, now)
    processed_dir = _dated_dir(processed_base, now)

    raw_path = raw_dir / f"{stamp}_{Path(file_name).name}"
    with raw_path.open("wb") as f:
        f.write(file_obj.read())

    try:
        df = pd.read_excel(raw_path)
    except ImportError:
        return ShipyardIngestResult(
            is_valid=False,
            errors=["엑셀 엔진(openpyxl)이 설치되어 있지 않습니다. requirements 설치 후 다시 시도하세요."],
            raw_path=str(raw_path),
            row_count=0,
        )
    except Exception as exc:
        return ShipyardIngestResult(
            is_valid=False,
            errors=[f"엑셀 파일을 읽지 못했습니다: {exc}"],
            raw_path=str(raw_path),
            row_count=0,
        )
    df.columns = [str(c).strip() for c in df.columns]

    errors = validate_shipyard_df(df)
    if errors:
        return ShipyardIngestResult(
            is_valid=False,
            errors=errors,
            raw_path=str(raw_path),
            row_count=len(df),
        )

    parquet_path = processed_dir / f"shipyard_tasks_{stamp}.parquet"
    df.to_parquet(parquet_path, index=False)

    return ShipyardIngestResult(
        is_valid=True,
        errors=[],
        raw_path=str(raw_path),
        parquet_path=str(parquet_path),
        row_count=len(df),
    )


def load_latest_shipyard_tasks(data_root: str | Path = "data") -> pd.DataFrame:
    root = Path(data_root)
    processed_base = root / "shipyard" / "processed"
    if not processed_base.exists():
        return pd.DataFrame()

    candidates = sorted(
        processed_base.glob("*/shipyard_tasks_*.parquet"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return pd.DataFrame()

    return pd.read_parquet(candidates[0])

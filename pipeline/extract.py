"""Extract: download and cache the Online Retail II dataset.

Idempotent: if the file already exists and looks complete, the download is skipped.
Tries the direct .xlsx host first, then a .zip mirror (UCI serves both at different times).
"""
from __future__ import annotations

import io
import zipfile

import requests

from . import config

# A complete download is ~45 MB; anything much smaller is a truncated/error page.
_MIN_BYTES = 5_000_000


def _looks_complete(path) -> bool:
    return path.exists() and path.stat().st_size > _MIN_BYTES


def _download(url: str) -> bytes:
    print(f"  GET {url}")
    resp = requests.get(url, stream=True, timeout=120, headers={"User-Agent": "retail-analytics-platform"})
    resp.raise_for_status()
    chunks, total, next_mark = [], 0, 10 << 20  # log every ~10 MB
    for chunk in resp.iter_content(chunk_size=1 << 20):
        chunks.append(chunk)
        total += len(chunk)
        if total >= next_mark:
            print(f"    downloaded {total / 1e6:.0f} MB")
            next_mark += 10 << 20
    print(f"    downloaded {total / 1e6:.1f} MB total")
    return b"".join(chunks)


def _xlsx_from_zip(blob: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".xlsx"))
        print(f"  extracting {name} from zip")
        return zf.read(name)


def extract() -> str:
    """Ensure the dataset xlsx is cached locally; return its path as a string."""
    config.ensure_dirs()
    target = config.XLSX_PATH

    if _looks_complete(target):
        print(f"[extract] cached: {target} ({target.stat().st_size / 1e6:.1f} MB)")
        return str(target)

    urls = [config.DATASET_URL, *config.DATASET_MIRRORS]
    last_err: Exception | None = None
    for url in urls:
        try:
            blob = _download(url)
            if url.lower().endswith(".zip"):
                blob = _xlsx_from_zip(blob)
            target.write_bytes(blob)
            print(f"[extract] saved: {target} ({len(blob) / 1e6:.1f} MB)")
            return str(target)
        except Exception as err:  # noqa: BLE001 - try the next mirror
            last_err = err
            print(f"[extract] failed via {url}: {err}")

    raise RuntimeError(
        "Could not download Online Retail II from any source. "
        "Download it manually from https://archive.ics.uci.edu/dataset/502/online+retail+ii "
        f"and place the .xlsx at {target}."
    ) from last_err


if __name__ == "__main__":
    extract()

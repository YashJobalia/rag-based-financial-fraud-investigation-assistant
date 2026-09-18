"""Acquire and profile the ULB benchmark, never ingest it into investigation RAG.

Standard library only. Run from any directory with Python 3.12+.
Original labels remain in quarantined raw data, outside app/deployment inputs.
"""

import csv
import hashlib
import json
import math
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "external"
SOURCE = "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud"
DOWNLOAD = "https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv"
METADATA = "https://www.kaggle.com/api/v1/datasets/view/mlg-ulb/creditcardfraud"
EXPECTED = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount", "Class"]
LIMIT = 200_000_000


def profile(path: Path) -> dict:
    counts = Counter()
    rows = 0
    bounds = {name: [math.inf, -math.inf] for name in ("Time", "Amount")}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED:
            raise ValueError("Unexpected schema; review source before proceeding")
        for row in reader:
            if None in row or any(row.get(name) in (None, "") for name in EXPECTED):
                raise ValueError("Malformed row or missing value")
            values = {key: float(value) for key, value in row.items()}
            if not all(math.isfinite(value) for value in values.values()):
                raise ValueError("Non-finite numeric value")
            if row["Class"] not in ("0", "1"):
                raise ValueError("Unexpected target label")
            counts[row["Class"]] += 1
            for name, bound in bounds.items():
                bound[0] = min(bound[0], values[name])
                bound[1] = max(bound[1], values[name])
            rows += 1
    if rows != 284807 or counts != {"0": 284315, "1": 492}:
        raise ValueError("Counts differ from reviewed release; investigate source change")
    return {
        "rows": rows, "columns": EXPECTED, "column_count": len(EXPECTED),
        "label_counts": dict(counts), "missing_values": 0,
        "numeric_ranges": bounds, "sha256": digest.hexdigest(),
        "bytes": path.stat().st_size,
    }


def main() -> None:
    raw = BASE / "raw" / "ulb-creditcard"
    raw.mkdir(parents=True, exist_ok=True)
    target = raw / "creditcard.csv"
    with urllib.request.urlopen(METADATA, timeout=45) as response:
        metadata = json.load(response)
    if metadata.get("licenseName") != "Database: Open Database, Contents: Database Contents":
        raise ValueError("Source license changed; review before downloading")
    downloaded = not target.exists()
    if downloaded:
        temporary = target.with_suffix(".csv.part")
        try:
            with urllib.request.urlopen(DOWNLOAD, timeout=60) as response, temporary.open("wb") as out:
                size = 0
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > LIMIT:
                        raise ValueError("Download exceeded reviewed size limit")
                    out.write(block)
            result = profile(temporary)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    else:
        result = profile(target)
    report_path = BASE / "ulb-creditcard-profile.json"
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if previous["observed"]["sha256"] != result["sha256"]:
            raise ValueError("Checksum differs from recorded acquisition")
        acquired_at = previous["acquired_at_utc"]
    else:
        acquired_at = datetime.now(timezone.utc).isoformat()
    report = {
        "dataset": "ULB / Worldline Credit Card Fraud Detection",
        "source": SOURCE, "source_version": metadata["currentVersionNumber"],
        "download_url": DOWNLOAD,
        "mirror_documentation": "https://www.tensorflow.org/tutorials/structured_data/imbalanced_data",
        "license_as_reported_by_source": metadata["licenseName"],
        "license_urls": ["https://opendatacommons.org/licenses/odbl/1-0/",
                         "https://opendatacommons.org/licenses/dbcl/1-0/"],
        "acquired_at_utc": acquired_at,
        "mirror_matches_source_version": "Not byte-verified against Kaggle archive; schema and counts verified",
        "observed": result,
        "use": "Offline transaction-fraud detection benchmark only",
        "ato_suitability": "Insufficient: no account, login, device or recipient identifiers",
        "runtime_ingested": False,
        "label_policy": "Class stays in ignored raw data; never supply as RAG/model evidence",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {result['rows']:,} rows / {result['column_count']} columns")
    print(f"SHA-256: {result['sha256']}")
    print("Raw data quarantined under data/external/raw/; no database or model calls")


if __name__ == "__main__":
    main()

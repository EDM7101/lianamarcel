#!/usr/bin/env python3
"""CSV (Spalte address) nach targets.txt konvertieren."""

import argparse
import csv
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("output_txt", type=Path)
    args = ap.parse_args()
    rows = []
    with args.input_csv.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            a = (row.get("address") or "").strip()
            if a and not a.startswith("#"):
                rows.append(a)
    args.output_txt.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"{len(rows)} Adressen -> {args.output_txt}")


if __name__ == "__main__":
    main()

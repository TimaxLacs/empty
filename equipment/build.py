#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "index.html"


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def validate(data: dict) -> None:
    core_ids = [item["id"] for cat in data["categories"] for item in cat["items"]]
    indiv_ids = [item["id"] for item in data["individual"]]
    allowed = {"+", "-", ">", "~", "!", "x", "?"}

    if len(core_ids) != 51:
        raise SystemExit(f"Expected 51 core items, got {len(core_ids)}")
    if len(indiv_ids) != 18:
        raise SystemExit(f"Expected 18 individual items, got {len(indiv_ids)}")

    for person in data["people"]:
        missing_core = [item_id for item_id in core_ids if item_id not in person["core"]]
        extra_core = [item_id for item_id in person["core"] if item_id not in core_ids]
        missing_ind = [item_id for item_id in indiv_ids if item_id not in person["individual"]]
        extra_ind = [item_id for item_id in person["individual"] if item_id not in indiv_ids]
        bad_core = [f"{k}={v}" for k, v in person["core"].items() if v not in allowed]
        bad_ind = [f"{k}={v}" for k, v in person["individual"].items() if v not in allowed]
        problems = []
        if missing_core:
            problems.append(f"missing core {missing_core}")
        if extra_core:
            problems.append(f"extra core {extra_core}")
        if missing_ind:
            problems.append(f"missing individual {missing_ind}")
        if extra_ind:
            problems.append(f"extra individual {extra_ind}")
        if bad_core:
            problems.append(f"bad core {bad_core}")
        if bad_ind:
            problems.append(f"bad individual {bad_ind}")
        if problems:
            raise SystemExit(f"{person['name']}: " + "; ".join(problems))


def build() -> None:
    data = load_data()
    validate(data)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUTPUT_PATH.write_text(template.replace("__DATA__", payload), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} for {len(data['people'])} people")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Training dataset management skeleton for 3.0 micro-model factory."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict
from app.core.config import config_manager

DATA_ROOT = Path(config_manager.get("system.data_dir", "./data")) / "training"
DATA_ROOT.mkdir(parents=True, exist_ok=True)

def add_training_sample(dataset_name: str, input_sample: dict, output_sample: dict, source: str) -> dict:
    ds_dir = DATA_ROOT / dataset_name
    ds_dir.mkdir(parents=True, exist_ok=True)
    samples_file = ds_dir / "samples.jsonl"
    line = {"timestamp": datetime.now(timezone.utc).isoformat(), "source": source, "input": input_sample, "output": output_sample}
    with open(samples_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    dataset_card_path = ds_dir / "dataset_card.json"
    if not dataset_card_path.exists():
        card = {"dataset_dir": str(ds_dir), "samples": 1, "generated_at": int(datetime.now(timezone.utc).timestamp())}
        with open(dataset_card_path, "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2, ensure_ascii=False)
    return {"dataset": dataset_name, "lines_written": 1}

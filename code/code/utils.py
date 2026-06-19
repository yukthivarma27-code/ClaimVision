import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import diskcache as dc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("claimlens")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
CACHE_DIR = Path.home() / ".claimlens_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

cache = dc.Cache(str(CACHE_DIR))

def get_image_path(image_rel_path: str) -> Path:
    return (DATASET_DIR / image_rel_path).resolve()

def image_hash(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def parse_image_paths(paths_str: str) -> list[str]:
    return [p.strip() for p in paths_str.split(";") if p.strip()]

def image_id_from_path(path: str) -> str:
    return Path(path).stem

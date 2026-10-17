"""Snapshots: raw collector output saved as JSON so reports can be re-analysed and re-rendered offline.
Customer data lives here: the snapshot folder is git-ignored (hard rule 2)."""
from __future__ import annotations
import json, pathlib

class Snapshot:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
    def save(self, name: str, data) -> None:
        (self.root / f"{name}.json").write_text(json.dumps(data, indent=1, sort_keys=True))
    def load(self, name: str):
        p = self.root / f"{name}.json"
        return json.loads(p.read_text()) if p.exists() else None
    def has(self, name: str) -> bool:
        return (self.root / f"{name}.json").exists()

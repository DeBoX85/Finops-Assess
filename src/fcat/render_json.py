import json, pathlib
from dataclasses import asdict
from . import SCHEMA_VERSION
from .checks import meta_dict, REGISTRY

def render(path, manifest, findings):
    doc = {"schema_version": SCHEMA_VERSION, "manifest": manifest,
           "check_catalogue": [meta_dict(m) for m, _ in REGISTRY],
           "findings": [asdict(f) for f in findings]}
    pathlib.Path(path).write_text(json.dumps(doc, indent=1))
    return doc

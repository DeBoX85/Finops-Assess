import json
import pathlib
from dataclasses import asdict

from . import SCHEMA_VERSION
from .checks import REGISTRY, meta_dict


def render(path, manifest, findings):
    from .checks import load_builtin

    load_builtin()
    doc = {
        "schema_version": SCHEMA_VERSION,
        "manifest": manifest,
        "check_catalogue": [meta_dict(m) for m, _ in REGISTRY],
        "findings": [asdict(f) for f in findings],
    }
    pathlib.Path(path).write_text(json.dumps(doc, indent=1))
    return doc

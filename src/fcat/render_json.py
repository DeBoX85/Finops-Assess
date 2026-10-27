import json
import pathlib
from dataclasses import asdict

from . import SCHEMA_VERSION, audit, confidence
from .checks import REGISTRY, meta_dict


def render(path, manifest, findings):
    from .checks import load_builtin

    load_builtin()
    policy, records = confidence.load_policy(), confidence.load_records()
    doc = {
        "schema_version": SCHEMA_VERSION,
        "manifest": manifest,
        "check_catalogue": [meta_dict(m, policy, records) for m, _ in REGISTRY],
        "confidence_policy": {**policy, "text": confidence.policy_text(policy)},
        "findings": [asdict(f) for f in findings],
    }
    doc["audit"] = audit.build(doc)
    pathlib.Path(path).write_text(json.dumps(doc, indent=1))
    return doc

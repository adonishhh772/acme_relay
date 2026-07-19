#!/usr/bin/env python3
"""CI gate: versioned prompts must be valid YAML with monotonic version and labels."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "apps" / "api" / "prompts"
BASELINE = ROOT / "apps" / "api" / "prompts" / ".version-baseline"


def main() -> int:
    errors: list[str] = []
    versions: dict[str, int] = {}
    if BASELINE.exists():
        for line in BASELINE.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            name, version = line.split("=")
            versions[name.strip()] = int(version.strip())

    for path in sorted(PROMPTS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append(f"{path.name}: not a mapping")
            continue
        for field in ("name", "version", "template", "labels", "variables"):
            if field not in data:
                errors.append(f"{path.name}: missing {field}")
        if not isinstance(data.get("version"), int) or data["version"] < 1:
            errors.append(f"{path.name}: version must be positive int")
        labels = data.get("labels") or []
        if "production" in labels and "user_roles" not in (data.get("variables") or []):
            errors.append(f"{path.name}: production prompt requires user_roles variable")
        name = str(data.get("name"))
        version = int(data.get("version") or 0)
        baseline = versions.get(name)
        if baseline is not None and version < baseline:
            errors.append(f"{path.name}: version {version} < baseline {baseline}")

    if errors:
        print("Prompt CI gate failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Prompt CI gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

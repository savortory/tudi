"""Validate the public catalog and, optionally, compare it to a prior release."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = re.compile(r"camera/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*\.json")
APPROVED_FILES = {
    ".gitignore", "LICENSE", "README.md", "THIRD_PARTY_NOTICES",
    ".github/workflows/catalog.yml", "devices/manifest.json",
    "devices/recipe.schema.json", "devices/tools/validate.py",
}


def read_catalog(root):
    manifest = json.loads((root / "manifest.json").read_bytes())
    if manifest["schemaVersion"] != 1:
        raise ValueError("Unsupported manifest version")
    items = {item["id"]: item for item in manifest["items"]}
    if not items or len(items) != len(manifest["items"]):
        raise ValueError("Expected a nonempty manifest with unique IDs")
    return items


def validate(previous_root):
    items = read_catalog(ROOT)
    schema = json.loads((ROOT / "recipe.schema.json").read_bytes())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    expected = set(APPROVED_FILES)
    for recipe_id, item in items.items():
        path = item["path"]
        if not RECIPE_PATH.fullmatch(path) or Path(path).stem != recipe_id:
            raise ValueError(f"Invalid catalog path for {recipe_id}")
        raw = (ROOT / path).read_bytes()
        if len(raw) > 256 * 1024 or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError(f"Unexpected size or checksum for {recipe_id}")
        recipe = json.loads(raw)
        validator.validate(recipe)
        if any(item[key] != recipe[key] for key in ("id", "revision", "schemaVersion")):
            raise ValueError(f"Manifest metadata differs for {recipe_id}")
        if recipe["config"].get("tudiSense") and recipe["config"]["protocol"] != "mjpeg":
            raise ValueError("Tudi Sense requires MJPEG")
        for route in [recipe["config"]["path"], *recipe["config"]["discovery"]["paths"],
                      recipe["config"].get("ptz", {}).get("path", "")]:
            if re.search(r"(password|passwd|token|secret|auth)=", route, re.I):
                raise ValueError(f"Credential-like query parameter in {recipe_id}")
        expected.add("devices/" + path)

    entries = subprocess.check_output(
        ["git", "ls-files", "--stage", "-z"], cwd=ROOT.parent
    ).decode().rstrip("\0").split("\0")
    tracked = set()
    for entry in entries:
        metadata, path = entry.split("\t", 1)
        if metadata.split()[0] not in {"100644", "100755"}:
            raise ValueError(f"Non-regular Git entry at {path}")
        tracked.add(path)
    if tracked != expected:
        raise ValueError(f"Unexpected or missing tracked files: {sorted(tracked ^ expected)}")

    if previous_root:
        for recipe_id, old in read_catalog(previous_root).items():
            current = items.get(recipe_id)
            if current and (
                current["revision"] < old["revision"]
                or (current["revision"] == old["revision"] and current["sha256"] != old["sha256"])
            ):
                raise ValueError(f"Increment revision for changed recipe {recipe_id}")
    print(f"Validated {len(items)} recipes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path)
    validate(parser.parse_args().previous)

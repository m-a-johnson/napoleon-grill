#!/usr/bin/env python3
"""Helpers for the release workflow.

pick-bump   Read PR label names (one per line) on stdin, print the biggest
            requested bump (major > minor > patch), or nothing if none match.
bump        Bump the "version" in manifest.json (patch|minor|major), keeping
            the file's formatting, and print the new version.
"""
from __future__ import annotations

import re
import sys

MANIFEST = "custom_components/napoleon_grill/manifest.json"
ORDER = ("patch", "minor", "major")
VERSION_RE = re.compile(r'("version"\s*:\s*")(\d+)\.(\d+)\.(\d+)(")')


def pick_bump(labels: list[str]) -> str:
    found = {
        label.strip().removeprefix("release:")
        for label in labels
        if label.strip().startswith("release:")
    }
    valid = [level for level in ORDER if level in found]
    return valid[-1] if valid else ""


def bump_text(text: str, level: str) -> tuple[str, str]:
    if level not in ORDER:
        raise ValueError(f"bump must be one of {ORDER}, got {level!r}")
    matches = VERSION_RE.findall(text)
    if len(matches) != 1:
        raise ValueError(f'expected exactly one "version": "X.Y.Z", found {len(matches)}')
    major, minor, patch = (int(part) for part in matches[0][1:4])
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"
    return VERSION_RE.sub(lambda m: f"{m.group(1)}{new}{m.group(5)}", text), new


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "pick-bump":
        print(pick_bump(sys.stdin.read().splitlines()))
        return 0
    if argv[1] == "bump" and len(argv) in (3, 4):
        path = argv[3] if len(argv) > 3 else MANIFEST
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        new_text, new = bump_text(text, argv[2])
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(new_text)
        print(new)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

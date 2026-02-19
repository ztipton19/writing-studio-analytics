#!/usr/bin/env python
"""Generate pinned release requirements from the current environment.

Reads requirements.txt and writes requirements-release.txt with exact versions.
"""

from __future__ import annotations

import re
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from packaging.version import Version

SRC = Path("requirements.txt")
OUT = Path("requirements-release.txt")

PKG_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)")
MIN_RE = re.compile(r"^\s*[A-Za-z0-9_.\-]+\s*>=\s*([^\s#]+)")


def parse_pkg(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    m = PKG_RE.match(stripped)
    if not m:
        return None
    return m.group(1)


def main() -> int:
    if not SRC.exists():
        print("requirements.txt not found")
        return 1

    lines = SRC.read_text(encoding="utf-8").splitlines()
    out_lines = [
        f"# Generated on {date.today().isoformat()} by scripts/freeze_release_requirements.py",
        "# Pinned release dependencies for reproducible supervisor handoff",
        "",
    ]

    missing = []

    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            out_lines.append(raw)
            continue

        pkg = parse_pkg(raw)
        if not pkg:
            out_lines.append(raw)
            continue

        try:
            installed = version(pkg)
            min_match = MIN_RE.match(raw.strip())
            if min_match:
                min_required = min_match.group(1)
                if Version(installed) < Version(min_required):
                    out_lines.append(f"{pkg}=={min_required}  # raised to declared minimum")
                else:
                    out_lines.append(f"{pkg}=={installed}")
            else:
                out_lines.append(f"{pkg}=={installed}")
        except PackageNotFoundError:
            m = MIN_RE.match(raw.strip())
            if m:
                out_lines.append(f"{pkg}=={m.group(1)}  # fallback: not installed in freeze env")
            else:
                missing.append(pkg)
                out_lines.append(f"# MISSING IN ENV: {raw}")

    OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    if missing:
        print("Generated requirements-release.txt with missing packages:")
        for pkg in missing:
            print(f" - {pkg}")
        return 2

    print("Generated requirements-release.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

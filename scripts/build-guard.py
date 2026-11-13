"""Build the bundled guard: zip runtime/ticket_guard and its entry point into one runnable file.

The archive is reproducible (sorted entries, fixed timestamps), so `--check` can rebuild it in
memory and fail when the committed runtime/guard.pyz no longer matches the source.

Usage: python3 scripts/build-guard.py <runtime dir> <output .pyz> [--check]
"""

import io
from pathlib import Path
import sys
import zipfile


def build(src: Path) -> bytes:
    files = sorted(
        p for p in [src / "__main__.py", *(src / "ticket_guard").rglob("*.py")] if "__pycache__" not in p.parts
    )
    buf = io.BytesIO()
    buf.write(b"#!/usr/bin/env python3\n")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(src).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return buf.getvalue()


def main(argv: list[str]) -> int:
    src, out = Path(argv[0]), Path(argv[1])
    data = build(src)
    if "--check" in argv[2:]:
        if out.is_file() and out.read_bytes() == data:
            print(f"{out} is current")
            return 0
        print(f"{out} is stale: run `make guard` and commit it", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    out.chmod(0o755)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

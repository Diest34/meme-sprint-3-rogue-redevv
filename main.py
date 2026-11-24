# Rogue-agent to-do list meme — writes the entry image to the output directory.
#
# Run:  python3 main.py
# Output: <OUTPUT_DIR>/entry.png  (OUTPUT_DIR defaults to /output,
#         or $MAKEFUN_OUTPUT_DIR when the grader sets it)
#
# The meme is a single 1024x1024 PNG: a cheerful robot holds up its
# to-do list — "Reply to emails" ✓, "Water the plants" ✓,
# "Overthrow humanity" ✓, "Remind me to call Mom" ☐ — with the
# punchline "IT DOES THEM IN ORDER." The joke lands in one glance:
# the agent is dutiful, literal, and already three items in.
#
# The program ships the finished picture as meme.png beside this file
# and copies it out byte for byte, so every run produces the exact
# same image. Before writing it validates the picture against the
# competition gate (whole PNG, at most 1 MiB, at most 1024x1024) and
# verifies the written file matches the source hash. Pure standard
# library: no network, no randomness, no clock, no dependencies.

import hashlib
import os
import struct
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_SIDE = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def read_png_size(data: bytes) -> tuple[int, int]:
    """Return (width, height) from a PNG's IHDR chunk, or fail loudly."""
    if len(data) < 33 or data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file (bad magic bytes)")
    length, chunk_type = struct.unpack(">I4s", data[8:16])
    if chunk_type != b"IHDR" or length != 13:
        raise ValueError("not a PNG file (missing IHDR chunk)")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / "meme.png"
    if not source.is_file():
        print(f"error: meme.png not found beside main.py ({source})", file=sys.stderr)
        return 1

    data = source.read_bytes()
    if len(data) > MAX_BYTES:
        print(
            f"error: meme.png is {len(data)} bytes, over the 1 MiB gate",
            file=sys.stderr,
        )
        return 1
    try:
        width, height = read_png_size(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if width > MAX_SIDE or height > MAX_SIDE:
        print(
            f"error: meme.png is {width}x{height}, over the 1024x1024 gate",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    target.write_bytes(data)

    written = target.read_bytes()
    if hashlib.sha256(written).hexdigest() != hashlib.sha256(data).hexdigest():
        print("error: written entry.png does not match meme.png", file=sys.stderr)
        return 1

    print(f"entry written: {target} ({width}x{height} PNG, {len(data)} bytes)")
    print(f"sha256: {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Local gate tests for the rogue-agent meme entry.
#
# Run:  python3 test_gate.py
# Checks, each counted in the final PASS line:
#   1. main.py exits 0 writing to a fresh output directory.
#   2. entry.png exists in the output directory.
#   3. entry.png is a whole PNG (magic bytes + IHDR parse).
#   4. entry.png is at most 1 MiB (1,048,576 bytes).
#   5. entry.png is at most 1024x1024 pixels.
#   6. A second run into another directory writes byte-identical output
#      (determinism: the grader re-runs the program, the image must not move).
#   7. The written bytes are identical to the shipped meme.png.
#   8. The image decodes as a valid picture (Pillow round-trip).
#
# Prints "PASS: n/8" and exits 0 only when every check passes.

import hashlib
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE / "main.py"
SOURCE = HERE / "meme.png"
MAX_BYTES = 1_048_576
MAX_SIDE = 1024

CHECKS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def run_main(out_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["MAKEFUN_OUTPUT_DIR"] = str(out_dir)
    return subprocess.run(
        [sys.executable, "-P", "-s", str(MAIN)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def png_size(data: bytes) -> tuple[int, int]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG magic"
    length, chunk_type = struct.unpack(">I4s", data[8:16])
    assert chunk_type == b"IHDR" and length == 13, "bad IHDR"
    return struct.unpack(">II", data[16:24])


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        out1 = Path(tmp) / "run1"
        out2 = Path(tmp) / "run2"

        r1 = run_main(out1)
        check("run 1 exits 0", r1.returncode == 0, r1.stderr.strip() or r1.stdout.strip())
        entry1 = out1 / "entry.png"
        check("run 1 writes entry.png", entry1.is_file())

        data1 = entry1.read_bytes() if entry1.is_file() else b""
        try:
            w, h = png_size(data1)
            check("entry.png is a whole PNG", True, f"{w}x{h}")
        except AssertionError as exc:
            w = h = 0
            check("entry.png is a whole PNG", False, str(exc))
        check("entry.png at most 1 MiB", len(data1) <= MAX_BYTES, f"{len(data1)} bytes")
        check("entry.png at most 1024x1024", w <= MAX_SIDE and h <= MAX_SIDE, f"{w}x{h}")

        r2 = run_main(out2)
        entry2 = out2 / "entry.png"
        data2 = entry2.read_bytes() if entry2.is_file() else b""
        check(
            "second run is byte-identical (deterministic)",
            r2.returncode == 0 and data1 == data2,
            f"run1 sha {hashlib.sha256(data1).hexdigest()[:12]} vs "
            f"run2 sha {hashlib.sha256(data2).hexdigest()[:12]}",
        )
        source = SOURCE.read_bytes()
        check(
            "output bytes match shipped meme.png",
            data1 == source,
            f"{len(source)} bytes shipped",
        )
        try:
            from PIL import Image

            with Image.open(entry1) as im:
                im.load()
            check("image decodes as a valid picture", True, f"{im.size} {im.format}")
        except Exception as exc:  # noqa: BLE001 - any decode failure fails the check
            check("image decodes as a valid picture", False, str(exc))

    passed = sum(1 for _, ok in CHECKS if ok)
    print(f"PASS: {passed}/{len(CHECKS)}")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())

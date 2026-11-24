#!/usr/bin/env python3
"""Publish the postmortem entry for the make.fun bounty
"The Postmortem That Made Us Laugh".

``entry.txt`` next to this file holds the entry: a short account,
one or two sentences and no more than 400 characters, of the
silliest or most fatal time an AI coding agent misunderstood what
it was asked or wrecked the code it was given. Running this program
copies those exact bytes into ``entry.txt`` inside the output
directory and reads the copy back, so the published file is
byte-identical to the source, trailing newline included.

Where the output goes: ``--output-dir`` wins, else
``MAKEFUN_OUTPUT_DIR``, else ``/output``. ``--verify-only`` checks
the gate and writes nothing. ``--max-chars`` changes the gate
(default 400). ``--quiet`` hides the success line. The program uses
only the standard library and never touches the network, the clock,
or randomness, so every run publishes the same bytes.
"""

import argparse
import os
import sys
from pathlib import Path

MAX_CHARS = 400
FALLBACK_DIR = "/output"


def load_raw_bytes() -> bytes:
    """Read the entry file as raw bytes, or fail with a clear message."""
    path = Path(__file__).resolve().parent / "entry.txt"
    if not path.is_file():
        raise SystemExit(f"entry.txt not found next to {__file__}")
    return path.read_bytes()


def gate_check(raw: bytes, limit: int) -> str:
    """Validate the entry against the gate; return its text.

    The gate is the sealed scorer's: UTF-8 text, 1 to ``limit``
    characters, not only white space, one or two sentences on a
    single line. A byte-order mark is rejected so the published
    text starts with the entry itself, and control characters
    (other than the one trailing newline) are rejected so nothing
    invisible rides along.
    """
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SystemExit("entry.txt starts with a byte-order mark")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit("entry.txt is not valid UTF-8")
    line = text[:-1] if text.endswith("\n") else text
    if not line or line.isspace():
        raise SystemExit("entry is empty or only white space")
    if len(line) > limit:
        raise SystemExit(
            f"entry is {len(line)} characters, over the {limit} limit"
        )
    if "\n" in line or "\r" in line:
        raise SystemExit("entry must be one or two sentences on one line")
    if any(ord(ch) < 32 and ch not in "\t" for ch in line):
        raise SystemExit("entry contains a control character")
    return line


def resolve_outdir(flag_value):
    """Resolve the output directory: flag, environment, fallback."""
    if flag_value:
        return Path(flag_value)
    env_value = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_value:
        return Path(env_value)
    return Path(FALLBACK_DIR)


def write_verified(raw: bytes, outdir: Path) -> Path:
    """Write the raw bytes out and verify the copy byte for byte."""
    outdir.mkdir(parents=True, exist_ok=True)
    destination = outdir / "entry.txt"
    destination.write_bytes(raw)
    if destination.read_bytes() != raw:
        raise SystemExit("published entry does not match entry.txt")
    return destination


def parse_cli(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=None,
                        help="directory to write entry.txt into")
    parser.add_argument("--verify-only", action="store_true",
                        help="validate the entry without writing it")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS,
                        help="character limit for the entry")
    parser.add_argument("--quiet", action="store_true",
                        help="print nothing on success")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    options = parse_cli(argv)
    raw = load_raw_bytes()
    line = gate_check(raw, options.max_chars)
    if options.verify_only:
        if not options.quiet:
            print(f"Valid: {len(line)} characters")
        return 0
    destination = write_verified(raw, resolve_outdir(options.output_dir))
    if not options.quiet:
        print(f"Wrote {len(line)} characters to {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Ping IndexNow for one or more public mymoviejam.com URLs.

Requires the published key file at:
  https://mymoviejam.com/3fdbfbd0753d44d6bf2e56efa4e18824.txt

Usage:
  python3 scripts/indexnow_ping.py https://mymoviejam.com/blog/some-review/
  python3 scripts/indexnow_ping.py url1 url2 url3

Optional: INDEXNOW_KEY env overrides the default key.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

HOST = "mymoviejam.com"
KEY = os.environ.get("INDEXNOW_KEY", "3fdbfbd0753d44d6bf2e56efa4e18824")
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"


def main(argv: list[str]) -> int:
    urls = [u.strip() for u in argv[1:] if u.strip()]
    if not urls:
        print(__doc__)
        return 2
    for u in urls:
        if "mymoviejam.com" not in u:
            print(f"skip (not mymoviejam.com): {u}", file=sys.stderr)
            return 2
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode(errors="replace")
        print(f"IndexNow HTTP {resp.status}: {body or '(empty)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

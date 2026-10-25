"""Restore reviewed photograph bytes or verify the local pinned asset collection.

Network retrieval is restricted to the three explicitly reviewed image providers.
This command never searches or publishes unreviewed candidates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend/public"
ALLOWED_HOSTS = frozenset({
    "upload.wikimedia.org", "thumb.wikimedia.org",
    "openfoodfacts-images.s3.eu-west-3.amazonaws.com",
})
MAX_BYTES = 8 * 1024 * 1024


def approved_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or parsed.fragment):
        raise ValueError("Unapproved image provider URL")
    return url


class ReviewedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        approved_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


OPENER = urllib.request.build_opener(ReviewedRedirectHandler())


def asset_path(asset):
    local = asset["file"]
    if not re.fullmatch(r"/bottles/[-a-z0-9]+\.(jpg|png|webp)", local):
        raise ValueError("Invalid local photograph path")
    target = (PUBLIC / local.lstrip("/")).resolve()
    if PUBLIC.resolve() not in target.parents:
        raise ValueError("Photograph path escapes the public directory")
    return target


def verify_bytes(data, asset):
    if len(data) > MAX_BYTES:
        raise ValueError("Photograph exceeds the 8 MiB limit")
    if hashlib.sha256(data).hexdigest() != asset["sha256"]:
        raise ValueError("Photograph bytes changed; review the source before updating its pinned hash: " + asset["product_slug"])
    if len(data) != asset["bytes"]:
        raise ValueError("Photograph byte count does not match its manifest")


def restore(asset, verify_only=False):
    target = asset_path(asset)
    if verify_only:
        data = target.read_bytes()
    else:
        request = urllib.request.Request(approved_url(asset["download_url"]), headers={
            "User-Agent": "Alcooltest/1.0 (https://github.com/nabz0r/AlcooholTest)",
        })
        with OPENER.open(request, timeout=45) as response:
            approved_url(response.url)
            data = response.read(MAX_BYTES + 1)
    verify_bytes(data, asset)
    if not verify_only:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(target)
    return len(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Check local files without using the network.")
    args = parser.parse_args()
    assets = json.loads((ROOT / "data/assets.json").read_text())
    for asset in assets:
        print(asset["product_slug"], asset.get("view", "front"), restore(asset, args.verify_only), "verified")


if __name__ == "__main__":
    main()

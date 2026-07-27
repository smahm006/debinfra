"""GitHub release helpers used by deploys."""

import json
import urllib.request


def latest_asset(repo: str, match: str) -> str:
    """Return the download URL of the newest release asset whose name contains `match`."""
    with urllib.request.urlopen(f"https://api.github.com/repos/{repo}/releases/latest") as r:
        release = json.load(r)
    for asset in release["assets"]:
        if match in asset["name"]:
            return asset["browser_download_url"]
    raise ValueError(f"no asset matching {match!r} in {repo} latest release")

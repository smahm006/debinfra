"""sops-encrypted secrets, decrypted with the YubiKey-held GPG key."""

import functools
import json
import os
import subprocess
import sys

from debinfra import REPO_ROOT


class SecretsUnavailable(RuntimeError):
    pass


@functools.lru_cache(maxsize=None)
def load(name: str) -> dict:
    """Decrypt secrets/<name>.sops.yaml via sops; cached per-process."""
    if os.environ.get("DEBINFRA_NO_SECRETS") == "1":
        return {}
    path = REPO_ROOT / "secrets" / f"{name}.sops.yaml"
    if not path.exists():
        raise SecretsUnavailable(f"missing {path}")
    try:
        r = subprocess.run(
            ["sops", "-d", "--output-type", "json", str(path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise SecretsUnavailable(
            "sops not found on PATH. Run `debinfra bootstrap` first, or pass --no-secrets."
        ) from None
    except subprocess.CalledProcessError as e:
        raise SecretsUnavailable(
            f"cannot decrypt {path.name}:\n{e.stderr.strip()}\n"
            "Hints: is the YubiKey plugged in? does `gpg --card-status` work? "
            "is GNUPGHOME pointing at ~/.config/gnupg? Or re-run with --no-secrets."
        ) from None
    return json.loads(r.stdout)


def maybe(name: str) -> dict:
    """Best-effort variant for inventory/group_data: empty dict + warning on failure."""
    try:
        return load(name)
    except SecretsUnavailable as e:
        print(f"[debinfra] secrets '{name}' unavailable; continuing without. ({e})", file=sys.stderr)
        return {}


def check() -> list[str]:
    """Return problems with secrets/*.sops.yaml files (unencrypted or undecryptable)."""
    problems = []
    for path in sorted((REPO_ROOT / "secrets").glob("*.sops.yaml")):
        text = path.read_text()
        if "ENC[" not in text or "sops:" not in text:
            problems.append(f"{path.name}: NOT ENCRYPTED — do not commit this")
            continue
        r = subprocess.run(["sops", "-d", str(path)], capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"{path.name}: cannot decrypt ({r.stderr.strip().splitlines()[-1]})")
    return problems

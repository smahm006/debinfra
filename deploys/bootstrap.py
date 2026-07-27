"""Fresh-machine bootstrap: everything needed before secrets can be decrypted.

Requires zero secrets. Flow on a fresh box:
    install uv -> git clone debinfra -> uv sync -> debinfra bootstrap -> plug YubiKey -> debinfra deploy
"""

import subprocess

from pyinfra import host
from pyinfra.operations import apt, files, python, server, systemd

from debinfra import FILES, REPO_ROOT

SOPS_VERSION = "3.10.2"

home = host.data.user_home
user = host.data.home_user
gnupg_home = f"{home}/.config/gnupg"

apt.packages(
    name="Bootstrap: gpg + smartcard packages",
    packages=[
        "gnupg",
        "gnupg-agent",
        "dirmngr",
        "scdaemon",
        "pcscd",
        "pinentry-tty",
        "pinentry-gnome3",
    ],
    update=True,
    _sudo=True,
)

systemd.service(
    name="Bootstrap: enable pcscd",
    service="pcscd",
    running=True,
    enabled=True,
    _sudo=True,
)

files.directory(
    name="Bootstrap: ~/.local/bin",
    path=f"{home}/.local/bin",
    user=user,
    group=user,
    mode="755",
)

files.download(
    name="Bootstrap: sops binary",
    src=f"https://github.com/getsops/sops/releases/download/v{SOPS_VERSION}/sops-v{SOPS_VERSION}.linux.amd64",
    dest=f"{home}/.local/bin/sops",
    user=user,
    group=user,
    mode="755",
)


def _ensure_ssh_remote():
    url = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if url.startswith("https://github.com/"):
        ssh_url = f"git@github.com:{url.removeprefix('https://github.com/').removesuffix('.git')}.git"
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "remote", "set-url", "origin", ssh_url],
            check=True,
        )
        print(f"[debinfra] switched origin remote from https to ssh: {ssh_url}")


if host.data.is_local:
    python.call(
        name="Bootstrap: switch debinfra origin remote to ssh",
        function=_ensure_ssh_remote,
    )

# gnupg dotfiles only (the full dotfiles deploy comes later, with secrets available)
gnupg_src = FILES / "dotfiles" / "common" / "home" / ".config" / "gnupg"
files.directory(path=gnupg_home, user=user, group=user, mode="700")
for _f in sorted(gnupg_src.iterdir()):
    if _f.is_file():
        if host.data.is_local:
            files.link(
                name=f"Bootstrap: link gnupg/{_f.name}",
                path=f"{gnupg_home}/{_f.name}",
                target=str(_f),
                force=True,
            )
        else:
            files.put(
                name=f"Bootstrap: copy gnupg/{_f.name}",
                src=str(_f),
                dest=f"{gnupg_home}/{_f.name}",
                user=user,
                group=user,
                mode="600",
            )

files.put(
    name="Bootstrap: yubikey public key",
    src=str(FILES / "yubikey_public.asc"),
    dest=f"{home}/.cache/yubikey_public.asc",
    user=user,
    group=user,
    mode="644",
)

server.shell(
    name="Bootstrap: import yubikey public key",
    commands=[f"GNUPGHOME={gnupg_home} gpg --import {home}/.cache/yubikey_public.asc"],
)

result = server.shell(
    name="Bootstrap: gpg card status (needs YubiKey plugged in)",
    commands=[f"GNUPGHOME={gnupg_home} gpg --card-status"],
    _ignore_errors=True,
)


def _card_hint():
    if not result.did_succeed:
        print(
            "\n[debinfra] gpg --card-status failed — plug in the YubiKey and re-run "
            "`debinfra bootstrap`, then run `debinfra deploy`.\n"
        )


python.call(name="Bootstrap: YubiKey hint", function=_card_hint)

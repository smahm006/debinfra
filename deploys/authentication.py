"""GPG/YubiKey, SSH, and server hardening services (port of roles/authentication)."""

import io
import subprocess

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server, systemd

from debinfra import FILES
from debinfra.registry import task

GPG_SSH_KEY_ID = "D5725EEFAB586861"


@task("auth_gpg", groups={"clients"})
@deploy("Auth: gpg + smartcard")
def auth_gpg():
    gnupg_home = f"{host.data.user_home}/.config/gnupg"
    files.directory(path=gnupg_home, mode="700", user=host.data.home_user, group=host.data.home_user)
    server.shell(
        name="fix gnupg permissions",
        commands=[
            f"find {gnupg_home} -type d -exec chmod 700 {{}} +",
            f"find {gnupg_home} -type f -exec chmod 600 {{}} +",
        ],
    )
    files.put(
        src=str(FILES / "yubikey_public.asc"),
        dest=f"{host.data.user_home}/.cache/yubikey_public.asc",
        mode="644",
    )
    server.shell(
        name="import yubikey public key",
        commands=[f"GNUPGHOME={gnupg_home} gpg --import {host.data.user_home}/.cache/yubikey_public.asc"],
    )
    server.shell(
        name="refresh gpg smartcard stubs",
        commands=[f"GNUPGHOME={gnupg_home} gpg --card-status"],
        _ignore_errors=True,
    )


@task("auth_ssh")
@deploy("Auth: ssh files + authorized_keys")
def auth_ssh():
    home = host.data.user_home
    user = host.data.home_user
    files.directory(path=f"{home}/.ssh", mode="700", user=user, group=user)
    server.shell(
        name="fix ssh permissions",
        commands=[
            f"find {home}/.ssh -type d -exec chmod 700 {{}} +",
            f"find {home}/.ssh -type f -not -name '*.pub' -not -name authorized_keys -exec chmod 600 {{}} +",
            f"find {home}/.ssh -type f \\( -name '*.pub' -o -name authorized_keys \\) -exec chmod 644 {{}} +",
        ],
    )
    if "servers" in host.groups:
        # export the YubiKey auth subkey on the control machine, install as authorized_keys
        pub = subprocess.run(
            ["gpg", "--export-ssh-key", GPG_SSH_KEY_ID],
            capture_output=True,
            text=True,
            check=True,
            env={"GNUPGHOME": f"/home/{user}/.config/gnupg", "PATH": "/usr/bin:/bin"},
        ).stdout.strip()
        files.put(
            name="authorized_keys from yubikey gpg key",
            src=io.StringIO(pub + "\n"),
            dest=f"{home}/.ssh/authorized_keys",
            user=user,
            group=user,
            mode="644",
            create_remote_dir=True,
        )


@task("auth_sshd", groups={"servers"})
@deploy("Auth: sshd service")
def auth_sshd():
    files.put(
        name="ssh banner",
        src=io.StringIO("Authorized access only. All activity is monitored and logged.\n"),
        dest="/etc/ssh/banner",
        user="root",
        group="root",
        mode="644",
        _sudo=True,
    )
    systemd.service(service="ssh", running=True, enabled=True, _sudo=True)


@task("auth_firewall", groups={"servers"})
@deploy("Auth: nftables service")
def auth_firewall():
    systemd.service(service="nftables", running=True, enabled=True, _sudo=True)


@task("auth_fail2ban", groups={"servers"})
@deploy("Auth: fail2ban service")
def auth_fail2ban():
    systemd.service(service="fail2ban", running=True, enabled=True, _sudo=True)

"""Layered dotfiles deploy (port of roles/dotfiles).

Layers: common -> graphical (laptop+vm) -> machine_type. Symlink into the repo on
the local machine, copy over SSH. Root files are always copied, owned by root.
"""

from pathlib import Path

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server, systemd

from debinfra import TEMPLATES, secrets
from debinfra.dotutil import layered_files
from debinfra.registry import task

# Harness-specific paths (relative to $HOME) that should mirror the canonical
# agent memory file at ~/.config/ai/agents.md. Add new harnesses here as they're
# adopted, e.g. "opencode": ".config/opencode/AGENTS.md".
AGENT_HARNESS_LINKS = {
    "claude": ".claude/CLAUDE.md",
    "codex": ".config/codex/AGENTS.md",
}


@task("dot_home")
@deploy("Dotfiles: home")
def dot_home():
    home = host.data.user_home
    user = host.data.home_user
    for src, rel in layered_files(host.data.machine_type, "home"):
        dest = f"{home}/{rel}"
        parent = str(rel.parent)
        if parent != ".":
            files.directory(path=f"{home}/{parent}", user=user, group=user, mode="755")
        if host.data.is_local:
            files.link(name=f"link ~/{rel}", path=dest, target=str(src), force=True)
        else:
            mode = oct(src.stat().st_mode & 0o777)[2:]
            files.put(name=f"copy ~/{rel}", src=str(src), dest=dest, user=user, group=user, mode=mode)

    host_color = {"laptop": "green", "vm": "orange", "server": "yellow", "rpi": "yellow"}[
        host.data.machine_type
    ]
    files.template(
        name="template ~/.config/starship.toml",
        src=str(TEMPLATES / "starship.toml.j2"),
        dest=f"{home}/.config/starship.toml",
        user=user,
        group=user,
        mode="644",
        host_color=host_color,
    )

    if "clients" in host.groups:
        server_hosts = secrets.maybe("all").get("server_hosts", {})
        if server_hosts:
            files.directory(path=f"{home}/.ssh", user=user, group=user, mode="700")
            files.template(
                name="template ~/.ssh/config",
                src=str(TEMPLATES / "ssh_config.j2"),
                dest=f"{home}/.ssh/config",
                user=user,
                group=user,
                mode="600",
                server_hosts=server_hosts,
                server_gateway=secrets.maybe("all").get("server_gateway", ""),
                user_home=home,
            )
        # without secrets, leave the existing ~/.ssh/config untouched


@task("dot_agents", groups={"clients"})
@deploy("Dotfiles: AI agent harness links")
def dot_agents():
    home = host.data.user_home
    user = host.data.home_user
    canonical = f"{home}/.config/ai/agents.md"
    for harness, rel in AGENT_HARNESS_LINKS.items():
        dest = f"{home}/{rel}"
        parent = str(Path(rel).parent)
        if parent != ".":
            files.directory(path=f"{home}/{parent}", user=user, group=user, mode="755")
        files.link(name=f"link ~/{rel} ({harness})", path=dest, target=canonical, force=True)


@task("dot_root")
@deploy("Dotfiles: root")
def dot_root():
    for src, rel in layered_files(host.data.machine_type, "root"):
        dest = f"/{rel}"
        parent = str(rel.parent)
        if parent != ".":
            files.directory(path=f"/{parent}", user="root", group="root", mode="755", _sudo=True)
        mode = "755" if src.name.endswith(".sh") else "644"
        files.put(
            name=f"copy /{rel}",
            src=str(src),
            dest=dest,
            user="root",
            group="root",
            mode=mode,
            _sudo=True,
        )

    if host.data.machine_type in ("server", "rpi"):
        s = secrets.load("all")
        ctx = {
            "server_hosts": s.get("server_hosts", {}),
            "server_gateway": s.get("server_gateway", ""),
            "inventory_hostname": host.data.hostname,
        }

        sshd = files.template(
            name="template /etc/ssh/sshd_config",
            src=str(TEMPLATES / "sshd_config.j2"),
            dest="/etc/ssh/sshd_config",
            user="root",
            group="root",
            mode="644",
            _sudo=True,
            **ctx,
        )
        server.shell(name="validate sshd config", commands=["sshd -t"], _sudo=True)
        systemd.service(service="ssh", restarted=True, _sudo=True, _if=sshd.did_change)

        nft = files.template(
            name="template /etc/nftables.conf",
            src=str(TEMPLATES / "nftables.conf.j2"),
            dest="/etc/nftables.conf",
            user="root",
            group="root",
            mode="750",
            _sudo=True,
            **ctx,
        )
        systemd.service(service="nftables", reloaded=True, _sudo=True, _if=nft.did_change)

        f2b = files.template(
            name="template /etc/fail2ban/jail.local",
            src=str(TEMPLATES / "jail.local.j2"),
            dest="/etc/fail2ban/jail.local",
            user="root",
            group="root",
            mode="644",
            _sudo=True,
            **ctx,
        )
        systemd.service(service="fail2ban", restarted=True, _sudo=True, _if=f2b.did_change)

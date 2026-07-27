"""debinfra CLI — thin wrapper that drives the pyinfra CLI."""

import getpass
import os
import socket
import subprocess

import typer

from debinfra import REPO_ROOT

app = typer.Typer(no_args_is_help=True, add_completion=False)
secrets_app = typer.Typer(no_args_is_help=True)
app.add_typer(secrets_app, name="secrets", help="Manage sops-encrypted secrets")

HOST_BY_MACHINE = {
    "laptop": "sm-laptop",
    "vm": "sm-vm",
    "server": "sm-server",
    "rpi": "sm-rpi",
}
KNOWN_HOSTS = set(HOST_BY_MACHINE.values())


def parse_selectors(words: list[str]) -> list[str]:
    """Old debstrap grammar: spaces join with '_', commas separate selectors.

    "dev go" -> ["dev_go"];  "dot home, auth gpg" -> ["dot_home", "auth_gpg"]
    """
    parts = " ".join(words).split(",")
    return [p.strip().replace(" ", "_") for p in parts if p.strip()]


def _limit(target: str | None) -> str:
    host = HOST_BY_MACHINE.get(target, target) if target else socket.gethostname()
    if host not in KNOWN_HOSTS:
        raise typer.BadParameter(
            f"unknown target {host!r}; use one of {sorted(HOST_BY_MACHINE)} or a hostname"
        )
    if host == socket.gethostname():
        return "@local"
    return host


def _run_pyinfra(deploy_file: str, limit: str, dry: bool, env: dict) -> None:
    cmd = ["pyinfra", "-y", "--limit", limit, "inventory.py", deploy_file]
    if dry:
        cmd.insert(1, "--dry")
    r = subprocess.run(cmd, cwd=REPO_ROOT, env={**os.environ, **env})
    raise typer.Exit(r.returncode)


def _sudo_password(no_secrets: bool = False, hostname: str | None = None) -> str:
    if os.environ.get("DEBINFRA_SUDO_PASSWORD"):
        return os.environ["DEBINFRA_SUDO_PASSWORD"]
    if not no_secrets:
        from debinfra import secrets

        # per-host secrets/<hostname>.sops.yaml wins over the shared all.sops.yaml
        for name in ([hostname] if hostname else []) + ["all"]:
            if (REPO_ROOT / "secrets" / f"{name}.sops.yaml").exists():
                stored = secrets.maybe(name).get("sudo_password")
                if stored:
                    return stored
    return getpass.getpass("sudo password: ")


@app.command()
def deploy(
    selectors: list[str] = typer.Argument(None, help="Task selectors, e.g. 'pkg' or 'dev go'"),
    target: str = typer.Option(None, "--target", "-t", help="laptop|vm|server|rpi or hostname"),
    skip: list[str] = typer.Option([], "--skip", "-s", help="Selectors to skip"),
    dry: bool = typer.Option(False, "--dry", help="Show operations without executing"),
    no_secrets: bool = typer.Option(False, "--no-secrets", help="Run without decrypting secrets"),
):
    """Run provisioning tasks (all defaults for this machine when no selectors given)."""
    limit = _limit(target)
    hostname = socket.gethostname() if limit == "@local" else limit
    env = {
        "DEBINFRA_TASKS": ",".join(parse_selectors(selectors or [])),
        "DEBINFRA_SKIP": ",".join(parse_selectors(list(skip))),
        "DEBINFRA_NO_SECRETS": "1" if no_secrets else "",
        "DEBINFRA_SUDO_PASSWORD": _sudo_password(no_secrets, hostname),
    }
    _run_pyinfra("deploys/run.py", limit, dry, env)


@app.command()
def bootstrap(dry: bool = typer.Option(False, "--dry")):
    """Fresh-machine phase 1: gpg/pcscd/sops, zero secrets needed. Then plug in the YubiKey."""
    env = {
        "DEBINFRA_NO_SECRETS": "1",
        "DEBINFRA_SUDO_PASSWORD": _sudo_password(no_secrets=True),
    }
    _run_pyinfra("deploys/bootstrap.py", "@local", dry, env)


@app.command("list")
def list_tasks():
    """List every task selector and where it applies."""
    os.environ.setdefault("DEBINFRA_NO_SECRETS", "1")
    from debinfra import registry

    registry.load_all()
    for t in registry.TASKS.values():
        scope = ",".join(sorted(t.hosts) or sorted(t.machine_types) or sorted(t.groups)) or "all"
        note = "" if t.default else "  (explicit only)"
        typer.echo(f"{t.name:24s} [{scope}]{note}")


@secrets_app.command()
def edit(name: str = typer.Argument("all")):
    """Open secrets/<name>.sops.yaml in $EDITOR via sops."""
    raise typer.Exit(subprocess.run(["sops", f"secrets/{name}.sops.yaml"], cwd=REPO_ROOT).returncode)


@secrets_app.command()
def check():
    """Verify every secrets file is really encrypted and decryptable. Use as a pre-commit gate."""
    from debinfra import secrets as s

    problems = s.check()
    for p in problems:
        typer.secho(p, fg="red")
    if not problems:
        typer.secho("all secrets files encrypted and decryptable", fg="green")
    raise typer.Exit(1 if problems else 0)


if __name__ == "__main__":
    app()

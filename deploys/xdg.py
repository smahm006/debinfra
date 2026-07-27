"""XDG directory layout (port of roles/xdg)."""

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server

from debinfra.registry import task


def _dirs(kind: str) -> list[str]:
    out = []
    for layer in ("common", "group", "host"):
        out += host.data.get(f"xdg_{kind}_{layer}") or []
    return out


def _create(kind: str):
    user = host.data.home_user
    for path in _dirs(kind):
        files.directory(path=path, user=user, group=user, mode="755")


@task("xdg_config")
@deploy("XDG: config dirs")
def xdg_config():
    _create("config")


@task("xdg_data")
@deploy("XDG: data dirs")
def xdg_data():
    _create("data")


@task("xdg_state")
@deploy("XDG: state dirs")
def xdg_state():
    _create("state")


@task("xdg_cache")
@deploy("XDG: cache dirs")
def xdg_cache():
    _create("cache")


@task("xdg_home")
@deploy("XDG: home dirs")
def xdg_home():
    _create("home")


@task("xdg_clean")
@deploy("XDG: remove stock home dirs")
def xdg_clean():
    home = host.data.user_home
    for d in ("Desktop", "Documents", "Downloads", "Pictures", "Videos", "Music", "Templates", "Public"):
        files.directory(path=f"{home}/{d}", present=False)


@task("xdg_user_dirs")
@deploy("XDG: user-dirs.dirs")
def xdg_user_dirs():
    mapping = {
        "DOCUMENTS": "$HOME/org/inbox",
        "DOWNLOAD": "$HOME/dump",
        "TEMPLATES": "$HOME/inbox",
        "DESKTOP": "$HOME/inbox",
        "MUSIC": "$HOME/media/audio",
        "PICTURES": "$HOME/media/images",
        "VIDEOS": "$HOME/media/videos",
    }
    server.shell(
        name="Point xdg-user-dirs at the custom tree",
        commands=[f'xdg-user-dirs-update --set {k} "{v}"' for k, v in mapping.items()],
    )

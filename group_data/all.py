import os

from debinfra import secrets

_s = secrets.maybe("all")

# -- Identity -----------------------------------------------------------------
home_user = "smahm"
user_home = f"/home/{home_user}"
user_email = _s.get("user_email", "")
server_gateway = _s.get("server_gateway", "")
server_hosts = _s.get("server_hosts", {})

# sudo password comes from the CLI prompt, never from disk
_sudo_password = os.environ.get("DEBINFRA_SUDO_PASSWORD") or None
_use_sudo_password = bool(_sudo_password)

# -- XDG base dirs ------------------------------------------------------------
xdg_cache_home = f"{user_home}/.cache"
xdg_config_home = f"{user_home}/.config"
xdg_data_home = f"{user_home}/.local/share"
xdg_state_home = f"{user_home}/.local/state"
xdg_bin_home = f"{user_home}/.local/bin"

lab_home = f"{user_home}/lab"
dump_home = f"{user_home}/dump"
org_home = f"{user_home}/org"
apps_home = f"{user_home}/apps"

xdg_config_common = [
    xdg_config_home,
    f"{xdg_config_home}/git",
    f"{xdg_config_home}/gnupg",
    f"{xdg_config_home}/vim",
    f"{xdg_config_home}/python",
    f"{xdg_config_home}/npm",
    f"{xdg_config_home}/kube",
    f"{xdg_config_home}/zsh",
]

xdg_data_common = [
    xdg_data_home,
    f"{xdg_data_home}/python",
    f"{xdg_data_home}/npm",
    f"{xdg_data_home}/terminfo",
]

xdg_state_common = [
    xdg_state_home,
    f"{xdg_state_home}/bash",
    f"{xdg_state_home}/zsh",
    f"{xdg_state_home}/less",
    f"{xdg_state_home}/python",
    f"{xdg_state_home}/node",
    f"{xdg_state_home}/vim/backup",
    f"{xdg_state_home}/vim/swap",
    f"{xdg_state_home}/vim/undo",
    f"{xdg_state_home}/vim/view",
]

xdg_cache_common = [
    xdg_cache_home,
    f"{xdg_cache_home}/python",
    f"{xdg_cache_home}/zsh",
]

xdg_home_common = [
    lab_home,
    f"{lab_home}/resources",
    f"{lab_home}/toolchains",
    f"{lab_home}/toolchains/rust",
    f"{lab_home}/toolchains/go",
    f"{lab_home}/toolchains/go/sdk",
    f"{lab_home}/toolchains/go/path",
    f"{lab_home}/toolchains/zig",
    dump_home,
    org_home,
    apps_home,
]

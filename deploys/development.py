"""Developer toolchains (port of roles/development)."""

import json
import urllib.request

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.files import File
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import apt, files, server

from debinfra.apt import install_testing
from debinfra.registry import task

ZIG_VERSION = "0.16.0"
EMACS_BRANCH = "emacs-31"

GO_ARCH = {"x86_64": "amd64", "aarch64": "arm64"}


def _lab(sub: str = "") -> str:
    return f"{host.data.user_home}/lab{sub}"


def _bin_home() -> str:
    return f"{host.data.user_home}/.local/bin"


def _npm_global(name: str, packages: list[str]):
    """npm -g into the XDG prefix from ~/.config/npm/npmrc (no sudo, no nvm)."""
    home = host.data.user_home
    env = " ".join(
        [
            f'XDG_CONFIG_HOME="{home}/.config"',
            f'XDG_CACHE_HOME="{home}/.cache"',
            f'XDG_DATA_HOME="{home}/.local/share"',
            f'XDG_STATE_HOME="{home}/.local/state"',
            f'NPM_CONFIG_USERCONFIG="{home}/.config/npm/npmrc"',
        ]
    )
    server.shell(name=name, commands=[f"{env} npm install --global {' '.join(packages)}"])


@task("dev_python", machine_types={"laptop", "vm", "server"})
@deploy("Dev: python + uv")
def dev_python():
    apt.packages(packages=["python3-pip", "python3-venv", "python3-full"], _sudo=True)
    server.shell(
        name="install uv",
        commands=["curl -LsSf https://astral.sh/uv/install.sh | sh"],
        _if=lambda: host.get_fact(File, path=f"{_bin_home()}/uv") is None,
    )
    if "clients" in host.groups:
        for tool in ("ruff", "ty"):
            server.shell(
                name=f"uv tool install {tool}",
                commands=[f"{_bin_home()}/uv tool install --upgrade --force {tool}"],
            )


@task("dev_go", machine_types={"laptop", "vm", "server"})
@deploy("Dev: go toolchain")
def dev_go():
    arch = GO_ARCH[host.get_fact(Arch)]
    with urllib.request.urlopen("https://go.dev/dl/?mode=json") as r:
        go_version = json.load(r)[0]["version"]  # e.g. "go1.24.5"
    sdk = _lab("/toolchains/go/sdk")
    installed = host.get_fact(Command, command=f"{sdk}/bin/go version 2>/dev/null || true")
    if go_version not in (installed or ""):
        server.shell(
            name=f"install {go_version}",
            commands=[
                f"curl -fsSL -o /tmp/{go_version}.tar.gz https://golang.org/dl/{go_version}.linux-{arch}.tar.gz",
                f"rm -rf {sdk} && mkdir -p {sdk}",
                f"tar -C {sdk} --strip-components=1 -xzf /tmp/{go_version}.tar.gz",
            ],
        )
    if "clients" in host.groups:
        server.shell(
            name="go dev tools",
            commands=[
                f"GOROOT={sdk} GOPATH={_lab('/toolchains/go/path')} {sdk}/bin/go install {mod}"
                for mod in (
                    "golang.org/x/tools/gopls@latest",
                    "golang.org/x/tools/cmd/goimports@latest",
                    "mvdan.cc/gofumpt@latest",
                )
            ],
        )


@task("dev_rust", machine_types={"laptop", "vm", "server"})
@deploy("Dev: rust toolchain")
def dev_rust():
    rust = _lab("/toolchains/rust")
    env = f"CARGO_HOME={rust}/.cargo RUSTUP_HOME={rust}/.rustup"
    files.directory(path=rust, mode="755")
    server.shell(
        name="install rustup",
        commands=[
            "curl -fsSL -o /tmp/rustup-init.sh https://sh.rustup.rs",
            f"{env} sh /tmp/rustup-init.sh -y",
        ],
        _if=lambda: host.get_fact(File, path=f"{rust}/.cargo/bin/rustc") is None,
    )
    if "clients" in host.groups:
        server.shell(
            name="rust-src component",
            commands=[f"{env} {rust}/.cargo/bin/rustup component add rust-src"],
        )


@task("dev_zig", machine_types={"laptop", "vm", "server"})
@deploy("Dev: zig toolchain")
def dev_zig():
    zig_arch = {"x86_64": "x86_64", "aarch64": "aarch64", "armv7l": "arm"}[host.get_fact(Arch)]
    zig = _lab("/toolchains/zig")
    installed = host.get_fact(Command, command=f"{zig}/zig version 2>/dev/null || true")
    if ZIG_VERSION not in (installed or ""):
        server.shell(
            name=f"install zig {ZIG_VERSION}",
            commands=[
                f"curl -fsSL -o /tmp/zig.tar.xz https://ziglang.org/download/{ZIG_VERSION}/zig-{zig_arch}-linux-{ZIG_VERSION}.tar.xz",
                f"rm -rf {zig} && mkdir -p {zig}",
                f"tar -C {zig} --strip-components=1 -xJf /tmp/zig.tar.xz",
            ],
        )


@task("dev_node", machine_types={"laptop", "vm", "server"})
@deploy("Dev: node from testing")
def dev_node():
    install_testing("node + npm from testing", ["nodejs", "npm"])
    _npm_global("pnpm", ["pnpm"])
    if "clients" in host.groups:
        _npm_global("node language servers", ["yaml-language-server", "vscode-langservers-extracted"])


@task("dev_shell", machine_types={"laptop", "vm", "server"})
@deploy("Dev: shell stack (zsh + plugins, starship, atuin, zoxide)")
def dev_shell():
    home = host.data.user_home
    apt.packages(
        name="shell packages",
        packages=[
            "shfmt",
            "shellcheck",
            "starship",
            "atuin",
            "zoxide",
            "zsh",
            "zsh-autosuggestions",
            "zsh-syntax-highlighting",
        ],
        _sudo=True,
    )

    server.user(
        name="zsh as login shell",
        user=host.data.home_user,
        shell="/usr/bin/zsh",
        _sudo=True,
    )

    # one-time: seed zsh history from the old bash history (plain format is compatible)
    server.shell(
        name="seed zsh history from bash history",
        commands=[
            f"mkdir -p {home}/.local/state/zsh && cp {home}/.local/state/bash/history {home}/.local/state/zsh/history"
        ],
        _if=lambda: host.get_fact(File, path=f"{home}/.local/state/zsh/history") is None
        and host.get_fact(File, path=f"{home}/.local/state/bash/history") is not None,
    )

    if "clients" in host.groups:
        _npm_global("bash-language-server", ["bash-language-server"])


@task("dev_yaml", machine_types={"laptop", "vm", "server"})
@deploy("Dev: yaml tooling")
def dev_yaml():
    for tool in ("yamllint", "yamlfmt"):
        server.shell(name=f"uv tool install {tool}", commands=[f"{_bin_home()}/uv tool install --upgrade --force {tool}"])


@task("dev_cpp", groups={"clients"})
@deploy("Dev: clang toolchain")
def dev_cpp():
    apt.packages(packages=["clang", "clang-tidy", "clang-tools"], update=True, no_recommends=True, _sudo=True)


@task("dev_emacs", groups={"clients"})
@deploy("Dev: emacs from the emacs-31 release branch")
def dev_emacs():
    installed = host.get_fact(Command, command="emacs --version 2>/dev/null | head -1 || true") or ""
    if "GNU Emacs 31" in installed:
        _emacs_daemon()
        return

    gcc_major = (host.get_fact(Command, command="gcc -dumpversion") or "").strip().split(".")[0]
    apt.packages(
        name="emacs build deps",
        packages=[
            f"libgcc-{gcc_major}-dev",
            f"libgccjit-{gcc_major}-dev",
            "libacl1-dev",
            "libc6-dev",
            "libgnutls28-dev",
            "libgpm-dev",
            "libgtk-3-dev",
            "libjpeg-dev",
            "libncurses-dev",
            "libnotify-dev",
            "libpng-dev",
            "librsvg2-dev",
            "libsqlite3-dev",
            "libtiff-dev",
            "libtree-sitter-dev",
            "libx11-dev",
            "libxml2-dev",
            "libmagickwand-dev",
        ],
        update=True,
        no_recommends=True,
        _sudo=True,
    )
    src = "/tmp/emacs-31-src"
    server.shell(
        name=f"clone {EMACS_BRANCH} branch",
        commands=[
            f"rm -rf {src}",
            f"git clone --depth 1 --branch {EMACS_BRANCH} https://git.savannah.gnu.org/git/emacs.git {src}",
        ],
    )
    server.shell(
        name="build emacs (native-comp, pgtk, tree-sitter)",
        commands=[
            (
                f"cd {src} && ./autogen.sh && "
                "./configure --with-native-compilation --without-ns --without-x "
                "--with-pgtk --with-tree-sitter --with-imagemagick && "
                "make -j$(nproc)"
            )
        ],
    )
    server.shell(name="install emacs", commands=[f"cd {src} && make install"], _sudo=True)
    _emacs_daemon()


def _emacs_daemon():
    # make install ships a user unit at /usr/local/lib/systemd/user/emacs.service;
    # clients open frames on it via emacsclient (EDITOR/mod+e are wired to it)
    server.shell(
        name="enable emacs daemon (systemd user unit)",
        commands=["systemctl --user enable --now emacs.service"],
    )

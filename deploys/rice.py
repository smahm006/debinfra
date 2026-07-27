"""Sway desktop stack for graphical clients (port of roles/rice; tofi replaced by rofi)."""

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.files import File
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server, systemd

from debinfra.apt import install_testing
from debinfra.github import latest_asset
from debinfra.registry import task


@task("rice_sway", groups={"clients"})
@deploy("Rice: sway stack")
def rice_sway():
    apt.packages(
        name="sway + wayland packages",
        packages=[
            "sway",
            "swaylock",
            "swayidle",
            "sway-notification-center",
            "wl-clipboard",
            "grim",
            "grimshot",
            "foot",
            "libwayland-dev",
            "wayland-protocols",
            "hwdata",
        ],
        update=True,
        no_recommends=True,
        _sudo=True,
    )
    if host.get_fact(Command, command="which chayang || true") == "":
        server.shell(
            name="build chayang from source (not packaged)",
            commands=[
                "rm -rf /tmp/chayang && git clone https://gitlab.freedesktop.org/emersion/chayang.git /tmp/chayang",
                "cd /tmp/chayang && meson build && ninja -C build",
            ],
        )
        server.shell(name="install chayang", commands=["cd /tmp/chayang && ninja -C build install"], _sudo=True)


@task("rice_waybar", groups={"clients"})
@deploy("Rice: waybar")
def rice_waybar():
    apt.packages(name="waybar", packages=["waybar"], _sudo=True)


@task("rice_menu", groups={"clients"})
@deploy("Rice: rofi 2.x (wayland) + cliphist")
def rice_menu():
    install_testing("rofi 2.x from testing", ["rofi"])

    files.download(
        name="cliphist binary",
        src=latest_asset("sentriz/cliphist", "linux-amd64"),
        dest=f"{host.data.user_home}/.local/bin/cliphist",
        mode="755",
    )


@task("rice_fonts", groups={"clients"})
@deploy("Rice: fonts")
def rice_fonts():
    apt.packages(name="noto fonts", packages=["fonts-noto"], _sudo=True)
    fonts = f"{host.data.user_home}/.local/share/fonts"
    downloads = {
        "MapleMono": "https://github.com/subframe7536/Maple-font/releases/latest/download/MapleMonoNormal-TTF.zip",
        "SourceCodePro": "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/SourceCodePro.zip",
        "NerdFontsSymbolsOnly": "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/NerdFontsSymbolsOnly.zip",
    }
    changed = False
    for name, url in downloads.items():
        if host.get_fact(Command, command=f"ls {fonts}/{name}/*.ttf >/dev/null 2>&1 && echo yes || true") != "yes":
            server.shell(
                name=f"install {name} fonts",
                commands=[
                    f"curl -fsSL -o /tmp/{name}.zip {url}",
                    f"mkdir -p {fonts}/{name} && unzip -o /tmp/{name}.zip -d {fonts}/{name}",
                ],
            )
            changed = True
    if changed:
        server.shell(name="refresh font cache", commands=["fc-cache -f"])


@task("rice_theme", groups={"clients"})
@deploy("Rice: GTK dark theme")
def rice_theme():
    block = (
        "[Settings]\n"
        "gtk-application-prefer-dark-theme=1\n"
        "gtk-theme-name=Materia-Blackout\n"
        "gtk-icon-theme-name=Materia-Blackout-Icons\n"
        "gtk-cursor-theme-name=Notwaita-Black\n"
    )
    for ver in ("gtk-3.0", "gtk-4.0"):
        files.block(
            name=f"dark mode for {ver}",
            path=f"{host.data.user_home}/.config/{ver}/settings.ini",
            content=block,
            try_prevent_shell_expansion=True,
            marker="# {mark} CUSTOM CONFIGURATION",
        )


@task("rice_ly", groups={"clients"})
@deploy("Rice: ly display manager")
def rice_ly():
    zig = f"{host.data.user_home}/lab/toolchains/zig/zig"
    if host.get_fact(File, path="/usr/bin/ly") is None:
        server.shell(
            name="clone + build ly",
            commands=[
                "rm -rf /tmp/ly && git clone https://codeberg.org/fairyglade/ly.git /tmp/ly",
                f"cd /tmp/ly && {zig} build",
            ],
        )
        server.shell(
            name="install ly (systemd)",
            commands=[f"cd /tmp/ly && {zig} build installexe -Dinit_system=systemd"],
            _sudo=True,
        )
    # ly installs templated units; the session runs on tty2
    systemd.service(service="ly@tty2", running=True, enabled=True, _sudo=True)


@task("rice_keyd", machine_types={"laptop"})
@deploy("Rice: keyd (laptop keyboard remap)")
def rice_keyd():
    if host.get_fact(Command, command="which keyd || true") == "":
        server.shell(
            name="clone + build keyd",
            commands=[
                "rm -rf /tmp/keyd && git clone https://github.com/rvaiya/keyd /tmp/keyd",
                "cd /tmp/keyd && make -j$(nproc)",
            ],
        )
        server.shell(name="install keyd", commands=["cd /tmp/keyd && make install"], _sudo=True)
    systemd.service(service="keyd", running=True, enabled=True, _sudo=True)

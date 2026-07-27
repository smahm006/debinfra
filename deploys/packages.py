"""apt packages (port of roles/packages)."""

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import apt, files, server

from debinfra.dotutil import GRAPHICAL_TYPES
from debinfra.registry import task


def _apt(name, packages, recommends=False):
    apt.packages(name=name, packages=packages, no_recommends=not recommends, _sudo=True)


@task("pkg_base")
@deploy("Packages: base")
def pkg_base():
    apt.update(name="apt update", cache_time=3600, _sudo=True)
    _apt(
        "base packages",
        [
            "apt-transport-https",
            "bash-completion",
            "build-essential",
            "ca-certificates",
            "curl",
            "dkms",
            "git",
            "gnupg",
            "gnupg2",
            "linux-base",
            "lsb-release",
            "man-db",
            "manpages",
            "net-tools",
            "openssh-server",
            "suckless-tools",
            "wget",
        ],
    )


@task("pkg_build")
@deploy("Packages: build tools")
def pkg_build():
    _apt(
        "build tools",
        ["automake", "autotools-dev", "cmake", "gcc", "make", "meson", "ninja-build", "scdoc", "texinfo"],
    )


@task("pkg_network")
@deploy("Packages: network")
def pkg_network():
    _apt(
        "network packages",
        ["ca-certificates", "curl", "network-manager", "nmap", "wget", "net-tools", "wireless-tools"],
    )
    if host.data.machine_type == "laptop":
        _apt("laptop network packages", ["iwd"])
    if "servers" in host.groups:
        _apt("server network packages", ["openssh-server"])


@task("pkg_security")
@deploy("Packages: security")
def pkg_security():
    _apt(
        "security packages",
        [
            "cryptsetup",
            "dirmngr",
            "gnupg-agent",
            "pinentry-tty",
            "pinentry-gnome3",
            "pcscd",
            "scdaemon",
            "yubikey-manager",
            "yubikey-personalization",
        ],
    )


@task("pkg_power", machine_types={"laptop"})
@deploy("Packages: laptop power")
def pkg_power():
    _apt("laptop power packages", ["acpi", "tlp", "upower"], recommends=True)


@task("pkg_utility")
@deploy("Packages: utilities")
def pkg_utility():
    _apt(
        "utility packages",
        [
            "bc",
            "ethtool",
            "fd-find",
            "fzf",
            "gzip",
            "jq",
            "mediainfo",
            "nano",
            "ncdu",
            "nvme-cli",
            "p7zip",
            "parallel",
            "parted",
            "ripgrep",
            "scdaemon",
            "scdoc",
            "screen",
            "trash-cli",
            "tree",
            "udevil",
            "unrar-free",
            "usbutils",
            "xdg-user-dirs",
            "xdg-user-dirs-gtk",
            "xdg-utils",
            "yq",
            "zip",
        ],
    )
    if host.data.machine_type == "laptop":
        _apt("laptop utility packages", ["brightnessctl"])
    if host.data.machine_type in GRAPHICAL_TYPES:
        _apt("desktop utility packages", ["desktop-file-utils"])


@task("pkg_vm", machine_types={"vm"})
@deploy("Packages: VMware guest tools")
def pkg_vm():
    _apt("open-vm-tools", ["open-vm-tools", "open-vm-tools-desktop"], recommends=True)


@task("pkg_apps")
@deploy("Packages: applications")
def pkg_apps():
    _apt("application packages", ["gparted", "vim"])
    if "clients" in host.groups:
        _apt(
            "client desktop applications",
            [
                "blueman",
                "sxiv",
                "thunar",
                "thunar-archive-plugin",
                "thunar-media-tags-plugin",
                "thunar-volman",
                "zathura",
            ],
        )
        _apt(
            "client applications",
            [
                "libreoffice",
                "mupdf",
                "qbittorrent",
                "redshift-gtk",
                "ffmpeg",
                "ffmpegthumbnailer",
                "imagemagick",
                "wine",
            ],
        )
    if "servers" in host.groups:
        _apt(
            "server applications",
            [
                "fail2ban",
                "htop",
                "iotop",
                "lsof",
                "nftables",
                "strace",
                "tcpdump",
                "unattended-upgrades",
                "apt-listchanges",
            ],
        )


@task("pkg_audio", groups={"clients"})
@deploy("Packages: audio")
def pkg_audio():
    _apt("audio packages", ["pipewire-pulse", "wireplumber", "pulseaudio-utils"])


@task("pkg_android", groups={"clients"})
@deploy("Packages: android tools")
def pkg_android():
    _apt("android tools", ["adb", "fastboot", "heimdall-flash"])


@task("pkg_firefox", groups={"clients"})
@deploy("Packages: firefox (Mozilla repo)")
def pkg_firefox():
    files.directory(path="/etc/apt/keyrings", mode="755", _sudo=True)
    files.download(
        name="Mozilla apt signing key",
        src="https://packages.mozilla.org/apt/repo-signing-key.gpg",
        dest="/etc/apt/keyrings/packages.mozilla.org.asc",
        mode="644",
        _sudo=True,
    )
    mozilla_sources = (
        "Types: deb\n"
        "URIs: https://packages.mozilla.org/apt\n"
        "Suites: mozilla\n"
        "Components: main\n"
        "Signed-By: /etc/apt/keyrings/packages.mozilla.org.asc\n"
    )
    src = files.block(
        name="Mozilla apt repository",
        path="/etc/apt/sources.list.d/mozilla.sources",
        content=mozilla_sources,
        try_prevent_shell_expansion=True,
        marker="# {mark} debinfra",
        _sudo=True,
    )
    files.block(
        name="Pin Mozilla repository",
        path="/etc/apt/preferences.d/mozilla",
        content="Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000\n",
        try_prevent_shell_expansion=True,
        marker="# {mark} debinfra",
        _sudo=True,
    )
    apt.update(name="apt update (mozilla repo)", _sudo=True, _if=src.did_change)
    apt.packages(name="firefox", packages=["firefox"], _sudo=True)


@task("pkg_flatpak", groups={"clients"})
@deploy("Packages: flatpak apps")
def pkg_flatpak():
    _apt("flatpak", ["flatpak"])
    server.shell(
        name="add flathub remote",
        commands=["flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo"],
        _sudo=True,
    )
    for app in ("com.fastmail.Fastmail", "com.bitwarden.desktop"):
        server.shell(
            name=f"flatpak install {app}",
            commands=[f"flatpak install --noninteractive flathub {app}"],
        )
    if host.data.machine_type in GRAPHICAL_TYPES:
        # add Wayland flags to exported .desktop launchers
        server.shell(
            name="Wayland flags in flatpak .desktop files",
            commands=[
                r"""for f in /var/lib/flatpak/exports/share/applications/*.desktop; do
  [ -e "$f" ] || continue
  sed -i -E 's|^(Exec=.*flatpak run\s+(-[^ ]+\s+)*)([^ ]+)(.*)$|\1--socket=wayland \3 -ozone-platform-hint=auto --enable-features=WaylandWindowDecorations\4|' "$(readlink -f "$f")"
done"""
            ],
            _sudo=True,
        )


@task("pkg_unattended", groups={"servers"})
@deploy("Packages: unattended upgrades")
def pkg_unattended():
    from debinfra import secrets

    _apt("unattended-upgrades", ["unattended-upgrades", "apt-listchanges"])
    server.shell(
        name="enable automatic security upgrades",
        commands=[
            'echo "unattended-upgrades unattended-upgrades/enable_auto_updates boolean true" | debconf-set-selections',
            "dpkg-reconfigure -f noninteractive unattended-upgrades",
        ],
        _sudo=True,
    )
    email = secrets.load("all").get("user_email", "")
    if email:
        files.line(
            name="unattended-upgrades mail address",
            path="/etc/apt/apt.conf.d/50unattended-upgrades",
            line=f'Unattended-Upgrade::Mail "{email}";',
            replace=f'Unattended-Upgrade::Mail "{email}";',
            _sudo=True,
        )


@task("pkg_upgrade")
@deploy("Packages: full upgrade")
def pkg_upgrade():
    apt.update(name="apt update", _sudo=True)
    apt.dist_upgrade(name="apt full-upgrade", _sudo=True)

"""Shared apt helpers: the low-pinned testing suite."""

import io

from pyinfra.operations import apt, files, server

TESTING_SOURCES = "deb http://deb.debian.org/debian/ testing main contrib non-free non-free-firmware\n"
TESTING_PREFS = """\
Package: *
Pin: release a=testing
Pin-Priority: 10
"""


def enable_testing():
    """Add the testing suite, pinned low so nothing moves unless asked for by -t testing."""
    src = files.put(
        name="testing apt source (low pin)",
        src=io.StringIO(TESTING_SOURCES),
        dest="/etc/apt/sources.list.d/testing-unsable.list",
        mode="644",
        _sudo=True,
    )
    files.put(
        name="pin testing at low priority",
        src=io.StringIO(TESTING_PREFS),
        dest="/etc/apt/preferences.d/testing-unsable",
        mode="644",
        _sudo=True,
    )
    apt.update(name="apt update (testing)", _sudo=True, _if=src.did_change)


def install_testing(name: str, packages: list[str]):
    """Install packages from testing (apt.packages has no suite selector)."""
    enable_testing()
    server.shell(
        name=name,
        commands=[f"apt-get install -y -t testing {' '.join(packages)}"],
        _sudo=True,
    )

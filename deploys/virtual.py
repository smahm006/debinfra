"""Docker, vagrant, kubectl, k3s (port of roles/virtual)."""

import subprocess
import sys
import urllib.request

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.files import File
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import apt, files, server, systemd

from debinfra import secrets
from debinfra.registry import task

K8S_ARCH = {"x86_64": "amd64", "aarch64": "arm64"}


@task("virt_docker", hosts={"sm-laptop", "sm-server"})
@deploy("Virtual: docker")
def virt_docker():
    if host.get_fact(Command, command="which docker || true") == "":
        server.shell(
            name="install docker (get.docker.com)",
            commands=[
                "curl -fsSL -o /tmp/get-docker.sh https://get.docker.com",
                "sh /tmp/get-docker.sh",
            ],
            _sudo=True,
        )
    server.user(
        name="add user to docker group",
        user=host.data.home_user,
        groups=["docker"],
        append=True,
        _sudo=True,
    )


@task("virt_vagrant", groups={"clients"}, hosts={"sm-laptop"})
@deploy("Virtual: vagrant-libvirt")
def virt_vagrant():
    apt.packages(
        packages=["vagrant-libvirt", "libvirt-daemon-system"],
        update=True,
        _sudo=True,
    )
    server.user(
        name="add user to libvirt group",
        user=host.data.home_user,
        groups=["libvirt"],
        append=True,
        _sudo=True,
    )


@task("virt_kubectl", hosts={"sm-laptop", "sm-server"})
@deploy("Virtual: kubectl")
def virt_kubectl():
    with urllib.request.urlopen("https://dl.k8s.io/release/stable.txt") as r:
        stable = r.read().decode().strip()
    arch = K8S_ARCH[host.get_fact(Arch)]
    files.download(
        name=f"kubectl {stable}",
        src=f"https://dl.k8s.io/release/{stable}/bin/linux/{arch}/kubectl",
        dest="/usr/local/bin/kubectl",
        mode="755",
        _sudo=True,
    )
    files.directory(
        path=f"{host.data.user_home}/.config/kube",
        user=host.data.home_user,
        group=host.data.home_user,
        mode="700",
    )


@task("virt_k3s", hosts={"sm-server"})
@deploy("Virtual: k3s")
def virt_k3s():
    if host.get_fact(File, path="/usr/local/bin/k3s") is None:
        server.shell(
            name="install k3s",
            commands=[
                "curl -fsSL -o /tmp/k3s-install.sh https://get.k3s.io",
                "INSTALL_K3S_EXEC='--disable servicelb --disable local-storage' sh /tmp/k3s-install.sh",
            ],
            _sudo=True,
        )
    systemd.service(service="k3s", running=True, enabled=True, _sudo=True)
    server.shell(
        name="user-accessible kubeconfig",
        commands=[
            f"install -o {host.data.home_user} -g {host.data.home_user} -m 600 "
            f"/etc/rancher/k3s/k3s.yaml {host.data.user_home}/.config/kube/config"
        ],
        _sudo=True,
    )


@task("virt_kubeconfig", hosts={"sm-laptop"})
@deploy("Virtual: fetch kubeconfig from sm-server")
def virt_kubeconfig():
    import io

    net = secrets.load("all").get("server_hosts", {}).get("sm-server", {})
    target = net.get("ip", "sm-server")
    port = str(net.get("port", 22))
    try:
        raw = subprocess.run(
            ["ssh", "-p", port, f"{host.data.home_user}@{target}", "cat ~/.config/kube/config"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"[debinfra] skipping kubeconfig fetch (sm-server unreachable: {e})", file=sys.stderr)
        return
    raw = raw.replace("https://127.0.0.1:6443", f"https://{net.get('ip', 'sm-server')}:6443")
    files.directory(path=f"{host.data.user_home}/.config/kube", mode="700")
    files.put(
        name="deploy kubeconfig",
        src=io.StringIO(raw),
        dest=f"{host.data.user_home}/.config/kube/config",
        mode="600",
    )

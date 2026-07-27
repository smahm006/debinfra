"""Odoo on the k3s single node (replaces the InvenTree cluster role)."""

import io

import yaml as pyyaml

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server

from debinfra import FILES, secrets
from debinfra.registry import task

MANIFESTS = ("namespace.yaml", "configmap.yaml", "database.yaml", "server.yaml")


@task("cluster_odoo", hosts={"sm-server"})
@deploy("Cluster: odoo")
def cluster_odoo():
    user = host.data.home_user
    for sub in ("", "/db", "/data", "/manifests", "/backups"):
        files.directory(path=f"/opt/odoo{sub}", user=user, group=user, mode="755", _sudo=True)

    for name in MANIFESTS + ("backup.sh", "restore.sh"):
        src = FILES / "odoo" / name
        mode = "755" if name.endswith(".sh") else "644"
        files.put(src=str(src), dest=f"/opt/odoo/manifests/{name}", user=user, group=user, mode=mode)

    server.shell(
        name="apply namespace",
        commands=["kubectl apply -f /opt/odoo/manifests/namespace.yaml"],
    )

    # render the k8s Secret locally from sops, push via tmpfs, apply, remove
    data = secrets.load("odoo")
    manifest = pyyaml.safe_dump(
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "odoo-secrets", "namespace": "odoo"},
            "stringData": data,
        }
    )
    files.put(src=io.StringIO(manifest), dest="/dev/shm/odoo-secret.yaml", mode="600")
    server.shell(
        name="apply odoo secret",
        commands=[
            "kubectl apply -f /dev/shm/odoo-secret.yaml",
            "rm -f /dev/shm/odoo-secret.yaml",
        ],
    )

    for name in ("configmap.yaml", "database.yaml", "server.yaml"):
        server.shell(name=f"apply {name}", commands=[f"kubectl apply -f /opt/odoo/manifests/{name}"])

    server.crontab(
        name="odoo backup cron",
        command="BACKUP_DIR=/opt/odoo/backups /opt/odoo/manifests/backup.sh",
        cron_name="odoo-backup",
        hour=3,
        minute=0,
    )


@task("cluster_odoo_backup", hosts={"sm-server"}, default=False)
@deploy("Cluster: odoo backup now")
def cluster_odoo_backup():
    server.shell(
        name="run odoo backup",
        commands=["BACKUP_DIR=/opt/odoo/backups /opt/odoo/manifests/backup.sh"],
    )


@task("cluster_odoo_restore", hosts={"sm-server"}, default=False)
@deploy("Cluster: odoo restore latest snapshot")
def cluster_odoo_restore():
    server.shell(
        name="run odoo restore (latest)",
        commands=["echo y | BACKUP_DIR=/opt/odoo/backups /opt/odoo/manifests/restore.sh"],
    )

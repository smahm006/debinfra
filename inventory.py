import socket

from debinfra import secrets

_current = socket.gethostname()
_net = secrets.maybe("all").get("server_hosts", {})


def _mk(name: str, machine_type: str):
    data = {
        "hostname": name,
        "machine_type": machine_type,
        "home_user": "smahm",
        "user_home": "/home/smahm",
        "is_local": name == _current,
    }
    if name == _current:
        return ("@local", data)
    net = _net.get(name, {})
    return (
        name,
        {
            **data,
            "ssh_user": "smahm",
            "ssh_hostname": net.get("ip", name),  # falls back to ~/.ssh/config resolution
            "ssh_port": net.get("port", 22),
        },
    )


clients = [_mk("sm-laptop", "laptop"), _mk("sm-vm", "vm")]
servers = [_mk("sm-server", "server"), _mk("sm-rpi", "rpi")]

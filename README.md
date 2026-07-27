# debinfra

Provisioning for my Debian machines, powered by
[pyinfra](https://pyinfra.com).

## Fresh machine

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone git@github.com:smahm006/debinfra.git ~/lab/projects/public/debinfra
cd ~/lab/projects/public/debinfra
uv sync
uv run debinfra bootstrap     # gpg/pcscd/sops + gnupg dotfiles, zero secrets needed
# plug in the YubiKey, then:
uv run debinfra deploy        # everything for this machine
```

After the first deploy, `~/.local/bin/debinfra` is on PATH and wraps `uv run`.

## Usage

```sh
debinfra deploy                     # all default tasks for this machine
debinfra deploy pkg                 # every pkg_* task
debinfra deploy dev go              # dev_go ("spaces join, commas separate")
debinfra deploy dot home, rice      # dot_home + all rice_*
debinfra deploy --target server     # provision sm-server over SSH
debinfra deploy --skip rice         # everything except rice_*
debinfra deploy --dry               # don't execute
debinfra deploy --no-secrets        # skip anything needing sops
debinfra list                       # all selectors and their scope
debinfra secrets edit [name]        # sops-edit secrets/<name>.sops.yaml
debinfra secrets check              # verify everything is encrypted + decryptable
```

The sudo password comes from `sudo_password:` in `secrets/<hostname>.sops.yaml`
(per-host, e.g. `sm-laptop.sops.yaml`) or `secrets/all.sops.yaml` (shared), else it
is prompted. Secrets are sops-encrypted with
the YubiKey GPG key; on a fresh machine nothing but `bootstrap` is possible until the
YubiKey is present — that is the design.

Enable the commit guard once per clone:

```sh
git config core.hooksPath .githooks
```

## Layout

- `inventory.py` — hosts/groups; the current machine connects as `@local`
- `group_data/` — data per group (all/clients/servers)
- `secrets/` — sops-encrypted YAML (the ONLY place secrets live)
- `debinfra/` — CLI (typer), task registry, sops wrapper
- `deploys/` — one module per area; every function is a `debinfra list` selector
- `files/dotfiles/{common,graphical,laptop,vm,server,rpi}/{home,root}/` — layered
  dotfiles; symlinked on the local machine, copied over SSH
- `files/odoo/` — k8s manifests + backup/restore for the Odoo instance
- `templates/` — jinja2 (sshd, nftables, fail2ban, ssh client config)

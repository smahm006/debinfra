"""Task registry: replicates the old Ansible tag scheme as named deploy functions.

Selector grammar (unchanged from debstrap):
  "pkg"       -> every task named pkg or pkg_*
  "pkg_base"  -> exactly pkg_base
  []          -> every task with default=True
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Task:
    name: str
    fn: Callable
    groups: set[str] = field(default_factory=set)  # empty = all hosts
    hosts: set[str] = field(default_factory=set)  # e.g. {"sm-server"}
    machine_types: set[str] = field(default_factory=set)  # e.g. {"laptop", "vm"}
    default: bool = True  # False = only runs when named explicitly

    def applies(self, host) -> bool:
        hostname = host.data.get("hostname", host.name)
        if self.hosts and hostname not in self.hosts:
            return False
        if self.groups and not (self.groups & set(host.groups)):
            return False
        if self.machine_types and host.data.get("machine_type") not in self.machine_types:
            return False
        return True


TASKS: dict[str, Task] = {}  # insertion-ordered == execution order


def task(
    name: str,
    groups: set[str] | None = None,
    hosts: set[str] | None = None,
    machine_types: set[str] | None = None,
    default: bool = True,
):
    def wrap(fn):
        if name in TASKS:
            raise ValueError(f"duplicate task name: {name}")
        TASKS[name] = Task(name, fn, groups or set(), hosts or set(), machine_types or set(), default)
        return fn

    return wrap


def _matches(name: str, selector: str) -> bool:
    return name == selector or name.startswith(selector + "_")


def resolve(selectors: list[str], skip: list[str]) -> list[Task]:
    picked = [
        t
        for t in TASKS.values()
        if (not selectors and t.default) or any(_matches(t.name, s) for s in selectors)
    ]
    return [t for t in picked if not any(_matches(t.name, s) for s in skip)]


def load_all():
    """Import every deploy module; import order is the old playbook role order."""
    import deploys.xdg  # noqa: F401
    import deploys.dotfiles  # noqa: F401
    import deploys.packages  # noqa: F401
    import deploys.authentication  # noqa: F401
    import deploys.development  # noqa: F401
    import deploys.virtual  # noqa: F401
    import deploys.rice  # noqa: F401
    import deploys.cluster  # noqa: F401

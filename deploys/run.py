"""The single parameterized deploy file pyinfra executes (once per targeted host).

Selection comes from DEBINFRA_TASKS / DEBINFRA_SKIP env vars, set by the debinfra CLI.
"""

import os

from pyinfra import host

from debinfra import registry

registry.load_all()

_sel = [s for s in os.environ.get("DEBINFRA_TASKS", "").split(",") if s]
_skip = [s for s in os.environ.get("DEBINFRA_SKIP", "").split(",") if s]

_tasks = registry.resolve(_sel, _skip)
_unknown = [
    s for s in _sel if not any(t.name == s or t.name.startswith(s + "_") for t in registry.TASKS.values())
]
if _unknown:
    raise SystemExit(f"unknown selector(s): {', '.join(_unknown)} — see `debinfra list`")

for _t in _tasks:
    if _t.applies(host):
        _t.fn()

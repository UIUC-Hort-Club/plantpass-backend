# Agent skills

Skills for both PlantPass repos live in `skills/`. `.claude/skills` is a symlink to it,
so Claude Code and any agent that reads `.agents/skills` see the same files.

## Ours

The path a feature takes. Each one stops for the architect where it says so.

| Skill | Does | Stops for the architect |
|---|---|---|
| `plan-feature` | Decides whether a feature should exist; writes a one-page spec | Always, before any code |
| `build-feature` | Implements an approved spec in both repos, with tests | If there is no approved spec |
| `check` | Runs every local check in both repos and reports honestly | No |
| `ship` | Pull requests, CI, independent review, merge, deploy watch, smoke test | When its merge gate is not met (decision D10), and always inside a freeze window |

## Vendored: ponytail

`ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt` are copied
unmodified from <https://github.com/DietrichGebert/ponytail> (MIT, see
`skills/ponytail/LICENSE`), version 5.3.3, commit `96608e0`, copied 2026-11-14.

They are plain instruction files. The upstream plugin's hooks, status band and
usage ledger are not installed, and `ponytail-gain` and `ponytail-help` were
left out because they only describe those plugin features.

To update: copy the four `SKILL.md` files from upstream again, read the diff,
and change the commit above. Do not edit them in place; put PlantPass-specific
rules in `AGENTS.md` or in our own skills.

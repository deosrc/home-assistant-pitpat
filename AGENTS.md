# AGENTS.md

## Project

Home Assistant custom integration (**HACS**) for the PitPat pet GPS tracker. Domain: `pitpat`. Not affiliated with or endorsed by PitPat. Experimental hobby project.

## Repository layout

- `custom_components/pitpat/` — the integration itself:
  - `__init__.py` — entry setup/unload, `PLATFORMS` list, options update listener.
  - `api.py` — async aiohttp client for PitPat's OAuth + REST APIs (auth, api, activity, location hosts).
  - `coordinator.py` — `PitPatDataUpdateCoordinator` (`DataUpdateCoordinator`) that periodically polls the API and caches data.
  - `entity.py` — shared base entity class.
  - `sensor.py`, `binary_sensor.py`, `button.py`, `select.py`, `device_tracker.py` — platform entities built on the coordinator data. Each uses an `EntityDescription` subclass with an `applicable_devices` filter.
  - `config_flow.py`, `options_flow.py` — setup + options (poll interval, signal-lost-after-overdue).
  - `statistics.py` — imports historical activity into the recorder (requires `recorder` dependency).
  - `typeutils.py`, `const.py` — type helpers and constants (device model enums, API mappings).
  - `manifest.json`, `strings.json`, `translations/en.json`.
- `tests/` — plain `unittest` tests for `const`, `coordinator` (pure helpers such as `_day_is_today`), `statistics`, `typeutils`.
- `mockoon/` — Mockoon definitions (`auth.json`, `api.json`, `activity.json`, `location.json`) for mocking PitPat APIs locally.
- `blueprints/automation/` — example automation blueprints.
- `debug_configuration.yaml`, `.vscode/run-ha.sh` — local test HA instance (Docker); `.vscode/launch.json` attaches debugpy on port 5678.
- `.devcontainer/` — dev container (Ubuntu + Python 3.14 + docker-in-docker).
- `.github/workflows/` — CI; `.github/release.yaml` groups release notes by PR label (`breaking-change`, `bug`, `enhancement`, `ignore-for-release`).
- `hacs.json` — HACS metadata (minimum HA version).

## Commands

- Run tests: `python -m unittest discover -v -s './tests/'` (there is no pytest — `unittest` only).
- Install deps: `pip install -r requirements.txt` (pins `homeassistant==2026.1.3`).
- Local HA: `./.vscode/run-ha.sh` mounts `custom_components/` into a Docker HA container on port 8123; config comes from `debug_configuration.yaml`.
- Mock the PitPat APIs: run Mockoon with the definitions in `mockoon/` and temporarily swap the `__HOST_*` constants in `api.py` for the commented-out `localhost:5100`–`5103` ones (don't commit that change).

## Code style

- Python: 4-space indent, type hints (`X | None` unions; `Dict`/`Any` from `typing`), module-level `_LOGGER = logging.getLogger(__name__)`. Only `const.py` and `statistics.py` use `from __future__ import annotations`; add it where forward references need it.
- JSON/YAML: 2-space indent (see `.editorconfig`).
- No linter/formatter is configured locally; CI runs **hassfest** and the **HACS action** (`validation_and_formatting.yaml`), plus GitHub Actions "Tests" workflow against Python 3.14.

## Conventions & constraints

- Integration type is a `cloud_polling` hub with `config_flow: true`; do not break config/options flow compatibility.
- Requires Home Assistant 2026.1.3+ and Python 3.14 (devcontainer + CI pin this). Keep `requirements.txt`, `hacs.json`, and the image tag in `.vscode/run-ha.sh` on the same HA version.
- All entity state comes from `coordinator.data`; entities never fetch from the API. Buttons/selects run actions via `self.coordinator.api_client` (`press_fn`/`update_fn` on the description) and then refresh the coordinator.
- `statistics.py` relies on the HA `recorder` (declared in `manifest.json` `dependencies`) — keep imports compatible with its API; it already guards optional recorder symbols such as unit converters with `try`/`except`.
- Auth lives in `api.py`: email/password OAuth + refresh tokens; `InvalidCredentialsError` must surface as `ConfigEntryAuthFailed` in the coordinator.
- Device model members in `const.py` are based on limited hardware knowledge — new models should map to `Device.Unknown` (via `Device.from_model`) rather than erroring, and `Device.Unknown` gets every entity regardless of `applicable_devices`.
- The integration is deliberately under-tested (one hardware unit); add/extend `unittest` tests in `tests/` for any const/statistics/typeutils logic changes.
- Bump `version` in `manifest.json` for any user-facing change (PR template reminder).
- Never commit `.data/` (local HA runtime directory, gitignored).
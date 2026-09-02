# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Bumped the `amit_hvac_control` dependency to `>=0.5.0`. As of 0.5.0, the setters behind ventilation mode, target air temperature, target CO2, heating temperature, and heating mode now re-fetch device state after posting and retry (up to 3 attempts, 1s apart) until the controller actually reflects the change, raising `SettingNotConfirmedException` if it never does — see [upstream changelog](https://github.com/mitch3s/amit-hvac-control-api/blob/main/CHANGELOG.md).
- Pinned all third-party GitHub Actions in `lint.yml`, `validate.yml`, and `release.yml` to commit SHAs (with version comments) instead of floating tags/branches, added `permissions: {}` at the workflow level, and added `persist-credentials: false` to checkout steps.
- Replaced the custom `Dockerfile.dev` (a copy of home-assistant/core's devcontainer image, with bluez/ffmpeg/libav*/hass-release tooling this integration doesn't use) with a lean `devcontainer-features`-based image, matching current `integration_blueprint` practice.
- Bumped the devcontainer to Python 3.14 and `ruff` to 0.15.21, pinned the dev `homeassistant` requirement to 2026.8.3 to match `hacs.json`'s minimum supported version, and added a `hacs` minimum version field to `hacs.json`. Added `ffmpeg`, `libturbojpeg0`, and `libpcap-dev` as devcontainer apt packages, committed `.devcontainer-lock.json` to pin the resolved feature versions, and switched `scripts/lint` to run `ruff format` before `ruff check --fix`.
- Dropped the UDP 5683 port mapping that had been kept for Shelly testing — this integration has no Shelly dependency, and `forwardPorts`/`portsAttributes` (TCP-only) now cover the one port the devcontainer actually needs (8123).

### Fixed

- `AmitSensorCoordinator` and `AmitFanCoordinator` now translate `amit_hvac_control` exceptions into `ConfigEntryAuthFailed`/`UpdateFailed` instead of letting them propagate as raw, unhandled exceptions — authentication failures now trigger Home Assistant's reauth flow, and connection/parsing errors surface as a clean "unable to connect" state instead of a full traceback in the log.
- The climate, fan, and number entities now catch `SettingNotConfirmedException` from `amit_hvac_control` 0.5.0's setters and raise a translated `HomeAssistantError` instead of letting it propagate as a raw traceback; entities backed by a coordinator also trigger a refresh so any optimistic state gets corrected once the confirmation fails.
- Fixed `AmitHeatingClimateEntity` calling `TemperatureApi.async_set_heading_mode`, a method that has never existed in any published `amit_hvac_control` release — the correct name is `async_set_heating_mode`. This meant setting the heating HVAC mode or turning heating on/off always raised `AttributeError`.

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Pinned all third-party GitHub Actions in `lint.yml`, `validate.yml`, and `release.yml` to commit SHAs (with version comments) instead of floating tags/branches, added `permissions: {}` at the workflow level, and added `persist-credentials: false` to checkout steps.
- Replaced the custom `Dockerfile.dev` (a copy of home-assistant/core's devcontainer image, with bluez/ffmpeg/libav*/hass-release tooling this integration doesn't use) with a lean `devcontainer-features`-based image, matching current `integration_blueprint` practice.

### Fixed

- `AmitSensorCoordinator` and `AmitFanCoordinator` now translate `amit_hvac_control` exceptions into `ConfigEntryAuthFailed`/`UpdateFailed` instead of letting them propagate as raw, unhandled exceptions — authentication failures now trigger Home Assistant's reauth flow, and connection/parsing errors surface as a clean "unable to connect" state instead of a full traceback in the log.

# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-06-07

### Added

- Add GitHub Actions CI workflow.
- Add GitHub Actions PyPI publishing workflow using Trusted Publishing.

### Changed

- Use SPDX license metadata in `pyproject.toml`.
- Retry transient Aliyun ESA `CreateRecord` errors such as `Site.ServiceBusy` and `TooManyRequests`.
- Remove the unused generated TypeScript demo from the release package.

## [0.1.0] - 2026-06-06

### Added

- Initial Certbot DNS authenticator plugin for Aliyun ESA.
- DNS-01 TXT record creation and cleanup through Aliyun ESA APIs.
- English and Simplified Chinese documentation.
- Unit tests for site matching, TXT record creation, and safe TXT record deletion.

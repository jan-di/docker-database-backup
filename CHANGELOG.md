# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- AES Encryption of dump files
- Support for cron expressions as schedule.
- Option to change gzip compression level. Default: `6`
- Option to overwrite the basename of the dump files
- Options to change the internal network name/target alias

### Changed
- Rename option `INTERVAL` to `SCHEDULE`

### Fixed
- Encapsulated user input in double quotes at dump commands

## [0.1.0] - 2021-09-04
### Added
- Initial Release

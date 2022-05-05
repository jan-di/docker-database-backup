# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2022-05-05
### Added
- Open Metrics/Prometheus endpoint
- Add grace time options to ignore errors on newly started targets

### Changed
- Updated python version and external dependencies

## [0.3.0] - 2021-11-06
### Added
- Support multiple service instances on the same docker engine
- Add retention policies to keep multiple versions of dump files.
- Option to add a timestamp at the end of the dump file. Works also if no retention policy is used.
- Cleanup old networks that are not removed successfully

### Changed
- Custom dump file names now follow the same naming rules as docker containers.
- Add generated base64 suffix to network name to prevent duplicates with docker-compose

### Removed
- Dropped Support for i386 Architecture

## [0.2.0] - 2021-10-04
### Added
- AES Encryption of dump files
- Support for cron expressions as schedule.
- Option to create a backup right after start, independent of the schedule.
- Option to change gzip compression level. Default: `6`
- Option to overwrite the basename of the dump files
- Options to change the internal network name/target alias

### Changed
- Rename option `INTERVAL` to `SCHEDULE`
- Rename option `VERBOSE` to `DEBUG`

### Fixed
- Encapsulated user input in double quotes at dump commands

## [0.1.0] - 2021-09-04
### Added
- Initial Release

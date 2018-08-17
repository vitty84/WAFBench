# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project does adhere to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Developing
- pywb
- FTW-compatible-tool

## [1.2.0] - 2018-08-17
### Added
- [pywb](./pywb/README.md) an enhanced tool to wb.
### Changed
- Rename `./sample` to `./example` 

## [1.1.0] - 2018-08-13
### Added
- Add a feature to forcefully assert the "Connection: close" for each request packets.

## [1.0.1] - 2018-08-01
### Changed
- Send requests ordered by time.
- Disable the buffer of stdout

### Fixed
- Some typos
- Crash without specified log
- Request header estimation error
- Request header end setting error

## [1.0.0] - 2018-07-16
### Added
- [README.md](./README.md) describes WAF Bench tool suits project.
- [CHANGELOG.md](./CHANGELOG.md) to track changes.
- [wb](./wb/README.md), a superset of [ab](https://github.com/CloudFundoo/ApacheBench-ab) to make benchmarking WAF more easily.
- `./sample` to show demos of WAF Bench tool suits. Currently, it only has examples for wb.

### Changed
- Revise the Makefile for apr and wb to support wb new feature.

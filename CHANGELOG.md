# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project does adhere to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- [FTW Compatible Tool Suits](./FTW-compatible-tool/README.md) to support FTW testing.
- `./sample` adds a demo of wb showing how to send raw HTTP requests and serveral demos for FTW Compatible Tool Suits.
- Add tutorial of conducting FTW testing in [wb's README](./wb/README.md).

## [1.0.0] - 2018-07-16
### Added
- [README.md](./README.md) describes WAF Bench tool suits probject.
- [CHANGELOG.md](./CHANGELOG.md) to track changes.
- [wb](./wb/README.md), a superset of [ab](https://github.com/CloudFundoo/ApacheBench-ab) to make benchmarking WAF more easily.
- `./sample` to show demos of WAF Bench tool suits. Currently, it only has examples for wb.

### Changed
- Revise the Makefile for apr and wb to support wb new feature.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project does adhere to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- [FTW Compatible Tool Suits](./FTW-compatible-tool/README.md) to support FTW testing.
- [`./Generator`](./Generator/README.md) contains some generators to generate `wb` format packets from high level information. Currently there is only a `YAML_generator.py`.
- `./example` adds several demos for wb and FTW Compatible Tool Suits.
- Add tutorial of conducting FTW testing in [wb's README](./wb/README.md).
- [README.md](./README.md) adds infos about FTW Compatible Tool Suits and YAML generator.
- [README.md](./README.md) adds attributions to [FTW](https://github.com/fastly/ftw)

### Changed
- Revise motivations and dependency instructions in [README.md](./README.md)
- Rename `./sample` to `./example` 

## [1.0.0] - 2018-07-16
### Added
- [README.md](./README.md) describes WAF Bench tool suits probject.
- [CHANGELOG.md](./CHANGELOG.md) to track changes.
- [wb](./wb/README.md), a superset of [ab](https://github.com/CloudFundoo/ApacheBench-ab) to make benchmarking WAF more easily.
- `./sample` to show demos of WAF Bench tool suits. Currently, it only has examples for wb.

### Changed
- Revise the Makefile for apr and wb to support wb new feature.

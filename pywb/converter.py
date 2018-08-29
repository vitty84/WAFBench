#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Convert multiple packets into a packets list

This exports:
    - read_packets_from_pkt_files is a function that
        reads packets from .pkt files.
    - read_packets_from_pkt_paths: is a function that
        reads packets from a set of paths that can be .pkt files
        or directories that include .pkt files.
    - convert_rules_to_packets: is a function that
        convert a set of ftw.ruleset to a packets generator
    - convert_yaml_strings_to_packets: is a function that
        convert a set of yaml strings required by ftw to a packets generator
    - convert_yaml_files_to_packets: is a function that
        convert a set of yaml files required by ftw to a packets generator
    - convert_yaml_directories_to_packets: is a function that
        convert a set of directories contains yaml files required by ftw
        to a packets generator
    - convert_yaml_paths_to_packets: is a function that
        convert a set of paths contains yaml files required by ftw
        to a packets generator
    - convert: is a function that execute a convertion
        from a set of paths to a packets generators
    - execute: is a function that execute a convertion and
        export all of packets into the exporter

Convert packets saved in files(.yaml, .pkt) or strings into a packets list
"""

__all__ = [
    "read_packets_from_pkt_files",
    "read_packets_from_pkt_paths",
    "convert_rules_to_packets",
    "convert_yaml_strings_to_packets",
    "convert_yaml_files_to_packets",
    "convert_yaml_directories_to_packets",
    "convert_yaml_paths_to_packets",
    "convert",
    "execute",
]

import os
import io
import sys
import functools

import ftw
import yaml

import packetsexporter


def _accept_iterable(func):
    @functools.wraps(func)
    def _decorator(iterable_):
        if not hasattr(iterable_, "__iter__"):
            iterable_ = [iterable_]
        return func(iterable_)
    return _decorator


def _expand_nest_generator(func):
    @functools.wraps(func)
    def _decorator(*args, **kw):
        iterable_ = func(*args, **kw)
        if not hasattr(iterable_, "__iter__"):
            yield iterable_
        else:
            iterable_ = iterable_.__iter__()
            visit_stack = [iterable_]
            while visit_stack:
                iterable_ = visit_stack[-1]
                if not hasattr(iterable_, "__iter__"):
                    yield iterable_
                    visit_stack.pop()
                else:
                    try:
                        iterable_ = next(iterable_)
                        if hasattr(iterable_, "__iter__"):
                            iterable_ = iterable_.__iter__()
                        visit_stack.append(iterable_)
                    except StopIteration:
                        visit_stack.pop()
    return _decorator


@_accept_iterable
@_expand_nest_generator
def read_packets_from_pkt_files(files):
    """Read packets from .pkt files

    Arguments:
        files: a set of files of save packets

    Return a packets generator
    """
    buffer_ = ""
    for file_ in files:
        file_ = os.path.abspath(file_)
        with open(file_, "rb", io.DEFAULT_BUFFER_SIZE) as fd:
            while True:
                bytes_ = fd.read(io.DEFAULT_BUFFER_SIZE)
                if not bytes_:
                    if buffer_:
                        yield buffer_
                    break
                while bytes_:
                    delimit_pos = bytes_.find('\0')
                    if delimit_pos == -1:
                        buffer_ += bytes_
                        bytes_ = None
                    else:
                        buffer_ += bytes_[:delimit_pos]
                        if buffer_:
                            yield buffer_
                        buffer_ = ""
                        bytes_ = bytes_[delimit_pos + 1:]


@_accept_iterable
@_expand_nest_generator
def read_packets_from_pkt_paths(paths):
    """ Reads packets from a set of paths that can be .pkt files
        or directories that include .pkt files.

    Arguments:
        paths: a set of paths that can be .pkt files
            or directories that include .pkt files.

    Return a packets generator
        that will generate all of packets saved in those paths
    """
    for path_ in paths:
        import os
        path_ = os.path.abspath(path_)

        if os.path.isdir(path_):
            for root, _, files in os.walk(path_):
                for file in files:
                    if os.path.splitext(file)[1].lower() != ".pkt":
                        continue
                    yield read_packets_from_pkt_files(
                        os.path.join(root, file))
        elif os.path.isfile(path_):
            if os.path.splitext(path_)[1].lower() != ".pkt":
                continue
            yield read_packets_from_pkt_files(path_)
        else:
            raise IOError("No such file or path: '%s'" % (path_, ))


@_accept_iterable
@_expand_nest_generator
def convert_rules_to_packets(rules):
    """ Convert a set of ftw.ruleset to a packets generator

    Arguments:
        rules: a set of ftw.ruleset

    Return a packets generator
        that will generate all of packets from those ftw.rulesets
    """
    for rule in rules:
        for test in rule.tests:
            for _, stage in enumerate(test.stages):
                http_ua = ftw.http.HttpUA()
                http_ua.request_object = stage.input
                http_ua.build_request()
                yield str(http_ua.request)


@_accept_iterable
@_expand_nest_generator
def convert_yaml_strings_to_packets(strings):
    """ Convert a set of yaml strings required by ftw to a packets generator

    Arguments:
        strings: a set of yaml strings required by ftw

    Return a packets generator
        that will generate all of packets included in those yaml strings
    """
    for string_ in strings:
        rule = ftw.ruleset.Ruleset(yaml.load(string_))
        yield convert_rules_to_packets(rule)


@_accept_iterable
@_expand_nest_generator
def convert_yaml_files_to_packets(files):
    """ Convert a set of yaml files required by ftw to a packets generator

    Arguments:
        files: a set of yaml files required by ftw

    Return a packets generator
        that will generate all of packets saved in those yaml files
    """
    for file_ in files:
        if os.path.splitext(file_)[1].lower() != ".yaml":
            continue
        rules = ftw.util.get_rulesets(file_, False)
        yield convert_rules_to_packets(rules)


@_accept_iterable
@_expand_nest_generator
def convert_yaml_directories_to_packets(directories):
    """ Convert a set of directories contains yaml files required by ftw
        to a packets generator

    Arguments:
        directories: a set of directories contains yaml files required by ftw

    Return a packets generator
        that will generate all of packets saved in those directories
    """
    for directory_ in directories:
        rules = ftw.util.get_rulesets(directory_, True)
        yield convert_rules_to_packets(rules)


@_accept_iterable
@_expand_nest_generator
def convert_yaml_paths_to_packets(paths):
    """ Convert a set of paths contains yaml files required by ftw
        to a packets generator

    Arguments:
        paths: a set of paths contains yaml files required by ftw

    Return a packets generator
        that will generate all of packets saved in those paths
    """
    for path_ in paths:
        if os.path.isfile(path_):
            yield convert_yaml_files_to_packets(path_)
        elif os.path.isdir(path_):
            yield convert_yaml_directories_to_packets(path_)
        else:
            raise IOError("No such file or path: '%s'" % (path_, ))


CONVERTERS = {
    ".yaml": convert_yaml_paths_to_packets,
    ".pkt": read_packets_from_pkt_paths,
}


@_accept_iterable
@_expand_nest_generator
def convert(paths):
    """ Execute a convertion from a set of paths to a packets generators

    Arguments:
        paths: a set of paths includes .yaml and .pkt files
            or directories contain those kind of files

    Return a packets generator
        that will generate all of packets saved in those paths
    """
    for path_ in paths:
        for _, convertor in CONVERTERS.items():
            yield convertor(path_)


def execute(paths, exporter=None):
    """ Execute a convertion and export all of packets into the exporter

    Arguments:
        paths: a set of paths includes %s files
            or directories contain those kind of files
        exporter
    """
    if not isinstance(exporter, packetsexporter.PacketsExporter):
        with packetsexporter.PacketsExporter(exporter) as exporter:
            for packet in convert(paths):
                exporter.export(packet)
    else:
        for packet in convert(paths):
            exporter.export(packet)


def _help():
    return '''
converter.py
    convert yaml or pkt files into a pkt file

SYNOPSIS
    python converter.py [OPTION] [PATHS...]
    ./converter.py [OPTION] [PATHS...]

DESCRIPTION
    PATHS...        input .yaml/.pkt files or directories that includes \
 these kinds of files
    -o/--output     output packets file , default is stdout
    -h/--help       print help

EXAMPLE
    ./converter.py rtt_ruleset/ -o packets.pkt
    '''


if __name__ == '__main__':
    packets_file = ""
    packets_files = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-h" or sys.argv[i] == "--help":
            print(help())
            sys.exit(0)
        elif sys.argv[i] == "-o" or sys.argv[i] == "--output":
            i += 1
            if i >= len(sys.argv):
                raise ValueError("need an argument as the output")
            packets_file = sys.argv[i]
        else:
            packets_files.append(sys.argv[i])
        i += 1

    execute(packets_files, packets_file)

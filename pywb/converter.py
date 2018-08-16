#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pywb_utility import *


# read packets from .pkt file
# @param pkt_file: the path of file of save packets
# @return: packets list. the packets list saved in the file
def read_packets_from_pkt_file(pkt_file):
    import os
    pkt_file = os.path.abspath(pkt_file)
    if not os.path.exists(pkt_file):
        error(pkt_file + " is not existed\n")
    with open(pkt_file, "rb") as f:
        return [f.read()]
    return []

# read packets from .pkt file set
# @param pkt_paths: the path set of save packets
# @return: packets list. the packets list saved in the file
def read_packets_from_pkt_paths(pkt_paths = []):

    if type(pkt_paths) == str:
        pkt_paths = [pkt_paths]
    packets = []

    for pkt_path in pkt_paths:
        import os
        pkt_path = os.path.abspath(pkt_path)
        if not os.path.exists(pkt_path):
            error(pkt_path + " is not existed\n")
            
        if os.path.isdir(pkt_path):
            for root, _, files in os.walk(pkt_path):
                for file in files:
                    #second item is file ext
                    if os.path.splitext(file)[1].lower() != ".pkt":
                        continue
                    packets += read_packets_from_pkt_file(os.path.join(root, file))
                    
        elif os.path.isfile(pkt_path):
            if os.path.splitext(pkt_path)[1].lower() != ".pkt":
                continue
            packets += read_packets_from_pkt_file(pkt_path)
            
    return packets

# Convert ruleset to packets
# @param ruleset: the ftw.ruleset
# @return: packets generator
def convert_ruleset_to_packets(ruleset):
    for rule in ruleset:
        for test in rule.tests:
            for _, stage in enumerate(test.stages):
                import ftw
                http_ua = ftw.http.HttpUA()
                http_ua.request_object = stage.input
                http_ua.build_request()
                yield str(http_ua.request)

# Convert yaml string to packets
# @param yaml_string: a string of yaml format
# @return: packets generator
def convert_yaml_string_to_packets(yaml_string):
    import yaml
    import ftw
    rule = ftw.ruleset.Ruleset(yaml.load(yaml_string))
    return convert_ruleset_to_packets([rule])

# Convert yaml file to packets
# @param yaml_file: a file of yaml format
# @return: packets generator
def convert_yaml_file_to_packets(yaml_file):
    import ftw
    ruleset = ftw.util.get_rulesets(yaml_file, False)
    return convert_ruleset_to_packets(ruleset)

# Convert yaml file to packets
# @param yaml_directory: a directory includes some files of yaml format
# @return: packets generator
def convert_yaml_directory_to_packets(yaml_directory):
    import ftw
    #True means that recursively visit the yaml file from the directory
    ruleset = ftw.util.get_rulesets(yaml_directory, True)
    return convert_ruleset_to_packets(ruleset)

# help document
def help():
    return '''
converter.py
    convert yaml or pkt files into a pkt file

SYNOPSIS
    python converter.py [OPTION] [PATHS...]
    ./converter.py [OPTION] [PATHS...]

DESCRIPTION
    PATHS...        input .yaml/.pkt files or directories that includes these kinds of files
    -o/--output     output packets file , default is stdout
    -h/--help       print help
    
EXAMPLE
    ./converter.py rtt_ruleset/ -o packets.pkt
    '''

converters = {
    ".yaml": convert_yaml_directory_to_packets,
    ".pkt" : read_packets_from_pkt_paths,
}

# execute this file
# @param packet_paths: a list of path that includes .pkt or .yaml files
# @param outputer: output file of packets, default is stdout
def execute(packet_paths = [], outputer = ""):

    if type(packet_paths) == str:
        packet_paths = [packet_paths]

    import packets_outputer
    if type(outputer) != packets_outputer.packets_outputer:
        outputer = packets_outputer.packets_outputer(outputer)

    #convert all path to abs path
    for i in range(len(packet_paths)):
        import os
        packet_paths[i] = os.path.abspath(packet_paths[i])
        if not os.path.exists(packet_paths[i]):
            error(packet_paths[i] + " is not existed\n")

    #convert all packets files into outputer
    for path in packet_paths:
        import os
        if os.path.isdir(path):
            for _, converter in converters.items():
                outputer(converter(path))
        elif os.path.isfile(path):
            _, file_ext = os.path.splitext(path)
            file_ext = file_ext.lower()
            if file_ext not in converters:
                error(path + "'s extension " + file_ext + " isn't supported")
            outputer(converters[file_ext](path))

if __name__ == '__main__':
    import sys
    import os
    
    executable = os.path.basename(os.path.normpath(sys.argv[0]))
    if executable == "python" or executable == "python3":
        sys.argv = sys.argv[1:]

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
                error()
            packets_file = sys.argv[i]
        else:
            packets_files.append(sys.argv[i])
        i += 1

    execute(packets_files, packets_file)

#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pywb_utility import *

#PKT convert    

def read_packets_from_pkt_file(pkt_file):
    import os
    pkt_file = os.path.abspath(pkt_file)
    if not os.path.exists(pkt_file):
        error(pkt_file + " is not existed\n")
    with open(pkt_file, "rb") as f:
        return [f.read()]

def pkt_files_merge(pkt_files = []):

    if type(pkt_files) == str:
        pkt_files = [pkt_files]
    packets = []

    for pkt_file in pkt_files:
        import os
        pkt_file = os.path.abspath(pkt_file)
        if not os.path.exists(pkt_file):
            error(pkt_file + " is not existed\n")
            
        if os.path.isdir(pkt_file):
            for root, _, files in os.walk(pkt_file):
                for file in files:
                    #second item is file ext
                    if os.path.splitext(file)[1].lower() != ".pkt":
                        continue
                    packets += read_packets_from_pkt_file(os.path.join(root, file))
                    
        elif os.path.isfile(pkt_file):
            if os.path.splitext(pkt_file)[1].lower() != ".pkt":
                continue
            packets += read_packets_from_pkt_file(pkt_file)
            
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
    convert yaml or pkt files into a file

SYNOPSIS
    python converter.py [OPTION] [PATHS...]
    ./converter.py [OPTION] [PATHS...]

DESCRIPTION
    PATHS...        input .yaml or .pkt files or directories that includes these kinds of files
    -o/--output     output packets file , default is stdout
    -h/--help       print help
    
EXAMPLE
    #normal
    ./converter.py rtt_ruleset/ -o packets.pkt
    '''

converters = {
    ".yaml": convert_yaml_directory_to_packets,
    ".pkt" : pkt_files_merge,
}

# execute this file
# @param yaml_files: a list includes yaml files or directories that include some files of yaml format, default is stdin
# @param packets_file: output file for packets, default is stdout
def execute(packet_paths = [], outputer = ""):
    # import sys
    #read packets
    # if not yaml_files:
    #     packets = convert_yaml_string_to_packets(sys.stdin.read())
    #     outputer(packets)

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

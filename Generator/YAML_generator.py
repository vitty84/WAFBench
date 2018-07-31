#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import ftw
import yaml
import argparse

# Convert ruleset to packets
# @param ruleset: the ftw.ruleset
# @return: packets generator
def convert_ruleset_to_packets(ruleset):
    for rule in ruleset:
        for test in rule.tests:
            for _, stage in enumerate(test.stages):
                http_ua = ftw.http.HttpUA()
                http_ua.request_object = stage.input
                http_ua.build_request()
                yield str(http_ua.request)

# Convert yaml string to packets
# @param yaml_string: a string of yaml format
# @return: packets generator
def convert_yaml_string_to_packets(yaml_string):
    rule = ftw.ruleset.Ruleset(yaml.load(yaml_string))
    return convert_ruleset_to_packets([rule])

# Convert yaml file to packets
# @param yaml_file: a file of yaml format
# @return: packets generator
def convert_yaml_file_to_packets(yaml_file):
    ruleset = ftw.util.get_rulesets(yaml_file, False)
    return convert_ruleset_to_packets(ruleset)

# Convert yaml file to packets
# @param yaml_directory: a directory includes some files of yaml format
# @return: packets generator
def convert_yaml_directory_to_packets(yaml_directory):
    #True means that recursively visit the yaml file from the directory
    ruleset = ftw.util.get_rulesets(yaml_directory, True)
    return convert_ruleset_to_packets(ruleset)

# output packets to a file descriptor
# @param packets: packets generator
# @param output_file: file descriptor for output
is_first_packets = True
def output_packets(packets, output_file):
    for packet in packets:
        if not is_first_packets:
            output_file.write("\0")
        output_file.write(packet)
        is_first_packets = False

# help document
def help():
    return '''
YAML_generator.py
    
SYNOPSIS
    python YAML_generator.py [OPTION] [FILES...]
    ./YAML_generator.py [OPTION] [FILES...]

DESCRIPTION
    FILES...    input yaml files or directory, default is stdin if no files are provided

    -o/--output output packets file , default is stdout
    
    -h/--help   print help
    
EXAMPLE
    #pipeline is recommended to test yaml file and observe the output
    cat file.yaml | ./YAML_generator.py
    
    #normal
    ./YAML_generator.py rtt_ruleset/ -o packets.pkt
    
    '''
# execute this file
# @param yaml_files: a list includes yaml files or directories that include some files of yaml format, default is stdin
# @param packets_file: output file for packets, default is stdout
def execute(yaml_files = [], packets_file = ""):
    import sys

    if not packets_file:
        packets_file = sys.stdout
    else:
        packets_file = open(packets_file, 'wb')


    #read packets
    if not yaml_files:
        packets = convert_yaml_string_to_packets(sys.stdin.read())
        output_packets(packets, packets_file)
    #convert all path to abs path
    for i in range(len(yaml_files)):
        import os
        yaml_files[i] = os.path.abspath(yaml_files[i])
        if not os.path.exists(yaml_files[i]):
            import sys
            sys.stderr.write(yaml_files[i] + " is not existed\n")
            sys.exit(-1)
        
    for yaml_file in yaml_files:
        import os
        i = 0
        if os.path.isdir(yaml_file):
            packets = convert_yaml_directory_to_packets(yaml_file)
        elif os.path.isfile(yaml_file):
            packets = convert_yaml_file_to_packets(yaml_file)
        output_packets(packets, packets_file)

#error 
def error():
    import sys
    sys.stderr.write("error argument\n")
    sys.exit(-1)

if __name__ == '__main__':
    import sys

    # if len(sys.argv) == 1:
        # print(help())
        # sys.exit(0)

    packets_file = ""
    yaml_files = []
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
            yaml_files.append(sys.argv[i])
        i += 1

    execute(yaml_files, packets_file)
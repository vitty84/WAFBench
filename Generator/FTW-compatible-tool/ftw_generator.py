# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ftw import http, util, ruleset
import yaml
import argparse
import sys
import os
import json

# Generate the dummy request string from the fixed YAML file.
# @return: The request string.
def generate_dummy_request():
    dummy_request_string = ''
    dummy_request_yaml = '''
---
  meta: 
    author: "csanders-git"
    enabled: true
    name: "Example_Tests"
    description: "This file contains example tests."
  tests: 
    - 
      test_title: 920272-3
      stages: 
        - 
          stage: 
            input:
              dest_addr: "127.0.0.1"
              port: 80
              uri: "/WB_Dummy_Request_URI"
              headers:
                  User-Agent: "ModSecurity CRS 3 Tests"
                  Host: "localhost"
                  Accept: "*/*"
            output:
                  log_contains: ""
 
    '''
    rulesets = [ruleset.Ruleset(yaml.load(dummy_request_yaml))]
    http_ua = http.HttpUA()
    for rule in rulesets:
        for test in rule.tests:
            for index, stage in enumerate(test.stages):
                http_ua.request_object = stage.input
                
                #Build the request and print
                http_ua.build_request()
                dummy_request_string = str(http_ua.request)
    if dummy_request_string == '':
        sys.stderr.write('Can not create dummy request correctly! Please check the existance and permission of wb_dummy_request.yaml!\n')
    return dummy_request_string

# Save the raw YAML code into a diction. The key is the test title, the value is the raw YAML code.
# @param input_filename:    The name of YAML file.
# @param raw_yaml_diction:  The diction to save the YAML code.
def save_raw_yaml_in_dict(input_filename, raw_yaml_diction):
    #save each test as a diction item 
    #maybe there should exist a lib?
    with open(input_filename,'rb') as yaml_file:
        find_new_test = False
        tests_start = False
        stage_start = False
        title = ''
        test = ''
        for line in yaml_file:
            buf = line.replace(' ','')
            buf = buf.replace('\n','')
            if tests_start == False:
                if 'tests:' in buf:
                    #'tests:' marks the start of all requests.
                    tests_start = True
                continue
            if stage_start == True and buf == '-':
                #Start of a new test, end of a test
                raw_yaml_diction[title] = test
                stage_start = False
                title = ''
                test = ''
                continue
            test = test + line
            if 'test_title:' in buf:
                title_position = buf.find('test_title:') + len('test_title:')
                title = buf[title_position:]
            if 'stage:' in line:
                stage_start = True
        raw_yaml_diction[title] = test
        
# Dealing with one yaml file
# @param input_filename:                A string. The raw request yaml filename.
# @param output_request_filename:       The output request package filename.
# @param output_conditions_filename:    The log condition filename
# @param raw_yaml_diction:              The diction to save raw YAML code.
# @param dummy_request_string:          The dummy request in string format.
# @param is_first_file:                 Is this file the first file. We do not need to add a '\0' before the first request in the package file.
def generate_request_from_file(input_filename, output_request_filename, output_conditions_filename, raw_yaml_diction, dummy_request_string, is_first_file):
    local_request_cnt = 0
    rulesets = util.get_rulesets(input_filename, False)
    http_ua = http.HttpUA()
    with open(output_request_filename, 'a') as output_request, open(output_conditions_filename, 'a') as output_conditions:
        #Iterate the raw yaml file
        for rule in rulesets:
            for test in rule.tests:
                for index, stage in enumerate(test.stages):
                    http_ua.request_object = stage.input

                    #Build the request and print
                    http_ua.build_request()
                    req = str(http_ua.request)
                    #output.write(http_ua.request)
                    if local_request_cnt != 0 or is_first_file == False:
                        output_request.write('\0')
                    output_request.write(req)
                    # We add a dummy request after every normal request.
                    # The dummy request will create a special log in server's log file.
                    # We can determine wich request does a log belongs to according to these special logs.
                    output_request.write('\0'+dummy_request_string)
                    local_request_cnt = local_request_cnt + 1
                    diction = stage.stage_dict['output']
                    diction['test_title'] = test.test_title
                    json.dump(diction, output_conditions, ensure_ascii=False)
                    output_conditions.write('\n')
                    save_raw_yaml_in_dict(input_filename, raw_yaml_diction)

# Get all files in the given folder.
# @param input_folder:  A string, the given folder.
# @return:              The list of all files' name.
def get_files(input_folder):
    input_files = []
    for fpath, dirname, fnames in os.walk(input_folder, followlinks = True):
        for fname in fnames:
            fname = os.path.join(fpath,fname)
            if fname.endswith(".yaml"):
                input_files.append(fname)
    return input_files

# Generate requests from a folder.
# @param input_folder:      A string, the path of given folder.
# @param output_request:    An opened file object. The output request package file.
# @param output_conditions: An opened file object. The condition file, save the conditions used by comparator.
# @param raw_yaml_diction:  The diction to save raw YAML code.
# @param dummy_request_string:  The dummy request in string format.
def generate_request_from_folder(input_folder, output_request_filename, output_conditions_filename, raw_yaml_diction, dummy_request_string):
    files = get_files(input_folder)
    is_first_file = True
    for filename in files:
        generate_request_from_file(filename, output_request_filename, output_conditions_filename, raw_yaml_diction, dummy_request_string, is_first_file)
        is_first_file = False

# Check the file operation of given file name.
# @param input_filename:                The name of YAML file. Check the read operation.
# @param output_request_filename:       The name of request package file. Check the write operation.
# @param output_raw_yaml_filename:      The name of raw yaml code file. Check the write operation.
# @param output_conditions_filename:    The name of condition file. Check the write operation.
# @return:                              Whether the file open operation is successful or not.
def check_file_operation(input_filename, output_request_filename, output_raw_yaml_filename, output_conditions_filename):
    #check input_file
    if input_filename != '' and os.path.isfile(input_filename):
        try:
            fd = open(input_filename,'rb')
        except IOError:
            print('Can not open input file ' + input_filename)
            return False
        else:
            fd.close()
    #check output_request
    try:
        fd = open(output_request_filename,'wb')
    except IOError:
        print('Can not open output request file ' + output_request_filename)
        return False
    else:
        fd.close()
    #check output_raw_yaml
    try:
        fd = open(output_raw_yaml_filename,'wb')
    except IOError:
        print('Can not open output raw yaml file ' + output_raw_yaml_filename)
        return False
    else:
        fd.close()
    #check output_conditions
    try:
        fd = open(output_conditions_filename,'wb')
    except IOError:
        print('Can not open output conditions file ' + output_conditions_filename)
        return False
    else:
        fd.close()
    return True

# @param input_yaml:        The name of input YAML file or folder.
# @param output_request:    The file include all requests' packages.
#                           Each package is separated by a '\0'
# @param output_raw_yaml:   The file include all requests' raw yaml code.
#                           The file is a json diction. The key is the test title, the value is the yaml code string.
# @param output_conditions: The file include all requests' check conditions, means key-val pairs in 'output' stage.
#                           The file contains each request's conditions in a line, saved as the json diction. 
#                           Use json.loads(line) to load one line.
#                           The order of conditions is the same as the order of generating the request. 
def ftw_generator(input_yaml, output_request, output_raw_yaml, output_conditions):
    
    dummy_request_string = generate_dummy_request()
    input_yamlname = os.path.abspath(input_yaml)
    output_request_filename = os.path.abspath(output_request)
    output_raw_yaml_filename = os.path.abspath(output_raw_yaml)
    output_conditions_filename = os.path.abspath(output_conditions)

    if not check_file_operation(input_yamlname, output_request_filename, output_raw_yaml_filename, output_conditions_filename):
        quit()

    #YAML_DICTION: An diction to save all raw yaml codes. The key is the test_title, the value is the raw yaml code string.
    raw_yaml_diction = {}
    if os.path.isfile(input_yaml):
        generate_request_from_file(input_yamlname,output_request_filename, output_conditions_filename,raw_yaml_diction,dummy_request_string, True)
    else:
        generate_request_from_folder(input_yamlname,output_request_filename, output_conditions_filename,raw_yaml_diction,dummy_request_string)

    with open(output_raw_yaml_filename, 'wb') as output_raw_yaml_fd:
        json.dump(raw_yaml_diction, output_raw_yaml_fd, ensure_ascii=False)
        output_raw_yaml_fd.close()

    print('DONE!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_yaml', '-f', 
                        help='The input YAML file or dir of requests', 
                        required=True)
    parser.add_argument('--output_request', '-o', 
                        help='The file to save all request packages', 
                        default='temp_requests.dat')
    parser.add_argument('--output_raw_yaml', '-y', 
                        help='The json file to save the test title and it\'s raw yaml code', 
                        default='temp_raw_yaml.dat')
    parser.add_argument('--output_conditions', '-c', 
                        help='The json file to save the check condition of each test', 
                        default='temp_conditions.dat')
    args=parser.parse_args()
    ftw_generator(args.input_yaml, args.output_request, args.output_raw_yaml, args.output_conditions)

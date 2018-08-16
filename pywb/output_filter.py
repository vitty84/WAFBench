
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


# INTERFACE for processing of the stderr and stdout of wb
# line by line to process the stderr and stdout of wb
class filter(object):
    #process one line
    # @param line: one line output from stderr and stdout of wb
    def __call__(self, line):
        pass

# IMPLEMENT line printer
# print the line
class simple_printer(filter):
    def __call__(self, line):
        if line != None:  
            import sys
            sys.stdout.write(line)
        return line

# IMPLEMENT document reviser
# revise some help document, because the option parsers will modify some help document
class help_document_revise(filter):
    def __init__(self, enhance_options = {}):
        self.__buffer = ""
        self.__ignore = False
        self.__options = enhance_options
        self.__print_new_option = False

    def __call__(self, line):
        
        if line == None:
            return None

        import re
        
        #replace executable
        pattern = "^Usage:\s*(\S+)"
        wb_path = re.finditer(pattern, line)
        for wb_path in wb_path:
            import sys
            return line[:wb_path.start()] + sys.argv[0] + line[wb_path.end():]


        #print help of enhance options
        pattern = "New options for wb"
        if re.match(pattern, line):
            self.__print_new_option = True
            return line

        if self.__print_new_option:
            for _, option in self.__options.items():
                line += option.help()
            self.__print_new_option = False
            return line
        

        #remove old option help
        pattern = "^\s{4}(-\w)"
        opt = re.search(pattern, line)
        if opt:            
            opt = opt.group(1)
            if opt in self.__options:
                self.__ignore = True
                # return self.__options[opt].help()
            else:
                self.__ignore = False
        
        #first char isn't a space, need cancel ignore
        pattern = "^\S"
        if re.match(pattern, line):
            self.__ignore = False

        #ignore this line
        if not self.__ignore:
            return line
        return None
        
        


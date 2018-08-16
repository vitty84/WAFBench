 [WB Home Page](../README.md)

# pywb

`pywb` is an enhanced interface for `wb`. It is more friendly to use and easier for developing.

## Features

## Prerequisites

Some software or libraries may be necessary for have been listed in [WB Home Page](../README.md), but another requisite is that `wb`(after 2018-08-14) need be installed.

### Synopsis

```
./pywb.py [options] [http[s]://]hostname[:port]/path
```

### Options

**options** are compatible with [wb](../wb/README.md).


***ENHANCE OPTION***

- -F supports *.yaml and *.pkt and directories that include these kinds of file.
- -u and -p will automatically identify the file type that wants to be sent by its ext, and modify the Content-Type. These options support almost all of the types that are mentioned by MIME.

### Example

```
#post a json file, automatically infer the Content-Type
./pywb.py  10.0.1.131:18080  -p ../example/packets/requestbody2kb.json  -t 5 -c 20

#send packets in a specified directory
./pywb.py  10.0.1.131:18080  -F ../example/packets/  -t 5 -c 20

#send packets in multiple files
./pywb.py  10.0.1.43:18080 -t 5 -c 20 -k -F ../example/packets/test-2-packets.yaml -F ../example/packets/test-2-packets.pkt
```

### Develop
Two interfaces are provided to developers to customize new features. 
```
# option_parser.py
#
# INTERFACE for option parsing
# implement this interface and bind its instance to an option
# this instance will be called when the option meet
class parser(object):
    # parse option
    # @param options: the parameters of the triggered option, 
    #                 it's the parameters list that doesn't include triggered option
    # @return:        the number of parameters of this parser need
    def parse(self, options):
        return 0
    
    # dump the option for wb
    # @return:        the options that will be passed to wb
    #                 it's a parameters list. if the space-separated string is inserted
    #                 into the return list, it'll be as just one parameter to pass to wb
    def dump(self):
        return []

    # help document
    # @return: the help document for the option bound by this instance 
    def help(self):
        return " "

# INTERFACE for processing of the stderr and stdout of wb
# line by line to process the stderr and stdout of wb
# It's not recommended to modify the line, 
# because it maybe conflicts with other filters
class filter(object):
    #process one line
    # @param line: a line of string type from stderr and stdout of wb,
    #              the concrete content depends on the runtime of wb
    # @return:     what content the filter want to output. 
    #              if the return is None, this filter will be a terminator,
    #              It means that all of the filters after this will lose the 
    #              information of this line.
    def __call__(self, line):
        return line


#######################
#EXAMPLE OPTION PARSER#
#######################


import pywb
import option_parser

# IMPLEMENT import command
# import previous command that save in the file pywb.ini (-t 5 -c 20 10.0.1.43:18080)
# by -x pywb.ini
class execute_init(option_parser.parser):
    def parse(self, options):
        #options[0] will be the file path
        command = ""
        with open(options[0], 'r') as fd:
            command = fd.readline()
            #remove newline char
            command = command.strip()
        #split command into a list
        self.__command = command.split(' ')
        #return 1 to tell pywb, this parser only eat one argument
        return 1
    def dump(self):
        #return all of commands that will pass to wb
        print self.__command
        return self.__command
    def help(self):
        return "   -x FILE      will import some arguments that were saved in FILE as the arguments of wb"

#execute wb
pywb.execute(["-x", "pywb.ini"], customize d_options = { "-x" : execute_init()})



#######################
#EXAMPLE FILTER       #
#######################

import pywb
import output_filter

# IMPLEMENT logger
# to save all of output from wb 
class logger(output_filter.filter):
    def __init__(self, log_file):
        self.__log_file = log_file
    def __call__(self, line):
        #ignore those lines only include spaces
        import re
        with open(self.__log_file, 'a') as fd:
            #save log into file
            fd.write(line)
        return line

pywb.execute([], customized_filters=[logger("log")])

```

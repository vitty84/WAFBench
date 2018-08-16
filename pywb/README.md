[WB Home Page](../README.md)

# pywb

`pywb` is an enhanced interface for `wb`. It is more friendly to use and more easy for developing.

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
./pywb.py  10.0.1.43:18080 -t 5 -c 20 -k -F ../example/packets/test-2-packets.yaml -F ../example/packets/test-2-packets.pkt​
```

### Develop
Two interfaces are provided to developer to customize new features. 
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
    #                 it's a parameters list. if space-separated string is inserted
    #                 in to the return list, it'll be as just one parameter to pass to wb
    def dump(self):
        return []

    # help document
    # @return: the help document for the option bound by this instance 
    def help(self):
        return " "

# INTERFACE for processing of the stderr and stdout of wb
# line by line to process the stderr and stdout of wb
class filter(object):
    #process one line
    # @param line: a line of string type from stderr and stdout of wb,
    #              the concrete content is depend on the runtime of wb
    # @return:     what content the filter want to output. 
    #              if return is None, this filter will be an terminator,
    #              It means that all of filter after this will lose the 
    #              information of this line.
    def __call__(self, line):
        return line

#implement some class for your features
class my_parser(parser):
    pass

class my_filter(filter):
    pass


#install your instance into wb
pywb.execute(sys.argv[1:], {"my_option" : my_parser()}, [my_filter()])
```

from pywb_utility import *

# INTERFACE for option parsing
# implement this interface and bind its instance to an option
# this instance will be called when the option meet
class parser(object):
    # parse option
    # @param options: the parameters of the triggered option 
    # @return: the number of parameters of this parser need
    def parse(self, options):
        return 0
    
    # dump the option for wb
    # @return: the options that will be passed to wb
    def dump(self):
        return []

    # help document
    # @return: the help document for the option bound by this instance 
    def help(self):
        return " "

class options_parser(parser):
    def __init__(self, enhance_options):
        self.__enhance_options = enhance_options
    def parse(self, options):
        acceptable_options = "n:c:t:s:b:T:p:u:v:lrkVhwiIx:y:z:C:H:P:A:g:X:de:SqB:m:Z:f:Y:a:o:F:j:J:O:R:D:U:Y:W:E:G:Q:K012:3456789"
        
        single_option = []
        double_option = []

        i = 0
        while i < len(options):
            option = options[i]
            i+=1
            if option in self.__enhance_options:
                i += self.__enhance_options[option].parse(options[i:])
                continue
            
            if option[0] != "-":
                single_option.append(option)
                continue

            position = acceptable_options.find(option[1:])
            #not support argument
            if position == -1:
                error("unsupported argument [" + option + "]")
            if acceptable_options[position + 1] == ":":
                double_option.append(option)
                if i >= len(options):
                    error("option [" + option + "] need an argument")
                option = options[i]
                i+=1
                double_option.append(option)
                continue
            else:
                single_option.insert(0, option)
                continue

        self.__options = [get_wb_path()]

        #dump all trigger
        for _, trigger in self.__enhance_options.items():
            self.__options += trigger.dump()

        self.__options += double_option
        self.__options += single_option

        return len(options)

    def dump(self):
        return self.__options

class packet_file_enhance(parser):

    def __init__(self, packets_file):
        self.__packets_file = packets_file
        self.__read_packets_path = []
        

    def parse(self, options):
        if len(options) > 0:
            self.__read_packets_path.append(options[0])
        return 1

    def dump(self):
        if len(self.__read_packets_path) == 0:
            return []
        import converter
        converter.execute(self.__read_packets_path, self.__packets_file)
        return ["-F", self.__packets_file]

    def help(self):
        import converter
        help_string = "    -F pkt_files    support \"%s\" or direcotries that include these kind of files\n"%(",".join(converter.converters.keys()))
        return help_string

class upload_file_enhance(parser):
    
    def __init__(self, option, content_type_modify):
        self.__option = option
        self.__post_files = []
        self.__content_type_modify = content_type_modify
    def parse(self, options):
        if len(options) > 0:
            self.__post_files.append(options[0])
        return 1
    
    def dump(self):
        if len(self.__post_files) == 0:
            return []
        #if Content-Type is set, we don't need automatic inferring
        if self.__content_type_modify.is_set():
            return [self.__option, post_file]

        #current only support one file at once post request
        if len(self.__post_files) > 1:
            error("current only support one file at once request post")
        
        import os
        post_file = self.__post_files[0]
        if not os.path.exists(post_file):
            error(post_file + " isn't exist")

        _,file_ext = os.path.splitext(post_file)
        file_ext = file_ext.lower()

        content_type = "application/octet-stream"
        if file_ext in mime_type_dict:
            content_type = mime_type_dict[file_ext]
        
        return [self.__option, post_file , "-T", content_type]
            
    def help(self):
        if self.__option == "-p":
            return "    -p postfile     File containing data to POST. Content-Type will be detected by file ext,\n"+\
                   "                    the Content-Type will be application/actet-stream if file ext cannot be identified\n"
        elif self.__option == "-u":
            return "    -u putfile      File containing data to PUT. Content-Type will be detected by file ext,\n"+\
                   "                    the Content-Type will be application/actet-stream if file ext cannot be identified\n"

class content_type_modify(parser):
    def __init__(self):
        self.__content_type = None
    def help(self):
        return "    -T content-type Content-type header to use for POST/PUT data, eg.\n"+\
               "                    'application/x-www-form-urlencoded'\n"
    def parse(self, options):
        self.__content_type = options[0]
        return 1
    def is_set(self):
        return self.__content_type != None
    def dump(self):
        if self.__content_type:
            return ["-T", self.__content_type]
        return []
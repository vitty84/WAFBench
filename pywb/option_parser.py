
from pywb_utility import *

class options_parser(object):
    def parse(self, options):
        acceptable_options = "n:c:t:s:b:T:p:u:v:lrkVhwiIx:y:z:C:H:P:A:g:X:de:SqB:m:Z:f:Y:a:o:F:j:J:O:R:D:U:Y:W:E:G:Q:K012:3456789"
        trigger_options = {
            "-F": packet_file_enhance("default.pkt"),
            "-p": upload_file_enhance("-p"),
            "-u": upload_file_enhance("-u"),
            }

        single_option = []
        double_option = []

        i = 0
        while i < len(options):
            option = options[i]
            i+=1
            if option in trigger_options:
                i += trigger_options[option].parse(options[i:])
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
        for _, trigger in trigger_options.items():
            self.__options += trigger.dump()

        self.__options += double_option
        self.__options += single_option

        return len(options)

    def dump(self):
        return self.__options

class packet_file_enhance(options_parser):
    import YAML_convert
    import PKT_convert
    
    __converters = {
        ".yaml":YAML_convert.execute,
        ".pkt":PKT_convert.packet_files_merge,
    }

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

        import packets_outputer
        outputer = packets_outputer.packets_outputer(self.__packets_file)

        for path in self.__read_packets_path:
            import os
            path = os.path.abspath(path)
            if not os.path.exists(path):
                error(path + " is not exist")
            if os.path.isdir(path):
                for _, converter in packet_file_enhance.__converters.items():
                    converter(path, outputer)
            else:
                _, file_ext = os.path.splitext(path)
                file_ext = file_ext.lower()
                if file_ext not in packet_file_enhance.__converters:
                    error(path + "'s extension " + file_ext + " isn't supported")
                packet_file_enhance.__converters[file_ext](path, outputer)

        return ["-F", self.__packets_file]

    @staticmethod
    def help():
        help_string = "    -F pkt_files    support \"%s\" or direcotries that include these kind of files\n"%(",".join(packet_file_enhance.converters.keys()))
        return help_string

class upload_file_enhance(options_parser):
    
    def __init__(self, option):
        self.__option = option
        self.__post_files = []
    def parse(self, options):
        if len(options) > 0:
            self.__post_files.append(options[0])
        return 1
    
    def dump(self):
        if len(self.__post_files) == 0:
            return []

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
            

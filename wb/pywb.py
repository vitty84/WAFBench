#!/usr/bin/python

def error(error_message):
    import sys
    sys.stderr.write(error_message+"\n")
    sys.exit(-1)



def get_wb_path():
    search_positions = ["./wb", "/bin/wb", "/usr/bin/wb"]
    import os
    for position in search_positions:
        if os.path.exists(position):
            return position
    error("wb cannot be found")




class options_parser(object):
    def parse(self, options):
        acceptable_options = "n:c:t:s:b:T:p:u:v:lrkVhwiIx:y:z:C:H:P:A:g:X:de:SqB:m:Z:f:Y:a:o:F:j:J:O:R:D:U:Y:W:E:G:Q:K012:3456789"
        trigger_options = {
            "-F": packet_file_enhance("default.pkt"),
            "-h": helper_enhance(),
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

class packet_file_enhance(object):
    import YAML_convert
    import PKT_convert
    
    converters = {
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
                for _, converter in packet_file_enhance.converters.items():
                    converter(path, outputer)
            else:
                _, file_ext = os.path.splitext(path)
                file_ext = file_ext.lower()
                if file_ext not in packet_file_enhance.converters:
                    error(path + "'s extension " + file_ext + " isn't supported")
                packet_file_enhance.converters[file_ext](path, outputer)

        return ["-F", self.__packets_file]

    @staticmethod
    def help():
        help_string = "    -F pkt_files    support \"%s\" or direcotries that include these kind of files\n"%(",".join(packet_file_enhance.converters.keys()))
        return help_string

class helper_enhance(object):
    def parse(self, options):
        import subprocess
        wb = get_wb_path()
        sub = subprocess.Popen([wb, "-h"], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = sub.communicate()
        
        import re
        help_map = {
            "-F":packet_file_enhance.help
        }

        #find all options start
        start_pattern = "\s{4}(-\w)\s"
        option_start = {}
        for position in re.finditer(start_pattern, stderr):
            last_end = position.start()
            option_start[position.group(1)] = position.start()
            
        #find all options end
        option_end = {}
        end_pattern = "\s{4}(-\w)\s"
        for k, v in option_start.items():
            result = re.search(end_pattern, stderr[v+6:])
            if result:
                option_end[k] = result.start() + v + 6
            else:
                option_end[k] = len(stderr)
        
        anchor = []
        substitution = {}
        for k in help_map.keys():
            anchor.append(option_start[k])
            anchor.append(option_end[k])
            substitution[option_start[k]] = k
        anchor.sort()
        new_help = ""
        copy_pos = 0
        print(anchor)
        print(substitution)
        for i in xrange(len(substitution)):
            new_help += stderr[copy_pos: anchor[i * 2]]
            new_help += help_map[substitution[anchor[i * 2]]]()
            copy_pos = anchor[i * 2 + 1]
            i+=1
        new_help += stderr[copy_pos:]
        
        print(stdout)
        print(new_help)

        import sys
        sys.exit(0)
        return 0

    def dump(self):
        return []

def execute(argument):
    parser = options_parser()
    parser.parse(argument)
    argument = parser.dump()
    real_command = " ".join(argument)
    print(real_command)
    import os
    os.system(real_command)

if __name__ == '__main__':
    import sys
    import os

    executable = os.path.basename(os.path.normpath(sys.argv[0]))
    if executable == "python" or executable == "python3":
        #remove python executable
        sys.argv = sys.argv[1:]
    #remove executable name
    sys.argv = sys.argv[1:]
    execute(sys.argv)
    

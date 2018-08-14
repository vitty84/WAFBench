#!/usr/bin/python

def run_wb(argument, output_filters = []):
    try:
        import subprocess
        wb = subprocess.Popen(argument, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = wb.stdout.readline()
            if not line:
                break
            for flt in output_filters:
                line = flt(line)
                if line is None:
                    break

    except KeyboardInterrupt:
        pass    


def execute(argument, customized_options = {}, customized_filters = []):
    
    #enhance parse option
    import option_parser
    enhance_options = {
            "-F": option_parser.packet_file_enhance("default.pkt"),

            "-p": option_parser.upload_file_enhance("-p"),
            "-u": option_parser.upload_file_enhance("-u"),
            "-T": option_parser.content_type_help_modify(),
            
            }

    for opt, parser in customized_options.items():
        enhance_options[opt] = parser

    parser = option_parser.options_parser(enhance_options = enhance_options)

    parser.parse(argument)
    argument = parser.dump()
    # print(real_command)
    
    #output enhance

    #execute
    import output_filter
    output_filters = [
        output_filter.help_document_revise(enhance_options),
        output_filter.simple_printer(),
    ]

    output_filters = customized_filters + output_filters
    run_wb(argument, output_filters)

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
    

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

    packet_file_enchance = option_parser.packet_file_enhance("default.pkt")
    content_type_modify = option_parser.content_type_modify()
    post_file_enchande = option_parser.upload_file_enhance("-p", content_type_modify)
    put_file_enchande = option_parser.upload_file_enhance("-u", content_type_modify)

    enhance_options = {
            "-F": packet_file_enchance,

            "-p": post_file_enchande,
            "-u": put_file_enchande,
            "-T": content_type_modify,
            
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

    execute(sys.argv[1:])
    

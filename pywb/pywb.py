#!/usr/bin/python

def run_wb(real_command, output_parsers = []):
    import os
    os.system(real_command)

def execute(argument):
    
    #enhance parse option
    import option_parser
    parser = option_parser.options_parser()
    parser.parse(argument)
    argument = parser.dump()
    real_command = " ".join(argument)
    print(real_command)
    
    #output enhance

    #execute
    run_wb(real_command)

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
    

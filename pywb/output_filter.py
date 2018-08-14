
class filter(object):
    def __call__(self, line):
        pass


class simple_printer(filter):
    def __call__(self, line):
        import sys
        sys.stdout.write(line)
        return line


class help_document_revise(filter):
    def __init__(self, enhance_options = {}):
        self.__buffer = ""
        self.__ignore = False
        self.__options = enhance_options

    def __call__(self, line):
        #capture opt
        import re
        pattern = "^\s{4}(-\w)"
        opt = re.search(pattern, line)
        if opt:
            
            opt = opt.group(1)
            if opt in self.__options:
                self.__ignore = True
                return self.__options[opt].help()
            else:
                self.__ignore = False

        #ignore this line
        
        if not self.__ignore:
            return line
        return None
        
        


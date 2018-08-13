# make a outputer to output the packets
# @param packets_file: the path of file that want to output the packets
# @return: packets outputer

class packets_outputer(object):
    def __init__(self, packets_file):
        import sys
        if not packets_file:
            self.__packets_file = sys.stdout
        else:
            self.__packets_file = open(packets_file, 'wb')    

        self.__is_first_packets = True
        
    # output packets
    # @param packets: packets generator
    def __call__(self, packets):
        for packet in packets:
            if not self.__is_first_packets:
                self.__packets_file.write("\0")
            self.__packets_file.write(packet)
            self.__is_first_packets = False
        

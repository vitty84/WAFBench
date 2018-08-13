
    

def read_packets_from_file(pkt_file):
    import os
    pkt_file = os.path.abspath(pkt_file)
    if not os.path.exists(pkt_file):
        import sys
        sys.stderr.write(pkt_file + " is not existed\n")
        sys.exit(-1)
    #second item is file ext
    if os.path.splitext(pkt_file)[1].lower() != ".pkt":
        return None
    with open(pkt_file, "rb") as f:
        return [f.read()]

def packet_files_merge(pkt_files = [], outputer = ""):
    import packets_outputer
    if type(outputer) != packets_outputer.packets_outputer:
        outputer = packets_outputer.packets_outputer(outputer)

    import sys
    #read packets
    if not pkt_files:
        packets = sys.stdin.read()
        outputer(packets)

    if type(pkt_files) == str:
        pkt_files = [pkt_files]

    for pkt_file in pkt_files:
        import os

        pkt_file = os.path.abspath(pkt_file)
        if not os.path.exists(pkt_file):
            import sys
            sys.stderr.write(pkt_file + " is not existed\n")
            sys.exit(-1)
            
        if os.path.isdir(pkt_file):
            for root, _, files in os.walk(pkt_file):
                for file in files:
                    packets = read_packets_from_file(os.path.join(root, file))
                    if packets != None:
                        outputer(packets)    
        elif os.path.isfile(pkt_file):
            packets = read_packets_from_file(pkt_file)
            if packets != None:
                outputer(packets)


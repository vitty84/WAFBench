#!/bin/sh
basepath=$(cd `dirname $0`; pwd)
echo "Send custom traffics"
echo "command: wb -F packets/test-2-packets.pkt -c 20 -t 5 10.0.1.44:12705"
wb -F packets/test-2-packets.pkt -c 20 -t 5 10.0.1.44:12705

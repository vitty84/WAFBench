#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Send traffics customized by yaml"
echo "command: ../Generator/YAML_generator.py packets/test-1-packet.yaml -o /tmp/packet.pkt"
echo "command: wb -F /tmp/packet.pkt -c 20 -t 5 10.0.1.44:12701"
../Generator/YAML_generator.py packets/test-1-packet.yaml -o /tmp/packet.pkt
wb -F /tmp/packet.pkt -c 20 -t 5 10.0.1.44:12701

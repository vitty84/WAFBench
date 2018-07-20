#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

Usage()
{
	USAGE_STR="
RTT - Regression Testing Tool 0.1 (2017 Dec 20, compiled Dec 20 2017 20:00:00)
Usage:
   rtt.sh [arguments]

Example: 
   ./rtt.sh -y rtt_rules/ -l /mnt/netsys44/logs/error.log -d 10.0.1.44:12701. 

Required Arguments:
   -d <destination>     specify your destination address and prot, e.g. -d 10.0.1.44:12701.                  
   -y <input_yaml>      specify the yaml file or the folder including the yaml files.
   -l <input_log>       specify the modsecurity error.log. Please mount the folder containing your logs first.

Optional Arguments:
   -o <output_result>   Specify the output file for logging the testing result.
   -h                   Print Help (this message) and exit                   

"
	echo "$USAGE_STR"
	exit
}

INPUT_YAML_FILE=""
INPUT_DST_ADDR=""
INPUT_LOG_FILE=""
OUTPUT_RESULT_FILE=""

while getopts "d:y:l:o:h" arg
do
        case $arg in
        d)
		INPUT_DST_ADDR=$OPTARG
                ;;
	y)
		INPUT_YAML_FILE=$OPTARG
		;;
	l)
		INPUT_LOG_FILE=$OPTARG
		;;
	o)
		OUTPUT_RESULT_FILE=$OPTARG
		;;
        h)
                Usage
                ;;
        ?)
                echo "Unknown Argument: $arg"
                Usage
                ;;
        esac
done

if [ "$INPUT_YAML_FILE" = "" ];
then
	echo "Please input your Yaml File/Folder using -y."
	Usage
elif [ -f $INPUT_YAML_FILE ]; 
then
	GEN_YAML_FILE_FLAG="-f"
elif [ -d $INPUT_YAML_FILE ]; 
then
	GEN_YAML_FILE_FLAG="-f"
else
	echo "Unexpected Error."
	Usage
fi

if [ "$INPUT_LOG_FILE" = "" ];
then
	echo "Please input your modsecurity log file using -l."
	Usage
elif [ ! -f $INPUT_LOG_FILE  ];
then
	echo "The log file $INPUT_LOG_FILE cannot be found."
	Usage
fi

if [ "$INPUT_DST_ADDR" = "" ];
then
	echo "Please input your destination using -d."
	Usage
fi
TEMP_PKTS_FILE=temp_requests.dat
TEMP_RESPONSE_FILE=temp_responses.dat
REPEAT_TIME=1

python ftw_generator.py $GEN_YAML_FILE_FLAG $INPUT_YAML_FILE -o $TEMP_PKTS_FILE
echo "" > $INPUT_LOG_FILE
echo "python ftw_generator.py $GEN_YAML_FILE_FLAG $INPUT_YAML_FILE -o $TEMP_PKTS_FILE"
wb -r -U "" -F $TEMP_PKTS_FILE -o $TEMP_RESPONSE_FILE -n $REPEAT_TIME $INPUT_DST_ADDR 
python ftw_comparator.py -L $INPUT_LOG_FILE -q $TEMP_PKTS_FILE -r $TEMP_RESPONSE_FILE -o $OUTPUT_RESULT_FILE -j $OUTPUT_RESULT_FILE.json

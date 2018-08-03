[WB Home Page](../README.md)

# FTW-Compatible Tool

FTW-Compatible Tool is the wb's extension module, which supports [FTW](https://github.com/fastly/ftw)(Framework for Testing WAFs) format YAML for WAF correctness testing. As FTW, it uses the OWASP Core Ruleset V3 as a baseline.

## Introduction

FTW-Compatible Tool is a part of [WB](../README.md), the Web Application Firewall Bench tool suits. It contains 4 tools: FTW Generator, FTW Comparator, FTW Log Searcher and Regression Testing Tool.

* *FTW Generator*: According to the FTW format YAML files, the FTW Generator generate input packets for [wb](../wb/README.md);
* *FTW Comparator*: FTW Comparator does comparison between WB's output and related expected conditions written in FTW format YAML files;
* *FTW Log Searcher*: According to a given test title, FTW Log Searcher can find the detailed information including raw YAML, request, response, and etc.;
* *Regression Testing Tool (rtt.sh)*: rtt.sh is the script that makes FTW-Compatible Tool easier to use.

## Installation

### Dependencies

* **Python** to run those script
* **FTW** python module to interpret YAML file

Python2 installation is as follows: 

```
sudo yum install python           # Install python2
sudo yum install python-pip       # Install python2 pip
sudo pip install --upgrade pip    # Update pip
sudo pip install ftw			  # Install the ftw library
```

Python3 installation is as follows: 

```
sudo yum install python34         # Intanll python3
sudo yum install python34-pip     # Intanll python3 pip
sudo pip3 install --upgrade pip   # Update pip
sudo pip3 install ftw			  # Install the ftw library
```

## How to use FTW-compatible tools 

### Before Using FTW Toolset

* In order to analyze the log of the server, the FTW-compatatible tool will send a dummy request after each normal request. This dummy request is designed to generate a special marker in the log of the server, so we can identify in each trace of log to which request belongs.
* Then, to generate the marker, we need to add a rule file *1000-WB-Logrule.conf* into Modsecurity ruleset. This rule will cause no influence to the WAF, but just add a special log information when a dummy request is received.
* To get the server's log conveniently, we recommends you to mount the server's log file to the local test client machine. Here is a reference: [link](https://unix.stackexchange.com/questions/62677/best-way-to-mount-remote-folder).
* What's more, you also need to modify some configuration of the CRS on the server. You can refer to [FTW Readme](https://github.com/fastly/ftw/blob/master/README.md) about how FTW configures the server.

### FTW Generator

```
python ftw_generator.py -f <input_file> [<optional arguments>]
```

The list of arguments:

* -f *\<input_file\>*: The input YAML file or folder of requests.
* -o *\<output_request_file\>*: The output request file name. Default is 'temp_requests.dat'.
* -y *\<output_raw_yaml_file\>*: The file to save the raw YAML code of each request, which is used by FTW Log Searcher. Default is 'temp_raw_yaml.dat'.
* -c *\<output_conditions_file\>*: The file to save the comparison conditions for each file. Default is 'temp_conditions.dat'.

The FTW Generator accepts FTW-Compatible YAML files and converts it into packaged request file, which can be parsed by WB Sender with *-F \<packaged-request-file\>* directive. 

**Note**: The argument -f and -F can only use one at the same time.

**Note**: You may find example yaml files in [Regression tests for OWASP CRS v3](https://github.com/SpiderLabs/OWASP-CRS-regressions).

### FTW Comparator

```
python ftw_comparator.py -L <input_server_log> [optional arguments]
```

The argument list is as follows:

* -q *\<input_request_file\>*: The packaged request file generated by FTW Generator. Default is 'temp_requests.dat'
* -r *\<input_response_file\>*: The packaged response file generated by WB. Default is 'temp_responses.dat'
* -y *\<input_raw_yaml_file\>*: The raw YAML code file generated by FTW Generator. Default is 'temp_raw_yaml.dat'
* -L *\<input_server_log\>*: The log of the proxy server under test. Usually we use mount or other method to get the remote server log.
* -c *\<input_conditions_file\>*: The comparison conditions file generated by FTW Generator. Default is 'temp_conditions.dat'
* -o *\<output_result\>*: The file to save the comparison result. Default is 'comp_output.dat'.
* -j *\<output_result_json\>*: The file so save the comparison result in JSON diction file. Used by FTW Log Searcher. Default is 'comp_output.dat.json'

When WB finishing HTTP exchange a response result file will be generated if  `-o/-R <response-file-name>` option is set. FTW Comparator can verify the WAF correctness by taking YAML file, response result and server log as arguments and print report of that on the screen.

### FTW Log Searcher

```
python ftw_log_searcher.py [-f result_json_file]
```

The argument list is as follows:
* -f *\<result_json_file\>*: specify the json file generated by FTW Comparator. Default is 'comp_output.json'.

This tool is used to inquire the detailed information of given test. This tool will output the raw YAML code, the real traffic package, the real response package and the check result according to the input test title. When you input the empty string, the program will exit.

### FTW Test Script - Regression Testing Tool (RTT)

If reading tutorial written above carefully you'll find that a typical test cycle combines *FTW Generator*, [*WB*](../wb/README.md) and *FTW Comparator* together:

```
python ftw_generator.py ...
wb ...
python ftw_comparator.py...
```

To save your time, the FTW Test Script --- rtt.sh --- has been introduced for this purpose. It do all jobs for you with several options. Therefore just run
```
 ./rtt.sh -y <input_yaml> -d <destination> -l <input_log> [optional arguments]
```

The argument list is as follows:
* -d *\<destination\>*: Specify your destination address and prot, e.g. -d 10.0.1.44:12701.
* -y *\<input_yaml\>*: Specify the YAML file or the folder including the YAML files.
* -l *\<input_log\>*: Specify the modsecurity error.log. Please mount the folder containing your logs first.
* -o *\<output_result\>*: Specify the output file for logging the testing result. If this option is not indicated, the result will be output to stdout.
* -s *\<timeout\>*: Specify the maximum number of seconds to wait before the socket times out. Default is 1 second.
* -h: print help and exit  

**Note**: You may find example yaml files in [Regression tests for OWASP CRS v3](https://github.com/SpiderLabs/OWASP-CRS-regressions).
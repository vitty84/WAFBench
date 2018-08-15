[WB Home Page](../README.md)

# pywb

`pywb` is an enhanced interface for `wb`. It is more friendly to use and more easy for developing.

## Features

## Prerequisites

Some software or libraries may be necessary for have been listed in [WB Home Page](../README.md), but another requisite is that `wb`(after 2018-08-14) need be installed.

### Synopsis

```
./pywb.py [options] [http[s]://]hostname[:port]/path
```

### Options


**options** are compatible with [wb](../wb/README.md).


***ENHANCE OPTION***

- -F supports *.yaml and *.pkt and directories that include these kinds of file.
- -u and -p will automatically identify the file type that wants to be sent by its ext, and modify the Content-Type. These options support almost all of the types that are mentioned by MIME.

### Example

Normal usage:

```
#post a json file
./pywb.py  10.0.1.131:18080  -p ../example/packets/requestbody2kb.json  -t 5 -c 20

#send packets in a specified direcotry
./pywb.py  10.0.1.131:18080  -F ../example/packets/  -t 5 -c 20
```

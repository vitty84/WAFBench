[WB Home Page](../README.md)

# Generator

Because handwritten `wb` format packets are error-prone, there are several generators for transforming high-level information to `wb` format packets.

## YAML Generator

YAML generator generates `wb` format packets from [FTW](https://github.com/fastly/ftw) format YAML. You should refer to the [link](https://github.com/fastly/ftw/blob/master/docs/YAMLFormat.md) for detailed format description.

### Synopsis

```
    python yaml_generator.py [options] [files...]
    ./yaml_generator.py [option] [files...]
```

### Options

```
    FILES...    input yaml files or directory, default is stdin if no
    files are provided

    -o/--output output packets file, default is stdout

    -h/--help   print help
```

### Example

Normal usage:

```
./YAML_generator.py example/dir/ -o packets.pkt
```

Pipe is recommended to test YAML file and observe the output:

```
cat file.yaml | ./YAML_generator.py
```



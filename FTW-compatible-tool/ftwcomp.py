#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" ftwcomp(FTW-Compatible-Tool)
"""

import os
import sys
import copy
import datetime
import sqlite3
import argparse
import re
import uuid
import ast
import collections

import pywb
import ftwsql
import ftw


def ExistSetElseNone(dict_, key_):
    return dict_[key_] if key_ in dict_ else None


def load_tests(db_connector, yaml_paths):
    cursor = db_connector.cursor()
    for test in \
            pywb.ftwhelper.get(yaml_paths, pywb.ftwhelper.FTW_TYPE.TEST):
        for stage in \
                pywb.ftwhelper.get(test, pywb.ftwhelper.FTW_TYPE.STAGE):
            for packet in \
                    pywb.ftwhelper.get(stage, pywb.ftwhelper.FTW_TYPE.PACKETS):
                cursor.execute(
                    ftwsql.SQL_INSERT_REQUEST,
                    (
                        str(uuid.uuid1().int),
                        test["test_title"],
                        str(test),
                        str(test.ORIGINAL_FILE),
                        str(stage['input']),
                        str(stage['output']),
                        packet,
                    ))
    db_connector.commit()


def init_ftw_db(db_name):
    if not db_name:
        db_name = "ftw.%s.%s.sqlite3.db" % (
            os.getpid(),
            str(datetime.datetime.now()).replace(' ', '-')
        )
    db_connector = sqlite3.connect(db_name)
    # initialize database : create table and index
    cursor = db_connector.cursor()
    try:
        cursor.executescript(ftwsql.SQL_INITIALIZE_DATABASE)
        db_connector.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        return db_connector


class Delimiter(object):
    _MAGIC_PATTERN = r"{magic_string}-<{unique_key}>"

    _DELIMITER_PACKET_FORMAT = r'''
---
  meta:
    author: "Microsoft"
    enabled: true
    description: "Delimiter packet"
  tests:
    -
      test_title: {magic_pattern}
      stages:
        -
          stage:
            input:
              dest_addr: "127.0.0.1"
              port: 80
              uri: "/"
              headers:
                  User-Agent: "WAFBench"
                  Host: "{magic_pattern}"
                  Accept: "*/*"
            output:
                  log_contains: ""
    '''

    _DELIMITER_RULE_FORMAT = r'''
SecRule REQUEST_HEADERS:Host "{magic_pattern}" \
    "phase:5,\
    id:010203,\
    t:none,\
    block,\
    msg:'%{{matched_var}}'"
    '''

    @staticmethod
    def _generate_magic_string():
        return "%s" % (uuid.uuid1().int, )

    def __init__(self, magic_string=None):
        if magic_string:
            self._magic_string = magic_string
        else:
            self._magic_string = Delimiter._generate_magic_string()
        pattern = Delimiter._MAGIC_PATTERN.format(
            **{
                "magic_string": self._magic_string,
                "unique_key": r"(\w*)",
            }
        )
        self._magic_search = re.compile(pattern)

    def get_delimiter_rule(self):
        return Delimiter._DELIMITER_RULE_FORMAT.format(
            **{"magic_pattern": self._magic_search.pattern}
        )

    def get_delimiter_key(self, line):
        result = self._magic_search.search(line)
        if result:
            return result.group(1)
        else:
            return None

    def get_delimiter_packets(self, key):
        yaml_string = Delimiter._DELIMITER_PACKET_FORMAT.format(
            **{"magic_pattern": Delimiter._MAGIC_PATTERN.format(
                **{
                    "magic_string": self._magic_string,
                    "unique_key": str(key)
                }
            )}
        )
        for packet in\
                pywb.ftwhelper.get(
                    yaml_string,
                    pywb.ftwhelper.FTW_TYPE.PACKETS):
            yield packet


def create_pkt_file(db_connector, file_path, delimiter=None):
    cursor = db_connector.cursor()
    cursor = cursor.execute(ftwsql.SQL_QUERY_REQUEST)
    with pywb.packetsdumper.PacketsDumper(file_path) as dumper:
        while True:
            row = cursor.fetchone()
            if not row:
                break
            if delimiter:
                # insert begin delimiter
                dumper.dump(delimiter.get_delimiter_packets(row[0]))
            dumper.dump(row[1])
            if delimiter:
                # insert end delimiter
                dumper.dump(delimiter.get_delimiter_packets(row[0]))


def parse(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument("-db", "--db", required=False)
    return parser.parse_args(arguments)


class COLLECT_STATE:
    FINISH_COLLECT = 1
    START_COLLECT = 2
    PAUSE_COLLECT = 3
    FINISH_COLLECT = 4

REQUEST_PATTERN = r"^writing request\((\d+) bytes\)\=\>\["
RESPONSE_PATTERN = r"^LOG\: http packet received\((\d+) bytes\)\:\n"


class RawPacketCollector(object):
    def __init__(self, start_pattern, end_pattern):
        self._start_pattern = start_pattern
        self._end_pattern = end_pattern
        self.reset()

    def __call__(self, line):
        result = re.search(self._start_pattern, line)
        if self.rested_size == 0 and result:
            self.state = COLLECT_STATE.START_COLLECT
            self.rested_size = int(result.group(1))
            line = line[len(result.group(0)):]
        if self.rested_size and self.state == COLLECT_STATE.START_COLLECT:
            if len(line) < self.rested_size:
                self.collected_buffer += line
                self.rested_size -= len(line)
            else:
                self.collected_buffer += line[:self.rested_size]
                self.rested_size = 0
                self.state = COLLECT_STATE.PAUSE_COLLECT
        if self.state != COLLECT_STATE.FINISH_COLLECT\
                and self.rested_size == 0\
                and re.match(self._end_pattern, line):
            finished_buffer = self.collected_buffer
            self.state = COLLECT_STATE.FINISH_COLLECT
            self.reset()
            return finished_buffer
        return None

    def reset(self):
        self.state = COLLECT_STATE.FINISH_COLLECT
        self.collected_buffer = ""
        self.rested_size = 0


class RealTrafficCollector(object):
    def __init__(self, db_connector, delimiter):
        self._cursor = db_connector.cursor()
        # clean raw traffic
        self._cursor.execute(ftwsql.SQL_CLEAN_RAW_TRAFFIC)
        self._delimiter = delimiter
        self._reset()

    def __call__(self, request_packet, response_packet):
        key = self._delimiter.get_delimiter_key(request_packet)
        if key:
            if self._current_key is None:
                # enter collect
                self._current_key = key
            elif self._current_key == key:
                # exit collect
                ret = self._cursor.execute(
                    ftwsql.SQL_INSERT_RAW_TRAFFIC,
                    (
                        self._request_buffer,
                        self._response_buffer,
                        self._current_key
                    )
                )
                if ret.rowcount == 0:
                    raise ValueError(
                        "Traffic %s is not existed" % (self._current_key,)
                    )
                elif ret.rowcount > 1:
                    raise ValueError(
                        "Traffic %s is not unique, internal error"
                        % (self._current_key,)
                    )
                self._reset()
            else:
                raise ValueError(
                    "Traffic %s doesn't have end delimiter, traffic error"
                    % (self._current_key,)
                )
        else:
            if request_packet:
                self._request_buffer += request_packet
            if response_packet:
                self._response_buffer += response_packet

    def _reset(self):
        self._current_key = None
        self._request_buffer = ""
        self._response_buffer = ""


class OutputCollector(pywb.OutputFilter):
    def __init__(self, real_traffic_collector):
        self._real_traffic_collector = real_traffic_collector
        self._raw_request_collector = \
            RawPacketCollector(
                REQUEST_PATTERN,
                RESPONSE_PATTERN
            )
        self._raw_response_collector = \
            RawPacketCollector(
                RESPONSE_PATTERN,
                r"(%s)|(^Complete requests)" % (REQUEST_PATTERN,)
            )

    def __call__(self, line):
        request_collect_state = self._raw_request_collector.state
        response_collect_state = self._raw_response_collector.state
        raw_request_buffer = None
        raw_response_buffer = None

        if response_collect_state != COLLECT_STATE.START_COLLECT:
            raw_request_buffer = self._raw_request_collector(line)
        if request_collect_state != COLLECT_STATE.START_COLLECT:
            raw_response_buffer = self._raw_response_collector(line)

        if raw_request_buffer:
            self._raw_request_buffer = raw_request_buffer
        if raw_response_buffer:
            self._raw_response_buffer = raw_response_buffer
            self._record_raw_data()

    def _record_raw_data(self):
        self._real_traffic_collector(
            self._raw_request_buffer,
            self._raw_response_buffer)
        self._raw_request_buffer = ""
        self._raw_response_buffer = ""


class LogCollector(object):
    def __init__(self, db_connector, delimiter):
        self._cursor = db_connector.cursor()
        # clean raw log
        self._cursor.execute(ftwsql.SQL_CLEAN_RAW_LOG)
        self._delimiter = delimiter
        self._reset()

    def __call__(self, logline, reversed_=False):
        key = self._delimiter.get_delimiter_key(logline)
        if key:
            if self._current_key is None:
                # enter collect
                self._current_key = key
            elif self._current_key == key:
                # exit collect
                ret = self._cursor.execute(
                    ftwsql.SQL_INSERT_RAW_LOG,
                    (
                        self._log_buffer.strip(),
                        self._current_key
                    )
                )
                if ret.rowcount > 1:
                    raise ValueError(
                        "Traffic %s is not unique, internal error"
                        % (self._current_key,)
                    )
                self._reset()
            else:
                raise ValueError(
                    "Traffic %s doesn't have end delimiter, traffic error"
                    % (self._current_key,)
                )
        else:
            if logline:
                if reversed_:
                    self._log_buffer = "%s\n%s" % (logline, self._log_buffer)
                else:
                    self._log_buffer = "%s\n%s" % (self._log_buffer, logline)

    def _reset(self):
        self._current_key = None
        self._log_buffer = ""


def modify_rule_config(delimiter):
    print("Add this rule into the tail of rule conf file")
    print(delimiter.get_delimiter_rule())
    raw_input("Press Enter to continue")


def export_log(db_connector, delimiter, logpath=None):
    if logpath:
        collector = LogCollector(db_connector, delimiter)
        with open(logpath, "r") as fd:
            for line in fd:
                collector(line, reversed_=False)
    else:
        collector = LogCollector(db_connector, delimiter)
        print("Input log (ctl+d to finish) or log file path >>")
        while True:
            try:
                line = raw_input("")
                if os.path.isfile(os.path.expanduser(line)):
                    export_log(db_connector, delimiter, line)
                    return
                collector(line, reversed_=False)
            except EOFError:
                break
    db_connector.commit()


def check_result(db_connector):
    cursor = db_connector.cursor()
    cursor = cursor.execute(ftwsql.SQL_QUERY_RESULT)

    STATUS = "status"
    LOG = "log_contains"
    NOTLOG = "no_log_contains"
    RESPONSE = "response_contains"
    HTML = "html_contains"
    ERROR = "expect_error"

    while True:
        row = cursor.fetchone()
        if not row:
            break
        result_row = collections.OrderedDict(
            (cursor.description[i][0], row[i])
            for i in range(0, len(cursor.description))
        )
        output = ast.literal_eval(result_row["output"])
        error = ""
        matched = True
        try:
            if STATUS in output:
                matched = matched and \
                    (bool(result_row["raw_response"])
                     and bool(re.search(
                         output[STATUS],
                         result_row["raw_response"].split('\n')[0])))

            if LOG in output:
                matched = matched and \
                    (bool(result_row["raw_log"])
                     and bool(re.search(
                              output[LOG],
                              result_row["raw_log"])))

            if NOTLOG in output:
                matched = matched and \
                    (not bool(result_row["raw_log"])
                     or not bool(re.search(
                         output[NOTLOG],
                         result_row["raw_log"])))

            if RESPONSE in output:
                matched = matched and \
                    (bool(result_row["raw_response"]
                          and bool(re.search(
                              output[RESPONSE],
                              result_row["raw_response"]))))

            if HTML in output:
                matched = matched and \
                    (bool(result_row["raw_response"]
                          and bool(re.search(
                              output[HTML],
                              result_row["raw_response"]))))

            if ERROR in output:
                matched = matched and \
                    (bool(result_row["raw_response"])
                        is not bool(output[ERROR]))

            if not matched:
                for key, value in result_row.items():
                    print("%s : %s" % (key, repr(value)))
                print error

        except re.error as e:
            print(e)


def execute(arguments):
    # parse argument
    arguments = parse(arguments)

    # init ftw db
    db_connector = init_ftw_db(":memory:")
    # db_connector = init_ftw_db("example.db")

    # load tests by yaml paths
    load_tests(
        db_connector,
        "~/demo/WAFBench/FTW-compatible-tool/test-2-attack-packets.yaml")

    # create .pkt file by db
    delimiter = Delimiter("Delimiter")
    create_pkt_file(db_connector, "test.pkt", delimiter)

    # modify rule config
    modify_rule_config(delimiter)

    # execute pywb
    collector = RealTrafficCollector(db_connector, delimiter)
    ret = pywb.execute([
        "-F", "test.pkt",
        "-v", "4",
        "netsys44:18080",
        "-n", "1",
        "-c", "1",
        "-r",
        "-o", "/dev/null"],
        customized_filters=[OutputCollector(collector)])
    db_connector.commit()

    # export log
    export_log(db_connector, delimiter)

    # check result at db
    check_result(db_connector)

    db_connector.close()

    print("Finish")
    return ret

if __name__ == "__main__":
    sys.exit(execute(sys.argv[1:]))
    pass

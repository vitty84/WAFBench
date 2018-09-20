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
import textwrap
import functools
import abc
import inspect

import pywb
import ftwsql
import ftw


def get_terminal_szie():
    return map(int, os.popen('stty size', 'r').read().split())


MAX_HEIGHT, MAX_WIDTH = get_terminal_szie()


# TOPICS
class TOPICS(object):

    # func(raw_request)
    RAW_REQUEST = "RAW_REQUEST"
    # func(raw_response)
    RAW_RESPONSE = "RAW_RESPONSE"

    # func(traffic_id, traffic_request, traffic_response)
    TRAFFIC = "TRAFFIC"
    # func(line)
    RAW_LOG = "RAW_LOG"

    # func(traffic_id, log_content)
    CHECK_RESULT = "CHECK_RESULT"

    SPECS = {
        RAW_REQUEST: inspect.ArgSpec(
            args=["raw_request"],
            varargs=None,
            keywords=None,
            defaults=None
        ),
        RAW_RESPONSE: inspect.ArgSpec(
            args=["raw_response"],
            varargs=None,
            keywords=None,
            defaults=None
        ),
        TRAFFIC: inspect.ArgSpec(
            args=["traffic_id", "traffic_request", "traffic_response"],
            varargs=None,
            keywords=None,
            defaults=None
        ),
        RAW_LOG: inspect.ArgSpec(
            args=['line'],
            varargs=None,
            keywords=None,
            defaults=None
        ),
        CHECK_RESULT: inspect.ArgSpec(
            args=['traffic_id, log_content'],
            varargs=None,
            keywords=None,
            defaults=None
        ),
    }


class Broker(object):

    def __init__(self):
        self._subscribers = {}

    def _check_spec(self, topic, subscriber):
        if topic not in TOPICS.SPECS:
            return
        target_spec = TOPICS.SPECS[topic]
        subscribe_spec = inspect.getargspec(subscriber)
        if subscribe_spec == target_spec:
            return
        method_spec = copy.deepcopy(target_spec)
        method_spec.args.insert(0, 'self')
        if subscribe_spec == method_spec:
            return
        raise ValueError(
            "subscriber<%s> is not compatible with the topic<%s> spec<%s>"
            % (subscribe_spec, topic, target_spec))

    def subscribe(self, topic, subscriber):
        self._subscribers.get(topic, []).append(subscriber)

    def publish(self, topic, *args, **kwargs):
            map(lambda subscriber: subscriber(*args, **kwargs),
                self._subscribers.get(topic, []))


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


def init_ftw_db(arguments):
    db_connector = sqlite3.connect(arguments.database)
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


def create_pkt_file(db_connector, file_path,
                    delimiter=None, select_sql=ftwsql.SQL_QUERY_REQUEST):
    cursor = db_connector.cursor()
    cursor = cursor.execute(select_sql)
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


class COLLECT_STATE:
    FINISH_COLLECT = 1
    START_COLLECT = 2
    PAUSE_COLLECT = 3
    FINISH_COLLECT = 4

REQUEST_PATTERN = r"^writing request\((\d+) bytes\)\=\>\["
RESPONSE_PATTERN = r"^LOG\: http packet received\((\d+) bytes\)\:\n"


class RawPacketCollector(object):
    def __init__(self, start_pattern, end_pattern,
                 topic, broker):
        self._start_pattern = start_pattern
        self._end_pattern = end_pattern
        self._topic = topic
        self._broker = broker
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
            self._broker.publish(self._topic, self.collected_buffer)
            self.state = COLLECT_STATE.FINISH_COLLECT
            self.reset()
            return finished_buffer
        return None

    def reset(self):
        self.state = COLLECT_STATE.FINISH_COLLECT
        self.collected_buffer = ""
        self.rested_size = 0


class RealTrafficCollector(object):
    def __init__(self, db_connector, delimiter, interactor=None):
        self._cursor = db_connector.cursor()
        # clean raw traffic
        self._cursor.execute(ftwsql.SQL_CLEAN_RAW_TRAFFIC)
        self._delimiter = delimiter
        self._interactor = interactor
        self._traffic_count = 0
        self._received_count = 0

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
                if self._interactor:
                    if self._traffic_count == 0:
                        self._cursor.execute(
                            ftwsql.SQL_QUERY_TRAFFIC_COUNT)
                        self._traffic_count = \
                            int(self._cursor.fetchone()[0])
                    if self._traffic_count != 0:
                        self._cursor.execute(
                            ftwsql.SQL_QUERY_TEST_TITLE,
                            (self._current_key,))
                        row = self._cursor.fetchone()
                        self._received_count += 1
                        self._interactor.progress_bar(
                            self._received_count,
                            self._traffic_count,
                            row[0])
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
        # return line

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
        print("Input"
              " the log strings (Ctl-D <i.e. EOF> to finish input) "
              "or the log file path :")
        while True:
            try:
                line = raw_input("")
                if os.path.isfile(os.path.expanduser(line)):
                    export_log(db_connector, delimiter, line)
                    return
                collector(line, reversed_=False)
            except EOFError:
                break


def check_result(db_connector, interactor):
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
        result_row["output"] = ast.literal_eval(result_row["output"])
        check_result = {}
        try:
            if STATUS in result_row["output"]:
                check_result[STATUS] = \
                    (bool(result_row["raw_response"])
                     and bool(re.search(
                         repr(result_row["output"][STATUS]),
                         result_row["raw_response"].split('\n')[0])))

            if LOG in result_row["output"]:
                check_result[LOG] = \
                    (bool(result_row["raw_log"])
                     and bool(re.search(
                              repr(result_row["output"][LOG]),
                              result_row["raw_log"])))

            if NOTLOG in result_row["output"]:
                check_result[NOTLOG] = \
                    (not bool(result_row["raw_log"])
                     or not bool(re.search(
                         repr(result_row["output"][NOTLOG]),
                         result_row["raw_log"])))

            if RESPONSE in result_row["output"]:
                check_result[RESPONSE] = \
                    (bool(result_row["raw_response"]
                          and bool(re.search(
                              repr(result_row["output"][RESPONSE]),
                              result_row["raw_response"]))))

            if HTML in result_row["output"]:
                check_result[HTML] = \
                    (bool(result_row["raw_response"]
                          and bool(re.search(
                              repr(result_row["output"][HTML]),
                              result_row["raw_response"]))))

            if ERROR in result_row["output"]:
                check_result[ERROR] = \
                    (bool(result_row["raw_response"])
                        is not bool(result_row["output"][ERROR]))
            interactor.print_check_result(result_row, check_result)
        except re.error as e:
            print(e)


def parse(arguments):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--database",
        default=":memory:"
    )

    test_ = parser.add_argument_group("test")
    test_.add_argument(
        "-s",
        "--server",
    )
    test_.add_argument(
        "-l",
        "--log",
    )
    mode = test_.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        "-r",
        "--replay",
        action="store_true")
    mode.add_argument(
        "-t",
        "--testset",
        action="store")

    observe = parser.add_argument_group("observe")
    observe.add_argument(
        "--show",
        action="store_true"
    )
    arguments = parser.parse_args(arguments)
    return arguments


class Interactor(object):
    class UI:
        RESET = '\033[0m'
        BOLD = '\033[01m'
        UNDERLINE = '\033[04m'

        class FG:
            RED = '\033[31m'
            YELLOW = '\033[93m'

        class BG:
            RED = '\033[41m'
            LIGHTGREY = '\033[47m'

    def __init__(
            self,
            arguments,
            db_connector,
            delimiter):
        self._arguments = arguments
        self._cursor = db_connector.cursor()
        self._delimiter = delimiter
        self.welcome()

    def welcome(self):
        print(r'''
________________________      __          _________
\_   _____/\__    ___/  \    /  \         \_   ___ \  ____   _____ ______
 |    __)    |    |  \   \/\/   /  ______ /    \  \/ /  _ \ /     \\____ \
 |     \     |    |   \        /  /_____/ \     \___(  <_> )  Y Y  \  |_> >
 \___  /     |____|    \__/\  /            \______  /\____/|__|_|  /   __/
     \/                     \/                    \/             \/|__| 
            ''')

    def bye(self):
        print("")
        print("~" * MAX_WIDTH)
        print("bye~")

    def prepared_tutorial(self):
        print("Add this rule into the tail of rule conf file")
        print(self._delimiter.get_delimiter_rule())
        raw_input("Press Enter to continue")

    def progress_bar(self, count, total, title):
        if count > total:
            raise ValueError(
                "Count(%s) over total(%s) : %s" % (count, total, title))

        total_len = MAX_WIDTH
        done_filling = '*'
        undone_filling = '-'

        percent_len = len("100.0%")
        filling_len = total_len - percent_len - 2
        title = "(%s)" % (title)
        if len(title) > filling_len:
            title = title[:filling_len - 4] + "...)"
        title_len = len(title)
        percent = float(int(count / float(total)) * 100) / 100.0
        done_filling_len = int(max(
            percent * filling_len - title_len, 
            0))
        undone_filling_len = int(max(
            filling_len - title_len - done_filling_len,
            0))
        buffer_ = "[{title}{done_filling}{undone_filling}]{percent}%"
        buffer_ = buffer_.format(
            title=title,
            done_filling=done_filling * done_filling_len,
            undone_filling=undone_filling * undone_filling_len,
            percent=("%s" % (100.0 * percent, )
                     ).rjust(len("100.0"))[:len("100.0")]
        )
        if count == total:
            sys.stdout.write(buffer_ + "\n")
        else:
            sys.stdout.write(buffer_ + "\r")
        sys.stdout.flush()

    def import_log_tutorial(self):
        if not self._arguments.log:
            print("Input"
                  " the log strings (Ctl-D <i.e. EOF> to finish input) "
                  "or the log file path :")

    def print_check_result(self, traffic, check_result):
        # All check is OK
        if reduce(lambda x, y: x and y, check_result.values()):
            return

        wrapper = textwrap.TextWrapper()
        wrapper.width = MAX_WIDTH
        indent = len(max(traffic.keys(), key=len))
        # '+3' for two spaces and a colon
        wrapper.subsequent_indent = ' ' * (indent + 3)
        for k, v in traffic.items():
            prefix = Interactor.UI.BOLD \
                + k.ljust(indent) \
                + Interactor.UI.RESET
            wrapper.initial_indent = prefix + " : "

            buffer_ = ""
            if k == "output":
                buffer_ += "{"
                len_ = len(v.keys())
                for k, v in v.items():
                    if not check_result[k]:
                        buffer_ += Interactor.UI.BG.RED + Interactor.UI.BOLD
                    buffer_ += "%s: %s" % (k, repr(v))
                    buffer_ += Interactor.UI.RESET
                    len_ -= 1
                    if len_ != 0:
                        buffer_ += ", "
                buffer_ = buffer_.strip()
                buffer_ += "}"
            elif isinstance(v, str) or isinstance(v, unicode):
                buffer_ += repr(v.encode('utf-8'))
            else:
                buffer_ += str(v)
            print(wrapper.fill(buffer_))


def execute(arguments, interactor=Interactor):
    # parse argument
    arguments = parse(arguments)

    # init environment
    # init broker
    broker = Broker()
    # init ftw db
    db_connector = init_ftw_db(arguments)
    # init delimiter
    delimiter = Delimiter("Delimiter")
    # init interactor
    interactor = interactor(arguments, db_connector, delimiter)
    # init collectors
    real_traffic_collector = \
        RealTrafficCollector(db_connector, delimiter, interactor)
    wb_output_collector = \
        OutputCollector(real_traffic_collector)

    # load tests by yaml paths
    load_tests(
        db_connector,
        "~/demo/WAFBench/FTW-compatible-tool/test-2-attack-packets.yaml")
    # load_tests(
    #     db_connector,
    #     "~/demo/WAFBench/FTW-compatible-tool/OWASP-CRS-regressions/tests/")

    # create .pkt file by db
    create_pkt_file(db_connector, "test.pkt", delimiter)

    # execute pywb
    ret = pywb.execute([
        "-F", "test.pkt",
        "-v", "4",
        "netsys44:18080",
        "-n", "1",
        "-c", "1",
        "-r",
        "-s", "1",
        "-o", "/dev/null"],
        customized_filters=[wb_output_collector])

    # pywb success
    if ret == 0:
        # export log
        export_log(db_connector, delimiter)
        db_connector.commit()

        # check result at db
        check_result(db_connector, interactor)
    else:
        db_connector.rollback()

    db_connector.close()

    interactor.bye()
    return ret

if __name__ == "__main__":
    sys.exit(execute(sys.argv[1:]))
    pass

# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

def error(error_message):
    import sys
    sys.stderr.write(error_message+"\n")
    sys.exit(-1)


def get_wb_path():
    search_positions = ["./wb", "../wb/wb", "/bin/wb", "/usr/bin/wb"]
    import os
    for position in search_positions:
        if os.path.exists(position):
            return position
    error("wb cannot be found")


import mimetypes
mimetypes.init()
mime_type_dict = mimetypes.types_map
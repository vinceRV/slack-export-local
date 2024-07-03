#!/bin/bash

export_destination=html_output
local_destination=local_only

function usage {
    [ -n "$1" ] && echo -e "\n$1\n"
    echo "Usage: $0 archive_name"
    exit 1
}

archive_name=$1
[ -z "$archive_name" ] && usage "missing archive name"

[ -d "$export_destination" ] && rm -rf "$export_destination"
slack-export-viewer -z "$archive_name" \
    --html-only \
    -o "$export_destination"

[ -d "$local_destination" ] && rm -rf "$local_destination"
python tolocal.py $export_destination $local_destination

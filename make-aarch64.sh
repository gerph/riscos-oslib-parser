#!/bin/bash
##
# Build all the AArch64 source files
#

set -e

dest=$1
shift
if [[ "$dest" == '' ]] ; then
    echo "Syntax: $(basename "$0") <destdir> [<defmod files>*]" >&2
    exit 1
fi

for file in "$@" ; do
    name=$(basename "$file" .swi)
    echo "+++ Processing $name from $file"
    python oslib_parser.py --create-aarch64-api "$dest/$name.s" "$file"
done

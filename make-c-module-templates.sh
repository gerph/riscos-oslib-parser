#!/bin/bash
##
# Build all the templates for building C modules.
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
    mkdir -p "$dest/$name/cmhg"
    mkdir -p "$dest/$name/c"
    python oslib_parser.py --create-module-cmhg-template "$dest/$name/cmhg/modhead" "$file"
    python oslib_parser.py --create-module-c-template "$dest/$name/c/modhead" "$file"
done

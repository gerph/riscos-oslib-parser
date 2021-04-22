#!/bin/bash
##
# Obtain OSLib and try building all the interfaces.
#

set -e
set -o pipefail

if [[ ! -d ro-oslib-code ]] ; then
    svn checkout https://svn.code.sf.net/p/ro-oslib/code/trunk ro-oslib-code
fi

rm -rf artifacts || true
mkdir -p artifacts

tmp=/tmp/oslib_parser.$$.log

OSLibSource=ro-oslib-code/!OSLib/Source

for section in Computer Core User Toolbox ; do

    # Build the RISC OS Python interfaces for Chris
    target="artifacts/CPython/${section}"
    mkdir -p "${target}"
    for def in "${OSLibSource}/${section}/oslib/"*.swi ; do
        name=$(basename "$def" .swi)
        echo "+++ Processing ${section}/${name}"
        if ! python oslib_parser.py $def --create-python-api-template "${target}/${name}.py" 2>&1 | tee "$tmp" ; then
            mv "$tmp" "${target}/${name}-failed.log"
        fi
    done
done

rm -f "$tmp"

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

state=()

OSLibSource=ro-oslib-code/!OSLib/Source

artifactdir="artifacts/CPython"
npass=0
nfail=0
for section in Computer Core User Toolbox ; do
    # Build the RISC OS Python interfaces for Chris
    # We put these files into the same directory, rather than split between the sections.
    target="${artifactdir}/oslib"
    mkdir -p "${target}"
    for def in "${OSLibSource}/${section}/oslib/"*.swi ; do
        name=$(basename "$def" .swi)
        echo "+++ Processing ${section}/${name}"
        if ! python oslib_parser.py --oslib-dir "$OSLibSource" $def --create-python-api-template "${target}/${name}.py" 2>&1 | tee "$tmp" ; then
            mv "$tmp" "${target}/${name}-failed.log"
            nfail=$((nfail + 1))
        else
            npass=$((npass + 1))
        fi
    done
done
echo "--------"
state+=("Finished generating for CPython: Pass=$npass  Fail=$nfail")


artifactdir="artifacts/Constants"
npass=0
nfail=0
for section in Computer Core User Toolbox ; do
    # Build the constants
    target="${artifactdir}/${section}"
    mkdir -p "${target}"
    for def in "${OSLibSource}/${section}/oslib/"*.swi ; do
        name=$(basename "$def" .swi)
        echo "+++ Processing ${section}/${name}"
        if ! python oslib_parser.py $def --create-pymodule-constants "${target}/${name}.py" 2>&1 | tee "$tmp" ; then
            mv "$tmp" "${target}/${name}-failed.log"
            nfail=$((nfail + 1))
        else
            npass=$((npass + 1))
        fi
    done
done
echo "--------"
state+=("Finished generating for constants: Pass=$npass  Fail=$nfail")


artifactdir="artifacts/PyModule"
npass=0
nfail=0
for section in Computer Core User Toolbox ; do
    # Build the RISC OS Pyromaniac module stubs
    target="${artifactdir}/${section}"
    mkdir -p "${target}"
    for def in "${OSLibSource}/${section}/oslib/"*.swi ; do
        name=$(basename "$def" .swi)
        echo "+++ Processing ${section}/${name}"
        if ! python oslib_parser.py $def --create-pymodule-template "${target}/${name}.py" 2>&1 | tee "$tmp" ; then
            mv "$tmp" "${target}/${name}-failed.log"
            nfail=$((nfail + 1))
        else
            npass=$((npass + 1))
        fi
    done
done
echo "--------"
state+=("Finished generating for PyModule stubs: Pass=$npass  Fail=$nfail")


artifactdir="artifacts/PyromaniacAPI"
npass=0
nfail=0
for section in Computer Core User Toolbox ; do
    # Build the RISC OS Pyromaniac APIs
    target="${artifactdir}/${section}"
    mkdir -p "${target}"
    for def in "${OSLibSource}/${section}/oslib/"*.swi ; do
        name=$(basename "$def" .swi)
        echo "+++ Processing ${section}/${name}"
        if ! python oslib_parser.py $def --create-api-template "${target}/${name}.py" 2>&1 | tee "$tmp" ; then
            mv "$tmp" "${target}/${name}-failed.log"
            nfail=$((nfail + 1))
        else
            npass=$((npass + 1))
        fi
    done
done
echo "--------"
state+=("Finished generating for Pyromaniac APIs: Pass=$npass  Fail=$nfail")

for report in "${state[@]}" ; do
    echo "$report"
done

rm -f "$tmp"

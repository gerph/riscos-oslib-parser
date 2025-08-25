#!/bin/bash
##
# Build all the modules that we've generated.
#
# We...
#
#   Create a new Makefile using riscos-project
#   Build using riscos-amu
#
# In the future we might send this off to the build service, but it will
# almost certainly take a reasonable amount of time to build all the
# different components
#

for dir in generated/cmodule-templates/* ; do
    if [[ -d "$dir" ]] ; then
        cd "$dir"
        rm -f Makefile,fe1
        riscos-project create --type cmodule --name "$(basename "$dir")"
        riscos-amu
        cd -
    fi
done


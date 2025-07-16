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

for i in generated/cmodule-templates/* ; do
    if [[ -d "$i" ]] ; then
        cd $i
        riscos-project create --type cmodule --name "$(basename "$i")"
        riscos-amu
        cd -
    fi
done


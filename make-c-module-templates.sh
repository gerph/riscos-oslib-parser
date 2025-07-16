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

VMANAGE=
if type -p vmanage 2> /dev/null > /dev/null ; then
    VMANAGE=vmanage
elif -x ./vmanage ; then
    VMANAGE=./vmanage
fi


for file in "$@" ; do
    name=$(basename "$file" .swi)

    # Skip anything that isn't really a module
    if [[ "$file" =~ /OS[^/]*\.swi ]] ; then
        continue
    fi
    if [[ "$file" =~ /Wimp[^/][^/]*\.swi ]] ; then
        # Any of the sub-files for the Wimp
        continue
    fi
    # Failing modules at the moment:
    #   ConvertSprite (reuse of the variable 'regs')
    #   DiagnosticDump (reuse of the variable 'regs')
    #   DrawFile (Draw_PathElement is referenced within Draw_PathElement)
    #   FileSwitch (wrong CMHG SWI chunk base)
    #   ImageFileConvert (misinterpreted Void type)
    #   ImageFileRender (misinterpreted .int type)
    #   InverseTable (misinterpreted OSSpriteOp_Area type - should be .Ref?)
    #   PDriver (misinterpreted .int type, Draw_PathElement referenced within Draw_PathElement)
    #   ZapFontMenu (wrong CMHG SWI chunk base)

    # Skip any Toolbox modules, as there's no need to rebuild them
    # (and they give us errors about wrong SWI chunk bases)
    if [[ "$file" =~ /Toolbox/ ]] ; then
        continue
    fi

    OSLIB_DIR=$(dirname "$(dirname "$(dirname "$file")")")
    echo "+++ Processing $name from $file"
    mkdir -p "$dest/$name/cmhg"
    mkdir -p "$dest/$name/c"
    mkdir -p "$dest/$name/h"
    python oslib_parser.py --create-module-cmhg-template "$dest/$name/cmhg/modhead" "$file" --oslib-dir "$OSLIB_DIR"
    python oslib_parser.py --create-module-c-template "$dest/$name/c/module" "$file" --oslib-dir "$OSLIB_DIR"
    python oslib_parser.py --create-module-h-template "$dest/$name/h/types" "$file" --oslib-dir "$OSLIB_DIR"
    if [[ "$VMANAGE" != '' ]] ; then
        # VManage can be located https://github.com/gerph/riscos-vmanage
        ( cd "$dest/$name" ; "$VMANAGE" init )
    fi
done

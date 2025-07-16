##
# Test the OSLib parser is doing a useful thing
#

.PHONY: all oslib dirs

OUTPUT ?= generated

OSLIB_DIR ?= oslib
OSLIB_SOURCES = ${OSLIB_DIR}/Source

SWI_FILES = ${OSLIB_SOURCES}/Core/oslib/*.swi \
			${OSLIB_SOURCES}/Computer/oslib/*.swi \
			${OSLIB_SOURCES}/User/oslib/*.swi \
			${OSLIB_SOURCES}/Toolbox/oslib/*.swi \

all: \
	${OUTPUT}/swi_conditions.py \
	${OUTPUT}/nvram_constants.py \
	${OUTPUT}/wimp_messages.py \
	pymodules-templates \
	pymodules-constants \
	pyromaniac-apis \
	python-apis \
	module-templates \
	aarch64

oslib: ${OSLIB_SOURCES}/Core/oslib/OS.swi

dirs:
	mkdir -p ${OUTPUT}

${OSLIB_SOURCES}/Core/oslib/OS.swi:
	svn co 'svn://svn.code.sf.net/p/ro-oslib/code/trunk/!OSLib' oslib

${OUTPUT}/swi_conditions.py: oslib dirs
	python oslib_parser.py --oslib-dir ${OSLIB_SOURCES} --swi-conditions $@ ${SWI_FILES}

${OUTPUT}/nvram_constants.py: oslib dirs
	python oslib_parser.py --oslib-dir ${OSLIB_SOURCES} --create-nvram-constants $@ ${SWI_FILES}

${OUTPUT}/wimp_messages.py: oslib dirs
	python oslib_parser.py --oslib-dir ${OSLIB_SOURCES} --create-message-details $@ ${SWI_FILES}

pymodules-templates:
	mkdir -p ${OUTPUT}/pymodule-templates
	./make-pymodule-templates.sh ${OUTPUT}/pymodule-templates ${SWI_FILES}

pymodules-constants:
	mkdir -p ${OUTPUT}/pymodule-constants
	./make-pymodule-constants.sh ${OUTPUT}/pymodule-constants ${SWI_FILES}

pyromaniac-apis:
	mkdir -p ${OUTPUT}/pyromaniac-apis
	./make-pyromaniac-apis.sh ${OUTPUT}/pyromaniac-apis ${SWI_FILES}

python-apis:
	mkdir -p ${OUTPUT}/python-apis
	./make-python-apis.sh ${OUTPUT}/python-apis ${SWI_FILES}

aarch64:
	mkdir -p ${OUTPUT}/aarch64
	./make-aarch64.sh ${OUTPUT}/aarch64 ${SWI_FILES}

module-templates: vmanage
	mkdir -p ${OUTPUT}/cmodule-templates
	./make-c-module-templates.sh ${OUTPUT}/cmodule-templates ${SWI_FILES}

vmanage:
	wget -O vmanage https://raw.githubusercontent.com/gerph/riscos-vmanage/refs/heads/master/vmanage
	chmod +x vmanage
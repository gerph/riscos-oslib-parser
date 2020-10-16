# OSLib def file parser

## Introduction

This repository contains a parser for the RISC OS [OSLib](http://ro-oslib.sourceforge.net/) API header file format ('def' files).
OSLib provides interfaces for the system calls used by RISC OS, in a type safe and structured manner.
As such, it's a great source of information and a means for building API interfaces.

OSLib is supplied with a parser for these files which can generate a number of interfaces, and documentation formats.
However, it does not make it easy to target other languages or purposes.

The `oslib_parser.py` module was written to fill a particular need - that of extracting the meaning from entry and exit register mappings for SWIs.
It was written organically to parse the structures in the def files, as they were encountered.
As such, it is not complete, not may it be accurate.

It is, however, sufficient to meet the original requirement of generating SWI register mappings, and has been used to create interface definitions for RISC OS pyromaniac.

## Generating files

The tool uses Jinja2 templates to generate the source and API files.
There are 4 different types of file that can be generated with the parser:

* SWI conditions (`--swi-conditions FILE`): Generates a Python file containing SWI entry and exit details.
* PyModule template (`--create-pymodule-template FILE`): Generates a Python PyModule for use with RISC OS Pyromaniac.
* Python constants (`--create-pymodule-constants FILE`): Generate a Python file containing constants for the module.
* Pyromaniac API template (`--create-api-template FILE`): Generate a Pyromaniac API method for the module.

## Usage

Multiple 'def' files can be parsed by the command, but only a single file will be output for each generator.

For example, to create an API definition for the URL module interfaces:

```
./oslib_parser.py --create-api-template url.py ../../oslib/User/def/url
```

Adding the `-debug` option will show the structures as they are parsed.

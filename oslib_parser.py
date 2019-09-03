#!/usr/bin/env python
"""
Parse an OSLib definition file.
"""

import argparse
import os
import re
import sys


# Whether we debug the parser
debug = False


class ParseError(Exception):
    pass


class Union(object):

    def __init__(self):
        self.members = []

    def add_member(self, dtype):
        self.members.append(dtype)


class Array(object):

    def __init__(self, dtype, elements):
        self.dtype = dtype
        self.nelements = elements


class Struct(object):

    def __init__(self):
        self.members = []

    def add_member(self, dtype):
        self.members.append(dtype)


class Member(object):

    def __init__(self, dtype, name, array=None):
        self.dtype = dtype
        self.name = name
        self.array = array


class Constant(object):

    def __init__(self, name, dtype, value):
        self.name = name
        self.dtype = dtype
        self.value = value


class Register(object):

    def __init__(self, reg, assign, dtype, name, update=False, corrupted=False):
        self.reg = reg
        self.assign = assign
        self.dtype = dtype
        self.name = name
        self.update = update
        self.corrupted = corrupted

    def __repr__(self):
        return "<Register(%s %s %s: %s)>" % (self.reg, self.assign, self.dtype, self.name)


class SWI(object):

    def __init__(self, name):
        self.name = name
        self.number = None
        self.description = None
        self.starred = False
        self.hidden = False
        # When hidden, the entry and exit parameters are not valid
        self.entry = []
        self.exit = []

    def __repr__(self):
        if self.hidden:
            args = 'hidden'
        else:
            args = '%s entry, %s exit' % (len(self.entry), len(self.exit))
        return "<SWI(&%x %s, %s)>" % (0xFFFFFF if self.number is None else self.number,
                                      self.name,
                                      args)

    def add_entry(self, reg):
        self.entry.append(reg)
        # Create a dictionary of the registers as well?

    def add_exit(self, reg):
        self.exit.append(reg)
        # Create a dictionary of the registers as well?


class DefMod(object):

    def __init__(self):
        self.constants =  {}
        self.title = None
        self.types = {}
        self.needs = []
        self.types = {}
        self.swis = {}
        self.interfaces = {}

    def __repr__(self):
        return "<DefMod(%r, %i constants)>" % (self.title, len(self.constants))

    def add_constant(self, const):
        if const.name in self.constants:
            print("Redefinition of constant '%s'" % (const.name,))
        self.constants[const.name] = const

    def add_need(self, need):
        if need in self.needs:
            print("Duplicate requirement of '%s'" % (need,))
        self.needs.append(need)
        # FIXME: Parse another DefMod file?

    def add_type(self, name, dtype):
        if name in self.types:
            print("Duplicate type of '%s'" % (name,))
        self.types[name] = dtype

    def add_swi(self, swi):
        if swi.name in self.interfaces:
            print("Redefinition of SWI %x : %r / %r" % (swi.number, swi, self.interfaces[swi.name]))
        if swi.number in self.swis:
            self.swis[swi.number].append(swi)
        else:
            self.swis[swi.number] = [swi]
        self.interfaces[swi.name] = swi


class Statement(object):
    token_re = re.compile('^(\.?[A-Za-z_][A-Za-z_0-9]*|(?:&|0x)[0-9A-Fa-f]+|\.\.\.|%[01]+|0b[01]+|-?[0-9]+|[!\?:,\(\)=\|\[\]#\*\+]|->|"[^"]*"|\'[^\']*\')')

    def __init__(self, defmod, lines):
        self.lines = lines
        self.defmod = defmod
        if True:
            tok = self.token()
            if debug:
                print("Statement: %s" % (tok,))
            method_name = 'parse_%s' % (tok.lower(),)
            method = getattr(self, method_name, None)
            if method:
                method()
            else:
                if debug:
                    print("  not parseable")

    def list_tokens(self, label='Tokens'):
        print("%s:" % (label,))
        while True:
            tok = self.token()
            if not tok:
                break
            print("  '%s'" % (tok,))

    def token(self):
        while self.lines:
            line = self.lines[0].strip()
            if not line:
                self.lines.pop(0)
            else:
                match = self.token_re.search(line)
                if match:
                    tok = match.group(1)
                    line = line[len(tok):]
                    self.lines[0] = line
                    return tok
                else:
                    if len(self.lines) > 1:
                        line = line + ' ' + self.lines.pop(1).lstrip()
                        self.lines[0] = line
                    else:
                        raise ParseError("Cannot process token from line: %r" % (line,))

        return None

    def push_token(self, tok):
        if tok:
            self.lines.insert(0, tok)

    def token_group(self, terminal):
        """
        Return a list of tokens from the stream up to a terminator.
        """
        toks = []
        #print("Token group: terminal = %r" % (terminal,))
        while True:
            tok = self.token()
            #print(" TG: %s" % (tok,))
            if not tok:
                break
            if tok == terminal:
                break
            toks.append(tok)
        return toks

    def __repr__(self):
        return "<Statement()>"

    def value(self, toks):
        """
        Return a value parsed from a set of tokens.
        """
        stack = []
        #print("  value=%r" % (toks,))
        for tok in toks:
            if tok[0] == '%':
                value = int(tok[1:], 2)
            elif tok[0:2] == '0b':
                value = int(tok[2:], 2)
            elif tok[0] == '&':
                value = int(tok[1:], 16)
            elif tok[0:2] == '0x':
                value = int(tok[2:], 16)
            elif tok.isdigit() or (tok[0] == '-' and tok[1:].isdigit()):
                value = int(tok)
            elif tok[0] == '"' and tok[-1] == '"':
                value = tok[1:-1]
            elif tok[0] == "'" and tok[-1] == "'":
                #value = tok[1:-1]
                # This is a literal for now?
                value = tok
            else:
                # It's a constant string, I assume
                # FIXME: This isn't distinguishable from a regular string.
                value = tok
            stack.append(value)
        if not stack:
            return None
        if len(stack) == 1:
            return stack[0]
        # Eventually we'll include some expression processor
        return stack

    def expect(self, expect):
        tok = self.token()
        if isinstance(expect, tuple):
            if tok in expect or (tok and tok.upper() in expect):
                return tok
        else:
            if tok == expect or (tok and tok.upper() == expect):
                return tok

        raise ParseError("Expected %r, but got %r" % (expect, tok))

    def gettype(self, named=True):
        tok = self.token()
        elements = None
        if tok == '[':
            # This is an array of elements
            elements = self.token_group(']')
            # Recurse, because it could be an array of an array, etc.
            dtype = self.gettype(named=named)
            dtype = Array(dtype, elements)
            return dtype

        if tok == '.Ref':
            dtype = '&' + self.token()
        elif tok in ('.Struct', '.Union'):
            if tok == '.Struct':
                obj = Struct()
            else:
                obj = Union()
            self.expect('(')
            while True:
                # Each member consists of a type and a name
                dtype = self.gettype()
                name = self.token()

                tok = self.token()
                if tok and tok[0] == '"':
                    # This type has a comment.
                    # FIXME: Process it.
                    # (skipped for now)
                    pass
                else:
                    self.push_token(tok)

                tok = self.expect((',', ')', '...'))
                if tok == '...':
                    # This last item is actually an variable array
                    dtype = Array(dtype, '...')

                obj.add_member(Member(dtype, name))

                if tok == ')':
                    break
                if tok == '...':
                    # The next token must be the closing bracket
                    self.expect(')')
                    break

            dtype = obj
        else:
            dtype = tok

        if named:
            self.expect(':')
        return dtype

    def parse_title(self):
        self.defmod.title = self.token()
        if debug:
            print("  Title: %r" % (self.defmod.title,))

    def parse_const(self):
        #self.list_tokens('Constants')
        while True:
            toks = self.token_group(',')
            if not toks:
                break
            name = toks[0]
            if toks[1] != '=':
                raise ParseError("Constant token format unexpected (no =): %r" % (toks,))
            consttype = toks[2]
            if consttype == '.Ref':
                consttype = '&' + toks[3]
                toks.pop(2)
            if toks[3] != ':':
                raise ParseError("Constant token format unexpected (type specifier): %r" % (toks,))
            value = self.value(toks[4:])
            self.defmod.add_constant(Constant(name, consttype, value))
            if debug:
                print("  Constant: '%s' => (%s) %s" % (name, consttype, value))

    def parse_type(self):
        #self.list_tokens('Types')
        while True:
            name = self.token()
            if not name:
                break

            tok = self.token()
            if tok and tok[0] == '"':
                # This type has a comment.
                # FIXME: Process it.
                # (skipped for now)
                pass
            else:
                self.push_token(tok)

            tok = self.expect(("=", ',', None))
            if tok == ',' or tok is None:
                # Not sure what an unnamed type should be, but I'm going to call it a Bits right now.
                dtype = '.Any'
                if tok:
                    self.push_token(tok)
            else:
                dtype = self.gettype(named=False)

                tok = self.token()
                if tok and tok[0] == '"':
                    # This type has a comment.
                    # FIXME: Process it.
                    # (skipped for now)
                    pass
                else:
                    self.push_token(tok)

            self.defmod.add_type(name, dtype)
            if debug:
                print("  Type: %s" % (name,))

            tok = self.expect((',', None))
            if tok is None:
                break

    def parse_needs(self):
        #self.list_tokens('Needs')
        while True:
            need = self.token()
            if not need:
                break
            self.defmod.add_need(need)
            if debug:
                print("  Needs: %s" % (need,))

            tok = self.token()
            if tok is None:
                break
            if tok != ',':
                raise ParseError("Expected a ',' in Needs, but got %r" % (tok,))

    def parse_swi(self):
        # Format looks something like:
        # {Name = (NUMBER number "description",
        #          ENTRY ( {register ->|= type: name,}* )
        #          EXIT ( {register!? = .REF? type: name,}* )
        #          ABSENT
        #         ),?}*
        while True:
            name = self.token()
            if not name:
                break
            tok = self.token()
            self.expect('(')

            swi = SWI(name)

            while True:
                tok = self.expect(('NUMBER', 'ENTRY', 'EXIT', 'ABSENT')).upper()
                if tok == 'NUMBER':
                    tok = self.token()
                    swinumber = self.value([tok])
                    tok = self.token()
                    # The description could be omitted
                    description = None
                    if tok == '*':
                        # Not entirely sure what this means, but there isn't a description if so.
                        swi.starred = True
                    elif tok[0] != '"':
                        self.push_token(tok)
                    else:
                        description = self.value([tok])

                    swi.number = swinumber
                    swi.description = description

                elif tok == 'ABSENT':
                    swi.hidden = True

                elif tok == 'ENTRY':
                    self.expect('(')
                    while True:
                        reg = self.token()
                        if reg[0] != 'R' and reg != 'FLAGS':
                            raise ParseError("Entry register name not understood: %s" % (reg,))
                        if reg == 'FLAGS':
                            dtype = '.flags'
                            name = None
                        else:
                            assign = self.expect(('->', '=', '#', '|', '+'))
                            # | means 'OR with the previous value'
                            # + appears to mean 'store the previous value as the first byte and the
                            #   rest of the structure is this structure' (for OS_Word)
                            if assign == '#':
                                dtype = '.literal'
                                name = self.value([self.token()])
                            else:
                                # In OSSpriteOp, there's a place where a constant is used with
                                # an '=', where here we expect to fetch a type. Because of this
                                # I'm going to fetch two tokens, then put them back and decode
                                # what I really want to do for that case. Probably this is just
                                # an oddity of the syntax, but I just need to get it to parse
                                # really.
                                if assign == '=':
                                    tok1 = self.token()
                                    tok2 = self.token()
                                    if tok2 == ',' or tok2 == ')':
                                        # This was the literal case just discussed.
                                        dtype = '.literal'
                                        name = self.value([tok1])
                                        self.push_token(tok2)
                                    else:
                                        self.push_token(tok2)
                                        self.push_token(tok1)
                                        dtype = self.gettype()
                                        name = self.token()
                                else:
                                    dtype = self.gettype()
                                    name = self.token()

                        # There might be a comment on the register.
                        tok = self.token()
                        if tok[0] == '"':
                            # Comment field present
                            pass
                        else:
                            self.push_token(tok)

                        swi.add_entry(Register(reg, assign, dtype, name))

                        tok = self.expect((',', ')'))
                        if tok == ')':
                            break

                elif tok == 'EXIT':
                    self.expect('(')
                    while True:
                        reg = self.token()
                        if reg[0] != 'R' and reg != 'FLAGS':
                            raise ParseError("Exit register name not understood: %s" % (reg,))
                        updated = False
                        corrupted = False
                        if reg == 'FLAGS':
                            assign = self.expect(('!',))
                            dtype = '.flags'
                            name = None
                        else:
                            assign = self.expect(('!', '?', '->', '=', '#'))
                            if assign == '!':
                                updated = True
                                assign = self.expect(('?', '->', '=', '#'))
                            if assign == '#':
                                dtype = '.literal'
                                name = self.value([self.token()])
                            elif assign == '?':
                                dtype = '.corrupted'
                                name = None
                                corrupted = True
                            else:
                                dtype = self.gettype()
                                name = self.token()

                        # There might be a comment on the register.
                        tok = self.token()
                        if tok[0] == '"':
                            # Comment field present
                            pass
                        else:
                            self.push_token(tok)

                        swi.add_exit(Register(reg, assign, dtype, name, updated, corrupted))

                        tok = self.expect((',', ')'))
                        if tok == ')':
                            break
                else:
                    raise ParseError("Unparseable SWI token '%s'" % (tok,))

                tok = self.expect((',', ')'))
                if tok == ')':
                    break

            self.defmod.add_swi(swi)
            if debug:
                print("  SWI: %r" % (swi,))

            tok = self.expect((',', None))
            if tok is None:
                break


def parse_file(filename):
    defmod = DefMod()
    with open(filename) as fh:
        accumulator = []
        inquotes = False
        for line in fh:
            # Replace any hard spaces with regular spaces
            line = line.replace('\xa0', ' ')
            line = line.rstrip('\n')
            if '//' in line:
                before, after = line.split('//', 1)
                line = before
            while ';' in line:
                before, after = line.split(';', 1)
                quotes_present = len(before.split('"')) - 1
                if quotes_present & 1:
                    inquotes = not inquotes

                if inquotes:
                    # This is a ; in a quoted string, so we need to just move it to the accumulator
                    # so that we can skip it nicely.
                    accumulator.append(before)
                    line = after
                    continue

                line = after
                accumulator.append(before)
                Statement(defmod, accumulator)
                accumulator = []

            if line:
                accumulator.append(line)

            quotes_present = len(line.split('"')) - 1
            if quotes_present & 1:
                inquotes = not inquotes

    return defmod


def write_all_swi_conditions(defmods, filename):
    with open(filename, 'w') as fh:
        # Header:
        fh.write('''\
"""
Conditions for the entry to SWIs by name.

Hopefully these will be correct.
"""

swi_conditions = {
''')

        defmods = [defmod for defmod in defmods if defmod.swis]
        defmods = sorted(defmods, key=lambda defmod: min(defmod.swis))

        for defmod in defmods:
            fh.write('    # %s:\n' % (defmod.title,))
            write_swi_conditions(defmod, fh)
            fh.write('\n')

        # Footer:
        fh.write('''\
}
''')


def write_swi_conditions(defmod, fh):
    for swi, swilist in defmod.swis.items():
        swidef = swilist[0]

        if '_' not in swidef.name:
            # Skip vectors, events, etc
            continue
        if swidef.name.startswith("Service_") or \
           swidef.name.startswith("Event_") or \
           swidef.name.startswith("UpCall_"):
            # Skip services, events
            continue

        regdefs = {
            'entry': {},
            'exit': {},
        }
        for name, regs in (('entry', swidef.entry), ('exit', swidef.exit)):

            regdef = regdefs[name]
            for reg in regs:
                if reg.reg == 'FLAGS':
                    continue

                if reg.assign == '#':
                    desc = 'constant ' + str(reg.name)
                    name = None
                elif reg.assign == '->':
                    desc = 'pointer to ' + reg.name
                    name = reg.name
                elif reg.assign == '|':
                    desc = "OR " + reg.name
                    name = reg.name
                elif reg.assign == '+':
                    desc = "in block " + reg.name
                    name = reg.name
                elif reg.assign == '?':
                    desc = 'corrupted'
                    name = None
                elif reg.assign == '!':
                    desc = 'updated ' + reg.name
                    name = reg.name
                elif reg.assign == '=':
                    if isinstance(reg.dtype, str) and reg.dtype[0] == '&':
                        desc = 'pointer to fill ' + reg.name
                    else:
                        desc = reg.name
                    name = reg.name
                else:
                    desc = "unknown assignment '%s' of %s" % (reg.assign, reg.name)
                    name = None

                regnum = int(reg.reg[1:])
                if regnum in regdef:
                    regdef[regnum] += ' ' + desc
                else:
                    regdef[regnum] = desc

        entry_reglist = ['%i: "%s"' % (num, desc) for num, desc in sorted(regdefs['entry'].items())]
        exit_reglist = ['%i: "%s"' % (num, desc) for num, desc in sorted(regdefs['exit'].items())]
        fh.write("    0x%06x: {" % (swidef.number,))
        fh.write("'description': %r,\n" % (swidef.description,))
        fh.write("               ")
        fh.write("'entry': {%s},\n" % (", ".join(entry_reglist),))
        fh.write("               ")
        fh.write("'exit': {%s}},\n" % (", ".join(exit_reglist)))


def setup_argparse():
    parser = argparse.ArgumentParser(usage="%s [<options>] <def-mod-file>" % (os.path.basename(sys.argv[0]),))
    parser.add_argument('--debug', action='store_true', default=False,
                        help="Enable debugging")
    parser.add_argument('files', nargs="+",
                        help="DefMod files to read")
    parser.add_argument('--swi-conditions', action='store',
                        help="File to write the SWI conditions into")

    return parser


def main():
    parser = setup_argparse()

    options = parser.parse_args()

    global debug
    debug = options.debug

    all_defmods = []

    for defmodfile in options.files:
        print("Reading %s" % (defmodfile,))
        try:
            defmod = parse_file(defmodfile)
            all_defmods.append(defmod)
        except Exception as exc:
            print("  Failed %s: %r" % (defmodfile, exc))

    if options.swi_conditions:
        write_all_swi_conditions(all_defmods, options.swi_conditions)


if __name__ == '__main__':
    sys.exit(main())

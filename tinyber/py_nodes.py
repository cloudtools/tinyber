# -*- Mode: Python -*-

from tinyber import nodes
from tinyber.writer import Writer
import os
import sys

def psafe (s):
    return s.replace ('-', '_')

def emit_pairs(out, tag, pairs, reversed=False):
    out.writelines('%s = {' % tag)
    with out.indent():
        for x in pairs:
            if reversed:
                out.writelines("%s: %s," % (x[1], x[0]))
            else:
                out.writelines("%s: %s," % (x[0], x[1]))
    out.writelines('}')

class c_base_type (nodes.c_base_type):

    def emit (self, out):
        pass

    def emit_decode (self, out):
        type_name, min_size, max_size = self.attrs
        if type_name == 'INTEGER':
            out.writelines ('v = src.next_INTEGER(%s, %s)' % (min_size, max_size),)
        elif type_name == 'OCTET STRING':
            out.writelines ('v = src.next_OCTET_STRING(%s, %s)' % (min_size, max_size),)
        elif type_name == 'BOOLEAN':
            out.writelines ('v = src.next_BOOLEAN()')
        else:
            import pdb
            pdb.set_trace()

    def emit_encode (self, out, val):
        type_name, min_size, max_size = self.attrs
        if type_name == 'INTEGER':
            out.writelines ('dst.emit_INTEGER(%s)' % (val,))
        elif type_name == 'OCTET STRING':
            out.writelines ('dst.emit_OCTET_STRING(%s)' % (val,))
        elif type_name == 'BOOLEAN':
            out.writelines ('dst.emit_BOOLEAN(%s)' % (val,))
        else:
            import pdb
            pdb.set_trace()

class c_sequence (nodes.c_sequence):

    parent_class = 'SEQUENCE'

    def emit (self, out):
        name, slots = self.attrs
        out.writelines ('__slots__ = (')
        with out.indent():
            for x in slots:
                out.writelines("'%s'," % psafe(x))
        out.writelines (')')

    def emit_decode (self, out):
        name, slots = self.attrs
        types = self.subs
        out.writelines ('src = src.next(TAG.SEQUENCE, FLAG.STRUCTURED)')
        for i in range (len (slots)):
            slot_name = slots[i]
            slot_type = types[i]
            slot_type.emit_decode (out)
            out.writelines ('self.%s = v' % (psafe(slot_name),))
        out.writelines ('src.assert_done()')

    def emit_encode (self, out, val):
        name, slots = self.attrs
        types = self.subs
        out.writelines ('with dst.TLV(TAG.SEQUENCE, FLAG.STRUCTURED):')
        with out.indent():
            for i in reversed (range (len (types))):
                types[i].emit_encode (out, 'self.%s' % (psafe(slots[i]),))

class c_sequence_of (nodes.c_sequence_of):

    def emit (self, out):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs

    def emit_decode (self, out):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs
        out.writelines (
            'src, save = src.next(TAG.SEQUENCE, FLAG.STRUCTURED), src',
            'a = []',
            'while not src.done():'
        )
        with out.indent():
            seq_type.emit_decode (out)
            out.writelines ('a.append(v)')
        if min_size is not None and min_size > 0:
            out.writelines ('if len(a) < %d:' % (min_size,))
            with out.indent():
                out.writelines ('raise ConstraintViolation(a)')
        if max_size is not None:
            out.writelines ('if len(a) > %d:' % (max_size,))
            with out.indent():
                out.writelines ('raise ConstraintViolation(a)')
        out.writelines ('v, src = a, save')

    def emit_encode (self, out, val):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs
        out.writelines ('with dst.TLV(TAG.SEQUENCE, FLAG.STRUCTURED):')
        with out.indent():
            out.writelines ('for v in reversed(%s):' % (val,))
            with out.indent():
                seq_type.emit_encode (out, 'v')

class c_set_of (nodes.c_sequence_of):

    def emit (self, out):
        min_size, max_size, = self.attrs
        [item_type] = self.subs

    def emit_decode (self, out):
        min_size, max_size, = self.attrs
        [item_type] = self.subs
        out.writelines (
            'src, save = src.next(TAG.SET, FLAG.STRUCTURED), src',
            'a = set()',
            'while not src.done():'
        )
        with out.indent():
            item_type.emit_decode (out)
            out.writelines ('a.add (v)')
        out.writelines ("# check constraints")
        out.writelines ('v, src = a, save')

    def emit_encode (self, out, val):
        min_size, max_size, = self.attrs
        [item_type] = self.subs
        out.writelines ('with dst.TLV(TAG.SET, FLAG.STRUCTURED):')
        with out.indent():
            out.writelines ('for v in %s:' % (val,))
            with out.indent():
                item_type.emit_encode (out, 'v')


class c_choice (nodes.c_choice):

    parent_class = 'CHOICE'
    nodecoder = True
    noencoder = True

    def emit (self, out):
        name, slots, tags = self.attrs
        types = self.subs
        pairs = []
        for i in range (len (slots)):
            pairs.append ((types[i].name(), tags[i]))
        emit_pairs(out, 'tags_f', pairs)
        emit_pairs(out, 'tags_r', pairs, reversed=True)

class c_enumerated (nodes.c_enumerated):

    def emit (self, out):
        defname, alts, = self.attrs
        pairs = []
        for name, val in alts:
            pairs.append (("'%s'" % name, val))
        emit_pairs(out, 'tags_f', pairs)
        emit_pairs(out, 'tags_r', pairs, reversed=True)

    parent_class = 'ENUMERATED'
    nodecoder = True
    noencoder = True

class c_defined (nodes.c_defined):

    def emit (self, out):
        name, max_size = self.attrs

    def emit_decode (self, out):
        type_name, max_size = self.attrs
        out.writelines (
            'v = %s()' % (type_name,),
            'v._decode(src)',
        )

    def emit_encode (self, out, val):
        type_name, max_size = self.attrs
        out.writelines ('%s._encode(dst)' % (val,))

class PythonBackend:

    def __init__ (self, args, walker, module_name, path):
        self.args = args
        self.walker = walker
        self.module_name = module_name
        self.path = path
        self.base_path = os.path.join(path, module_name)

    def gen_decoder (self, type_name, type_decl, node):
        # generate a decoder for a type assignment.
        self.out.newline()
        self.out.writelines ('def _decode(self, src):')
        with self.out.indent():
            node.emit_decode (self.out)
            # this line is unecessary (but harmless) on normal defined sequence types
            self.out.writelines ('self.value = v')

    def gen_encoder (self, type_name, type_decl, node):
        # generate an encoder for a type assignment
        self.out.newline()
        self.out.writelines ('def _encode(self, dst):')
        with self.out.indent():
            node.emit_encode (self.out, 'self.value')

    def gen_codec_funs (self, type_name, type_decl, node):
        if not hasattr (node, 'nodecoder'):
            self.gen_decoder (type_name, type_decl, node)
        if not hasattr (node, 'noencoder'):
            self.gen_encoder (type_name, type_decl, node)

    def generate_code (self):
        self.out = Writer (open (self.base_path + '_ber.py', 'w'), indent_size=4)
        command = os.path.basename(sys.argv[0])
        self.out.writelines (
            '# -*- Mode: Python -*-',
            '# generated by: %s %s' % (command, " ".join(sys.argv[1:])),
            '# *** do not edit ***',
            '',
        )
        if self.args.no_standalone:
            self.out.writelines ('from tinyber.codec import *', '')
        else:
            pkg_dir, _ = os.path.split (__file__)

            self.out.writelines ('# --- start codec.py ---', '')
            with open(os.path.join(pkg_dir, 'codec.py'), 'r') as infile:
                for line in infile:
                    self.out.writelines (line[:-1])
            self.out.writelines('', '# --- end codec.py ---')

        self.tag_assignments = self.walker.tag_assignments
        # generate typedefs and prototypes.
        for (type_name, node, type_decl) in self.walker.defined_types:
            if hasattr (node, 'parent_class'):
                parent_class = node.parent_class
            else:
                parent_class = 'ASN1'
            self.out.newline()
            self.out.newline()
            self.out.writelines ('class %s(%s):' % (type_name, parent_class))
            with self.out.indent():
                self.out.writelines (
                    'max_size = %d' % (node.max_size())
                )
                node.emit (self.out)
                self.gen_codec_funs (type_name, type_decl, node)
        self.out.close()
